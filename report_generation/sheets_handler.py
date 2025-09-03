from google_clients import get_gspread_client
from config import SPREADSHEET_ID, WORKSHEET_NAME

def get_pending_records():
    """Obtiene todos los registros de la hoja de cálculo que están marcados como 'Pendiente'."""
    print("Accediendo a Google Sheets para buscar registros pendientes...")
    gc = get_gspread_client()
    worksheet = gc.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    
    all_records = worksheet.get_all_records()
    header = worksheet.row_values(1)
    
    pending_records = []
    for i, record in enumerate(all_records):
        if record.get('Estado') == 'Pendiente':
            pending_records.append((i + 2, record)) # Guardamos el número de fila y los datos
            
    if pending_records:
        print(f"Se encontraron {len(pending_records)} registros pendientes.")
    else:
        print("No hay registros pendientes para procesar.")
        
    return worksheet, pending_records, header

def update_record_status(worksheet, row_numbers):
    """Actualiza el estado de una lista de filas a 'Generado'."""
    print("\nActualizando estados en Google Sheets...")
    col_index = worksheet.find('Estado').col

    for row_num in row_numbers:
        worksheet.update_cell(row_num, col_index, 'Generado')
        print(f" - Fila {row_num} actualizada a 'Generado'.")
