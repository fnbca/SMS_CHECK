import streamlit as st
import os
import base64
import requests

# Chargement des clés API depuis les secrets Streamlit
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
API_URL = st.secrets["FIDEALIS_API_URL"]
API_KEY = st.secrets["FIDEALIS_API_KEY"]
ACCOUNT_KEY = st.secrets["FIDEALIS_ACCOUNT_KEY"]

# Fonction pour obtenir les coordonnées GPS à partir d'une adresse
def get_coordinates(address):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    return None, None

# Fonction pour se connecter à l'API Fidealis
def api_login():
    login_response = requests.get(
        f"{API_URL}?key={API_KEY}&call=loginUserFromAccountKey&accountKey={ACCOUNT_KEY}"
    )
    login_data = login_response.json()
    if 'PHPSESSID' in login_data:
        return login_data["PHPSESSID"]
    return None

# Fonction pour appeler l'API Fidealis
def api_upload_files(description, files, session_id):
    for i in range(0, len(files), 12):
        batch_files = files[i:i + 12]
        data = {
            "key": API_KEY,
            "PHPSESSID": session_id,
            "call": "setDeposit",
            "description": description,
            "type": "deposit",
            "hidden": "0",
            "sendmail": "1",
        }
        for idx, file in enumerate(batch_files, start=1):
            with open(file, "rb") as f:
                encoded_file = base64.b64encode(f.read()).decode("utf-8")
                data[f"filename{idx}"] = os.path.basename(file)
                data[f"file{idx}"] = encoded_file
        requests.post(API_URL, data=data)

# Interface utilisateur Streamlit
st.title("Formulaire de dépôt FIDEALIS pour RES-EC-104")

session_id = api_login()
if not session_id:
    st.error("Échec de la connexion à l'API.")
else:
    # Champs de saisie du formulaire
    beneficiary_name = st.text_input("Nom et prénom du bénéficiaire *", help="Noter le nom et prénom du bénéficiaire")

    invoice_photos = st.file_uploader(
        "Facture (Min: 4, Max: 20) *", accept_multiple_files=True, type=["jpg", "png"]
    )

    work_address = st.text_input("Adresse des travaux *", help="Merci de confirmer l'adresse des travaux")
    confirm_address = st.checkbox("Je confirme l'adresse des travaux *")

    luminaire_photos = st.file_uploader(
        "Photos Luminaires (Min: 1, Max: 10) *", accept_multiple_files=True, type=["jpg", "png"]
    )

    confirm_installation = st.checkbox("Je certifie que l’installation est complète et fonctionnelle *")

    if st.button("Soumettre"):
        if not beneficiary_name or not work_address:
            st.error("Veuillez remplir tous les champs obligatoires.")
        elif len(invoice_photos) < 4 or len(invoice_photos) > 20:
            st.error("Le nombre de photos de la facture doit être compris entre 4 et 20.")
        elif len(luminaire_photos) < 1 or len(luminaire_photos) > 10:
            st.error("Le nombre de photos des luminaires doit être compris entre 1 et 10.")
        elif not confirm_address:
            st.error("Veuillez confirmer l'adresse des travaux.")
        elif not confirm_installation:
            st.error("Veuillez certifier que l’installation est complète et fonctionnelle.")
        else:
            st.info("Récupération des coordonnées GPS...")

            # Récupérer la latitude et la longitude
            latitude, longitude = get_coordinates(work_address)
            if latitude is None or longitude is None:
                st.error("Impossible de récupérer les coordonnées GPS. Veuillez vérifier l'adresse.")
            else:
                st.info("Préparation de l'envoi...")

                # Sauvegarde des fichiers localement
                saved_files = []
                for idx, file in enumerate(invoice_photos + luminaire_photos):
                    save_path = f"{beneficiary_name}_temp_{idx + 1}.jpg"
                    with open(save_path, "wb") as f:
                        f.write(file.read())
                    saved_files.append(save_path)

                # Description pour l'API avec certification et coordonnées GPS
                description = (
                    f"SCELLÉ NUMERIQUE Bénéficiaire: {beneficiary_name}, "
                    f"Adresse des travaux: {work_address}, "
                    f"Coordonnées GPS: ({latitude}, {longitude}), "
                    f"Confirmation adresse: {'Oui' if confirm_address else 'Non'}, "
                    f"Certification installation: {'Oui' if confirm_installation else 'Non'}"
                )

                # Envoi des fichiers à l'API
                st.info("Envoi des données...")
                api_upload_files(description, saved_files, session_id)
                st.success("Données envoyées avec succès !")
