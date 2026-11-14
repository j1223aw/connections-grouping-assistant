"""
stage_shorts_metadata.py

Step 2 of Phase 1 YouTube Shorts Local Pipeline:
1. Verifies/creates output_shorts/, output_shorts/frames/, output_shorts/audio/.
2. Reads daily_puzzle.json from root directory.
3. Formats and writes output_shorts/today_shorts_metadata.txt with:
   - Video Title: NYT Connections Hints Today - [Date] #shorts #nytconnections
   - Description / Pinned Comment:
     Stuck on today's grid? View the full interactive board breakdown & test associations without spoilers at: https://connectionsassistant.com/breakdowns.html
   - Tags: NYT Connections, Connections hints, NYT Connections today, Connections Assistant
"""

import argparse
import json
from pathlib import Path
import sys


def ensure_directories(base_dir: Path) -> dict[str, Path]:
    """Ensure output_shorts and its subdirectories exist."""
    dirs = {
        "output": base_dir / "output_shorts",
        "frames": base_dir / "output_shorts" / "frames",
        "audio": base_dir / "output_shorts" / "audio",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def load_puzzle_data(puzzle_path: Path) -> dict:
    """Load and parse daily_puzzle.json."""
    if not puzzle_path.exists():
        raise FileNotFoundError(
            f"Puzzle file not found at '{puzzle_path}'. "
            "Please run 'python fetch_daily_puzzle.py' first."
        )

    with open(puzzle_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_metadata_content(puzzle_data: dict) -> str:
    """Generate clean YouTube Shorts metadata text."""
    puzzle_date = puzzle_data.get("date", "Today")

    video_title = f"NYT Connections Hints Today - {puzzle_date} #shorts #nytconnections"
    description_and_comment = (
        "Stuck on today's grid? View the full interactive board breakdown & test associations without spoilers at: "
        "https://connectionsassistant.com/breakdowns.html"
    )
    tags = "NYT Connections, Connections hints, NYT Connections today, Connections Assistant"

    content = f"""------------------- VIDEO TITLE -------------------
{video_title}

------------------- DESCRIPTION -------------------
{description_and_comment}

----------------- PINNED COMMENT -----------------
{description_and_comment}

---------------------- TAGS ----------------------
{tags}
"""
    return content


def stage_metadata(
    root_dir: Path | None = None,
    puzzle_file: Path | None = None,
    output_file: Path | None = None,
    sync_web: bool = False,
    short_id: str | None = None,
    trap_name: str | None = None,
    deploy: bool = False,
    dry_run: bool = False,
) -> Path:
    """Main staging workflow."""
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent

    dirs = ensure_directories(root_dir)
    print(f"[+] Verified output directories at: {dirs['output']}")
    print(f"    - Frames: {dirs['frames']}")
    print(f"    - Audio:  {dirs['audio']}")

    if puzzle_file is None:
        puzzle_file = root_dir / "daily_puzzle.json"

    print(f"[+] Reading puzzle data from: {puzzle_file}...")
    puzzle_data = load_puzzle_data(puzzle_file)

    if output_file is None:
        output_file = dirs["output"] / "today_shorts_metadata.txt"

    print(f"[+] Formatting metadata for date: {puzzle_data.get('date')}...")
    metadata_text = generate_metadata_content(puzzle_data)

    print(f"[+] Writing metadata to: {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(metadata_text)

    print(f"[✓] Metadata successfully written to {output_file.name}")

    if sync_web or deploy:
        from sync_daily_web import sync_web_pipeline
        print("\n[+] Triggering daily web synchronization...")
        sync_web_pipeline(
            root_dir=root_dir,
            puzzle_path=puzzle_file,
            short_id=short_id,
            trap_name=trap_name,
            deploy=deploy,
            dry_run=dry_run,
        )

    return output_file


def main():
    parser = argparse.ArgumentParser(description="Stage YouTube Shorts metadata and synchronize web pages from daily_puzzle.json.")
    parser.add_argument(
        "--puzzle",
        default=None,
        help="Path to daily_puzzle.json (defaults to daily_puzzle.json in root)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output metadata text file",
    )
    parser.add_argument(
        "--sync-web",
        action="store_true",
        help="Synchronize multi-page announcement banners and public/breakdowns.html",
    )
    parser.add_argument(
        "--short-id",
        default=None,
        help="YouTube Short ID to embed in public/breakdowns.html (e.g. TF_eBP_eN20)",
    )
    parser.add_argument(
        "--trap-name",
        default=None,
        help="Primary decoy trap name for announcement banners",
    )
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Deploy public/ to Firebase Hosting after staging",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview web synchronization changes without saving or deploying",
    )
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    puzzle_path = Path(args.puzzle).resolve() if args.puzzle else None
    output_path = Path(args.output).resolve() if args.output else None

    try:
        stage_metadata(
            root_dir=root_dir,
            puzzle_file=puzzle_path,
            output_file=output_path,
            sync_web=args.sync_web,
            short_id=args.short_id,
            trap_name=args.trap_name,
            deploy=args.deploy,
            dry_run=args.dry_run,
        )
    except Exception as e:
        print(f"[!] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
