import json
import subprocess
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant\video_pipeline")
CLIENT_SECRETS = BASE_DIR / "client_secrets.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Verified active playlist ID from your channel
PLAYLIST_ID = "PLrujECpbJ25iriPAQg_whVztpdpuA98Zt"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

PINNED_COMMENT_TEXT = "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html"

TARGET_VIDEOS = [
    {"search": "tie trap", "title": "The TIE Trap | NYT Connections Hints", "topic": "The TIE Trap: Neckwear vs Game Scores"},
    {"search": "bat trap", "title": "The BAT Trap | NYT Connections Hints", "topic": "The BAT Trap: Baseball Bats vs Flying Mammals"},
    {"search": "ring trap", "title": "The RING Trap | NYT Connections Hints", "topic": "The RING Trap: Jewelry Accessories vs Circus Arenas"},
    {"search": "file trap", "title": "The FILE Trap | NYT Connections Hints", "topic": "The FILE Trap: Digital vs Metal Smoothing Tools"},
    {"search": "key trap", "title": "The KEY Trap | NYT Connections Hints", "topic": "The KEY Trap: Door Openers vs Musical Scales"}
]

def get_authenticated_service():
    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)

def copy_to_clipboard(text: str):
    try:
        cmd = f"Set-Clipboard -Value \"{text}\""
        subprocess.run(["powershell", "-Command", cmd], check=True)
        print("[✓] Pinned CTA auto-copied to Windows clipboard.")
    except Exception:
        pass

def run_scheduled_upgrades():
    youtube = get_authenticated_service()
    quota_spent = 0
    watch_links = []

    print("[*] Fetching channel uploads playlist...")
    channel_response = youtube.channels().list(mine=True, part="contentDetails").execute()
    quota_spent += 1
    uploads_list_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Pull up to 50 items to span the entire scheduled queue
    playlist_items = youtube.playlistItems().list(
        playlistId=uploads_list_id,
        part="snippet",
        maxResults=50
    ).execute()
    quota_spent += 1

    items = playlist_items.get("items", [])
    print(f"[*] Scanned {len(items)} channel uploads. Matching target window...\n")

    for target in TARGET_VIDEOS:
        matched_item = None
        for item in items:
            title = item["snippet"]["title"]
            if target["search"] in title.lower():
                matched_item = item
                break

        if not matched_item:
            print(f"[?] Target '{target['search']}' not found in latest 50 uploads. Skipping.")
            continue

        video_id = matched_item["snippet"]["resourceId"]["videoId"]
        print(f"[+] Found: {matched_item['snippet']['title']} (ID: {video_id})")

        # 1. Update Video Snippet (50 units)
        full_desc = (
            f"{target['topic']}\n\n"
            "Stuck on today's grid? Test associations without spoilers at https://connectionsassistant.com/nyt-connections-guide.html\n\n"
            "🟨 TIER 1 • EASIEST (Direct Synonyms)\n"
            "🟩 TIER 2 • MODERATE (Contextual Link)\n"
            "🟦 TIER 3 • CHALLENGING (Trivia & Patterns)\n"
            "🟪 TIER 4 • TRICKIEST (Lateral Wordplay)\n\n"
            "#NYTConnections #ConnectionsHints #WordPuzzle #Shorts"
        )

        try:
            youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": {
                        "title": target["title"],
                        "description": full_desc,
                        "categoryId": "27",
                        "tags": ["NYT Connections hints today", "Connections hints", "word puzzle", "Shorts"]
                    }
                }
            ).execute()
            quota_spent += 50
            print("  [✓] Updated title, tags, and 4-tier description.")
        except Exception as e:
            print(f"  [!] Snippet update error: {e}")

        # 2. Add to Playlist (50 units)
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
            print("  [✓] Added to NYT Connections Hints playlist.")
        except Exception as e:
            print(f"  [!] Playlist insert notice: {e}")

        watch_links.append((target["title"], f"https://www.youtube.com/watch?v={video_id}"))

    copy_to_clipboard(PINNED_COMMENT_TEXT)

    print("\n" + "="*70)
    print(f"[OK] Upgrade complete! Total API units consumed: {quota_spent} / 10,000 max.")
    print("="*70)
    if watch_links:
        print("\nACTION: Pin Referral Comment on Scheduled Videos (CTA already in clipboard):")
        print(f"Text: \"{PINNED_COMMENT_TEXT}\"\n")
        for t, link in watch_links:
            print(f"• {t}: {link}")
        print("\nClick link -> Paste (Ctrl+V) -> Post -> ⋮ -> Pin.")
        print("="*70 + "\n")

if __name__ == "__main__":
    run_scheduled_upgrades()
