import os
import json
import asyncio
import subprocess
import edge_tts

PIPELINE_DIR = r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline"
OUTPUT_DIR = os.path.join(PIPELINE_DIR, "output")
RENDER_DIR = os.path.join(PIPELINE_DIR, "rendered_videos")
os.makedirs(RENDER_DIR, exist_ok=True)

VOICE = "en-US-ChristopherNeural"

# Direct Windows Font Path - avoids Fontconfig lookup error
FONT_PATH = "C\\:/Windows/Fonts/arialbd.ttf"

async def create_voiceover(full_text: str, output_audio: str):
    communicate = edge_tts.Communicate(full_text, VOICE)
    await communicate.save(output_audio)

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

def sanitize_text(text: str) -> str:
    return text.replace("\\", "/").replace("'", "").replace(":", " -").replace("%", "").replace(",", "")

def render_short_ffmpeg(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    short_id = os.path.splitext(os.path.basename(json_path))[0]
    out_mp4 = os.path.join(RENDER_DIR, f"{short_id}.mp4")
    temp_audio = os.path.join(PIPELINE_DIR, f"{short_id}_temp.mp3")

    print(f"\n[*] Processing Short: {short_id}")
    print(f"    Title: {data.get('video_title')}")

    # 1. Synthesize audio narration
    scenes = data.get("scenes", [])
    full_narration = " ".join([s["voiceover"] for s in scenes])
    asyncio.run(create_voiceover(full_narration, temp_audio))
    
    total_duration = get_audio_duration(temp_audio) + 0.8
    print(f"    Narration ready ({total_duration:.2f}s)")

    # 2. Extract and sanitize text
    hook = sanitize_text(data.get("hook_headline", "NYT CONNECTIONS TRAP"))
    category = sanitize_text(data.get("target_category", ""))
    tier_color = data.get("tier_hex_color", "0xbe2edd").replace("#", "0x")

    overlay_1 = sanitize_text(scenes[0].get("overlay_text", "")) if len(scenes) > 0 else ""
    overlay_2 = sanitize_text(scenes[1].get("overlay_text", "")) if len(scenes) > 1 else ""

    # 3. Construct filtergraph using direct fontfile path
    filter_complex = (
        f"color=c=0x2d3436:s=1080x1920:d={total_duration}[bg];"
        f"[bg]drawtext=fontfile='{FONT_PATH}':text='{hook}':fontcolor=0xf9ca24:fontsize=50:x=(w-text_w)/2:y=240:box=1:boxcolor=0x000000@0.6:boxborderw=14,"
        f"drawtext=fontfile='{FONT_PATH}':text='{overlay_1}':fontcolor=white:fontsize=44:x=(w-text_w)/2:y=650:enable='between(t,0,10)',"
        f"drawtext=fontfile='{FONT_PATH}':text='{overlay_2}':fontcolor=white:fontsize=44:x=(w-text_w)/2:y=650:enable='gte(t,10)',"
        f"drawtext=fontfile='{FONT_PATH}':text='{category}':fontcolor={tier_color}:fontsize=48:x=(w-text_w)/2:y=1180:enable='gte(t,12)',"
        f"drawtext=fontfile='{FONT_PATH}':text='connectionsassistant.com':fontcolor=0x00cec9:fontsize=40:x=(w-text_w)/2:y=1700"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", filter_complex,
        "-i", temp_audio,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        out_mp4
    ]

    print(f"    Rendering 1080x1920 vertical canvas via FFmpeg...")
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        print(f" [OK] Export complete: {out_mp4}")
    else:
        print(f" [!] FFmpeg Error:\n{res.stderr.decode('utf-8', errors='ignore')}")

    if os.path.exists(temp_audio):
        os.remove(temp_audio)

def render_all():
    json_files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith(".json")]
    for jf in json_files:
        render_short_ffmpeg(jf)

if __name__ == "__main__":
    render_all()