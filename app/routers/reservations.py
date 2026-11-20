import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.database import get_connection
from app.schemas import BilletOut, ReservationIn
from app.security import get_current_user

router = APIRouter(prefix="/reservations", tags=["Réservations"])

SELECT_BILLET = """
    SELECT r.id, r.utilisateur_id, r.code_billet, r.statut, r.date_reservation,
           f.titre AS titre_film, s.salle, s.date_heure_debut, p.numero_place, s.tarif
    FROM reservations r
    JOIN seances s ON s.id = r.seance_id
    JOIN films f ON f.id = s.film_id
    JOIN places p ON p.id = r.place_id
"""


@router.post("", response_model=BilletOut, status_code=status.HTTP_201_CREATED)
def reserver(
    data: ReservationIn,
    user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    """Réserve une place pour l'utilisateur connecté et renvoie son billet."""
    place = conn.execute(
        "SELECT id, statut FROM places WHERE id = %s AND seance_id = %s",
        (data.place_id, data.seance_id),
    ).fetchone()
    if place is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Place introuvable pour cette séance")

    seance = conn.execute(
        "SELECT date_heure_debut > now() AS a_venir FROM seances WHERE id = %s", (data.seance_id,)
    ).fetchone()
    if not seance["a_venir"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette séance est déjà commencée")

    if place["statut"] != "LIBRE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette place n'est plus disponible")

    conn.execute("UPDATE places SET statut = 'RESERVEE' WHERE id = %s", (place["id"],))
    reservation_id = conn.execute(
        """
        INSERT INTO reservations (utilisateur_id, seance_id, place_id, code_billet)
        VALUES (%s, %s, %s, %s)
        RETURNING id
        """,
        (user["id"], data.seance_id, place["id"], "LGC-" + uuid.uuid4().hex[:12].upper()),
    ).fetchone()["id"]
    return conn.execute(SELECT_BILLET + " WHERE r.id = %s", (reservation_id,)).fetchone()


@router.get("/moi", response_model=list[BilletOut])
def mes_reservations(
    user: dict = Depends(get_current_user), conn: Connection = Depends(get_connection)
):
    """Liste les réservations de l'utilisateur connecté, les plus proches en premier."""
    return conn.execute(
        SELECT_BILLET + " WHERE r.utilisateur_id = %s ORDER BY s.date_heure_debut", (user["id"],)
    ).fetchall()


@router.get("/{reservation_id}/billet", response_model=BilletOut)
def lire_billet(
    reservation_id: int,
    user: dict = Depends(get_current_user),
    conn: Connection = Depends(get_connection),
):
    """Billet dématérialisé d'une réservation. Réservé à son propriétaire et aux administrateurs."""
    billet = conn.execute(SELECT_BILLET + " WHERE r.id = %s", (reservation_id,)).fetchone()
    # Même réponse si la réservation n'existe pas ou appartient à quelqu'un d'autre
    if billet is None or (billet["utilisateur_id"] != user["id"] and user["role"] != "ADMIN"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Billet introuvable")
    return billet
