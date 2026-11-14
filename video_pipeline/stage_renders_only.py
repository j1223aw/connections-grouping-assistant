import asyncio
import re
import shutil
from pathlib import Path

from quota_watchdog_engine import (
    BASE_DIR,
    TEMP_DIR,
    generate_blueprint,
    synthesize_speech,
    get_audio_duration,
    render_board_frames,
    assemble_short,
)

TARGET_DATE = "2026-11-08"
STAGING_DIR = BASE_DIR / "staged_for_manual_upload" / TARGET_DATE

async def stage_manual_renders():
    topics_file = BASE_DIR / "topics.txt"
    if not topics_file.exists():
        print("[!] topics.txt not found!")
        return

    topics = [line.strip() for line in topics_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not topics:
        print("[!] No topics found in topics.txt")
        return

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    slots = [
        ("08:00 AM EDT", "12:00:00Z"),
        ("12:30 PM EDT", "16:30:00Z"),
        ("05:00 PM EDT", "21:00:00Z"),
    ]
    pinned_cta = "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html"

    print("=" * 65)
    print(f" AUTONOMOUS ZERO-API STAGING ENGINE: {TARGET_DATE}")
    print(f" Output Directory: {STAGING_DIR.resolve()}")
    print("=" * 65)

    for i, topic in enumerate(topics[:3]):
        slot_label, slot_utc = slots[i] if i < len(slots) else (f"Slot {i+1}", "")
        print(f"\n[+] Staging Video {i+1}/3: {topic} ({slot_label})")

        prefix = re.sub(r"[^a-zA-Z0-9]", "_", topic.lower())[:30]
        slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.lower()).strip("-")[:40]
        output_mp4 = str(STAGING_DIR / f"video_{i+1}_nyt-connections-hints-{slug}.mp4")

        # 1. Structured Blueprint via Gemini 2.5 Flash
        blueprint = generate_blueprint(topic)

        # 2. Synthesize 3-scene speech audio
        a1 = str(TEMP_DIR / f"{prefix}_a1.mp3")
        a2 = str(TEMP_DIR / f"{prefix}_a2.mp3")
        a3 = str(TEMP_DIR / f"{prefix}_a3.mp3")

        await synthesize_speech(blueprint.scene1_narration, a1)
        await synthesize_speech(blueprint.scene2_narration, a2)
        await synthesize_speech(blueprint.scene3_narration, a3)

        durations = [get_audio_duration(a1), get_audio_duration(a2), get_audio_duration(a3)]
        total_dur = sum(durations)
        print(f"    [+] Synthesized audio: {total_dur:.2f}s across 3 scenes")

        # 3. Render HTML frames via Playwright
        frames = await render_board_frames(blueprint, prefix)

        # 4. Assemble video with NVENC
        assemble_short(frames, [a1, a2, a3], durations, output_mp4)

        # 5. Extract Scene 3 frame for custom thumbnail
        thumb_file = STAGING_DIR / f"video_{i+1}_thumbnail_{slug}.png"
        if len(frames) >= 3 and Path(frames[2]).exists():
            shutil.copyfile(frames[2], thumb_file)

        # 6. Save copy-paste metadata manifest
        title_topic = topic.split(":")[0].strip()
        manifest_path = STAGING_DIR / f"video_{i+1}_metadata_{slug}.txt"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(f"SCHEDULE TIME:   {TARGET_DATE} at {slot_label} (UTC: {slot_utc})\n")
            f.write(f"VIDEO FILE:      {Path(output_mp4).name}\n")
            f.write(f"THUMBNAIL:       {thumb_file.name}\n\n")
            f.write("------------------- TITLE (Copy-Paste) -------------------\n")
            f.write(f"{title_topic} | NYT Connections Hints\n\n")
            f.write("---------------- DESCRIPTION (Copy-Paste) ----------------\n")
            f.write(f"{topic}\n\n")
            f.write(f"{pinned_cta}\n\n")
            f.write("#NYTConnections #Connections #WordPuzzle #BrainTeaser #ConnectionsShorts\n\n")
            f.write("-------------- PINNED COMMENT (Copy-Paste) ---------------\n")
            f.write(f"{pinned_cta}\n\n")
            f.write("---------------- RELATED VIDEO & PLAYLIST ----------------\n")
            f.write("RELATED VIDEO ID: iuaLTp3Pj7E\n")
            f.write("PLAYLIST NAME:    NYT Connections Hints & Strategies\n")

        print(f"    [✓] Video Rendered: {Path(output_mp4).name}")
        print(f"    [✓] Thumbnail:      {thumb_file.name}")
        print(f"    [✓] Manifest:       {manifest_path.name}")

    # Cleanup temp scratch files
    for item in TEMP_DIR.glob(f"*.mp3"):
        item.unlink(missing_ok=True)
    for item in TEMP_DIR.glob(f"*.png"):
        item.unlink(missing_ok=True)
    if (BASE_DIR / "concat.txt").exists():
        (BASE_DIR / "concat.txt").unlink(missing_ok=True)

    print("\n" + "=" * 65)
    print(f"[✓] All 3 videos staged successfully with 0 YouTube API units used!")
    print(f"[✓] Inspect files at: {STAGING_DIR.resolve()}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(stage_manual_renders())
