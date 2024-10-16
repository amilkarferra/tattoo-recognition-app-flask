import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_image(filename, text, size=(200, 200), color="white", text_color="black"):
    image = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    position = ((size[0] - text_width) / 2, (size[1] - text_height) / 2)
    draw.text(position, text, fill=text_color, font=font)
    image.save(f"static/images/{filename}")

# Create static/images directory if it doesn't exist
os.makedirs("static/images", exist_ok=True)

# List of tattoo designs from tattoo_database.json
tattoo_designs = [
    "circulo.png", "triangulo.png", "emoji_corazon.png", "estrella.png", "flor.png",
    "lion_tattoo.png", "lotus_flower.png", "anchor_tattoo.png", "butterfly_tattoo.png",
    "tree_of_life.png", "compass_rose.png", "dragon_tattoo.png", "infinity_symbol.png",
    "mandala_tattoo.png", "phoenix_tattoo.png"
]

# Generate placeholder images
for design in tattoo_designs:
    create_placeholder_image(design, design.split('.')[0].replace('_', ' ').title())

print("Placeholder images have been generated in the static/images/ directory.")
