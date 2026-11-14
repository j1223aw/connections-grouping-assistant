"""
generate_shorts.py

YouTube Shorts Local Pipeline Generator (Phase 1).
Automates the production of high-retention 1080x1920 vertical Shorts from daily_puzzle.json:
1. Loads daily_puzzle.json and identifies target category & red herring decoy overlap.
2. Formulates a fast-paced 3-scene blueprint (Hook -> Decoy Trap -> Reveal & CTA).
3. Synthesizes neural voiceover via edge-tts (en-US-ChristopherNeural @ +18%).
4. Captures 1080x1920 HTML5/CSS board frames via Playwright headless Chromium.
5. Assembles high-bitrate MP4 via FFmpeg using NVIDIA NVENC (h264_nvenc) hardware acceleration.
6. Saves final video to output_shorts/today_connections_short.mp4.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from typing import List

import edge_tts
from playwright.async_api import async_playwright

# Optional Gemini client for dynamic scriptwriting
try:
    from google import genai
    from google.genai import types
    from pydantic import BaseModel, Field
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output_shorts"
FRAMES_DIR = OUTPUT_DIR / "frames"
AUDIO_DIR = OUTPUT_DIR / "audio"
DEFAULT_PUZZLE = ROOT_DIR / "daily_puzzle.json"
TEMPLATE_PATH = ROOT_DIR / "video_pipeline" / "templates" / "board_template.html"

VOICE_NAME = "en-US-GuyNeural"
VOICE_RATE = "+0%"
VOICE_PITCH = "-8Hz"


if HAS_GEMINI:
    class ShortBlueprintSchema(BaseModel):
        hook: str = Field(description="Max 5 words. High curiosity hook headline for header.")
        theme: str = Field(description="Target category name being deconstructed")
        tier_name: str = Field(description="Yellow, Green, Blue, or Purple")
        tier_color: str = Field(description="yellow, green, blue, or purple")
        decoy_words: List[str] = Field(description="3 to 4 words creating the overlap trap")
        solution_words: List[str] = Field(description="Exact 4 uppercase words solving the target category as they appear on the board tiles")
        scene1_narration: str = Field(description="Hook scene narration. Max 18 words.")
        scene2_narration: str = Field(description="Decoy trap narration naming the tempting board tiles. Max 22 words.")
        scene3_narration: str = Field(
            description=(
                "Reveal and CTA narration (max 30 words). "
                "CRITICAL: Must state the category name and explicitly name all 4 exact uppercase board tile words. "
                "For wordplay/compound categories, explicitly explain the wordplay linking each tile word to its compound: "
                "e.g., 'The category is ENDS OF STORM TYPES: CANE as in hurricane, CLONE as in cyclone, EASTER as in nor'easter, and SOON as in monsoon. Test candidate boards at connectionsassistant.com' "
                "Never substitute the tile words with the completed compounds alone."
            )
        )


def ensure_directories():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def load_puzzle_data(puzzle_file: Path) -> dict:
    """Load and validate daily_puzzle.json."""
    if not puzzle_file.exists():
        raise FileNotFoundError(
            f"Puzzle file not found at '{puzzle_file}'. "
            "Please run 'python fetch_daily_puzzle.py' first."
        )
    with open(puzzle_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "categories" not in data or len(data["categories"]) < 4:
        raise ValueError("Invalid daily_puzzle.json format: expected 4 categories.")
    return data


def generate_blueprint_gemini(puzzle_data: dict) -> dict | None:
    """Use Gemini to dynamically generate script narration if API key is present."""
    if not HAS_GEMINI or not os.environ.get("GEMINI_API_KEY"):
        return None

    try:
        client = genai.Client()
        cats_json = json.dumps(puzzle_data["categories"], indent=2)
        prompt = f"""You are the master puzzle analyst for YouTube channel @ConnectionsAssistant.
Create a high-retention 30-second vertical YouTube Short script deconstructing today's trickiest trap from this official NYT Connections puzzle:
Categories:
{cats_json}

