-- __author__ = "myName"
-- Schéma de base de données PostgreSQL pour le Reporting Al Omrane

-- Table des Acheteurs (Filiales du Holding)
CREATE TABLE filiale (
    id_filiale SERIAL PRIMARY KEY,
    nom_organisme VARCHAR(255) UNIQUE NOT NULL,
    acronyme VARCHAR(50)
);

-- Table des Marchés Publics (Appels d'offres)
CREATE TABLE appel_offre (
    ref_interne VARCHAR(50) PRIMARY KEY, -- Clé primaire (identifiant unique du portail)
    reference_publique VARCHAR(100) NOT NULL,
    objet TEXT NOT NULL,
    categorie VARCHAR(100),
    lieu_execution VARCHAR(255),
    date_limite TIMESTAMP,
    lien_detail TEXT,
    id_filiale INTEGER REFERENCES filiale(id_filiale) ON DELETE CASCADE
);

-- Index pour accélérer les recherches du Dashboard
CREATE INDEX idx_date_limite ON appel_offre(date_limite);
CREATE INDEX idx_categorie ON appel_offre(categorie);