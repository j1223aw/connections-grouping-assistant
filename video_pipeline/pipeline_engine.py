import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
import edge_tts
from playwright.async_api import async_playwright
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline")
OUTPUT_ROOT = BASE_DIR / "pipeline_output"
OUTPUT_ROOT.mkdir(exist_ok=True)
RENDER_DIR = BASE_DIR / "rendered_videos"
RENDER_DIR.mkdir(exist_ok=True)
TEMP_FRAME_DIR = BASE_DIR / "temp_frames"
TEMP_FRAME_DIR.mkdir(exist_ok=True)
TEMPLATE_PATH = BASE_DIR / "templates" / "board_template.html"
TOPICS_FILE = BASE_DIR / "topics.txt"
CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "token.json"

VOICE_NAME = "en-US-ChristopherNeural"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# -------------------------------------------------------------
# 1. Structured Gemini Blueprint Generation
# -------------------------------------------------------------
class Scene(BaseModel):
    scene_number: int = Field(description="1: Hook, 2: Decoy Trap Split, 3: Solve Reveal & CTA")
    voiceover: str = Field(description="Narration line for this scene")

class VideoBlueprint(BaseModel):
    video_title: str
    hook_headline: str
    target_category: str
    category_tier: str
    tier_hex_color: str
    board_words: list[str] = Field(description="Exactly 16 puzzle words")
    red_herrings_identified: list[str] = Field(description="4 decoy words")
    target_words: list[str] = Field(description="4 solution words")
    scenes: list[Scene]
    pinned_comment: str
    youtube_tags: list[str]

