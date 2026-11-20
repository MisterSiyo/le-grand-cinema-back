-- Création des tables de la base Le Grand Cinéma (PostgreSQL).
-- Lancement : psql -U postgres -d le_grand_cinema -f database/init.sql
-- Le script peut être relancé, les tables existantes ne sont pas touchées.

-- Spectateurs et administrateurs
CREATE TABLE IF NOT EXISTS utilisateurs (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nom               VARCHAR(100) NOT NULL,
    prenom            VARCHAR(100) NOT NULL,
    email             VARCHAR(255) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role              VARCHAR(20)  NOT NULL DEFAULT 'USER',
    date_creation     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Films
CREATE TABLE IF NOT EXISTS films (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre         VARCHAR(255) NOT NULL,
    description   TEXT,
    duree_minutes INTEGER      NOT NULL CHECK (duree_minutes > 0),
    categorie     VARCHAR(100)
);

-- Séances : un film dans une salle à une date et une heure
CREATE TABLE IF NOT EXISTS seances (
    id                INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    film_id           INTEGER       NOT NULL REFERENCES films (id) ON DELETE CASCADE,
    salle             VARCHAR(50)   NOT NULL,
    date_heure_debut  TIMESTAMP     NOT NULL,
    tarif             NUMERIC(6, 2) NOT NULL CHECK (tarif >= 0)
);

CREATE INDEX IF NOT EXISTS idx_seances_film_id ON seances (film_id);

-- Places d'une séance. Un numéro de place est unique dans une séance.
CREATE TABLE IF NOT EXISTS places (
    id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    seance_id     INTEGER     NOT NULL REFERENCES seances (id) ON DELETE CASCADE,
    numero_place  INTEGER     NOT NULL CHECK (numero_place > 0),
    statut        VARCHAR(20) NOT NULL DEFAULT 'LIBRE',
    CONSTRAINT uq_places_seance_numero UNIQUE (seance_id, numero_place)
);

-- Réservations : une place réservée par un utilisateur
CREATE TABLE IF NOT EXISTS reservations (
    id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilisateur_id   INTEGER     NOT NULL REFERENCES utilisateurs (id) ON DELETE RESTRICT,
    seance_id        INTEGER     NOT NULL REFERENCES seances (id) ON DELETE CASCADE,
    place_id         INTEGER     NOT NULL REFERENCES places (id) ON DELETE CASCADE,
    code_billet      VARCHAR(64) NOT NULL UNIQUE,
    statut           VARCHAR(20) NOT NULL DEFAULT 'CONFIRMEE',
    date_reservation TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reservations_utilisateur_id ON reservations (utilisateur_id);
CREATE INDEX IF NOT EXISTS idx_reservations_seance_id      ON reservations (seance_id);
CREATE INDEX IF NOT EXISTS idx_reservations_place_id       ON reservations (place_id);
