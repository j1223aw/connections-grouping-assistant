"""
sync_daily_web.py

Automated Multi-Page Banner Sync & breakdowns.html Staging Pipeline.

Responsibilities:
1. Parse daily_puzzle.json to extract the puzzle date, day of the week, and primary decoy trap.
2. Programmatically update announcement banners across:
   - public/index.html
   - public/strategy.html
   - public/faq.html
   - public/nyt-connections-guide.html
   Using the format:
   `Stuck on today's {trap_name}? Watch {day_name}'s breakdown →`
   Ensuring link target is `breakdowns.html#today`.
3. Programmatically stage public/breakdowns.html:
   - Header text: `{day_name}, {formatted_date} • Puzzle #{puzzle_number}`
   - Subtitle: Describing the revealed Purple wordplay category and overlapping decoy trap.
   - YouTube iframe embed target: set to the latest Short ID.
   - Dynamic 16 board tiles and tier legend chips.
4. Optional one-step deployment:
   - Runs `firebase deploy --only hosting` when --deploy is flagged.
   - Supports --dry-run for non-destructive inspection.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple


BANNER_PAGES = [
    Path("public/index.html"),
    Path("public/strategy.html"),
    Path("public/faq.html"),
    Path("public/nyt-connections-guide.html"),
]

# Known curated puzzle metadata for verified breakdowns
CURATED_PUZZLE_METADATA: Dict[str, Dict[str, str]] = {
    "1360": {
        "trap_name": "3-tier WATER & OCEAN decoy or BRAIN ___ compounds",
        "purple_title": "BRAIN ___",
        "decoy_subtitle": "the 3-tier <strong>WATER & OCEAN</strong> decoy trap",
        "red_herring_advisory": (
            "<em>SURF, WAVES, WATER SKIER, and BARGE</em> tempt an immediate water/ocean grouping! "
            "However, every single one belongs to a completely different tier: "
            "<em>SURF</em> is an Internet action (Yellow), <em>WAVES</em> is a Brain compound (Purple), "
            "and <em>BARGE</em> and <em>WATER SKIER</em> are things that are towed (Blue). "
            "Do not burn a guess grouping them together!"
        ),
        "wordplay_breakdown": (
            "The Purple group connects compound words and idioms beginning with 'BRAIN': "
            "<em>BRAIN FREEZE</em>, <em>BRAIN TEASER</em>, <em>BRAIN TRUST</em>, and <em>BRAIN WAVES</em>."
        ),
    },
    "2026-11-13": {
        "trap_name": "3-tier WATER & OCEAN decoy or BRAIN ___ compounds",
        "purple_title": "BRAIN ___",
        "decoy_subtitle": "the 3-tier <strong>WATER & OCEAN</strong> decoy trap",
        "red_herring_advisory": (
            "<em>SURF, WAVES, WATER SKIER, and BARGE</em> tempt an immediate water/ocean grouping! "
            "However, every single one belongs to a completely different tier: "
            "<em>SURF</em> is an Internet action (Yellow), <em>WAVES</em> is a Brain compound (Purple), "
            "and <em>BARGE</em> and <em>WATER SKIER</em> are things that are towed (Blue). "
            "Do not burn a guess grouping them together!"
        ),
        "wordplay_breakdown": (
            "The Purple group connects compound words and idioms beginning with 'BRAIN': "
            "<em>BRAIN FREEZE</em>, <em>BRAIN TEASER</em>, <em>BRAIN TRUST</em>, and <em>BRAIN WAVES</em>."
        ),
    },
    "1351": {
        "trap_name": "5-word CUT decoy or vegetable homophones",
        "purple_title": "VEGETABLE HOMOPHONES",
        "decoy_subtitle": "the 5-word <strong>CUT</strong> salon decoy trap",
        "red_herring_advisory": (
            "<em>CUT</em> connects to both <strong>HAIR SALON SERVICES</strong> "
            "(with <em>TRIM, BLOWOUT, COLOR, EXTENSIONS</em>) and <strong>MUSCULAR</strong> "
            "(with <em>BUILT, JACKED, RIPPED</em>). Isolating the physical fitness tier immediately "
            "neutralizes the decoy trap."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on vegetable homophones: "
            "<em>CARAT</em> (carrot), <em>CHARRED</em> (chard), <em>KORN</em> (corn), and <em>LEAK</em> (leek)."
        ),
    },
    "2026-11-08": {
        "trap_name": "5-word CUT decoy or vegetable homophones",
        "purple_title": "VEGETABLE HOMOPHONES",
        "decoy_subtitle": "the 5-word <strong>CUT</strong> salon decoy trap",
        "red_herring_advisory": (
            "<em>CUT</em> connects to both <strong>HAIR SALON SERVICES</strong> "
            "(with <em>TRIM, BLOWOUT, COLOR, EXTENSIONS</em>) and <strong>MUSCULAR</strong> "
            "(with <em>BUILT, JACKED, RIPPED</em>). Isolating the physical fitness tier immediately "
            "neutralizes the decoy trap."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on vegetable homophones: "
            "<em>CARAT</em> (carrot), <em>CHARRED</em> (chard), <em>KORN</em> (corn), and <em>LEAK</em> (leek)."
        ),
    },
    "1350": {
        "trap_name": "cardinal directions decoy or storm endings",
        "purple_title": "ENDS OF STORM TYPES",
        "decoy_subtitle": "the cardinal directions decoy trap",
        "red_herring_advisory": (
            "<em>EASTER</em> appears alongside <em>NORTH</em> and <em>SOUTH</em>, creating an alluring "
            "compass direction trap. Isolating the storm endings neutralizes the decoy."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on storm endings: "
            "<em>CANE</em> (hurricane), <em>CLONE</em> (cyclone), <em>EASTER</em> (nor'easter), and <em>SOON</em> (monsoon)."
        ),
    },
    "2026-11-07": {
        "trap_name": "cardinal directions decoy or storm endings",
        "purple_title": "ENDS OF STORM TYPES",
        "decoy_subtitle": "the cardinal directions decoy trap",
        "red_herring_advisory": (
            "<em>EASTER</em> appears alongside <em>NORTH</em> and <em>SOUTH</em>, creating an alluring "
            "compass direction trap. Isolating the storm endings neutralizes the decoy."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on storm endings: "
            "<em>CANE</em> (hurricane), <em>CLONE</em> (cyclone), <em>EASTER</em> (nor'easter), and <em>SOON</em> (monsoon)."
        ),
    },
    "1366": {
        "trap_name": "CARD SHARK scam decoy or sea creature endings",
        "purple_title": "ENDING IN SEA CREATURES",
        "decoy_subtitle": "the 5-word <strong>CARD SHARK</strong> scam decoy trap",
        "red_herring_advisory": (
            "<em>CARD SHARK</em> appears alongside <em>CON JOB, SHELL GAME, FLIMFLAM, and RIP-OFF</em>, "
            "tempting an immediate deceitful scheme grouping. However, recognizing that <em>CARD SHARK</em> "
            "ends with a marine animal (shark) unlocks the Purple tier and leaves the four true swindles intact."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on compound terms ending in sea creatures: "
            "<em>CARD SHARK</em> (shark), <em>FUN SPONGE</em> (sponge), <em>GAMMA RAY</em> (ray), and <em>NAVY SEAL</em> (seal)."
        ),
    },
    "2026-11-09": {
        "trap_name": "CARD SHARK scam decoy or sea creature endings",
        "purple_title": "ENDING IN SEA CREATURES",
        "decoy_subtitle": "the 5-word <strong>CARD SHARK</strong> scam decoy trap",
        "red_herring_advisory": (
            "<em>CARD SHARK</em> appears alongside <em>CON JOB, SHELL GAME, FLIMFLAM, and RIP-OFF</em>, "
            "tempting an immediate deceitful scheme grouping. However, recognizing that <em>CARD SHARK</em> "
            "ends with a marine animal (shark) unlocks the Purple tier and leaves the four true swindles intact."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on compound terms ending in sea creatures: "
            "<em>CARD SHARK</em> (shark), <em>FUN SPONGE</em> (sponge), <em>GAMMA RAY</em> (ray), and <em>NAVY SEAL</em> (seal)."
        ),
    },
    "1361": {
        "trap_name": "BEEKEEPER trade decoy or five-vowel words",
        "purple_title": "WORDS WITH FIVE OF ONE VOWEL",
        "decoy_subtitle": "the 5-word <strong>BEEKEEPER</strong> trade decoy trap",
        "red_herring_advisory": (
            "<em>BEEKEEPER</em> appears alongside <em>APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT</em>, "
            "tempting an immediate historical occupation grouping. However, recognizing that <em>BEEKEEPER</em> "
            "contains five E's unlocks the Purple vowel tier and leaves the four true old-timey trades intact."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on words containing five of a single vowel: "
            "<em>ABRACADABRA</em> (five A's), <em>BEEKEEPER</em> (five E's), <em>INVISIBILITY</em> (five I's), and <em>PROTOZOOLOGY</em> (five O's)."
        ),
    },
    "2026-11-10": {
        "trap_name": "BEEKEEPER trade decoy or five-vowel words",
        "purple_title": "WORDS WITH FIVE OF ONE VOWEL",
        "decoy_subtitle": "the 5-word <strong>BEEKEEPER</strong> trade decoy trap",
        "red_herring_advisory": (
            "<em>BEEKEEPER</em> appears alongside <em>APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT</em>, "
            "tempting an immediate historical occupation grouping. However, recognizing that <em>BEEKEEPER</em> "
            "contains five E's unlocks the Purple vowel tier and leaves the four true old-timey trades intact."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on words containing five of a single vowel: "
            "<em>ABRACADABRA</em> (five A's), <em>BEEKEEPER</em> (five E's), <em>INVISIBILITY</em> (five I's), and <em>PROTOZOOLOGY</em> (five O's)."
        ),
    },
    "1249": {
        "trap_name": "rainbow TEA decoy or words ending in palindromes",
        "purple_title": "WORDS ENDING IN PALINDROMES",
        "decoy_subtitle": "the 4-color <strong>TEA</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREEN, AFTERNOON, BUBBLE, and HERBAL</em> tempt an immediate 'Types of Tea' grouping. "
            "However, recognizing that each belongs to a different tier (Golf, Palindromes, Inflatables, Medicine) "
            "dissolves the decoy and keeps all four groups clean."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on words ending in palindromes: "
            "<em>AFTERNOON</em> (noon), <em>PATOOT</em> (toot), <em>RHEOSTATS</em> (stats), and <em>SHREDDER</em> (redder)."
        ),
    },
    "1250": {
        "trap_name": "BACK TO THE FUTURE decoy or Oscar Best Picture winners",
        "purple_title": "STARTING WITH BEST PICTURE OSCAR WINNERS",
        "decoy_subtitle": "the 4-color <strong>BACK TO THE FUTURE</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY</em> immediately suggest a "
            "4-word sci-fi movie theme! However, every single one belongs to a completely different tier: "
            "<em>GREAT SCOTT</em> is an exclamation (Yellow), <em>FLUX CAPACITOR</em> starts with a variation (Green), "
            "<em>DOC BROWN</em> ends in a cooking method (Blue), and <em>MARTY MCFLY</em> starts with an Oscar winner (Purple). "
            "Do not burn a guess grouping them together!"
        ),
        "wordplay_breakdown": (
            "The Purple group connects phrases whose opening words won the Academy Award for Best Picture: "
            "<em>GLADIATOR</em> SANDALS (Gladiator, 2000), <em>MARTY</em> MCFLY (Marty, 1955), "
            "<em>MOONLIGHT</em> SONATA (Moonlight, 2016), and <em>ROCKY</em> ROAD (Rocky, 1976)."
        ),
    },
    "1352": {
        "trap_name": "BACK TO THE FUTURE decoy or Oscar Best Picture winners",
        "purple_title": "STARTING WITH BEST PICTURE OSCAR WINNERS",
        "decoy_subtitle": "the 4-color <strong>BACK TO THE FUTURE</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY</em> immediately suggest a "
            "4-word sci-fi movie theme! However, every single one belongs to a completely different tier: "
            "<em>GREAT SCOTT</em> is an exclamation (Yellow), <em>FLUX CAPACITOR</em> starts with a variation (Green), "
            "<em>DOC BROWN</em> ends in a cooking method (Blue), and <em>MARTY MCFLY</em> starts with an Oscar winner (Purple). "
            "Do not burn a guess grouping them together!"
        ),
        "wordplay_breakdown": (
            "The Purple group connects phrases whose opening words won the Academy Award for Best Picture: "
            "<em>GLADIATOR</em> SANDALS (Gladiator, 2000), <em>MARTY</em> MCFLY (Marty, 1955), "
            "<em>MOONLIGHT</em> SONATA (Moonlight, 2016), and <em>ROCKY</em> ROAD (Rocky, 1976)."
        ),
    },
    "2026-11-12": {
        "trap_name": "BACK TO THE FUTURE decoy or Oscar Best Picture winners",
        "purple_title": "STARTING WITH BEST PICTURE OSCAR WINNERS",
        "decoy_subtitle": "the 4-color <strong>BACK TO THE FUTURE</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY</em> immediately suggest a "
            "4-word sci-fi movie theme! However, every single one belongs to a completely different tier: "
            "<em>GREAT SCOTT</em> is an exclamation (Yellow), <em>FLUX CAPACITOR</em> starts with a variation (Green), "
            "<em>DOC BROWN</em> ends in a cooking method (Blue), and <em>MARTY MCFLY</em> starts with an Oscar winner (Purple). "
            "Do not burn a guess grouping them together!"
        ),
        "wordplay_breakdown": (
            "The Purple group connects phrases whose opening words won the Academy Award for Best Picture: "
            "<em>GLADIATOR</em> SANDALS (Gladiator, 2000), <em>MARTY</em> MCFLY (Marty, 1955), "
            "<em>MOONLIGHT</em> SONATA (Moonlight, 2016), and <em>ROCKY</em> ROAD (Rocky, 1976)."
        ),
    },
    "1354": {
        "trap_name": "rainbow TEA decoy or words ending in palindromes",
        "purple_title": "WORDS ENDING IN PALINDROMES",
        "decoy_subtitle": "the 4-color <strong>TEA</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREEN, AFTERNOON, BUBBLE, and HERBAL</em> tempt an immediate 'Types of Tea' grouping. "
            "However, recognizing that each belongs to a different tier (Golf, Palindromes, Inflatables, Medicine) "
            "dissolves the decoy and keeps all four groups clean."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on words ending in palindromes: "
            "<em>AFTERNOON</em> (noon), <em>PATOOT</em> (toot), <em>RHEOSTATS</em> (stats), and <em>SHREDDER</em> (redder)."
        ),
    },
    "2026-11-11": {
        "trap_name": "rainbow TEA decoy or words ending in palindromes",
        "purple_title": "WORDS ENDING IN PALINDROMES",
        "decoy_subtitle": "the 4-color <strong>TEA</strong> rainbow decoy trap",
        "red_herring_advisory": (
            "<em>GREEN, AFTERNOON, BUBBLE, and HERBAL</em> tempt an immediate 'Types of Tea' grouping. "
            "However, recognizing that each belongs to a different tier (Golf, Palindromes, Inflatables, Medicine) "
            "dissolves the decoy and keeps all four groups clean."
        ),
        "wordplay_breakdown": (
            "The Purple group relies on words ending in palindromes: "
            "<em>AFTERNOON</em> (noon), <em>PATOOT</em> (toot), <em>RHEOSTATS</em> (stats), and <em>SHREDDER</em> (redder)."
        ),
    },
}


def load_daily_puzzle(puzzle_path: Path) -> Dict[str, Any]:
    """Load and validate daily_puzzle.json."""
    if not puzzle_path.exists():
        raise FileNotFoundError(
            f"daily_puzzle.json not found at '{puzzle_path}'. "
            "Run 'python fetch_daily_puzzle.py' first."
        )
    with open(puzzle_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "categories" not in data or len(data["categories"]) < 4:
        raise ValueError(f"Invalid puzzle format in {puzzle_path}: expected 4 categories.")
    return data


def parse_puzzle_date_info(puzzle_data: Dict[str, Any]) -> Dict[str, str]:
    """Extract day name, formatted date, and puzzle number."""
    date_str = str(puzzle_data.get("date", "2026-11-08"))
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = dt.strftime("%A")
        formatted_date = f"{dt.strftime('%b')} {dt.day}, {dt.year}"
    except ValueError:
        day_name = "Today"
        formatted_date = date_str

    puzzle_id = str(puzzle_data.get("id", ""))
    return {
        "date_str": date_str,
        "day_name": day_name,
        "formatted_date": formatted_date,
        "puzzle_id": puzzle_id,
    }


def extract_trap_metadata(puzzle_data: Dict[str, Any], custom_trap: Optional[str] = None) -> Dict[str, str]:
    """Extract or infer trap name, subtitle description, and purple category."""
    pid = str(puzzle_data.get("id", ""))
    pdate = str(puzzle_data.get("date", ""))

    curated = CURATED_PUZZLE_METADATA.get(pid) or CURATED_PUZZLE_METADATA.get(pdate)
    categories = puzzle_data.get("categories", [])
    purple_cat = next((c for c in categories if c.get("level") == 3), categories[-1] if categories else {})
    purple_title = purple_cat.get("title", "PURPLE WORDPLAY").strip().upper()
    purple_words = [str(w).upper() for w in purple_cat.get("words", [])]

    if curated and not custom_trap:
        return curated.copy()

    if custom_trap:
        trap_name = custom_trap.strip()
    else:
        # Heuristic: Check for compass / direction words
        all_words = [str(w).upper() for c in categories for w in c.get("words", [])]
        compass = [w for w in all_words if any(d in w for d in ["NORTH", "SOUTH", "EAST", "WEST"])]
        if len(compass) >= 3:
            trap_name = f"cardinal directions decoy or {purple_title.lower()}"
        else:
            cat0 = categories[0].get("title", "decoy").strip().lower() if categories else "decoy"
            trap_name = f"{cat0} decoy or {purple_title.lower()}"

    decoy_subtitle = f"the {trap_name}"
    red_herring_advisory = (
        "Watch out for candidate crossover between groups before committing guesses. "
        "Isolating straightforward tiers immediately neutralizes decoy traps."
    )
    wordplay_breakdown = (
        f"The Purple group relies on {purple_title.lower()}: "
        + ", ".join(f"<em>{w}</em>" for w in purple_words) + "."
    )

    return {
        "trap_name": trap_name,
        "purple_title": purple_title,
        "decoy_subtitle": decoy_subtitle,
        "red_herring_advisory": red_herring_advisory,
        "wordplay_breakdown": wordplay_breakdown,
    }


def extract_video_id(raw_id_or_url: str) -> str:
    """Extract clean 11-character video ID from a URL or raw ID string."""
    if not raw_id_or_url:
        return ""
    val = raw_id_or_url.strip()
    m = re.search(r"(?:shorts/|v=|youtu\.be/)([a-zA-Z0-9_-]{11})", val)
    if m:
        return m.group(1)
    m = re.search(r"([a-zA-Z0-9_-]{11})", val)
    if m:
        return m.group(1)
    return val


def get_cached_short_id(root_dir: Path, fallback: str = "TF_eBP_eN20") -> str:
    """Retrieve saved short ID from file, existing HTML, or fallback."""
    id_file = root_dir / "output_shorts" / "latest_short_id.txt"
    if id_file.exists():
        stored = extract_video_id(id_file.read_text(encoding="utf-8").strip())
        if stored:
            return stored

    # Check existing breakdowns.html
    breakdowns_file = root_dir / "public" / "breakdowns.html"
    if breakdowns_file.exists():
        content = breakdowns_file.read_text(encoding="utf-8")
        m = re.search(r'youtube-nocookie\.com/embed/([a-zA-Z0-9_-]+)', content)
        if m:
            return extract_video_id(m.group(1))

    return fallback


def save_cached_short_id(root_dir: Path, short_id: str) -> None:
    """Save active Short ID for subsequent workflow steps."""
    clean_id = extract_video_id(short_id)
    out_dir = root_dir / "output_shorts"
    out_dir.mkdir(parents=True, exist_ok=True)
    id_file = out_dir / "latest_short_id.txt"
    id_file.write_text(clean_id, encoding="utf-8")


def get_cached_masterclass_id(root_dir: Path, fallback: str = "G50D-qZDsC4") -> str:
    """Retrieve saved Masterclass ID from file or fallback."""
    id_file = root_dir / "output_masterclass" / "latest_masterclass_id.txt"
    if id_file.exists():
        stored = extract_video_id(id_file.read_text(encoding="utf-8").strip())
        if stored:
            return stored
    return fallback


def save_cached_masterclass_id(root_dir: Path, masterclass_id: str) -> None:
    """Save active Masterclass ID for subsequent workflow steps."""
    clean_id = extract_video_id(masterclass_id)
    out_dir = root_dir / "output_masterclass"
    out_dir.mkdir(parents=True, exist_ok=True)
    id_file = out_dir / "latest_masterclass_id.txt"
    id_file.write_text(clean_id, encoding="utf-8")


def generate_chapters_html(categories: List[Dict[str, Any]], trap_meta: Dict[str, str]) -> Tuple[str, str]:
    """Generate dynamic video chapter items for both Short and Masterclass modes."""
    cats_by_level = {c.get("level", i): c.get("title", f"Tier {i+1}").strip().title() for i, c in enumerate(categories)}
    y_title = cats_by_level.get(0, "Direct Synonyms")
    g_title = cats_by_level.get(1, "Media Attention")
    b_title = cats_by_level.get(2, "Things That Are Towed")
    p_title = cats_by_level.get(3, "Lateral Wordplay")

    clean_decoy = re.sub(r'<[^>]+>', '', trap_meta.get("decoy_subtitle", "Decoy Trap")).strip()
    if clean_decoy.lower().startswith("the "):
        clean_decoy = clean_decoy[4:]
    clean_decoy = clean_decoy.title()

    short_chapters = f'''<div class="chapters-list" id="chapters-list-short">
                                    <div class="chapter-item" onclick="seekVideo(0)">
                                        <span class="chapter-time">0:00</span>
                                        <span class="chapter-desc">{clean_decoy} Alert</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(18)">
                                        <span class="chapter-time">0:18</span>
                                        <span class="chapter-desc">Lateral Wordplay &amp; {p_title} Clue</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(35)">
                                        <span class="chapter-time">0:35</span>
                                        <span class="chapter-desc">Safe Solve Strategy &bull; Streak Protected!</span>
                                    </div>
                                </div>'''

    masterclass_chapters = f'''<div class="chapters-list" id="chapters-list-masterclass" style="display: none;">
                                    <div class="chapter-item" onclick="seekVideo(0)">
                                        <span class="chapter-time">0:00</span>
                                        <span class="chapter-desc">Introduction &amp; Decoy Trap Alert</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(35)">
                                        <span class="chapter-time">0:35</span>
                                        <span class="chapter-desc">🟨 {y_title}</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(133)">
                                        <span class="chapter-time">2:13</span>
                                        <span class="chapter-desc">🟩 {g_title}</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(225)">
                                        <span class="chapter-time">3:45</span>
                                        <span class="chapter-desc">🟦 {b_title}</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(316)">
                                        <span class="chapter-time">5:16</span>
                                        <span class="chapter-desc">🟪 {p_title} Wordplay</span>
                                    </div>
                                    <div class="chapter-item" onclick="seekVideo(399)">
                                        <span class="chapter-time">6:39</span>
                                        <span class="chapter-desc">Complete Solved Grid Recap</span>
                                    </div>
                                </div>'''
    return short_chapters, masterclass_chapters


def sync_announcement_banners(
    root_dir: Path,
    trap_name: str,
    day_name: str,
    dry_run: bool = False,
) -> Dict[Path, bool]:
    """
    Update announcement banner copy across public HTML pages.
    Format: Stuck on today's {trap_name}? Watch {day_name}'s breakdown →
    Anchor: breakdowns.html#today
    """
    banner_text = f"Stuck on today's {trap_name}? Watch {day_name}'s breakdown &rarr;"
    results: Dict[Path, bool] = {}

    ribbon_pattern = re.compile(
        r'(<aside\s+class="breakdown-teaser-ribbon"[^>]*>.*?'
        r'<span\s+style="[^"]*font-weight:\s*700[^"]*">\s*)'
        r'.*?'
        r'(\s*</span>\s*</div>\s*<a\s+href=")[^"]*(".*?</aside>)',
        re.DOTALL,
    )

    for rel_path in BANNER_PAGES:
        file_path = root_dir / rel_path
        if not file_path.exists():
            print(f"    [!] Warning: File {rel_path} does not exist.")
            results[file_path] = False
            continue

        original_content = file_path.read_text(encoding="utf-8")
        if not ribbon_pattern.search(original_content):
            print(f"    [!] Warning: .breakdown-teaser-ribbon not found in {rel_path}.")
            results[file_path] = False
            continue

        updated_content = ribbon_pattern.sub(
            rf'\g<1>{banner_text}\g<2>breakdowns.html#today\g<3>',
            original_content,
        )

        has_changed = (updated_content != original_content)
        results[file_path] = has_changed

        if has_changed:
            if not dry_run:
                file_path.write_text(updated_content, encoding="utf-8")
                print(f"    [✓] Updated banner in {rel_path}")
            else:
                print(f"    [~] [DRY-RUN] Would update banner in {rel_path}")
        else:
            print(f"    [-] Banner already up-to-date in {rel_path}")

    return results


def generate_solved_stack_html(categories: List[Dict[str, Any]]) -> str:
    """Generate 4 color tier rows with category labels directly over rows of 4 tiles."""
    tier_meta = {
        0: ("yellow", "pill-yellow", "tile-yellow", "🟨 YELLOW TIER", "Direct Match"),
        1: ("green",  "pill-green",  "tile-green",  "🟩 GREEN TIER",  "Theme &amp; Context"),
        2: ("blue",   "pill-blue",   "tile-blue",   "🟦 BLUE TIER",   "Compounds &amp; Trivia"),
        3: ("purple", "pill-purple", "tile-purple", "🟪 PURPLE TIER", "Lateral Wordplay"),
    }
    sorted_cats = sorted(categories, key=lambda c: c.get("level", 0))
    stack_rows: List[str] = []
    for cat in sorted_cats:
        lvl = cat.get("level", 0)
        tier_color, pill_cls, tile_cls, badge_label, hint_label = tier_meta.get(
            lvl, ("yellow", "pill-yellow", "tile-yellow", "🟨 YELLOW TIER", "Direct Match")
        )
        title = cat.get("title", "").strip().upper()
        words = cat.get("words", [])
        tiles_html = "\n".join(
            f'                                <div class="solved-tile {tile_cls}">{w.strip().upper()}</div>'
            for w in words
        )
        stack_rows.append(f"""                            <div class="solved-tier-row tier-{tier_color}">
                                <div class="solved-tier-header">
                                    <div class="tier-header-left">
                                        <span class="tier-pill {pill_cls}">{badge_label}</span>
                                        <span class="tier-title">{title}</span>
                                    </div>
                                    <span class="tier-hint-sub">{hint_label}</span>
                                </div>
                                <div class="solved-row-tiles">
{tiles_html}
                                </div>
                            </div>""")
    return '<!-- Solved Board in 4-Word Rows with Labels Over Them -->\n                        <div class="solved-tiers-stack" id="solved-tiers-stack">\n' + "\n".join(stack_rows) + '\n                        </div>'


def generate_board_tiles_html(categories: List[Dict[str, Any]]) -> str:
    """Generate 16 colored word tiles sorted by tier level."""
    tier_classes = {0: "tile-yellow", 1: "tile-green", 2: "tile-blue", 3: "tile-purple"}
    sorted_cats = sorted(categories, key=lambda c: c.get("level", 0))
    tiles: List[str] = []
    for cat in sorted_cats:
        level = cat.get("level", 0)
        cls = tier_classes.get(level, "tile-yellow")
        for word in cat.get("words", []):
            tiles.append(f'                            <div class="breakdown-tile {cls}">{word.upper()}</div>')
    return "\n".join(tiles)


def generate_legend_chips_html(categories: List[Dict[str, Any]]) -> str:
    """Generate 4 tier legend chips sorted by tier level."""
    sorted_cats = sorted(categories, key=lambda c: c.get("level", 0))
    emojis = {0: "🟨", 1: "🟩", 2: "🟦", 3: "🟪"}
    chip_classes = {0: "chip-yellow", 1: "chip-green", 2: "chip-blue", 3: "chip-purple"}
    chips: List[str] = []
    for cat in sorted_cats:
        lvl = cat.get("level", 0)
        emoji = emojis.get(lvl, "🟨")
        cls = chip_classes.get(lvl, "chip-yellow")
        title = cat.get("title", "").strip().title()
        chips.append(f'                            <span class="legend-chip {cls}">{emoji} {title}</span>')
    return "\n".join(chips)


def sync_breakdowns_page(
    root_dir: Path,
    puzzle_data: Dict[str, Any],
    short_id: Optional[str] = None,
    masterclass_id: Optional[str] = None,
    custom_subtitle: Optional[str] = None,
    dry_run: bool = False,
) -> Tuple[Path, bool]:
    """
    Programmatically update the #today spotlight container in public/breakdowns.html:
    1. Header: {day_name}, {formatted_date} • Puzzle #{puzzle_number}
    2. Subtitle: Describing revealed Purple wordplay and overlapping decoy trap
    3. YouTube iframe embed target set to latest Short ID
    4. 16 Board Tiles and Legend Chips
    """
    breakdowns_file = root_dir / "public" / "breakdowns.html"
    if not breakdowns_file.exists():
        raise FileNotFoundError(f"breakdowns.html not found at '{breakdowns_file}'")

    date_info = parse_puzzle_date_info(puzzle_data)
    trap_meta = extract_trap_metadata(puzzle_data)

    if not short_id:
        short_id = get_cached_short_id(root_dir)
    else:
        short_id = extract_video_id(short_id)
        if not dry_run:
            save_cached_short_id(root_dir, short_id)

    if not masterclass_id:
        masterclass_id = get_cached_masterclass_id(root_dir)
    else:
        masterclass_id = extract_video_id(masterclass_id)
        if not dry_run:
            save_cached_masterclass_id(root_dir, masterclass_id)

    date_str = date_info["date_str"]
    day_name = date_info["day_name"]
    formatted_date = date_info["formatted_date"]
    puzzle_id = date_info["puzzle_id"]

    badge_text = f"TODAY'S BREAKDOWN ({date_str})"
    header_text = f"{day_name}, {formatted_date} &bull; Puzzle #{puzzle_id}"

    purple_title = trap_meta["purple_title"]
    decoy_subtitle = trap_meta["decoy_subtitle"]
    if custom_subtitle:
        subtitle_html = f'<p style="font-size: 14px; color: var(--ink-muted); margin: 0;">{custom_subtitle}</p>'
    else:
        # Avoid duplicate "the"
        prefix = "" if decoy_subtitle.lower().startswith("the ") else "the "
        subtitle_html = (
            f'<p style="font-size: 14px; color: var(--ink-muted); margin: 0;">'
            f'Step-by-step breakdown of the <strong>{purple_title}</strong> wordplay &amp; {prefix}{decoy_subtitle}.</p>'
        )

    iframe_title = f"NYT Connections Hints Today - {day_name} {formatted_date}"
    iframe_html = (
        f'<div class="short-container">\n'
        f'                            <iframe src="https://www.youtube-nocookie.com/embed/{short_id}?rel=0" '
        f'title="{iframe_title}" '
        f'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n'
        f'                        </div>'
    )

    original_html = breakdowns_file.read_text(encoding="utf-8")

    section_pattern = re.compile(r'(<section class="daily-spotlight" id="today">)(.*?)(</section>)', re.DOTALL)
    m = section_pattern.search(original_html)
    if not m:
        raise ValueError("Could not find <section class='daily-spotlight' id='today'> in breakdowns.html")

    pre, body, post = m.group(1), m.group(2), m.group(3)

    # 1. Update Badge
    body = re.sub(r'<span class="badge-today">.*?</span>', f'<span class="badge-today">{badge_text}</span>', body)

    # 2. Update Header
    body = re.sub(
        r'<h2 style="margin: 8px 0 4px 0; font-size: 22px;">.*?</h2>',
        f'<h2 style="margin: 8px 0 4px 0; font-size: 22px;">{header_text}</h2>',
        body,
    )

    # 3. Update Subtitle
    body = re.sub(
        r'<p style="font-size: 14px; color: var\(--ink-muted\); margin: 0;">.*?</p>',
        subtitle_html,
        body,
        flags=re.DOTALL,
    )

    # 4. Update Video Bento / Iframe
    if 'id="video-bento"' in body:
        # Update facade thumbnail
        body = re.sub(
            r'(id="facade-thumb"\s+src=")https://i\.ytimg\.com/vi/[a-zA-Z0-9_-]+/hqdefault\.jpg(")',
            rf'\g<1>https://i.ytimg.com/vi/{short_id}/hqdefault.jpg\g<2>',
            body,
        )
        # Update chapters dynamically
        short_chapters, masterclass_chapters = generate_chapters_html(
            puzzle_data.get("categories", []),
            trap_meta,
        )
        chapters_box_html = (
            f'<div class="video-chapters-box" id="video-chapters-box">\n'
            f'                                <div class="chapters-header">\n'
            f'                                    <span class="chapters-title">⏱️ VIDEO TIMESTAMPS</span>\n'
            f'                                    <span class="chapters-safe-pill">Spoiler-Free Cues</span>\n'
            f'                                </div>\n'
            f'                                {short_chapters}\n'
            f'                                {masterclass_chapters}\n'
            f'                            </div>'
        )
        body = re.sub(
            r'<div class="video-chapters-box" id="video-chapters-box">.*?(?=\s*<!-- Friendly Coach Tip Bar -->)',
            chapters_box_html,
            body,
            flags=re.DOTALL,
        )
    elif '<div class="short-container">' in body:
        body = re.sub(
            r'<div class="short-container">\s*<iframe .*?</iframe>\s*</div>',
            iframe_html,
            body,
            flags=re.DOTALL,
        )

    # 5. Update Advisory Box
    advisory_html = (
        f'<div class="trap-advisory-box">\n'
        f'                            <strong>⚠️ Red Herring Advisory:</strong> {trap_meta["red_herring_advisory"]}\n'
        f'                        </div>'
    )
    body = re.sub(
        r'<div class="trap-advisory-box">.*?</div>',
        advisory_html,
        body,
        flags=re.DOTALL,
    )

    # 6. Update Solved Board (Rows of 4 with labels over them)
    solved_stack_html = generate_solved_stack_html(puzzle_data.get("categories", []))
    if 'id="solved-tiers-stack"' in body or 'class="solved-tiers-stack"' in body:
        body = re.sub(
            r'(?:<!-- Solved Board in 4-Word Rows with Labels Over Them -->\s*)?<div class="solved-tiers-stack"[^>]*>.*?(?=\s*<p style="font-size: 13px; color: var\(--ink-muted\); margin: 12px 0 0 0;)',
            f"{solved_stack_html}\n\n                        ",
            body,
            flags=re.DOTALL,
        )
    else:
        # Fallback / Upgrade from legacy breakdown-grid & tier-legend-row
        body = re.sub(
            r'<div class="breakdown-grid"[^>]*>.*?(?:<div class="tier-legend-row">.*?</div>\s*)?(?=\s*<p style="font-size: 13px; color: var\(--ink-muted\); margin: 12px 0 0 0;)',
            f'{solved_stack_html}\n\n                        ',
            body,
            flags=re.DOTALL,
        )

    # 8. Update Wordplay Breakdown
    wordplay_html = (
        f'<p style="font-size: 13px; color: var(--ink-muted); margin: 12px 0 0 0; line-height: 1.5;">\n'
        f'                            <strong>Lateral Wordplay Breakdown:</strong> {trap_meta["wordplay_breakdown"]}\n'
        f'                        </p>'
    )
    body = re.sub(
        r'<p style="font-size: 13px; color: var\(--ink-muted\); margin: 12px 0 0 0; line-height: 1.5;">\s*<strong>Lateral Wordplay Breakdown:</strong>.*?</p>',
        wordplay_html,
        body,
        flags=re.DOTALL,
    )

    # 9. Update Word Guide (Lexical Encyclopedia Accordion)
    try:
        from lexical_sync import update_lexical_accordion_in_html
        body = update_lexical_accordion_in_html(body, puzzle_data, root_dir)
        print("    [✓] Synced 16-word lexical encyclopedia accordion.")
    except Exception as e:
        print(f"    [!] Warning: Failed to sync lexical accordion: {e}")

    updated_html = original_html[:m.start()] + pre + body + post + original_html[m.end():]
    
    # Also update short and masterclass in script VIDEO_CONFIG if present
    updated_html = re.sub(
        r'(short:\s*{\s*id:\s*")[a-zA-Z0-9_-]+(")',
        rf'\g<1>{short_id}\g<2>',
        updated_html,
    )
    updated_html = re.sub(
        r'(short:\s*{\s*id:\s*"[^"]*",\s*title:\s*")[^"]*(")',
        rf'\g<1>NYT Connections Hints Today - {day_name} {formatted_date}\g<2>',
        updated_html,
    )
    if masterclass_id:
        updated_html = re.sub(
            r'(masterclass:\s*{\s*id:\s*")[a-zA-Z0-9_-]+(")',
            rf'\g<1>{masterclass_id}\g<2>',
            updated_html,
        )
        updated_html = re.sub(
            r'(masterclass:\s*{\s*id:\s*"[^"]*",\s*title:\s*")[^"]*(")',
            rf'\g<1>Todays NYT Connections Explained ({formatted_date}) | Full Solution & Word Meanings (#{puzzle_id})\g<2>',
            updated_html,
        )
    
    has_changed = (updated_html != original_html)

    if has_changed:
        if not dry_run:
            breakdowns_file.write_text(updated_html, encoding="utf-8")
            print(f"    [✓] Updated #today spotlight in {breakdowns_file.name}")
        else:
            print(f"    [~] [DRY-RUN] Would update #today spotlight in {breakdowns_file.name}")
    else:
        print(f"    [-] #today spotlight already up-to-date in {breakdowns_file.name}")

    return breakdowns_file, has_changed


def sync_index_daily_words(
    root_dir: Path,
    puzzle_data: Dict[str, Any],
    dry_run: bool = False,
) -> Tuple[Path, bool]:
    """
    Synchronize public/daily_puzzle.json and public/index.html with today's 16 words:
    1. Writes public/daily_puzzle.json with formatted JSON.
    2. Updates public/index.html:
       - Header: {day_name}, {formatted_date} • Puzzle #{puzzle_id}
       - 16 scrambled starting board word chips
       - Embedded JavaScript `currentTodayPuzzle` object
    """
    date_info = parse_puzzle_date_info(puzzle_data)
    day_name = date_info["day_name"]
    formatted_date = date_info["formatted_date"]
    puzzle_id = date_info["puzzle_id"]
    date_str = date_info["date_str"]

    starting_board = puzzle_data.get("starting_board", [])
    if not starting_board or len(starting_board) != 16:
        starting_board = [w.upper() for c in puzzle_data.get("categories", []) for w in c.get("words", [])]

    # 1. Update public/daily_puzzle.json
    pub_json_file = root_dir / "public" / "daily_puzzle.json"
    if not dry_run:
        pub_json_file.write_text(json.dumps(puzzle_data, indent=2), encoding="utf-8")
        print(f"    [✓] Synced {pub_json_file.name} for {date_str} (Puzzle #{puzzle_id})")
    else:
        print(f"    [~] [DRY-RUN] Would sync {pub_json_file.name} for {date_str}")

    # 2. Update public/index.html
    index_file = root_dir / "public" / "index.html"
    if not index_file.exists():
        return index_file, False

    orig_html = index_file.read_text(encoding="utf-8")
    updated_html = orig_html

    # Header text
    header_text = f"{day_name}, {formatted_date} &bull; Puzzle #{puzzle_id}"
    updated_html = re.sub(
        r'<h2 class="today-title-text" id="todayTitleText">.*?</h2>',
        f'<h2 class="today-title-text" id="todayTitleText">{header_text}</h2>',
        updated_html
    )

    # 16 word chips
    chips_html = "\n".join(f'                    <div class="today-word-chip">{w.upper()}</div>' for w in starting_board)
    chips_container = f'<div class="today-chips-container" id="todayChipsContainer">\n{chips_html}\n                </div>'
    updated_html = re.sub(
        r'<div class="today-chips-container" id="todayChipsContainer">.*?</div>\s*(?=\s*<!-- Deck Actions -->)',
        chips_container + '\n',
        updated_html,
        flags=re.DOTALL
    )

    # Embedded currentTodayPuzzle JS
    js_puzzle_str = json.dumps(puzzle_data, indent=4)
    js_replacement = f'let currentTodayPuzzle = {js_puzzle_str};'
    updated_html = re.sub(
        r'let currentTodayPuzzle\s*=\s*\{.*?\};\s*(?=\s*// Render Word Chips Dynamically)',
        js_replacement + '\n\n        ',
        updated_html,
        flags=re.DOTALL
    )

    has_changed = (updated_html != orig_html)
    if has_changed:
        if not dry_run:
            index_file.write_text(updated_html, encoding="utf-8")
            print(f"    [✓] Synced today's 16 words in {index_file.name}")
        else:
            print(f"    [~] [DRY-RUN] Would update today's words in {index_file.name}")
    else:
        print(f"    [-] Today's words in {index_file.name} already up-to-date")

    return index_file, has_changed


def archive_previous_breakdown(root_dir: Path, current_date: str, dry_run: bool = False) -> Optional[Path]:
    """
    If breakdowns.html currently contains a spotlight for a previous day,
    snapshot that day's breakdown into public/breakdowns/YYYY-MM-DD.html
    and ensure it is linked in the archive list and sitemap.xml.
    """
    breakdowns_file = root_dir / "public" / "breakdowns.html"
    if not breakdowns_file.exists():
        return None

    content = breakdowns_file.read_text(encoding="utf-8")
    m = re.search(r'<span class="badge-today">TODAY\'S BREAKDOWN \((.*?)\)</span>', content)
    if not m:
        return None

    prev_date = m.group(1).strip()
    if prev_date == current_date:
        return None  # Already today

    archive_dir = root_dir / "public" / "breakdowns"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{prev_date}.html"

    if archive_file.exists():
        print(f"    [-] Archive {archive_file.name} already exists.")
        return archive_file

    print(f"    [+] Archiving previous breakdown ({prev_date}) -> {archive_file.name}...")

    section_m = re.search(r'(<section class="daily-spotlight" id="today">.*?</section>)', content, re.DOTALL)
    if not section_m:
        return None

    spotlight_html = section_m.group(1)
    spotlight_html = re.sub(
        r'<span class="badge-today">TODAY\'S BREAKDOWN \(.*?\)</span>',
        f'<span class="badge-archive">PAST PUZZLE • {prev_date}</span>',
        spotlight_html
    )
    spotlight_html = re.sub(r'<span class="live-pill">.*?</span>', '', spotlight_html)
    spotlight_html = spotlight_html.replace('id="today"', '')

    standalone_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9227690723872378" crossorigin="anonymous"></script>
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-ERDGNDJ01Q"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-ERDGNDJ01Q');
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Complete puzzle hints, board walkthrough, and 16-word guide for NYT Connections ({prev_date}).">
    <link rel="canonical" href="https://connectionsassistant.com/breakdowns/{prev_date}.html">
    <title>NYT Connections Hints & Breakdown — {prev_date} | Connections Assistant</title>
    <link rel="stylesheet" href="../style.css">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=JetBrains+Mono:wght@500;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container" style="max-width: 960px; margin: 0 auto; padding: 24px 16px;">
        <header style="margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <h1 style="font-family: 'Fraunces', serif; font-size: 24px; margin: 0;">
                    <a href="../index.html" style="text-decoration: none; color: inherit;">Connections Grouping Assistant</a>
                </h1>
                <nav style="display: flex; gap: 8px;">
                    <a href="../breakdowns.html" class="btn-tactile btn-primary" style="font-size: 12px; padding: 6px 12px; text-decoration: none;">Today's Board &rarr;</a>
                </nav>
            </div>
        </header>
        <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <a href="../breakdowns.html" style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; text-decoration: none; color: var(--ink);">&larr; Back to Today's Live Breakdown</a>
            <span style="font-size: 12px; color: var(--ink-muted);">Past Puzzle Breakdown</span>
        </div>
        <main>
            {spotlight_html}
        </main>
    </div>
</body>
</html>"""

    if not dry_run:
        archive_file.write_text(standalone_html, encoding="utf-8")
        print(f"    [✓] Created evergreen archive: {archive_file.name}")

        sitemap_file = root_dir / "public" / "sitemap.xml"
        if sitemap_file.exists():
            sm = sitemap_file.read_text(encoding="utf-8")
            target_url = f"https://connectionsassistant.com/breakdowns/{prev_date}.html"
            if target_url not in sm:
                entry = f"""  <url>
    <loc>{target_url}</loc>
    <lastmod>{prev_date}</lastmod>
    <changefreq>never</changefreq>
    <priority>0.80</priority>
  </url>
</urlset>"""
                sm = sm.replace("</urlset>", entry)
                sitemap_file.write_text(sm, encoding="utf-8")
                print(f"    [✓] Added {target_url} to sitemap.xml")

    return archive_file


