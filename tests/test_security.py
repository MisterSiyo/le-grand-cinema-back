import jwt

from app.config import get_settings
from app.security import create_token, hash_password, verify_password


def test_le_mot_de_passe_est_hache():
    hache = hash_password("motdepasse123")
    assert hache != "motdepasse123"
    assert verify_password("motdepasse123", hache)


def test_un_mauvais_mot_de_passe_est_refuse():
    assert not verify_password("autre-mot-de-passe", hash_password("motdepasse123"))


def test_deux_hachages_du_meme_mot_de_passe_different():
    assert hash_password("motdepasse123") != hash_password("motdepasse123")


def test_le_jeton_contient_l_utilisateur_et_son_role():
    settings = get_settings()
    contenu = jwt.decode(create_token(7, "ADMIN"), settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    assert contenu["sub"] == "7"
    assert contenu["role"] == "ADMIN"
