import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant")
PUBLIC_DIR = BASE_DIR / "public"
ARCHIVE_DIR = PUBLIC_DIR / "breakdowns"
CACHE_DIR = BASE_DIR / "puzzle_history_cache"

ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# Curated metadata dictionary for rich decoy & wordplay notes
METADATA = {
    "2026-11-11": {
        "decoy": "the 4-color <strong>TEA</strong> rainbow decoy trap",
        "red_herring": "<em>GREEN, AFTERNOON, BUBBLE, and HERBAL</em> tempt an immediate 'Types of Tea' grouping. However, recognizing that each belongs to a different tier (Golf, Palindromes, Inflatables, Medicine) dissolves the decoy and keeps all four groups clean.",
        "purple_note": "The Purple group relies on words ending in palindromes: <em>AFTERNOON</em> (noon), <em>PATOOT</em> (toot), <em>RHEOSTATS</em> (stats), and <em>SHREDDER</em> (redder)."
    },
    "2026-11-10": {
        "decoy": "the 5-word <strong>BEEKEEPER</strong> trade trap",
        "red_herring": "<em>BEEKEEPER</em> appears alongside <em>APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT</em>, tempting an immediate old-timey occupation grouping. However, recognizing that <em>BEEKEEPER</em> contains exactly five E's unlocks the Purple vowel tier and leaves the four true historic trades intact.",
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
        "red_herring": "<em>EASTER</em> appears alongside <em>NORTH</em> and <em>SOUTH</em>, creating an alluring compass direction trap. Isolating the storm endings neutralizes the decoy.",
        "purple_note": "The Purple group relies on storm endings: <em>CANE</em> (hurricane), <em>CLONE</em> (cyclone), <em>EASTER</em> (nor'easter), and <em>SOON</em> (monsoon)."
    },
    "2026-11-06": {
        "decoy": "the composition / copy decoy trap",
        "red_herring": "<em>COPY</em> and <em>COMPOSITION</em> overlap heavily with writing and editing terms, creating tempting cross-category confusion with truck categories.",
        "purple_note": "The Purple group relies on phrases ending in parts of the eye: pupil, iris, cornea, and retina associations."
    },
    "2026-11-05": {
        "decoy": "the floral and cocktail overlap decoy",
        "red_herring": "Botanical terms overlap with liquor flavorings. Separating the footwear heels first keeps the liquor letter transformations intact.",
        "purple_note": "The Purple group consists of liquors with their last letters altered to form common words."
    }
}

# Load all cached puzzles sorted descending by date
all_puzzles = []
for p_path in sorted(CACHE_DIR.glob("*.json"), reverse=True):
    try:
        data = json.loads(p_path.read_text(encoding="utf-8"))
        all_puzzles.append(data)
    except Exception as e:
        print(f"Error reading {p_path}: {e}")

print(f"Loaded {len(all_puzzles)} cached puzzles.")

def format_date_long(d_str: str) -> tuple[str, str]:
    """Return ('Wednesday, Nov 11, 2026', 'Wednesday')"""
    dt = datetime.strptime(d_str, "%Y-%m-%d")
    return dt.strftime("%A, %b %d, %Y"), dt.strftime("%A")

