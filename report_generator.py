import os
import gspread
import openpyxl
from io import BytesIO
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- 1. CONFIGURACIÓN INICIAL ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDENTIALS_FILE = 'credentials.json'

# IDs de tus recursos de Google (reemplazar con los tuyos)
SHEET_ID = '1k_q4CctzbMnqDb2CbIPm-LdHzBHCkOcnBEiWoK12YoQ' # ID de tu Google Sheet
SHEET_NAME = 'RESIDUALES' # Nombre exacto de la hoja
PHOTOS_FOLDER_ID = '1E60fCgvOQUFYwL3JRLD1VqXN1bbHal_N' # Carpeta donde la App sube las fotos
REPORTS_FOLDER_ID = '13JzhVuKSM-gjBtsZaLhgHFK5uRsz0jCd' # Carpeta para guardar los reportes terminados
TEMPLATE_PATH = 'ejemplo.xltx' # Nombre de tu archivo de plantilla Excel

# --- 2. MAPEO DE CELDAS (El cerebro del generador) ---
# Este diccionario traduce los nombres de columna de tu Google Sheet a celdas en el Excel.
# 'type': 'direct' -> Pega el valor directamente en la celda.
# 'type': 'options' -> Busca el valor y pone una 'X' en la celda correspondiente.
# --- 2. MAPEO DE CELDAS (El cerebro del generador) ---
# Copia y pega este diccionario completo en tu archivo report_generator.py
CELL_MAPPING = {
    # Datos Generales
    'Fecha': {'type': 'direct', 'cell': 'D3'},
    'Consecutivo': {'type': 'direct', 'cell': 'H3'},
    'Dirección': {'type': 'direct', 'cell': 'D4'},
    'Levanto': {'type': 'direct', 'cell': 'D5'},
    'Pozo Numero': {'type': 'direct', 'cell': 'D6'},
    'Cota Rasante': {'type': 'direct', 'cell': 'D7'},
    'Tipo Sistema': {
        'type': 'options',
        'values': {'Aguas Lluvia': 'D9', 'Aguas Residuales': 'F9', 'Combinado': 'H9'}
    },
    'Tipo de Pozo': {
        'type': 'options',
        'values': {'Pozo': 'D11', 'Camara': 'F11', 'Alivio': 'H11'}
    },

    # Tapa
    'Tapa Existe?': {
        'type': 'options',
        'values': {'Si': 'D16', 'No': 'F16'}
    },
    'Tipo de Tapa': {
        'type': 'options',
        'values': {
            'Ferroconcreto': 'D18', 'Concreto': 'F18', 'Hierro sin Bisagra': 'H18',
            'Hierro con bisagra': 'D19', 'Tapa Seguridad': 'F19', 'Tapa en fibra': 'H19'
        }
    },
    'Tapa Estado?': {
        'type': 'options',
        'values': {'Bueno': 'D21', 'Regular': 'F21', 'Malo': 'H21'}
    },
    'Tapa Diagnostico': {
        'type': 'options',
        'values': {'Cambiar': 'D23', 'Reparar': 'F23', 'No Requiere': 'H23'}
    },

    # Cargue
    'Cargue Existe?': {
        'type': 'options',
        'values': {'Si': 'D28', 'No': 'F28'}
    },
    'Cargue Estado?': {
        'type': 'options',
        'values': {
            'Bueno': 'D30', 'Regular': 'F30', 'Malo': 'H30',
            'Grietas': 'D31', 'Partido': 'F31', 'Hundido': 'H31'
        }
    },
    'Cargue Diagnostico': {
        'type': 'options',
        'values': {'Cambiar': 'D33', 'Reparar': 'F33', 'No Requiere': 'H33'}
    },

    # Cono
    'Cono Existe?': {
        'type': 'options',
        'values': {'Si': 'D38', 'No': 'F38'}
    },
    'Cono Estado?': {
        'type': 'options',
        'values': {
            'Bueno': 'D40', 'Regular': 'F40', 'Malo': 'H40',
            'Grietas': 'D41', 'Partido': 'F41', 'Hundido': 'H41'
        }
    },
    'Cono Diagnostico': {
        'type': 'options',
        'values': {'Cambiar': 'D43', 'Reparar': 'F43', 'No Requiere': 'H43'}
    },

    # Cilindro
    'Cilindro Material': {
        'type': 'options',
        'values': {'Mamposteria': 'D48', 'Concreto': 'F48', 'GRP': 'H48'}
    },
    'Cilindro Estado?': {
        'type': 'options',
        'values': {
            'Bueno': 'D50', 'Regular': 'F50', 'Malo': 'H50',
            'Grietas': 'D51', 'Partido': 'F51', 'Huecos': 'H51',
            'Sin Pañete': 'D52', 'Otro': 'F52' # 'Cual?' necesitará un campo de texto aparte
        }
    },
    'Cilindro Cual?': {'type': 'direct', 'cell': 'H52'}, # Campo para texto libre
    'Cilindro Diagnostico': {
        'type': 'options',
        'values': {'Cambiar': 'D54', 'Reparar': 'F54', 'No Requiere': 'H54'}
    },

    # Cañuela
    'Cañuela Estado?': {
        'type': 'options',
        'values': {
            'Bueno': 'D59', 'Regular': 'F59', 'Malo': 'H59',
            'Sedimentada': 'D60', 'Desgastada': 'F60', 'Socavacion': 'H60'
        }
    },
    'Cañuela Diagnostico': {
        'type': 'options',
        'values': {'Cambiar': 'D62', 'Reparar': 'F62', 'No Requiere': 'H62'}
    },

    # Conexiones Erradas
    'Conexiones Erradas': {'type': 'direct', 'cell': 'F64'},
    'Observaciones': {'type': 'direct', 'cell': 'C66'},
}

