from fastapi import APIRouter, Depends, HTTPException, Response, status
from psycopg import Connection
from psycopg.errors import ForeignKeyViolation

from app.database import get_connection
from app.routers.seances import lire_seance
from app.schemas import FilmIn, FilmOut, SeanceDetailOut, SeanceIn, SeanceUpdateIn
from app.security import require_admin

router = APIRouter(
    prefix="/admin", tags=["Administration - programmation"], dependencies=[Depends(require_admin)]
)

COLONNES_FILM = "id, titre, description, duree_minutes, categorie"


def _reservations_film(conn: Connection, film_id: int) -> int:
    return conn.execute(
        """
        SELECT count(*) AS n FROM reservations r JOIN seances s ON s.id = r.seance_id
        WHERE s.film_id = %s AND r.statut = 'CONFIRMEE'
        """,
        (film_id,),
    ).fetchone()["n"]


def _reservations_seance(conn: Connection, seance_id: int) -> int:
    return conn.execute(
        "SELECT count(*) AS n FROM reservations WHERE seance_id = %s AND statut = 'CONFIRMEE'",
        (seance_id,),
    ).fetchone()["n"]


@router.post("/films", response_model=FilmOut, status_code=status.HTTP_201_CREATED)
def creer_film(data: FilmIn, conn: Connection = Depends(get_connection)):
    """Ajoute un film au catalogue."""
    return conn.execute(
        f"""
        INSERT INTO films (titre, description, duree_minutes, categorie)
        VALUES (%s, %s, %s, %s) RETURNING {COLONNES_FILM}
        """,
        (data.titre, data.description, data.duree_minutes, data.categorie),
    ).fetchone()


@router.put("/films/{film_id}", response_model=FilmOut)
def modifier_film(film_id: int, data: FilmIn, conn: Connection = Depends(get_connection)):
    """Modifie un film."""
    film = conn.execute(
        f"""
        UPDATE films SET titre = %s, description = %s, duree_minutes = %s, categorie = %s
        WHERE id = %s RETURNING {COLONNES_FILM}
        """,
        (data.titre, data.description, data.duree_minutes, data.categorie, film_id),
    ).fetchone()
    if film is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film introuvable")
    return film


@router.delete("/films/{film_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_film(film_id: int, conn: Connection = Depends(get_connection)):
    """Supprime un film et ses séances. Refusé si des places sont réservées."""
    if conn.execute("SELECT 1 FROM films WHERE id = %s", (film_id,)).fetchone() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film introuvable")
    if _reservations_film(conn, film_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Ce film a des réservations, il ne peut pas être supprimé"
        )
    conn.execute("DELETE FROM films WHERE id = %s", (film_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/seances", response_model=SeanceDetailOut, status_code=status.HTTP_201_CREATED)
def creer_seance(data: SeanceIn, conn: Connection = Depends(get_connection)):
    """Programme une séance et crée ses places numérotées."""
    try:
        seance_id = conn.execute(
            """
            INSERT INTO seances (film_id, salle, date_heure_debut, tarif)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (data.film_id, data.salle, data.date_heure_debut, data.tarif),
        ).fetchone()["id"]
    except ForeignKeyViolation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film introuvable")
    conn.execute(
        "INSERT INTO places (seance_id, numero_place) SELECT %s, generate_series(1, %s)",
        (seance_id, data.nb_places),
    )
    return lire_seance(seance_id, conn)


@router.put("/seances/{seance_id}", response_model=SeanceDetailOut)
def modifier_seance(
    seance_id: int, data: SeanceUpdateIn, conn: Connection = Depends(get_connection)
):
    """Modifie la salle, l'horaire ou le tarif d'une séance."""
    modifiee = conn.execute(
        "UPDATE seances SET salle = %s, date_heure_debut = %s, tarif = %s WHERE id = %s RETURNING id",
        (data.salle, data.date_heure_debut, data.tarif, seance_id),
    ).fetchone()
    if modifiee is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Séance introuvable")
    return lire_seance(seance_id, conn)


@router.delete("/seances/{seance_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_seance(seance_id: int, conn: Connection = Depends(get_connection)):
    """Supprime une séance et ses places. Refusé si des places sont réservées."""
    if conn.execute("SELECT 1 FROM seances WHERE id = %s", (seance_id,)).fetchone() is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Séance introuvable")
    if _reservations_seance(conn, seance_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Cette séance a des réservations, elle ne peut pas être supprimée"
        )
    conn.execute("DELETE FROM seances WHERE id = %s", (seance_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
