import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant")
PUBLIC_DIR = BASE_DIR / "public"
ARCHIVE_DIR = PUBLIC_DIR / "breakdowns"
CACHE_DIR = BASE_DIR / "puzzle_history_cache"

# Curated metadata dictionary for rich decoy & wordplay notes
METADATA = {
    "2026-11-13": {
        "decoy": "the 3-tier <strong>WATER &amp; OCEAN</strong> decoy trap",
        "red_herring": "<em>SURF, WAVES, WATER SKIER, and BARGE</em> tempt an immediate water/ocean grouping! However, every single one belongs to a completely different tier: <em>SURF</em> is an Internet action (Yellow), <em>WAVES</em> is a Brain compound (Purple), and <em>BARGE and WATER SKIER</em> are things that are towed (Blue). Do not burn a guess grouping them together!",
        "purple_note": "The Purple group relies on compound phrases and idioms starting with 'BRAIN': <em>BRAIN FREEZE</em>, <em>BRAIN TEASER</em>, <em>BRAIN TRUST</em>, and <em>BRAIN WAVES</em>."
    },
    "2026-11-12": {
        "decoy": "the 4-color <strong>BACK TO THE FUTURE</strong> rainbow decoy trap",
        "red_herring": "<em>GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY</em> immediately suggest a 4-word sci-fi movie theme! However, every single one belongs to a completely different tier: <em>GREAT SCOTT</em> is an exclamation (Yellow), <em>FLUX CAPACITOR</em> starts with a variation (Green), <em>DOC BROWN</em> ends in a cooking method (Blue), and <em>MARTY MCFLY</em> starts with an Oscar winner (Purple). Do not burn a guess grouping them together!",
        "purple_note": "The Purple group connects phrases whose opening words won the Academy Award for Best Picture: <em>GLADIATOR</em> SANDALS (Gladiator, 2000), <em>MARTY</em> MCFLY (Marty, 1955), <em>MOONLIGHT</em> SONATA (Moonlight, 2016), and <em>ROCKY</em> ROAD (Rocky, 1976)."
    },
    "2026-11-11": {
        "decoy": "the 4-color <strong>TEA</strong> rainbow decoy trap",
        "red_herring": "<em>GREEN, AFTERNOON, BUBBLE, and HERBAL</em> tempt an immediate 'Types of Tea' grouping. However, recognizing that each belongs to a different tier (Golf, Palindromes, Inflatables, Medicine) dissolves the decoy and keeps all four groups clean and stress-free!",
        "purple_note": "The Purple group relies on words ending in palindromes: <em>AFTERNOON</em> (noon), <em>PATOOT</em> (toot), <em>RHEOSTATS</em> (stats), and <em>SHREDDER</em> (redder)."
    },
    "2026-11-10": {
        "decoy": "the 5-word <strong>BEEKEEPER</strong> trade trap",
        "red_herring": "<em>BEEKEEPER</em> appears alongside <em>APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT</em>, tempting an immediate old-timey occupation grouping. However, recognizing that <em>BEEKEEPER</em> contains exactly five E's unlocks the Purple vowel tier and leaves the four true historic trades intact!",
        "purple_note": "The Purple group relies on words containing exactly five of a single vowel: <em>ABRACADABRA</em> (5 A's), <em>BEEKEEPER</em> (5 E's), <em>INVISIBILITY</em> (5 I's), and <em>PROTOZOOLOGY</em> (5 O's)."
    },
    "2026-11-09": {
        "decoy": "the 5-word <strong>CARD SHARK</strong> scam decoy trap",
        "red_herring": "<em>CARD SHARK</em> appears alongside <em>CON JOB, SHELL GAME, FLIMFLAM, and RIP-OFF</em>, tempting an immediate deceitful scheme grouping. However, recognizing that <em>CARD SHARK</em> ends with a marine animal (shark) unlocks the Purple tier and leaves the four true swindles intact.",
        "purple_note": "The Purple group relies on compound terms ending in sea creatures: <em>CARD SHARK</em> (shark), <em>FUN SPONGE</em> (sponge), <em>GAMMA RAY</em> (ray), and <em>NAVY SEAL</em> (seal)."
    },
    "2026-11-08": {
        "decoy": "the 5-word <strong>CUT</strong> salon decoy trap",
        "red_herring": "<em>CUT</em> connects to both <strong>HAIR SALON SERVICES</strong> (with <em>TRIM, BLOWOUT, COLOR, EXTENSIONS</em>) and <strong>MUSCULAR</strong> (with <em>BUILT, JACKED, RIPPED</em>). Isolating the physical fitness tier immediately neutralizes the decoy trap.",
        "purple_note": "The Purple group relies on vegetable homophones: <em>CARAT</em> (carrot), <em>CHARRED</em> (chard), <em>KORN</em> (corn), and <em>LEAK</em> (leek)."
    },
    "2026-11-07": {
        "decoy": "the cardinal directions decoy trap",
        "red_herring": "<em>EASTER</em> appears alongside <em>NORTH</em> and <em>SOUTH</em>, creating an alluring compass direction trap. Isolating the storm endings first keeps your guesses safe.",
        "purple_note": "The Purple group relies on storm endings: <em>CANE</em> (hurricane), <em>CLONE</em> (cyclone), <em>EASTER</em> (nor'easter), and <em>SOON</em> (monsoon)."
    },
    "2026-11-06": {
        "decoy": "the composition & copy decoy trap",
        "red_herring": "<em>COPY</em> and <em>COMPOSITION</em> overlap heavily with writing and editorial terms, creating tempting cross-category confusion with truck categories.",
        "purple_note": "The Purple group relies on phrases ending in parts of the eye: pupil, iris, cornea, and retina associations."
    },
    "2026-11-05": {
        "decoy": "the floral & cocktail overlap decoy",
        "red_herring": "Botanical terms overlap with liquor flavorings. Separating the footwear heels first keeps the liquor letter transformations intact.",
        "purple_note": "The Purple group consists of liquors with their last letters altered to form common words."
    },
    "2026-11-04": {
        "decoy": "the sharp edge & care label overlap",
        "red_herring": "Geometric and edge descriptions tempt an immediate shapes cluster. Separating the 'DO NOT' care instructions first makes solving much smoother.",
        "purple_note": "The Purple group relies on compound words starting with 'FIRE'."
    },
    "2026-11-03": {
        "decoy": "the restaurant server & wheel decoy",
        "red_herring": "Service and dining terms blend with action verbs. Isolating the menu bar headings unlocks the lateral wordplay cleanly.",
        "purple_note": "The Purple group connects terms ending in standard computer menu bar headings."
    },
    "2026-11-02": {
        "decoy": "the outdoor trek & mist maker overlap",
        "red_herring": "Camping gear overlaps with weather and steam elements. Grouping the reflective mirror items first neutralizes the confusion.",
        "purple_note": "The Purple group connects everyday objects that feature mirrors."
    }
}

