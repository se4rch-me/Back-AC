from flask import Flask, request, jsonify

from data_ingestion.ingestion_service import ingest_survey
from google_clients import get_credentials

app = Flask(__name__)

# --- INICIALIZACIÓN ---
try:
    get_credentials() # Solo para verificar que las credenciales carguen al inicio
    print("Autenticación con Google verificada al iniciar el servidor web.")
except Exception as e:
    print(f"ERROR CRÍTICO al iniciar el servidor: {e}")

# --- RUTAS DE LA API ---
@app.route('/')
def home():
    return "Servidor de Encuestas para Acueducto (Modular): Activo y listo para recibir datos."

@app.route('/ingestar-encuesta', methods=['POST'])
def ingestar_encuesta_route():
    try:
        print("Paso 1: Solicitud POST recibida.")
        
        # Extraemos los datos del formulario
        datos_json_str = request.form['data']
        fotos = request.files.getlist('fotos')

        # Llamamos al servicio de ingesta
        ingest_survey(datos_json_str, fotos)

        return jsonify({'mensaje': 'Encuesta recibida y procesada correctamente.'}), 200

    except Exception as e:
        # En un caso real, sería bueno tener un logger más robusto aquí
        print(f"Error inesperado en /ingestar-encuesta: {e}")
        return jsonify({'mensaje': f'Error interno del servidor: {e}'}), 500

# Para pruebas locales: flask --app app run
