from datetime import datetime
from decimal import Decimal

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


class FilmOut(BaseModel):
    id: int
    titre: str
    description: str | None
    duree_minutes: int
    categorie: str | None


class SeanceOut(BaseModel):
    id: int
    film_id: int
    titre_film: str
    salle: str
    date_heure_debut: datetime
    tarif: Decimal
    places_total: int
    places_libres: int


class PlaceOut(BaseModel):
    id: int
    numero_place: int
    statut: str


class SeanceDetailOut(SeanceOut):
    places: list[PlaceOut]


class ReservationIn(BaseModel):
    seance_id: int
    place_id: int


class BilletOut(BaseModel):
    id: int
    code_billet: str
    statut: str
    date_reservation: datetime
    titre_film: str
    salle: str
    date_heure_debut: datetime
    numero_place: int
    tarif: Decimal
