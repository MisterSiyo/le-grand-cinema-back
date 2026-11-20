from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg import Connection

from app.database import get_connection
from app.schemas import SeanceDetailOut, SeanceOut

router = APIRouter(prefix="/seances", tags=["Séances"])

# Les places libres sont recalculées à chaque appel : c'est ce qui donne la disponibilité en temps réel.
SELECT_SEANCES = """
    SELECT s.id, s.film_id, f.titre AS titre_film, s.salle, s.date_heure_debut, s.tarif,
           count(p.id) AS places_total,
           count(p.id) FILTER (WHERE p.statut = 'LIBRE') AS places_libres
    FROM seances s
    JOIN films f ON f.id = s.film_id
    LEFT JOIN places p ON p.seance_id = s.id
"""


@router.get("", response_model=list[SeanceOut])
def lister_seances(
    film_id: int | None = Query(None, description="Ne garder que les séances de ce film"),
    jour: date | None = Query(None, description="Ne garder que les séances de ce jour (AAAA-MM-JJ)"),
    conn: Connection = Depends(get_connection),
):
    """Liste les séances à venir, avec le nombre de places libres."""
    return conn.execute(
        SELECT_SEANCES
        + """
        WHERE s.date_heure_debut >= now()
          AND (%(film_id)s::int IS NULL OR s.film_id = %(film_id)s)
          AND (%(jour)s::date IS NULL OR s.date_heure_debut::date = %(jour)s)
        GROUP BY s.id, f.titre
        ORDER BY s.date_heure_debut
        """,
        {"film_id": film_id, "jour": jour},
    ).fetchall()


@router.get("/{seance_id}", response_model=SeanceDetailOut)
def lire_seance(seance_id: int, conn: Connection = Depends(get_connection)):
    """Détail d'une séance avec le statut de chaque place."""
    seance = conn.execute(
        SELECT_SEANCES + " WHERE s.id = %s GROUP BY s.id, f.titre", (seance_id,)
    ).fetchone()
    if seance is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Séance introuvable")
    places = conn.execute(
        "SELECT id, numero_place, statut FROM places WHERE seance_id = %s ORDER BY numero_place",
        (seance_id,),
    ).fetchall()
    return {**seance, "places": places}
