import os
import json
import asyncio
import edge_tts
from moviepy.editor import (
    TextClip,
    ColorClip,
    CompositeVideoClip,
    AudioFileClip,
    concatenate_videoclips
)

PIPELINE_DIR = r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline"
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
RENDER_DIR = os.path.join(PIPELINE_DIR, "rendered_videos")
os.makedirs(RENDER_DIR, exist_ok=True)

VOICE = "en-US-ChristopherNeural"  # Authoritative, crisp narrator voice

async def create_audio(text: str, audio_path: str):
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(audio_path)

def render_short_video(json_file_path: str):
    with open(json_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    short_id = os.path.splitext(os.path.basename(json_file_path))[0]
    final_video_path = os.path.join(RENDER_DIR, f"{short_id}.mp4")
    
    print(f"\n[*] Rendering Short: {short_id}")
    print(f"    Title: {data.get('video_title')}")

    scene_clips = []
    
    for idx, scene in enumerate(data.get("scenes", [])):
        temp_audio = os.path.join(PIPELINE_DIR, f"temp_{short_id}_{idx}.mp3")
        asyncio.run(create_audio(scene["voiceover"], temp_audio))
        
        audio_clip = AudioFileClip(temp_audio)
        duration = audio_clip.duration + 0.3  # Add small buffer
        
        # 1080x1920 Dark Background matching app theme (#2d3436)
        bg = ColorClip(size=(1080, 1920), color=(45, 52, 54), duration=duration)
        
        # Dynamic Top Headline / Hook Banner
        hook_banner = TextClip(
            data.get("hook_headline", "NYT CONNECTIONS TRAP"),
            fontsize=52,
            color='yellow',
            font='Arial-Bold',
            size=(960, None),
            method='caption'
        ).set_position(('center', 180)).set_duration(duration)

        # Main Scene Text Overlay
        overlay = TextClip(
            scene["overlay_text"],
            fontsize=46,
            color='white',
            font='Arial-Bold',
            size=(900, None),
            method='caption'
        ).set_position(('center', 'center')).set_duration(duration)

        # Brand Footer Callout
        brand_footer = TextClip(
            "connectionsassistant.com",
            fontsize=38,
            color='#00cec9',
            font='Arial-Bold'
        ).set_position(('center', 1700)).set_duration(duration)

        scene_composite = CompositeVideoClip([bg, hook_banner, overlay, brand_footer]).set_audio(audio_clip)
        scene_clips.append(scene_composite)

    final_clip = concatenate_videoclips(scene_clips, method="compose")
    final_clip.write_videofile(
        final_video_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )
    
    # Cleanup temp audio
    for idx in range(len(data.get("scenes", []))):
        temp_audio = os.path.join(PIPELINE_DIR, f"temp_{short_id}_{idx}.mp3")
        if os.path.exists(temp_audio):
            os.remove(temp_audio)

    print(f" [OK] Export complete: {final_video_path}")

def render_all():
    json_files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    for jf in json_files:
        render_short_video(jf)

if __name__ == "__main__":
    render_all()