def generate_script(topic: str) -> VideoBlueprint:
    print(f"\n[+] Generating structured blueprint for: {topic}...")
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    prompt = f"""
    Create a high-retention 30-second NYT Connections breakdown about: "{topic}".
    Output JSON adhering strictly to VideoBlueprint.
    REQUIREMENTS:
    - Exactly 16 board words arranged as 4 distinct categories of 4 words each.
    - Exactly 4 decoy overlap words in red_herrings_identified.
    - Exactly 4 solution words in target_words for the target_category.
    - category_tier must be Yellow, Green, Blue, or Purple.
    - tier_hex_color must match tier (#f9ca24 for Yellow, #6ab04c for Green, #4b7bec for Blue, #be2edd for Purple).
    - scenes: Scene 1 introduces the board hook. Scene 2 breaks the decoy trap. Scene 3 reveals the category and gives CTA: "connectionsassistant.com".
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VideoBlueprint,
        ),
    )
    return VideoBlueprint.model_validate_json(response.text)

# -------------------------------------------------------------
# 2. Audio & Timing
# -------------------------------------------------------------
async def synthesize_neural_voice(script_text: str, output_mp3: str):
    communicate = edge_tts.Communicate(script_text, VOICE_NAME, rate="+18%")
    await communicate.save(output_mp3)

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())

# -------------------------------------------------------------
# 3. HTML Frame Generation & Playwright Capture
# -------------------------------------------------------------
def generate_board_html(hook: str, words: list[str], highlighted_words: list[str], solved_tier: str = None) -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    grid_items = ""
    for w in words:
        is_highlighted = w in highlighted_words
        style_class = "tile highlighted" if is_highlighted else "tile"
        if solved_tier and is_highlighted:
            style_class += f" solved-{solved_tier.lower()}"
        grid_items += f'<div class="{style_class}">{w}</div>'

    badge_html = f'<div class="badge {solved_tier.lower()}">{solved_tier.upper()} CATEGORY</div>' if solved_tier else ''
    html = template.replace("{{HOOK}}", hook)
    html = html.replace("{{BADGE_HTML}}", badge_html)
    html = html.replace("{{GRID_ITEMS}}", grid_items)
    return html

async def capture_frame(page, html_content: str, output_path: str):
    await page.set_content(html_content)
    await page.screenshot(path=output_path)

# -------------------------------------------------------------
# 4. YouTube Data API v3 Uploader
# -------------------------------------------------------------
def get_authenticated_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtube", "v3", credentials=creds)

def upload_and_schedule(video_path: Path, title: str, description: str, tags: list[str], publish_iso: str, thumbnail_path: Path = None):
    youtube = get_authenticated_service()
    print(f"\n[+] Preparing YouTube upload: {title}")
    print(f"[+] Scheduled release slot: {publish_iso}")
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_iso,
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(str(video_path), chunksize=1024*1024*8, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    print("[+] Uploading video stream to YouTube...")
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[+] Upload progress: {int(status.progress() * 100)}%")
    video_id = response.get("id")
    print(f"[✓] Upload successful & scheduled! Video ID: {video_id} (https://youtu.be/{video_id})")

    if thumbnail_path and thumbnail_path.exists():
        try:
            thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/png", resumable=True)
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("[✓] Custom thumbnail attached from Scene 3.")
        except Exception as e:
            print(f"[!] Warning: Could not set thumbnail: {e}")
    return video_id

# -------------------------------------------------------------
# 5. Master Execution Loop
# -------------------------------------------------------------
def slugify(text: str) -> str:
    text = text.lower()
    text = "".join(c if c.isalnum() else "_" for c in text).strip("_")
    return text[:35]

async def process_pipeline():
    if not TOPICS_FILE.exists():
        print(f"[!] {TOPICS_FILE} not found.")
        return

    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        topics = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not topics:
        print("[!] No topics found in topics.txt.")
        return

    print(f"[+] Loaded {len(topics)} topic(s) to process.")

    # Backfill missing slots for Sunday Oct 18 and Monday Oct 19 (12:30 PM and 6:00 PM EDT)
    schedule_times = [
        "2026-10-18T16:30:00Z",  # Sun Oct 18 @ 12:30 PM EDT
        "2026-10-18T22:00:00Z",  # Sun Oct 18 @ 6:00 PM EDT
        "2026-10-19T16:30:00Z",  # Mon Oct 19 @ 12:30 PM EDT
        "2026-10-19T22:00:00Z"   # Mon Oct 19 @ 6:00 PM EDT
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for idx, topic in enumerate(topics, 1):
            slug = slugify(topic)
            final_video = RENDER_DIR / f"{slug}.mp4"
            raw_audio_path = str(BASE_DIR / f"{slug}_narration.mp3")

            blueprint = generate_script(topic)
            full_narration = " ".join([s.voiceover for s in blueprint.scenes])

            # 1. Synthesize neural voiceover
            await synthesize_neural_voice(full_narration, raw_audio_path)
            audio_duration = get_audio_duration(raw_audio_path)
            print(f"[+] Audio generated. Duration: {audio_duration:.2f}s")

            # 2. Render modern board frames via Playwright
            f1_html = generate_board_html(blueprint.hook_headline, blueprint.board_words, [])
            f1_path = str(TEMP_FRAME_DIR / f"{slug}_1.png")
            await capture_frame(page, f1_html, f1_path)

            f2_html = generate_board_html("THE DECOY OVERLAP!", blueprint.board_words, blueprint.red_herrings_identified)
            f2_path = str(TEMP_FRAME_DIR / f"{slug}_2.png")
            await capture_frame(page, f2_html, f2_path)

            f3_html = generate_board_html(blueprint.target_category, blueprint.board_words, blueprint.target_words, blueprint.category_tier)
            f3_path = str(TEMP_FRAME_DIR / f"{slug}_3.png")
            await capture_frame(page, f3_html, f3_path)

            # 3. Proportional Scene Timings
            t1 = round(audio_duration * 0.20, 2)
            t2 = round(audio_duration * 0.35, 2)
            t3 = round(audio_duration - (t1 + t2), 2)

            concat_txt = BASE_DIR / "concat.txt"
            with open(concat_txt, "w") as f:
                f.write(f"file '{f1_path.replace(os.sep, '/')}'\nduration {t1}\n")
                f.write(f"file '{f2_path.replace(os.sep, '/')}'\nduration {t2}\n")
                f.write(f"file '{f3_path.replace(os.sep, '/')}'\nduration {t3}\n")
                f.write(f"file '{f3_path.replace(os.sep, '/')}'\n")

            # 4. FFmpeg Video Assembly
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_txt),
                "-i", raw_audio_path,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(final_video)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            print(f"[✓] Short successfully rendered: {final_video}")

            if os.path.exists(raw_audio_path):
                os.remove(raw_audio_path)

            # 5. YouTube Upload & Staggered Scheduling
            desc = (
                f"Solve tricky NYT Connections boards and defeat decoy overlap traps daily!\n"
                f"Analyze puzzle boards instantly at https://connectionsassistant.com/\n\n"
                f"#NYTConnections #WordPuzzle #BrainTeaser #ConnectionsHints #Shorts"
            )
            slot_iso = schedule_times[(idx - 1) % len(schedule_times)]
            upload_and_schedule(
                video_path=final_video,
                title=blueprint.video_title,
                description=desc,
                tags=blueprint.youtube_tags,
                publish_iso=slot_iso,
                thumbnail_path=Path(f3_path)
            )

        await browser.close()
    print("\n[OK] Pipeline batch processing complete!")

if __name__ == "__main__":
    asyncio.run(process_pipeline())