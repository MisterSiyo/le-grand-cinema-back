import pytest
from fastapi.testclient import TestClient

from app.database import close_pool, get_pool
from app.main import app
from app.security import create_token, hash_password

NB_UTILISATEURS_TEST = 5
EMAIL_TEST = "test.concurrence.{}@example.com"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def utilisateurs_test():
    """Crée quelques utilisateurs temporaires et renvoie un en-tête d'authentification pour chacun."""
    with get_pool().connection() as conn:
        entetes = []
        for i in range(NB_UTILISATEURS_TEST):
            user = conn.execute(
                "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe_hash) "
                "VALUES ('Test', 'Test', %s, %s) RETURNING id, role",
                (EMAIL_TEST.format(i), hash_password("motdepasse-test")),
            ).fetchone()
            entetes.append({"Authorization": "Bearer " + create_token(user["id"], user["role"])})
    yield entetes
    with get_pool().connection() as conn:
        conn.execute(
            "DELETE FROM reservations WHERE utilisateur_id IN "
            "(SELECT id FROM utilisateurs WHERE email LIKE 'test.concurrence.%')"
        )
        conn.execute("DELETE FROM utilisateurs WHERE email LIKE 'test.concurrence.%'")


@pytest.fixture
def place_libre(client):
    """Une place libre d'une séance à venir, remise à LIBRE à la fin du test."""
    with get_pool().connection() as conn:
        place = conn.execute(
            """
            SELECT p.id, p.seance_id FROM places p JOIN seances s ON s.id = p.seance_id
            WHERE p.statut = 'LIBRE' AND s.date_heure_debut > now()
            ORDER BY p.id LIMIT 1
            """
        ).fetchone()
    yield place
    with get_pool().connection() as conn:
        conn.execute("UPDATE places SET statut = 'LIBRE' WHERE id = %s", (place["id"],))


def pytest_sessionfinish(session, exitstatus):
    close_pool()