def build_history_section_html(current_page_date: str = "today") -> str:
    """Build the Past Puzzle Breakdowns & History Archive HTML block."""
    recent_cards = []
    # Featured top 5 most recent completed days
    for p in all_puzzles[:5]:
        p_date = p["date"]
        p_num = p["puzzle_number"]
        long_date, day_name = format_date_long(p_date)
        meta = METADATA.get(p_date, {})
        decoy_text = meta.get("decoy", f"Lateral wordplay &amp; category overlap")
        purple_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Purple"), "TRICKY WORDPLAY")
        yellow_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Yellow"), "")
        
        # Determine relative link depending on if on /breakdowns.html or inside /breakdowns/
        link_prefix = "" if current_page_date == "today" else ""
        link_target = f"breakdowns/{p_date}.html" if current_page_date == "today" else f"{p_date}.html"
        
        recent_cards.append(f"""                    <div style="background: #FFFFFF; border: 1.5px solid var(--border-lip); border-radius: 8px; padding: 12px 14px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div>
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                                <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 700; background: #FEF3C7; color: #92400E; padding: 2px 6px; border-radius: 4px;">PUZZLE #{p_num}</span>
                                <span style="font-weight: 700; font-size: 14px; color: var(--ink);">{long_date}</span>
                            </div>
                            <div style="font-size: 12.5px; color: var(--ink-muted);">
                                <strong>Yellow:</strong> {yellow_cat} &bull; <strong>Purple:</strong> {purple_cat}
                            </div>
                        </div>
                        <a href="{link_target}" class="btn-tactile btn-secondary" style="font-size: 12px; padding: 6px 12px; text-decoration: none;">
                            Read Full Breakdown &rarr;
                        </a>
                    </div>""")

    # Grid of all 30 days
    archive_grid_items = []
    for p in all_puzzles:
        p_date = p["date"]
        p_num = p["puzzle_number"]
        dt = datetime.strptime(p_date, "%Y-%m-%d")
        short_date = dt.strftime("%b %d (%a)")
        purple_cat = next((c["title"] for c in p["categories"] if c["tier"] == "Purple"), "")
        link_target = f"breakdowns/{p_date}.html" if current_page_date == "today" else f"{p_date}.html"
        
        is_current = (p_date == current_page_date)
        bg = "#F3E8FF" if is_current else "#FFFFFF"
        border = "2px solid #7C3AED" if is_current else "1px solid var(--border-lip)"

        archive_grid_items.append(f"""                        <a href="{link_target}" style="display: block; text-decoration: none; background: {bg}; border: {border}; border-radius: 6px; padding: 8px 10px; color: inherit; transition: transform 0.1s ease;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                                <span style="font-weight: 700; font-size: 12.5px; color: var(--ink);">{short_date}</span>
                                <span style="font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--ink-muted); font-weight: 700;">#{p_num}</span>
                            </div>
                            <div style="font-size: 11px; color: #6D28D9; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{purple_cat}">
                                🟪 {purple_cat}
                            </div>
                        </a>""")

    recent_html = "\n".join(recent_cards)
    grid_html = "\n".join(archive_grid_items)

    return f"""            <!-- PAST PUZZLE BREAKDOWNS & HISTORY SECTION -->
            <section class="breakdown-card" id="history" style="background: #FAF8F5; border: 2px solid var(--border-lip); margin: 24px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; border-bottom: 2px solid var(--stone); padding-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 18px; font-family: 'Fraunces', serif;">📚 Past Puzzle Breakdowns &amp; History Archive</h3>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; background: #EDE9FE; color: #5B21B6; border: 1px solid #7C3AED; padding: 2px 8px; border-radius: 4px; font-weight: 700;">30-DAY ARCHIVE</span>
                </div>
                <p style="font-size: 13.5px; color: var(--ink-muted); margin: 0 0 14px 0; line-height: 1.5;">
                    Missed a previous day's morning puzzle or reviewing past tricky boards? Explore full archived breakdowns with interactive boards, category solutions, and tactical explanations:
                </p>
                <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 18px;">
{recent_html}
                </div>

                <details class="archive-accordion" style="background: #FFFFFF; border: 1.5px solid var(--border-lip); border-radius: 8px; padding: 12px 14px;" open>
                    <summary style="cursor: pointer; font-family: 'JetBrains Mono', monospace; font-weight: 700; font-size: 12.5px; color: var(--ink); display: flex; justify-content: space-between; align-items: center; user-select: none;">
                        <span>📅 Explore Complete 30-Day Historical Archive (Oct 13 – Nov 11)</span>
                        <span style="font-size: 11px; background: #FEF3C7; color: #92400E; padding: 2px 6px; border-radius: 4px;">30 Puzzles &bull; Click to Toggle</span>
                    </summary>
                    <div style="margin-top: 12px; display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 8px;">
{grid_html}
                    </div>
                </details>
            </section>"""

print("History section builder defined.")
