import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any

# High-quality curated lexicon for today's & recent puzzles
BUILTIN_LEXICON: Dict[str, Dict[str, str]] = {
    # 2026-11-14 (Puzzle #1252)
    "ADVANCED": {
        "ipa": "ədˈvænst",
        "pos": "adjective",
        "definition": "Far on or ahead in development, complexity, or progress; cutting-edge.",
        "etymology": "From Old French avancier ('to move forward'), rooted in Latin abante ('from before').",
        "sentence": "The lab introduced an advanced diagnostic tool that cut processing time in half."
    },
    "FOREMOST": {
        "ipa": "ˈfɔːrmoʊst",
        "pos": "adjective",
        "definition": "Most prominent in rank, importance, or position; leading the field.",
        "etymology": "From Old English formest, a double superlative meaning 'earliest or most in front.'",
        "sentence": "She is widely regarded as the foremost authority on medieval linguistics."
    },
    "MODERN": {
        "ipa": "ˈmɒdərn",
        "pos": "adjective",
        "definition": "Relating to the present or recent times; characterized by up-to-date techniques or ideas.",
        "etymology": "From Late Latin modernus ('of today'), derived from Latin modo ('just now').",
        "sentence": "Modern architecture often favors open floor plans and natural light."
    },
    "PROGRESSIVE": {
        "ipa": "prəˈɡrɛsɪv",
        "pos": "adjective",
        "definition": "Happening or developing gradually; favoring new ideas, innovation, or reform.",
        "etymology": "From Latin progressus ('a going forward'), from pro- ('forward') + gradi ('to walk').",
        "sentence": "The company adopted a progressive remote-work policy ahead of its competitors."
    },
    "CAMPUS": {
        "ipa": "ˈkæmpəs",
        "pos": "noun",
        "definition": "The grounds and buildings of a university, college, hospital, or corporate institution.",
        "etymology": "From Latin campus ('open field or plain'), first used for Princeton University's grounds in 1774.",
        "sentence": "New students toured the brick walkways of the main campus before orientation."
    },
    "CENTER": {
        "ipa": "ˈsɛntər",
        "pos": "noun",
        "definition": "A building, facility, or hub dedicated to a particular public, cultural, or research activity.",
        "etymology": "From Greek kentron ('sharp point, stationary point of a compass') via Latin centrum.",
        "sentence": "The community arts center hosts weekend pottery and painting workshops."
    },
    "COMPLEX": {
        "ipa": "ˈkɒmplɛks",
        "pos": "noun",
        "definition": "A group of similar or interconnected buildings sharing a common site and purpose.",
        "etymology": "From Latin complexus ('woven together'), from com- ('together') + plectere ('to braid').",
        "sentence": "The new athletic complex includes an indoor track, pool, and tennis courts."
    },
    "FACILITY": {
        "ipa": "fəˈsɪlɪti",
        "pos": "noun",
        "definition": "A place, amenity, or piece of equipment provided for a particular institutional purpose.",
        "etymology": "From Latin facilis ('easy to do'), originally meaning ease before evolving to mean a helpful building.",
        "sentence": "Engineers tested the prototype inside a climate-controlled research facility."
    },
    "CHESS": {
        "ipa": "tʃɛs",
        "pos": "noun",
        "definition": "A two-player abstract strategy board game played on an 8x8 checkered grid of 64 squares.",
        "etymology": "From Old French esches, plural of eschec ('check'), ultimately from Persian shah ('king').",
        "sentence": "Opening with the queen's pawn is a classic strategy in tournament chess."
    },
    "GO": {
        "ipa": "ɡoʊ",
        "pos": "noun",
        "definition": "An ancient East Asian strategy board game where two players surround territory using black and white stones.",
        "etymology": "Borrowed from Japanese igo ('surrounding board game'), derived from Middle Chinese weiqi.",
        "sentence": "Despite simple placement rules, the game of Go has more legal board positions than atoms in the universe."
    },
    "OTHELLO": {
        "ipa": "oʊˈθɛloʊ",
        "pos": "noun",
        "definition": "A classic two-player strategy board game played with reversible black-and-white discs (also called Reversi).",
        "etymology": "Trademarked in 1971 by Goro Hasegawa, named after Shakespeare's play featuring dramatic reversals.",
        "sentence": "One clever corner move in Othello can flip an entire row of your opponent's discs."
    },
    "STRATEGO": {
        "ipa": "strəˈtiːɡoʊ",
        "pos": "noun",
        "definition": "A classic two-player strategy board game of hidden ranks, capture, and capturing the opponent's flag.",
        "etymology": "Derived from Greek strategos ('military commander'), popularized as a board game in the mid-20th century.",
        "sentence": "In Stratego, placing a bomb piece near your flag protects it from reckless scouts."
    },
    "BATTLE": {
        "ipa": "ˈbætəl",
        "pos": "noun",
        "definition": "Wordplay: 'RATTLE' (baby toy) with its first letter changed from R to B.",
        "etymology": "Standard word means combat (Latin battuere, 'to beat'), used here as a letter-swap decoy for a baby's rattle.",
        "sentence": "Swap the 'B' back to 'R' and BATTLE becomes RATTLE—the noisy baby toy hidden in today's Purple tier."
    },
    "MARRIAGE": {
        "ipa": "ˈmærɪdʒ",
        "pos": "noun",
        "definition": "Wordplay: 'CARRIAGE' (baby stroller/pram) with its first letter changed from C to M.",
        "etymology": "Standard word means matrimony (Old French mariage), used here as a first-letter swap for a baby carriage.",
        "sentence": "Change 'M' back to 'C' and MARRIAGE turns into CARRIAGE, completing the baby gear wordplay."
    },
    "MOTTLE": {
        "ipa": "ˈmɒtəl",
        "pos": "verb",
        "definition": "Wordplay: 'BOTTLE' (baby milk bottle) with its first letter changed from B to M.",
        "etymology": "Standard verb means to mark with spots or blotches; here it disguises a baby's bottle via a single-letter shift.",
        "sentence": "Replacing the opening 'M' with 'B' transforms MOTTLE into BOTTLE."
    },
    "TRIB": {
        "ipa": "trɪb",
        "pos": "noun",
        "definition": "Wordplay: 'CRIB' (baby bed) with its first letter changed from C to T.",
        "etymology": "Short for tribune or printing term; here it serves as a one-letter disguise for a baby's crib.",
        "sentence": "Swap 'T' for 'C' and TRIB reveals CRIB, finishing the four-item baby gear set."
    },
}


