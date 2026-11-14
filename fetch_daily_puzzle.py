"""
fetch_daily_puzzle.py

Ingestion pipeline for NYT Connections daily puzzle:
1. Queries the official NYT Connections v2 endpoint:
   https://www.nytimes.com/svc/connections/v2/{target_date}.json using urllib.request.
2. Defaults to the current date using the America/New_York timezone so it aligns with midnight drops.
3. Includes a browser User-Agent header in the request to avoid 403 blocks.
4. Normalizes the incoming JSON into a clean structure containing:
   - id
   - date
   - categories: an array of 4 objects containing tier, level (0 to 3), title, and words (all uppercase).
5. Writes the normalized output to daily_puzzle.json in the root folder with UTF-8 encoding and indent=2.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ENDPOINT_URL_TEMPLATE = "https://www.nytimes.com/svc/connections/v2/{target_date}.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

TIER_NAMES = {
    0: "Yellow",
    1: "Green",
    2: "Blue",
    3: "Purple",
}


def get_current_ny_date() -> str:
    """Return today's date formatted as YYYY-MM-DD in America/New_York timezone."""
    ny_tz = ZoneInfo("America/New_York")
    return datetime.now(ny_tz).strftime("%Y-%m-%d")


def fetch_raw_puzzle(target_date: str) -> dict:
    """Fetch raw puzzle data from NYT Connections v2 endpoint using urllib.request."""
    url = ENDPOINT_URL_TEMPLATE.format(target_date=target_date)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP request failed with status code {response.status}")
            raw_content = response.read().decode("utf-8")
            return json.loads(raw_content)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code} fetching puzzle from {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error fetching puzzle from {url}: {e.reason}") from e


def normalize_puzzle_data(raw_data: dict, target_date: str) -> dict:
    """Normalize raw NYT Connections JSON into the clean project structure."""
    raw_categories = raw_data.get("categories", [])
    normalized_categories = []

    for idx, cat in enumerate(raw_categories):
        level = cat.get("level", idx)
        tier = cat.get("tier", TIER_NAMES.get(level, f"Tier {level + 1}"))
        title = cat.get("title", "").strip()

        words = []
        if "cards" in cat and isinstance(cat["cards"], list):
            for card in cat["cards"]:
                if isinstance(card, dict) and "content" in card:
                    words.append(str(card["content"]).strip().upper())
        elif "words" in cat and isinstance(cat["words"], list):
            words = [str(w).strip().upper() for w in cat["words"]]

        normalized_categories.append({
            "tier": tier,
            "level": level,
            "title": title,
            "words": words,
        })

    # Preserve exact official starting board order if positions are provided
    starting_cards = []
    for cat in raw_categories:
        for card in cat.get("cards", []):
            if isinstance(card, dict) and "content" in card:
                starting_cards.append((card.get("position", 0), str(card["content"]).strip().upper()))
    if starting_cards:
        starting_cards.sort(key=lambda x: x[0])
        starting_board = [c[1] for c in starting_cards]
    else:
        starting_board = []

    # Calculate authentic NYT Connections Game Number (Puzzle #1 on June 12, 2023)
    p_date = datetime.strptime(target_date, "%Y-%m-%d").date()
    start_date = datetime(2023, 6, 12).date()
    puzzle_number = (p_date - start_date).days + 1

    return {
        "id": puzzle_number,
        "api_id": raw_data.get("id"),
        "puzzle_number": puzzle_number,
        "date": raw_data.get("print_date", target_date),
        "starting_board": starting_board,
        "categories": normalized_categories,
    }


def save_puzzle_json(data: dict, output_path: Path) -> None:
    """Save normalized puzzle data to JSON with UTF-8 encoding and indent=2."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def fetch_and_save_daily_puzzle(target_date: str | None = None, output_path: Path | None = None) -> Path:
    """Execute the full ingestion pipeline for given or default date."""
    if not target_date:
        target_date = get_current_ny_date()

    if output_path is None:
        output_path = Path(__file__).resolve().parent / "daily_puzzle.json"

    print(f"[+] Querying NYT Connections v2 endpoint for date: {target_date} (America/New_York)...")
    try:
        raw_data = fetch_raw_puzzle(target_date)
    except Exception as e:
        if output_path.exists():
            try:
                cached = json.loads(output_path.read_text(encoding="utf-8"))
                if cached.get("date") == target_date:
                    print(f"[!] Network fetch failed ({e}). Using existing cached {output_path.name} for {target_date}.")
                    return output_path
            except Exception:
                pass
        raise

    print(f"[+] Normalizing puzzle data (ID: {raw_data.get('id')})...")
    normalized_data = normalize_puzzle_data(raw_data, target_date)

    total_words = sum(len(cat["words"]) for cat in normalized_data["categories"])
    print(f"[+] Extracted {len(normalized_data['categories'])} categories ({total_words} words total).")

    print(f"[+] Writing normalized puzzle to: {output_path}...")
    save_puzzle_json(normalized_data, output_path)

    print(f"[✓] Successfully generated {output_path.name} with {total_words} words.")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Fetch and normalize daily NYT Connections puzzle.")
    parser.add_argument(
        "positional_date",
        nargs="?",
        default=None,
        help="Optional target date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--date",
        dest="date",
        default=None,
        help="Target date in YYYY-MM-DD format (defaults to current date in America/New_York timezone)",
    )
    parser.add_argument(
        "--output",
        dest="output",
        default=None,
        help="Output path for daily_puzzle.json (defaults to daily_puzzle.json in script directory)",
    )
    args = parser.parse_args()

    target_date = args.date or args.positional_date
    out_file = Path(args.output).resolve() if args.output else None

    try:
        fetch_and_save_daily_puzzle(target_date=target_date, output_path=out_file)
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
