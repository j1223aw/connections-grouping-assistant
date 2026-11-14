"""
generate_full_solution_short.py

YouTube Shorts Drop 2: Full Board Walkthrough Pipeline.
Generates high-retention 1080x1920 vertical Shorts solving the NYT Connections puzzle
strictly tier-by-tier in order:
🟨 Yellow (Level 0) -> 🟩 Green (Level 1) -> 🟦 Blue (Level 2) -> 🟪 Purple (Level 3).

Spec:
- Pacing: ~35-45 seconds across 4 scenes.
- Visuals: 8 synchronized frames (Highlight candidate tiles -> Snap solved banner into place).
- Audio: Neural edge-tts narration explaining each tier's identity, semantics, and wordplay.
- FFmpeg compilation via NVIDIA NVENC hardware acceleration (h264_nvenc @ 6 Mbps).
- Outputs:
  - output_shorts/today_connections_full_solution.mp4
  - output_shorts/today_full_solution_short.mp4
  - output_shorts/today_full_solution_metadata.txt
"""

import argparse
import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
from typing import Dict, List, Tuple

import edge_tts
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output_shorts"
FRAMES_DIR = OUTPUT_DIR / "solution_frames"
AUDIO_DIR = OUTPUT_DIR / "audio"
DEFAULT_PUZZLE = ROOT_DIR / "daily_puzzle.json"
TEMPLATE_PATH = ROOT_DIR / "video_pipeline" / "templates" / "full_solution_template.html"

VOICE_NAME = "en-US-GuyNeural"
VOICE_RATE = "+0%"
VOICE_PITCH = "-8Hz"


def ensure_directories():
    """Ensure output directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def load_puzzle_data(puzzle_file: Path) -> dict:
    """Load and validate daily_puzzle.json."""
    if not puzzle_file.exists():
        raise FileNotFoundError(f"Puzzle file not found at '{puzzle_file}'.")
    with open(puzzle_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "categories" not in data or len(data["categories"]) < 4:
        raise ValueError("Invalid daily_puzzle.json format: expected 4 categories.")
    return data


def get_audio_duration(audio_path: Path) -> float:
    """Get accurate duration of an audio file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())


