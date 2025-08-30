import os
import gspread
import openpyxl
from io import BytesIO
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- 1. CONFIGURACIÓN INICIAL ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
ruta_credenciales = '/etc/secrets/credentials.json'

# IDs de tus recursos de Google (reemplazar con los tuyos)
SHEET_ID = os.environ.get('SHEET_ID') # ID de tu Google Sheet
SHEET_NAME = 'RESIDUALES' # Nombre exacto de la hoja
PHOTOS_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID') # Carpeta donde la App sube las fotos
REPORTS_FOLDER_ID = os.environ.get('REPORTS_FOLDER_ID') # Carpeta para guardar los reportes terminados
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
# --- NUEVA FUNCIÓN DE AYUDA ---
def rellenar_hoja(sheet, datos_registro):
    """
    Toma una hoja de cálculo (sheet) y la rellena con los datos de un registro.
    """
    print(f"  - Rellenando hoja '{sheet.title}'...")
    for campo, mapeo in CELL_MAPPING.items():
        valor = datos_registro.get(campo)
        if valor is None or valor == '':
            continue

        if mapeo['type'] == 'direct':
            sheet[mapeo['cell']] = valor
        elif mapeo['type'] == 'options':
            celda_a_marcar = mapeo['values'].get(valor)
            if celda_a_marcar:
                sheet[celda_a_marcar] = 'X'
    print(f"  - Hoja '{sheet.title}' rellenada.")

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
    print("--- Iniciando Proceso de Generación de Reporte Consolidado ---")
    try:
        # --- Autenticación (sin cambios) ---
        credentials = Credentials.from_service_account_file(ruta_credenciales, scopes=SCOPES)
        gc = gspread.authorize(credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Autenticación con Google exitosa.")

        # --- Leer datos de Google Sheets (sin cambios) ---
        hoja = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
        todos_los_datos = hoja.get_all_records()
        header = hoja.row_values(1)
        columna_estado_idx = header.index('Estado') + 1

        # --- Filtrar solo los registros pendientes ---
        registros_pendientes = [
            (i + 2, registro) for i, registro in enumerate(todos_los_datos) if registro.get('Estado') == 'Pendiente'
        ]

        if not registros_pendientes:
            print("No hay registros pendientes para procesar. Finalizando.")
            return

        print(f"Se encontraron {len(registros_pendientes)} registros pendientes para procesar.")

        # --- Lógica de Creación del Reporte Consolidado ---
        # 1. Cargamos la plantilla UNA SOLA VEZ
        try:
            workbook = openpyxl.load_workbook(TEMPLATE_PATH)
            template_sheet = workbook.active
        except FileNotFoundError:
            print(f"Error Crítico: No se encontró la plantilla en la ruta: {TEMPLATE_PATH}")
            return
        
        # 2. Iteramos sobre los registros pendientes
        filas_a_actualizar = []
        for i, (fila_numero, registro) in enumerate(registros_pendientes):
            pozo_num = registro.get('Pozo Numero', f"Fila_{fila_numero}")
            print(f"\nProcesando Pozo: {pozo_num}")

            if i == 0:
                # Para el primer pozo, reutilizamos la primera hoja que ya existe
                nueva_hoja = template_sheet
                nueva_hoja.title = str(pozo_num)
            else:
                # Para los siguientes, copiamos la plantilla para crear una hoja nueva
                nueva_hoja = workbook.copy_worksheet(template_sheet)
                nueva_hoja.title = str(pozo_num)
            
            # 3. Rellenamos la nueva hoja con los datos del pozo actual
            rellenar_hoja(nueva_hoja, registro)
            filas_a_actualizar.append(fila_numero)
        
        # 4. Si creamos hojas nuevas, borramos la plantilla original si ya no la necesitamos
        if len(registros_pendientes) > 1:
             # Si el nombre de la plantilla original no fue cambiado (caso de un solo pozo)
             if template_sheet.title not in [str(r.get('Pozo Numero', f"Fila_{f}")) for f, r in registros_pendientes]:
                workbook.remove(template_sheet)


        # 5. Guardamos el libro de Excel completo en memoria
        buffer = BytesIO()
        workbook.save(buffer)
        buffer.seek(0)
        
        # 6. Generamos un nombre de archivo con la fecha y hora actual
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f'Reporte_Consolidado_{timestamp}.xlsx'

        # 7. Subimos el ÚNICO archivo a Google Drive
        upload_to_drive(buffer, filename, REPORTS_FOLDER_ID, drive_service)
        
        # 8. Actualizamos el estado de TODAS las filas procesadas en Google Sheets
        print("\nActualizando estados en Google Sheets...")
        for fila_num in filas_a_actualizar:
            hoja.update_cell(fila_num, columna_estado_idx, 'Generado')
            print(f" - Fila {fila_num} actualizada a 'Generado'.")

    except Exception as e:
        print(f"--- ¡Ocurrió un error inesperado! ---")
        print(f"Error: {e}")

    print("\n--- Proceso de Generación de Reportes Finalizado ---")

if __name__ == '__main__':
    main()