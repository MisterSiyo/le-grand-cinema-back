from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from psycopg import Connection

from app.config import get_settings
from app.database import get_connection

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(user_id: int, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    conn: Connection = Depends(get_connection),
) -> dict:
    """Retourne l'utilisateur du jeton, relu en base pour tenir compte d'un changement de rôle."""
    erreur = HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    if credentials is None:
        raise erreur
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erreur from None
    user = conn.execute(
        "SELECT id, nom, prenom, email, role FROM utilisateurs WHERE id = %s", (user_id,)
    ).fetchone()
    if user is None:
        raise erreur
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "ADMIN":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès réservé aux administrateurs")
    return user
