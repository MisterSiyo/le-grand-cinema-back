from datetime import date

from fastapi import APIRouter, Depends, Query
from psycopg import Connection

from app.database import get_connection
from app.schemas import (
    RemplissageSeanceOut,
    ReservationAdminOut,
    SyntheseRemplissageOut,
)
from app.security import require_admin

router = APIRouter(
    prefix="/admin", tags=["Administration - suivi"], dependencies=[Depends(require_admin)]
)

# Une place RESERVEE compte pour le remplissage. Le taux est en pourcentage, 0 si la séance n'a pas de place.
TAUX = "COALESCE(round(100.0 * count(p.id) FILTER (WHERE p.statut = 'RESERVEE') / NULLIF(count(p.id), 0), 1), 0)::float8"


@router.get("/remplissage", response_model=list[RemplissageSeanceOut])
def remplissage_par_seance(
    film_id: int | None = Query(None, description="Ne garder que les séances de ce film"),
    jour: date | None = Query(None, description="Ne garder que les séances de ce jour (AAAA-MM-JJ)"),
    conn: Connection = Depends(get_connection),
):
    """Taux de remplissage de chaque séance, des plus remplies aux moins remplies."""
    return conn.execute(
        f"""
        SELECT s.id AS seance_id, f.titre AS titre_film, s.salle, s.date_heure_debut,
               count(p.id) AS places_total,
               count(p.id) FILTER (WHERE p.statut = 'RESERVEE') AS places_reservees,
               {TAUX} AS taux_remplissage
        FROM seances s
        JOIN films f ON f.id = s.film_id
        LEFT JOIN places p ON p.seance_id = s.id
        WHERE (%(film_id)s::int IS NULL OR s.film_id = %(film_id)s)
          AND (%(jour)s::date IS NULL OR s.date_heure_debut::date = %(jour)s)
        GROUP BY s.id, f.titre
        ORDER BY taux_remplissage DESC, s.date_heure_debut
        """,
        {"film_id": film_id, "jour": jour},
    ).fetchall()


@router.get("/remplissage/synthese", response_model=SyntheseRemplissageOut)
def synthese_remplissage(conn: Connection = Depends(get_connection)):
    """Remplissage global et jour par jour, pour repérer les pics d'affluence."""
    par_jour = conn.execute(
        f"""
        SELECT s.date_heure_debut::date AS jour,
               count(DISTINCT s.id) AS nb_seances,
               count(p.id) AS places_total,
               count(p.id) FILTER (WHERE p.statut = 'RESERVEE') AS places_reservees,
               {TAUX} AS taux_remplissage
        FROM seances s
        LEFT JOIN places p ON p.seance_id = s.id
        GROUP BY jour
        ORDER BY jour
        """
    ).fetchall()
    total = sum(j["places_total"] for j in par_jour)
    reservees = sum(j["places_reservees"] for j in par_jour)
    return {
        "nb_seances": sum(j["nb_seances"] for j in par_jour),
        "places_total": total,
        "places_reservees": reservees,
        "taux_remplissage": round(100 * reservees / total, 1) if total else 0,
        "par_jour": par_jour,
    }


@router.get("/reservations", response_model=list[ReservationAdminOut])
def lister_reservations(
    seance_id: int | None = Query(None, description="Ne garder que les réservations de cette séance"),
    conn: Connection = Depends(get_connection),
):
    """Toutes les réservations, les plus récentes en premier."""
    return conn.execute(
        """
        SELECT r.id, r.code_billet, r.statut, r.date_reservation, u.email,
               f.titre AS titre_film, s.salle, s.date_heure_debut, p.numero_place
        FROM reservations r
        JOIN utilisateurs u ON u.id = r.utilisateur_id
        JOIN seances s ON s.id = r.seance_id
        JOIN films f ON f.id = s.film_id
        JOIN places p ON p.id = r.place_id
        WHERE (%(seance_id)s::int IS NULL OR r.seance_id = %(seance_id)s)
        ORDER BY r.date_reservation DESC
        """,
        {"seance_id": seance_id},
    ).fetchall()