CRITICAL RULES & STRICT BOARD TILE CONSTRAINTS:
1. Target Category: Target the trickiest category (usually Purple Level 3 or Blue Level 2).
2. Decoy Words: Highlight 3 to 4 uppercase words creating an overlapping trap across groups (e.g. NORTH, SOUTH, EASTER).
3. Solution Words: The exact 4 uppercase words solving the target category as they appear on the tiles.
4. STRICT BOARD TILE WORDING (ZERO SUBSTITUTION):
   - When revealing words in Scene 2 and Scene 3, the script MUST use the EXACT uppercase words that appear on the NYT board tiles (e.g. "CANE", "CLONE", "EASTER", "SOON").
   - You MUST explain wordplay explicitly rather than substituting the completed compound word.
     Exact expected format:
     "The category is ENDS OF STORM TYPES: CANE as in hurricane, CLONE as in cyclone, EASTER as in nor'easter, and SOON as in monsoon."
   - NEVER output "cyclone" or "hurricane" as the solution item—the items on the board are "CLONE" and "CANE".
5. Pacing & Word Limits:
   - Scene 1 (Hook): Max 18 words. Hook opening.
   - Scene 2 (Decoy trap): Max 22 words. Point out the tempting false group using exact tile names.
   - Scene 3 (Solution reveal + CTA): Max 30 words. Reveal category, name exact tiles explaining wordplay, and conclude with the mandatory CTA.