def generate_curated_solution_script(puzzle_data: dict) -> Dict[str, str]:
    """Generate precise ordered narration script for the 4 tiers."""
    pid = str(puzzle_data.get("id", ""))
    pdate = str(puzzle_data.get("date", ""))

    cats = {c.get("level", idx): c for idx, c in enumerate(puzzle_data.get("categories", []))}
    y = cats.get(0, {})
    g = cats.get(1, {})
    b = cats.get(2, {})
    p = cats.get(3, {})

    y_words = ", ".join(y.get("words", []))
    g_words = ", ".join(g.get("words", []))
    b_words = ", ".join(b.get("words", []))
    p_words = ", ".join(p.get("words", []))

    # Known curated scripts for specific puzzles
    if pid == "1361" or pdate == "2026-11-10":
        return {
            "yellow": "Starting with Yellow: BROUHAHA, FOOFARAW, HULLABALOO, and KERFUFFLE are all lively synonyms for an uproar or hubbub.",
            "green": "Next is Green: HYPERBOLE, METONYMY, ONOMATOPOEIA, and OXYMORON are all fundamental literary and rhetorical devices.",
            "blue": "Moving to Blue, don't let Beekeeper fool you: APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT are four true old-timey occupations.",
            "purple": "Finally, Purple reveals vowel frequency: ABRACADABRA has five A's, BEEKEEPER has five E's, INVISIBILITY has five I's, and PROTOZOOLOGY has five O's. Test tomorrow's board without spoilers at connectionsassistant.com!",
        }
    elif pid == "1366" or pdate == "2026-11-09":
        return {
            "yellow": "Starting with Yellow: CON JOB, FLIMFLAM, RIP-OFF, and SHELL GAME are all synonyms for a deceitful scheme.",
            "green": "Next is Green: BOOTCUT, DISTRESSED, LOW-RISE, and SKINNY are classic cuts and descriptors for jeans.",
            "blue": "Moving to Blue, the link turns physical: GRAPEFRUIT SPOON, MINT LEAF, STEAK KNIFE, and TAPE DISPENSER all feature serrated edges.",
            "purple": "Finally, Purple reveals the lateral wordplay: CARD SHARK, FUN SPONGE, GAMMA RAY, and NAVY SEAL all end in marine animals—shark, sponge, ray, and seal. Test tomorrow's board without spoilers at connectionsassistant.com!",
        }
    elif pid == "1351" or pdate == "2026-11-08":
        return {
            "yellow": "Starting with Yellow: TRIM, BLOWOUT, COLOR, and EXTENSIONS are all classic hair salon services.",
            "green": "Next is Green: BUILT, JACKED, RIPPED, and SOLID are all adjectives for a muscular physique.",
            "blue": "Moving to Blue: BRACKET, DIVISION, FIELD, and POOL are all sports tournament groupings.",
            "purple": "Finally, Purple reveals clever vegetable homophones: CARAT for carrot, CHARRED for chard, KORN for corn, and LEAK for leek. Test tomorrow's board without spoilers at connectionsassistant.com!",
        }
    elif pid in ["1250", "1352"] or pdate == "2026-11-12":
        return {
            "yellow": "Starting with Yellow: GOOD HEAVENS, GREAT SCOTT, HOLY SMOKES, and JIMINY CRICKET are all vintage exclamations of surprise.",
            "green": "Next is Green: CHANGE PURSE, FLUX CAPACITOR, SHIFT DRESS, and SWING SET all start with synonyms for variation and change.",
            "blue": "Moving to Blue: ARCTIC CHAR, COMEDY ROAST, DOC BROWN, and YOU'RE TOAST all end in culinary cooking methods—char, roast, brown, and toast.",
            "purple": "Finally, Purple reveals Hollywood trivia: GLADIATOR SANDALS, MARTY MCFLY, MOONLIGHT SONATA, and ROCKY ROAD all begin with Oscar Best Picture winners. Test tomorrow's board without spoilers at connectionsassistant.com!",
        }
    elif pid == "1350" or pdate == "2026-11-07":
        return {
            "yellow": f"Starting with Yellow: {y_words} all share direct synonyms for {y.get('title', 'the category').lower()}.",
            "green": f"Next is Green: {g_words} fit cleanly together as {g.get('title', 'the category').lower()}.",
            "blue": f"Moving to Blue: {b_words} all connect under {b.get('title', 'the category').lower()}.",
            "purple": f"Finally, Purple is lateral wordplay: CANE as in hurricane, CLONE as in cyclone, EASTER as in nor'easter, and SOON as in monsoon. Test tomorrow's board without spoilers at connectionsassistant.com!",
        }

    # High-quality dynamic fallback for any day's puzzle
    return {
        "yellow": f"Starting with Yellow: {y_words} are direct synonyms for {y.get('title', 'the group').lower()}.",
        "green": f"Next is Green: {g_words} all represent {g.get('title', 'the category').lower()}.",
        "blue": f"Moving to Blue: {b_words} share the connection of {b.get('title', 'the category').lower()}.",
        "purple": f"Finally, Purple solves {p.get('title', 'lateral wordplay').upper()}: {p_words}. Test tomorrow's board without spoilers at connectionsassistant.com!",
    }


async def synthesize_tier_audio(script_dict: Dict[str, str]) -> Tuple[List[Path], List[float], Path]:
    """Synthesize voiceover for all 4 tiers and concatenate into a single soundtrack."""
    tiers = ["yellow", "green", "blue", "purple"]
    audio_files = []
    durations = []

    for tier in tiers:
        text = script_dict[tier]
        out_file = AUDIO_DIR / f"solution_{tier}.mp3"
        print(f"    [Audio] Synthesizing {tier.upper()} voiceover ({VOICE_NAME} @ {VOICE_RATE})...")

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
            raise RuntimeError(f"Failed to synthesize {tier} audio after 3 attempts: {last_err}")

        dur = get_audio_duration(out_file)
        durations.append(dur)
        audio_files.append(out_file)
        print(f"        Duration: {dur:.2f}s | Text: \"{text[:45]}...\"")

    combined_audio = AUDIO_DIR / "solution_combined_narration.mp3"
    print(f"    [Audio] Concatenating 4 audio tracks into: {combined_audio.name}...")
    concat_cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_files[0]),
        "-i", str(audio_files[1]),
        "-i", str(audio_files[2]),
        "-i", str(audio_files[3]),
        "-filter_complex", "[0:a][1:a][2:a][3:a]concat=n=4:v=0:a=1[outa]",
        "-map", "[outa]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(combined_audio),
    ]
    subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    return audio_files, durations, combined_audio


def get_tile_font_class(word: str) -> str:
    """Classify tile word length for single-line text rendering."""
    length = len(word)
    if length <= 6:
        return "len-short"
    elif length <= 8:
        return "len-med"
    elif length <= 11:
        return "len-long"
    elif length <= 13:
        return "len-xlong"
    return "len-xxlong"


