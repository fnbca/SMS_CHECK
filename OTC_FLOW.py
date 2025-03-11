import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from twilio.rest import Client
import datetime

# 🔹 Charger les credentials depuis Streamlit Secrets
POSTGRES_USER = st.secrets["POSTGRES_USER"]
POSTGRES_PASSWORD = st.secrets["POSTGRES_PASSWORD"]
POSTGRES_HOST = st.secrets["POSTGRES_HOST"]
POSTGRES_PORT = st.secrets["POSTGRES_PORT"]
POSTGRES_DATABASE = st.secrets["POSTGRES_DATABASE"]
SSL_MODE = st.secrets["SSL_MODE"]

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]
FORM_URL = st.secrets["FORM_URL"]

USERS = {
    "admin": st.secrets["admin"],
    "user1": st.secrets["user1"],
    "user2": st.secrets["user2"],
}

# 🔹 Construire l'URL PostgreSQL
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode={SSL_MODE}"
engine = create_engine(DATABASE_URL)

# 🔹 Authentification utilisateur
def authenticate():
    st.title("🔐 Connexion requise")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")
    if st.button("🔑 Se connecter"):
        if username in USERS and USERS[username] == password:
            st.session_state["authenticated"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects.")
authenticate()

if "authenticated" not in st.session_state:
    st.stop()

# 🔹 Interface principale après connexion
st.title(f"📩 Envoi de SMS - Connecté en tant que {st.session_state['user']}")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# 📂 Upload CSV ou saisie manuelle des numéros
uploaded_file = st.file_uploader("📂 Téléchargez un fichier CSV avec une colonne 'phone_number'", type=["csv"])
manual_numbers = st.text_area("✍️ Ou entrez les numéros (séparés par une virgule)")

phone_numbers = []

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if "phone_number" in df.columns:
        phone_numbers = df["phone_number"].astype(str).tolist()
    else:
        st.error("⚠️ Le fichier CSV doit contenir une colonne **'phone_number'**.")

if manual_numbers:
    phone_numbers += [num.strip() for num in manual_numbers.split(",")]

# 🔹 Vérification des numéros (seuls les +33 sont autorisés)
valid_numbers = [num for num in phone_numbers if num.startswith("+33")]
invalid_numbers = [num for num in phone_numbers if not num.startswith("+33")]

# 🔹 Affichage des erreurs pour les numéros invalides
if invalid_numbers:
    st.error("❌ Les numéros suivants ne sont **pas valides** (seuls les numéros français +33 sont autorisés) :")
    for num in invalid_numbers:
        st.write(f"🔴 {num}")

# 🔹 Bouton d'envoi des SMS
if st.button("📤 Envoyer les SMS") and valid_numbers:
    for number in valid_numbers:
        try:
            message = client.messages.create(
                body=f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}",
                from_=TWILIO_PHONE_NUMBER,
                to=number
            )

            with engine.connect() as connection:
                query = text("""
                    INSERT INTO sms_logs (utilisateur, numero, message, url, statut, date_heure)
                    VALUES (:utilisateur, :numero, :message, :url, :statut, :date_heure)
                """)
                connection.execute(query, {
                    "utilisateur": st.session_state["user"],
                    "numero": number,
                    "message": f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}",
                    "url": FORM_URL,
                    "statut": "Envoyé",
                    "date_heure": datetime.datetime.now()
                })

            st.success(f"✅ SMS envoyé à {number}")
        except Exception as e:
            st.error(f"⚠️ Erreur d'envoi à {number} : {e}")

# 🔹 Affichage de l'historique des SMS envoyés
st.subheader("📊 Historique des SMS envoyés")

def get_sms_logs():
    with engine.connect() as connection:
        query = text("SELECT * FROM sms_logs ORDER BY date_heure DESC")
        result = connection.execute(query)
        return result.fetchall()

logs = get_sms_logs()

if logs:
    df_logs = pd.DataFrame(logs, columns=["ID", "Utilisateur", "Numéro", "Message", "URL", "Statut", "Date & Heure"])
    st.dataframe(df_logs)
else:
    st.info("📌 Aucun SMS envoyé pour le moment.")

# 🔹 Bouton de déconnexion
if st.button("🚪 Se déconnecter"):
    st.session_state["authenticated"] = False
    st.rerun()
