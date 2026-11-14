import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
import edge_tts
from playwright.async_api import async_playwright

# ==============================================================================
# MASTERCLASS CONFIGURATION & PATHS
# ==============================================================================
BASE_DIR = Path(r"C:\Users\Infinite\Documents\Connections Grouping Assistant")
OUTPUT_DIR = BASE_DIR / "output_masterclass"
TEMP_DIR = OUTPUT_DIR / "temp"
FINAL_VIDEO = OUTPUT_DIR / "masterclass_definitive_guide.mp4"

VOICE_NAME = "en-US-ChristopherNeural"
VOICE_RATE = "+10%"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# MASTER NEO-BRUTALIST HTML TEMPLATE (1920x1080)
# ==============================================================================
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Plus+Jakarta+Sans:wght@600;700;800&family=JetBrains+Mono:wght@700;800&display=swap');

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    width: 1920px;
    height: 1080px;
    background-color: #FAF8F5; /* Warm Alabaster */
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #1A1A1A;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 44px 72px;
    overflow: hidden;
  }

  /* Header Bar */
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 18px;
    box-shadow: 0 6px 0 #1A1A1A;
    padding: 18px 36px;
  }
  .brand {
    font-family: 'Fraunces', serif;
    font-size: 30px;
    font-weight: 900;
    letter-spacing: -0.02em;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .brand-badge {
    background: #1A1A1A;
    color: #FFFFFF;
    font-size: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 6px;
    letter-spacing: 0.05em;
  }
  .act-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 17px;
    font-weight: 800;
    background: #FEF9C3;
    border: 2.5px solid #1A1A1A;
    padding: 8px 22px;
    border-radius: 999px;
    box-shadow: 0 3px 0 #1A1A1A;
    letter-spacing: 0.03em;
  }

  /* Main Canvas Area */
  main {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin: 22px 0;
  }

  .scene-header {
    text-align: center;
    margin-bottom: 24px;
  }
  .scene-title {
    font-family: 'Fraunces', serif;
    font-size: 42px;
    font-weight: 900;
    line-height: 1.15;
    letter-spacing: -0.02em;
    margin-bottom: 8px;
  }
  .scene-subtitle {
    font-size: 21px;
    font-weight: 600;
    color: #4B5563;
  }

  /* Universal Tile Styling */
  .tile {
    background: #FFFFFF;
    border: 3px solid #1A1A1A;
    border-radius: 12px;
    box-shadow: 0 5px 0 #1A1A1A;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: clip;
    padding: 4px 10px;
  }

  /* Scene 1: 4x4 Grid */
  .grid-16 {
    display: grid;
    grid-template-columns: repeat(4, 210px);
    grid-gap: 14px;
    background: #FFFFFF;
    padding: 24px;
    border: 3.5px solid #1A1A1A;
    border-radius: 20px;
    box-shadow: 0 8px 0 #1A1A1A;
  }
  .grid-16 .tile {
    height: 82px;
    font-size: 20px;
    background: #F3F0E6;
  }
  .insight-banner {
    margin-top: 20px;
    background: #FEF9C3;
    border: 3px solid #1A1A1A;
    border-radius: 14px;
    padding: 14px 28px;
    font-size: 19px;
    font-weight: 700;
    box-shadow: 0 4px 0 #1A1A1A;
    text-align: center;
    max-width: 920px;
  }

  /* Scene 2: Polysemy Breakdown */
  .polysemy-layout {
    display: grid;
    grid-template-columns: 320px 1fr;
    grid-gap: 32px;
    align-items: center;
    width: 100%;
    max-width: 1560px;
    margin: 0 auto;
  }
  .anchor-card {
    background: #FFFFFF;
    border: 4px solid #1A1A1A;
    border-radius: 22px;
    box-shadow: 0 8px 0 #1A1A1A;
    padding: 36px 24px;
    text-align: center;
  }
  .anchor-word {
    font-family: 'Fraunces', serif;
    font-size: 58px;
    font-weight: 900;
    background: #F9DF6D;
    border: 3px solid #1A1A1A;
    border-radius: 14px;
    padding: 12px;
    box-shadow: 0 4px 0 #1A1A1A;
    margin-bottom: 14px;
  }
  .anchor-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 16px;
    font-weight: 700;
    color: #4B5563;
  }
  .domain-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    grid-gap: 16px;
  }
  .domain-card {
    background: #FFFFFF;
    border: 3px solid #1A1A1A;
    border-radius: 14px;
    box-shadow: 0 5px 0 #1A1A1A;
    padding: 16px 20px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .domain-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 800;
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1.5px solid #1A1A1A;
    width: fit-content;
  }
  .domain-name {
    font-family: 'Fraunces', serif;
    font-size: 22px;
    font-weight: 900;
  }
  .domain-desc {
    font-size: 16px;
    color: #374151;
    font-weight: 600;
  }

  /* Scene 3: 4-Tier Spectrum */
  .tier-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-gap: 20px;
    width: 100%;
  }
  .tier-card {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 18px;
    box-shadow: 0 7px 0 #1A1A1A;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 480px;
  }
  .tier-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 800;
    padding: 8px 12px;
    border-radius: 8px;
    border: 2px solid #1A1A1A;
    text-align: center;
    margin-bottom: 12px;
  }
  .tier-title {
    font-family: 'Fraunces', serif;
    font-size: 26px;
    font-weight: 900;
    margin-bottom: 8px;
  }
  .tier-desc {
    font-size: 16px;
    line-height: 1.45;
    color: #374151;
    font-weight: 600;
  }
  .tier-samples {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
    margin-top: 14px;
  }
  .tier-pill {
    font-size: 14px;
    font-weight: 800;
    padding: 7px 8px;
    border-radius: 8px;
    border: 2px solid #1A1A1A;
    background: #FAF8F5;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
  }
  .badge-yellow { background: #F9DF6D; }
  .badge-green  { background: #A0C35A; }
  .badge-blue   { background: #B0C4EF; }
  .badge-purple { background: #BA81C5; color: #FFFFFF; border-color: #6B21A8; }
  .purple-border { border-color: #6B21A8; box-shadow: 0 7px 0 #4C1D95; }

  /* Scene 4 & 5: Split Comparison Cards */
  .split-comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 28px;
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
  }
  .comp-card {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 20px;
    box-shadow: 0 8px 0 #1A1A1A;
    padding: 30px 28px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 480px;
  }
  .comp-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  .comp-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 8px;
    border: 2px solid #1A1A1A;
  }
  .comp-title {
    font-family: 'Fraunces', serif;
    font-size: 30px;
    font-weight: 900;
    margin-bottom: 6px;
  }
  .comp-theme {
    font-family: 'JetBrains Mono', monospace;
    font-size: 17px;
    font-weight: 700;
    color: #1A1A1A;
    margin-bottom: 16px;
  }
  .comp-tiles {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-gap: 10px;
    margin-bottom: 18px;
  }
  .comp-tiles .tile {
    height: 64px;
    font-size: 16px;
  }
  .comp-rule {
    background: #FAF8F5;
    border: 2.5px solid #1A1A1A;
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 16px;
    line-height: 1.45;
    font-weight: 600;
    color: #1F2937;
  }

  /* Scene 6: Decoy Math */
  .trap-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 22px;
    width: 100%;
    max-width: 1480px;
    margin: 0 auto;
  }
  .trap-banner {
    background: #FEF9C3;
    border: 3.5px solid #1A1A1A;
    border-left: 14px solid #CA8A04;
    border-radius: 18px;
    box-shadow: 0 7px 0 #1A1A1A;
    padding: 24px 36px;
    width: 100%;
  }
  .trap-banner h2 {
    font-family: 'Fraunces', serif;
    font-size: 32px;
    font-weight: 900;
    margin-bottom: 8px;
  }
  .trap-banner p {
    font-size: 19px;
    font-weight: 600;
    color: #374151;
  }
  .five-tiles-row {
    display: flex;
    gap: 14px;
    justify-content: center;
    width: 100%;
  }
  .five-tiles-row .tile {
    width: 220px;
    height: 78px;
    font-size: 19px;
  }
  .decoy-math-box {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-gap: 20px;
    width: 100%;
  }
  .math-stat {
    background: #FFFFFF;
    border: 3px solid #1A1A1A;
    border-radius: 14px;
    box-shadow: 0 5px 0 #1A1A1A;
    padding: 20px;
    text-align: center;
  }
  .math-stat .val {
    font-family: 'Fraunces', serif;
    font-size: 38px;
    font-weight: 900;
    margin-bottom: 4px;
  }
  .math-stat .lbl {
    font-size: 15px;
    font-weight: 700;
    color: #4B5563;
  }

  /* Scene 7: Case Study CUT */
  .case-study-grid {
    display: grid;
    grid-template-columns: 1fr 280px 1fr;
    grid-gap: 20px;
    align-items: center;
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
  }
  .cluster-card {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 18px;
    box-shadow: 0 7px 0 #1A1A1A;
    padding: 26px 22px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }
  .cluster-header {
    font-family: 'Fraunces', serif;
    font-size: 24px;
    font-weight: 900;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .cluster-tiles {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 10px;
  }
  .cluster-tiles .tile {
    height: 60px;
    font-size: 16px;
  }
  .hinge-column {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 12px;
  }
  .hinge-tile {
    background: #F9DF6D;
    border: 4px solid #1A1A1A;
    border-radius: 16px;
    box-shadow: 0 8px 0 #1A1A1A;
    width: 220px;
    height: 90px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Fraunces', serif;
    font-size: 34px;
    font-weight: 900;
  }
  .hinge-pill {
    background: #1A1A1A;
    color: #FFFFFF;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 999px;
  }

  /* Scene 8: Homophones */
  .homophones-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    grid-gap: 20px;
    width: 100%;
    max-width: 1560px;
    margin: 0 auto;
  }
  .homophone-card {
    background: #FFFFFF;
    border: 3.5px solid #6B21A8;
    border-radius: 18px;
    box-shadow: 0 7px 0 #4C1D95;
    padding: 26px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 12px;
  }
  .homophone-spelling {
    font-family: 'Fraunces', serif;
    font-size: 36px;
    font-weight: 900;
    background: #FAF8F5;
    border: 2.5px solid #1A1A1A;
    border-radius: 12px;
    padding: 10px 20px;
    width: 100%;
  }
  .phonetic-arrow {
    font-size: 22px;
    font-weight: 900;
    color: #6B21A8;
  }
  .homophone-target {
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 800;
    background: #E9D5FF;
    border: 2px solid #6B21A8;
    padding: 8px 16px;
    border-radius: 10px;
    width: 100%;
  }
  .homophone-desc {
    font-size: 15px;
    font-weight: 700;
    color: #4B5563;
  }

  /* Scene 9: Wordplay Patterns */
  .pattern-grid-3 {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-gap: 22px;
    width: 100%;
    max-width: 1600px;
    margin: 0 auto;
  }
  .pattern-box {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 18px;
    box-shadow: 0 7px 0 #1A1A1A;
    padding: 26px 22px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 460px;
  }
  .pattern-tag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 800;
    background: #FEF9C3;
    border: 2px solid #1A1A1A;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    margin-bottom: 10px;
  }
  .pattern-heading {
    font-family: 'Fraunces', serif;
    font-size: 26px;
    font-weight: 900;
    margin-bottom: 8px;
  }
  .pattern-body {
    font-size: 16px;
    font-weight: 600;
    line-height: 1.45;
    color: #374151;
  }
  .pattern-example {
    background: #FAF8F5;
    border: 2px solid #1A1A1A;
    border-radius: 12px;
    padding: 12px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    margin-top: 14px;
  }

  /* Scene 10: Scratchboard Protocol */
  .protocol-matrix {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-gap: 28px;
    width: 100%;
    max-width: 1560px;
    margin: 0 auto;
  }
  .matrix-card {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 20px;
    box-shadow: 0 8px 0 #1A1A1A;
    padding: 30px 28px;
    height: 480px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }
  .matrix-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }
  .matrix-title {
    font-family: 'Fraunces', serif;
    font-size: 28px;
    font-weight: 900;
  }
  .matrix-badge-bad {
    background: #FEE2E2;
    color: #991B1B;
    border: 2px solid #1A1A1A;
    padding: 6px 14px;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 800;
  }
  .matrix-badge-good {
    background: #DCFCE7;
    color: #166534;
    border: 2px solid #1A1A1A;
    padding: 6px 14px;
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 800;
  }
  .matrix-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .matrix-item {
    font-size: 17px;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  /* Scene 11: Assistant Showcase */
  .assistant-grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    grid-gap: 32px;
    align-items: center;
    width: 100%;
    max-width: 1560px;
    margin: 0 auto;
  }
  .features-container {
    background: #FFFFFF;
    border: 3.5px solid #1A1A1A;
    border-radius: 20px;
    box-shadow: 0 8px 0 #1A1A1A;
    padding: 32px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
  .feature-row {
    display: flex;
    align-items: flex-start;
    gap: 14px;
  }
  .feature-icon {
    font-size: 24px;
    background: #FAF8F5;
    border: 2px solid #1A1A1A;
    border-radius: 10px;
    padding: 8px;
    box-shadow: 0 3px 0 #1A1A1A;
  }
  .feature-text h3 {
    font-family: 'Fraunces', serif;
    font-size: 21px;
    font-weight: 900;
    margin-bottom: 2px;
  }
  .feature-text p {
    font-size: 15px;
    font-weight: 600;
    color: #4B5563;
  }
  .cta-card {
    background: #FFFFFF;
    border: 4px solid #1A1A1A;
    border-radius: 22px;
    box-shadow: 0 10px 0 #1A1A1A;
    padding: 40px 32px;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: 18px;
    align-items: center;
  }
  .cta-title {
    font-family: 'Fraunces', serif;
    font-size: 32px;
    font-weight: 900;
    line-height: 1.2;
  }
  .cta-url-pill {
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 900;
    background: #F9DF6D;
    border: 3px solid #1A1A1A;
    padding: 14px 28px;
    border-radius: 14px;
    box-shadow: 0 5px 0 #1A1A1A;
    display: inline-block;
  }

  /* Footer Bar */
  footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 18px;
    font-weight: 700;
    color: #6B7280;
    padding: 0 8px;
  }
  .footer-url {
    font-family: 'JetBrains Mono', monospace;
    font-size: 20px;
    font-weight: 800;
    color: #1A1A1A;
  }
