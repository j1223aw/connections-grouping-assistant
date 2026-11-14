"""
upload_today_short.py

Automated YouTube Uploader for Connections Assistant 2-Video Drops.
Supports uploading:
- Drop 1 (Teaser / Hints Short): output_shorts/today_connections_hints.mp4
- Drop 2 (Full Board Walkthrough): output_shorts/today_connections_full_solution.mp4

Sets title, description, tags, category, public status, custom thumbnail, playlist, and top comment.
Updates output_shorts/latest_short_id.txt (for Drop 1 web embed).
"""

import argparse
import json
import os
from pathlib import Path
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT_DIR = Path(__file__).resolve().parent
TOKEN_FILE = ROOT_DIR / "video_pipeline" / "token.json"
CLIENT_SECRETS_FILE = ROOT_DIR / "video_pipeline" / "client_secrets.json"
OUTPUT_DIR = ROOT_DIR / "output_shorts"
PUZZLE_FILE = ROOT_DIR / "daily_puzzle.json"

PLAYLIST_ID = "PLrujECPbJ25iriPAQg_wHvztpdpuA98Zt"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def get_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            print("[+] Refreshing access token...")
            try:
                creds.refresh(Request())
                refreshed = True
                print("[✓] Token refreshed successfully.")
            except Exception as e:
                print(f"[!] Refresh token expired or revoked ({e}).")

        if not refreshed:
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(f"Client secrets not found at {CLIENT_SECRETS_FILE}")
            print("[+] Launching OAuth browser authorization flow...")
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"[✓] Token saved to {TOKEN_FILE.name}.")

    return build("youtube", "v3", credentials=creds)


def upload_single_video(
    youtube,
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: Path | None = None,
    comment_text: str | None = None,
    save_as_latest_short: bool = False,
) -> str:
    """Uploads a video to YouTube and sets thumbnail, playlist, and comment."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found at {video_path}")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "24",  # Entertainment
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en-US",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    print(f"\n[+] Starting upload for {video_path.name} ({video_path.stat().st_size} bytes)...")
    media = MediaFileUpload(
        str(video_path),
        chunksize=1024 * 1024 * 8,
        resumable=True,
        mimetype="video/mp4",
    )
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"    Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    print(f"[✓] Published! Video ID: {video_id} (https://youtube.com/shorts/{video_id})")

    # Set Custom Thumbnail
    if thumbnail_path and thumbnail_path.exists():
        try:
            print(f"[+] Setting thumbnail from {thumbnail_path.name}...")
            thumb_media = MediaFileUpload(str(thumbnail_path), mimetype="image/png", resumable=True)
            youtube.thumbnails().set(videoId=video_id, media_body=thumb_media).execute()
            print("[✓] Thumbnail attached.")
        except Exception as e:
            print(f"[!] Warning attaching thumbnail: {e}")

    # Add to Playlist
    try:
        print(f"[+] Adding to playlist {PLAYLIST_ID}...")
        youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "playlistId": PLAYLIST_ID,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id,
                    },
                }
            },
        ).execute()
        print("[✓] Video added to playlist.")
    except Exception as e:
        print(f"[!] Warning adding to playlist: {e}")

    # Post Comment
    if comment_text:
        try:
            print("[+] Posting pinned link comment...")
            youtube.commentThreads().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "topLevelComment": {
                            "snippet": {
                                "textOriginal": comment_text,
                            }
                        },
                    }
                },
            ).execute()
            print("[✓] Comment posted.")
        except Exception as e:
            print(f"[!] Warning posting comment: {e}")

    # Save to latest_short_id.txt if requested
    if save_as_latest_short:
        id_file = OUTPUT_DIR / "latest_short_id.txt"
        id_file.write_text(video_id.strip(), encoding="utf-8")
        print(f"[✓] Saved as active short ID in {id_file.name}")

    return video_id


def upload_drop_1(youtube) -> str:
    """Upload Drop 1: Hints Short."""
    pdate = "Today"
    if PUZZLE_FILE.exists():
        with open(PUZZLE_FILE, "r", encoding="utf-8") as f:
            pdate = json.load(f).get("date", "Today")

    video_path = OUTPUT_DIR / "today_connections_hints.mp4"
    if not video_path.exists():
        video_path = OUTPUT_DIR / "today_connections_short.mp4"

    thumb_path = OUTPUT_DIR / "frames" / "scene_3.png"
    title = f"NYT Connections Hints Today - {pdate} #shorts #nytconnections #education #connectionshints"
    description = (
        "Stuck on today's grid? View the full interactive board breakdown & test associations without spoilers at: "
        "https://connectionsassistant.com/breakdowns.html\n\n\n"
        "#NYTConnections #WordPuzzle #BrainTeaser #ConnectionsHints #Shorts"
    )
    tags = [
        "NYT Connections",
        "Connections hints",
        "NYT Connections today",
        "Connections Assistant",
        "Rangsk",
        "NYT Connections Rangsk",
        "Chris Remington",
        "Wordle Solver",
    ]
    comment = (
        "Stuck on today's grid? View the full interactive board breakdown & test associations without spoilers at: "
        "https://connectionsassistant.com/breakdowns.html"
    )

    return upload_single_video(
        youtube=youtube,
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        thumbnail_path=thumb_path,
        comment_text=comment,
        save_as_latest_short=True,
    )


def upload_drop_2(youtube) -> str:
    """Upload Drop 2: Full Board Ordered Walkthrough."""
    pdate = "Today"
    pid = ""
    if PUZZLE_FILE.exists():
        with open(PUZZLE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            pdate = d.get("date", "Today")
            pid = d.get("id", "")

    video_path = OUTPUT_DIR / "today_connections_full_solution.mp4"
    thumb_path = OUTPUT_DIR / "solution_frames" / "frame_4b_purple_solved.png"

    title = f"NYT Connections Solution Today - {pdate} | Full Ordered Walkthrough #shorts #nytconnections"
    description = (
        f"Full step-by-step ordered solution for today's NYT Connections (#{pid} - {pdate}):\n"
        "Yellow to Green to Blue to Purple.\n\n"
        "Test candidate groups on our free interactive scratchboard without burning guesses:\n"
        "https://connectionsassistant.com/breakdowns.html\n\n"
        "#NYTConnections #ConnectionsSolution #WordPuzzle #BrainTeaser #Shorts"
    )
    tags = [
        "NYT Connections",
        "Connections solution today",
        "Connections full walkthrough",
        "NYT Connections answers",
        "Connections hints",
        "Connections Assistant",
        "Wordle Solver",
    ]
    comment = (
        "Solve today's puzzle without spoilers or test your theories at: "
        "https://connectionsassistant.com/breakdowns.html"
    )

    return upload_single_video(
        youtube=youtube,
        video_path=video_path,
        title=title,
        description=description,
        tags=tags,
        thumbnail_path=thumb_path,
        comment_text=comment,
        save_as_latest_short=False,
    )


def main():
    parser = argparse.ArgumentParser(description="Upload daily Shorts to YouTube channel.")
    parser.add_argument("--drop", choices=["1", "2", "all"], default="all", help="Which drop to upload (1, 2, or all)")
    args = parser.parse_args()

    youtube = get_service()

    if args.drop in ["1", "all"]:
        print("\n--- UPLOADING DROP 1 (HINTS SHORT) ---")
        upload_drop_1(youtube)

    if args.drop in ["2", "all"]:
        print("\n--- UPLOADING DROP 2 (FULL WALKTHROUGH SHORT) ---")
        upload_drop_2(youtube)

    print("\n[SUCCESS] YouTube deployment finished.")


if __name__ == "__main__":
    main()
