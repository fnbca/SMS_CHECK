import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# ✅ Récupérer les informations de connexion depuis Streamlit Secrets
POSTGRES_USER = st.secrets["POSTGRES_USER"]
POSTGRES_PASSWORD = st.secrets["POSTGRES_PASSWORD"]
POSTGRES_HOST = st.secrets["POSTGRES_HOST"]
POSTGRES_PORT = st.secrets["POSTGRES_PORT"]
POSTGRES_DATABASE = st.secrets["POSTGRES_DATABASE"]

# ✅ Construire l'URL de connexion PostgreSQL (compatible SQLAlchemy)
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"

# ✅ Connexion via SQLAlchemy avec un pool de connexions
engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)

# ✅ Vérifier si la connexion fonctionne
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT NOW();"))
        current_time = result.fetchone()[0]
        st.success(f"✅ Connexion réussie ! Heure actuelle : {current_time}")
except Exception as e:
    st.error(f"❌ Échec de connexion : {e}")

# ✅ Fonction pour récupérer les logs
def get_sms_logs():
    with engine.connect() as connection:
        query = text("SELECT * FROM sms_logs ORDER BY timestamp DESC")
        result = connection.execute(query)
        return result.fetchall()

# ✅ Affichage des logs dans Streamlit
st.subheader("📊 Historique des SMS envoyés")
logs = get_sms_logs()

if logs:
    df_logs = pd.DataFrame(logs, columns=["ID", "Utilisateur", "Numéro", "Message", "Date & Heure"])
    st.dataframe(df_logs)
else:
    st.info("📌 Aucun SMS envoyé pour le moment.")
