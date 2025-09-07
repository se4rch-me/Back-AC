import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import gspread

from config import GOOGLE_CREDENTIALS_JSON, SCOPES

# --- Constantes ---
# El archivo 'client_secret.json' que descargas de Google Cloud Console.
# Lo cargamos desde la variable de entorno que ya tenías configurada.
CLIENT_SECRETS_DICT = json.loads(GOOGLE_CREDENTIALS_JSON)
# Archivo para almacenar los tokens del usuario.
TOKEN_FILE = 'token.json' 

_credentials = None

def get_credentials():
    """
    Carga las credenciales del usuario desde el archivo token.json.
    Si el token ha expirado, lo refresca si es posible.
    Devuelve None si no hay un token válido.
    """
    global _credentials
    if _credentials and _credentials.valid:
        return _credentials

    if os.path.exists(TOKEN_FILE):
        _credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # Si las credenciales existen pero no son válidas (expiraron) y tenemos un refresh token
        if _credentials and not _credentials.valid and _credentials.refresh_token:
            try:
                print("Refrescando token de acceso expirado...")
                _credentials.refresh(Request())
                print("Token refrescado exitosamente.")
                # Guardamos las credenciales actualizadas (con el nuevo access token)
                save_credentials(_credentials)
            except Exception as e:
                print(f"Error al refrescar el token: {e}")
                # Si falla el refresh, es como no tener credenciales.
                # Forzamos una nueva autenticación eliminando el token corrupto.
                os.remove(TOKEN_FILE)
                return None
        return _credentials
    return None

def save_credentials(credentials):
    """Guarda las credenciales del usuario en el archivo token.json."""
    with open(TOKEN_FILE, 'w') as token:
        token.write(credentials.to_json())

def get_auth_flow(redirect_uri):
    """Crea y devuelve un objeto Flow para la autenticación."""
    return Flow.from_client_config(
        client_config=CLIENT_SECRETS_DICT,
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

def get_sheets_client():
    """Devuelve un cliente de Google Sheets autenticado."""
    credentials = get_credentials()
    if not credentials:
        raise Exception("Autenticación requerida. No se encontraron credenciales válidas.")
    return build('sheets', 'v4', credentials=credentials)

def get_drive_client():
    """Devuelve un cliente de Google Drive autenticado."""
    credentials = get_credentials()
    if not credentials:
        raise Exception("Autenticación requerida. No se encontraron credenciales válidas.")
    return build('drive', 'v3', credentials=credentials)

def get_gspread_client():
    """Devuelve un cliente de gspread autenticado."""
    credentials = get_credentials()
    if not credentials:
        raise Exception("Autenticación requerida. No se encontraron credenciales válidas.")
    return gspread.authorize(credentials)