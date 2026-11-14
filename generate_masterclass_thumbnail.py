import asyncio
from datetime import datetime
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output_masterclass"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAIL_PATH = OUTPUT_DIR / "today_deep_dive_thumbnail.png"
PUZZLE_FILE = ROOT_DIR / "daily_puzzle.json"

TRAPS_BY_DATE = {
    "2026-11-14": {
        "title": 'The Sneaky "WARFARE & COMBAT" Trap',
        "subtitle": "These words tempt a fake battle/military category, but actually cross Blue and Purple tiers:",
        "words": ["BATTLE", "STRATEGO", "CHESS", "GO"],
    },
    "2026-11-13": {
        "title": 'The 3-Tier "WATER & OCEAN" Trap',
        "subtitle": "These 4 words tempt a fake water & beach category, but actually cross 3 different color tiers:",
        "words": ["SURF", "WAVES", "WATER SKIER", "BARGE"],
    },
    "2026-11-12": {
        "title": 'The 4-Color "BACK TO THE FUTURE" Trap',
        "subtitle": "These 4 words tempt a fake movie category, but each belongs to a different color tier:",
        "words": ["GREAT SCOTT", "FLUX CAPACITOR", "DOC BROWN", "MARTY MCFLY"],
    },
}


def build_thumbnail_html(data: dict) -> str:
    pdate = data.get("date", "2026-11-13")
    pid = data.get("id", data.get("puzzle_number", "1251"))

    try:
        dt = datetime.strptime(pdate, "%Y-%m-%d")
        date_pill_str = f"{dt.strftime('%b').upper()} {dt.day}, {dt.year} &bull; #{pid}"
    except Exception:
        date_pill_str = f"{pdate} &bull; #{pid}"

    categories = data.get("categories", [])
    yellow_title = categories[0].get("title", "TIER 1") if len(categories) > 0 else "TIER 1"
    green_title = categories[1].get("title", "TIER 2") if len(categories) > 1 else "TIER 2"
    blue_title = categories[2].get("title", "TIER 3") if len(categories) > 2 else "TIER 3"
    purple_title = categories[3].get("title", "TIER 4") if len(categories) > 3 else "TIER 4"

    trap_info = TRAPS_BY_DATE.get(
        pdate,
        {
            "title": 'The Sneaky Red Herring Trap',
            "subtitle": "Watch out for words that appear to connect before checking all four category themes:",
            "words": ["SURF", "WAVES", "WATER SKIER", "BARGE"],
        },
    )

    trap_tiles_html = "".join(
        f'<div class="decoy-tile">{w}</div>' for w in trap_info["words"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,800;9..144,900&family=JetBrains+Mono:wght@700;800&family=Plus+Jakarta+Sans:wght@700;800;900&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1920px;
    height: 1080px;
    background: #FAF8F5;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #1A1A1A;
    display: flex;
    flex-direction: column;
    padding: 50px 70px;
    overflow: hidden;
    position: relative;
  }}

  /* Neo-Brutalist Outer Accent Frame */
  .frame-border {{
    position: absolute;
    inset: 20px;
    border: 5px solid #1A1A1A;
    pointer-events: none;
    border-radius: 24px;
  }}

  /* Header Bar */
  .header-bar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 5px solid #1A1A1A;
    padding-bottom: 24px;
    margin-bottom: 36px;
  }}
  .brand-badge {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}
  .logo-box {{
    background: #1A1A1A;
    color: #FFFFFF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 800;
    padding: 8px 18px;
    border-radius: 10px;
    letter-spacing: 0.05em;
  }}
  .header-title {{
    font-family: 'Fraunces', serif;
    font-size: 42px;
    font-weight: 900;
    letter-spacing: -0.02em;
  }}
  .date-pill {{
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    box-shadow: 4px 4px 0 #1A1A1A;
    border-radius: 12px;
    padding: 10px 24px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 800;
  }}

  /* Main Split Layout */
  .main-split {{
    display: grid;
    grid-template-columns: 1.05fr 1fr;
    gap: 44px;
    flex: 1;
    align-items: center;
  }}

  /* Left: 4 Tier Stack */
  .tier-stack {{
    display: flex;
    flex-direction: column;
    gap: 20px;
    height: 100%;
    justify-content: center;
  }}
  .tier-row {{
    display: flex;
    align-items: center;
    border: 4.5px solid #1A1A1A;
    border-radius: 18px;
    box-shadow: 7px 7px 0 #1A1A1A;
    padding: 22px 28px;
    font-size: 30px;
    font-weight: 900;
    letter-spacing: -0.01em;
  }}
  .tier-row.yellow {{ background: #F9CA24; color: #1A1A1A; }}
  .tier-row.green  {{ background: #6AB04C; color: #FFFFFF; }}
  .tier-row.blue   {{ background: #4834D4; color: #FFFFFF; }}
  .tier-row.purple {{ background: #BE2EDD; color: #FFFFFF; }}
  
  .tier-tag {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px;
    background: rgba(0, 0, 0, 0.18);
    padding: 6px 14px;
    border-radius: 8px;
    margin-right: 22px;
    letter-spacing: 0.05em;
    font-weight: 800;
  }}
  .tier-label {{
    flex: 1;
    font-family: 'Plus Jakarta Sans', sans-serif;
  }}

  /* Right: The High-CTR Decoy Hook Card */
  .decoy-card {{
    background: #FFFFFF;
    border: 5px solid #1A1A1A;
    border-radius: 22px;
    box-shadow: 10px 10px 0 #1A1A1A;
    padding: 36px 36px;
    display: flex;
    flex-direction: column;
    gap: 22px;
  }}
  .alert-badge {{
    background: #FF4757;
    color: #FFFFFF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 22px;
    font-weight: 900;
    padding: 8px 18px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    align-self: flex-start;
    border: 3px solid #1A1A1A;
  }}
  .decoy-title {{
    font-family: 'Fraunces', serif;
    font-size: 50px;
    line-height: 1.1;
    font-weight: 900;
    letter-spacing: -0.02em;
  }}
  .decoy-subtitle {{
    font-size: 22px;
    color: #555555;
    font-weight: 700;
    line-height: 1.4;
  }}
  .decoy-tiles {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    margin-top: 6px;
  }}
  .decoy-tile {{
    background: #FFF3CD;
    border: 3.5px solid #1A1A1A;
    border-radius: 12px;
    box-shadow: 3px 3px 0 #1A1A1A;
    padding: 14px 18px;
    text-align: center;
    font-size: 24px;
    font-weight: 900;
    letter-spacing: 0.03em;
  }}

  .cta-badge {{
    margin-top: 8px;
    background: #1A1A1A;
    color: #FFFFFF;
    border-radius: 14px;
    padding: 14px 24px;
    text-align: center;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.02em;
  }}
</style>
</head>
<body>
  <div class="frame-border"></div>

  <!-- Header -->
  <header class="header-bar">
    <div class="brand-badge">
      <div class="logo-box">NYT CONNECTIONS</div>
      <div class="header-title">Full Solution & Word Meanings</div>
    </div>
    <div class="date-pill">{date_pill_str}</div>
  </header>

  <!-- Main Split -->
  <main class="main-split">
    <!-- Left: 4 Tiers -->
    <div class="tier-stack">
      <div class="tier-row yellow">
        <span class="tier-tag">TIER 1</span>
        <span class="tier-label">{yellow_title}</span>
      </div>
      <div class="tier-row green">
        <span class="tier-tag">TIER 2</span>
        <span class="tier-label">{green_title}</span>
      </div>
      <div class="tier-row blue">
        <span class="tier-tag">TIER 3</span>
        <span class="tier-label">{blue_title}</span>
      </div>
      <div class="tier-row purple">
        <span class="tier-tag">TIER 4</span>
        <span class="tier-label">{purple_title}</span>
      </div>
    </div>

    <!-- Right: High-CTR Trap Hook -->
    <div class="decoy-card">
      <div class="alert-badge">⚠️ DECOY TRAP ALERT</div>
      <div class="decoy-title">{trap_info['title']}</div>
      <div class="decoy-subtitle">{trap_info['subtitle']}</div>
      <div class="decoy-tiles">
        {trap_tiles_html}
      </div>
      <div class="cta-badge">STEP-BY-STEP WALKTHROUGH &bull; 16 WORDS</div>
    </div>
  </main>
</body>
</html>
"""


async def generate_thumbnail(puzzle_path: Path = PUZZLE_FILE):
    data = {}
    if puzzle_path.exists():
        with open(puzzle_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    html_content = build_thumbnail_html(data)
    print(f"[+] Launching Playwright to render 1920x1080 thumbnail for {data.get('date')}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page.set_content(html_content)
        await page.evaluate("() => document.fonts.ready")
        await page.screenshot(path=str(THUMBNAIL_PATH))
        await browser.close()
    print(f"[✓] Masterclass thumbnail successfully rendered: {THUMBNAIL_PATH} ({THUMBNAIL_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    asyncio.run(generate_thumbnail())
