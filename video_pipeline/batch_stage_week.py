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

SCHEDULE = {
    "2026-11-09": [
        "The BAT Trap: Baseball Bats vs Nocturnal Mammals",
        "The POUND Trap: Imperial Weights vs Enclosed Shelters",
        "The CURRENT Trap: Ocean Flows vs Electrical Circuits"
    ],
    "2026-11-10": [
        "The BARK Trap: Tree Exteriors vs Canine Sounds",
        "The SEAL Trap: Marine Mammals vs Official Stamps",
        "The TIRE Trap: Rubber Wheels vs Growing Fatigued"
    ],
    "2026-11-11": [
        "The CHIP Trap: Snack Crisps vs Microprocessor Units",
        "The DATE Trap: Calendar Days vs Sweet Palm Fruits",
        "The FAN Trap: Cooling Blades vs Devoted Supporters"
    ],
    "2026-11-12": [
        "The MATCH Trap: Fire Starters vs Equal Counterparts",
        "The NET Trap: Mesh Enclosures vs Final Accounting Profits",
        "The RING Trap: Circular Jewelry vs Resonating Sounds"
    ],
    "2026-11-13": [
        "The SPRING Trap: Coiled Metals vs Flowing Water Sources",
        "The BOW Trap: Weapon Launchers vs Fronts of Ships",
        "The JAM Trap: Fruit Spreads vs Traffic Congestions"
    ],
    "2026-11-14": [
        "The WAVE Trap: Ocean Swells vs Hand Greetings",
        "The PITCH Trap: Baseball Throws vs Tar Resin Liquids",
        "The NAIL Trap: Metal Fasteners vs Finger Tips"
    ],
    "2026-11-15": [
        "The SPELL Trap: Magical Charms vs Periods of Time",
        "The YARD Trap: Grassy Lawns vs Unit Measurements",
        "The SCALE Trap: Weighing Devices vs Climbing Hurdles"
    ]
}

STAGING_BASE = BASE_DIR / "staged_for_manual_upload"

async def stage_entire_week():
    STAGING_BASE.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    slots = [
        ("08:00 AM EDT", "12:00:00Z"),
        ("12:30 PM EDT", "16:30:00Z"),
        ("05:00 PM EDT", "21:00:00Z"),
    ]
    pinned_cta = "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html"

    print("=" * 70)
    print("  AUTONOMOUS MULTI-DAY STAGING ENGINE (NOV 9 - NOV 15, 2026)")
    print(f"  Target Root: {STAGING_BASE.resolve()}")
    print("=" * 70)

    for target_date, topics in SCHEDULE.items():
        day_dir = STAGING_BASE / target_date
        day_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n>>> PROCESSING DATE: {target_date} ({len(topics)} videos)")

        for i, topic in enumerate(topics):
            slot_label, slot_utc = slots[i] if i < len(slots) else (f"Slot {i+1}", "")
            prefix = re.sub(r"[^a-zA-Z0-9]", "_", topic.lower())[:30]
            slug = re.sub(r"[^a-zA-Z0-9]+", "-", topic.lower()).strip("-")[:40]
            output_mp4 = str(day_dir / f"video_{i+1}_nyt-connections-hints-{slug}.mp4")

            if Path(output_mp4).exists():
                print(f"    [*] Already generated: {Path(output_mp4).name} (skipping)")
                continue

            print(f"    [+] Generating {i+1}/3: {topic} ({slot_label})")

            # 1. Blueprint via Gemini 2.5 Flash
            blueprint = generate_blueprint(topic)

            # 2. Synthesize Audio
            a1 = str(TEMP_DIR / f"{prefix}_a1.mp3")
            a2 = str(TEMP_DIR / f"{prefix}_a2.mp3")
            a3 = str(TEMP_DIR / f"{prefix}_a3.mp3")

            await synthesize_speech(blueprint.scene1_narration, a1)
            await synthesize_speech(blueprint.scene2_narration, a2)
            await synthesize_speech(blueprint.scene3_narration, a3)

            durations = [get_audio_duration(a1), get_audio_duration(a2), get_audio_duration(a3)]

            # 3. Render HTML frames
            frames = await render_board_frames(blueprint, prefix)

            # 4. NVENC Assembly
            assemble_short(frames, [a1, a2, a3], durations, output_mp4)

            # 5. Scene 3 thumbnail
            thumb_file = day_dir / f"video_{i+1}_thumbnail_{slug}.png"
            if len(frames) >= 3 and Path(frames[2]).exists():
                shutil.copyfile(frames[2], thumb_file)

            # 6. Metadata Manifest
            title_topic = topic.split(":")[0].strip()
            manifest_path = day_dir / f"video_{i+1}_metadata_{slug}.txt"
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(f"SCHEDULE TIME:   {target_date} at {slot_label} (UTC: {slot_utc})\n")
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

            print(f"        [✓] Rendered: {Path(output_mp4).name}")

    # Final cleanup
    for item in TEMP_DIR.glob("*.mp3"):
        item.unlink(missing_ok=True)
    for item in TEMP_DIR.glob("*.png"):
        item.unlink(missing_ok=True)
    if (BASE_DIR / "concat.txt").exists():
        (BASE_DIR / "concat.txt").unlink(missing_ok=True)

    print("\n" + "=" * 70)
    print(f"[✓] Full 7-day batch finished! Zero API units used.")
    print(f"[✓] Check output: {STAGING_BASE.resolve()}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(stage_entire_week())