# Known video short IDs for past breakdowns
VIDEO_EMBEDS = {
    "2026-11-13": "JXqKaB4AFpQ",
    "2026-11-12": "DSRF4SIJLak",
    "2026-11-11": "h6hP675xDq0",
    "2026-11-10": "TF_eBP_eN20",
}

# Load all cached puzzles sorted descending by date
all_puzzles = []
for p_path in sorted(CACHE_DIR.glob("*.json"), reverse=True):
    try:
        data = json.loads(p_path.read_text(encoding="utf-8"))
        all_puzzles.append(data)
    except Exception as e:
        print(f"Error reading {p_path}: {e}")

puzzle_by_date = {p["date"]: p for p in all_puzzles}
all_dates_desc = [p["date"] for p in all_puzzles]

def format_date_long(d_str: str) -> tuple[str, str, str]:
    dt = datetime.strptime(d_str, "%Y-%m-%d")
    return dt.strftime("%A, %b %d, %Y"), dt.strftime("%A"), dt.strftime("%b %d")

def build_history_section_html(current_page_date: str = "today") -> str:
    today_p_date = ""
    dp_file = BASE_DIR / "daily_puzzle.json"
    if dp_file.exists():
        try:
            today_p_date = json.loads(dp_file.read_text(encoding="utf-8")).get("date", "")
        except Exception:
            pass

    puzzles_for_history = all_puzzles
    if current_page_date == "today" and today_p_date:
        puzzles_for_history = [p for p in all_puzzles if p["date"] < today_p_date]

    recent_cards = []
    for idx, p in enumerate(puzzles_for_history[:5]):
        p_date = p["date"]
        p_num = p["puzzle_number"]
        long_date, day_name, short_d = format_date_long(p_date)
        meta = METADATA.get(p_date, {})
        purple_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Purple"), "TRICKY WORDPLAY")
        yellow_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Yellow"), "")
        
        link_target = f"breakdowns/{p_date}.html" if current_page_date == "today" else f"{p_date}.html"
        is_current = (p_date == current_page_date)
        
        # Friendly badge for recent items
        if idx == 0 and current_page_date == "today":
            status_pill = '<span style="font-family: \'JetBrains Mono\', monospace; font-size: 11px; font-weight: 700; background: #DCFCE7; color: #166534; padding: 2px 7px; border-radius: 4px; border: 1px solid #86EFAC;">⚡ YESTERDAY\'S PUZZLE</span>'
        elif is_current:
            status_pill = '<span style="font-family: \'JetBrains Mono\', monospace; font-size: 11px; font-weight: 700; background: #EDE9FE; color: #5B21B6; padding: 2px 7px; border-radius: 4px; border: 1px solid #7C3AED;">📍 CURRENT PAGE</span>'
        else:
            status_pill = f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 11px; font-weight: 700; background: #FEF3C7; color: #92400E; padding: 2px 7px; border-radius: 4px;">PUZZLE #{p_num}</span>'

        decoy_hint = meta.get("decoy", "Clever category overlaps &amp; lateral wordplay")

        recent_cards.append(f"""                    <div style="background: #FFFFFF; border: 1.5px solid var(--border-lip); border-radius: 10px; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; box-shadow: 2px 2px 0 var(--border-lip);">
                        <div style="flex: 1; min-width: 240px;">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 5px; flex-wrap: wrap;">
                                {status_pill}
                                <span style="font-weight: 700; font-size: 14.5px; color: var(--ink);">{long_date}</span>
                            </div>
                            <div style="font-size: 12.5px; color: var(--ink-muted); margin-bottom: 2px;">
                                <strong>Yellow:</strong> {yellow_cat} &bull; <strong>Purple:</strong> {purple_cat}
                            </div>
                            <div style="font-size: 12px; color: #78350F; font-style: italic;">
                                💡 Watch out for {decoy_hint}
                            </div>
                        </div>
                        <a href="{link_target}" class="btn-tactile btn-secondary" style="font-size: 12px; padding: 8px 14px; text-decoration: none;">
                            Review Walkthrough &rarr;
                        </a>
                    </div>""")

    archive_grid_items = []
    for p in puzzles_for_history:
        p_date = p["date"]
        p_num = p["puzzle_number"]
        dt = datetime.strptime(p_date, "%Y-%m-%d")
        short_date = dt.strftime("%b %d (%a)")
        purple_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Purple"), "")
        link_target = f"breakdowns/{p_date}.html" if current_page_date == "today" else f"{p_date}.html"
        
        is_current = (p_date == current_page_date)
        bg = "#F3E8FF" if is_current else "#FFFFFF"
        border = "2px solid #7C3AED" if is_current else "1.5px solid var(--border-lip)"
        current_indicator = ' <span style="font-size: 10px; background: #7C3AED; color: #FFF; padding: 1px 5px; border-radius: 3px; margin-left: 4px;">CURRENT</span>' if is_current else ''

        archive_grid_items.append(f"""                        <a href="{link_target}" style="display: block; text-decoration: none; background: {bg}; border: {border}; border-radius: 8px; padding: 9px 12px; color: inherit; transition: transform 0.12s ease, box-shadow 0.12s ease; box-shadow: 1.5px 1.5px 0 var(--border-lip);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                                <span style="font-weight: 700; font-size: 13px; color: var(--ink);">{short_date}{current_indicator}</span>
                                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: var(--ink-muted); font-weight: 700;">#{p_num}</span>
                            </div>
                            <div style="font-size: 11.5px; color: #6D28D9; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{purple_cat}">
                                🟪 {purple_cat}
                            </div>
                        </a>""")

    recent_html = "\n".join(recent_cards)
    grid_html = "\n".join(archive_grid_items)

    min_d_str = datetime.strptime(puzzles_for_history[-1]["date"], "%Y-%m-%d").strftime("%b %d")
    max_d_str = datetime.strptime(puzzles_for_history[0]["date"], "%Y-%m-%d").strftime("%b %d")
    count_str = f"{len(puzzles_for_history)} Puzzles"

    return f"""            <!-- PAST PUZZLE BREAKDOWNS & HISTORY SECTION -->
            <section class="breakdown-card" id="history" style="background: #FAF8F5; border: 2px solid var(--border-lip); border-radius: var(--radius-card); box-shadow: 4px 4px 0 var(--border-lip); padding: 22px; margin: 28px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; border-bottom: 2px solid var(--stone); padding-bottom: 10px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 22px;">📚</span>
                        <h3 style="margin: 0; font-size: 20px; font-family: 'Fraunces', serif;">Past Puzzle Breakdowns &amp; History Library</h3>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: #EDE9FE; color: #5B21B6; border: 1px solid #7C3AED; padding: 3px 10px; border-radius: 999px; font-weight: 700;">☕ 30-DAY SOLVER ARCHIVE</span>
                </div>

                <!-- Friendly Welcoming Banner -->
                <div style="background: #FFFBEB; border: 1.5px solid #F59E0B; border-radius: 12px; padding: 14px 18px; margin-bottom: 18px; display: flex; align-items: flex-start; gap: 14px;">
                    <span style="font-size: 26px; line-height: 1; user-select: none;">☕</span>
                    <div>
                        <div style="font-weight: 800; font-size: 14px; color: #92400E; margin-bottom: 3px;">
                            Welcome to Your Morning Puzzle Companion Library!
                        </div>
                        <p style="font-size: 13px; color: #78350F; margin: 0; line-height: 1.55;">
                            Missed a morning puzzle over the weekend, lost a streak to a sneaky decoy trap, or just love studying clever lateral wordplay? Pull up a chair! Below you'll find full step-by-step walkthroughs, solved 4x4 boards, and red herring tips for every puzzle from the past month.
                        </p>
                    </div>
                </div>

                <!-- Recent Breakdowns Showcase -->
                <div style="font-weight: 700; font-size: 13.5px; color: var(--ink); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                    <span>✨</span>
                    <span>Recent Daily Breakdowns:</span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 11px; margin-bottom: 18px;">
{recent_html}
                </div>

                <!-- Friendly Practice Coach Tip -->
                <div style="background: #F0FDF4; border: 1.5px solid #86EFAC; border-radius: 10px; padding: 12px 16px; margin: 18px 0; font-size: 12.5px; color: #166534; display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 20px; line-height: 1;">💡</span>
                    <div style="line-height: 1.5;">
                        <strong>Daily Solver's Tip:</strong> Practicing with past Purple tiers is the #1 way to train your brain to spot homophones, hidden prefixes, and Wyna Liu's lateral wordplay tricks before they catch you!
                    </div>
                </div>

                <!-- Complete 30-Day Grid Accordion -->
                <details class="archive-accordion" style="background: #FFFFFF; border: 1.5px solid var(--border-lip); border-radius: 10px; padding: 14px 16px; box-shadow: 2px 2px 0 var(--border-lip);" open>
                    <summary style="cursor: pointer; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 13px; color: var(--ink); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                        <span>📅 Complete Historical Puzzle Directory ({min_d_str} &ndash; {max_d_str})</span>
                        <span style="font-size: 11px; background: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px;">{count_str} &bull; Click to Toggle</span>
                    </summary>
                    <p style="font-size: 12.5px; color: var(--ink-muted); margin: 10px 0 12px 0;">
                        Click any date below to open its dedicated walkthrough with solved 4x4 color grids and category guides:
                    </p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 9px;">
{grid_html}
                    </div>
                </details>
            </section>"""

