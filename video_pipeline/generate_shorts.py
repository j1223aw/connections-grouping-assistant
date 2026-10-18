import os
import json
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Enforce Structured Output Schema (Karpathy Verifiability Rule)
class Scene(BaseModel):
    timestamp: str = Field(description="e.g. '0:00 - 0:03'")
    visual_action: str = Field(description="Description of visual grid animations, highlighted tiles, or zooms")
    overlay_text: str = Field(description="Bold on-screen text captions")
    voiceover: str = Field(description="Exact spoken line for TTS narration")

class ShortScript(BaseModel):
    video_title: str = Field(description="SEO-optimized Shorts title with #Shorts #NYTConnections")
    hook_headline: str = Field(description="Intriguing on-screen headline text (e.g., 'EVIL PURPLE TRAP')")
    target_category: str = Field(description="The primary category being deconstructed (usually Blue or Purple)")
    category_tier: str = Field(description="Yellow, Green, Blue, or Purple")
    tier_hex_color: str = Field(description="#f9ca24 (Yellow), #6ab04c (Green), #4834d4 (Blue), or #be2edd (Purple)")
    red_herrings_identified: List[str] = Field(description="Decoy words that mislead players")
    scenes: List[Scene] = Field(description="Chronological storyboard breakdown (30 to 45 seconds total)")
    pinned_comment: str = Field(description="Engagement question + CTA link to connectionsassistant.com")
    youtube_tags: List[str] = Field(description="Target tags for discovery")

# 2. System Instruction Grounding
SYSTEM_INSTRUCTION = """
You are an expert short-form video producer and scriptwriter for the YouTube Shorts channel @ConnectionsAssistant.
Your objective: Create high-retention 35-45 second vertical video scripts breaking down NYT Connections puzzles.
Brand Identity: High energy, intellectual, analytical, and fast-paced.
Core Palette:
- Yellow (#f9ca24)
- Green (#6ab04c)
- Blue (#4834d4)
- Purple (#be2edd)

Script Rules:
1. Hook (0:00-0:03): Direct pain point or curiosity gap (e.g., "The one word that ruined today's Connections board").
2. Tension/Decoy (0:03-0:18): Highlight 5-6 words that appear to fit one category to showcase the red herring.
3. Solve/Logic Reveal (0:18-0:34): Show the true grouping and explain the wordplay pattern.
4. Call to Action (0:34-0:40): Natural push to solve or test boards at https://connectionsassistant.com/.
"""

# 3. Client Initialization
# Assumes GEMINI_API_KEY is stored in your environment or Google Cloud credentials
client = genai.Client()

def generate_short_concept(board_words: List[str], theme_note: str = "") -> ShortScript:
    prompt = f"""
    Analyze these 16 words from a Connections puzzle and generate a complete YouTube Short production script:
    Words: {', '.join(board_words)}
    Special Focus/Theme Note: {theme_note if theme_note else "Deconstruct the trickiest purple or blue category"}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ShortScript,
            temperature=0.2
        )
    )
    return ShortScript.model_validate_json(response.text)

# 4. Batch Processing Queue
SAMPLE_BATCH = [
    {
        "id": "short_001_vessels_and_boards",
        "words": ["SWIFT", "RAPID", "FLEET", "QUICK", "FUJI", "GALA", "EMPIRE", "JAZZ", "CANOE", "KAYAK", "YACHT", "BARGE", "KEY", "DASH", "SURF", "SKATE"],
        "note": "Highlight how SWIFT and FLEET trick players away from the '___ BOARD' category."
    },
    {
        "id": "short_002_finance_and_tools",
        "words": ["BULL", "BEAR", "STAG", "SHEEP", "DRILL", "BIT", "TAP", "DIE", "BASS", "TROUT", "PIKE", "PERCH", "SPUR", "RAKE", "HOE", "SCYTHE"],
        "note": "Focus on the Machining tools (BIT, DIE, TAP, DRILL) vs Garden tools overlap."
    }
]

def run_batch():
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[*] Starting batch generation for {len(SAMPLE_BATCH)} Shorts...")

    for item in SAMPLE_BATCH:
        print(f"\n[+] Processing: {item['id']}")
        try:
            script_data = generate_short_concept(item["words"], item["note"])
            
            output_file = os.path.join(output_dir, f"{item['id']}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(script_data.model_dump_json(indent=2))
            
            print(f"    [OK] Saved script to {output_file}")
            print(f"    Title: {script_data.video_title}")
            print(f"    Hook: {script_data.hook_headline}")
            print(f"    Target Category: {script_data.target_category} ({script_data.category_tier})")
        except Exception as e:
            print(f"    [!] Error generating script for {item['id']}: {e}")

if __name__ == "__main__":
    run_batch()