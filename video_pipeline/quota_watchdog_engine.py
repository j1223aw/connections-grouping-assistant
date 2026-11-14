# -*- coding: utf-8 -*-
import os
import re
import json
import asyncio
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

import edge_tts
from playwright.async_api import async_playwright

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ---------------------------------------------------------
# DIRECTORIES & HARNESS CONFIG
# ---------------------------------------------------------
BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline")
TEMPLATES_DIR = BASE_DIR / "templates"
RENDER_DIR = BASE_DIR / "rendered_videos"
RENDER_DIR.mkdir(exist_ok=True)
TEMP_DIR = BASE_DIR / "temp_frames"
TEMP_DIR.mkdir(exist_ok=True)

CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "token.json"
CATALOG_FILE = BASE_DIR / "pipeline_catalog.json"

VOICE_NAME = "en-US-ChristopherNeural"
PLAYLIST_ID = "PLrujECpbJ25iriPAQg_whVztpdpuA98Zt"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

PINNED_COMMENT_TEXT = "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html"

# TARGET DATE FOR FILLING OCT 29 SCHEDULE GAP
TARGET_DATE = "2026-11-07"
MAX_DAILY_UPLOADS = 3
QUOTA_CEILING = 5500

# ---------------------------------------------------------
# HARNESS COMPONENT: LOCAL EXPERIENCE CATALOG (0 TOKENS / 0 QUOTA)
# ---------------------------------------------------------
def load_catalog() -> Dict[str, Any]:
    if CATALOG_FILE.exists():
        try:
            return json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"videos": {}}

def save_catalog(catalog: Dict[str, Any]):
    CATALOG_FILE.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

def copy_to_clipboard(text: str):
    try:
        cmd = f"Set-Clipboard -Value \"{text}\""
        subprocess.run(["powershell", "-Command", cmd], check=True)
        print("[✓] Pinned CTA message auto-copied to Windows clipboard.")
    except Exception as e:
        print(f"[!] Clipboard notice: {e}")

# ---------------------------------------------------------
# STRUCTURED GENAI SCHEMA (SUB-25S PACING)
# ---------------------------------------------------------
class ConnectionsBlueprint(BaseModel):
    hook: str = Field(description="Max 5 words. Bold curiosity hook")
    theme: str = Field(description="Category theme name")
    tier_name: str = Field(description="Yellow, Green, Blue, or Purple")
    tier_color: str = Field(description="yellow, green, blue, or purple")
    words_16: List[str] = Field(description="16 uppercase puzzle words")
    decoy_words: List[str] = Field(description="4 false overlap decoy words")
    solution_words: List[str] = Field(description="4 solution words")
    scene1_narration: str = Field(description="Max 18 words nudge")
    scene2_narration: str = Field(description="Max 22 words decoy alert")
    scene3_narration: str = Field(description="Max 20 words reveal & CTA")

def generate_blueprint(topic: str) -> ConnectionsBlueprint:
    print(f"\n[+] Generating structured blueprint via Gemini 2.5 Flash: {topic}...")
    client = genai.Client()
    prompt = f"""Break down this NYT Connections trap: {topic}
1. Grounding: All 16 words must be valid English words.
2. The Overlap Trap: 4 decoys must share an association with 1 solution word.
3. Retention Pacing: Narration total under 60 words for sub-30 second runtime."""
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ConnectionsBlueprint,
            temperature=0.2,
        ),
    )
    return response.parsed

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip())

async def synthesize_speech(text: str, out_path: str):
    comm = edge_tts.Communicate(text, VOICE_NAME, rate="+18%")
    await comm.save(out_path)

async def render_board_frames(blueprint: ConnectionsBlueprint, prefix: str) -> List[str]:
    template_path = TEMPLATES_DIR / "board_template.html"
    raw_html = template_path.read_text(encoding="utf-8")
    tier = blueprint.tier_color.lower()
    frames = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        s1_items = "".join([f'<div class="tile">{w}</div>' for w in blueprint.words_16])
        h1 = raw_html.replace("{{HOOK}}", blueprint.hook.upper()).replace("{{BADGE_HTML}}", "").replace("{{GRID_ITEMS}}", s1_items)
        p1 = str(TEMP_DIR / f"{prefix}_scene1.png")
        await page.set_content(h1)
        await page.screenshot(path=p1)
        frames.append(p1)

        s2_tiles = [
            f'<div class="tile highlighted">{w}</div>' if w in blueprint.decoy_words else f'<div class="tile">{w}</div>'
            for w in blueprint.words_16
        ]
        h2 = raw_html.replace("{{HOOK}}", "THE DECOY OVERLAP!").replace("{{BADGE_HTML}}", '<div class="badge yellow">⚠️ OVERLAPPING TRAP</div>').replace("{{GRID_ITEMS}}", "".join(s2_tiles))
        p2 = str(TEMP_DIR / f"{prefix}_scene2.png")
        await page.set_content(h2)
        await page.screenshot(path=p2)
        frames.append(p2)

        s3_tiles = [
            f'<div class="tile solved-{tier}">{w}</div>' if w in blueprint.solution_words else f'<div class="tile">{w}</div>'
            for w in blueprint.words_16
        ]
        h3 = raw_html.replace("{{HOOK}}", blueprint.theme.upper()).replace("{{BADGE_HTML}}", f'<div class="badge {tier}">{blueprint.tier_name.upper()} TIER</div>').replace("{{GRID_ITEMS}}", "".join(s3_tiles))
        p3 = str(TEMP_DIR / f"{prefix}_scene3.png")
        await page.set_content(h3)
        await page.screenshot(path=p3)
        frames.append(p3)

        await browser.close()
    return frames

