"""
render_daily_pipeline.py

Unified Midnight Drop Orchestrator for Connections Assistant.
Executes the full automated 2-video drop architecture at 12:01 AM EST:
1. Ingestion: Fetches official NYT Connections daily puzzle (fetch_daily_puzzle.py).
2. Reddit Dispatch: Formats progressive nudges & copies spoiler comment to clipboard (reddit_daily_nudge.py).
3. Drop 1 Render: Teaser & Trap Short (today_connections_hints.mp4) via generate_shorts.py.
4. Drop 2 Render: Full Ordered Walkthrough Short (today_connections_full_solution.mp4) via generate_full_solution_short.py.
5. Multi-Page Web Sync: Updates announcement banners and public/breakdowns.html (sync_daily_web.py).
6. Optional Deployment: Pushes to Firebase Hosting (--deploy).
"""

import argparse
import asyncio
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_SHORTS_DIR = ROOT_DIR / "output_shorts"
PUZZLE_FILE = ROOT_DIR / "daily_puzzle.json"


def log_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def step_fetch_puzzle(target_date: str | None = None) -> Path:
    log_banner("Step 1: Ingesting Daily Puzzle")
    from fetch_daily_puzzle import fetch_and_save_daily_puzzle, get_current_ny_date
    date_to_fetch = target_date or get_current_ny_date()
    puzzle_path = fetch_and_save_daily_puzzle(date_to_fetch, PUZZLE_FILE)
    print(f"[✓] Daily puzzle ingested for {date_to_fetch} -> {puzzle_path.name}")
    return puzzle_path


def step_reddit_nudge(puzzle_path: Path):
    log_banner("Step 2: Generating Reddit Dispatch & Clipboard Nudge")
    from reddit_daily_nudge import generate_nudge_comment, copy_to_clipboard_clean
    comment = generate_nudge_comment(str(puzzle_path))
    comment_file = ROOT_DIR / "today_reddit_comment.txt"
    comment_file.write_text(comment, encoding="utf-8")
    copy_to_clipboard_clean(comment)
    print(f"[✓] Reddit comment staged to {comment_file.name} & copied to clipboard.")


async def step_render_drop_1(puzzle_path: Path) -> Path:
    log_banner("Step 3: Rendering Drop 1 — Teaser & Decoy Short (Sub-30s)")
    from generate_shorts import generate_daily_short
    short_path = await generate_daily_short(puzzle_path)
    print(f"[✓] Drop 1 successfully rendered: {short_path.name}")
    return short_path


async def step_render_drop_2(puzzle_path: Path) -> Path:
    log_banner("Step 4: Rendering Drop 2 — Full Board Ordered Walkthrough (35-45s)")
    from generate_full_solution_short import generate_full_solution_pipeline
    sol_path, meta_path = await generate_full_solution_pipeline(puzzle_path)
    print(f"[✓] Drop 2 successfully rendered: {sol_path.name}")
    return sol_path


async def step_render_drop_3() -> Path:
    log_banner("Step 5: Rendering Drop 3 — 16:9 Long-Form Deep Dive Masterclass")
    import generate_daily_deep_dive
    await generate_daily_deep_dive.main()
    from generate_masterclass_thumbnail import generate_thumbnail
    await generate_thumbnail()
    master_path = ROOT_DIR / "output_masterclass" / "today_deep_dive_masterclass.mp4"
    print(f"[✓] Drop 3 successfully rendered: {master_path.name}")
    return master_path