</style>
</head>
<body>

  <header>
    <div class="brand">
      Connections Grouping Assistant
      <span class="brand-badge">MASTERCLASS</span>
    </div>
    <div class="act-pill">{{ACT_BADGE}}</div>
  </header>

  <main>
    <div class="scene-header">
      <div class="scene-title">{{SCENE_TITLE}}</div>
      <div class="scene-subtitle">{{SCENE_SUBTITLE}}</div>
    </div>
    {{SCENE_BODY}}
  </main>

  <footer>
    <div>Master Strategy & Cognitive Frameworks • 1080p Pillar Guide</div>
    <div class="footer-url">connectionsassistant.com</div>
  </footer>

</body>
</html>
"""

# ==============================================================================
# 5-ACT SCENE REGISTRY (~1,200 WORDS / 11 SCENES)
# ==============================================================================
SCENES = [
    # --------------------------------------------------------------------------
    # ACT 1: THE ANATOMY OF A GRID & CONTEXTUAL ELASTICITY
    # --------------------------------------------------------------------------
    {
        "id": 1,
        "act": "ACT 1 • ANATOMY OF A GRID",
        "title": "The Anatomy of a Connections Grid",
        "subtitle": "Sixteen shuffled tiles, four hidden quartets, and the illusion of obviousness.",
        "narration": (
            "Welcome to the definitive masterclass on conquering NYT Connections. Every morning, "
            "sixteen shuffled words appear on the board. On the surface, the rules sound deceptively simple: "
            "sort these sixteen tiles into four groups of four. But if you play purely on intuition, "
            "you are walking directly into a trap laid by the puzzle editor. The human brain is an association engine; "
            "the moment you see words like BAR, CLUB, and RING, your mind immediately leaps to nightlife or jewelry. "
            "Yet in a well-constructed grid, every single word is handpicked because it possesses high contextual elasticity—"
            "operating across multiple parts of speech and completely unrelated semantic domains. "
            "To win consistently and safeguard your streak, you must stop guessing and start deconstructing."
        ),
        "content_html": """
        <div style="display:flex; flex-direction:column; align-items:center;">
          <div class="grid-16">
            <div class="tile">BAR</div><div class="tile">CRANE</div><div class="tile">DRILL</div><div class="tile">FILE</div>
            <div class="tile">MATCH</div><div class="tile">POUND</div><div class="tile">ROW</div><div class="tile">TANK</div>
            <div class="tile">RING</div><div class="tile">SPRING</div><div class="tile">CLUB</div><div class="tile">BOW</div>
            <div class="tile">SHUFFLE</div><div class="tile">MINT</div><div class="tile">TRUNK</div><div class="tile">STAMP</div>
          </div>
          <div class="insight-banner">
            ⚠️ COGNITIVE BIAS TRAP: Intuitive pattern recognition forces solvers into premature guesses before evaluating the whole board.
          </div>
        </div>
        """
    },
    {
        "id": 2,
        "act": "ACT 1 • CONTEXTUAL ELASTICITY",
        "title": "Contextual Elasticity & Polysemy",
        "subtitle": "How single words are weaponized to operate across multiple unrelated domains.",
        "narration": (
            "The core psychological mechanism at play is what cognitive linguists call polysemy: "
            "a single word holding multiple unrelated definitions across distinct domains. Consider a simple word like BAR. "
            "Depending on its neighboring tiles, BAR can represent a legal accreditation exam, an establishment serving beverages, "
            "a physical block of chocolate, an Olympic gymnastics apparatus, or an action verb meaning to forbid access. "
            "When sixteen polysemic words collide on a single board, the possible combinations explode exponentially. "
            "Solvers who fail do not lack vocabulary—they fail because they anchor to the first definition their brain retrieves. "
            "Your first fundamental rule of Connections: never assign a permanent meaning to any tile until you have rigorously tested its competing identities."
        ),
        "content_html": """
        <div class="polysemy-layout">
          <div class="anchor-card">
            <div class="anchor-word">BAR</div>
            <div class="anchor-meta">Single Tile • 5 Distinct Domains</div>
            <div style="margin-top:16px; font-size:15px; font-weight:700; color:#CA8A04;">HIGH CONTEXTUAL ELASTICITY</div>
          </div>
          <div class="domain-grid">
            <div class="domain-card">
              <span class="domain-badge" style="background:#FEF9C3;">⚖️ LEGAL</span>
              <div class="domain-name">Accreditation Exam</div>
              <div class="domain-desc">Passing the bar exam, admitted to practice law.</div>
            </div>
            <div class="domain-card">
              <span class="domain-badge" style="background:#DCFCE7;">🍸 VENUE</span>
              <div class="domain-name">Hospitality Lounge</div>
              <div class="domain-desc">Cocktail bar, tavern, establishment serving drinks.</div>
            </div>
            <div class="domain-card">
              <span class="domain-badge" style="background:#E0E7FF;">🍫 OBJECT</span>
              <div class="domain-name">Physical Ingot / Block</div>
              <div class="domain-desc">Chocolate bar, gold bullion, block of solid soap.</div>
            </div>
            <div class="domain-card">
              <span class="domain-badge" style="background:#FCE7F3;">🤸 ATHLETICS</span>
              <div class="domain-name">Gymnastics Apparatus</div>
              <div class="domain-desc">Horizontal bar, parallel bars, weightlifting barbell.</div>
            </div>
          </div>
        </div>
        """
    },

    # --------------------------------------------------------------------------
    # ACT 2: DEMYSTIFYING THE 4 TIERS
    # --------------------------------------------------------------------------
    {
        "id": 3,
        "act": "ACT 2 • DEMYSTIFYING THE 4 TIERS",
        "title": "The 4-Tier Difficulty Hierarchy",
        "subtitle": "Calibrated by cognitive depth: how far into semantic memory your brain must search.",
        "narration": (
            "NYT Connections is calibrated on a precise four-tier cognitive hierarchy, designated by color. "
            "Solvers often assume this color order is arbitrary, but it actually reflects how deep your brain must search its semantic memory. "
            "Yellow is Tier 1, the most straightforward category. It features direct synonyms or tangible physical attributes. "
            "Green is Tier 2, requiring moderate contextual grouping—words linked by common environments or shared functional roles. "
            "Blue is Tier 3, demanding specialized cultural trivia, compound words, or domain-specific terminology. "
            "And Purple is Tier 4, the infamous lateral tier. Purple completely abandons literal definitions in favor of phonetic wordplay, "
            "orthographic patterns, and cryptic associations. Knowing which tier you are hunting dictates the mental tools you must deploy."
        ),
        "content_html": """
        <div class="tier-row">
          <div class="tier-card">
            <div>
              <div class="tier-badge badge-yellow">TIER 1 • EASIEST</div>
              <div class="tier-title">Yellow Tier</div>
              <div class="tier-desc">Direct synonyms or standard physical attributes requiring minimal lateral interpretation.</div>
            </div>
            <div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:800; color:#854D0E; margin-bottom:6px;">SAMPLE GROUP:</div>
              <div class="tier-samples">
                <span class="tier-pill">SHUFFLE</span><span class="tier-pill">SLIDE</span><span class="tier-pill">SLINK</span><span class="tier-pill">CREEP</span>
              </div>
            </div>
          </div>

          <div class="tier-card">
            <div>
              <div class="tier-badge badge-green">TIER 2 • MODERATE</div>
              <div class="tier-title">Green Tier</div>
              <div class="tier-desc">Contextual links, shared parts of speech, or familiar real-world environments.</div>
            </div>
            <div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:800; color:#3F6212; margin-bottom:6px;">SAMPLE GROUP:</div>
              <div class="tier-samples">
                <span class="tier-pill">HAMMER</span><span class="tier-pill">DRILL</span><span class="tier-pill">WRENCH</span><span class="tier-pill">PLIERS</span>
              </div>
            </div>
          </div>

          <div class="tier-card">
            <div>
              <div class="tier-badge badge-blue">TIER 3 • CHALLENGING</div>
              <div class="tier-title">Blue Tier</div>
              <div class="tier-desc">Trivia subsets, compound roots, pop culture, and specialized domain knowledge.</div>
            </div>
            <div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:800; color:#1E40AF; margin-bottom:6px;">SAMPLE GROUP:</div>
              <div class="tier-samples">
                <span class="tier-pill">POSTAL</span><span class="tier-pill">CREDIT</span><span class="tier-pill">WILD</span><span class="tier-pill">TAR</span>
              </div>
            </div>
          </div>

          <div class="tier-card purple-border">
            <div>
              <div class="tier-badge badge-purple">TIER 4 • TRICKIEST</div>
              <div class="tier-title">Purple Tier</div>
              <div class="tier-desc">Clever wordplay, homophones, palindromes, anagrams, or hidden letter mechanics.</div>
            </div>
            <div>
              <div style="font-family:'JetBrains Mono',monospace; font-size:12px; font-weight:800; color:#6B21A8; margin-bottom:6px;">SAMPLE GROUP:</div>
              <div class="tier-samples">
                <span class="tier-pill">KORN</span><span class="tier-pill">LEAK</span><span class="tier-pill">CARAT</span><span class="tier-pill">CHARD</span>
              </div>
            </div>
          </div>
        </div>
        """
    },
    {
        "id": 4,
        "act": "ACT 2 • MEANING VS. CONTEXT",
        "title": "Yellow vs. Green: Meaning vs. Context",
        "subtitle": "The crucial distinction between interchangeable synonyms and environmental associations.",
        "narration": (
            "Let us examine how Yellow and Green differ in practice. A Yellow category is characterized by direct synonymy. "
            "If the category is 'Move Stealthily,' words like SHUFFLE, SLIDE, SLINK, and CREEP can almost substitute for one another in a sentence. "
            "They share the same grammatical part of speech and denotative meaning. Green, by contrast, relies on contextual association. "
            "Take workshop implements: HAMMER, DRILL, WRENCH, and PLIERS. You cannot substitute a hammer for a drill, but they coexist naturally in a toolbox. "
            "Solvers often confuse Green with Yellow because both feel familiar. The crucial distinction is that Yellow links words by meaning, "
            "while Green links words by environment, function, or real-world circumstance."
        ),
        "content_html": """
        <div class="split-comparison">
          <div class="comp-card" style="border-top:10px solid #F9DF6D;">
            <div>
              <div class="comp-header">
                <div class="comp-title">Yellow Tier</div>
                <span class="comp-badge badge-yellow">DIRECT SYNONYMS</span>
              </div>
              <div class="comp-theme">Theme: "Move Stealthily / Quietly"</div>
              <div class="comp-tiles">
                <div class="tile">SHUFFLE</div><div class="tile">SLIDE</div><div class="tile">SLINK</div><div class="tile">CREEP</div>
              </div>
            </div>
            <div class="comp-rule">
              <strong>Cognitive Rule:</strong> Words can substitute directly in a sentence. They share identical grammatical part of speech and core denotation.
            </div>
          </div>

          <div class="comp-card" style="border-top:10px solid #A0C35A;">
            <div>
              <div class="comp-header">
                <div class="comp-title">Green Tier</div>
                <span class="comp-badge badge-green">CONTEXTUAL FUNCTION</span>
              </div>
              <div class="comp-theme">Theme: "Workshop Hand Tools"</div>
              <div class="comp-tiles">
                <div class="tile">HAMMER</div><div class="tile">DRILL</div><div class="tile">WRENCH</div><div class="tile">PLIERS</div>
              </div>
            </div>
            <div class="comp-rule">
              <strong>Cognitive Rule:</strong> Words are not interchangeable synonyms, but coexist in a shared physical habitat, tool chest, or functional domain.
            </div>
          </div>
        </div>
        """
    },
    {
        "id": 5,
        "act": "ACT 2 • TRIVIA VS. WORDPLAY",
        "title": "Blue vs. Purple: Trivia vs. Wordplay",
        "subtitle": "Moving from general word knowledge and trivia to clever wordplay patterns.",
        "narration": (
            "Moving up the ladder, Blue and Purple require an entirely different cognitive mode. "
            "Blue categories test general knowledge and cultural trivia. Typical Blue patterns include compound affixes—"
            "such as POSTAL, CREDIT, WILD, and TAR, which all precede the word CARD. Alternatively, Blue might group members of a sports team, "
            "movie directors, or geographic features. Purple, however, is where the puzzle editor plays psychological tricks. "
            "Purple ignores what words mean and focuses on how words look or sound. Anagrams, palindromes, words with letters added, "
            "or phonetic homophones like KORN, LEAK, CARAT, and CHARD sounding like corn, leek, carrot, and chard. "
            "When you see words that seem impossible to connect logically, you are almost always staring at Purple."
        ),
        "content_html": """
        <div class="split-comparison">
          <div class="comp-card" style="border-top:10px solid #B0C4EF;">
            <div>
              <div class="comp-header">
                <div class="comp-title">Blue Tier</div>
                <span class="comp-badge badge-blue">KNOWLEDGE & TRIVIA</span>
              </div>
              <div class="comp-theme">Theme: "Words Preceding 'CARD'"</div>
              <div class="comp-tiles">
                <div class="tile">POSTAL</div><div class="tile">CREDIT</div><div class="tile">WILD</div><div class="tile">TAR</div>
              </div>
            </div>
            <div class="comp-rule">
              <strong>Cognitive Rule:</strong> Compound affixes & cultural recall. Requires identifying unstated linguistic anchor terms (Postal Card, Credit Card, etc.).
            </div>
          </div>

          <div class="comp-card purple-border" style="border-top:10px solid #BA81C5;">
            <div>
              <div class="comp-header">
                <div class="comp-title">Purple Tier</div>
                <span class="comp-badge badge-purple">LATERAL WORDPLAY</span>
              </div>
              <div class="comp-theme">Theme: "Vegetable Homophones"</div>
              <div class="comp-tiles">
                <div class="tile">KORN</div><div class="tile">LEAK</div><div class="tile">CARAT</div><div class="tile">CHARD</div>
              </div>
            </div>
            <div class="comp-rule">
              <strong>Cognitive Rule:</strong> Ignores dictionary meanings. Subverts spelling in favor of pure phonetics, hidden affixes, or letterplay.
            </div>
          </div>
        </div>
        """
    },

    # --------------------------------------------------------------------------
    # ACT 3: THE 5-WORD DECOY TRAP & RED HERRING LAW
    # --------------------------------------------------------------------------
    {
        "id": 6,
        "act": "ACT 3 • THE RED HERRING LAW",
        "title": "The Mathematical Trap of the 5th Word",
        "subtitle": "Why guessing when you see five potential matches carries an 80% failure rate.",
        "narration": (
            "Now let us confront the primary cause of lost streaks: the devastating five-word decoy trap. "
            "When scanning a fresh grid, your eyes will frequently spot five words that share an obvious, undeniable theme. "
            "For instance, five animals, five colors, or five pieces of clothing. Most players instinctively select four and hit submit. "
            "This is a mathematical blunder. Five candidates contain five distinct combinations of four words. "
            "Exactly one combination is correct, meaning a blind guess carries an eighty percent chance of failure. "
            "The puzzle editor deliberately places that fifth candidate to exploit solver overconfidence. "
            "Remember the Golden Law of Connections: if you see five words that fit a category, you do not have a category yet—you have a red herring."
        ),
        "content_html": """
        <div class="trap-container">
          <div class="trap-banner">
            <h2>⚠️ The 5-Word Decoy Trap</h2>
            <p>Spotting 5 words sharing an obvious theme is not good luck—it is an intentional cognitive ambush laid by the puzzle editor.</p>
          </div>
          <div class="five-tiles-row">
            <div class="tile">CHESTNUT</div>
            <div class="tile">WALNUT</div>
            <div class="tile">PECAN</div>
            <div class="tile">CASHEW</div>
            <div class="tile" style="background:#FEE2E2; border-color:#DC2626; color:#991B1B;">DOUGHNUT</div>
          </div>
          <div class="decoy-math-box">
            <div class="math-stat">
              <div class="val" style="color:#2563EB;">5</div>
              <div class="lbl">Possible 4-Word Combinations C(5,4)</div>
            </div>
            <div class="math-stat">
              <div class="val" style="color:#16A34A;">1</div>
              <div class="lbl">True Valid Target Combination</div>
            </div>
            <div class="math-stat">
              <div class="val" style="color:#DC2626;">80%</div>
              <div class="lbl">Failure Probability on Random Guess</div>
            </div>
          </div>
        </div>
        """
    },
    {
        "id": 7,
        "act": "ACT 3 • CASE STUDY: TODAY'S OVERLAP",
        "title": "Case Study: The 'CUT' Pivot Hinge",
        "subtitle": "Hair salon services vs. athletic physique in Sunday's live puzzle.",
        "narration": (
            "To see this in action, analyze today's Sunday puzzle. Solvers immediately spotted words relating to hair styling: "
            "TRIM, BLOWOUT, COLOR, EXTENSIONS, and CUT. Five perfect matches. If you blindly lock in CUT with the salon words, "
            "you burn a guess. Why? Because across the board sat another cluster describing a muscular physique: "
            "BUILT, JACKED, and RIPPED. That cluster only has three words—it desperately needs a fourth. "
            "The word CUT is the pivot hinge. It belongs to the physique group, leaving TRIM, BLOWOUT, COLOR, and EXTENSIONS as the true salon quartet. "
            "Whenever you encounter a five-word cluster, stop and search the remaining tiles for an incomplete trio. "
            "The decoy word is always the bridge to another category."
        ),
        "content_html": """
        <div class="case-study-grid">
          <div class="cluster-card">
            <div class="cluster-header">
              <span>Hair Salon Services</span>
              <span class="domain-badge" style="background:#FEF9C3;">4 WORDS</span>
            </div>
            <div class="cluster-tiles">
              <div class="tile">TRIM</div>
              <div class="tile">BLOWOUT</div>
              <div class="tile">COLOR</div>
              <div class="tile">EXTENSIONS</div>
            </div>
            <div style="font-size:14px; font-weight:700; color:#15803D;">✓ Clean 4-word resolution without CUT!</div>
          </div>

          <div class="hinge-column">
            <div class="hinge-pill">THE PIVOT HINGE</div>
            <div class="hinge-tile">CUT</div>
            <div style="font-size:14px; font-weight:700; color:#CA8A04;">Bridges Salon & Fitness</div>
          </div>

          <div class="cluster-card">
            <div class="cluster-header">
              <span>Muscular Physique</span>
              <span class="domain-badge" style="background:#DCFCE7;">NEEDS 4TH WORD</span>
            </div>
            <div class="cluster-tiles">
              <div class="tile">BUILT</div>
              <div class="tile">JACKED</div>
              <div class="tile">RIPPED</div>
              <div class="tile" style="background:#F9DF6D; font-weight:900;">+ CUT</div>
            </div>
            <div style="font-size:14px; font-weight:700; color:#15803D;">✓ CUT completes the trio!</div>
          </div>
        </div>
        """
    },

    # --------------------------------------------------------------------------
    # ACT 4: THE 4 CLASSIC PURPLE MECHANICS
    # --------------------------------------------------------------------------
    {
        "id": 8,
        "act": "ACT 4 • PURPLE MECHANIC: HOMOPHONES",
        "title": "Purple Mechanic #1: Phonetic Homophones",
        "subtitle": "Orthography conceals what phonetics reveals: always whisper the words aloud.",
        "narration": (
            "Let us dissect the four classic Purple mechanics that appear week after week. The first and most frequent is the Phonetic Homophone. "
            "The human eye reads for spelling, but the human ear listens for sound. In today's grid, the editor presented KORN with a K, "
            "LEAK spelled L-E-A-K, CARAT spelled C-A-R-A-T, and CHARD. Read silently, they look like a nu-metal band, a plumbing failure, "
            "a gem metric, and an obscure leafy vegetable. But read them out loud, and their phonetic signatures become unmistakable: "
            "corn, leek, carrot, and chard—homophones of vegetables. Whenever a grid contains strange spellings or proper nouns with unusual orthography, "
            "whisper them out loud. Your ears will catch what your eyes miss."
        ),
        "content_html": """
        <div class="homophones-row">
          <div class="homophone-card">
            <div class="homophone-spelling">KORN</div>
            <div class="phonetic-arrow">↓ sounds like</div>
            <div class="homophone-target">CORN 🌽</div>
            <div class="homophone-desc">Band name masked as grain vegetable</div>
          </div>

          <div class="homophone-card">
            <div class="homophone-spelling">LEAK</div>
            <div class="phonetic-arrow">↓ sounds like</div>
            <div class="homophone-target">LEEK 🥬</div>
            <div class="homophone-desc">Plumbing issue masked as allium vegetable</div>
          </div>

          <div class="homophone-card">
            <div class="homophone-spelling">CARAT</div>
            <div class="phonetic-arrow">↓ sounds like</div>
            <div class="homophone-target">CARROT 🥕</div>
            <div class="homophone-desc">Gemstone unit masked as root vegetable</div>
          </div>

          <div class="homophone-card">
            <div class="homophone-spelling">CHARD</div>
            <div class="phonetic-arrow">↓ sounds like</div>
            <div class="homophone-target">CHARRED 🔥</div>
            <div class="homophone-desc">Leafy green paired via phonetic ambiguity</div>
          </div>
        </div>
        """
    },
    {
        "id": 9,
        "act": "ACT 4 • ADVANCED PURPLE MECHANICS",
        "title": "Purple Mechanics: Blanks, Affixes & Substrings",
        "subtitle": "The structural formulas behind advanced lateral categories.",
        "narration": (
            "The remaining three Purple mechanics follow strict structural formulas. First is the Fill-in-the-Blank, "
            "where four words precede or follow a shared invisible anchor word. For example, FIRE, WATER, PIN, and CHEESE all pair with WHEEL. "
            "Second is Substring Embedding, where words conceal hidden tokens—such as words containing chemical symbols, "
            "zodiac signs, or three-letter animal names embedded within their letters. Third is Orthographic Manipulation, "
            "featuring palindromes, words formed by dropping the first letter, or words that read as other words in reverse. "
            "When standard definitions fail to produce four neat groups, pivot immediately to structural analysis. "
            "Ask yourself: what invisible word completes these tiles, or what hidden sequence is locked inside their spelling?"
        ),
        "content_html": """
        <div class="pattern-grid-3">
          <div class="pattern-box">
            <div>
              <span class="pattern-tag">PATTERN 2</span>
              <div class="pattern-heading">Fill-in-the-Blanks</div>
              <div class="pattern-body">Words that precede or follow an unstated invisible anchor term.</div>
            </div>
            <div class="pattern-example">
              <div>FIRE, WATER, PIN, CHEESE</div>
              <div style="color:#6B21A8; font-weight:800; margin-top:4px;">➔ All precede "WHEEL"</div>
            </div>
          </div>

          <div class="pattern-box">
            <div>
              <span class="pattern-tag">PATTERN 3</span>
              <div class="pattern-heading">Substring Embedding</div>
              <div class="pattern-body">Words concealing hidden tokens (body parts, chemical elements, state codes).</div>
            </div>
            <div class="pattern-example">
              <div>Words containing US States:</div>
              <div style="color:#6B21A8; font-weight:800; margin-top:4px;">➔ CALI-brate, ME-mento, etc.</div>
            </div>
          </div>

          <div class="pattern-box">
            <div>
              <span class="pattern-tag">PATTERN 4</span>
              <div class="pattern-heading">Letter Alterations</div>
              <div class="pattern-body">Palindromes, words spelled backwards, or words missing the first/last letter.</div>
            </div>
            <div class="pattern-example">
              <div>Dropping Initial Letter:</div>
              <div style="color:#6B21A8; font-weight:800; margin-top:4px;">➔ (S)WHEAT, (P)LACE, (C)HEAR</div>
            </div>
          </div>
        </div>
        """
    },

    # --------------------------------------------------------------------------
    # ACT 5: ZERO-RISK SCRATCHBOARD PROTOCOL ON CONNECTIONSASSISTANT.COM
    # --------------------------------------------------------------------------
    {
        "id": 10,
        "act": "ACT 5 • ZERO-RISK SCRATCHBOARD",
        "title": "The Zero-Risk Scratchboard Protocol",
        "subtitle": "Why elite solvers never test uncertain hypotheses on the live NYT board.",
        "narration": (
            "Every Connections player faces the same agonizing moment: four guesses remaining, two overlapping clusters, and no certainty. "
            "On the official New York Times interface, every test costs a life. Four incorrect hypotheses, and your streak evaporates. "
            "Elite solvers never test hypotheses on the live board. Instead, they utilize the Scratchboard Protocol. "
            "By isolating suspected groups in an external sandbox, you can rearrange candidate quartets, visually trace five-word decoys, "
            "and stress-test every overlap before committing a single click to the official game. "
            "Separating your thinking phase from your execution phase is the single highest-impact habit you can adopt to maintain a flawless winning record."
        ),
        "content_html": """
        <div class="protocol-matrix">
          <div class="matrix-card">
            <div>
              <div class="matrix-header">
                <div class="matrix-title">Live NYT Board</div>
                <span class="matrix-badge-bad">HIGH STAKES • 4 LIVES</span>
              </div>
              <ul class="matrix-list">
                <li class="matrix-item">❌ Every hypothesis costs 1 life</li>
                <li class="matrix-item">❌ 80% failure rate when testing 5-word decoys</li>
                <li class="matrix-item">❌ Panic & streak anxiety force rushed guesses</li>
                <li class="matrix-item">❌ No visual way to isolate candidate sets</li>
              </ul>
            </div>
            <div style="background:#FEE2E2; border:2px solid #DC2626; border-radius:10px; padding:12px; font-weight:800; color:#991B1B; text-align:center;">
              Result: 1 Mistake away from streak destruction
            </div>
          </div>

          <div class="matrix-card" style="border-color:#16A34A; box-shadow:0 8px 0 #15803D;">
            <div>
              <div class="matrix-header">
                <div class="matrix-title">Scratchboard Protocol</div>
                <span class="matrix-badge-good">ZERO RISK • SANDBOX</span>
              </div>
              <ul class="matrix-list">
                <li class="matrix-item">✅ Infinite hypothesis testing with zero penalties</li>
                <li class="matrix-item">✅ Safe isolation of overlapping 5th candidate words</li>
                <li class="matrix-item">✅ Drag & drop candidate staging slots</li>
                <li class="matrix-item">✅ Total separation of reasoning vs. execution</li>
              </ul>
            </div>
            <div style="background:#DCFCE7; border:2px solid #16A34A; border-radius:10px; padding:12px; font-weight:800; color:#166534; text-align:center;">
              Result: 100% Streak Protection Guaranteed
            </div>
          </div>
        </div>
        """
    },
    {
        "id": 11,
        "act": "ACT 5 • CONNECTIONSASSISTANT.COM",
        "title": "Master Every Grid at connectionsassistant.com",
        "subtitle": "The dedicated zero-spoiler companion built to protect your streak.",
        "narration": (
            "This is why we built Connections Grouping Assistant at connectionsassistant.com. "
            "Our free web platform gives you an interactive, zero-spoiler scratchboard engineered specifically for daily solvers. "
            "You can paste today's puzzle in one click, drag candidate words into test slots, and receive progressive tactical nudges without spoiling the answer. "
            "If you are stuck on a five-word decoy, our engine will flag the overlap without revealing the categories. "
            "And every morning, our Breakdowns hub publishes an interactive post-game analysis untangling the day's trickiest traps. "
            "Bookmark connectionsassistant.com, protect your streak, and enjoy your morning puzzle."
        ),
        "content_html": """
        <div class="assistant-grid">
          <div class="features-container">
            <div class="feature-row">
              <div class="feature-icon">🛡️</div>
              <div class="feature-text">
                <h3>3-Stage Progressive Nudges</h3>
                <p>Gentle tactical nudges without ever revealing categories or spoiling words.</p>
              </div>
            </div>
            <div class="feature-row">
              <div class="feature-icon">⚡</div>
              <div class="feature-text">
                <h3>1-Click Clipboard Grid Import</h3>
                <p>Paste your 16 words instantly and start staging candidate clusters.</p>
              </div>
            </div>
            <div class="feature-row">
              <div class="feature-icon">🔍</div>
              <div class="feature-text">
                <h3>Overlapping Decoy Detection</h3>
                <p>Identifies 5-candidate traps and highlights pivot words like CUT.</p>
              </div>
            </div>
            <div class="feature-row">
              <div class="feature-icon">📊</div>
              <div class="feature-text">
                <h3>Daily Breakdowns & Streak Shield</h3>
                <p>Interactive post-game archives explaining every puzzle's mechanics.</p>
              </div>
            </div>
          </div>

          <div class="cta-card">
            <div style="font-family:'JetBrains Mono',monospace; font-size:14px; font-weight:800; background:#FEF9C3; border:2px solid #1A1A1A; padding:6px 14px; border-radius:8px;">
              FREE DAILY SOLVER SUITE
            </div>
            <div class="cta-title">Never Lose Your Daily Streak Again</div>
            <div class="cta-url-pill">connectionsassistant.com</div>
            <div style="font-size:16px; font-weight:700; color:#4B5563;">
              Full Guide & Daily Interactive Breakdowns
            </div>
          </div>
        </div>
        """
    }
]

# ==============================================================================
# PIPELINE HELPER FUNCTIONS
# ==============================================================================
async def synthesize_speech(text: str, output_path: Path, max_retries: int = 3):
    """Synthesizes speech using edge-tts with exponential retry backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            comm = edge_tts.Communicate(text, VOICE_NAME, rate=VOICE_RATE)
            await comm.save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 1000:
                return
        except Exception as e:
            print(f"    [!] TTS attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            await asyncio.sleep(2 * attempt)

def get_audio_duration(audio_path: Path) -> float:
    """Uses ffprobe to extract exact duration of an audio file."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return float(res.stdout.strip())

async def render_slide_frame(page, scene: dict, output_path: Path):
    """Renders a single 1920x1080 scene slide using Playwright Chromium."""
    html = HTML_TEMPLATE.replace("{{ACT_BADGE}}", scene["act"])
    html = html.replace("{{SCENE_TITLE}}", scene["title"])
    html = html.replace("{{SCENE_SUBTITLE}}", scene["subtitle"])
    html = html.replace("{{SCENE_BODY}}", scene["content_html"])

    await page.set_content(html, wait_until="load")
    # Wait for web fonts and layout stability
    await page.wait_for_timeout(250)
    await page.screenshot(path=str(output_path))

# ==============================================================================
# MASTER PIPELINE EXECUTION
# ==============================================================================
async def main():
    print("=" * 80)
    print("PRODUCING MASTERCLASS VIDEO: THE DEFINITIVE GUIDE TO SOLVING NYT CONNECTIONS")
    print("=" * 80)
    print(f"Output Target:  {FINAL_VIDEO}")
    print(f"Temp Directory: {TEMP_DIR}")
    print(f"Voice Config:   {VOICE_NAME} ({VOICE_RATE})")
    print(f"Total Scenes:   {len(SCENES)}")
    print("-" * 80)

    scene_audio_files = []
    scene_durations = []
    scene_frames = []

    # --------------------------------------------------------------------------
    # STEP 1: EDGE-TTS NARRATION SYNTHESIS
    # --------------------------------------------------------------------------
    print("\n[STEP 1/5] Synthesizing narration audio tracks via edge-tts...")
    total_words = 0
    for sc in SCENES:
        s_id = sc["id"]
        words = len(sc["narration"].split())
        total_words += words
        out_mp3 = TEMP_DIR / f"scene_{s_id:02d}.mp3"

        print(f"  [+] Scene {s_id:02d} ({words:3d} words): {sc['title'][:45]}...")
        await synthesize_speech(sc["narration"], out_mp3)
        dur = get_audio_duration(out_mp3)
        scene_audio_files.append(out_mp3)
        scene_durations.append(dur)
        print(f"      ✓ Synthesized: {dur:.2f}s")

    total_narration_dur = sum(scene_durations)
    print(f"\n[✓] Narration Synthesis Complete: {total_words} words | {total_narration_dur / 60:.2f} minutes ({total_narration_dur:.1f}s)")

    # --------------------------------------------------------------------------
    # STEP 2: PLAYWRIGHT 1920x1080 SLIDE RENDERING
    # --------------------------------------------------------------------------
    print("\n[STEP 2/5] Rendering 1920x1080 Neo-Brutalist slides via Playwright Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        for sc in SCENES:
            s_id = sc["id"]
            frame_png = TEMP_DIR / f"frame_{s_id:02d}.png"
            print(f"  [+] Capturing 1080p frame for Scene {s_id:02d}: {sc['title'][:40]}...")
            await render_slide_frame(page, sc, frame_png)
            scene_frames.append(frame_png)
            print(f"      ✓ Captured: {frame_png.name}")

        await browser.close()
    print("[✓] All 11 slides rendered in 1920x1080 resolution.")

    # --------------------------------------------------------------------------
    # STEP 3: CONCATENATE AUDIO TRACKS
    # --------------------------------------------------------------------------
    print("\n[STEP 3/5] Concatenating audio tracks into continuous master audio...")
    audio_list_txt = TEMP_DIR / "audio_list.txt"
    with open(audio_list_txt, "w", encoding="utf-8") as f:
        for a in scene_audio_files:
            f.write(f"file '{a.resolve().as_posix()}'\n")

    combined_audio = TEMP_DIR / "masterclass_full_audio.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(audio_list_txt),
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(combined_audio)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    master_audio_dur = get_audio_duration(combined_audio)
    print(f"[✓] Master audio concatenated: {combined_audio.name} ({master_audio_dur:.2f}s)")

    # --------------------------------------------------------------------------
    # STEP 4: GENERATE VIDEO CONCAT MANIFEST
    # --------------------------------------------------------------------------
    print("\n[STEP 4/5] Generating FFmpeg video concat manifest...")
    video_concat_txt = TEMP_DIR / "video_concat.txt"
    with open(video_concat_txt, "w", encoding="utf-8") as f:
        for i in range(len(SCENES)):
            f.write(f"file '{scene_frames[i].resolve().as_posix()}'\n")
            f.write(f"duration {scene_durations[i]:.2f}\n")
        # FFmpeg concat demuxer convention: repeat final image for holding
        f.write(f"file '{scene_frames[-1].resolve().as_posix()}'\n")
    print(f"[✓] Video manifest created: {video_concat_txt.name}")

    # --------------------------------------------------------------------------
    # STEP 5: COMPILE MASTERCLASS MP4 VIA NVIDIA NVENC ACCELERATION
    # --------------------------------------------------------------------------
    print("\n[STEP 5/5] Compiling 1080p masterclass video via NVIDIA NVENC (p4 preset, 8M bitrate)...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(video_concat_txt),
        "-i", str(combined_audio),
        "-c:v", "h264_nvenc",
        "-preset", "p4",
        "-b:v", "8M",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{master_audio_dur:.2f}",
        "-shortest",
        str(FINAL_VIDEO)
    ]

    print(f"  Command: {' '.join(ffmpeg_cmd)}")
    result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"[!] FFmpeg error:\n{result.stderr}")
        sys.exit(result.returncode)

    # --------------------------------------------------------------------------
    # VERIFICATION & SUMMARY
    # --------------------------------------------------------------------------
    if FINAL_VIDEO.exists():
        final_size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
        final_dur = get_audio_duration(FINAL_VIDEO)
        print("\n" + "=" * 80)
        print("MASTERCLASS VIDEO PRODUCTION COMPLETE!")
        print("=" * 80)
        print(f"  Output Video:  {FINAL_VIDEO}")
        print(f"  File Size:     {final_size_mb:.2f} MB")
        print(f"  Duration:      {final_dur:.2f} seconds ({final_dur / 60:.2f} minutes)")
        print(f"  Resolution:    1920x1080 (16:9 Landscape)")
        print(f"  Encoder:       h264_nvenc (preset p4, 8M bitrate)")
        print(f"  Audio:         en-US-ChristopherNeural (+10% rate, AAC 192k)")
        print("=" * 80)
    else:
        print("[!] Final video file was not found!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
