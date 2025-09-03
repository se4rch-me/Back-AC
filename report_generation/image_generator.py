import io
from PIL import Image as PILImage, ImageDraw, ImageFont

def create_connections_table_image(conexiones):
    """
    Dibuja una tabla SIMPLIFICADA con los datos de las conexiones y la devuelve como un buffer de imagen.
    """
    # --- AJUSTE: Ancho reducido para 3 columnas ---
    ancho, alto_fila, margen = 550, 30, 10
    alto_total = alto_fila * (len(conexiones) + 1)
    img = PILImage.new('RGB', (ancho, alto_total), color='white')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()

    # --- AJUSTE: Nuevos encabezados ---
    encabezados = ["Diámetro ()", "Profundidad (m)", "Material"]
    pos_x = margen
    for header in encabezados:
        draw.text((pos_x, 5), header, fill="black", font=font)
        pos_x += 180

    # --- AJUSTE: Nuevas filas de datos ---
    for i, conexion in enumerate(conexiones):
        fila_y = (i + 1) * alto_fila
        try:
            profundidad = round(float(conexion.get('cota_razante', 0)) - float(conexion.get('cota_clave', 0)), 2)
        except (ValueError, TypeError):
            profundidad = "N/A"

        datos_fila = [
            str(conexion.get('diametro_pulgadas', '')),
            str(profundidad),
            str(conexion.get('material', ''))
        ]
        
        pos_x = margen
        for dato in datos_fila:
            draw.text((pos_x, fila_y), dato, fill="black", font=font)
            pos_x += 180

    buffer_imagen = io.BytesIO()
    img.save(buffer_imagen, format='PNG')
    buffer_imagen.seek(0)
    print("  - Imagen de la tabla de conexiones creada.")
    return buffer_imagen
