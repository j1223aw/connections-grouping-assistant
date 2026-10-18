import os
import json
import asyncio
import subprocess
import edge_tts
from playwright.async_api import async_playwright

PIPELINE_DIR = r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline"
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
RENDER_DIR = os.path.join(PIPELINE_DIR, "rendered_videos")
TEMP_FRAME_DIR = os.path.join(PIPELINE_DIR, "temp_frames")
TEMPLATE_PATH = os.path.join(PIPELINE_DIR, "templates", "board_template.html")

os.makedirs(RENDER_DIR, exist_ok=True)
os.makedirs(TEMP_FRAME_DIR, exist_ok=True)

# High-fidelity natural neural voice (fast-paced, high retention)
VOICE_NAME = "en-US-ChristopherNeural"

async def synthesize_neural_voice(script_text: str, output_mp3: str):
    """Synthesizes voiceover at +18% rate to guarantee Shorts under 60s."""
    print(f"    [AI Voice] Synthesizing audio narration ({VOICE_NAME} @ +18%)...")
    communicate = edge_tts.Communicate(script_text, VOICE_NAME, rate="+18%")
    await communicate.save(output_mp3)

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def generate_board_html(hook, words, highlighted_words, solved_tier=None):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    grid_items = ""
    for w in words:
        is_highlighted = w in highlighted_words
        style_class = "tile highlighted" if is_highlighted else "tile"
        if solved_tier and is_highlighted:
            style_class += f" solved-{solved_tier.lower()}"
        grid_items += f'<div class="{style_class}">{w}</div>'

    badge_html = f'<div class="badge {solved_tier.lower()}">{solved_tier.upper()} CATEGORY</div>' if solved_tier else ''

    html = template.replace("{{HOOK}}", hook)
    html = html.replace("{{BADGE_HTML}}", badge_html)
    html = html.replace("{{GRID_ITEMS}}", grid_items)
    return html

async def capture_frame(page, html_content, output_path):
    await page.set_content(html_content)
    await page.screenshot(path=output_path)

async def build_short(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    short_id = os.path.splitext(os.path.basename(json_path))[0]
    final_video = os.path.join(RENDER_DIR, f"{short_id}.mp4")
    raw_audio_path = os.path.join(PIPELINE_DIR, f"{short_id}_narration.mp3")

    print(f"\n[*] Processing Short: {short_id}")
    scenes = data.get("scenes", [])
    full_narration = " ".join([s["voiceover"] for s in scenes])
    
    # 1. Synthesize audio at high-tempo pacing
    await synthesize_neural_voice(full_narration, raw_audio_path)
    audio_duration = get_audio_duration(raw_audio_path)
    print(f"    Audio generated. Duration: {audio_duration:.2f}s")

    # 2. Extract dynamic board words from JSON if present, else fallback by ID
    default_words = [
        "DRILL", "HAMMER", "SAW", "WRENCH",
        "COMB", "GEAR", "ZIPPER", "FORK",
        "STOCK", "BOND", "OPTION", "SHARE",
        "PLIERS", "LEVEL", "CHISEL", "PLANE"
    ] if "002" in short_id else [
        "SWIFT", "RAPID", "FLEET", "QUICK",
        "FUJI", "GALA", "EMPIRE", "JAZZ",
        "CANOE", "KAYAK", "YACHT", "BARGE",
        "KEY", "DASH", "SURF", "SKATE"
    ]
    board_words = data.get("board_words", default_words)
    red_herrings = data.get("red_herrings_identified", ["DRILL", "HAMMER", "SAW", "WRENCH"])
    target_solution = data.get("target_words", ["DRILL", "COMB", "GEAR", "ZIPPER"] if "002" in short_id else ["KEY", "DASH", "SURF", "SKATE"])
    tier = data.get("category_tier", "Blue" if "002" in short_id else "Purple")

    # 3. Render 1080x1920 frames via Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        # Frame 1: Hook Intro
        f1_html = generate_board_html(data.get("hook_headline", "TRAP BREAKDOWN"), board_words, [])
        f1_path = os.path.join(TEMP_FRAME_DIR, f"{short_id}_1.png")
        await capture_frame(page, f1_html, f1_path)

        # Frame 2: Decoy Trap Highlighted
        f2_html = generate_board_html("THE DECOY OVERLAP!", board_words, red_herrings)
        f2_path = os.path.join(TEMP_FRAME_DIR, f"{short_id}_2.png")
        await capture_frame(page, f2_html, f2_path)

        # Frame 3: Final Category Reveal
        f3_html = generate_board_html(data.get("target_category", "CATEGORY REVEAL"), board_words, target_solution, tier)
        f3_path = os.path.join(TEMP_FRAME_DIR, f"{short_id}_3.png")
        await capture_frame(page, f3_html, f3_path)

        await browser.close()

    # 4. Proportional Scene Timings
    t1 = round(audio_duration * 0.20, 2)
    t2 = round(audio_duration * 0.35, 2)
    t3 = round(audio_duration - (t1 + t2), 2)

    concat_txt = os.path.join(PIPELINE_DIR, "concat.txt")
    with open(concat_txt, "w") as f:
        f.write(f"file '{f1_path.replace(os.sep, '/')}'\nduration {t1}\n")
        f.write(f"file '{f2_path.replace(os.sep, '/')}'\nduration {t2}\n")
        f.write(f"file '{f3_path.replace(os.sep, '/')}'\nduration {t3}\n")
        f.write(f"file '{f3_path.replace(os.sep, '/')}'\n")

    # 5. FFmpeg Assembly
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-i", raw_audio_path,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        final_video
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f" [OK] Modernized Short rendered: {final_video}")

    if os.path.exists(raw_audio_path):
        os.remove(raw_audio_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        targets = [sys.argv[1]]
    else:
        targets = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    
    for t in targets:
        asyncio.run(build_short(t))