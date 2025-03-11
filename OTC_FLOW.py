import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# 🔹 Charger les credentials depuis Streamlit Secrets
POSTGRES_USER = st.secrets["POSTGRES_USER"]
POSTGRES_PASSWORD = st.secrets["POSTGRES_PASSWORD"]
POSTGRES_HOST = st.secrets["POSTGRES_HOST"]
POSTGRES_PORT = st.secrets["POSTGRES_PORT"]
POSTGRES_DATABASE = st.secrets["POSTGRES_DATABASE"]
SSL_MODE = st.secrets["SSL_MODE"]

# 🔹 Construire l'URL PostgreSQL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode={SSL_MODE}"

# 🔹 Se connecter avec SQLAlchemy
engine = create_engine(DATABASE_URL)

# 🔹 Tester la connexion
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT NOW();"))
        current_time = result.fetchone()[0]
        st.success(f"✅ Connexion réussie ! Heure actuelle : {current_time}")
except Exception as e:
    st.error(f"❌ Erreur de connexion : {e}")
