"""Plusieurs spectateurs réservent la même place au même moment : une seule réservation doit passer."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from app.database import get_pool
from app.main import app

pytestmark = pytest.mark.db


def test_une_seule_reservation_sur_une_place_demandee_en_meme_temps(utilisateurs_test, place_libre):
    donnees = {"seance_id": place_libre["seance_id"], "place_id": place_libre["id"]}
    depart = Barrier(len(utilisateurs_test))

    def reserver(entetes):
        client = TestClient(app)
        depart.wait()
        return client.post("/reservations", headers=entetes, json=donnees).status_code

    with ThreadPoolExecutor(max_workers=len(utilisateurs_test)) as pool:
        codes = list(pool.map(reserver, utilisateurs_test))

    with get_pool().connection() as conn:
        nb_reservations = conn.execute(
            "SELECT count(*) AS n FROM reservations WHERE place_id = %s", (place_libre["id"],)
        ).fetchone()["n"]

    assert codes.count(201) == 1, f"codes reçus : {codes}"
    assert nb_reservations == 1
