import streamlit as st
import pandas as pd
from twilio.rest import Client

# Configuration Streamlit & Twilio depuis les secrets
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]
FORM_URL = st.secrets["FORM_URL"]
users = { 
    "admin": st.secrets["admin"], 
    "user1": st.secrets["user1"], 
    "user2": st.secrets["user2"]
}

# Authentification
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
            st.rerun()
        else:
            st.error("❌ Identifiants incorrects. Veuillez réessayer.")

else:
    # PAGE PRINCIPALE - Interface d'envoi de SMS
    st.title(f"📩 Envoi de SMS - Connecté en tant que {st.session_state['user']}")

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    # Section : Upload CSV ou saisie manuelle des numéros
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

    # Vérification des numéros (seuls les +33 sont autorisés)
    valid_numbers = [num for num in phone_numbers if num.startswith("+33")]
    invalid_numbers = [num for num in phone_numbers if not num.startswith("+33")]

    # Affichage des erreurs pour les numéros invalides
    if invalid_numbers:
        st.error("❌ Les numéros suivants ne sont **pas valides** (seuls les numéros français +33 sont autorisés) :")
        for num in invalid_numbers:
            st.write(f"🔴 {num}")

    # Bouton d'envoi des SMS
    if st.button("📤 Envoyer les SMS") and valid_numbers:
        for number in valid_numbers:
            try:
                message = client.messages.create(
                    body=f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}",
                    from_=TWILIO_PHONE_NUMBER,
                    to=number
                )
                st.success(f"✅ SMS envoyé à {number}")
            except Exception as e:
                st.error(f"⚠️ Erreur d'envoi à {number} : {e}")

    # Déconnexion
    if st.button("🚪 Se déconnecter"):
        st.session_state["authentication_status"] = False
        st.rerun()
