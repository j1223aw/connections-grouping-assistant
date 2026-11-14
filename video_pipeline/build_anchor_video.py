import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts
from playwright.async_api import async_playwright
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline")
TEMPLATES_DIR = BASE_DIR / "templates"
RENDER_DIR = BASE_DIR / "rendered_videos"
RENDER_DIR.mkdir(exist_ok=True)
TEMP_DIR = BASE_DIR / "anchor_temp"
TEMP_DIR.mkdir(exist_ok=True)

CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "token.json"
VOICE_NAME = "en-US-ChristopherNeural"
PLAYLIST_NAME = "NYT Connections Hints & Strategies"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

SCENES = [
    {
        "id": 1,
        "title": "The 16-Word Grid Premise",
        "narration": (
            "Every day, sixteen shuffled words appear on the board. "
            "The goal sounds deceptively simple: find four groups of four. "
            "But if you play purely by instinct, the puzzle editor will beat you almost every time. "
            "To consistently solve every grid without blowing your guesses, you must understand the four-tier difficulty hierarchy, "
            "eliminate red herrings systematically, and master the core linguistic patterns."
        ),
        "content_html": """
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-family:'Fraunces',serif; font-size:42px; font-weight:900; margin-bottom:24px;">The 16-Word Grouping Grid</div>
          <div class="grid-16">
            <div class="tile">BAR</div><div class="tile">MATCH</div><div class="tile">CRANE</div><div class="tile">POUND</div>
            <div class="tile">SPRING</div><div class="tile">BOW</div><div class="tile">CLUB</div><div class="tile">STAMP</div>
            <div class="tile">SHUFFLE</div><div class="tile">MINT</div><div class="tile">TRUNK</div><div class="tile">DRILL</div>
            <div class="tile">FILE</div><div class="tile">RING</div><div class="tile">ROW</div><div class="tile">TANK</div>
          </div>
        </div>
        """
    },
    {
        "id": 2,
        "title": "The 4-Tier Difficulty Spectrum",
        "narration": (
            "The puzzle follows a strict cognitive spectrum. "
            "Yellow is Tier 1: straightforward direct synonyms and obvious physical categories. "
            "Green is Tier 2: contextual links, colloquialisms, or everyday associations. "
            "Blue is Tier 3: cultural trivia, pop references, and fill-in-the-blanks. "
            "And Purple is Tier 4: the dreaded abstract wordplay. "
            "Look for homophones, palindromes, letters added to words, and sneaky prefixes."
        ),
        "content_html": """
        <div class="tier-row">
          <div class="tier-card">
            <div>
              <div class="tier-badge badge-yellow">TIER 1 • EASIEST</div>
              <div class="tier-title">Yellow Tier</div>
              <div class="tier-desc">Direct synonyms or standard physical object groupings requiring minimal lateral interpretation.</div>
            </div>
            <div class="tier-samples">
              <span class="tier-pill">SHUFFLE</span><span class="tier-pill">SLIDE</span><span class="tier-pill">CREEP</span><span class="tier-pill">SLINK</span>
            </div>
          </div>
          <div class="tier-card">
            <div>
              <div class="tier-badge badge-green">TIER 2 • MODERATE</div>
              <div class="tier-title">Green Tier</div>
              <div class="tier-desc">Contextual links, shared parts of speech, or familiar real-world groupings.</div>
            </div>
            <div class="tier-samples">
              <span class="tier-pill">HAMMER</span><span class="tier-pill">DRILL</span><span class="tier-pill">WRENCH</span><span class="tier-pill">PLIERS</span>
            </div>
          </div>
          <div class="tier-card">
            <div>
              <div class="tier-badge badge-blue">TIER 3 • CHALLENGING</div>
              <div class="tier-title">Blue Tier</div>
              <div class="tier-desc">Trivia-based subsets, compound roots, pop culture, or geographic groupings.</div>
            </div>
            <div class="tier-samples">
              <span class="tier-pill">TAR</span><span class="tier-pill">POSTAL</span><span class="tier-pill">CREDIT</span><span class="tier-pill">WILD</span>
            </div>
          </div>
          <div class="tier-card purple-shimmer">
            <div>
              <div class="tier-badge badge-purple">TIER 4 • TRICKIEST</div>
              <div class="tier-title">Purple Tier</div>
              <div class="tier-desc">Clever wordplay, homophones, palindromes, anagrams, or hidden letters.</div>
            </div>
            <div class="tier-samples">
              <span class="tier-pill">THYME</span><span class="tier-pill">PEAR</span><span class="tier-pill">FLOUR</span><span class="tier-pill">CHILI</span>
            </div>
          </div>
        </div>
        """
    },
    {
        "id": 3,
        "title": "The 5-Word Red Herring Trap",
        "narration": (
            "Here is the number one trap that breaks streaks: the overlapping candidate. "
            "When you scan the board and immediately spot five words that seem to belong to the exact same theme, do not guess. "
            "That fifth word is an intentional red herring designed to burn your lives. "
            "If you see five matches, set that entire group aside. "
            "Find an isolated set of four with zero overlap elsewhere before touching it."
        ),
        "content_html": """
        <div style="display:flex; flex-direction:column; align-items:center; gap:28px;">
          <div class="trap-banner">
            <h2>⚠️ The 5-Word Overlapping Candidate Trap</h2>
            <p>Puzzle editors intentionally place 5 words sharing an obvious category (e.g., 5 animals or 5 tree types). Selecting 4 at random yields an 80% failure rate.</p>
          </div>
          <div style="display:flex; gap:16px;">
            <div class="tile trap">CHESTNUT</div>
            <div class="tile trap">WALNUT</div>
            <div class="tile trap">PECAN</div>
            <div class="tile trap">CASHEW</div>
            <div class="tile trap" style="background:#EF4444; color:#FFFFFF;">DOUGHNUT</div>
          </div>
          <div style="font-family:'JetBrains Mono',monospace; font-size:22px; font-weight:800; color:#CA8A04;">
            Rule of Thumb: Never guess a 5-candidate cluster until the overlapping decoy resolves elsewhere!
          </div>
        </div>
        """
    },
    {
        "id": 4,
        "title": "The 4 Essential Linguistic Patterns",
        "narration": (
            "When you are stuck, cycle through these four patterns: "
            "First: Fill-in-the-blank roots, words that share a hidden prefix or suffix like Fire, Water, and Pin before Wheel. "
            "Second: Phonetic matches, say the words out loud to catch homophones like Thyme and Time. "
            "Third: Syntactic shifts, check if a word shifts between a noun, verb, or adjective, like Train as a vehicle versus Train as coaching. "
            "Fourth: Contained words, anagrams or words buried inside larger words."
        ),
        "content_html": """
        <div class="pattern-grid">
          <div class="pattern-card">
            <div class="pattern-header">1. Fill-in-the-Blank Roots</div>
            <div class="pattern-body">Words that precede or follow a shared unstated anchor term (e.g., <em>Fire, Water, Pin, Cheese</em> before "Wheel").</div>
          </div>
          <div class="pattern-card">
            <div class="pattern-header">2. Phonetic Matches (Homophones)</div>
            <div class="pattern-body">Words that sound identical aloud despite divergent spellings (e.g., <em>Thyme / Time, Flour / Flower, Sole / Soul</em>).</div>
          </div>
          <div class="pattern-card">
            <div class="pattern-header">3. Syntactic Shifts (Parts of Speech)</div>
            <div class="pattern-body">Words switching grammatical function (e.g., <em>Train</em> as a physical locomotive vs. <em>Train</em> as athletic coaching).</div>
          </div>
          <div class="pattern-card">
            <div class="pattern-header">4. Contained Letters & Anagrams</div>
            <div class="pattern-body">Hidden internal patterns, backwards spellings, or words created by dropping the first or last letter.</div>
          </div>
        </div>
        """
    },
    {
        "id": 5,
        "title": "Semantic Elimination & The Assistant Tool",
        "narration": (
            "When you are down to the final eight words and hit mental fatigue, do not guess blindly. "
            "Use semantic elimination. "
            "Our tool at connectionsassistant.com runs server-side lexical reasoning to give you strategy nudges and anti-spoiler hints, "
            "revealing pattern types and anchor words without ruining the solve. "
            "Bookmark the guide, protect your streak, and solve smarter every morning."
        ),
        "content_html": """
        <div class="assistant-showcase">
          <div class="showcase-info">
            <h2>Computational Linguistic Reasoning</h2>
            <p>Our server-side engine calculates statistical co-occurrence vectors across words to highlight true clusters and surface red herrings with zero spoilers.</p>
            <div class="feature-pills">
              <span class="feature-pill">🛡️ 3-Stage Spoiler Shield</span>
              <span class="feature-pill">🔥 Local Streak Tracker</span>
              <span class="feature-pill">⚡ 1-Click Quick Paste</span>
            </div>
          </div>
          <div class="preview-box">
            <div class="streak">🔥 Keep Your Daily Streak Alive</div>
            <div style="margin-bottom:24px; color:#4B5563; font-size:18px;">Solve daily grids with confidence:</div>
            <div class="cta-link">connectionsassistant.com</div>
          </div>
        </div>
        """
    }
]

