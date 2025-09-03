import openpyxl
import io

from google_clients import get_credentials
from report_generation.sheets_handler import get_pending_records, update_record_status
from report_generation.drive_handler import download_master_report, update_master_report
from report_generation.excel_handler import fill_sheet

def main():
    """Función principal que orquesta la generación de reportes."""
    print("--- Iniciando Proceso de Generación de Reportes (Modular) ---")
    try:
        # 1. Verificar credenciales al inicio
        get_credentials()
        print("Autenticación con Google verificada.")

        # 2. Obtener registros pendientes de Google Sheets
        worksheet, pending_records, _ = get_pending_records()
        if not pending_records:
            print("No hay registros pendientes. Finalizando.")
            return

        # 3. Descargar el reporte maestro de Google Drive
        master_report_buffer = download_master_report()
        workbook = openpyxl.load_workbook(master_report_buffer)
        template_sheet = workbook[workbook.sheetnames[0]]
        print("Reporte maestro abierto en memoria.")

        # 4. Procesar cada registro pendiente
        processed_rows = []
        for row_number, record in pending_records:
            pozo_num = str(record.get('pozo_numero', f"Fila_{row_number}"))
            print(f"\nProcesando Pozo: {pozo_num}")
            
            # Copiar la plantilla y rellenar la nueva hoja
            new_sheet = workbook.copy_worksheet(template_sheet)
            new_sheet.title = pozo_num
            fill_sheet(new_sheet, record)
            
            processed_rows.append(row_number)

        # 5. Guardar el libro de trabajo actualizado en un buffer
        output_buffer = io.BytesIO()
        workbook.save(output_buffer)
        output_buffer.seek(0)

        # 6. Subir el reporte actualizado a Google Drive
        update_master_report(output_buffer)

        # 7. Actualizar el estado en Google Sheets
        update_record_status(worksheet, processed_rows)

    except Exception as e:
        print(f"--- ¡Ocurrió un error inesperado! ---")
        print(f"Error: {e}")

    print("\n--- Proceso Finalizado ---")

if __name__ == '__main__':
    main()
