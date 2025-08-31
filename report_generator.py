import os
import gspread
import openpyxl
import json
from io import BytesIO
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- CONSTANTES ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SHEET_NAME = 'RESIDUALES'
TEMPLATE_PATH = 'ejemplo.xltx' 
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

# --- FUNCIONES DE AYUDA ---
def rellenar_hoja(sheet, datos_registro):
    """Toma una hoja de cálculo y la rellena con los datos de un registro."""
    print(f"  - Rellenando hoja '{sheet.title}'...")
    for campo, mapeo in CELL_MAPPING.items():
        valor = datos_registro.get(campo)
        if valor is None or valor == '':
            continue
        if mapeo['type'] == 'direct':
            sheet[mapeo['cell']] = valor
        elif mapeo['type'] == 'options':
            # Convertimos a string por si el valor en Sheets es numérico (ej. Si/No como 1/0)
            celda_a_marcar = mapeo['values'].get(str(valor))
            if celda_a_marcar:
                sheet[celda_a_marcar] = 'X'
    print(f"  - Hoja '{sheet.title}' rellenada.")

def upload_to_drive(file_buffer, filename, folder_id, drive_service):
    """Sube un archivo desde un buffer de memoria a una carpeta de Google Drive."""
    print(f"Subiendo '{filename}' a Google Drive...")
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaIoBaseUpload(file_buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print("¡Subida completada!")

# --- FUNCIÓN PRINCIPAL ---
def main():
    print("--- Iniciando Proceso de Generación de Reporte Consolidado ---")
    try:
        # --- 1. LEER VARIABLES DE ENTORNO ---
        # Toda la configuración se lee aquí, dentro de la función principal.
        SHEET_ID = os.environ.get('SHEET_ID')
        REPORTS_FOLDER_ID = os.environ.get('REPORTS_FOLDER_ID')
        google_creds_json_str = os.environ.get('GOOGLE_CREDENTIALS_JSON')

        if not all([SHEET_ID, REPORTS_FOLDER_ID, google_creds_json_str]):
            raise ValueError("Una o más variables de entorno (SHEET_ID, REPORTS_FOLDER_ID, GOOGLE_CREDENTIALS_JSON) no están configuradas.")

        # --- 2. AUTENTICACIÓN (El único y correcto método para GitHub Actions) ---
        google_creds_dict = json.loads(google_creds_json_str)
        credentials = Credentials.from_service_account_info(google_creds_dict, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Autenticación con Google exitosa.")

        # --- 3. PROCESAR DATOS (Lógica de consolidación) ---
        hoja = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        todos_los_datos = hoja.get_all_records()
        header = hoja.row_values(1)
        columna_estado_idx = header.index('Estado') + 1

        registros_pendientes = [(i + 2, registro) for i, registro in enumerate(todos_los_datos) if registro.get('Estado') == 'Pendiente']

        if not registros_pendientes:
            print("No hay registros pendientes para procesar. Finalizando.")
            return

        print(f"Se encontraron {len(registros_pendientes)} registros pendientes para procesar.")
        
        workbook = openpyxl.load_workbook(TEMPLATE_PATH)
        template_sheet = workbook.active
        
        filas_a_actualizar = []
        for i, (fila_numero, registro) in enumerate(registros_pendientes):
            pozo_num = str(registro.get('Pozo Numero', f"Fila_{fila_numero}"))
            print(f"\nProcesando Pozo: {pozo_num}")

            nueva_hoja = template_sheet if i == 0 else workbook.copy_worksheet(template_sheet)
            nueva_hoja.title = pozo_num
            
            rellenar_hoja(nueva_hoja, registro)
            filas_a_actualizar.append(fila_numero)
        
        if len(registros_pendientes) > 1 and template_sheet.title == 'Sheet': # Nombre por defecto de la plantilla
             workbook.remove(template_sheet)
        
        # --- 4. GUARDAR Y SUBIR REPORTE ---
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f'Reporte_Consolidado_{timestamp}.xlsx'
        upload_to_drive(buffer, filename, REPORTS_FOLDER_ID, drive_service)
        
        # --- 5. ACTUALIZAR ESTADOS EN GOOGLE SHEETS ---
        print("\nActualizando estados en Google Sheets...")
        for fila_num in filas_a_actualizar:
            hoja.update_cell(fila_num, columna_estado_idx, 'Generado')
            print(f" - Fila {fila_num} actualizada a 'Generado'.")

    except FileNotFoundError:
        print(f"Error Crítico: No se encuentra la plantilla Excel '{TEMPLATE_PATH}'. Asegúrate de que está en el repositorio.")
    except Exception as e:
        print(f"--- ¡Ocurrió un error inesperado! ---")
        print(f"Error: {e}")

    print("\n--- Proceso de Generación de Reportes Finalizado ---")


if __name__ == '__main__':
    main()