def deploy_hosting(root_dir: Path) -> bool:
    """Deploy public/ directory to Firebase Hosting."""
    print("[+] Initiating Firebase Hosting deployment (`firebase deploy --only hosting`)...")
    cmd = "firebase deploy --only hosting"
    result = subprocess.run(cmd, cwd=root_dir, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print("[✓] Firebase Hosting deployment successful!")
        for line in result.stdout.splitlines():
            if "Hosting URL" in line or "Deploy complete" in line:
                print(f"    {line.strip()}")
        return True
    else:
        print(f"[!] Firebase Hosting deployment failed with code {result.returncode}:", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return False


def sync_web_pipeline(
    root_dir: Optional[Path] = None,
    puzzle_path: Optional[Path] = None,
    short_id: Optional[str] = None,
    masterclass_id: Optional[str] = None,
    trap_name: Optional[str] = None,
    deploy: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Main programmatic pipeline coordinating banner synchronization,
    breakdowns.html staging, and optional hosting deployment.
    """
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent

    if puzzle_path is None:
        puzzle_path = root_dir / "daily_puzzle.json"

    print(f"[+] Loading puzzle data from {puzzle_path.name}...")
    puzzle_data = load_daily_puzzle(puzzle_path)
    date_info = parse_puzzle_date_info(puzzle_data)
    trap_meta = extract_trap_metadata(puzzle_data, custom_trap=trap_name)

    effective_trap_name = trap_meta["trap_name"]
    day_name = date_info["day_name"]
    formatted_date = date_info["formatted_date"]
    puzzle_id = date_info["puzzle_id"]

    if not short_id:
        short_id = get_cached_short_id(root_dir)
    else:
        short_id = extract_video_id(short_id)

    if not masterclass_id:
        masterclass_id = get_cached_masterclass_id(root_dir)
    else:
        masterclass_id = extract_video_id(masterclass_id)

    print(f"    - Date: {date_info['date_str']} ({day_name}, {formatted_date})")
    print(f"    - Puzzle #{puzzle_id}")
    print(f"    - Decoy Trap Name: '{effective_trap_name}'")
    print(f"    - Purple Category: '{trap_meta['purple_title']}'")
    print(f"    - YouTube Short ID: '{short_id}'")
    print(f"    - YouTube Masterclass ID: '{masterclass_id}'")

    print("\n[+] Step 1: Synchronizing multi-page announcement banners...")
    banner_results = sync_announcement_banners(
        root_dir=root_dir,
        trap_name=effective_trap_name,
        day_name=day_name,
        dry_run=dry_run,
    )

    print("\n[+] Step 2a: Archiving previous day's breakdown if rolling over...")
    archive_file = archive_previous_breakdown(
        root_dir=root_dir,
        current_date=date_info["date_str"],
        dry_run=dry_run,
    )

    print("\n[+] Step 2b: Staging public/breakdowns.html (#today container)...")
    breakdowns_file, breakdowns_changed = sync_breakdowns_page(
        root_dir=root_dir,
        puzzle_data=puzzle_data,
        short_id=short_id,
        masterclass_id=masterclass_id,
        dry_run=dry_run,
    )

    print("\n[+] Step 2c: Updating 30-day historical archives, navigation links, and sitemap...")
    try:
        cache_dir = root_dir / "puzzle_history_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        today_cache = cache_dir / f"{date_info['date_str']}.json"
        if not today_cache.exists():
            today_cache.write_text(json.dumps(puzzle_data, indent=2), encoding="utf-8")
            print(f"    [✓] Cached today's puzzle #{puzzle_id} ({date_info['date_str']}) in puzzle_history_cache/")
        import subprocess
        subprocess.run([sys.executable, str(root_dir / "run_generate_all_archives.py")], check=True)
        print("    [✓] 30-day archive & history updated successfully.")
    except Exception as e:
        print(f"    [!] Warning: Failed to refresh archive directory ({e})")

    print("\n[+] Step 2d: Synchronizing today's 16 words on index.html and public/daily_puzzle.json...")
    index_file, index_changed = sync_index_daily_words(
        root_dir=root_dir,
        puzzle_data=puzzle_data,
        dry_run=dry_run,
    )

    deploy_success = False
    if deploy:
        if dry_run:
            print("\n[~] [DRY-RUN] Deployment skipped due to --dry-run.")
        else:
            print("\n[+] Step 3: Deploying hosting to production...")
            deploy_success = deploy_hosting(root_dir)

    return {
        "puzzle_id": puzzle_id,
        "date_info": date_info,
        "trap_meta": trap_meta,
        "short_id": short_id,
        "masterclass_id": masterclass_id,
        "banner_results": banner_results,
        "breakdowns_changed": breakdowns_changed,
        "index_changed": index_changed,
        "deployed": deploy_success,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Automated multi-page banner sync and breakdowns.html staging pipeline."
    )
    parser.add_argument(
        "--puzzle",
        default=None,
        help="Path to daily_puzzle.json (defaults to project root)",
    )
    parser.add_argument(
        "--short-id",
        default=None,
        help="YouTube Short ID to embed in breakdowns.html (e.g. TF_eBP_eN20)",
    )
    parser.add_argument(
        "--masterclass-id",
        default=None,
        help="YouTube Masterclass Video ID to embed in breakdowns.html (e.g. G50D-qZDsC4)",
    )
    parser.add_argument(
        "--trap-name",
        default=None,
        help="Custom primary decoy trap name for announcement banners",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files or deploying",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy public/ to Firebase Hosting after updating files",
    )

    args = parser.parse_args()
    root_dir = Path(__file__).resolve().parent
    puzzle_path = Path(args.puzzle).resolve() if args.puzzle else None

    try:
        sync_web_pipeline(
            root_dir=root_dir,
            puzzle_path=puzzle_path,
            short_id=args.short_id,
            masterclass_id=args.masterclass_id,
            trap_name=args.trap_name,
            deploy=args.deploy,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
