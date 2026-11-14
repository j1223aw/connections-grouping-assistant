import os
from PIL import Image, ImageDraw, ImageFont

w, h = 1280, 384
img = Image.new('RGB', (w, h), '#1E2328')
draw = ImageDraw.Draw(img)

# Load Windows Arial Bold
font_title = None
font_sub = None
font_url = None

for font_path in ['C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/arial.ttf']:
    if os.path.exists(font_path):
        try:
            font_title = ImageFont.truetype(font_path, 54)
            font_sub = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 28)
            font_url = ImageFont.truetype(font_path, 32)
            break
        except Exception:
            pass

if not font_title:
    font_title = font_sub = font_url = ImageFont.load_default()

# 1. Centered 4-Tile Brand Grid
# Start coordinates positioned in safe visual center
tile_start_x = 220
tile_start_y = 106
tile_size = 78
gap = 16

tiles = [
    ('#FFC800', (tile_start_x, tile_start_y, tile_start_x + tile_size, tile_start_y + tile_size)),
    ('#50C836', (tile_start_x + tile_size + gap, tile_start_y, tile_start_x + 2*tile_size + gap, tile_start_y + tile_size)),
    ('#2C35E8', (tile_start_x, tile_start_y + tile_size + gap, tile_start_x + tile_size, tile_start_y + 2*tile_size + gap)),
    ('#D018EE', (tile_start_x + tile_size + gap, tile_start_y + tile_size + gap, tile_start_x + 2*tile_size + gap, tile_start_y + 2*tile_size + gap))
]

for hex_col, box in tiles:
    draw.rounded_rectangle(box, radius=18, fill=hex_col)

# 2. Typography Aligned to Tiles
text_x = tile_start_x + 2*tile_size + gap + 48

draw.text((text_x, 110), 'CONNECTIONS ASSISTANT', fill='#FFFFFF', font=font_title)
draw.text((text_x, 180), 'Daily Progressive Nudges  |  Interactive Scratchboard', fill='#9CA3AF', font=font_sub)
draw.text((text_x, 224), 'connectionsassistant.com', fill='#FFC800', font=font_url)

out_file = os.path.join(os.getcwd(), 'reddit_banner.png')
img.save(out_file, 'PNG', optimize=True)
print(f'Successfully created centered banner: {out_file}')
