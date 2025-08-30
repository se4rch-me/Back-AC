import os
import json
from flask import Flask, request, jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

app = Flask(__name__)

# --- Configuración ---
# Es una mejor práctica leer estos valores de variables de entorno
# pero por ahora los dejamos aquí para claridad.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SPREADSHEET_ID = '1k_q4CctzbMnqDb2CbIPm-LdHzBHCkOcnBEiWoK12YoQ'
DRIVE_FOLDER_ID = '1E60fCgvOQUFYwL3JRLD1VqXN1bbHal_N'
SHEET_NAME = 'RESIDUALES' # Nombre de la hoja específica

@app.route('/')
def home():
    print("Solicitud GET en la raíz, todo en orden.")
    return "Servidor Flask para Reportes de Acueducto: ¡Activo!"

@app.route('/ingestar-encuesta', methods=['POST'])
def ingestar_encuesta():
    print("Paso 1: Solicitud POST recibida en /ingestar-encuesta.")

    try:
        if 'data' not in request.form:
            print("Error: 'data' no encontrado en el formulario.")
            return jsonify({'mensaje': 'Error: Campo de datos (data) no encontrado.'}), 400
        
        datos_json = request.form['data']
        datos_encuesta = json.loads(datos_json)
        print("Paso 2: Datos de encuesta decodificados.")
        
        # --- Autenticación con Google ---
        ruta_credenciales = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        print(f"Paso 3: Cargando credenciales desde {ruta_credenciales}")
        
        try:
            credentials = Credentials.from_service_account_file(ruta_credenciales, scopes=SCOPES)
            service_sheets = build('sheets', 'v4', credentials=credentials)
            service_drive = build('drive', 'v3', credentials=credentials)
            print("Paso 4: Credenciales y servicios de Google listos.")
        except FileNotFoundError:
            print("Error crítico: No se encontró el archivo 'credentials.json'.")
            return jsonify({'mensaje': 'Error de configuración del servidor: Faltan credenciales.'}), 500
        except Exception as e:
            print(f"Error al cargar credenciales o construir servicios: {e}")
            return jsonify({'mensaje': 'Error en la autenticación del servidor.'}), 500

        # --- Extracción de todos los datos del formulario ---
        # Usamos .get() para evitar errores si una clave no viene en el JSON
        print("Paso 5: Extrayendo datos del formulario.")
        fecha = datos_encuesta.get('fecha', '')
        consecutivo = datos_encuesta.get('consecutivo', '')
        direccion = datos_encuesta.get('direccion', '')
        levanto = datos_encuesta.get('levanto', '')
        pozo_numero = datos_encuesta.get('pozoNumero', '')
        cota_rasante = datos_encuesta.get('cotaRasante', '')
        tipo_sistema = datos_encuesta.get('tipoSistema', '')
        tipo_pozo = datos_encuesta.get('tipoPozo', '')
        
        # ... y así sucesivamente para todos los campos de 'Celdas formato acueducto.txt'
        # Esto es un ejemplo, hay que añadir todos los que falten.
        
        # Preparar la fila para Google Sheets en el orden correcto de las columnas
        # ¡IMPORTANTE! El orden aquí debe coincidir con el orden de las columnas en tu hoja.
        # Añadimos una columna 'Estado' al final para la gestión del reporte.
        fila = [
            fecha, consecutivo, direccion, levanto, pozo_numero, cota_rasante,
            tipo_sistema, tipo_pozo, # ... añadir el resto de campos ...
            'Pendiente' # Estado inicial para el generador de reportes
        ]
        
        # --- Escribir en Google Sheets ---
        print("Paso 6: Escribiendo datos en Google Sheets.")
        range_name = f'{SHEET_NAME}!A:Z' # Asegúrate de que el rango cubra todas tus columnas
        body = {'values': [fila]}
        
        service_sheets.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='USER_ENTERED', # 'USER_ENTERED' para que Sheets interprete los datos (ej. fechas)
            body=body
        ).execute()
        print("Paso 7: Datos escritos en Google Sheets.")
        
        # --- Subir fotos a Google Drive ---
        print("Paso 8: Procesando subida de fotos a Google Drive.")
        fotos = request.files.getlist('fotos')
        if fotos:
            for foto in fotos:
                print(f"Subiendo: {foto.filename}")
                file_metadata = {
                    'name': f"{pozo_numero}_{foto.filename}", # Renombramos la foto para identificarla
                    'parents': [DRIVE_FOLDER_ID]
                }
                media = MediaIoBaseUpload(io.BytesIO(foto.read()), mimetype=foto.mimetype, resumable=True)
                file = service_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print(f"Foto subida. ID de archivo: {file.get('id')}")
        else:
            print("No se enviaron fotos en esta solicitud.")
            
        print("Paso 9: Proceso completado exitosamente.")
        return jsonify({'mensaje': 'Datos y fotos recibidos y procesados correctamente.'}), 200

    except json.JSONDecodeError:
        print("Error: El campo 'data' no es un JSON válido.")
        return jsonify({'mensaje': 'Error: El formato de los datos es incorrecto (JSON inválido).'}), 400
    except Exception as e:
        print(f"Error inesperado en el servidor: {e}")
        return jsonify({'mensaje': f'Error interno del servidor: {e}'}), 500

if __name__ == '__main__':
    # Esto es para pruebas locales. PythonAnywhere usa su propio servidor.
    app.run(debug=True)