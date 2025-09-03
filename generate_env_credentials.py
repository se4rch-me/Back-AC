import json

try:
    # Abre tu archivo de credenciales original
    with open('credentials.json', 'r') as f:
        creds_dict = json.load(f)

    # Convierte el diccionario de Python de nuevo a un string de JSON
    # pero asegurándose de que sea una sola línea y maneje bien los caracteres especiales.
    single_line_json = json.dumps(creds_dict)

    print("\n--- ¡ÉXITO! ---")
    print("Copia la siguiente línea completa (incluyendo GOOGLE_CREDENTIALS_JSON=...)")
    print("y pégala en tu archivo .env, reemplazando la línea antigua.\n")
    
    # Usamos comillas simples al final para que Windows no se confunda.
    print(f"GOOGLE_CREDENTIALS_JSON='{single_line_json}'")
    print("\n" + "-"*13)

except FileNotFoundError:
    print("\nError: No se encontró el archivo 'credentials.json' en esta carpeta.")
except json.JSONDecodeError:
    print("\nError: El archivo 'credentials.json' no parece ser un JSON válido.")
