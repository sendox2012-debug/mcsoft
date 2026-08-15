from PIL import Image
import cairosvg
import os

SVG_PATH = "icon.svg"
ICO_PATH = "icon.ico"
PNG_PATH = "icon.png"

# SVG → PNG (512px)
cairosvg.svg2png(url=SVG_PATH, write_to=PNG_PATH, output_width=512, output_height=512)

# PNG → ICO (мультиразмерная)
img = Image.open(PNG_PATH)
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
         (128, 128), (256, 256)]
img.save(ICO_PATH, sizes=sizes)

print(f"Создано: {ICO_PATH}")