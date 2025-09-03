import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import gspread

from config import GOOGLE_CREDENTIALS_JSON, SCOPES

_credentials = None

def get_credentials():
    """Carga y devuelve las credenciales de Google desde la configuración."""
    global _credentials
    if _credentials:
        return _credentials

    if not GOOGLE_CREDENTIALS_JSON:
        raise ValueError("El secreto GOOGLE_CREDENTIALS_JSON no está presente en la configuración.")

    try:
        google_creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
        _credentials = Credentials.from_service_account_info(google_creds_dict, scopes=SCOPES)
        return _credentials
    except Exception as e:
        print(f"ERROR CRÍTICO: No se pudieron cargar las credenciales de Google. Error: {e}")
        raise

def get_sheets_client():
    """Devuelve un cliente de Google Sheets autenticado."""
    credentials = get_credentials()
    return build('sheets', 'v4', credentials=credentials)

def get_drive_client():
    """Devuelve un cliente de Google Drive autenticado."""
    credentials = get_credentials()
    return build('drive', 'v3', credentials=credentials)

def get_gspread_client():
    """Devuelve un cliente de gspread autenticado."""
    credentials = get_credentials()
    return gspread.authorize(credentials)
