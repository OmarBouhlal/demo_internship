import streamlit as st
import pandas as pd
import requests
import os

st.set_page_config(page_title="Dashboard Al Omrane", layout="wide")
st.title("📊 Reporting Automatisé - Groupe Al Omrane")

# Récupération des données via notre API
@st.cache_data
def load_data():
    api_base_url = os.getenv("API_BASE_URL", "http://api:8000")
    response = requests.get(f"{api_base_url}/api/marches", timeout=15)
    response.raise_for_status()
    return response.json()

try:
    data = load_data()
    df = pd.DataFrame(data)
except Exception as exc:
    st.error(f"Impossible de charger les données: {exc}")
    st.stop()

if df.empty:
    st.warning("Aucune donnée n'est disponible pour le moment.")
    st.stop()

if "nom_organisme" not in df.columns:
    st.error("La réponse de l'API ne contient pas la colonne 'nom_organisme'.")
    st.stop()

# Affichage des KPIs
col1, col2 = st.columns(2)
col1.metric("Total Marchés", len(df))
col2.metric("Filiales actives", df['nom_organisme'].nunique())

# Graphique : Nombre de marchés par filiale
st.subheader("Distribution des appels d'offres par filiale")
stats = df['nom_organisme'].value_counts()
st.bar_chart(stats)

# Tableau interactif
st.subheader("Détail des marchés")
st.dataframe(df)
