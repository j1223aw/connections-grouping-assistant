import os
import re
import json
import asyncio
import subprocess
from pathlib import Path
from typing import List

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

# Base directories
BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline")
TEMPLATES_DIR = BASE_DIR / "templates"
RENDER_DIR = BASE_DIR / "rendered_videos"
RENDER_DIR.mkdir(exist_ok=True)
TEMP_DIR = BASE_DIR / "temp_frames"
TEMP_DIR.mkdir(exist_ok=True)

CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "token.json"
VOICE_NAME = "en-US-ChristopherNeural"
PLAYLIST_NAME = "NYT Connections Hints & Strategies"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# Pydantic Structured Blueprint
class ConnectionsBlueprint(BaseModel):
    hook: str = Field(description="Max 5 words. High curiosity hook for header.")
    theme: str = Field(description="Category name (e.g. Parts of a Shoe).")
    tier_name: str = Field(description="Yellow, Green, Blue, or Purple")
    tier_color: str = Field(description="yellow, green, blue, or purple")
    words_16: List[str] = Field(description="Exact 16 puzzle words in uppercase.")
    decoy_words: List[str] = Field(description="Exact 4 words that create the false 5-word overlap trap.")
    solution_words: List[str] = Field(description="Exact 4 words that solve the category.")
    scene1_narration: str = Field(description="Stage 1: Fast nudge. Max 18 words.")
    scene2_narration: str = Field(description="Stage 2: Highlight decoy candidate trap. Max 22 words.")
    scene3_narration: str = Field(description="Stage 3: Reveal solution and CTA. Max 20 words.")

def generate_blueprint(topic: str) -> ConnectionsBlueprint:
    print(f"\n[+] Generating structured blueprint for: {topic}...")
    client = genai.Client()
    
    prompt = f"""You are the master puzzle designer for Connections Assistant.
Break down this puzzle trap: {topic}

Enforce Karpathy LLM reasoning principles:
1. Grounding: All 16 words must be valid English words. The solution must contain exactly 4 words.
2. The Overlap Trap: The 4 decoy words must share a plausible semantic link with one of the solution words.
3. Rapid Pacing: Total narration across all 3 scenes must be under 60 words for a sub-30 second runtime."""

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

        # Scene 1: Initial Grid
        s1_items = "".join([f'<div class="tile">{w}</div>' for w in blueprint.words_16])
        h1 = raw_html.replace("{{HOOK}}", blueprint.hook.upper())
        h1 = h1.replace("{{BADGE_HTML}}", "")
        h1 = h1.replace("{{GRID_ITEMS}}", s1_items)
        p1 = str(TEMP_DIR / f"{prefix}_scene1.png")
        await page.set_content(h1)
        await page.screenshot(path=p1)
        frames.append(p1)

        # Scene 2: Decoy Trap Highlighted
        s2_tiles = []
        for w in blueprint.words_16:
            if w in blueprint.decoy_words:
                s2_tiles.append(f'<div class="tile highlighted">{w}</div>')
            else:
                s2_tiles.append(f'<div class="tile">{w}</div>')
        h2 = raw_html.replace("{{HOOK}}", "THE DECOY OVERLAP!")
        h2 = h2.replace("{{BADGE_HTML}}", '<div class="badge yellow">⚠️ OVERLAPPING TRAP</div>')
        h2 = h2.replace("{{GRID_ITEMS}}", "".join(s2_tiles))
        p2 = str(TEMP_DIR / f"{prefix}_scene2.png")
        await page.set_content(h2)
        await page.screenshot(path=p2)
        frames.append(p2)

        # Scene 3: Solution Solved Tier
        s3_tiles = []
        for w in blueprint.words_16:
            if w in blueprint.solution_words:
                s3_tiles.append(f'<div class="tile solved-{tier}">{w}</div>')
            else:
                s3_tiles.append(f'<div class="tile">{w}</div>')
        h3 = raw_html.replace("{{HOOK}}", blueprint.theme.upper())
        badge_cls = f"badge {tier}"
        h3 = h3.replace("{{BADGE_HTML}}", f'<div class="{badge_cls}">{blueprint.tier_name.upper()} TIER</div>')
        h3 = h3.replace("{{GRID_ITEMS}}", "".join(s3_tiles))
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

