import os
from dotenv import load_dotenv

# Carga las variables de entorno desde un archivo .env
load_dotenv()

# --- CONFIGURACIÓN DE GOOGLE ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')

# --- IDs DE GOOGLE ---
SPREADSHEET_ID = os.environ.get('SHEET_ID')
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID') # Carpeta para las FOTOS
REPORTS_FOLDER_ID = os.environ.get('REPORTS_FOLDER_ID') # Carpeta para los reportes generados
MASTER_REPORT_ID = os.environ.get('MASTER_REPORT_ID') # ID del archivo maestro de reportes

# --- CONFIGURACIÓN DE LA HOJA DE CÁLCULO ---
SHEET_NAME = 'Tabla_Maestra_Pozos'

# --- CONFIGURACIÓN DE REPORTES ---
TEMPLATE_PATH = 'ejemplo.xltx'