def format_banner_html(cat: dict) -> str:
    """Render a single full-width solved category banner."""
    tier = str(cat.get("tier", "Yellow")).lower()
    title = str(cat.get("title", "")).upper()
    words = [str(w).upper() for w in cat.get("words", [])]
    words_str = " &bull; ".join(words)

    extra_class = ""
    if len(words_str) > 55:
        extra_class = "len-xlong"
    elif len(words_str) > 42:
        extra_class = "len-long"

    return f"""
    <div class="solved-banner {tier}">
      <div class="banner-category">{title}</div>
      <div class="banner-words {extra_class}">{words_str}</div>
    </div>
    """


def render_html_page(
    template_str: str,
    date_label: str,
    headline: str,
    badge_html: str,
    solved_categories: List[dict],
    active_tiles: List[str],
    highlighted_words: List[str],
    highlight_tier: str = "yellow",
) -> str:
    """Generate complete HTML page for a specific board transition."""
    # Build solved banners stack
    banners_html = ""
    if solved_categories:
        rendered_banners = [format_banner_html(cat) for cat in solved_categories]
        banners_html = f'<div class="banners-stack">{"".join(rendered_banners)}</div>'

    # Build remaining tiles grid
    tiles_grid_html = ""
    if active_tiles:
        tile_elements = []
        for word in active_tiles:
            fclass = get_tile_font_class(word)
            if word in highlighted_words:
                hclass = f"highlight-{highlight_tier.lower()}"
                tile_elements.append(f'<div class="tile {fclass} {hclass}">{word}</div>')
            else:
                tile_elements.append(f'<div class="tile {fclass}">{word}</div>')
        tiles_grid_html = f'<div class="tiles-grid">{"".join(tile_elements)}</div>'

    html = template_str.replace("{{DATE_LABEL}}", date_label)
    html = html.replace("{{HEADLINE}}", headline)
    html = html.replace("{{BADGE_HTML}}", badge_html)
    html = html.replace("{{BANNERS_HTML}}", banners_html)
    html = html.replace("{{TILES_GRID_HTML}}", tiles_grid_html)
    return html


async def render_all_frames(
    puzzle_data: dict,
    template_str: str,
    date_label: str,
) -> List[Tuple[Path, float]]:
    """
    Render the 8 distinct frames (2 per tier) using Playwright Chromium:
    - Frame 1a: All 16 tiles, Yellow highlighted
    - Frame 1b: Yellow solved banner + remaining 12 tiles
    - Frame 2a: Yellow solved banner + remaining 12 tiles with Green highlighted
    - Frame 2b: Yellow + Green solved banners + remaining 8 tiles
    - Frame 3a: Yellow + Green solved banners + remaining 8 tiles with Blue highlighted
    - Frame 3b: Yellow + Green + Blue solved banners + remaining 4 tiles
    - Frame 4a: 3 solved banners + remaining 4 Purple tiles highlighted
    - Frame 4b: All 4 solved banners (Board Complete!)
    """
    # Extract categories sorted strictly by level (0 to 3)
    cats_by_level = {c.get("level", idx): c for idx, c in enumerate(puzzle_data.get("categories", []))}
    y = cats_by_level[0]
    g = cats_by_level[1]
    b = cats_by_level[2]
    p = cats_by_level[3]

    # Initial starting board
    starting_board = puzzle_data.get("starting_board")
    if not starting_board or len(starting_board) < 16:
        # Deterministic shuffle fallback
        all_words = []
        for cat in [y, g, b, p]:
            all_words.extend([str(w).upper() for w in cat.get("words", [])])
        rng = random.Random(int(puzzle_data.get("id", 42)))
        starting_board = all_words.copy()
        rng.shuffle(starting_board)
    else:
        starting_board = [str(w).upper() for w in starting_board]

    # Active tiles remaining as each tier is solved
    board_16 = starting_board.copy()
    board_12 = [w for w in board_16 if w not in y["words"]]
    board_8 = [w for w in board_12 if w not in g["words"]]
    board_4 = [w for w in board_8 if w not in b["words"]]

    # Frame specs: (filename, headline, badge_html, solved_cats, active_tiles, hl_words, hl_tier)
    frame_specs = [
        # Scene 1: Yellow
        (
            "frame_1a_yellow_hl.png",
            "STEP 1: YELLOW TIER",
            '<div class="badge yellow">🟨 LEVEL 0 &bull; SYNONYMS</div>',
            [],
            board_16,
            y["words"],
            "yellow",
        ),
        (
            "frame_1b_yellow_solved.png",
            "YELLOW SOLVED!",
            f'<div class="badge yellow">🟨 {y["title"].upper()}</div>',
            [y],
            board_12,
            [],
            "yellow",
        ),
        # Scene 2: Green
        (
            "frame_2a_green_hl.png",
            "STEP 2: GREEN TIER",
            '<div class="badge green">🟩 LEVEL 1 &bull; CONTEXTUAL</div>',
            [y],
            board_12,
            g["words"],
            "green",
        ),
        (
            "frame_2b_green_solved.png",
            "GREEN SOLVED!",
            f'<div class="badge green">🟩 {g["title"].upper()}</div>',
            [y, g],
            board_8,
            [],
            "green",
        ),
        # Scene 3: Blue
        (
            "frame_3a_blue_hl.png",
            "STEP 3: BLUE TIER",
            '<div class="badge blue">🟦 LEVEL 2 &bull; SEMANTIC</div>',
            [y, g],
            board_8,
            b["words"],
            "blue",
        ),
        (
            "frame_3b_blue_solved.png",
            "BLUE SOLVED!",
            f'<div class="badge blue">🟦 {b["title"].upper()}</div>',
            [y, g, b],
            board_4,
            [],
            "blue",
        ),
        # Scene 4: Purple
        (
            "frame_4a_purple_hl.png",
            "STEP 4: PURPLE TIER",
            '<div class="badge purple">🟪 LEVEL 3 &bull; LATERAL WORDPLAY</div>',
            [y, g, b],
            board_4,
            p["words"],
            "purple",
        ),
        (
            "frame_4b_purple_solved.png",
            "BOARD SOLVED!",
            '<div class="badge complete">🎯 PERFECT SOLVE</div>',
            [y, g, b, p],
            [],
            [],
            "purple",
        ),
    ]

    rendered_files = []
    print("    [Visuals] Launching Playwright Chromium for 8-frame sequence (1080x1920)...")
    async with async_playwright() as p_playwright:
        browser = await p_playwright.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for spec in frame_specs:
            fname, headline, badge_html, solved_cats, active_tiles, hl_words, hl_tier = spec
            html = render_html_page(
                template_str=template_str,
                date_label=date_label,
                headline=headline,
                badge_html=badge_html,
                solved_categories=solved_cats,
                active_tiles=active_tiles,
                highlighted_words=hl_words,
                highlight_tier=hl_tier,
            )
            out_file = FRAMES_DIR / fname
            print(f"    [Visuals] Capturing {fname}...")
            await page.set_content(html)
            await page.screenshot(path=str(out_file))
            rendered_files.append(out_file)

        await browser.close()

    return rendered_files


