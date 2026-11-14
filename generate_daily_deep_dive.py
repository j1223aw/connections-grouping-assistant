"""
generate_daily_deep_dive.py

Daily Long-Form Masterclass & Word Guide Generator for NYT Connections.
Combines:
1. Daily Hints & Solutions.
2. The 4 Tiers Walkthrough (Direct Synonyms, Contextual Links, Trivia, and Lateral Mechanics).
3. The 16-Word Complete Guide: Definitions, Pronunciations, Word Origins, and Everyday Example Sentences.
4. British English Sub-Baritone Audio Calibration (en-GB-RyanNeural, pitch -8Hz, rate -2%, FFmpeg bass EQ).
5. 1080p 16:9 Widescreen Neo-Brutalist Visual Engine rendered with Playwright and hardware-accelerated with NVENC.
"""

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import edge_tts
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output_masterclass"
TEMP_DIR = OUTPUT_DIR / "temp_deep_dive"
FINAL_VIDEO = OUTPUT_DIR / "today_deep_dive_masterclass.mp4"
METADATA_FILE = OUTPUT_DIR / "today_deep_dive_metadata.txt"

VOICE_NAME = "en-GB-RyanNeural"
VOICE_PITCH = "-8Hz"
VOICE_RATE = "-2%"
EQ_FILTER = "bass=g=3.5:f=110"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Complete Curated Lexicon for Today's Puzzle (Nov 12, 2026 - Puzzle #1250)
CURATED_LEXICON = {
    "GOOD HEAVENS": {
        "ipa": "[ɡʊd ˈhɛv.ənz]",
        "pos": "interjection",
        "definition": "A vintage exclamation expressing surprise, shock, disbelief, or mild consternation without profanity.",
        "etymology": "Middle English euphemistic substitution for God, invoking the celestial heavens.",
        "sentence": "'Good heavens, look at how quickly the afternoon passed!' she remarked as the sun dipped below the horizon."
    },
    "GREAT SCOTT": {
        "ipa": "[ɡreɪt skɒt]",
        "pos": "interjection",
        "definition": "An exclamation of astonishment, wonder, or amazement, famously popularized by Doc Brown.",
        "etymology": "19th-century American military salute to General Winfield Scott; popularized in Back to the Future.",
        "sentence": "'Great Scott! You solved today's entire puzzle on your very first try without burning a single guess!'"
    },
    "HOLY SMOKES": {
        "ipa": "[ˈhoʊ.li smoʊks]",
        "pos": "interjection",
        "definition": "An informal, colorful exclamation of shock, amazement, or bewildered excitement.",
        "etymology": "Late 19th-century American colloquial euphemistic oath substituting 'smokes' for sacred terms.",
        "sentence": "'Holy smokes, did you see how fast that shooting star blazed across the clear midnight sky?'"
    },
    "JIMINY CRICKET": {
        "ipa": "[ˈdʒɪm.ɪ.ni ˈkrɪk.ɪt]",
        "pos": "interjection",
        "definition": "A mild, polite exclamation of surprise or bewilderment, later immortalized as Pinocchio's conscience.",
        "etymology": "Late 19th-century English minced oath for Jesus Christ; later named as Disney's iconic cricket character.",
        "sentence": "'Jiminy Cricket, that sudden thunderclap shook the entire living room window!'"
    },
    "CHANGE PURSE": {
        "ipa": "[ˈtʃeɪndʒ pɜːrs]",
        "pos": "noun",
        "definition": "A small pouch or clasp wallet specifically designed for carrying loose metal coins. First word CHANGE means variation.",
        "etymology": "Old French changier (to alter, vary) + Middle English purse (pouch, money bag).",
        "sentence": "She popped open the polished brass clasp of her leather change purse to pay the exact transit fare."
    },
    "FLUX CAPACITOR": {
        "ipa": "[flʌks kəˈpæs.ɪ.tər]",
        "pos": "noun",
        "definition": "The fictional core time-travel component of the DeLorean. First word FLUX denotes continuous change or flow.",
        "etymology": "Latin fluxus (a flowing, alteration) + Late Latin capacitas (capacity, holding charge).",
        "sentence": "Doc Brown famously sketched the Y-shaped schematic of the flux capacitor after hitting his head on a porcelain sink."
    },
    "SHIFT DRESS": {
        "ipa": "[ʃɪft drɛs]",
        "pos": "noun",
        "definition": "A classic, straight-cut dress that hangs loose from the shoulders without a fitted waistline. First word SHIFT means change.",
        "etymology": "Old English sciftan (to divide, arrange, change direction) + Old French drecier.",
        "sentence": "She chose a comfortable, breathable linen shift dress for the warm outdoor summer luncheon."
    },
    "SWING SET": {
        "ipa": "[swɪŋ sɛt]",
        "pos": "noun",
        "definition": "An outdoor playground frame with suspended seats for swinging back and forth. First word SWING represents oscillation or variation.",
        "etymology": "Old English swingan (to toss, oscillate, sway back and forth) + Old French sette.",
        "sentence": "Eager school children raced across the grass toward the playground's tall swing set as soon as the bell rang."
    },
    "ARCTIC CHAR": {
        "ipa": "[ˈɑːrk.tɪk tʃɑːr]",
        "pos": "noun",
        "definition": "A cold-water fish of the salmon family native to subpolar and alpine waters. Ends in CHAR, a dry heat cooking method.",
        "etymology": "Greek arktikos (northern) + Celtic ceara (blood-colored) + Middle English charen (to scorch).",
        "sentence": "The dinner menu featured pan-seared Arctic char served over a bed of roasted autumn vegetables."
    },
    "COMEDY ROAST": {
        "ipa": "[ˈkɒm.ə.di roʊst]",
        "pos": "noun",
        "definition": "A festive banquet where an honored guest is humorously teased with witty insults. Ends in ROAST, an oven cooking method.",
        "etymology": "Greek komoidia (amusing spectacle) + Old French rostir (to brown over dry heat).",
        "sentence": "Fellow comedians and close friends gathered on stage for the annual charity comedy roast, exchanging affectionate jabs."
    },
    "DOC BROWN": {
        "ipa": "[dɒk braʊn]",
        "pos": "noun",
        "definition": "Dr. Emmett Brown, the eccentric time-travel inventor in Back to the Future. Ends in BROWN, to cook until golden.",
        "etymology": "Colloquial short form of doctor (Latin docere, to teach) + Old English brūn (golden-brown surface).",
        "sentence": "Doc Brown adjusted his protective welding goggles before routing 1.21 gigawatts of electricity into the vehicle."
    },
    "YOU'RE TOAST": {
        "ipa": "[jʊər toʊst]",
        "pos": "phrase",
        "definition": "A colloquial idiom warning that someone is in severe trouble, finished, or defeated. Ends in TOAST, browned via radiant heat.",
        "etymology": "Latin torrere (to scorch, parch) via Old French toster; American slang emergence in the 1980s.",
        "sentence": "'If the head coach catches you arriving late to the championship scrimmage, you're toast!'"
    },
    "GLADIATOR SANDALS": {
        "ipa": "[ˈɡlæd.i.eɪ.tər ˈsæn.dəlz]",
        "pos": "noun",
        "definition": "Strappy flat footwear featuring crisscrossing leather bands around the foot and ankle. Starts with GLADIATOR (Best Picture, 2000).",
        "etymology": "Latin gladiator (swordsman, from gladius) + Greek sandalion (light wooden or leather sole).",
        "sentence": "She paired her bohemian summer maxi dress with comfortable leather gladiator sandals."
    },
    "MARTY MCFLY": {
        "ipa": "[ˈmɑːr.ti məkˈflaɪ]",
        "pos": "noun",
        "definition": "The teenage guitarist hero of the Back to the Future trilogy. Starts with MARTY, Delbert Mann's 1955 Best Picture winner.",
        "etymology": "Diminutive of Martin (Latin Mars, Roman god) + Gaelic Mac an fhleisdeir (arrow maker's son).",
        "sentence": "Marty McFly grabbed his skateboard and hooked onto the rear bumper of a passing pickup truck to reach school."
    },
    "MOONLIGHT SONATA": {
        "ipa": "[ˈmuːn.laɪt səˈnɑː.tə]",
        "pos": "noun",
        "definition": "Ludwig van Beethoven's beloved Piano Sonata No. 14 in C-sharp minor. Starts with MOONLIGHT (Best Picture, 2016).",
        "etymology": "Old English mōna (moon) + lēoht (light) + Italian sonata (piece played on an instrument).",
        "sentence": "The concert hall fell into complete silence as the pianist began the gentle, melancholic chords of Beethoven's Moonlight Sonata."
    },
    "ROCKY ROAD": {
        "ipa": "[ˈrɒk.i roʊd]",
        "pos": "noun",
        "definition": "An iconic ice cream flavor packed with rich chocolate, marshmallows, and toasted nuts. Starts with ROCKY (Best Picture, 1976).",
        "etymology": "Old English rocc (crag, stone) + Old English rād (riding, journey, highway).",
        "sentence": "On a warm summer evening after dinner, he enjoyed a generous waffle cone of rocky road ice cream."
    }
}