def step_stage_manual_upload(puzzle_path: Path):
    log_banner("Step 5: Staging Manual Upload Metadata & Verification Package")
    data = {}
    if puzzle_path.exists():
        with open(puzzle_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    pdate = data.get("date", "Today")
    pid = data.get("id", "")

    # Drop 1: Hints Short
    drop1_title = f"Stuck on Today's NYT Connections? Gentle Hints & Trap Alert ({pdate}) #shorts #nytconnections"
    drop1_desc = (
        f"Morning walkthrough and hints for today's NYT Connections puzzle (#{pid} - {pdate}).\n\n"
        "🧩 Practice today's 16 words risk-free (Zero Spoilers — Copy, Paste, or 1-Click Fill) without burning your 4 guesses:\n"
        "https://connectionsassistant.com/\n\n"
        "THE 4 COLOR TIERS:\n"
        "🟨 TIER 1 • EASIEST (Direct Synonyms) — Words that share the same meaning\n"
        "🟩 TIER 2 • MODERATE (Contextual Link) — Connected by a common theme or subject\n"
        "🟦 TIER 3 • CHALLENGING (Trivia & Patterns) — Specialized trivia or shared word patterns\n"
        "🟪 TIER 4 • TRICKIEST (Lateral Wordplay) — Clever wordplay or spelling tricks\n\n"
        "#NYTConnections #WordPuzzle #BrainTeaser #ConnectionsHints #Shorts #KeepSharp #SeniorGames"
    )
    drop1_comment = (
        "🧩 Practice today's 16 words risk-free (Zero Spoilers) without burning your 4 NYT guesses! "
        "Link in channel bio (connectionsassistant.com) or tap the Related Video above for the full breakdown."
    )
    drop1_tags = "NYT Connections, Connections hints, NYT Connections today, Connections Assistant, spoiler-free practice board, gentle hints, connections hints without spoilers, brain health, word puzzle"
    drop1_thumb = OUTPUT_SHORTS_DIR / "frames" / "scene_3.png"
    drop1_video = OUTPUT_SHORTS_DIR / "today_connections_hints.mp4"

    meta1_file = OUTPUT_SHORTS_DIR / "today_shorts_metadata.txt"
    meta1_content = f"""======================================================================
DROP 1 (HINTS & TRAP SHORT) — MANUAL UPLOAD METADATA
======================================================================
VIDEO FILE:     {drop1_video}
THUMBNAIL FILE: {drop1_thumb}

------------------- VIDEO TITLE -------------------
{drop1_title}

------------------- DESCRIPTION -------------------
{drop1_desc}

----------------- PINNED COMMENT -----------------
{drop1_comment}

---------------------- TAGS ----------------------
{drop1_tags}
"""
    meta1_file.write_text(meta1_content, encoding="utf-8")

    # Drop 2: Full Solution Short
    cats_by_level = {c.get("level", 0): c for c in data.get("categories", [])}
    y_title = cats_by_level.get(0, {}).get("title", "Yellow").title()
    g_title = cats_by_level.get(1, {}).get("title", "Green").title()
    b_title = cats_by_level.get(2, {}).get("title", "Blue").title()
    p_title = cats_by_level.get(3, {}).get("title", "Purple").title()

    drop2_title = f"NYT Connections Solution Today ({pdate}) | Step-by-Step Walkthrough #shorts #nytconnections"
    drop2_desc = (
        f"Step-by-step solution for today's NYT Connections puzzle (#{pid} - {pdate}):\n\n"
        f"🟨 TIER 1 • EASIEST (Direct Synonyms): {y_title}\n"
        f"   → Words that share the same direct meaning\n\n"
        f"🟩 TIER 2 • MODERATE (Contextual Link): {g_title}\n"
        f"   → Connected by a common theme or subject\n\n"
        f"🟦 TIER 3 • CHALLENGING (Trivia & Patterns): {b_title}\n"
        f"   → Specialized trivia or shared word patterns\n\n"
        f"🟪 TIER 4 • TRICKIEST (Lateral Wordplay): {p_title}\n"
        f"   → Clever wordplay or spelling tricks\n\n"
        "🧩 Practice today's 16 words risk-free (Zero Spoilers) on our Copy/Paste Scratchboard:\n"
        "https://connectionsassistant.com/\n\n"
        "☕ Full word meanings, origins, and daily decoy breakdowns:\n"
        "https://connectionsassistant.com/breakdowns.html\n\n"
        "#NYTConnections #ConnectionsSolution #WordPuzzle #BrainTeaser #Shorts #KeepSharp #WordGames"
    )
    drop2_comment = "🧩 Practice today's 16 words risk-free (Zero Spoilers) via our channel bio (connectionsassistant.com), or tap the Related Video for full word meanings & origins!"
    drop2_tags = "NYT Connections, Connections solution today, Connections full walkthrough, NYT Connections answers, Connections hints, Connections Assistant, Connections practice board, brain games"
    drop2_thumb = OUTPUT_SHORTS_DIR / "solution_frames" / "frame_4b_purple_solved.png"
    drop2_video = OUTPUT_SHORTS_DIR / "today_connections_full_solution.mp4"

    meta2_file = OUTPUT_SHORTS_DIR / "today_full_solution_metadata.txt"
    meta2_content = f"""======================================================================
DROP 2 (FULL BOARD ORDERED WALKTHROUGH) — MANUAL UPLOAD METADATA
======================================================================
VIDEO FILE:     {drop2_video}
THUMBNAIL FILE: {drop2_thumb}

------------------- VIDEO TITLE -------------------
{drop2_title}

------------------- DESCRIPTION -------------------
{drop2_desc}

----------------- PINNED COMMENT -----------------
{drop2_comment}

---------------------- TAGS ----------------------
{drop2_tags}
"""
    meta2_file.write_text(meta2_content, encoding="utf-8")

    # Drop 3: Masterclass Metadata
    try:
        from generate_daily_deep_dive import write_video_metadata
        write_video_metadata(puzzle_path)
    except Exception as e:
        print(f"[!] Warning staging Masterclass metadata: {e}")

    # Combined Guide
    guide_file = OUTPUT_SHORTS_DIR / "MANUAL_UPLOAD_GUIDE.txt"
    guide_content = f"""======================================================================
CONNECTIONS ASSISTANT — DAILY YOUTUBE SHORTS MANUAL UPLOAD GUIDE
Puzzle Date: {pdate} | Puzzle #{pid}
======================================================================

>>> DROP 1: TEASER & DECOY TRAP SHORT
- Video File:      {drop1_video}
- Thumbnail File:  {drop1_thumb}
- Title:           {drop1_title}
- Description:
{drop1_desc}
- Pinned Comment:  {drop1_comment}
- Tags:            {drop1_tags}

----------------------------------------------------------------------
>>> DROP 2: FULL BOARD ORDERED WALKTHROUGH SHORT
- Video File:      {drop2_video}
- Thumbnail File:  {drop2_thumb}
- Title:           {drop2_title}
- Description:
{drop2_desc}
- Pinned Comment:  {drop2_comment}
- Tags:            {drop2_tags}

----------------------------------------------------------------------
>>> DROP 3: 16:9 LONG-FORM DEEP DIVE MASTERCLASS
- Video File:      {ROOT_DIR / "output_masterclass" / "today_deep_dive_masterclass.mp4"}
- Thumbnail File:  {ROOT_DIR / "output_masterclass" / "today_deep_dive_thumbnail.png"}
- Metadata File:   {ROOT_DIR / "output_masterclass" / "today_deep_dive_metadata.txt"}
- Title:           NYT Connections Explained Today ({pdate}) | Full Solution, Word Meanings & Clues

----------------------------------------------------------------------
>>> POST-UPLOAD WEBSITE UPDATE (1 STEP):
After uploading Drop 1, grab its YouTube Video ID or URL (e.g. TF_eBP_eN20) and run:
  python sync_daily_web.py --short-id <VIDEO_ID> --deploy

This instantly swaps the live embed on breakdowns.html and pushes to production!
======================================================================
"""
    guide_file.write_text(guide_content, encoding="utf-8")
    print(f"[✓] Staged Drop 1 metadata -> {meta1_file.name}")
    print(f"[✓] Staged Drop 2 metadata -> {meta2_file.name}")
    print(f"[✓] Staged comprehensive upload guide -> {guide_file.name}")


def step_upload_drops():
    log_banner("Optional: Uploading Shorts to YouTube Channel via API")
    from upload_today_short import get_service, upload_drop_1, upload_drop_2
    youtube = get_service()
    print("\n--- UPLOADING DROP 1 (HINTS SHORT) ---")
    id1 = upload_drop_1(youtube)
    print(f"[✓] Drop 1 Live on YouTube: https://youtube.com/shorts/{id1}")

    print("\n--- UPLOADING DROP 2 (FULL WALKTHROUGH SHORT) ---")
    id2 = upload_drop_2(youtube)
    print(f"[✓] Drop 2 Live on YouTube: https://youtube.com/shorts/{id2}")
    return id1, id2


def step_family_challenge(puzzle_path: Path):
    log_banner("Step 6: Generating Family Morning Challenge Post & HD Board")
    cmd = [sys.executable, str(ROOT_DIR / "render_family_board.py")]
    subprocess.run(cmd, check=True)
    img_path = ROOT_DIR / "todays_family_board.png"
    post_path = ROOT_DIR / "todays_family_post.txt"
    print(f"[✓] Family board rendered: {img_path.name}")
    print(f"[✓] Family challenge text staged: {post_path.name}")


def step_sync_web(deploy: bool = False, dry_run: bool = False, short_id: str | None = None):
    log_banner("Step 7: Synchronizing Sitewide Announcement Banners & breakdowns.html")
    from sync_daily_web import sync_web_pipeline
    sync_web_pipeline(
        root_dir=ROOT_DIR,
        puzzle_path=PUZZLE_FILE,
        short_id=short_id,
        deploy=deploy,
        dry_run=dry_run,
    )


async def run_pipeline(
    target_date: str | None = None,
    deploy: bool = False,
    upload: bool = False,
    short_id: str | None = None,
    skip_renders: bool = False,
):
    start_time = time.time()
    log_banner("Connections Assistant — 2-Video Midnight Drop Pipeline Initiated")

    # 1. Fetch Puzzle
    puzzle_path = step_fetch_puzzle(target_date)

    # 2. Reddit Dispatch
    try:
        step_reddit_nudge(puzzle_path)
    except Exception as e:
        print(f"[!] Reddit nudge warning: {e}")

    if not skip_renders:
        # 3. Render Drop 1 (Hints & Trap Short)
        await step_render_drop_1(puzzle_path)

        # 4. Render Drop 2 (Full Ordered Walkthrough Short)
        await step_render_drop_2(puzzle_path)

        # 5. Render Drop 3 (16:9 Long-Form Deep Dive Masterclass)
        await step_render_drop_3()
    else:
        print("[~] Skipping video rendering as requested (--skip-renders).")

    # 5. Manual Upload Staging
    step_stage_manual_upload(puzzle_path)

    # 6. Family Morning Challenge Post & Board Screenshot
    step_family_challenge(puzzle_path)

    # Optional: Automated API Upload (off by default)
    if upload:
        try:
            step_upload_drops()
        except Exception as e:
            print(f"[!] YouTube API upload warning: {e}")

    # 7. Sync Web Pages & Deploy Hosting
    step_sync_web(deploy=deploy, short_id=short_id)

    elapsed = time.time() - start_time
    log_banner("Pipeline Run Complete")
    print(f"Total Pipeline Runtime: {elapsed:.2f}s")
    print(f"Drop 1: {OUTPUT_SHORTS_DIR / 'today_connections_hints.mp4'}")
    print(f"Drop 2: {OUTPUT_SHORTS_DIR / 'today_connections_full_solution.mp4'}")
    print(f"Drop 3: {ROOT_DIR / 'output_masterclass' / 'today_deep_dive_masterclass.mp4'}")
    print(f"Guide:  {OUTPUT_SHORTS_DIR / 'MANUAL_UPLOAD_GUIDE.txt'}")
    print(f"Family: {ROOT_DIR / 'todays_family_board.png'} & {ROOT_DIR / 'todays_family_post.txt'}")


def main():
    parser = argparse.ArgumentParser(description="Run Connections Assistant 2-Video Midnight Drop Pipeline.")
    parser.add_argument("--date", default=None, help="Target puzzle date (YYYY-MM-DD)")
    parser.add_argument("--deploy", action="store_true", help="Deploy public/ to Firebase Hosting after staging")
    parser.add_argument("--short-id", default=None, help="YouTube Short ID to embed in breakdowns.html (e.g. TF_eBP_eN20)")
    parser.add_argument("--upload", action="store_true", help="Upload Drop 1 & Drop 2 via YouTube API (default: False, manual upload)")
    parser.add_argument("--skip-renders", action="store_true", help="Skip video re-rendering (useful for metadata/web sync)")
    args = parser.parse_args()

    asyncio.run(run_pipeline(
        target_date=args.date,
        deploy=args.deploy,
        upload=args.upload,
        short_id=args.short_id,
        skip_renders=args.skip_renders,
    ))


if __name__ == "__main__":
    main()