6. Mandatory CTA: End Scene 3 with: "Test candidate boards at connectionsassistant.com"."""

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ShortBlueprintSchema,
                temperature=0.2,
            ),
        )
        data = json.loads(resp.text)

        # Enforce strict board tile constraint: ensure all 4 solution tiles appear in scene3_narration
        sol_words = [str(w).upper() for w in data.get("solution_words", [])]
        s3 = data.get("scene3_narration", "")
        missing_tiles = [w for w in sol_words if w not in s3.upper()]
        if missing_tiles:
            print(f"    [!] Gemini omitted exact board tile(s) {missing_tiles} in scene3_narration. Enforcing board tile wording.")
            theme = data.get("theme", "TARGET CATEGORY")
            if puzzle_data.get("id") == 1350 or puzzle_data.get("date") == "2026-11-07":
                data["scene3_narration"] = "The category is ENDS OF STORM TYPES: CANE as in hurricane, CLONE as in cyclone, EASTER as in nor'easter, and SOON as in monsoon. Test candidate boards at connectionsassistant.com."
            elif puzzle_data.get("id") == 1351 or puzzle_data.get("date") == "2026-11-08":
                data["scene3_narration"] = "The category is VEGETABLE HOMOPHONES: CARAT as in carrot, CHARRED as in chard, KORN as in corn, and LEAK as in leek. Test candidate boards at connectionsassistant.com."
            elif puzzle_data.get("id") == 1366 or puzzle_data.get("date") == "2026-11-09":
                data["scene3_narration"] = "The category is ENDING IN SEA CREATURES: CARD SHARK ending in shark, FUN SPONGE ending in sponge, GAMMA RAY ending in ray, and NAVY SEAL ending in seal. Test candidate boards at connectionsassistant.com."
            elif puzzle_data.get("id") == 1361 or puzzle_data.get("date") == "2026-11-10":
                data["scene3_narration"] = "The category is WORDS WITH FIVE OF ONE VOWEL: ABRACADABRA with five A's, BEEKEEPER with five E's, INVISIBILITY with five I's, and PROTOZOOLOGY with five O's. Test candidate boards at connectionsassistant.com."
            elif puzzle_data.get("id") in [1250, 1352] or puzzle_data.get("date") == "2026-11-12":
                data["scene3_narration"] = "The category is STARTING WITH BEST PICTURE OSCAR WINNERS: GLADIATOR SANDALS, MARTY MCFLY, MOONLIGHT SONATA, and ROCKY ROAD. Test candidate boards at connectionsassistant.com."
            else:
                data["scene3_narration"] = f"The category is {theme}: {', '.join(sol_words)}. Test candidate boards at connectionsassistant.com."

        return data
    except Exception as e:
        print(f"    [!] Gemini script generation bypassed ({e}); using deterministic blueprint.")
        return None


def get_deterministic_blueprint(puzzle_data: dict) -> dict:
    """Deterministic fallback blueprint generator for daily puzzles."""
    categories = puzzle_data.get("categories", [])
    # Target purple (level 3) or blue (level 2)
    target_cat = next((c for c in categories if c.get("level") == 3), categories[-1])

    theme = target_cat.get("title", "PURPLE CATEGORY").strip().upper()
    solution_words = [str(w).upper() for w in target_cat.get("words", [])]

    # Specific trap for 2026-11-07 / ID 1350
    if puzzle_data.get("id") == 1350 or puzzle_data.get("date") == "2026-11-07":
        decoy_words = ["NORTH", "SOUTH", "EASTER"]
        hook = "THE COMPASS DIRECTION TRAP!"
        s1 = "Stuck on today's Connections board? Before you burn guesses, watch out for this lethal trap."
        s2 = "You see North and South right next to Easter, tempting you into an obvious cardinal directions trap."
        s3 = "The category is ENDS OF STORM TYPES: CANE as in hurricane, CLONE as in cyclone, EASTER as in nor'easter, and SOON as in monsoon. Test candidate boards at connectionsassistant.com."
    elif puzzle_data.get("id") == 1351 or puzzle_data.get("date") == "2026-11-08":
        decoy_words = ["CUT", "TRIM", "BLOWOUT"]
        hook = "THE SALON OVERLAP TRAP!"
        s1 = "Stuck on today's Connections board? Before you burn guesses, watch out for this sneaky overlap."
        s2 = "Seeing Cut next to Trim and Blowout makes hair salon services tempting, but watch for tricky homophones."
        s3 = "The category is VEGETABLE HOMOPHONES: CARAT as in carrot, CHARRED as in chard, KORN as in corn, and LEAK as in leek. Test candidate boards at connectionsassistant.com."
    elif puzzle_data.get("id") == 1366 or puzzle_data.get("date") == "2026-11-09":
        decoy_words = ["CARD SHARK", "CON JOB", "SHELL GAME"]
        hook = "THE CARD SHARK SCAM TRAP!"
        s1 = "Stuck on Monday's Connections board? Before you burn guesses, watch out for this sneaky scam trap."
        s2 = "Seeing Card Shark alongside Con Job and Shell Game makes gambling schemes tempting, but look at word endings."
        s3 = "The category is ENDING IN SEA CREATURES: CARD SHARK ending in shark, FUN SPONGE ending in sponge, GAMMA RAY ending in ray, and NAVY SEAL ending in seal. Test candidate boards at connectionsassistant.com."
    elif puzzle_data.get("id") == 1361 or puzzle_data.get("date") == "2026-11-10":
        decoy_words = ["BEEKEEPER", "APOTHECARY", "SCRIVENER"]
        hook = "THE BEEKEEPER TRADE TRAP!"
        s1 = "Stuck on Tuesday's Connections board? Before you burn guesses, watch out for this sneaky trade trap."
        s2 = "Seeing Beekeeper alongside Apothecary and Scrivener makes historical jobs tempting, but count the vowels!"
        s3 = "The category is WORDS WITH FIVE OF ONE VOWEL: ABRACADABRA with five A's, BEEKEEPER with five E's, INVISIBILITY with five I's, and PROTOZOOLOGY with five O's. Test candidate boards at connectionsassistant.com."
    elif puzzle_data.get("id") in [1250, 1352] or puzzle_data.get("date") == "2026-11-12":
        decoy_words = ["GREAT SCOTT", "FLUX CAPACITOR", "DOC BROWN", "MARTY MCFLY"]
        hook = "THE BACK TO THE FUTURE TRAP!"
        s1 = "Stuck on Thursday's Connections board? Before you burn guesses, watch out for this sneaky sci-fi trap."
        s2 = "Seeing Great Scott, Flux Capacitor, Doc Brown, and Marty McFly tempts an immediate Back to the Future theme!"
        s3 = "The category is STARTING WITH BEST PICTURE OSCAR WINNERS: GLADIATOR SANDALS, MARTY MCFLY, MOONLIGHT SONATA, and ROCKY ROAD. Test candidate boards at connectionsassistant.com."
    else:
        # General fallback
        decoy_words = solution_words[:2]
        hook = f"THE TRICKY {theme} TRAP!"
        s1 = f"Stuck on today's Connections grid? Let's break down the trickiest category before you lose lives."
        s2 = f"Watch out for multi-meaning decoys hiding in plain sight across candidate groupings."
        s3 = f"The category is {theme}: {', '.join(solution_words)}. Test candidate boards at connectionsassistant.com."

    return {
        "hook": hook,
        "theme": theme,
        "tier_name": target_cat.get("tier", "Purple"),
        "tier_color": target_cat.get("tier", "Purple").lower(),
        "decoy_words": decoy_words,
        "solution_words": solution_words,
        "scene1_narration": s1,
        "scene2_narration": s2,
        "scene3_narration": s3,
    }


def get_audio_duration(audio_path: Path) -> float:
    """Get accurate duration of an audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())


