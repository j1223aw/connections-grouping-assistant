import json
from pathlib import Path
import urllib.request
from datetime import datetime, timedelta

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant")
ARCHIVE_DATA_DIR = BASE_DIR / "puzzle_history_cache"
ARCHIVE_DATA_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

TIER_NAMES = {0: "Yellow", 1: "Green", 2: "Blue", 3: "Purple"}
START_GAME_DATE = datetime(2023, 6, 12).date()

# We want the past 30 days from Nov 11, 2026 back to Oct 13, 2026
start_dt = datetime(2026, 11, 11)
dates_to_fetch = [(start_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]

print(f"Fetching {len(dates_to_fetch)} dates from {dates_to_fetch[-1]} to {dates_to_fetch[0]}...")

results = {}
for d_str in dates_to_fetch:
    cache_file = ARCHIVE_DATA_DIR / f"{d_str}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            results[d_str] = data
            print(f"  [cached] {d_str} (Puzzle #{data.get('puzzle_number')})")
            continue
        except Exception:
            pass

    url = f"https://www.nytimes.com/svc/connections/v2/{d_str}.json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            
            p_date = datetime.strptime(d_str, "%Y-%m-%d").date()
            puzzle_number = (p_date - START_GAME_DATE).days + 1
            
            raw_cats = raw.get("categories", [])
            categories = []
            starting_cards = []
            for idx, cat in enumerate(raw_cats):
                level = cat.get("level", idx)
                tier = cat.get("tier", TIER_NAMES.get(level, f"Tier {level+1}"))
                title = cat.get("title", "").strip()
                words = []
                for card in cat.get("cards", []):
                    if isinstance(card, dict) and "content" in card:
                        w = str(card["content"]).strip().upper()
                        words.append(w)
                        starting_cards.append((card.get("position", 0), w))
                categories.append({
                    "tier": tier,
                    "level": level,
                    "title": title,
                    "words": words
                })
            
            starting_cards.sort(key=lambda x: x[0])
            starting_board = [c[1] for c in starting_cards]
            
            normalized = {
                "id": puzzle_number,
                "api_id": raw.get("id"),
                "puzzle_number": puzzle_number,
                "date": d_str,
                "starting_board": starting_board,
                "categories": categories
            }
            cache_file.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")
            results[d_str] = normalized
            print(f"  [fetched] {d_str} (Puzzle #{puzzle_number}) - {[c['title'] for c in categories]}")
    except Exception as e:
        print(f"  [error] {d_str}: {e}")

print(f"\nDone! Successfully collected {len(results)} puzzles.")
