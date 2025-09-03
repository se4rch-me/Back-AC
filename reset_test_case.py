import gspread
from google_clients import get_gspread_client
from config import SPREADSHEET_ID, WORKSHEET_NAME, PENDING_STATUS, GENERATED_STATUS
from run_report_generator import main as run_generator

TEST_WELL_NAME = "GeminiTest"

def reset_test_record_status():
    """
    Busca el registro de prueba en la hoja maestra y resetea su estado
    de 'Generado' a 'Pendiente'.
    """
    print(f"--- Reseteando estado del registro de prueba '{TEST_WELL_NAME}' ---")
    try:
        gspread_client = get_gspread_client()
        spreadsheet = gspread_client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

        cell = worksheet.find(TEST_WELL_NAME)
        if not cell:
            print(f"No se encontró el registro de prueba '{TEST_WELL_NAME}'.")
            return False

        headers = worksheet.row_values(1)
        try:
            status_col_index = headers.index("Estado") + 1
        except ValueError:
            print("No se encontró la columna 'Estado' en la hoja.")
            return False

        worksheet.update_cell(cell.row, status_col_index, PENDING_STATUS)
        print(f"Estado del pozo '{TEST_WELL_NAME}' en la fila {cell.row} cambiado a '{PENDING_STATUS}'.")
        return True

    except Exception as e:
        print(f"Error al resetear el estado del registro de prueba: {e}")
        return False

if __name__ == "__main__":
    if reset_test_record_status():
        print("\n--- Ejecutando el generador de reportes automáticamente ---")
        run_generator()
