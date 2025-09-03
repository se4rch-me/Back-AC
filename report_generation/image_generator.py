from PIL import Image, ImageDraw, ImageFont
import io
import json

# Constantes para la apariencia de la tabla
FONT_PATH = "C:\\Windows\\Fonts\\calibri.ttf"
FONT_SIZE = 16
HEADER_FONT_SIZE = 18
PADDING = 10
MIN_FONT_SIZE = 8
MIN_HEADER_FONT_SIZE = 10
MIN_PADDING = 4
BACKGROUND_COLOR = "white"
TEXT_COLOR = "black"
HEADER_COLOR = "black"
LINE_COLOR = "black"

def create_connections_table_image(conexiones, target_width_px=None):
    """Crea una imagen PNG que representa una tabla con los datos de las conexiones."""
    
    headers = ["Diámetro (pulg)", "Profundidad (m)", "Material"]
    
    data_for_table = [headers]
    for c in conexiones:
        try:
            profundidad = round(float(c.get('cota_razante', 0)) - float(c.get('cota_clave', 0)), 2)
        except (ValueError, TypeError):
            profundidad = "N/A"
        data_for_table.append([
            c.get('diametro_pulgadas', ''),
            profundidad,
            c.get('material', '')
        ])

    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        header_font = ImageFont.truetype(FONT_PATH, HEADER_FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()
        header_font = ImageFont.load_default()

    padding = PADDING
    
    original_col_widths = [
        max(header_font.getbbox(str(header))[2], max(font.getbbox(str(item))[2] for item in col)) 
        for header, col in zip(headers, zip(*data_for_table))
    ]
    original_img_width = sum(original_col_widths) + (len(original_col_widths) + 1) * padding

    if target_width_px and original_img_width > target_width_px:
        scale_factor = target_width_px / original_img_width
        
        new_font_size = max(MIN_FONT_SIZE, int(FONT_SIZE * scale_factor))
        new_header_font_size = max(MIN_HEADER_FONT_SIZE, int(HEADER_FONT_SIZE * scale_factor))
        padding = max(MIN_PADDING, int(PADDING * scale_factor))
        
        try:
            font = ImageFont.truetype(FONT_PATH, new_font_size)
            header_font = ImageFont.truetype(FONT_PATH, new_header_font_size)
        except IOError:
            font = ImageFont.load_default()
            header_font = ImageFont.load_default()

    col_widths = [
        max(header_font.getbbox(str(header))[2], max(font.getbbox(str(item))[2] for item in col)) 
        for header, col in zip(headers, zip(*data_for_table))
    ]
    img_width = int(sum(col_widths) + (len(col_widths) + 1) * padding)
    
    row_height = font.getbbox('A')[3] - font.getbbox('A')[1] + padding
    header_height = header_font.getbbox('A')[3] - header_font.getbbox('A')[1] + padding
    img_height = header_height + len(conexiones) * row_height

    image = Image.new('RGB', (img_width, int(img_height)), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    y_offset = 0
    x_offset = padding
    for i, header in enumerate(headers):
        draw.text((x_offset, y_offset + padding // 2), header, font=header_font, fill=HEADER_COLOR)
        x_offset += col_widths[i] + padding
    y_offset += header_height
    draw.line([(0, y_offset), (img_width, y_offset)], fill=LINE_COLOR, width=2)

    for row_values in data_for_table[1:]:
        x_offset = padding
        for i, cell_value in enumerate(row_values):
            draw.text((x_offset, y_offset + padding // 2), str(cell_value), font=font, fill=TEXT_COLOR)
            x_offset += col_widths[i] + padding
        y_offset += row_height
        draw.line([(0, y_offset), (img_width, y_offset)], fill=LINE_COLOR, width=1)

    img_buffer = io.BytesIO()
    image.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    print("  - Imagen de la tabla de conexiones creada.")
    return img_buffer