def calculate_frame_durations(tier_durations: List[float]) -> List[float]:
    """
    Calculate precise sub-frame durations for the 8 frames matching 4 audio scenes.
    For each tier:
    - Frame A (Highlight): 2.2s (or 28% of tier duration)
    - Frame B (Solved): Remaining duration
    """
    frame_durs = []
    for dur in tier_durations:
        dur_a = min(2.4, dur * 0.28)
        dur_b = dur - dur_a
        frame_durs.extend([dur_a, dur_b])
    return frame_durs


def assemble_full_solution_mp4(
    frames: List[Path],
    durations: List[float],
    combined_audio: Path,
    output_video: Path,
):
    """Assemble final MP4 using FFmpeg concat demuxer and NVENC hardware encoder."""
    concat_txt = OUTPUT_DIR / "solution_video_concat.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for frame, dur in zip(frames, durations):
            f.write(f"file '{frame.resolve().as_posix()}'\n")
            f.write(f"duration {dur:.2f}\n")
        # Concat demuxer requires repeating the final file
        f.write(f"file '{frames[-1].resolve().as_posix()}'\n")

    print("    [FFmpeg] Compiling 1080x1920 MP4 via NVIDIA NVENC (h264_nvenc @ 6 Mbps)...")
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
        print(f"    [!] NVENC failed ({e.stderr.decode('utf-8', errors='ignore')[:120]}); falling back to libx264...")
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