def get_audio_duration(audio_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(res.stdout.strip())

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

async def main():
    print("=" * 70)
    print("PRODUCING MASTER ANCHOR VIDEO: THE DEFINITIVE GUIDE TO NYT CONNECTIONS")
    print("=" * 70)

    template_file = TEMPLATES_DIR / "anchor_template.html"
    template_html = template_file.read_text(encoding="utf-8")

    scene_audio_files = []
    scene_durations = []
    frame_paths = []

    # 1. Synthesize Audio for Each Chapter
    for sc in SCENES:
        s_id = sc["id"]
        out_mp3 = str(TEMP_DIR / f"scene_{s_id}.mp3")
        print(f"[+] Synthesizing Scene {s_id} voiceover...")
        comm = edge_tts.Communicate(sc["narration"], VOICE_NAME, rate="+12%")
        await comm.save(out_mp3)
        dur = get_audio_duration(out_mp3)
        scene_audio_files.append(out_mp3)
        scene_durations.append(dur)
        print(f"    Scene {s_id} duration: {dur:.2f}s")

    # 2. Render 1920x1080 Frames via Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        for sc in SCENES:
            s_id = sc["id"]
            frame_path = str(TEMP_DIR / f"frame_{s_id}.png")
            html = template_html.replace("{{CONTENT}}", sc["content_html"])
            await page.set_content(html)
            await page.screenshot(path=frame_path)
            frame_paths.append(frame_path)
            print(f"[✓] Captured landscape frame for Scene {s_id}")

        await browser.close()

    # 3. Concatenate Audio Tracks
    combined_audio = str(TEMP_DIR / "anchor_full_audio.mp3")
    audio_list_txt = TEMP_DIR / "audio_list.txt"
    with open(audio_list_txt, "w") as f:
        for a in scene_audio_files:
            f.write(f"file '{a.replace(os.sep, '/')}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list_txt), "-c", "copy", combined_audio
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # 4. Create Video Concat Manifest
    concat_txt = TEMP_DIR / "anchor_concat.txt"
    with open(concat_txt, "w") as f:
        for i in range(len(SCENES)):
            f.write(f"file '{frame_paths[i].replace(os.sep, '/')}'\n")
            f.write(f"duration {scene_durations[i]:.2f}\n")
        f.write(f"file '{frame_paths[-1].replace(os.sep, '/')}'\n")

    # 5. FFmpeg Assembly with NVENC
    final_output = RENDER_DIR / "the_definitive_guide_to_solving_nyt_connections.mp4"
    print(f"\n[+] Encoding master 1080p landscape video with NVENC...")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", combined_audio,
        "-c:v", "h264_nvenc", "-preset", "p6", "-b:v", "10M", "-pix_fmt", "yuv420p", "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(final_output)
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(f"[✓] Anchor video rendered successfully: {final_output}")

    # 6. YouTube Upload (Published as Public Master Pillar Video)
    title = "The Definitive Guide to Solving NYT Connections | Master Strategy & Color Tiers"
    description = (
        "Master daily 16-word grouping grids without burning guesses or losing your streak!\n\n"
        "Read the full interactive guide: https://connectionsassistant.com/nyt-connections-guide.html\n"
        "Analyze your board with zero spoilers: https://connectionsassistant.com/\n\n"
        "Chapters:\n"
        "0:00 - The 16-Word Board Trap\n"
        "0:25 - The 4 Difficulty Tiers (Yellow, Green, Blue, Purple)\n"
        "1:10 - Deconstructing the 5-Word Red Herring\n"
        "1:45 - 4 Linguistic Patterns to Spot Every Game\n"
        "2:20 - Semantic Elimination & Protecting Your Streak\n\n"
        "🟨 TIER 1 • EASIEST (Direct Synonyms)\n"
        "🟩 TIER 2 • MODERATE (Contextual Link)\n"
        "🟦 TIER 3 • CHALLENGING (Trivia & Patterns)\n"
        "🟪 TIER 4 • TRICKIEST (Lateral Wordplay)\n\n"
        "#NYTConnections #ConnectionsHints #WordPuzzle #BrainTeaser #ConnectionsGuide"
    )
    tags = [
        "NYT Connections", "Connections hints", "NYT Connections guide",
        "how to solve connections", "word puzzle strategy", "connections tutorial",
        "connections assistant", "purple category"
    ]

    youtube = get_authenticated_service()
    print(f"\n[+] Uploading anchor video to YouTube...")
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "27"
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(str(final_output), chunksize=1024*1024*8, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[+] Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"\n[✓] Master Anchor Video Published! Video ID: {video_id} (https://youtu.be/{video_id})")

    # Set Custom Thumbnail from Scene 2 (4-Tier Spectrum)
    thumb_path = TEMP_DIR / "frame_2.png"
    if thumb_path.exists():
        try:
            thumb_media = MediaFileUpload(str(thumb_path), mimetype="image/png", resumable=True)
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("[✓] Custom 16:9 thumbnail attached.")
        except Exception as e:
            print(f"[!] Thumbnail error: {e}")

    # Add to Playlist
    add_to_playlist(youtube, video_id, PLAYLIST_NAME)

    print("\n[OK] Anchor deployment complete! This video is now your permanent Related Video target.")

if __name__ == "__main__":
    asyncio.run(main())
