# -*- coding: utf-8 -*-
import asyncio
import re
from pathlib import Path
import quota_watchdog_engine as engine

async def render_offline_batch():
    topics_file = engine.BASE_DIR / "missing_slots_topics.txt"
    topics = [line.strip() for line in topics_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    
    print(f"[+] Starting offline local render for {len(topics)} missing slots (0 YouTube API Quota)...")
    
    for i, topic in enumerate(topics, 1):
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', topic.lower()).strip('-')[:40]
        prefix = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())[:30]
        output_mp4 = engine.RENDER_DIR / f"nyt-connections-hints-today-{slug}-connectionsassistant.mp4"
        thumbnail_png = engine.RENDER_DIR / f"thumb-{slug}.png"
        
        print(f"\n[{i}/{len(topics)}] Processing: {topic}")
        blueprint = engine.generate_blueprint(topic)
        
        a1 = str(engine.TEMP_DIR / f"{prefix}_a1.mp3")
        a2 = str(engine.TEMP_DIR / f"{prefix}_a2.mp3")
        a3 = str(engine.TEMP_DIR / f"{prefix}_a3.mp3")
        await engine.synthesize_speech(blueprint.scene1_narration, a1)
        await engine.synthesize_speech(blueprint.scene2_narration, a2)
        await engine.synthesize_speech(blueprint.scene3_narration, a3)
        
        durations = [engine.get_audio_duration(a1), engine.get_audio_duration(a2), engine.get_audio_duration(a3)]
        total_dur = sum(durations)
        
        frames = await engine.render_board_frames(blueprint, prefix)
        engine.assemble_short(frames, [a1, a2, a3], durations, str(output_mp4))
        
        # Save Scene 3 as dedicated thumbnail alongside MP4
        Path(frames[2]).replace(thumbnail_png)
        
        print(f"[✓] Rendered MP4: {output_mp4.name} ({total_dur:.2f}s)")
        print(f"[✓] Exported Thumbnail: {thumbnail_png.name}")

    print("\n[OK] All 5 missing slot videos and thumbnails rendered locally in rendered_videos/.")

if __name__ == "__main__":
    asyncio.run(render_offline_batch())