def assemble_short(frames: List[str], audios: List[str], durations: List[float], output_path: str):
    concat_audio = str(TEMP_DIR / "combined_audio.mp3")
    audio_list_txt = TEMP_DIR / "audio_list.txt"
    with open(audio_list_txt, "w") as f:
        for a in audios:
            f.write(f"file '{a.replace(os.sep, '/')}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list_txt), "-c", "copy", concat_audio
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    concat_video_txt = TEMP_DIR / "video_concat.txt"
    with open(concat_video_txt, "w") as f:
        for i in range(len(frames)):
            f.write(f"file '{frames[i].replace(os.sep, '/')}'\n")
            f.write(f"duration {durations[i]:.2f}\n")
        f.write(f"file '{frames[-1].replace(os.sep, '/')}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_video_txt),
        "-i", concat_audio,
        "-c:v", "h264_nvenc", "-preset", "p6", "-b:v", "6M", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

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

async def process_safe_queue():
    topics_file = BASE_DIR / "topics.txt"
    if not topics_file.exists():
        print("[!] topics.txt not found!")
        return

    topics = [line.strip() for line in topics_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    catalog = load_catalog()

    quota_spent = 0
    target_topics = topics[:MAX_DAILY_UPLOADS]
    print(f"[WATCHDOG] Active Window Filter: Processing {len(target_topics)} candidate(s) for target date {TARGET_DATE}.")

    # Timestamps for 8:00 AM EDT, 12:30 PM EDT, 5:00 PM EDT
    time_slots = ["T12:00:00Z", "T16:30:00Z", "T21:00:00Z"]
    schedule_times = [f"{TARGET_DATE}{slot}" for slot in time_slots]

    youtube = get_authenticated_service()

    for i, topic in enumerate(target_topics):
        if quota_spent + 1700 > QUOTA_CEILING:
            print(f"[WATCHDOG HOOK] Approaching quota ceiling ({quota_spent} used). Stopping execution.")
            break

        prefix = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())[:30]
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', topic.lower()).strip('-')[:40]
        output_mp4 = RENDER_DIR / f"nyt-connections-hints-today-{slug}-connectionsassistant.mp4"

        if slug in catalog["videos"] and catalog["videos"][slug].get("uploaded"):
            print(f"[*] State Cache: {slug} already uploaded. Skipping.")
            continue

        blueprint = generate_blueprint(topic)

        a1 = str(TEMP_DIR / f"{prefix}_a1.mp3")
        a2 = str(TEMP_DIR / f"{prefix}_a2.mp3")
        a3 = str(TEMP_DIR / f"{prefix}_a3.mp3")
        await synthesize_speech(blueprint.scene1_narration, a1)
        await synthesize_speech(blueprint.scene2_narration, a2)
        await synthesize_speech(blueprint.scene3_narration, a3)

        durations = [get_audio_duration(a1), get_audio_duration(a2), get_audio_duration(a3)]
        total_dur = sum(durations)

        frames = await render_board_frames(blueprint, prefix)
        assemble_short(frames, [a1, a2, a3], durations, str(output_mp4))
        print(f"[✓] Rendered: {output_mp4.name} ({total_dur:.2f}s)")

        release_slot = schedule_times[i % len(schedule_times)]
        clean_title = f"{topic.split(':')[0]} | NYT Connections Hints"[:100]
        description = (
            f"{topic}\n\n"
            "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html\n\n"
            "🟨 TIER 1 • EASIEST (Direct Synonyms)\n"
            "🟩 TIER 2 • MODERATE (Contextual Link)\n"
            "🟦 TIER 3 • CHALLENGING (Trivia & Patterns)\n"
            "🟪 TIER 4 • TRICKIEST (Lateral Wordplay)\n\n"
            "#NYTConnections #ConnectionsHints #WordPuzzle #Shorts"
        )

        body = {
            "snippet": {
                "title": clean_title,
                "description": description,
                "tags": ["NYT Connections hints today", "Connections hints", "word puzzle", "Shorts"],
                "categoryId": "27"
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": release_slot,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(str(output_mp4), chunksize=1024*1024*8, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        
        response = None
        while response is None:
            status, response = request.next_chunk()

        video_id = response.get("id")
        quota_spent += 1600
        print(f"[✓] Uploaded: {video_id} (Scheduled {release_slot}). Quota used: {quota_spent}")

        try:
            thumb_media = MediaFileUpload(frames[2], mimetype="image/png", resumable=True)
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            quota_spent += 50
            print(f"[✓] Thumbnail set. Quota used: {quota_spent}")
        except Exception as e:
            print(f"[!] Thumbnail notice: {e}")

        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": PLAYLIST_ID,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()
            quota_spent += 50
            print(f"[✓] Added to playlist {PLAYLIST_ID}. Quota used: {quota_spent}")
        except Exception as e:
            print(f"[!] Playlist notice: {e}")

        catalog["videos"][slug] = {
            "id": video_id,
            "title": clean_title,
            "publishAt": release_slot,
            "uploaded": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        save_catalog(catalog)

    copy_to_clipboard(PINNED_COMMENT_TEXT)
    print(f"\n[OK] Quota-safe run finished. Total API units consumed: {quota_spent} / 10,000 max.")

if __name__ == "__main__":
    asyncio.run(process_safe_queue())
