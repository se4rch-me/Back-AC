import json
import io
from googleapiclient.http import MediaIoBaseUpload

from google_clients import get_sheets_client, get_drive_client
from config import SPREADSHEET_ID, SHEET_NAME, DRIVE_FOLDER_ID

def ingest_survey(data_str, files):
    """
    Procesa los datos de la encuesta, los guarda en Google Sheets y sube las fotos a Drive.
    """
    service_sheets = get_sheets_client()
    service_drive = get_drive_client()

    # 1. Procesar y aplanar los datos JSON
    datos = json.loads(data_str)
    print("Paso 2: Datos JSON decodificados.")

    fila_para_sheets = _prepare_row_for_sheets(datos)
    print("Paso 3: Fila de datos preparada para Google Sheets.")

    # 2. Escribir en Google Sheets
    service_sheets.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:Z",
        valueInputOption='USER_ENTERED',
        body={'values': [fila_para_sheets]}
    ).execute()
    print("Paso 4: Datos escritos en Google Sheets.")

    # 3. Procesar y subir imágenes
    pozo_numero = datos.get('pozo_numero', 'SIN_ID')
    if files:
        print(f"Paso 5: Procesando {len(files)} imágenes para el pozo {pozo_numero}.")
        _upload_photos(service_drive, files, pozo_numero)
        print("Paso 6: Imágenes subidas a Google Drive.")
    else:
        print("Paso 5 y 6: No se enviaron imágenes.")

def _prepare_row_for_sheets(datos):
    """Prepara una lista de valores a partir del JSON para insertar en la hoja de cálculo."""
    return [
        datos.get('fecha'),
        datos.get('consecutivo'),
        datos.get('direccion'),
        datos.get('levanto'),
        datos.get('pozo_numero'),
        datos.get('tipo_sistema'),
        datos.get('tipo_pozo'),
        datos.get('tapa', {}).get('existe'),
        datos.get('tapa', {}).get('tipo'),
        datos.get('tapa', {}).get('estado'),
        datos.get('tapa', {}).get('diagnostico'),
        datos.get('cargue', {}).get('existe'),
        datos.get('cargue', {}).get('estado'),
        datos.get('cargue', {}).get('diagnostico'),
        datos.get('cilindro', {}).get('material'),
        datos.get('cilindro', {}).get('estado'),
        datos.get('cilindro', {}).get('diagnostico'),
        datos.get('canuela', {}).get('estado'),
        datos.get('canuela', {}).get('diagnostico'),
        datos.get('escalones', {}).get('existe'),
        datos.get('escalones', {}).get('tipo'),
        datos.get('escalones', {}).get('estado'),
        datos.get('escalones', {}).get('diagnostico'),
        datos.get('estado_general_pozo'),
        datos.get('observaciones'),
        json.dumps(datos.get('conexiones', [])), # Convertir a string JSON
        'Pendiente' # Estado inicial
    ]

def _upload_photos(service_drive, files, pozo_numero):
    """Sube una lista de archivos a una carpeta de Google Drive."""
    for i, foto in enumerate(files, 1):
        file_metadata = {
            'name': f"{pozo_numero}-{i}",
            'parents': [DRIVE_FOLDER_ID]
        }
        media = MediaIoBaseUpload(io.BytesIO(foto.read()), mimetype=foto.mimetype)
        service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
