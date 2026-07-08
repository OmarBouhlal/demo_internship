from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
import pandas as pd
import os

app = FastAPI()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "alomrane_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS")
if not DB_PASS:
    raise RuntimeError("DB_PASS is required")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

@app.get("/api/marches")
def get_marches():
    # Récupère tous les marchés avec le nom de la filiale
    query = """
    SELECT a.*, f.nom_organisme 
    FROM appel_offre a 
    JOIN filiale f ON a.id_filiale = f.id_filiale
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_dict(orient="records")

@app.get("/api/stats")
def get_stats():
    # Agrégation automatique pour le dashboard
    query = """
    SELECT f.nom_organisme, count(a.ref_interne) as nb_marches
    FROM appel_offre a
    JOIN filiale f ON a.id_filiale = f.id_filiale
    GROUP BY f.nom_organisme
    """
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_dict(orient="records")
# Dans backend/main.py
if __name__ == "__main__":
    import uvicorn
    # Important : bind sur 0.0.0.0 pour être accessible depuis les autres conteneurs
    uvicorn.run(app, host="0.0.0.0", port=8000)