SLIDE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@700;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    width: 1920px;
    height: 1080px;
    background-color: #FAF8F5;
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #1A1A1A;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 40px 64px;
    overflow: hidden;
  }

  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 16px;
    box-shadow: 0 6px 0 #1A1A1A;
    padding: 16px 32px;
  }
  .brand {
    font-family: 'Fraunces', serif;
    font-size: 28px;
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-badge {
    background: #1A1A1A;
    color: #FFFFFF;
    font-size: 13px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
  }
  .act-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 800;
    background: #FEF9C3;
    border: 2.5px solid #1A1A1A;
    padding: 6px 18px;
    border-radius: 999px;
    box-shadow: 0 3px 0 #1A1A1A;
  }

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin: 18px 0;
  }

  .scene-title {
    font-family: 'Fraunces', serif;
    font-size: 44px;
    font-weight: 900;
    line-height: 1.15;
    margin-bottom: 8px;
  }
  .scene-subtitle {
    font-size: 20px;
    color: #525252;
    font-weight: 600;
    margin-bottom: 22px;
  }

  /* Cards & Grid Containers */
  .grid-4x4 {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }
  .word-tile {
    background: #FFFFFF;
    border: 3px solid #1A1A1A;
    border-radius: 12px;
    box-shadow: 0 4px 0 #1A1A1A;
    padding: 18px;
    text-align: center;
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 0.04em;
  }

  .lexicon-card-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
  }
  .lexicon-card {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 14px;
    box-shadow: 0 5px 0 #1A1A1A;
    padding: 18px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .lexicon-top {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
    border-bottom: 2px solid #E5E5E5;
    padding-bottom: 6px;
  }
  .lexicon-word {
    font-family: 'Fraunces', serif;
    font-size: 26px;
    font-weight: 900;
  }
  .lexicon-ipa {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: #4B5563;
    background: #F3F4F6;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid #D1D5DB;
  }
  .lexicon-def {
    font-size: 15px;
    font-weight: 600;
    color: #1F2937;
    margin-bottom: 6px;
    line-height: 1.4;
  }
  .lexicon-etym {
    font-size: 13px;
    color: #6B7280;
    font-style: italic;
    margin-bottom: 6px;
  }
  .lexicon-sentence {
    font-size: 14px;
    font-weight: 700;
    color: #111827;
    background: #F9FAFB;
    padding: 6px 10px;
    border-radius: 6px;
    border-left: 3.5px solid #1A1A1A;
  }

  /* WWWWWH Bento Box */
  .wwwwwh-bento {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
  }
  .bento-cell {
    background: #FFFFFF;
    border: 3px solid #1A1A1A;
    border-radius: 12px;
    box-shadow: 0 4px 0 #1A1A1A;
    padding: 14px 18px;
  }
  .bento-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 800;
    text-transform: uppercase;
    color: #4B5563;
    margin-bottom: 4px;
  }
  .bento-val {
    font-size: 16px;
    font-weight: 700;
    line-height: 1.35;
  }

  .tier-banner {
    border: 3.5px solid #1A1A1A;
    border-radius: 12px;
    box-shadow: 0 5px 0 #1A1A1A;
    padding: 14px 20px;
    margin-bottom: 16px;
    font-weight: 800;
    font-size: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .banner-yellow { background: #F9CA24; }
  .banner-green  { background: #6AB04C; color: #FFFFFF; }
  .banner-blue   { background: #4834D4; color: #FFFFFF; }
  .banner-purple { background: #BE2EDD; color: #FFFFFF; }

  footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 2.5px solid #1A1A1A;
    padding-top: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
  }
</style>
</head>
<body>
  <header>
    <div class="brand">
      Connections Assistant
      <span class="brand-badge">DAILY DEEP DIVE</span>
    </div>
    <div class="act-pill">{act_pill}</div>
  </header>

  <main>
    {main_content}
  </main>

  <footer>
    <span>Daily Master Guide • connectionsassistant.com</span>
    <span>{footer_tag}</span>
  </footer>
</body>
</html>
"""

SCENES = [
    {
        "id": "scene_01_intro_board",
        "act_pill": "ACT 1: THE BOARD & BACK TO THE FUTURE TRAP",
        "footer_tag": "Puzzle #1250 Analysis",
        "narration": (
            "Welcome to Connections Assistant. Today, we walk through the full puzzle for New York Times Connections "
            "Puzzle 1250 for Thursday, November 12th. At first glance, the grid presents four tempting sci-fi movie references: "
            "Great Scott, Flux Capacitor, Doc Brown, and Marty McFly. This is a classic four-color rainbow decoy trap spanning all four tiers. "
            "Today we will break down each category step by step, followed by the word meanings, "
            "origins, and pronunciations for all sixteen words."
        ),
        "content": """
        <div class="scene-title">Today's Step-by-Step Walkthrough</div>
        <div class="scene-subtitle">Puzzle #1250 &bull; Spotting the 4-Color BACK TO THE FUTURE Trap</div>
        <div class="grid-4x4">
          <div class="word-tile" style="border: 3.5px dashed #D97706; background: #FEF3C7;">GREAT SCOTT (DECOY)</div>
          <div class="word-tile">ROCKY ROAD</div>
          <div class="word-tile">YOU'RE TOAST</div>
          <div class="word-tile" style="border: 3.5px dashed #D97706; background: #FEF3C7;">FLUX CAPACITOR (DECOY)</div>
          <div class="word-tile">MOONLIGHT SONATA</div>
          <div class="word-tile">JIMINY CRICKET</div>
          <div class="word-tile" style="border: 3.5px dashed #D97706; background: #FEF3C7;">MARTY MCFLY (DECOY)</div>
          <div class="word-tile">COMEDY ROAST</div>
          <div class="word-tile" style="border: 3.5px dashed #D97706; background: #FEF3C7;">DOC BROWN (DECOY)</div>
          <div class="word-tile">CHANGE PURSE</div>
          <div class="word-tile">ARCTIC CHAR</div>
          <div class="word-tile">GOOD HEAVENS</div>
          <div class="word-tile">SHIFT DRESS</div>
          <div class="word-tile">GLADIATOR SANDALS</div>
          <div class="word-tile">HOLY SMOKES</div>
          <div class="word-tile">SWING SET</div>
        </div>
        """
    },
    {
        "id": "scene_02_yellow_wwwwwh",
        "act_pill": "ACT 2: 🟨 TIER 1 • EASIEST (Direct Synonyms)",
        "footer_tag": 'Category: "GADZOOKS!"',
        "narration": (
            "Let us begin with Tier One, Direct Synonyms. Category title: Gadzooks! "
            "The Who and What: vintage, colorful exclamations expressing shock, astonishment, or surprise. "
            "Where: Level One, the top yellow banner. "
            "When: solved early by recognizing expressive outbursts that convey mild astonishment without profanity. "
            "Why: the constructor anchors the grid with nostalgic expressions from classic literature and screenplays. "
            "How: confirm each phrase functions as an independent exclamation: Good Heavens, Great Scott, Holy Smokes, and Jiminy Cricket."
        ),
        "content": """
        <div class="tier-banner banner-yellow">
          <span>🟨 TIER 1 • EASIEST (Direct Synonyms)</span>
          <span>CATEGORY: "GADZOOKS!"</span>
        </div>
        <div class="wwwwwh-bento">
          <div class="bento-cell"><div class="bento-label">WHO & WHAT</div><div class="bento-val">Vintage, colorful exclamations expressing shock, astonishment, or surprise.</div></div>
          <div class="bento-cell"><div class="bento-label">WHERE</div><div class="bento-val">Level 1 Yellow Banner; serves as the foundational conceptual anchor of today's grid.</div></div>
          <div class="bento-cell"><div class="bento-label">WHEN TO SOLVE</div><div class="bento-val">Early in your solve; identify standalone emotional interjections of amazement.</div></div>
          <div class="bento-cell"><div class="bento-label">WHY IT EXISTS</div><div class="bento-val">Anchors the puzzle with nostalgic spoken phrases before compound wordplay.</div></div>
          <div class="bento-cell"><div class="bento-label">HOW TO VALIDATE</div><div class="bento-val">Confirm exclamation use: Good Heavens, Great Scott, Holy Smokes, Jiminy Cricket.</div></div>
          <div class="bento-cell"><div class="bento-label">KEY TAKEAWAY</div><div class="bento-val">GREAT SCOTT tempts the movie trap, but functions here as a classic exclamation.</div></div>
        </div>
        """
    },
    {
        "id": "scene_03_yellow_lexicon",
        "act_pill": "ACT 2: 🟨 TIER 1 WORD GUIDE",
        "footer_tag": "Good Heavens • Great Scott • Holy Smokes • Jiminy Cricket",
        "narration": (
            "Here are the word meanings, origins, and examples for Tier One. "
            "Good Heavens, pronounced [ɡʊd ˈhɛv.ənz], a polite expression of surprise, substituting heavens for the divine. In a sentence: Good heavens, look at how quickly the afternoon passed! "
            "Great Scott, pronounced [ɡreɪt skɒt], an outburst of amazement honoring General Winfield Scott, made famous by Doc Brown. In a sentence: Great Scott! You solved today's entire puzzle on your very first try! "
            "Holy Smokes, pronounced [ˈhoʊ.li smoʊks], a colorful American exclamation of shock or excitement. In a sentence: Holy smokes, did you see how fast that shooting star blazed across the sky? "
            "And Jiminy Cricket, pronounced [ˈdʒɪm.ɪ.ni ˈkrɪk.ɪt], a minced oath for Jesus Christ, later Disney's conscience. In a sentence: Jiminy Cricket, that sudden thunderclap shook the entire living room window!"
        ),
        "content": """
        <div class="scene-title" style="font-size: 34px;">Tier 1 Word Meanings & Origins</div>
        <div class="lexicon-card-grid">
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">GOOD HEAVENS</span><span class="lexicon-ipa">[ɡʊd ˈhɛv.ənz]</span></div>
            <div class="lexicon-def">A vintage exclamation expressing surprise, shock, disbelief, or mild consternation.</div>
            <div class="lexicon-etym">Middle English euphemistic substitution for God, invoking celestial heavens.</div>
            <div class="lexicon-sentence">"Good heavens, look at how quickly the afternoon passed!"</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">GREAT SCOTT</span><span class="lexicon-ipa">[ɡreɪt skɒt]</span></div>
            <div class="lexicon-def">An exclamation of astonishment, wonder, or amazement; popularized in Back to the Future.</div>
            <div class="lexicon-etym">19th-century American military salute honoring General Winfield Scott.</div>
            <div class="lexicon-sentence">"Great Scott! You solved today's puzzle without burning a guess!"</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">HOLY SMOKES</span><span class="lexicon-ipa">[ˈhoʊ.li smoʊks]</span></div>
            <div class="lexicon-def">An informal, colorful exclamation of shock, amazement, or bewildered excitement.</div>
            <div class="lexicon-etym">Late 19th-century American colloquial euphemism substituting 'smokes' for sacred terms.</div>
            <div class="lexicon-sentence">"Holy smokes, did you see how fast that shooting star blazed?"</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">JIMINY CRICKET</span><span class="lexicon-ipa">[ˈdʒɪm.ɪ.ni ˈkrɪk.ɪt]</span></div>
            <div class="lexicon-def">A mild, polite exclamation of surprise or bewilderment, later immortalized as Pinocchio's conscience.</div>
            <div class="lexicon-etym">Late 19th-century English minced oath; later Disney's iconic cricket.</div>
            <div class="lexicon-sentence">"Jiminy Cricket, that sudden thunderclap shook the entire window!"</div>
          </div>
        </div>
        """
    },
    {
        "id": "scene_04_green_wwwwwh",
        "act_pill": "ACT 3: 🟩 TIER 2 • MODERATE (Contextual Link)",
        "footer_tag": "Category: Starting With Variations",
        "narration": (
            "Next is Tier Two, Contextual Links. Category title: Starting With Variations. "
            "Who and What: compound nouns or phrases whose opening words are direct synonyms for fluctuation, alteration, or change. "
            "Where: Level Two, the green banner. "
            "When: identified when you isolate the first word of each two-word term. "
            "Why: tests your ability to spot shared meanings hidden at the head of everyday phrases. "
            "How: test the leading words: Change in Change Purse, Flux in Flux Capacitor, Shift in Shift Dress, and Swing in Swing Set."
        ),
        "content": """
        <div class="tier-banner banner-green">
          <span>🟩 TIER 2 • MODERATE (Contextual Link)</span>
          <span>CATEGORY: STARTING WITH VARIATIONS</span>
        </div>
        <div class="wwwwwh-bento">
          <div class="bento-cell"><div class="bento-label">WHO & WHAT</div><div class="bento-val">Compound terms whose opening words are synonyms for fluctuation, alteration, or change.</div></div>
          <div class="bento-cell"><div class="bento-label">WHERE</div><div class="bento-val">Level 2 Green Banner; tests vocabulary breadth across compound word heads.</div></div>
          <div class="bento-cell"><div class="bento-label">WHEN TO SOLVE</div><div class="bento-val">Identifiable once you isolate the opening word of each multi-word phrase.</div></div>
          <div class="bento-cell"><div class="bento-label">WHY IT EXISTS</div><div class="bento-val">Hides dynamic synonyms (Change, Flux, Shift, Swing) inside unrelated objects.</div></div>
          <div class="bento-cell"><div class="bento-label">HOW TO VALIDATE</div><div class="bento-val">Check opening synonyms: Change Purse, Flux Capacitor, Shift Dress, Swing Set.</div></div>
          <div class="bento-cell"><div class="bento-label">KEY TAKEAWAY</div><div class="bento-val">FLUX CAPACITOR looks cinematic, but its opening word 'Flux' solves Green.</div></div>
        </div>
        """
    },
    {
        "id": "scene_05_green_lexicon",
        "act_pill": "ACT 3: 🟩 TIER 2 WORD GUIDE",
        "footer_tag": "Change Purse • Flux Capacitor • Shift Dress • Swing Set",
        "narration": (
            "Looking at the variation terms in context: "
            "Change Purse, pronounced [ˈtʃeɪndʒ pɜːrs], from Old French changier, a small clasp pouch for loose coins. In a sentence: She popped open the polished brass clasp of her leather change purse. "
            "Flux Capacitor, pronounced [flʌks kəˈpæs.ɪ.tər], from Latin fluxus, a flowing, the DeLorean's core time device. In a sentence: Doc Brown famously sketched the schematic of the flux capacitor after hitting his head. "
            "Shift Dress, pronounced [ʃɪft drɛs], from Old English sciftan, a straight-cut dress hanging loose from the shoulders. In a sentence: She chose a comfortable linen shift dress for the warm summer luncheon. "
            "And Swing Set, pronounced [swɪŋ sɛt], from Old English swingan, an outdoor playground frame with suspended seats. In a sentence: Eager school children raced across the grass toward the playground's tall swing set."
        ),
        "content": """
        <div class="scene-title" style="font-size: 34px;">Tier 2 Word Meanings & Origins</div>
        <div class="lexicon-card-grid">
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">CHANGE PURSE</span><span class="lexicon-ipa">[ˈtʃeɪndʒ pɜːrs]</span></div>
            <div class="lexicon-def">A small clasp wallet designed for carrying loose coins. First word CHANGE means variation.</div>
            <div class="lexicon-etym">Old French changier (to alter, vary) + Middle English purse (pouch).</div>
            <div class="lexicon-sentence">"She popped open the polished brass clasp of her leather change purse."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">FLUX CAPACITOR</span><span class="lexicon-ipa">[flʌks kəˈpæs.ɪ.tər]</span></div>
            <div class="lexicon-def">The fictional time-travel core of the DeLorean. First word FLUX denotes continuous flow or change.</div>
            <div class="lexicon-etym">Latin fluxus (a flowing, alteration) + capacitas (capacity).</div>
            <div class="lexicon-sentence">"Doc Brown famously sketched the schematic of the flux capacitor."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">SHIFT DRESS</span><span class="lexicon-ipa">[ʃɪft drɛs]</span></div>
            <div class="lexicon-def">A classic straight-cut dress hanging loose without a fitted waistline. First word SHIFT means change.</div>
            <div class="lexicon-etym">Old English sciftan (to divide, arrange, change direction).</div>
            <div class="lexicon-sentence">"She chose a comfortable linen shift dress for the warm luncheon."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">SWING SET</span><span class="lexicon-ipa">[swɪŋ sɛt]</span></div>
            <div class="lexicon-def">An outdoor playground frame with suspended seats. First word SWING represents oscillation.</div>
            <div class="lexicon-etym">Old English swingan (to toss, oscillate, sway back and forth).</div>
            <div class="lexicon-sentence">"Eager school children raced across the grass toward the tall swing set."</div>
          </div>
        </div>
        """
    },
    {
        "id": "scene_06_blue_wwwwwh",
        "act_pill": "ACT 4: 🟦 TIER 3 • CHALLENGING (Trivia & Patterns)",
        "footer_tag": "Category: Ending In Ways To Cook Things",
        "narration": (
            "Now to Tier Three, Trivia and Shared Patterns. Category title: Ending In Ways To Cook Things. "
            "Who and What: two-word phrases whose final words are recognized culinary methods for preparing food. "
            "Where: Level Three, the blue banner. "
            "When: recognized by focusing on the tail ends of phrases rather than their literal meanings. "
            "Why: combines fish, comedy specials, movie characters, and slang idioms to camouflage the culinary pattern. "
            "How: inspect the second word of each phrase: Char in Arctic Char, Roast in Comedy Roast, Brown in Doc Brown, and Toast in You're Toast."
        ),
        "content": """
        <div class="tier-banner banner-blue">
          <span>🟦 TIER 3 • CHALLENGING (Trivia & Patterns)</span>
          <span>CATEGORY: ENDING IN WAYS TO COOK THINGS</span>
        </div>
        <div class="wwwwwh-bento">
          <div class="bento-cell"><div class="bento-label">WHO & WHAT</div><div class="bento-val">Compound terms whose final words are recognized culinary methods for preparing food.</div></div>
          <div class="bento-cell"><div class="bento-label">WHERE</div><div class="bento-val">Level 3 Blue Banner; tests pattern recognition on phrase endings across genres.</div></div>
          <div class="bento-cell"><div class="bento-label">WHEN TO SOLVE</div><div class="bento-val">Recognizable once you shift attention from overall meanings to tail words.</div></div>
          <div class="bento-cell"><div class="bento-label">WHY IT EXISTS</div><div class="bento-val">Blends subpolar fish, comedy roasts, and movie names to mask the cooking theme.</div></div>
          <div class="bento-cell"><div class="bento-label">HOW TO VALIDATE</div><div class="bento-val">Check culinary endings: Char (Arctic Char), Roast (Comedy Roast), Brown (Doc Brown), Toast (You're Toast).</div></div>
          <div class="bento-cell"><div class="bento-label">KEY TAKEAWAY</div><div class="bento-val">DOC BROWN tempts the sci-fi trap, but its culinary ending 'Brown' anchors Blue.</div></div>
        </div>
        """
    },
    {
        "id": "scene_07_blue_lexicon",
        "act_pill": "ACT 4: 🟦 TIER 3 WORD GUIDE",
        "footer_tag": "Arctic Char • Comedy Roast • Doc Brown • You're Toast",
        "narration": (
            "Here are the word meanings and examples for Tier Three: Ending In Ways To Cook Things. "
            "Arctic Char, pronounced [ˈɑːrk.tɪk tʃɑːr], ending in CHAR, a dry heat cooking method. In a sentence: The dinner menu featured pan-seared Arctic char served over roasted autumn vegetables. "
            "Comedy Roast, pronounced [ˈkɒm.ə.di roʊst], ending in ROAST, an oven cooking method. In a sentence: Fellow comedians gathered on stage for the annual charity comedy roast, exchanging affectionate jabs. "
            "Doc Brown, pronounced [dɒk braʊn], ending in BROWN, cooking food until golden. In a sentence: Doc Brown adjusted his protective welding goggles before routing electricity into the vehicle. "
            "And You're Toast, pronounced [jʊər toʊst], ending in TOAST, browning via radiant heat. In a sentence: If the head coach catches you arriving late to scrimmage, you're toast!"
        ),
        "content": """
        <div class="scene-title" style="font-size: 34px;">Tier 3 Word Meanings & Origins</div>
        <div class="lexicon-card-grid">
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">ARCTIC CHAR</span><span class="lexicon-ipa">[ˈɑːrk.tɪk tʃɑːr]</span></div>
            <div class="lexicon-def">A cold-water fish of the salmon family. Ends in CHAR, a high-heat browning method.</div>
            <div class="lexicon-etym">Greek arktikos (northern) + Celtic ceara + Middle English charen (to scorch).</div>
            <div class="lexicon-sentence">"The menu featured pan-seared Arctic char over roasted vegetables."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">COMEDY ROAST</span><span class="lexicon-ipa">[ˈkɒm.ə.di roʊst]</span></div>
            <div class="lexicon-def">A banquet teasing an honored guest with witty insults. Ends in ROAST, an oven cooking method.</div>
            <div class="lexicon-etym">Greek komoidia + Old French rostir (to brown over dry heat).</div>
            <div class="lexicon-sentence">"Comedians gathered on stage for the annual charity comedy roast."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">DOC BROWN</span><span class="lexicon-ipa">[dɒk braʊn]</span></div>
            <div class="lexicon-def">The eccentric inventor in Back to the Future. Ends in BROWN, to cook until golden.</div>
            <div class="lexicon-etym">Colloquial doctor + Old English brūn (golden-brown surface).</div>
            <div class="lexicon-sentence">"Doc Brown adjusted his protective welding goggles before the test."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">YOU'RE TOAST</span><span class="lexicon-ipa">[jʊər toʊst]</span></div>
            <div class="lexicon-def">A colloquial warning that someone is in severe trouble. Ends in TOAST, browned via radiant heat.</div>
            <div class="lexicon-etym">Latin torrere (to scorch) via Old French toster; 1980s American idiom.</div>
            <div class="lexicon-sentence">"If the head coach catches you arriving late, you're toast!"</div>
          </div>
        </div>
        """
    },
    {
        "id": "scene_08_purple_wwwwwh",
        "act_pill": "ACT 5: 🟪 TIER 4 • TRICKIEST (Lateral Wordplay)",
        "footer_tag": "Category: Starting With Best Picture Oscar Winners",
        "narration": (
            "Finally, Tier Four, Lateral Wordplay. Category title: Starting With Best Picture Oscar Winners. "
            "Who and What: famous compound terms and proper names whose first words match Academy Award Best Picture winning films. "
            "Where: Level Four, the purple banner. "
            "When: solved by linking cinematic history to everyday compounds. "
            "Why: the constructor challenges solvers to connect ancient warriors, teenage travelers, classical music, and ice cream through Hollywood's highest prize. "
            "How: identify the Oscar winners: Gladiator from 2000 in Gladiator Sandals, Marty from 1955 in Marty McFly, Moonlight from 2016 in Moonlight Sonata, and Rocky from 1976 in Rocky Road."
        ),
        "content": """
        <div class="tier-banner banner-purple">
          <span>🟪 TIER 4 • TRICKIEST (Lateral Wordplay)</span>
          <span>CATEGORY: STARTING WITH BEST PICTURE OSCAR WINNERS</span>
        </div>
        <div class="wwwwwh-bento">
          <div class="bento-cell"><div class="bento-label">WHO & WHAT</div><div class="bento-val">Compound terms whose first words won the Academy Award for Best Picture.</div></div>
          <div class="bento-cell"><div class="bento-label">WHERE</div><div class="bento-val">Level 4 Purple Banner; the signature cultural trivia and wordplay mechanic of Connections.</div></div>
          <div class="bento-cell"><div class="bento-label">OSCAR WINNERS</div><div class="bento-val">GLADIATOR (2000), MARTY (1955), MOONLIGHT (2016), and ROCKY (1976).</div></div>
          <div class="bento-cell"><div class="bento-label">WHY IT EXISTS</div><div class="bento-val">Connects disparate fields (footwear, sci-fi, classical piano, ice cream) via film history.</div></div>
          <div class="bento-cell"><div class="bento-label">HOW TO VALIDATE</div><div class="bento-val">Confirm leading Best Picture titles: Gladiator Sandals, Marty McFly, Moonlight Sonata, Rocky Road.</div></div>
          <div class="bento-cell"><div class="bento-label">KEY TAKEAWAY</div><div class="bento-val">MARTY MCFLY anchors the movie trap, but 'Marty' (1955) completes Purple.</div></div>
        </div>
        """
    },
    {
        "id": "scene_09_purple_lexicon",
        "act_pill": "ACT 5: 🟪 TIER 4 WORD GUIDE",
        "footer_tag": "Gladiator Sandals • Marty McFly • Moonlight Sonata • Rocky Road",
        "narration": (
            "Here are the words starting with Oscar Best Picture winners, along with their meanings and examples: "
            "Gladiator Sandals, pronounced [ˈɡlæd.i.eɪ.tər ˈsæn.dəlz], starting with Gladiator, Best Picture in 2000. In a sentence: She paired her bohemian summer dress with comfortable leather gladiator sandals. "
            "Marty McFly, pronounced [ˈmɑːr.ti məkˈflaɪ], starting with Marty, Best Picture in 1955. In a sentence: Marty McFly grabbed his skateboard and hooked onto a passing pickup truck to reach school. "
            "Moonlight Sonata, pronounced [ˈmuːn.laɪt səˈnɑː.tə], starting with Moonlight, Best Picture in 2016. In a sentence: The concert hall fell silent as the pianist began the gentle chords of Beethoven's Moonlight Sonata. "
            "And Rocky Road, pronounced [ˈrɒk.i roʊd], starting with Rocky, Best Picture in 1976. In a sentence: On a warm summer evening, he enjoyed a generous waffle cone of rocky road ice cream."
        ),
        "content": """
        <div class="scene-title" style="font-size: 34px;">Tier 4 Word Meanings & Origins</div>
        <div class="lexicon-card-grid">
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">GLADIATOR SANDALS</span><span class="lexicon-ipa">[ˈɡlæd.i.eɪ.tər ˈsæn.dəlz]</span></div>
            <div class="lexicon-def">Strappy flat footwear with crisscrossing leather bands. Starts with GLADIATOR (Best Picture, 2000).</div>
            <div class="lexicon-etym">Latin gladiator (swordsman) + Greek sandalion (light leather sole).</div>
            <div class="lexicon-sentence">"She paired her bohemian summer dress with leather gladiator sandals."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">MARTY MCFLY</span><span class="lexicon-ipa">[ˈmɑːr.ti məkˈflaɪ]</span></div>
            <div class="lexicon-def">The teenage protagonist of Back to the Future. Starts with MARTY (Best Picture, 1955).</div>
            <div class="lexicon-etym">Diminutive of Martin + Gaelic Mac an fhleisdeir (arrow maker's son).</div>
            <div class="lexicon-sentence">"Marty McFly grabbed his skateboard to hitch a ride to school."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">MOONLIGHT SONATA</span><span class="lexicon-ipa">[ˈmuːn.laɪt səˈnɑː.tə]</span></div>
            <div class="lexicon-def">Beethoven's beloved Piano Sonata No. 14 in C-sharp minor. Starts with MOONLIGHT (Best Picture, 2016).</div>
            <div class="lexicon-etym">Old English mōna + lēoht + Italian sonata (piece played on an instrument).</div>
            <div class="lexicon-sentence">"The hall fell silent as the pianist began Beethoven's Moonlight Sonata."</div>
          </div>
          <div class="lexicon-card">
            <div class="lexicon-top"><span class="lexicon-word">ROCKY ROAD</span><span class="lexicon-ipa">[ˈrɒk.i roʊd]</span></div>
            <div class="lexicon-def">An iconic ice cream flavor with chocolate, marshmallows, and nuts. Starts with ROCKY (Best Picture, 1976).</div>
            <div class="lexicon-etym">Old English rocc (crag, stone) + Old English rād (journey, highway).</div>
            <div class="lexicon-sentence">"On a warm summer evening, he enjoyed a waffle cone of rocky road ice cream."</div>
          </div>
        </div>
        """
    },
    {
        "id": "scene_10_solved_and_scratchboard",
        "act_pill": "ACT 6: BOARD SUMMARY & REVIEW",
        "footer_tag": "Zero-Risk Scratchboard • connectionsassistant.com",
        "narration": (
            "And with that, Puzzle twelve fifty is completely resolved. "
            "Yellow: Gadzooks! Green: Starting With Variations. Blue: Ending In Ways To Cook Things. And Purple: Starting With Best Picture Oscar Winners. "
            "To test your candidate groupings every morning without burning your four guesses, visit connectionsassistant.com. "
            "Subscribe for daily video guides, and enjoy your morning puzzle."
        ),
        "content": """
        <div class="scene-title">Final Board Resolution & Summary</div>
        <div class="scene-subtitle">Puzzle #1250 Clean 4-Tier Solved State</div>
        <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
          <div class="tier-banner banner-yellow" style="margin: 0; padding: 10px 16px; font-size: 16px;">
            <span>🟨 "GADZOOKS!": GOOD HEAVENS, GREAT SCOTT, HOLY SMOKES, JIMINY CRICKET</span>
          </div>
          <div class="tier-banner banner-green" style="margin: 0; padding: 10px 16px; font-size: 16px;">
            <span>🟩 STARTING WITH VARIATIONS: CHANGE PURSE, FLUX CAPACITOR, SHIFT DRESS, SWING SET</span>
          </div>
          <div class="tier-banner banner-blue" style="margin: 0; padding: 10px 16px; font-size: 16px;">
            <span>🟦 ENDING IN WAYS TO COOK THINGS: ARCTIC CHAR, COMEDY ROAST, DOC BROWN, YOU'RE TOAST</span>
          </div>
          <div class="tier-banner banner-purple" style="margin: 0; padding: 10px 16px; font-size: 16px;">
            <span>🟪 STARTING WITH BEST PICTURE OSCAR WINNERS: GLADIATOR SANDALS, MARTY MCFLY, MOONLIGHT SONATA, ROCKY ROAD</span>
          </div>
        </div>
        <div style="background: #FFFFFF; border: 3.5px solid #1A1A1A; border-radius: 14px; box-shadow: 0 5px 0 #1A1A1A; padding: 18px 24px; text-align: center;">
          <h3 style="font-family: 'Fraunces', serif; font-size: 24px; margin-bottom: 6px;">Test Candidate Groups on the Free Scratchboard</h3>
          <p style="font-size: 16px; color: #4B5563; font-weight: 600;">connectionsassistant.com &bull; Zero external API dependencies &bull; 100% Free</p>
        </div>
        """
    }
]

async def synthesize_speech(text: str, raw_path: Path, eq_path: Path):
    """Synthesize speech using Edge-TTS with pitch/rate and apply FFmpeg low-shelf EQ."""
    communicate = edge_tts.Communicate(text, VOICE_NAME, rate=VOICE_RATE, pitch=VOICE_PITCH)
    await communicate.save(str(raw_path))

    # Apply FFmpeg low-shelf EQ (bass=g=3.5:f=110)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_path),
        "-af", EQ_FILTER,
        str(eq_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[-] FFmpeg EQ error on {raw_path.name}: {res.stderr}")
        eq_path.write_bytes(raw_path.read_bytes())


async def render_slide(page, html_content: str, output_path: Path):
    """Render 1920x1080 slide image using Playwright."""
    await page.set_content(html_content, wait_until="networkidle")
    await page.wait_for_timeout(300)
    await page.screenshot(path=str(output_path), full_page=False)


def get_audio_duration(file_path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(file_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(res.stdout.strip())
    except Exception:
        return 5.0


def compile_segment(image_path: Path, audio_path: Path, output_path: Path, duration: float):
    """Compile image + audio segment into MP4 using NVENC or libx264."""
    cmd_nvenc = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "h264_nvenc", "-preset", "p4", "-b:v", "6M",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]
    res = subprocess.run(cmd_nvenc, capture_output=True, text=True)
    if res.returncode != 0:
        cmd_cpu = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.3f}",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_path)
        ]
        subprocess.run(cmd_cpu, check=True)


def concatenate_segments(segment_paths: list[Path], final_path: Path):
    """Concatenate all scene MP4 segments into the final video."""
    concat_list = TEMP_DIR / "concat_list.txt"
    lines = [f"file '{p.resolve().as_posix()}'" for p in segment_paths]
    concat_list.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(final_path)
    ]
    subprocess.run(cmd, check=True)


def write_video_metadata(puzzle_file: Path = BASE_DIR / "daily_puzzle.json"):
    """Write standardized description and tags metadata for the long-form masterclass."""
    data = {}
    if puzzle_file.exists():
        with open(puzzle_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    pdate = data.get("date", "2026-11-14")
    pid = data.get("id", data.get("puzzle_number", "1252"))

    from datetime import datetime
    try:
        dt = datetime.strptime(pdate, "%Y-%m-%d")
        full_date_str = f"{dt.strftime('%A')} {dt.strftime('%b')} {dt.day}, {dt.year}"
        date_short = f"{dt.strftime('%b')} {dt.day}, {dt.year}"
    except Exception:
        full_date_str = pdate
        date_short = pdate

    cats = data.get("categories", [])
    y = cats[0] if len(cats) > 0 else {}
    g = cats[1] if len(cats) > 1 else {}
    b = cats[2] if len(cats) > 2 else {}
    p = cats[3] if len(cats) > 3 else {}

    y_title = y.get("title", "USE THE INTERNET")
    g_title = g.get("title", "MEDIA ATTENTION")
    b_title = b.get("title", "THINGS THAT ARE TOWED")
    p_title = p.get("title", "BRAIN ___")

    y_words = ", ".join(y.get("words", []))
    g_words = ", ".join(g.get("words", []))
    b_words = ", ".join(b.get("words", []))
    p_words = ", ".join(p.get("words", []))

    title = f"Todays NYT Connections Explained ({date_short}) | Full Solution & Word Meanings (#{pid})"
    desc = f"""Step-by-step walkthrough and 16-word guide for today's NYT Connections ({full_date_str} • Puzzle #{pid}).

☕ TODAY'S 4-TIER BREAKDOWN:
🟨 TIER 1 • EASIEST (Direct Synonyms): {y_title}
   • Words that share the same direct meaning or action.
   • Words: {y_words}

🟩 TIER 2 • MODERATE (Contextual Link): {g_title}
   • Connected by a common public, broadcasting, or news theme.
   • Words: {g_words}

🟦 TIER 3 • CHALLENGING (Trivia & Patterns): {b_title}
   • Vehicles, vessels, or sports equipment pulled behind another vehicle.
   • Words: {b_words}

🟪 TIER 4 • TRICKIEST (Lateral Wordplay): {p_title}
   • Compound phrases and idioms completing the lateral wordplay pattern!
   • Words: {p_words}

⚠️ TODAY'S SNEAKY DECOY TRAPS:
Watch out for BATTLE tempting an immediate military / warfare combat grouping with CHESS, GO, and STRATEGO! Every single one belongs to a completely different tier: BATTLE is baby gear with its first letter changed (Purple), while CHESS, GO, and STRATEGO are strategy board games (Blue). Also beware of COMPLEX and ADVANCED tempting an intricate / difficult trap!

🧩 PRACTICE TODAY'S 16 WORDS RISK-FREE (ZERO SPOILERS):
Copy, paste, or 1-click fill today's 16 words onto our free practice scratchboard without burning your 4 NYT guesses:
https://connectionsassistant.com/

📖 FULL 16-WORD MEANINGS & DAILY ARCHIVE:
https://connectionsassistant.com/breakdowns.html

TIMESTAMPS:
0:00 - Introduction & Decoy Trap Alert
0:35 - Act 2: 🟨 TIER 1 • EASIEST ({y_title})
1:10 - Tier 1 Words: {y_words}
2:13 - Act 3: 🟩 TIER 2 • MODERATE ({g_title})
2:50 - Tier 2 Words: {g_words}
3:45 - Act 4: 🟦 TIER 3 • CHALLENGING ({b_title})
4:22 - Tier 3 Words: {b_words}
5:16 - Act 5: 🟪 TIER 4 • TRICKIEST ({p_title})
5:53 - Tier 4 Words: {p_words}
6:39 - Act 6: Solved Board Recap & Scratchboard Strategy

#NYTConnections #ConnectionsHints #WordPuzzle #BrainTeaser #Etymology #Vocabulary #KeepSharp #SeniorGames
"""
    tags = "NYT Connections, Connections hints today, Connections solution today, Connections Assistant, NYT Connections guide, word puzzle, Rangsk, Connections Rangsk, vocabulary, word origins, keep sharp, senior brain games"
    comment = "🧩 Practice today's 16 words risk-free (Zero Spoilers) on our Copy/Paste Scratchboard: https://connectionsassistant.com/ | Full word origins & breakdowns: https://connectionsassistant.com/breakdowns.html"

    content = f"""======================================================================
DROP 3: DAILY LONG-FORM MASTERCLASS & WORD GUIDE METADATA
======================================================================
VIDEO FILE:     {FINAL_VIDEO}
THUMBNAIL FILE: {OUTPUT_DIR / "today_deep_dive_thumbnail.png"}

------------------- VIDEO TITLE -------------------
{title}

------------------- DESCRIPTION -------------------
{desc}

----------------- PINNED COMMENT -----------------
{comment}

---------------------- TAGS ----------------------
{tags}
"""
    METADATA_FILE.write_text(content, encoding="utf-8")
    print(f"[✓] Metadata staged to {METADATA_FILE.name}")


async def main():
    print("======================================================================")
    print("  CONNECTIONS ASSISTANT: DAILY LONG-FORM DEEP DIVE VIDEO GENERATOR    ")
    print("  Thursday, Nov 12, 2026 (Puzzle #1250)                               ")
    print("  British Sub-Baritone Audio Calibration (en-GB-RyanNeural -8Hz -2%)  ")
    print("======================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        segment_files = []

        for idx, scene in enumerate(SCENES, 1):
            sid = scene["id"]
            print(f"\n[+] Processing Scene {idx}/{len(SCENES)}: {sid}...")

            # 1. Generate HTML & Render Slide
            html = (
                SLIDE_TEMPLATE
                .replace("{act_pill}", scene["act_pill"])
                .replace("{main_content}", scene["content"])
                .replace("{footer_tag}", scene["footer_tag"])
            )
            slide_img = TEMP_DIR / f"{sid}.png"
            await render_slide(page, html, slide_img)
            print(f"    [✓] Slide rendered: {slide_img.name}")

            # 2. Synthesize Speech & Apply EQ
            raw_audio = TEMP_DIR / f"{sid}_raw.mp3"
            eq_audio = TEMP_DIR / f"{sid}_eq.mp3"
            await synthesize_speech(scene["narration"], raw_audio, eq_audio)
            duration = get_audio_duration(eq_audio) + 0.5  # slight tail padding
            print(f"    [✓] Audio synthesized with sub-baritone EQ ({duration:.2f}s)")

            # 3. Compile Segment MP4
            segment_mp4 = TEMP_DIR / f"{sid}.mp4"
            compile_segment(slide_img, eq_audio, segment_mp4, duration)
            segment_files.append(segment_mp4)
            print(f"    [✓] Segment compiled: {segment_mp4.name}")

        await browser.close()

    # 4. Concatenate Final MP4
    print(f"\n[+] Concatenating {len(segment_files)} segments into final video...")
    concatenate_segments(segment_files, FINAL_VIDEO)
    print(f"[✓] Final Masterclass Video compiled successfully -> {FINAL_VIDEO}")

    # 5. Write Video Metadata
    write_video_metadata()
    print("[✓] Pipeline execution finished cleanly.")


if __name__ == "__main__":
    asyncio.run(main())
