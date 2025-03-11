import streamlit as st
import pandas as pd
import sqlite3
import datetime
from twilio.rest import Client

# ✅ Charger les credentials depuis Streamlit Secrets
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]
FORM_URL = st.secrets["FORM_URL"]

# ✅ Liste des utilisateurs définis dans les secrets (Sans section [users])
users = {
    "admin": st.secrets["admin"],
    "user1": st.secrets["user1"],
    "user2": st.secrets["user2"]
}

# ✅ Création ou connexion à la base SQLite
conn = sqlite3.connect("sessions.db", check_same_thread=False)
cursor = conn.cursor()

# ✅ Création de la table pour stocker les logs d'activité
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sms_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        phone_number TEXT,
        message TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

# ✅ Fonction pour enregistrer une action dans la base
def log_sms_action(username, phone_number, message):
    cursor.execute("""
        INSERT INTO sms_logs (username, phone_number, message) 
        VALUES (?, ?, ?)
    """, (username, phone_number, message))
    conn.commit()

# ✅ Authentification
if "authentication_status" not in st.session_state:
    st.session_state["authentication_status"] = False

if not st.session_state["authentication_status"]:
    st.title("🔒 Connexion requise")
    username = st.text_input("Nom d'utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("🔑 Se connecter"):
        if username in users and users[username] == password:
            st.session_state["authentication_status"] = True
            st.session_state["user"] = username
            st.rerun()  # ✅ Mise à jour immédiate
        else:
            st.error("❌ Identifiants incorrects. Veuillez réessayer.")

else:
    # ✅ PAGE PRINCIPALE - Interface d'envoi de SMS
    st.title(f"📩 Envoi de SMS - Connecté en tant que {st.session_state['user']}")

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # 📌 Upload CSV ou saisie manuelle des numéros
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

    # ✅ Vérification des numéros (seuls les +33 sont autorisés)
    valid_numbers = [num for num in phone_numbers if num.startswith("+33")]
    invalid_numbers = [num for num in phone_numbers if not num.startswith("+33")]

    # 📌 Affichage des erreurs pour les numéros invalides
    if invalid_numbers:
        st.error("❌ Les numéros suivants ne sont **pas valides** (seuls les numéros français +33 sont autorisés) :")
        for num in invalid_numbers:
            st.write(f"🔴 {num}")

    # ✅ Bouton d'envoi des SMS
    if st.button("📤 Envoyer les SMS") and valid_numbers:
        for number in valid_numbers:
            try:
                message_content = f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}"
                message = client.messages.create(
                    body=message_content,
                    from_=TWILIO_PHONE_NUMBER,
                    to=number
                )

                # ✅ Enregistrer l'envoi dans la base
                log_sms_action(st.session_state["user"], number, message_content)

                st.success(f"✅ SMS envoyé à {number}")
            except Exception as e:
                st.error(f"⚠️ Erreur d'envoi à {number} : {e}")

    # ✅ Affichage de l'historique des SMS envoyés
    st.subheader("📊 Historique des SMS envoyés")
    logs = cursor.execute("SELECT * FROM sms_logs ORDER BY timestamp DESC").fetchall()

    if logs:
        df_logs = pd.DataFrame(logs, columns=["ID", "Utilisateur", "Numéro", "Message", "Date & Heure"])
        st.dataframe(df_logs)
    else:
        st.info("📌 Aucun SMS envoyé pour le moment.")

    # ✅ Bouton de déconnexion
    if st.button("🚪 Se déconnecter"):
        st.session_state["authentication_status"] = False
        st.rerun()
