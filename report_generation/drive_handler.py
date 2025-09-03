import io
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from google_clients import get_drive_client
from config import MASTER_REPORT_ID, DRIVE_FOLDER_ID

def download_master_report():
    """Descarga el archivo de reporte maestro desde Google Drive y lo devuelve como un buffer en memoria."""
    print("Descargando reporte maestro desde Google Drive...")
    service = get_drive_client()
    request = service.files().get_media(fileId=MASTER_REPORT_ID)
    file_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(file_buffer, request)
    
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Descarga: {int(status.progress() * 100)}%.")
        
    file_buffer.seek(0)
    print("Reporte maestro descargado.")
    return file_buffer

def download_photo(pozo_numero):
    """Descarga la primera foto encontrada para un número de pozo específico."""
    print(f"  - Buscando foto para el pozo {pozo_numero} en Drive...")
    service = get_drive_client()
    query = f"'{DRIVE_FOLDER_ID}' in parents and name starts with '{pozo_numero}-'"
    response = service.files().list(q=query, fields="files(id, name)").execute()
    files = response.get('files', [])
    
    if not files:
        print(f"  - Advertencia: No se encontró una foto para el pozo {pozo_numero}.")
        return None

    foto_id = files[0].get('id')
    print(f"  - Descargando foto '{files[0].get('name')}'...")
    request = service.files().get_media(fileId=foto_id)
    buffer_foto = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer_foto, request)
    
    done = False
    while not done:
        _, done = downloader.next_chunk()
        
    buffer_foto.seek(0)
    return buffer_foto

def update_master_report(file_buffer):
    """Actualiza el archivo de reporte maestro en Google Drive con el contenido del buffer."""
    print(f"Actualizando el archivo maestro en Google Drive...")
    service = get_drive_client()
    media = MediaIoBaseUpload(file_buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    service.files().update(fileId=MASTER_REPORT_ID, media_body=media).execute()
    print("¡Archivo maestro actualizado con éxito!")
