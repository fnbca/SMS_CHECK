# import streamlit as st
# import pandas as pd
# from sqlalchemy import create_engine, text
# from twilio.rest import Client
# import datetime

# # 🔹 Charger les credentials depuis Streamlit Secrets
# POSTGRES_USER = st.secrets["POSTGRES_USER"]
# POSTGRES_PASSWORD = st.secrets["POSTGRES_PASSWORD"]
# POSTGRES_HOST = st.secrets["POSTGRES_HOST"]
# POSTGRES_PORT = st.secrets["POSTGRES_PORT"]
# POSTGRES_DATABASE = st.secrets["POSTGRES_DATABASE"]
# SSL_MODE = st.secrets["SSL_MODE"]

# TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
# TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
# TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]
# FORM_URL = st.secrets["FORM_URL"]

# USERS = {
#     "admin": st.secrets["admin"],
#     "user1": st.secrets["user1"],
#     "user2": st.secrets["user2"],
# }

# # 🔹 Construire l'URL PostgreSQL
# DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}?sslmode={SSL_MODE}"
# engine = create_engine(DATABASE_URL)

# # 🔹 Vérifier et créer la table sms_logs si elle n'existe pas
# def create_table_if_not_exists():
#     with engine.connect() as connection:
#         connection.execute(text("""
#             CREATE TABLE IF NOT EXISTS sms_logs (
#                 id SERIAL PRIMARY KEY,
#                 utilisateur TEXT,
#                 numero TEXT,
#                 message TEXT,
#                 url TEXT,
#                 statut TEXT,
#                 date_heure TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         """))

# create_table_if_not_exists()

# # 🔹 Gestion de la session utilisateur et navigation
# if "authenticated" not in st.session_state:
#     st.session_state["authenticated"] = False
# if "user" not in st.session_state:
#     st.session_state["user"] = None
# if "page" not in st.session_state:
#     st.session_state["page"] = "login"

# # 🔹 Page de connexion
# if st.session_state["page"] == "login":
#     st.title("🔐 Connexion requise")
#     username = st.text_input("Nom d'utilisateur")
#     password = st.text_input("Mot de passe", type="password")

#     if st.button("🔑 Se connecter"):
#         if username in USERS and USERS[username] == password:
#             st.session_state["authenticated"] = True
#             st.session_state["user"] = username
#             st.session_state["page"] = "sms"
#             st.rerun()
#         else:
#             st.error("❌ Identifiants incorrects.")

# # 🔹 Interface principale après connexion
# if st.session_state["authenticated"] and st.session_state["page"] == "sms":
#     st.title(f"📩 Envoi de SMS - Connecté en tant que {st.session_state['user']}")

#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

#     # 📂 Upload CSV ou saisie manuelle des numéros
#     uploaded_file = st.file_uploader("📂 Téléchargez un fichier CSV avec une colonne 'phone_number'", type=["csv"])
#     manual_numbers = st.text_area("✍️ Ou entrez les numéros (séparés par une virgule)")

#     phone_numbers = []

#     if uploaded_file:
#         df = pd.read_csv(uploaded_file)
#         if "phone_number" in df.columns:
#             phone_numbers = df["phone_number"].astype(str).tolist()
#         else:
#             st.error("⚠️ Le fichier CSV doit contenir une colonne **'phone_number'**.")

#     if manual_numbers:
#         phone_numbers += [num.strip() for num in manual_numbers.split(",")]

#     # 🔹 Vérification des numéros (seuls les +33 sont autorisés)
#     valid_numbers = [num for num in phone_numbers if num.startswith("+33")]
#     invalid_numbers = [num for num in phone_numbers if not num.startswith("+33")]

#     # 🔹 Affichage des erreurs pour les numéros invalides
#     if invalid_numbers:
#         st.error("❌ Les numéros suivants ne sont **pas valides** (seuls les numéros français +33 sont autorisés) :")
#         for num in invalid_numbers:
#             st.write(f"🔴 {num}")

#     # 🔹 Bouton d'envoi des SMS
#     if st.button("📤 Envoyer les SMS") and valid_numbers:
#         for number in valid_numbers:
#             try:
#                 message = client.messages.create(
#                     body=f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}",
#                     from_=TWILIO_PHONE_NUMBER,
#                     to=number
#                 )

#                 with engine.connect() as connection:
#                     query = text("""
#                         INSERT INTO sms_logs (utilisateur, numero, message, url, statut, date_heure)
#                         VALUES (:utilisateur, :numero, :message, :url, :statut, :date_heure)
#                     """)
#                     connection.execute(query, {
#                         "utilisateur": st.session_state["user"],
#                         "numero": number,
#                         "message": f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}",
#                         "url": FORM_URL,
#                         "statut": "Envoyé",
#                         "date_heure": datetime.datetime.now()
#                     })

#                 st.success(f"✅ SMS envoyé à {number}")
#             except Exception as e:
#                 st.error(f"⚠️ Erreur d'envoi à {number} : {e}")