async def synthesize_all_narration(blueprint: dict) -> tuple[list[Path], list[float], Path]:
    """Synthesize neural audio for the 3 scenes and concatenate them."""
    scenes_text = [
        blueprint["scene1_narration"],
        blueprint["scene2_narration"],
        blueprint["scene3_narration"],
    ]

    audio_files = []
    durations = []

    for i, text in enumerate(scenes_text, start=1):
        out_file = AUDIO_DIR / f"scene_{i}.mp3"
        print(f"    [Audio] Synthesizing Scene {i} voiceover ({VOICE_NAME} @ {VOICE_RATE}, {VOICE_PITCH})...")
        
        # Retry up to 3 times on transient socket / TTS endpoint drops
        saved = False
        last_err = None
        for attempt in range(1, 4):
            try:
                comm = edge_tts.Communicate(text, VOICE_NAME, rate=VOICE_RATE, pitch=VOICE_PITCH)
                await comm.save(str(out_file))
                saved = True
                break
            except Exception as ex:
                last_err = ex
                print(f"        [!] Edge-TTS attempt {attempt}/3 failed ({ex}). Retrying in 1.5s...")
                await asyncio.sleep(1.5)

        if not saved:
            raise RuntimeError(f"Failed to synthesize Scene {i} audio after 3 attempts: {last_err}")

        dur = get_audio_duration(out_file)
        durations.append(dur)
        audio_files.append(out_file)
        print(f"            Duration: {dur:.2f}s | Text: \"{text[:45]}...\"")

    combined_audio = AUDIO_DIR / "combined_narration.mp3"
    print(f"    [Audio] Concatenating audio tracks into: {combined_audio.name}...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_files[0]),
        "-i", str(audio_files[1]),
        "-i", str(audio_files[2]),
        "-filter_complex", "[0:a][1:a][2:a]concat=n=3:v=0:a=1[outa]",
        "-map", "[outa]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(combined_audio),
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    return audio_files, durations, combined_audio


def get_tile_font_style(word: str) -> tuple[str, str]:
    """Calculate CSS font class and inline style based on string length to strictly prevent wrapping."""
    length = len(word)
    if length <= 6:
        return "len-short", "font-size: 24px;"
    elif length <= 8:
        return "len-med", "font-size: 20px;"
    elif length <= 11:
        return "len-long", "font-size: 16px;"
    elif length <= 13:
        return "len-xlong", "font-size: 14px;"
    else:
        # 14+ letters (e.g. TAPE DISPENSER, GRAPEFRUIT SPOON)
        return "len-xxlong", "font-size: 12.5px;"


def build_board_html(template_str: str, hook: str, badge_html: str, all_words: list[str], highlighted_words: list[str], solved_words: list[str], tier_color: str) -> str:
    """Inject board tiles and styling classes into the template with strict single-line scaling."""
    tile_divs = []
    for w in all_words:
        len_class, font_style = get_tile_font_style(w)
        base_style = f"{font_style} white-space: nowrap; overflow: hidden; text-overflow: clip;"
        if w in solved_words:
            tile_divs.append(f'<div class="tile {len_class} solved-{tier_color.lower()}" style="{base_style}">{w}</div>')
        elif w in highlighted_words:
            tile_divs.append(f'<div class="tile {len_class} highlighted" style="{base_style}">{w}</div>')
        else:
            tile_divs.append(f'<div class="tile {len_class}" style="{base_style}">{w}</div>')

    html = template_str.replace("{{HOOK}}", hook)
    html = html.replace("{{BADGE_HTML}}", badge_html)
    html = html.replace("{{GRID_ITEMS}}", "".join(tile_divs))
    return html


async def render_scene_frames(blueprint: dict, all_words: list[str]) -> list[Path]:
    """Render 3 1080x1920 scenes using Playwright Chromium."""
    if TEMPLATE_PATH.exists():
        raw_template = TEMPLATE_PATH.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Board template missing at '{TEMPLATE_PATH}'")

    frames = []

    # Scene 1: Initial Hook Grid
    s1_html = build_board_html(
        raw_template,
        hook=blueprint["hook"].upper(),
        badge_html='<div class="badge yellow">NYT CONNECTIONS HINTS</div>',
        all_words=all_words,
        highlighted_words=[],
        solved_words=[],
        tier_color=blueprint.get("tier_color", "purple")
    )
    p1 = FRAMES_DIR / "scene_1.png"

    # Scene 2: Decoy Overlap Highlighted
    s2_html = build_board_html(
        raw_template,
        hook="THE DECOY OVERLAP!",
        badge_html='<div class="badge yellow">⚠️ OVERLAPPING TRAP</div>',
        all_words=all_words,
        highlighted_words=blueprint["decoy_words"],
        solved_words=[],
        tier_color=blueprint.get("tier_color", "purple")
    )
    p2 = FRAMES_DIR / "scene_2.png"

    # Scene 3: Solved Category Reveal
    tier_name = blueprint.get("tier_name", "Purple").upper()
    tier_color = blueprint.get("tier_color", "purple").lower()
    s3_html = build_board_html(
        raw_template,
        hook=blueprint["theme"].upper(),
        badge_html=f'<div class="badge {tier_color}">{tier_name} TIER REVEAL</div>',
        all_words=all_words,
        highlighted_words=[],
        solved_words=blueprint["solution_words"],
        tier_color=tier_color
    )
    p3 = FRAMES_DIR / "scene_3.png"

    print("    [Visuals] Launching Playwright Chromium (1080x1920)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for i, (html, out_path) in enumerate([(s1_html, p1), (s2_html, p2), (s3_html, p3)], start=1):
            print(f"    [Visuals] Capturing Scene {i} frame -> {out_path.name}...")
            await page.set_content(html)
            await page.screenshot(path=str(out_path))
            frames.append(out_path)

        await browser.close()

    return frames


def assemble_video_ffmpeg(frames: list[Path], durations: list[float], combined_audio: Path, output_video: Path):
    """Assemble final 1080x1920 MP4 using FFmpeg and NVIDIA NVENC acceleration."""
    concat_txt = OUTPUT_DIR / "video_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for frame, dur in zip(frames, durations):
            f.write(f"file '{frame.resolve().as_posix()}'\n")
            f.write(f"duration {dur:.2f}\n")
        # Concat demuxer requires repeating the last file
        f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

    print(f"    [FFmpeg] Rendering with NVIDIA NVENC (h264_nvenc @ 6 Mbps)...")
    cmd_nvenc = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(combined_audio),
        "-c:v", "h264_nvenc", "-preset", "p6", "-b:v", "6M", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_video),
    ]

    try:
        subprocess.run(cmd_nvenc, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print(f"    [!] NVENC encode failed ({e.stderr.decode('utf-8', errors='ignore')[:120]}); falling back to libx264...")
        cmd_cpu = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_txt),
            "-i", str(combined_audio),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_video),
        ]
        subprocess.run(cmd_cpu, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)