def _fetch_dictionary_entry(word: str) -> Dict[str, str]:
    """Query free dictionaryapi.dev for authentic definition, IPA, POS, and example sentence."""
    clean_w = word.strip().lower()
    if " " in clean_w:
        return {}
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.request.quote(clean_w)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ConnectionsAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status != 200:
                return {}
            payload = json.loads(resp.read().decode("utf-8"))
            if not isinstance(payload, list) or not payload:
                return {}
            entry = payload[0]
            ipa = entry.get("phonetic", "")
            if not ipa:
                for p in entry.get("phonetics", []):
                    if p.get("text"):
                        ipa = p["text"]
                        break
            meanings = entry.get("meanings", [])
            pos = meanings[0].get("partOfSpeech", "word") if meanings else "word"
            definition = ""
            sentence = ""
            for m in meanings:
                for d in m.get("definitions", []):
                    if not definition and d.get("definition"):
                        definition = d["definition"]
                    if not sentence and d.get("example"):
                        sentence = d["example"]
                    if definition and sentence:
                        break
                if definition and sentence:
                    break
            origin = entry.get("origin", "")
            if definition:
                return {
                    "ipa": ipa.strip("/[] "),
                    "pos": pos,
                    "definition": definition,
                    "etymology": origin,
                    "sentence": sentence,
                }
    except Exception:
        return {}
    return {}


def get_lexicon_data(root_dir: Path, puzzle_words: list[str] | None = None) -> Dict[str, Dict[str, str]]:
    """Combine BUILTIN_LEXICON, CURATED_LEXICON, local cache, and live DictionaryAPI lookups."""
    merged: Dict[str, Dict[str, str]] = {}

    cache_file = root_dir / "word_lexicon_cache.json"
    if cache_file.exists():
        try:
            merged.update(json.loads(cache_file.read_text(encoding="utf-8")))
        except Exception:
            pass

    try:
        import sys
        sys.path.append(str(root_dir))
        from generate_daily_deep_dive import CURATED_LEXICON
        merged.update(CURATED_LEXICON)
    except Exception:
        pass

    merged.update(BUILTIN_LEXICON)

    if puzzle_words:
        updated_cache = False
        for w in puzzle_words:
            wu = w.strip().upper()
            if wu not in merged:
                fetched = _fetch_dictionary_entry(wu)
                if fetched:
                    merged[wu] = fetched
                    updated_cache = True
        if updated_cache:
            try:
                cache_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            except Exception:
                pass

    return merged


