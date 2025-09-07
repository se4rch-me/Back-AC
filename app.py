import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Permite OAuth sobre HTTP para desarrollo.
from flask import Flask, request, jsonify, redirect, url_for, session
from flask_cors import CORS

from data_ingestion.ingestion_service import ingest_survey
from google_clients import get_auth_flow, save_credentials, get_credentials

app = Flask(__name__)
CORS(app) # Habilita CORS para todas las rutas
# Se necesita una clave secreta para manejar la sesión donde se guarda el estado de OAuth.
app.secret_key = os.urandom(24)

# --- Constantes ---
# La URL donde corre tu PWA. El usuario será redirigido aquí después de la autenticación.
PWA_URL = os.environ.get("PWA_URL", "http://localhost:8080")

# --- Rutas de Autenticación ---
@app.route('/login')
def login():
    """Inicia el flujo de autenticación OAuth 2.0."""
    # El redirect_uri debe ser la URL completa de nuestro endpoint de callback.
    redirect_uri = url_for('oauth2callback', _external=True)
    flow = get_auth_flow(redirect_uri)

    # Generamos la URL de autorización y guardamos el estado para seguridad.
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )
    session['state'] = state

    return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
    """Callback de Google después de la autenticación."""
    # Verificamos que el estado coincida para evitar ataques CSRF.
    state = session['state']
    flow = get_auth_flow(url_for('oauth2callback', _external=True))
    
    # Usamos la URL completa de la solicitud para que coincida con el redirect_uri.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Guardamos las credenciales obtenidas.
    credentials = flow.credentials
    save_credentials(credentials)

    print("Autenticación completada y token guardado.")
    return redirect(PWA_URL)

@app.route('/auth/status')
def auth_status():
    """Verifica si el usuario está autenticado (si existe token.json)."""
    if get_credentials():
        return jsonify({'status': 'authenticated'}), 200
    else:
        return jsonify({'status': 'unauthenticated'}), 401

# --- Rutas de la API ---
@app.route('/')
def home():
    return "Servidor de Encuestas para Acueducto (Modular): Activo y listo para recibir datos."

@app.route('/ingestar-encuesta', methods=['POST'])
def ingestar_encuesta_route():
    """Recibe y procesa una encuesta, requiere autenticación previa."""
    # Paso 1: Verificar si el usuario está autenticado.
    credentials = get_credentials()
    if not credentials:
        print("Bloqueando solicitud: Se requiere autenticación.")
        return jsonify({'mensaje': 'Error: Se requiere autenticación. Por favor, inicie sesión.'}), 401

    try:
        print("Paso 1: Solicitud POST recibida (usuario autenticado).")
        
        # Extraemos los datos del formulario
        datos_json_str = request.form['data']
        fotos = request.files.getlist('fotos')

        # Llamamos al servicio de ingesta
        ingest_survey(datos_json_str, fotos)

        return jsonify({'mensaje': 'Encuesta recibida y procesada correctamente.'}), 200

    except Exception as e:
        print(f"Error inesperado en /ingestar-encuesta: {e}")
        return jsonify({'mensaje': f'Error interno del servidor: {e}'}), 500

# Para pruebas locales: flask --app app run