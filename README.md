# Backend de Acueducto - Versión Modular

Este proyecto gestiona la recepción de datos de inspecciones de pozos y la generación de reportes automáticos en formato Excel. Esta versión ha sido refactorizada para tener una arquitectura modular que facilita el mantenimiento y la escalabilidad.

## Estructura de Archivos

El proyecto se organiza de la siguiente manera:

```
back-ac-modular/
├── app.py                  # Servidor web Flask para la recepción de datos.
├── run_report_generator.py # Script principal para generar los reportes.
├── config.py               # Módulo de configuración centralizado.
├── google_clients.py       # Gestor de clientes y autenticación con APIs de Google.
├── requirements.txt        # Dependencias del proyecto.
├── ejemplo.xltx            # Plantilla de Excel para los reportes.
├── .env                    # Archivo para variables de entorno (no incluido en git).
│
├── data_ingestion/         # Módulo para la lógica de ingesta de datos.
│   └── ingestion_service.py
│
└── report_generation/      # Módulo para la lógica de generación de reportes.
    ├── excel_handler.py
    ├── drive_handler.py
    ├── sheets_handler.py
    └── image_generator.py
```

## Instalación

1.  Clona este repositorio.
2.  Crea un entorno virtual:
    ```bash
    python -m venv venv
    ```
3.  Activa el entorno virtual:
    *   En Windows: `venv\Scripts\activate`
    *   En macOS/Linux: `source venv/bin/activate`
4.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
5.  Crea un archivo `.env` en la raíz del proyecto y añade las variables de entorno necesarias (ver `config.py`).

## Uso

### Servidor Web

El servidor Flask se encarga de recibir los datos de las encuestas a través de una API REST.

Para iniciarlo, ejecuta:

```bash
flask --app app run
```

El endpoint principal es:

*   `POST /ingestar-encuesta`: Recibe los datos de la encuesta en formato `multipart/form-data`, incluyendo un campo `data` con el JSON de la encuesta y archivos de `fotos`.

### Generador de Reportes

Este script se encarga de leer los registros pendientes de Google Sheets, generar las nuevas hojas en el reporte maestro de Excel y actualizar su estado.

Para ejecutarlo, usa el siguiente comando:

```bash
python run_report_generator.py
```

---

## Documentación de Módulos y Métodos

### `config.py`

Centraliza toda la configuración de la aplicación, cargando variables de entorno y definiendo constantes.

### `google_clients.py`

Gestiona la autenticación y la creación de los clientes para las APIs de Google.

*   `get_credentials()`: Carga las credenciales desde la variable de entorno `GOOGLE_CREDENTIALS_JSON`.
*   `get_sheets_client()`: Devuelve un cliente `googleapiclient` para Google Sheets.
*   `get_drive_client()`: Devuelve un cliente `googleapiclient` para Google Drive.
*   `get_gspread_client()`: Devuelve un cliente `gspread` para una interacción más sencilla con Google Sheets.

### `data_ingestion/ingestion_service.py`

Contiene la lógica de negocio para procesar los datos de las encuestas.

*   `ingest_survey(data_str, files)`: Orquesta el proceso de ingesta. Decodifica el JSON, prepara la fila de datos, la escribe en Google Sheets y sube las imágenes a Google Drive.
*   `_prepare_row_for_sheets(datos)`: Transforma el diccionario de datos JSON en una lista ordenada para ser insertada en la hoja de cálculo.
*   `_upload_photos(service_drive, files, pozo_numero)`: Itera sobre los archivos de imagen y los sube a la carpeta especificada en Google Drive.

### `report_generation/sheets_handler.py`

Maneja las operaciones de lectura y escritura en Google Sheets para el generador de reportes.

*   `get_pending_records()`: Obtiene todos los registros de la "Tabla Maestra" cuyo estado es "Pendiente". Devuelve el objeto de la hoja, una lista de registros pendientes y la cabecera.
*   `update_record_status(worksheet, row_numbers)`: Actualiza el estado de una lista de filas a "Generado" después de que han sido procesadas.

### `report_generation/drive_handler.py`

Gestiona las interacciones con Google Drive.

*   `download_master_report()`: Descarga el archivo maestro de Excel desde Google Drive y lo carga en un buffer en memoria.
*   `download_photo(pozo_numero)`: Busca y descarga la foto de un pozo específico desde Google Drive.
*   `update_master_report(file_buffer)`: Sube el buffer del archivo de Excel modificado para actualizar el reporte maestro en Google Drive.

### `report_generation/image_generator.py`

Crea imágenes dinámicamente.

*   `create_connections_table_image(conexiones)`: Genera una imagen PNG que representa una tabla con los datos de las conexiones del pozo.

### `report_generation/excel_handler.py`

Se encarga de la manipulación del archivo Excel.

*   `CELL_MAPPING`: Un diccionario que actúa como "receta", mapeando cada campo de los datos a una celda o un grupo de celdas en la plantilla de Excel.
*   `fill_sheet(sheet, record)`: Rellena una hoja de Excel (una copia de la plantilla) con los datos de un registro específico, siguiendo las reglas de `CELL_MAPPING` e insertando las imágenes generadas o descargadas.
