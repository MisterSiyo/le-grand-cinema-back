"""Données de démonstration : python -m app.seed

Ne fait rien si la base contient déjà des films.
Les mots de passe des deux comptes viennent du fichier .env.
"""
import sys

from app.config import get_settings
from app.database import get_pool
from app.security import hash_password

NB_PLACES = 50

FILMS = [
    ("Le Voyage de Chihiro", "Une fillette entre dans un monde habité par des esprits.", 125, "Animation"),
    ("Blade Runner 2049", "Un officier de police découvre un secret enfoui depuis trente ans.", 164, "Science-fiction"),
    ("La La Land", "Un pianiste de jazz et une comédienne vivent leur histoire à Los Angeles.", 128, "Comédie musicale"),
    ("Parasite", "Une famille pauvre s'infiltre dans le quotidien d'une famille riche.", 132, "Thriller"),
    ("Whiplash", "Un jeune batteur de jazz face à un professeur intransigeant.", 107, "Drame"),
]

# (index du film, salle, jours à partir d'aujourd'hui, heure, tarif)
SEANCES = [
    (0, "Salle 1", 1, "14:00", 8.50), (0, "Salle 1", 2, "16:30", 8.50),
    (1, "Salle 2", 1, "18:00", 10.00), (1, "Salle 2", 2, "21:00", 10.00),
    (2, "Salle 1", 1, "20:30", 9.00), (2, "Salle 3", 3, "19:00", 9.00),
    (3, "Salle 3", 1, "17:00", 9.50), (3, "Salle 2", 3, "20:00", 9.50),
    (4, "Salle 3", 2, "21:15", 8.00), (4, "Salle 1", 3, "18:30", 8.00),
]


def main() -> None:
    settings = get_settings()
    if not settings.seed_admin_password or not settings.seed_user_password:
        sys.exit("Renseigner SEED_ADMIN_PASSWORD et SEED_USER_PASSWORD dans le fichier .env")

    pool = get_pool()
    with pool.connection() as conn:
        if conn.execute("SELECT count(*) AS n FROM films").fetchone()["n"]:
            print("La base contient déjà des données, rien à faire.")
            return

        conn.execute(
            """
            INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe_hash, role) VALUES
            ('Admin', 'Cinéma', 'admin@legrandcinema.fr', %s, 'ADMIN'),
            ('Dupont', 'Marie', 'user@legrandcinema.fr', %s, 'USER')
            """,
            (hash_password(settings.seed_admin_password), hash_password(settings.seed_user_password)),
        )
        film_ids = [
            conn.execute(
                "INSERT INTO films (titre, description, duree_minutes, categorie) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                film,
            ).fetchone()["id"]
            for film in FILMS
        ]
        for film_index, salle, jours, heure, tarif in SEANCES:
            seance_id = conn.execute(
                """
                INSERT INTO seances (film_id, salle, date_heure_debut, tarif)
                VALUES (%s, %s, (CURRENT_DATE + %s * INTERVAL '1 day') + %s::time, %s)
                RETURNING id
                """,
                (film_ids[film_index], salle, jours, heure, tarif),
            ).fetchone()["id"]
            conn.execute(
                "INSERT INTO places (seance_id, numero_place) SELECT %s, generate_series(1, %s)",
                (seance_id, NB_PLACES),
            )
    pool.close()
    print(f"{len(FILMS)} films, {len(SEANCES)} séances, {len(SEANCES) * NB_PLACES} places, 2 comptes créés.")


if __name__ == "__main__":
    main()