def generate_lexical_accordion_html(puzzle_data: Dict[str, Any], root_dir: Path) -> str:
    """Generate the full-width <details class="lexical-accordion"> block without repetitive boilerplate."""
    categories = puzzle_data.get("categories", [])
    all_words = [w for c in categories for w in c.get("words", [])]
    curated = get_lexicon_data(root_dir, puzzle_words=all_words)

    tier_styles = [
        ("yellow", "🟨 TIER 1 &bull; EASIEST", "Direct Synonyms &amp; Clear Match"),
        ("green",  "🟩 TIER 2 &bull; MEDIUM",  "Shared Real-World Context"),
        ("blue",   "🟦 TIER 3 &bull; HARD",    "Trivia, Sets &amp; Compound Links"),
        ("purple", "🟪 TIER 4 &bull; TRICKY WORDPLAY", "Lateral Wordplay &amp; Letter Shifts"),
    ]

    parts = [
        '                <!-- FULL-WIDTH DAILY WORD GUIDE -->',
        '                <details class="lexical-accordion" id="lexical-encyclopedia" open>',
        '                    <summary class="lexical-summary">',
        "                        <span>📖 TODAY'S WORD GUIDE: MEANINGS, ORIGINS &amp; HOW EACH GROUP CONNECTS</span>",
        '                        <span class="lexical-badge-pill">16 Words Explained &bull; Click to Open / Close &darr;</span>',
        '                    </summary>',
        '                    <div class="lexical-body">'
    ]

    for idx, cat in enumerate(categories):
        tier_color, tier_label, tier_sub = tier_styles[min(idx, len(tier_styles) - 1)]
        cat_title = cat.get("title", f"Tier {idx+1}")
        words = cat.get("words", [])
        words_joined = ", ".join(words)

        parts.append(f"""                        <!-- TIER {idx + 1} -->
                        <div class="lexical-tier-card" style="border-top: 5px solid var(--tier-{tier_color});">
                            <div class="lexical-tier-header">
                                <div class="lexical-tier-top">
                                    <span class="legend-chip chip-{tier_color}">{tier_label}</span>
                                    <span class="tier-type-badge">{tier_sub}</span>
                                </div>
                                <div class="tier-category-heading">{cat_title}</div>
                            </div>

                            <div class="wwwwwh-grid">
                                <div class="wwwwwh-box">
                                    <strong>GROUP CONNECTION:</strong> {words_joined} all share the unifying bond: <strong>{cat_title}</strong>.
                                </div>
                                <div class="wwwwwh-box">
                                    <strong>SOLVE STRATEGY:</strong> Verify all four words against <em>{cat_title}</em> before submitting to avoid 1-away traps with overlapping red herrings.
                                </div>
                            </div>

                            <div class="words-lexicon-grid">""")

        for word in words:
            wu = word.strip().upper()
            info = curated.get(wu, {})
            ipa = info.get("ipa", "").strip("[]/ ")
            ipa_html = f'<span class="lex-ipa">/{ipa}/</span>' if ipa else ''
            pos = info.get("pos", "")
            pos_html = f'<span class="lex-pos">{pos}</span>' if pos else ''
            definition = info.get("definition", f"Part of today's '{cat_title}' group.")
            etymology = info.get("etymology", "")
            sentence = info.get("sentence", "")

            etym_html = f'\n                                    <div class="lex-etym"><strong>Origin &amp; Note:</strong> {etymology}</div>' if etymology else ''
            sent_html = f'\n                                    <div class="lex-sentence">"{sentence.strip(chr(34) + chr(39))}"</div>' if sentence else ''

            parts.append(f"""                                <div class="lex-card">
                                    <div class="lex-header">
                                        <span class="lex-word">{wu}</span>
                                        {ipa_html}
                                        {pos_html}
                                    </div>
                                    <div class="lex-def">{definition}</div>{etym_html}{sent_html}
                                </div>""")

        parts.append("""                            </div>
                        </div>""")

    parts.append("                    </div>")
    parts.append("                </details>")

    return "\n".join(parts)


def update_lexical_accordion_in_html(html_content: str, puzzle_data: Dict[str, Any], root_dir: Path) -> str:
    """Replace the <details class="lexical-accordion" id="lexical-encyclopedia"> block inside html_content."""
    new_accordion = generate_lexical_accordion_html(puzzle_data, root_dir)
    pattern = re.compile(
        r'(?:<!-- FULL-WIDTH DAILY WORD GUIDE -->\s*)?<details class="lexical-accordion" id="lexical-encyclopedia"[^>]*>.*?</details>',
        re.DOTALL
    )
    if not pattern.search(html_content):
        return html_content
    return pattern.sub(new_accordion, html_content, count=1)


def sync_breakdowns_encyclopedia(root_dir: Path, puzzle_data: Dict[str, Any], dry_run: bool = False) -> bool:
    """Replace the <details class="lexical-accordion" id="lexical-encyclopedia"> block in public/breakdowns.html."""
    breakdowns_file = root_dir / "public" / "breakdowns.html"
    if not breakdowns_file.exists():
        return False

    orig_content = breakdowns_file.read_text(encoding="utf-8")
    new_accordion = generate_lexical_accordion_html(puzzle_data, root_dir)

    pattern = re.compile(
        r'(?:<!-- FULL-WIDTH DAILY WORD GUIDE -->\s*)?<details class="lexical-accordion" id="lexical-encyclopedia"[^>]*>.*?</details>',
        re.DOTALL
    )

    if not pattern.search(orig_content):
        print("    [!] Could not locate #lexical-encyclopedia block in breakdowns.html")
        return False

    updated_content = pattern.sub(new_accordion, orig_content, count=1)

    if updated_content != orig_content:
        if not dry_run:
            breakdowns_file.write_text(updated_content, encoding="utf-8")
            print("    [✓] Synced 16-word lexical encyclopedia accordion.")
        else:
            print("    [~] [DRY-RUN] Would update 16-word lexical encyclopedia accordion.")
        return True
    else:
        print("    [-] Lexical encyclopedia already up-to-date.")
        return False