def stage_metadata(puzzle_data: dict, output_file: Path) -> str:
    """Format and write metadata for Drop 2."""
    pdate = puzzle_data.get("date", "Today")
    pid = puzzle_data.get("id", "")

    cats_by_level = {c.get("level", 0): c for c in puzzle_data.get("categories", [])}
    y_title = cats_by_level.get(0, {}).get("title", "Yellow").title()
    g_title = cats_by_level.get(1, {}).get("title", "Green").title()
    b_title = cats_by_level.get(2, {}).get("title", "Blue").title()
    p_title = cats_by_level.get(3, {}).get("title", "Purple").title()

    title = f"NYT Connections Solution Today - {pdate} | Full Ordered Walkthrough #shorts #nytconnections"
    description = (
        f"Full step-by-step ordered solution for today's NYT Connections (#{pid} - {pdate}):\n\n"
        f"🟨 TIER 1 • EASIEST (Direct Synonyms): {y_title}\n"
        f"🟩 TIER 2 • MODERATE (Contextual Link): {g_title}\n"
        f"🟦 TIER 3 • CHALLENGING (Trivia & Patterns): {b_title}\n"
        f"🟪 TIER 4 • TRICKIEST (Lateral Wordplay): {p_title}\n\n"
        "Test candidate groups on our free interactive scratchboard without burning guesses:\n"
        "https://connectionsassistant.com/breakdowns.html\n\n"
        "#NYTConnections #ConnectionsSolution #WordPuzzle #BrainTeaser #Shorts"
    )
    pinned_comment = (
        "Solve today's puzzle without spoilers or test your theories at: "
        "https://connectionsassistant.com/breakdowns.html"
    )
    tags = (
        "NYT Connections, Connections solution today, Connections full walkthrough, "
        "NYT Connections answers, Connections hints, Connections Assistant, Wordle Solver"
    )

    content = f"""------------------- VIDEO TITLE -------------------
{title}

------------------- DESCRIPTION -------------------
{description}

----------------- PINNED COMMENT -----------------
{pinned_comment}

---------------------- TAGS ----------------------
{tags}
"""
    output_file.write_text(content, encoding="utf-8")
    return content


async def generate_full_solution_pipeline(puzzle_file: Path | None = None) -> Tuple[Path, Path]:
    """Execute complete Drop 2 pipeline."""
    ensure_directories()
    if puzzle_file is None:
        puzzle_file = DEFAULT_PUZZLE

    print(f"\n[1/5] Loading puzzle from: {puzzle_file.name}...")
    puzzle_data = load_puzzle_data(puzzle_file)
    pdate = puzzle_data.get("date", "Today")
    pid = puzzle_data.get("id", "Unknown")

    try:
        dt = datetime.strptime(pdate, "%Y-%m-%d")
        date_label = f"{dt.strftime('%A, %b')} {dt.day}, {dt.year}".upper()
    except Exception:
        date_label = str(pdate).upper()

    print(f"      Date: {pdate} ({date_label}) | Puzzle #{pid}")

    print("\n[2/5] Formulating 4-tier ordered solution script...")
    scripts = generate_curated_solution_script(puzzle_data)
    for tier, line in scripts.items():
        print(f"      [{tier.upper():6}] {line}")

    print("\n[3/5] Synthesizing speech narration via Edge-TTS...")
    audio_files, tier_durations, combined_audio = await synthesize_tier_audio(scripts)
    total_audio_time = sum(tier_durations)
    print(f"      Total Narration Time: {total_audio_time:.2f}s (Paced for 35-45s Short)")

    print("\n[4/5] Rendering 8-frame sequential board states via Playwright...")
    template_str = TEMPLATE_PATH.read_text(encoding="utf-8")
    frames = await render_all_frames(puzzle_data, template_str, date_label)
    frame_durations = calculate_frame_durations(tier_durations)

    output_video = OUTPUT_DIR / "today_connections_full_solution.mp4"
    print("\n[5/5] Assembling final video via FFmpeg NVENC...")
    assemble_full_solution_mp4(frames, frame_durations, combined_audio, output_video)

    # Also create alias today_full_solution_short.mp4
    alias_video = OUTPUT_DIR / "today_full_solution_short.mp4"
    shutil.copyfile(output_video, alias_video)

    # Stage metadata file
    meta_path = OUTPUT_DIR / "today_full_solution_metadata.txt"
    stage_metadata(puzzle_data, meta_path)

    file_size_mb = output_video.stat().st_size / (1024 * 1024)
    print(f"\n[✓] Drop 2 Full Solution Short successfully created!")
    print(f"    Path:      {output_video}")
    print(f"    Duration:  {total_audio_time:.2f}s")
    print(f"    Size:      {file_size_mb:.2f} MB")
    print(f"    Format:    1080x1920 Vertical MP4 (30 FPS)")
    print(f"    Metadata:  {meta_path.name}")

    return output_video, meta_path


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube Shorts Drop 2 (Full Board Walkthrough).")
    parser.add_argument("--puzzle", default=None, help="Path to daily_puzzle.json")
    args = parser.parse_args()

    puzzle_path = Path(args.puzzle).resolve() if args.puzzle else None
    try:
        asyncio.run(generate_full_solution_pipeline(puzzle_path))
    except Exception as err:
        print(f"\n[!] Error generating full solution short: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