def add_to_playlist(youtube, video_id: str, playlist_name_keyword: str = "NYT Connections Hints"):
    try:
        playlists = youtube.playlists().list(mine=True, part="snippet", maxResults=25).execute()
        target_id = next((pl["id"] for pl in playlists.get("items", []) if playlist_name_keyword.lower() in pl["snippet"]["title"].lower()), None)
        if target_id:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": target_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id}
                    }
                }
            ).execute()
            print(f"[✓] Added {video_id} to playlist: {playlist_name_keyword}")
    except Exception as e:
        print(f"[!] Playlist sync note: {e}")

async def process_batch():
    topics_file = BASE_DIR / "topics.txt"
    if not topics_file.exists():
        print("[!] topics.txt not found!")
        return

    topics = [line.strip() for line in topics_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"[+] Loaded {len(topics)} topic(s) to process.")

    # Target release schedule: Friday, October 30 (8:00 AM, 12:30 PM, 6:00 PM EDT)
    schedule_times = [
        "2026-10-30T12:00:00Z",  # Fri Oct 30 @ 8:00 AM EDT
        "2026-10-30T16:30:00Z",  # Fri Oct 30 @ 12:30 PM EDT
        "2026-10-30T22:00:00Z"   # Fri Oct 30 @ 6:00 PM EDT
    ]

    youtube = get_authenticated_service()

    for i, topic in enumerate(topics):
        prefix = re.sub(r'[^a-zA-Z0-9]', '_', topic.lower())[:30]
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', topic.lower()).strip('-')[:40]
        output_mp4 = RENDER_DIR / f"nyt-connections-hints-today-{slug}-connectionsassistant.mp4"

        blueprint = generate_blueprint(topic)

        a1 = str(TEMP_DIR / f"{prefix}_a1.mp3")
        a2 = str(TEMP_DIR / f"{prefix}_a2.mp3")
        a3 = str(TEMP_DIR / f"{prefix}_a3.mp3")

        await synthesize_speech(blueprint.scene1_narration, a1)
        await synthesize_speech(blueprint.scene2_narration, a2)
        await synthesize_speech(blueprint.scene3_narration, a3)

        durations = [get_audio_duration(a1), get_audio_duration(a2), get_audio_duration(a3)]
        total_dur = sum(durations)
        print(f"[+] Audio generated. Duration: {total_dur:.2f}s")

        frames = await render_board_frames(blueprint, prefix)
        assemble_short(frames, [a1, a2, a3], durations, str(output_mp4))
        print(f"[✓] Short successfully rendered: {output_mp4.name}")

        release_slot = schedule_times[i % len(schedule_times)]
        clean_title = f"{topic.split(':')[0]} | NYT Connections Hints"[:100]

        description = (
            f"{topic}\n\n"
            "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/\n\n"
            "🟨 TIER 1 • EASIEST (Direct Synonyms)\n"
            "🟩 TIER 2 • MODERATE (Contextual Link)\n"
            "🟦 TIER 3 • CHALLENGING (Trivia & Patterns)\n"
            "🟪 TIER 4 • TRICKIEST (Lateral Wordplay)\n\n"
            "#NYTConnections #ConnectionsHints #WordPuzzle #BrainTeaser #Shorts"
        )

        print(f"\n[+] Uploading: {clean_title}")
        print(f"[+] Scheduled for: {release_slot}")

        body = {
            "snippet": {
                "title": clean_title,
                "description": description,
                "tags": ["NYT Connections hints today", "Connections hints", "NYT Connections", "word puzzle", "Shorts"],
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
        print(f"[✓] Scheduled! Video ID: {video_id} (https://youtu.be/{video_id})")

        thumb_path = frames[2]
        try:
            thumb_media = MediaFileUpload(thumb_path, mimetype="image/png", resumable=True)
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("[✓] Scene 3 thumbnail attached.")
        except Exception as e:
            print(f"[!] Thumbnail note: {e}")

        add_to_playlist(youtube, video_id, PLAYLIST_NAME)

    print("\n[OK] Pipeline batch processing complete!")

if __name__ == "__main__":
    asyncio.run(process_batch())

# Harness2 & YouTube Ingest Pre-Upload SEO Optimization Hook
def get_seo_video_filename(title: str, puzzle_id: str) -> str:
    clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title).strip().lower()
    keyword_slug = clean_title.replace(' ', '-')
    return f"nyt-connections-hints-today-{keyword_slug}-puzzle-{puzzle_id}.mp4"
