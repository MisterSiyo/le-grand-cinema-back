from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import Connection

from app.database import get_connection
from app.schemas import FilmOut

router = APIRouter(prefix="/films", tags=["Films"])


@router.get("", response_model=list[FilmOut])
def lister_films(conn: Connection = Depends(get_connection)):
    """Liste les films du catalogue."""
    return conn.execute(
        "SELECT id, titre, description, duree_minutes, categorie FROM films ORDER BY titre"
    ).fetchall()


@router.get("/{film_id}", response_model=FilmOut)
def lire_film(film_id: int, conn: Connection = Depends(get_connection)):
    """Détail d'un film."""
    film = conn.execute(
        "SELECT id, titre, description, duree_minutes, categorie FROM films WHERE id = %s",
        (film_id,),
    ).fetchone()
    if film is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Film introuvable")
    return film
