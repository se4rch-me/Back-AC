import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuracin de Google API ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
GOOGLE_CREDENTIALS_JSON = os.environ.get('GOOGLE_CREDENTIALS_JSON')
GOOGLE_CREDENTIALS_JSON_BASE64 = os.getenv("GOOGLE_CREDENTIALS_JSON_BASE64")

# --- Configuracin de Google Sheets ---
SPREADSHEET_ID = os.environ.get('SHEET_ID')
WORKSHEET_NAME = "Tabla Maestra"

# --- Configuracin de Google Drive ---
MASTER_REPORT_ID = os.getenv("MASTER_REPORT_ID")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")
REPORTS_FOLDER_ID = os.getenv('REPORTS_FOLDER_ID')

# --- Configuracin de Reportes ---
TEMPLATE_SHEET_NAME = "PZ14"
TEMPLATE_PATH = 'ejemplo1.xltx'

# --- Constantes de Estado ---
PENDING_STATUS = "Pendiente"
GENERATED_STATUS = "Generado"

# --- Cabeceras de la Hoja de Clculo ---
SHEET_HEADERS = [
    "fecha", "consecutivo", "pozo_numero", "direccion", "levanto",
    "tipo_sistema", "tipo_pozo", "tapa_existe", "tapa_tipo", "tapa_estado",
    "tapa_diagnostico", "cargue_existe", "cargue_estado", "cargue_diagnostico",
    "cono_existe", "cono_estado", "cono_diagnostico", "cilindro_material",
    "cilindro_cual", "cilindro_estado", "cilindro_diagnostico", "canuela_estado",
    "canuela_diagnostico", "escalones_existe", "escalones_tipo", "escalones_estado",
    "escalones_diagnostico", "estado_general_pozo", "observaciones", "conexiones",
    "foto_url", "estado"
]