def generar_reporte_excel(datos_registro, plantilla_path):
    """
    Carga la plantilla de Excel, la rellena con los datos de un registro
    y devuelve el archivo como un buffer en memoria.
    """
    try:
        workbook = openpyxl.load_workbook(plantilla_path)
        sheet = workbook.active
    except FileNotFoundError:
        print(f"Error Crítico: No se encontró la plantilla en la ruta: {plantilla_path}")
        return None, None

    # Iterar sobre el mapeo para rellenar el excel
    for campo, mapeo in CELL_MAPPING.items():
        valor = datos_registro.get(campo)
        if valor is None or valor == '':
            continue # Si no hay dato en la hoja de cálculo, no hacemos nada

        if mapeo['type'] == 'direct':
            sheet[mapeo['cell']] = valor
            print(f"  - Escribiendo '{valor}' en celda {mapeo['cell']}")

        elif mapeo['type'] == 'options':
            celda_a_marcar = mapeo['values'].get(valor)
            if celda_a_marcar:
                sheet[celda_a_marcar] = 'X' # Marcamos con una X
                print(f"  - Marcando celda {celda_a_marcar} para la opción '{valor}'")

    # Guardar el archivo en un buffer de memoria
    buffer = BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    pozo_numero = datos_registro.get('Pozo Numero', 'SIN_ID')
    filename = f'Reporte_Pozo_{pozo_numero}.xlsx'

    return buffer, filename

def upload_to_drive(file_buffer, filename, folder_id, drive_service):
    """Sube un archivo desde un buffer de memoria a una carpeta de Google Drive."""
    print(f"Subiendo '{filename}' a Google Drive...")
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(file_buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    print("¡Subida completada!")

def main():
    """Función principal que se ejecutará como tarea programada."""
    print("--- Iniciando Proceso de Generación de Reportes ---")
    try:
        # --- Autenticación ---
        credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Autenticación con Google exitosa.")

        # --- Leer datos de Google Sheets ---
        hoja = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        todos_los_datos = hoja.get_all_records() # Obtiene todos los datos como una lista de diccionarios

        # Encontrar la columna de "Estado" para poder actualizarla
        header = hoja.row_values(1)
        try:
            columna_estado_idx = header.index('Estado') + 1
        except ValueError:
            print("Error Crítico: No se encontró la columna 'Estado' en la hoja de cálculo.")
            return

        print(f"Se encontraron {len(todos_los_datos)} registros en total.")

        # --- Procesar cada registro ---
        # Iteramos con un índice para saber el número de la fila (sumamos 2 por el header y el índice base 0)
        for i, registro in enumerate(todos_los_datos):
            fila_numero = i + 2
            estado = registro.get('Estado')

            if estado == 'Pendiente':
                pozo_num = registro.get('Pozo Numero', 'N/A')
                print(f"\nProcesando registro en Fila {fila_numero} (Pozo: {pozo_num})...")

                # 1. Generar el archivo Excel en memoria
                reporte_buffer, filename = generar_reporte_excel(registro, TEMPLATE_PATH)

                if not reporte_buffer:
                    print(f"Error al generar el reporte para el pozo {pozo_num}. Saltando al siguiente.")
                    continue

                # 2. Subir el reporte a Google Drive
                upload_to_drive(reporte_buffer, filename, REPORTS_FOLDER_ID, drive_service)

                # 3. Actualizar el estado en Google Sheets a "Generado"
                print(f"Actualizando estado a 'Generado' en la fila {fila_numero}...")
                hoja.update_cell(fila_numero, columna_estado_idx, 'Generado')
                print("¡Estado actualizado!")

    except FileNotFoundError:
        print(f"Error Crítico: No se encuentra el archivo de credenciales '{CREDENTIALS_FILE}'.")
    except Exception as e:
        print(f"--- ¡Ocurrió un error inesperado! ---")
        print(f"Error: {e}")
        # En un sistema de producción, aquí podrías enviar una notificación por email.

    print("\n--- Proceso de Generación de Reportes Finalizado ---")

if __name__ == '__main__':
    main()