def build_standalone_archive_page(puzzle_data: dict, prev_p: dict | None, next_p: dict | None) -> str:
    p_date = puzzle_data["date"]
    p_num = puzzle_data["puzzle_number"]
    long_date, day_name, short_d = format_date_long(p_date)
    
    cats = puzzle_data["categories"]
    yellow = next(c for c in cats if c["tier"] == "Yellow")
    green = next(c for c in cats if c["tier"] == "Green")
    blue = next(c for c in cats if c["tier"] == "Blue")
    purple = next(c for c in cats if c["tier"] == "Purple")
    
    meta = METADATA.get(p_date, {})
    decoy_summary = meta.get("decoy", f"lateral wordplay &amp; cross-category overlaps")
    red_herring_text = meta.get(
        "red_herring",
        f"Solvers had to watch out for vocabulary that could easily fit into multiple categories. A great rule of thumb for boards like this is to identify the straightforward Yellow and Green synonyms first, which immediately isolates the subtle lateral wordplay in the Purple tier!"
    )
    purple_note_text = meta.get(
        "purple_note",
        f"The Purple tier ({purple['title']}) challenged solvers to think outside traditional definitions and spot the lateral bond linking: <em>{', '.join(purple['words'])}</em>."
    )
    
    # Solved 4x4 rows with labels over them
    tier_meta = [
        ("Yellow", "pill-yellow", "tile-yellow", "🟨 YELLOW TIER", yellow, "Direct Match"),
        ("Green",  "pill-green",  "tile-green",  "🟩 GREEN TIER",  green,  "Theme &amp; Context"),
        ("Blue",   "pill-blue",   "tile-blue",   "🟦 BLUE TIER",   blue,   "Compounds &amp; Trivia"),
        ("Purple", "pill-purple", "tile-purple", "🟪 PURPLE TIER", purple, "Lateral Wordplay"),
    ]
    stack_rows = []
    for t_name, pill_cls, tile_cls, badge_label, cat, hint_label in tier_meta:
        row_tiles = "\n".join(
            f'                                <div class="solved-tile {tile_cls}">{w.strip().upper()}</div>'
            for w in cat["words"]
        )
        stack_rows.append(f"""                        <div class="solved-tier-row tier-{t_name.lower()}">
                            <div class="solved-tier-header">
                                <div class="tier-header-left">
                                    <span class="tier-pill {pill_cls}">{badge_label}</span>
                                    <span class="tier-title">{cat['title'].strip().upper()}</span>
                                </div>
                                <span class="tier-hint-sub">{hint_label}</span>
                            </div>
                            <div class="solved-row-tiles">
{row_tiles}
                            </div>
                        </div>""")
    solved_stack_html = "\n".join(stack_rows)

    # 4 Category Walkthrough Cards with friendly explanations
    tier_info = [
        ("Yellow Tier", "yellow", yellow, "Direct &amp; Friendly Match", "These 4 words share a straightforward, direct definition or membership in this clear-cut set. Solvers usually lock this group down first to simplify the board!"),
        ("Green Tier", "green", green, "Context &amp; Theme", "These terms share a common real-world theme, environment, or everyday conversational setting."),
        ("Blue Tier", "blue", blue, "Structure &amp; Compounds", "These words share a clever structural mechanic, common phrase partner, or compound word pairing."),
        ("Purple Tier", "purple", purple, "Tricky Lateral Wordplay", "The creative lateral group! Requires thinking outside dictionary definitions to spot letter patterns, homophones, or pop-culture trivia.")
    ]
    cards_html = []
    for t_name, t_color, cat, sub_label, desc in tier_info:
        word_chips = " ".join(f'<span class="mono" style="font-weight: 700; font-size: 12.5px; background: var(--stone); border: 1px solid var(--stone-border); padding: 3px 8px; border-radius: 4px; display: inline-block; margin: 2px 2px 2px 0;">{w}</span>' for w in cat["words"])
        cards_html.append(f"""                        <div style="background: #FFFFFF; border: 1.5px solid var(--border-lip); border-left: 6px solid var(--tier-{t_color}); border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; box-shadow: 2px 2px 0 var(--border-lip);">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; flex-wrap: wrap; gap: 6px;">
                                <strong style="font-size: 15px; font-family: 'Fraunces', serif;">{t_name.upper()}: {cat['title']}</strong>
                                <span class="legend-chip chip-{t_color}" style="font-size: 11px; padding: 2px 8px; font-weight: 700;">{sub_label}</span>
                            </div>
                            <div style="margin: 8px 0;">
                                {word_chips}
                            </div>
                            <div style="font-size: 12.5px; color: var(--ink-muted); line-height: 1.5;">
                                {desc}
                            </div>
                        </div>""")
    walkthrough_block = "\n".join(cards_html)

    # Optional video embed block
    video_id = VIDEO_EMBEDS.get(p_date)
    video_block = ""
    if video_id:
        video_block = f"""
                    <!-- Embedded Video Walkthrough -->
                    <div style="margin-bottom: 22px; background: #FFFFFF; border: 2px solid var(--border-lip); border-radius: 12px; padding: 16px; box-shadow: 3px 3px 0 var(--border-lip);">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                            <span style="font-size: 18px;">🎬</span>
                            <strong style="font-family: 'Fraunces', serif; font-size: 16px;">60-Second Video Walkthrough</strong>
                        </div>
                        <div style="max-width: 320px; margin: 0 auto; aspect-ratio: 9 / 16; border-radius: 8px; overflow: hidden; border: 2px solid var(--border-lip); background: #000;">
                            <iframe src="https://www.youtube-nocookie.com/embed/{video_id}?rel=0" title="NYT Connections Hints - {long_date}" style="width: 100%; height: 100%; border: 0;" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                        </div>
                    </div>"""

    # Prev / Next Navigation buttons
    if prev_p:
        prev_d = prev_p["date"]
        prev_num = prev_p["puzzle_number"]
        _, prev_day, prev_short = format_date_long(prev_d)
        prev_btn = f'<a href="{prev_d}.html" class="btn-tactile btn-secondary" style="font-size: 12.5px; padding: 8px 14px; text-decoration: none;">&larr; Previous: {prev_day} ({prev_short}, #{prev_num})</a>'
    else:
        prev_btn = '<span></span>'

    if next_p:
        next_d = next_p["date"]
        next_num = next_p["puzzle_number"]
        _, next_day, next_short = format_date_long(next_d)
        next_btn = f'<a href="{next_d}.html" class="btn-tactile btn-secondary" style="font-size: 12.5px; padding: 8px 14px; text-decoration: none;">Next: {next_day} ({next_short}, #{next_num}) &rarr;</a>'
    else:
        next_btn = '<a href="../breakdowns.html" class="btn-tactile btn-primary" style="font-size: 12.5px; padding: 8px 14px; text-decoration: none;">Today\'s Live Board &rarr;</a>'

    history_block = build_history_section_html(current_page_date=p_date)

    return f"""<!DOCTYPE html>
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
    <meta name="robots" content="noindex, follow">
    <meta name="description" content="Friendly puzzle hints, board walkthrough, and 4-color category solutions for NYT Connections ({p_date}) Puzzle #{p_num}.">
    <link rel="canonical" href="https://connectionsassistant.com/breakdowns/{p_date}.html">
    <title>NYT Connections Hints &amp; Walkthrough — {p_date} (Puzzle #{p_num}) | Connections Assistant</title>
    <link rel="stylesheet" href="../style.css">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,700;1,9..144,600&family=JetBrains+Mono:wght@500;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Site Header with Universal Brand Bar & Navigation -->
    <header>
        <div class="nav-container">
            <a href="../index.html" class="brand-group">
                <span class="brand-title">Connections Assistant</span>
            </a>
            <div class="nav-right">
                <a href="../index.html" class="streak-pill" id="streakPill" title="Daily Solver Streak">
                    🔥 <span id="streakCount">1</span> Day Streak
                </a>
                <div class="nav-links">
                    <a href="../index.html">Solver</a>
                    <a href="../breakdowns.html" class="active">Breakdowns</a>
                    <a href="../nyt-connections-guide.html">Guide</a>
                    <a href="../strategy.html">Strategy</a>
                    <a href="../faq.html">FAQ</a>
                </div>
            </div>
        </div>
    </header>

    <div class="container" style="max-width: 860px; margin: 0 auto; padding: 24px 16px;">
        <!-- Breadcrumb & Quick Jump Bar -->
        <nav class="breadcrumb-bar" style="margin-bottom: 16px; font-size: 13px; color: var(--ink-muted); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 6px;">
                <a href="../index.html" style="color: var(--ink); text-decoration: none; font-weight: 600;">🏠 Home</a>
                <span>&rsaquo;</span>
                <a href="../breakdowns.html" style="color: var(--ink); text-decoration: none; font-weight: 600;">📚 Breakdowns</a>
                <span>&rsaquo;</span>
                <span style="color: var(--ink); font-weight: 700;">{short_d} (#{p_num})</span>
            </div>
            <a href="../breakdowns.html" class="btn-tactile btn-secondary" style="font-size: 11.5px; padding: 5px 12px; text-decoration: none;">
                &larr; Today's Live Board
            </a>
        </nav>

        <!-- Welcoming Archive Notification Pill -->
        <div style="background: #EFF6FF; border: 1.5px solid #93C5FD; border-radius: 12px; padding: 12px 16px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 22px; user-select: none;">👋</span>
                <div>
                    <div style="font-weight: 800; font-size: 13.5px; color: #1E3A8A;">
                        Welcome to the Historical Puzzle Library!
                    </div>
                    <div style="font-size: 12.5px; color: #1E40AF; line-height: 1.45;">
                        You're reviewing NYT Connections <strong>#{p_num}</strong> from <strong>{long_date}</strong>. Catching up on past boards or reviewing clever wordplay? You're in the right place!
                    </div>
                </div>
            </div>
            <a href="../breakdowns.html" class="btn-tactile btn-primary" style="font-size: 11.5px; padding: 6px 13px; text-decoration: none;">
                Play Today's Board &rarr;
            </a>
        </div>

        <main>
            <article class="content-bento" style="margin-bottom: 24px;">
                <div class="daily-header" style="border-bottom: 2px solid var(--stone); padding-bottom: 14px; margin-bottom: 18px;">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap;">
                        <span class="badge-archive" style="background: #EDE9FE; color: #5B21B6; border: 1px solid #7C3AED; font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px;">PAST PUZZLE ARCHIVE &bull; {p_date}</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; background: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px;">PUZZLE #{p_num}</span>
                    </div>
                    <h1 style="margin: 0 0 6px 0; font-size: 24px; font-family: 'Fraunces', serif;">
                        {long_date} Walkthrough &amp; Clues
                    </h1>
                    <p style="font-size: 14px; color: var(--ink-muted); margin: 0; line-height: 1.5;">
                        A friendly, step-by-step solver guide breaking down the <strong>{purple['title']}</strong> category, decoy traps, and all four color groupings.
                    </p>
                </div>

                <!-- Friendly Morning Solver's Debrief Box -->
                <div style="background: #FFFFFF; border: 2px solid var(--border-lip); border-radius: 12px; padding: 16px 18px; margin-bottom: 20px; box-shadow: 3px 3px 0 var(--border-lip);">
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 18px;">☕</span>
                        <h2 style="margin: 0; font-family: 'Fraunces', serif; font-size: 16px; color: var(--ink); border: none; padding: 0;">
                            Morning Coach's Debrief
                        </h2>
                    </div>
                    <p style="font-size: 13.5px; color: var(--ink-muted); margin: 0 0 10px 0; line-height: 1.55;">
                        Every Connections board comes with its own unique personality. Some mornings give us easy straight-down-the-line synonyms, while others feature sneaky cross-category traps designed to drain your four guesses before your morning coffee cools down! If this board gave you trouble, don't sweat it &mdash; you're in great company. Here is exactly how the 16 words sort out:
                    </p>
                    <div style="background: #FFFBEB; border: 1.5px solid #F59E0B; border-radius: 8px; padding: 11px 14px; font-size: 13px; color: #78350F; line-height: 1.5;">
                        <strong>🕵️ Coach's Red Herring Note:</strong> {red_herring_text}
                    </div>
                </div>
{video_block}
                <!-- Tactical Solved Board -->
                <div style="margin-bottom: 20px;">
                    <h3 style="font-size: 16px; margin: 0 0 8px 0; font-family: 'Fraunces', serif;">🎯 Solved Board &amp; Color Groups</h3>
                    <p style="font-size: 13px; color: var(--ink-muted); margin-bottom: 12px;">
                        All 16 words arranged into their official color-coded difficulty tiers:
                    </p>

                    <div class="solved-tiers-stack">
{solved_stack_html}
                    </div>

                    <p style="font-size: 13px; color: var(--ink-muted); margin: 12px 0 18px 0; line-height: 1.5;">
                        <strong>Lateral Wordplay Breakdown:</strong> {purple_note_text}
                    </p>
                </div>

                <!-- Category Walkthrough Cards -->
                <div style="margin: 22px 0 10px 0;">
                    <h3 style="font-size: 16px; margin-bottom: 12px; font-family: 'Fraunces', serif;">Category Solutions &amp; Word Connections:</h3>
{walkthrough_block}
                </div>

                <!-- Friendly Prev / Next Day Navigation -->
                <div style="margin-top: 24px; padding-top: 18px; border-top: 2px solid var(--stone); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                    {prev_btn}
                    {next_btn}
                </div>
            </article>

            <!-- Complete 30-Day Historical Archive Section -->
{history_block}

            <!-- Friendly Interactive Solver Nudge -->
            <div style="background: #FFFFFF; border: 2px solid var(--border-lip); border-radius: 12px; padding: 22px; margin: 28px 0; box-shadow: 3px 3px 0 var(--border-lip); text-align: center;">
                <h4 style="font-family: 'Fraunces', serif; font-size: 18px; margin-bottom: 8px;">
                    ☕ Ready to Tackle Today's Live Board?
                </h4>
                <p style="font-size: 13.5px; color: var(--ink-muted); max-width: 580px; margin: 0 auto 16px auto; line-height: 1.55;">
                    Don't let tricky red herrings break your streak! Use our gentle, spoiler-safe Interactive Solver Grid to test your hunches risk-free before submitting to the New York Times.
                </p>
                <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
                    <a href="../index.html" class="btn-tactile btn-primary" style="font-size: 13px; padding: 10px 18px; text-decoration: none;">
                        🎮 Open Interactive Solver Grid &rarr;
                    </a>
                    <a href="../breakdowns.html" class="btn-tactile btn-secondary" style="font-size: 13px; padding: 10px 18px; text-decoration: none;">
                        📖 Today's Live Breakdown &rarr;
                    </a>
                </div>
            </div>
        </main>

        <section class="support-banner">
            <h4>☕ Enjoying Your Morning Puzzle Companion?</h4>
            <p>We love keeping this helper fast, free, and friendly for everyone enjoying their daily morning word puzzle. If our gentle hints helped you today, consider buying us a coffee!</p>
            <div class="support-btn-group">
                <a href="https://ko-fi.com/connectionsassistant" target="_blank" rel="noopener noreferrer" class="btn-support btn-kofi">☕ Tip $3 on Ko-fi</a>
                <a href="https://paypal.me/j1223aw/2" target="_blank" rel="noopener noreferrer" class="btn-support btn-paypal">🅿️ Tip $2 via PayPal</a>
            </div>
        </section>

        <footer>
            <p>&copy; 2026 Connections Grouping Assistant. All rights reserved.</p>
            <p style="margin: 4px 0 12px 0;">This independent helper utility is not affiliated with the New York Times Company.</p>
            <div class="footer-links">
                <a href="../privacy.html">Privacy Policy</a>
                <a href="../terms.html">Terms of Service</a>
                <a href="../contact.html">Contact Us</a>
                <a href="https://www.reddit.com/user/ConnectionsCoach/" target="_blank" rel="noopener noreferrer">Reddit: u/ConnectionsCoach</a>
                <a href="https://www.youtube.com/@ConnectionsAssistant" target="_blank" rel="noopener noreferrer">YouTube: @ConnectionsAssistant</a>
            </div>
        </footer>
    </div>
</body>
</html>"""

