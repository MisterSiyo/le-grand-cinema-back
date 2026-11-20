from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection
from psycopg.errors import UniqueViolation

from app.database import get_connection
from app.schemas import ConnexionIn, InscriptionIn, TokenOut, UtilisateurOut
from app.security import create_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/inscription", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def inscription(data: InscriptionIn, conn: Connection = Depends(get_connection)):
    """Crée un compte spectateur (rôle USER) et renvoie un jeton de connexion."""
    try:
        user = conn.execute(
            """
            INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe_hash)
            VALUES (%s, %s, %s, %s)
            RETURNING id, nom, prenom, email, role
            """,
            (data.nom, data.prenom, data.email.lower(), hash_password(data.mot_de_passe)),
        ).fetchone()
    except UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette adresse email est déjà utilisée") from None
    return TokenOut(access_token=create_token(user["id"], user["role"]), utilisateur=user)


@router.post("/connexion", response_model=TokenOut)
def connexion(data: ConnexionIn, conn: Connection = Depends(get_connection)):
    """Vérifie l'email et le mot de passe, puis renvoie un jeton de connexion."""
    user = conn.execute(
        "SELECT id, nom, prenom, email, role, mot_de_passe_hash FROM utilisateurs WHERE email = %s",
        (data.email.lower(),),
    ).fetchone()
    # Même message si l'email est inconnu ou le mot de passe faux
    if user is None or not verify_password(data.mot_de_passe, user["mot_de_passe_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect")
    return TokenOut(access_token=create_token(user["id"], user["role"]), utilisateur=user)


@router.get("/moi", response_model=UtilisateurOut)
def moi(user: dict = Depends(get_current_user)):
    """Renvoie l'utilisateur connecté."""
    return user
