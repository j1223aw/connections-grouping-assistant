"""
render_family_board.py

Generates the daily morning family puzzle challenge:
1. Reads daily_puzzle.json (date and starting_board).
2. Renders an authentic, crisp 1080x1080 board screenshot via Playwright (HD scale factor 2).
3. Saves to todays_family_board.png and todays_board_hd.png (and artifact directory).
4. Generates todays_family_post.txt with the morning family challenge message.
5. Copies the message to the Windows clipboard via 64-bit ctypes.
"""

import ctypes
from ctypes import wintypes
from datetime import datetime
import json
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent
PUZZLE_FILE = ROOT_DIR / "daily_puzzle.json"
OUTPUT_IMG = ROOT_DIR / "todays_family_board.png"
OUTPUT_IMG_HD = ROOT_DIR / "todays_board_hd.png"
POST_FILE = ROOT_DIR / "todays_family_post.txt"
ARTIFACT_DIR = Path(r"C:\Users\Infinite\.gemini\antigravity\brain\deba67d0-cd17-4201-8eac-06f483d25f88")
ARTIFACT_IMG = ARTIFACT_DIR / "todays_family_board.png"


def copy_to_clipboard_clean(text: str) -> None:
    """Copies text to the Windows clipboard as CF_UNICODETEXT using 64-bit ctypes."""
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL

    encoded = text.encode("utf-16le") + b"\x00\x00"
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    p_mem = kernel32.GlobalLock(h_mem)
    ctypes.memmove(p_mem, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)

    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
    user32.CloseClipboard()


def load_puzzle(puzzle_path: Path) -> dict:
    if not puzzle_path.exists():
        raise FileNotFoundError(f"Missing {puzzle_path}")
    with open(puzzle_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_board_html(data: dict) -> str:
    pdate = data.get("date", "2026-11-12")
    try:
        dt = datetime.strptime(pdate, "%Y-%m-%d")
        formatted_date = f"{dt.strftime('%B')} {dt.day}, {dt.year}"
    except Exception:
        formatted_date = pdate

    words = data.get("starting_board", [])
    if not words:
        # Fallback: flatten categories
        for cat in data.get("categories", []):
            words.extend(cat.get("words", []))

    # Ensure 16 words
    words = words[:16]

    tiles_html = []
    for w in words:
        w_clean = str(w).strip().upper()
        # Add long class for long words/compounds
        extra_cls = " long" if len(w_clean) >= 13 else ""
        tiles_html.append(f'    <div class="tile{extra_cls}">{w_clean}</div>')

    grid_content = "\n".join(tiles_html)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1080px;
    background: #FFFFFF;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 50px 40px;
  }}
  .header {{
    text-align: center;
    margin-bottom: 24px;
  }}
  .title-row {{
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 16px;
    margin-bottom: 10px;
  }}
  .title {{
    font-family: 'Georgia', serif;
    font-size: 58px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: #121212;
  }}
  .date {{
    font-family: 'Georgia', serif;
    font-size: 32px;
    font-weight: 400;
    color: #555555;
  }}
  .subtext {{
    font-size: 24px;
    font-weight: 500;
    color: #333333;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    width: 900px;
    margin-bottom: 34px;
  }}
  .tile {{
    background: #EFEFE6;
    height: 126px;
    border-radius: 9px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 10px 14px;
    font-size: 21px;
    font-weight: 700;
    text-transform: uppercase;
    color: #000000;
    line-height: 1.16;
    letter-spacing: 0.2px;
  }}
  .tile.long {{
    font-size: 18px;
    line-height: 1.14;
    padding: 8px 10px;
  }}
  .mistakes-row {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 30px;
    font-size: 24px;
    font-weight: 500;
    color: #333333;
  }}
  .dots {{
    display: flex;
    gap: 10px;
  }}
  .dot {{
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #5A5A5A;
  }}
  .actions {{
    display: flex;
    gap: 16px;
  }}
  .btn {{
    border: 1.5px solid #000000;
    border-radius: 30px;
    padding: 14px 28px;
    font-size: 22px;
    font-weight: 600;
    color: #000000;
    background: #FFFFFF;
  }}
  .btn.submit {{
    border-color: #888888;
    color: #888888;
  }}
</style>
</head>
<body>
  <div class="header">
    <div class="title-row">
      <div class="title">Connections</div>
      <div class="date">{formatted_date}</div>
    </div>
    <div class="subtext">Create four groups of four!</div>
  </div>

  <div class="grid">
{grid_content}
  </div>

  <div class="mistakes-row">
    <span>Mistakes Remaining:</span>
    <div class="dots">
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
      <div class="dot"></div>
    </div>
  </div>

  <div class="actions">
    <div class="btn">Shuffle</div>
    <div class="btn">Deselect All</div>
    <div class="btn submit">Submit</div>
  </div>
</body>
</html>
"""


def generate_family_message() -> str:
    return (
        "Good Morning, Family! ☕\n\n"
        "Here’s Today’s NYT Connections puzzle for your morning coffee. The goal is to sort the 16 words into 4 secret groups of 4.\n\n"
        "Heads up: there is a VERY sneaky trap today that tries to pull 4 words together that don’t actually belong. Don’t fall for it!\n\n"
        "Play it here: https://www.nytimes.com/games/connections\n\n"
        "Let’s see who can solve it with zero mistakes! 🎯\n\n"
        "(If you get stuck and don’t want to burn your 4 guesses, you can test candidate combos on the free scratchboard here: https://connectionsassistant.com)"
    )


def render_family_package(puzzle_path: Path = PUZZLE_FILE, copy_to_clip: bool = True) -> tuple[Path, Path]:
    data = load_puzzle(puzzle_path)
    html_content = build_board_html(data)

    print(f"[+] Launching Playwright to render clean HD board screenshot...")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080}, device_scale_factor=2)
        page.set_content(html_content)
        page.screenshot(path=str(OUTPUT_IMG))
        page.screenshot(path=str(OUTPUT_IMG_HD))
        if ARTIFACT_DIR.exists():
            page.screenshot(path=str(ARTIFACT_IMG))
        browser.close()

    print(f"[✓] Rendered family board image -> {OUTPUT_IMG.name}")

    msg = generate_family_message()
    POST_FILE.write_text(msg, encoding="utf-8")
    print(f"[✓] Staged family challenge post -> {POST_FILE.name}")

    if copy_to_clip:
        copy_to_clipboard_clean(msg)
        print("[✓] Copied family challenge post directly to Windows clipboard!")

    return OUTPUT_IMG, POST_FILE


if __name__ == "__main__":
    render_family_package()