def run():
    print(f"[+] Loaded {len(all_puzzles)} cached puzzles from {CACHE_DIR.name}")
    dates_asc = sorted(all_dates_desc)
    generated_count = 0

    # 1. Generate / Update All 30 Archive Pages
    for idx, d_str in enumerate(dates_asc):
        out_file = ARCHIVE_DIR / f"{d_str}.html"
        prev_p = puzzle_by_date[dates_asc[idx - 1]] if idx > 0 else None
        next_p = puzzle_by_date[dates_asc[idx + 1]] if idx < len(dates_asc) - 1 else None
        
        p_data = puzzle_by_date[d_str]
        page_html = build_standalone_archive_page(p_data, prev_p, next_p)
        out_file.write_text(page_html, encoding="utf-8")
        generated_count += 1
        print(f"  [✓] Generated welcoming archive page: {out_file.name} (Puzzle #{p_data['puzzle_number']})")

    print(f"\n[✓] Successfully generated all {generated_count} welcoming archive pages!")

    # 2. Update public/breakdowns.html with the Welcoming History Section
    breakdowns_path = PUBLIC_DIR / "breakdowns.html"
    b_content = breakdowns_path.read_text(encoding="utf-8")
    b_history_html = build_history_section_html(current_page_date="today")

    if '<!-- PAST PUZZLE BREAKDOWNS & HISTORY SECTION -->' in b_content:
        b_content = re.sub(
            r'<!-- PAST PUZZLE BREAKDOWNS & HISTORY SECTION -->[\s\S]*?</section>',
            b_history_html,
            b_content
        )
        breakdowns_path.write_text(b_content, encoding="utf-8")
        print("[✓] Updated PAST PUZZLE BREAKDOWNS & HISTORY SECTION in breakdowns.html!")
    else:
        print("[!] Warning: PAST PUZZLE section marker not found in breakdowns.html!")

    # 3. Clean sitemap.xml to include only high-value canonical core pages
    sitemap_path = PUBLIC_DIR / "sitemap.xml"
    today_date = all_dates_desc[0] if all_dates_desc else datetime.now().strftime("%Y-%m-%d")
    core_pages = [
        ("https://connectionsassistant.com/", today_date, "daily", "1.00"),
        ("https://connectionsassistant.com/breakdowns.html", today_date, "daily", "0.95"),
        ("https://connectionsassistant.com/nyt-connections-guide.html", "2026-11-14", "weekly", "0.85"),
        ("https://connectionsassistant.com/strategy.html", "2026-11-14", "weekly", "0.85"),
        ("https://connectionsassistant.com/faq.html", "2026-11-14", "weekly", "0.80"),
        ("https://connectionsassistant.com/about.html", "2026-11-14", "monthly", "0.75"),
        ("https://connectionsassistant.com/contact.html", "2026-11-14", "monthly", "0.50"),
        ("https://connectionsassistant.com/privacy.html", "2026-11-14", "yearly", "0.30"),
        ("https://connectionsassistant.com/terms.html", "2026-11-14", "yearly", "0.30"),
    ]
    url_blocks = []
    for loc, lastmod, freq, prio in core_pages:
        url_blocks.append(f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>""")
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(url_blocks) + "\n</urlset>\n"
    sitemap_path.write_text(sitemap_xml, encoding="utf-8")
    print(f"[✓] Cleaned sitemap.xml to {len(core_pages)} high-value core pages (excluded thin programmatic archives)!")

    print("\n[✓] Done generating archives, linking history, and updating sitemap!")

if __name__ == "__main__":
    run()
