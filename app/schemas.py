from datetime import date, datetime
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


class FilmIn(BaseModel):
    titre: str = Field(min_length=1, max_length=255)
    description: str | None = None
    duree_minutes: int = Field(gt=0, le=600)
    categorie: str | None = Field(default=None, max_length=100)


class SeanceIn(BaseModel):
    film_id: int
    salle: str = Field(min_length=1, max_length=50)
    date_heure_debut: datetime
    tarif: Decimal = Field(ge=0, max_digits=6, decimal_places=2)
    nb_places: int = Field(default=50, ge=1, le=500)


class SeanceUpdateIn(BaseModel):
    salle: str = Field(min_length=1, max_length=50)
    date_heure_debut: datetime
    tarif: Decimal = Field(ge=0, max_digits=6, decimal_places=2)


class RemplissageSeanceOut(BaseModel):
    seance_id: int
    titre_film: str
    salle: str
    date_heure_debut: datetime
    places_total: int
    places_reservees: int
    taux_remplissage: float


class RemplissageJourOut(BaseModel):
    jour: date
    nb_seances: int
    places_total: int
    places_reservees: int
    taux_remplissage: float


class SyntheseRemplissageOut(BaseModel):
    nb_seances: int
    places_total: int
    places_reservees: int
    taux_remplissage: float
    par_jour: list[RemplissageJourOut]


class ReservationAdminOut(BaseModel):
    id: int
    code_billet: str
    statut: str
    date_reservation: datetime
    email: EmailStr
    titre_film: str
    salle: str
    date_heure_debut: datetime
    numero_place: int
