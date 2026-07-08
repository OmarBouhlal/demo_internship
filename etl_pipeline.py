"""
__author__ = "myName"
Pipeline ETL : Du CSV nettoyé vers PostgreSQL relationnel
"""

import pandas as pd
import os
from sqlalchemy import create_engine, text
from sqlalchemy.dialects.postgresql import insert

# Configuration de la connexion PostgreSQL
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS")
if not DB_PASS:
    raise RuntimeError("DB_PASS is required")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "alomrane_db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def clean_text(text_val):
    """Supprime le bruit textuel (les doublons séparés par ' ... ')."""
    if pd.isna(text_val):
        return None
    return str(text_val).split(' ... ')[0].strip()

def run_etl(csv_path="al_omrane_group.csv"):
    print("🧹 Démarrage de l'ETL (Extraction & Transformation)...",flush=True)
    
    # 1. EXTRACTION
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"❌ Fichier {csv_path} introuvable.")
        return

    # 2. TRANSFORMATION (Nettoyage)
    # Garder uniquement Al Omrane
    df = df[df['organisme'].str.contains('OMRANE', case=False, na=False)].copy()
    
    # Nettoyage des textes
    df['objet'] = df['objet'].apply(clean_text)
    df['lieu_execution'] = df['lieu_execution'].apply(clean_text)
    
    # Typage des dates
    df['date_limite'] = pd.to_datetime(df['date_limite'], format='%d/%m/%Y %H:%M', errors='coerce')
    
    # Suppression des lignes sans référence technique (clé primaire obligatoire)
    df = df.dropna(subset=['ref_interne'])
    
    print(f"✅ Données nettoyées. {len(df)} lignes prêtes pour l'insertion.")
    
    # 3. CHARGEMENT (Load vers PostgreSQL)
    print("🔌 Connexion à la base de données...")
    engine = create_engine(DATABASE_URL)
    
    # 3. CHARGEMENT (Load vers PostgreSQL)
    print("🔌 Connexion et insertion dans la base de données...")
    from sqlalchemy import MetaData, Table
    
    metadata = MetaData()
    # On définit explicitement la table pour SQLAlchemy
    appel_offre_table = Table(
        'appel_offre', metadata,
        autoload_with=engine
    )
    
    with engine.begin() as conn: # 'begin' gère le commit automatiquement
        # A. Gestion des filiales
        filiales_uniques = df['organisme'].dropna().unique()
        for filiale_nom in filiales_uniques:
            conn.execute(text("""
                INSERT INTO filiale (nom_organisme) 
                VALUES (:nom) 
                ON CONFLICT (nom_organisme) DO NOTHING;
            """), {"nom": filiale_nom})
        
        # B. Récupération des IDs
        filiales_db = pd.read_sql("SELECT id_filiale, nom_organisme FROM filiale", conn)
        filiale_map = dict(zip(filiales_db['nom_organisme'], filiales_db['id_filiale']))
        
        # C. Mapping
        df['id_filiale'] = df['organisme'].map(filiale_map)
        donnees_a_inserer = df[[
            'ref_interne', 'reference', 'objet', 'categorie', 
            'lieu_execution', 'date_limite', 'lien_detail', 'id_filiale'
        ]].rename(columns={'reference': 'reference_publique'})
        
        # D. Upsert propre
        records = donnees_a_inserer.to_dict(orient='records')
        
        stmt = insert(appel_offre_table).values(records)
        
        # Définition de l'action en cas de conflit sur la clé primaire 'ref_interne'
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['ref_interne'],
            set_={
                'reference_publique': stmt.excluded.reference_publique,
                'objet': stmt.excluded.objet,
                'categorie': stmt.excluded.categorie,
                'date_limite': stmt.excluded.date_limite,
                'lieu_execution': stmt.excluded.lieu_execution
            }
        )
        
        conn.execute(upsert_stmt)

    print("🚀 ETL terminé ! Données insérées/mises à jour dans PostgreSQL avec succès.")

if __name__ == "__main__":
    run_etl()