async def generate_daily_short(puzzle_file: Path | None = None) -> Path:
    """Full Shorts generation pipeline."""
    ensure_directories()
    if puzzle_file is None:
        puzzle_file = DEFAULT_PUZZLE

    print(f"\n[1/5] Loading puzzle from: {puzzle_file.name}...")
    puzzle_data = load_puzzle_data(puzzle_file)
    puzzle_date = puzzle_data.get("date", "Today")
    puzzle_id = puzzle_data.get("id", "Unknown")
    print(f"      Puzzle Date: {puzzle_date} | ID: {puzzle_id}")

    # Gather 16 words and shuffle deterministically for natural board layout
    all_words = []
    for cat in puzzle_data.get("categories", []):
        all_words.extend([str(w).upper() for w in cat.get("words", [])])
    
    # Deterministic intermingled grid
    rng = random.Random(int(puzzle_id) if str(puzzle_id).isdigit() else 42)
    shuffled_words = all_words.copy()
    rng.shuffle(shuffled_words)

    print(f"\n[2/5] Formulating Shorts storyboard blueprint...")
    blueprint = generate_blueprint_gemini(puzzle_data) or get_deterministic_blueprint(puzzle_data)
    print(f"      Hook Headline:    {blueprint['hook']}")
    print(f"      Target Category:  {blueprint['theme']} ({blueprint.get('tier_name', 'Purple')})")
    print(f"      Decoy Words:      {', '.join(blueprint['decoy_words'])}")
    print(f"      Solution Words:   {', '.join(blueprint['solution_words'])}")

    print(f"\n[3/5] Synthesizing speech narration via Edge-TTS...")
    audio_files, durations, combined_audio = await synthesize_all_narration(blueprint)
    total_audio_time = sum(durations)
    print(f"      Total Narration Time: {total_audio_time:.2f}s (Paced for sub-30s Shorts)")

    print(f"\n[4/5] Rendering 1080x1920 board frames via Playwright...")
    frames = await render_scene_frames(blueprint, shuffled_words)

    output_video = OUTPUT_DIR / "today_connections_hints.mp4"
    print(f"\n[5/5] Assembling video via FFmpeg NVENC...")
    assemble_video_ffmpeg(frames, durations, combined_audio, output_video)

    # Maintain backward compatibility aliases
    alias_short = OUTPUT_DIR / "today_connections_short.mp4"
    import shutil
    shutil.copyfile(output_video, alias_short)

    file_size_mb = output_video.stat().st_size / (1024 * 1024)
    print(f"\n[✓] Drop 1 Hints Short successfully created!")
    print(f"    Path:      {output_video}")
    print(f"    Alias:     {alias_short.name}")
    print(f"    Duration:  {total_audio_time:.2f}s")
    print(f"    Size:      {file_size_mb:.2f} MB")
    print(f"    Format:    1080x1920 Vertical MP4 (30 FPS)")

    return output_video


def main():
    parser = argparse.ArgumentParser(description="Generate daily YouTube Short from daily_puzzle.json.")
    parser.add_argument(
        "--puzzle",
        default=None,
        help="Path to daily_puzzle.json (defaults to daily_puzzle.json in root)",
    )
    args = parser.parse_args()

    puzzle_path = Path(args.puzzle).resolve() if args.puzzle else None

    try:
        asyncio.run(generate_daily_short(puzzle_file=puzzle_path))
    except Exception as e:
        print(f"\n[!] Pipeline Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
