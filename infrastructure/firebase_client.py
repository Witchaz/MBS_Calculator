import os
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():

    if firebase_admin._apps:
        return firestore.client()

    local_key_path = "mbs-calculator-firebase-adminsdk-fbsvc-86153c9e06.json"

    if os.path.exists(local_key_path):
        cred = credentials.Certificate(local_key_path)
        firebase_admin.initialize_app(cred)
    else:
        from streamlit import secrets
        firebase_secrets = dict(secrets["firebase_service_account"])
        firebase_secrets["private_key"] = (
            firebase_secrets["private_key"].replace("\\n", "\n")
        )
        cred = credentials.Certificate(firebase_secrets)
        firebase_admin.initialize_app(cred)

    return firestore.client()