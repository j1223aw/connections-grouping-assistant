import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

# 1. Canvas Setup
WIDTH, HEIGHT = 1080, 1920
bg_color = (15, 15, 22)
card_bg = (30, 30, 42)
text_color = (255, 255, 255)
sub_color = (180, 185, 200)

font_title = ImageFont.load_default()
font_tile = ImageFont.load_default()

# 2. Tiles for Monday #1552
tiles = [
    "STEAK KNIFE", "CARD SHARK", "CON JOB", "BOOTCUT",
    "NAVY SEAL", "SHELL GAME", "MINT LEAF", "GAMMA RAY",
    "TAPE DISPENSER", "LOW-RISE", "FUN SPONGE", "RIP-OFF",
    "SKINNY", "FLIMFLAM", "GRAPEFRUIT SPOON", "DISTRESSED"
]

img = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
draw = ImageDraw.Draw(img)

# Header
draw.rectangle([(60, 80), (1020, 220)], fill=(24, 24, 34), outline=(70, 70, 90), width=2)
draw.text((100, 110), "NYT CONNECTIONS • PUZZLE #1552", fill=(240, 190, 70))
draw.text((100, 155), "Monday, November 9, 2026", fill=text_color)

# Trap Callout
draw.rectangle([(60, 250), (1020, 390)], fill=(45, 20, 25), outline=(224, 49, 49), width=3)
draw.text((90, 280), "⚠️ 5-WORD DECOY TRAP: CARD SHARK", fill=(255, 100, 100))
draw.text((90, 325), "CARD SHARK pivots to Purple (Marine Animals)!", fill=sub_color)

# 4x4 Grid
grid_top = 440
tile_w, tile_h = 215, 130
gap = 20
start_x = 75

for idx, word in enumerate(tiles):
    r = idx // 4
    c = idx % 4
    x1 = start_x + c * (tile_w + gap)
    y1 = grid_top + r * (tile_h + gap)
    x2 = x1 + tile_w
    y2 = y1 + tile_h
    
    # Highlight CARD SHARK as trap
    border_col = (224, 49, 49) if word == "CARD SHARK" else (60, 60, 80)
    fill_col = (50, 25, 30) if word == "CARD SHARK" else card_bg
    
    draw.rectangle([(x1, y1), (x2, y2)], fill=fill_col, outline=border_col, width=2)
    draw.text((x1 + 15, y1 + 50), word, fill=text_color)

# Revealed Categories at Bottom
cat_top = 1100
cats = [
    ("🟨 SWINDLES / SCAMS", "CON JOB, FLIMFLAM, RIP-OFF, SHELL GAME", (249, 226, 175)),
    ("🟩 STYLES OF JEANS", "BOOTCUT, DISTRESSED, LOW-RISE, SKINNY", (166, 227, 161)),
    ("🟦 SERRATED EDGES", "GRAPEFRUIT SPOON, MINT LEAF, STEAK KNIFE, TAPE DISPENSER", (137, 180, 250)),
    ("🟪 ENDING IN MARINE ANIMALS", "CARD SHARK, FUN SPONGE, GAMMA RAY, NAVY SEAL", (203, 166, 247))
]

for label, words, col in cats:
    draw.rectangle([(60, cat_top), (1020, cat_top + 140)], fill=col, outline=(30, 30, 30), width=2)
    draw.text((90, cat_top + 25), label, fill=(15, 15, 20))
    draw.text((90, cat_top + 75), words, fill=(35, 35, 45))
    cat_top += 165

# Footer
draw.text((220, 1810), "Solve on the scratchboard: connectionsassistant.com", fill=(140, 140, 160))

img.save("board_1552.png")
print("[1/2] board_1552.png generated successfully.")

# Encode with NVENC over narration
ffmpeg_cmd = [
    "ffmpeg", "-y",
    "-loop", "1", "-i", "board_1552.png",
    "-i", "narration_1552.mp3",
    "-c:v", "h264_nvenc",
    "-preset", "p6",
    "-tune", "hq",
    "-b:v", "12M",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
    "-b:a", "192k",
    "-shortest",
    "Connections_1552_Monday.mp4"
]
subprocess.run(ffmpeg_cmd, check=True)
print("[2/2] Final video generated: Connections_1552_Monday.mp4")
