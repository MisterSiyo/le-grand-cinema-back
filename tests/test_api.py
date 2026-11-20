import pytest

pytestmark = pytest.mark.db


def test_sante(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_liste_des_films(client):
    reponse = client.get("/films")
    assert reponse.status_code == 200
    assert len(reponse.json()) > 0


def test_film_inconnu(client):
    assert client.get("/films/999999").status_code == 404


def test_seances_avec_places_libres(client):
    seance = client.get("/seances").json()[0]
    assert 0 <= seance["places_libres"] <= seance["places_total"]


def test_reservation_sans_connexion_refusee(client):
    assert client.post("/reservations", json={"seance_id": 1, "place_id": 1}).status_code == 401


def test_espace_admin_interdit_sans_connexion(client):
    assert client.get("/admin/remplissage").status_code == 401


def test_connexion_avec_mauvais_mot_de_passe(client):
    reponse = client.post("/auth/connexion", json={"email": "inconnu@example.com", "mot_de_passe": "x"})
    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Email ou mot de passe incorrect"


def test_espace_admin_interdit_a_un_utilisateur(client, utilisateurs_test):
    assert client.get("/admin/remplissage", headers=utilisateurs_test[0]).status_code == 403


def test_une_place_reservee_ne_peut_pas_etre_reservee_deux_fois(client, utilisateurs_test, place_libre):
    donnees = {"seance_id": place_libre["seance_id"], "place_id": place_libre["id"]}
    premiere = client.post("/reservations", headers=utilisateurs_test[0], json=donnees)
    seconde = client.post("/reservations", headers=utilisateurs_test[1], json=donnees)
    assert premiere.status_code == 201
    assert seconde.status_code == 409