#     # 🔹 Affichage de l'historique des SMS envoyés
#     st.subheader("📊 Historique des SMS envoyés")

#     def get_sms_logs():
#         with engine.connect() as connection:
#             query = text("SELECT * FROM sms_logs ORDER BY date_heure DESC")
#             result = connection.execute(query)
#             return result.fetchall()

#     logs = get_sms_logs()

#     if logs:
#         df_logs = pd.DataFrame(logs, columns=["ID", "Utilisateur", "Numéro", "Message", "URL", "Statut", "Date & Heure"])
#         st.dataframe(df_logs)
#     else:
#         st.info("📌 Aucun SMS envoyé pour le moment.")

#     # 🔹 Bouton de déconnexion
#     if st.button("🚪 Se déconnecter"):
#         st.session_state["authenticated"] = False
#         st.session_state["page"] = "login"
#         st.rerun()



import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import sql
from twilio.rest import Client

# 🚀 Configuration depuis les secrets de Streamlit
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = st.secrets["TWILIO_PHONE_NUMBER"]
FORM_URL = st.secrets["FORM_URL"]

DB_HOST = st.secrets["DB_HOST"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASSWORD = st.secrets["DB_PASSWORD"]
DB_PORT = st.secrets["DB_PORT"]

users = {
    "admin": st.secrets["admin"],
    "user1": st.secrets["user1"],
    "user2": st.secrets["user2"]
}

# 🚀 Connexion à la base de données
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

# 🚀 Création de la table si elle n'existe pas
def create_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_logs (
                id SERIAL PRIMARY KEY,
                utilisateur TEXT NOT NULL,
                numero TEXT NOT NULL,
                message TEXT NOT NULL,
                url TEXT NOT NULL,
                statut TEXT NOT NULL,
                date_heure TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la création de la table : {e}")

# 🚀 Fonction pour stocker un SMS envoyé dans la base
def log_sms(utilisateur, numero, message, url, statut):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sms_logs (utilisateur, numero, message, url, statut) 
            VALUES (%s, %s, %s, %s, %s);
        """, (utilisateur, numero, message, url, statut))

        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"⚠️ Erreur lors de l'insertion dans la base : {e}")

# 🚀 Fonction pour récupérer les logs des SMS envoyés
def get_sms_logs(utilisateur):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if utilisateur == "admin":
            query = "SELECT * FROM sms_logs ORDER BY date_heure DESC;"
        else:
            query = "SELECT * FROM sms_logs WHERE utilisateur = %s ORDER BY date_heure DESC;"

        cursor.execute(query, (utilisateur,) if utilisateur != "admin" else ())
        logs = cursor.fetchall()

        conn.commit()
        cursor.close()
        conn.close()
        
        return logs
    except Exception as e:
        st.error(f"⚠️ Erreur lors de la récupération des logs : {e}")
        return []

# 🚀 Authentification
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
            st.experimental_rerun()
        else:
            st.error("❌ Identifiants incorrects. Veuillez réessayer.")

else:
    # ✅ Création de la table au cas où elle n'existe pas
    create_table()

    # 🚀 Interface d'envoi de SMS
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

    # 🚀 Vérification des numéros (seuls les +33 sont autorisés)
    valid_numbers = [num for num in phone_numbers if num.startswith("+33")]
    invalid_numbers = [num for num in phone_numbers if not num.startswith("+33")]

    if invalid_numbers:
        st.error("❌ Les numéros suivants ne sont **pas valides** (seuls les numéros français +33 sont autorisés) :")
        for num in invalid_numbers:
            st.write(f"🔴 {num}")

    # 🚀 Envoi des SMS et stockage des logs
    if st.button("📤 Envoyer les SMS") and valid_numbers:
        for number in valid_numbers:
            try:
                message_body = f"Bonjour, veuillez remplir votre formulaire ici : {FORM_URL}"
                message = client.messages.create(
                    body=message_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=number
                )

                log_sms(st.session_state["user"], number, message_body, FORM_URL, "Envoyé")
                st.success(f"✅ SMS envoyé à {number}")

            except Exception as e:
                log_sms(st.session_state["user"], number, message_body, FORM_URL, f"Échec : {e}")
                st.error(f"⚠️ Erreur d'envoi à {number} : {e}")

    # 🚀 Affichage de l'historique des SMS
    st.title("📊 Historique des SMS envoyés")
    
    logs = get_sms_logs(st.session_state["user"])
    if logs:
        df_logs = pd.DataFrame(logs, columns=["ID", "Utilisateur", "Numéro", "Message", "URL", "Statut", "Date & Heure"])
        st.dataframe(df_logs)
    else:
        st.write("📭 Aucun SMS enregistré pour le moment.")

    # 🚪 Déconnexion
    if st.button("🚪 Se déconnecter"):
        st.session_state["authentication_status"] = False
        st.rerun()
