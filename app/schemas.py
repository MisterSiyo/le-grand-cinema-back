from pydantic import BaseModel, EmailStr, Field


class InscriptionIn(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    mot_de_passe: str = Field(min_length=8, max_length=64)


class ConnexionIn(BaseModel):
    email: EmailStr
    mot_de_passe: str = Field(max_length=64)


class UtilisateurOut(BaseModel):
    id: int
    nom: str
    prenom: str
    email: EmailStr
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurOut
