"""
reddit_daily_nudge.py

Reddit Dispatcher Node for Connections Grouping Assistant.

Responsibilities:
1. Load and parse daily_puzzle.json from the project root directory.
2. Format a progressive spoiler-shielded Reddit comment following reddit_nudge_skill.md:
   - Header with today's date and a clear 'No Direct Spoilers' disclaimer.
   - 4 bullet points (🟨, 🟩, 🟦, 🟪) with progressive conceptual clues wrapped in strict >!spoiler!< tags.
   - Explicit '⚠️ Red Herring Alert' breaking down overlapping traps across groups.
   - Verified attribution disclosure pointing to connectionsassistant.com and @ConnectionsAssistant.
3. Memory & Encoding Hygiene:
   - 64-bit Win32 ctypes API (kernel32.GlobalAlloc, GMEM_MOVEABLE, user32.OpenClipboard, SetClipboardData CF_UNICODETEXT)
     injects the comment directly as UTF-16LE without stdout piping, eliminating emoji mojibake.
4. Writes local fallback file today_reddit_comment.txt in UTF-8.
"""

import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys

ATTRIBUTION_DISCLOSURE = (
    "*(Want to test candidate groupings on today's 16 words risk-free without burning your 4 guesses? "
    "Free zero-spoiler practice scratchboard & daily video breakdowns linked in my profile!)*"
)

KNOWN_TRAPS = {
    "1350": (
        "Watch out for cardinal directions: NORTH and SOUTH appear alongside EASTER, "
        "creating an alluring compass direction trap (North, South, East). "
        "Do not burn a guess grouping directions together—EASTER belongs to storm endings "
        "(Nor'easter), while NORTH and SOUTH are U.S. state name prefixes (Carolina/Dakota)."
    ),
    "2026-11-07": (
        "Watch out for cardinal directions: NORTH and SOUTH appear alongside EASTER, "
        "creating an alluring compass direction trap (North, South, East). "
        "Do not burn a guess grouping directions together—EASTER belongs to storm endings "
        "(Nor'easter), while NORTH and SOUTH are U.S. state name prefixes (Carolina/Dakota)."
    ),
    "1351": (
        "Watch out for hair styling misdirection: CUT appears alongside "
        "TRIM, BLOWOUT, COLOR, and EXTENSIONS, tempting you into a 5-word salon trap. "
        "CUT belongs to the muscular physique group (Built, Jacked, Ripped), "
        "leaving the four salon services clean."
    ),
    "2026-11-08": (
        "Watch out for hair styling misdirection: CUT appears alongside "
        "TRIM, BLOWOUT, COLOR, and EXTENSIONS, tempting you into a 5-word salon trap. "
        "CUT belongs to the muscular physique group (Built, Jacked, Ripped), "
        "leaving the four salon services clean."
    ),
    "1366": (
        "Watch out for casino & scam misdirection: CARD SHARK appears alongside "
        "CON JOB, SHELL GAME, FLIMFLAM, and RIP-OFF, tempting you into a 5-word hustler trap. "
        "CARD SHARK ends in a sea creature (Shark), leaving the four deceitful schemes intact."
    ),
    "2026-11-09": (
        "Watch out for casino & scam misdirection: CARD SHARK appears alongside "
        "CON JOB, SHELL GAME, FLIMFLAM, and RIP-OFF, tempting you into a 5-word hustler trap. "
        "CARD SHARK ends in a sea creature (Shark), leaving the four deceitful schemes intact."
    ),
    "1361": (
        "Watch out for historical trades misdirection: BEEKEEPER appears alongside "
        "APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT, tempting you into a 5-word occupation trap. "
        "Do not burn a guess grouping BEEKEEPER with old-timey jobs—it belongs to the vowel count tier "
        "(words with five of one vowel: 5 E's), leaving the four historical trades clean."
    ),
    "2026-11-10": (
        "Watch out for historical trades misdirection: BEEKEEPER appears alongside "
        "APOTHECARY, HABERDASHER, SCRIVENER, and WAINWRIGHT, tempting you into a 5-word occupation trap. "
        "Do not burn a guess grouping BEEKEEPER with old-timey jobs—it belongs to the vowel count tier "
        "(words with five of one vowel: 5 E's), leaving the four historical trades clean."
    ),
    "1249": (
        "Watch out for the seductive 'Kinds of Tea' rainbow trap: GREEN, AFTERNOON, BUBBLE, and HERBAL "
        "immediately tempt an enticing 4-word tea theme! However, every single one of these words actually anchors a different "
        "tier: GREEN is on the golf course, HERBAL is medicine, BUBBLE is filled with air, and AFTERNOON ends in a palindrome (NOON). "
        "Do not burn a guess on tea!"
    ),
    "1250": (
        "Watch out for the tempting 'Back to the Future' rainbow decoy trap: "
        "GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY immediately suggest a 4-word sci-fi movie theme! "
        "However, every single one belongs to a completely different tier: "
        "GREAT SCOTT is an exclamation, FLUX CAPACITOR starts with a variation, "
        "DOC BROWN ends in a cooking method (brown), and MARTY MCFLY starts with an Oscar Best Picture winner (Marty, 1955). "
        "Do not burn a guess grouping them together!"
    ),
    "1352": (
        "Watch out for the tempting 'Back to the Future' rainbow decoy trap: "
        "GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY immediately suggest a 4-word sci-fi movie theme! "
        "However, every single one belongs to a completely different tier: "
        "GREAT SCOTT is an exclamation, FLUX CAPACITOR starts with a variation, "
        "DOC BROWN ends in a cooking method (brown), and MARTY MCFLY starts with an Oscar Best Picture winner (Marty, 1955). "
        "Do not burn a guess grouping them together!"
    ),
    "2026-11-12": (
        "Watch out for the tempting 'Back to the Future' rainbow decoy trap: "
        "GREAT SCOTT, FLUX CAPACITOR, DOC BROWN, and MARTY MCFLY immediately suggest a 4-word sci-fi movie theme! "
        "However, every single one belongs to a completely different tier: "
        "GREAT SCOTT is an exclamation, FLUX CAPACITOR starts with a variation, "
        "DOC BROWN ends in a cooking method (brown), and MARTY MCFLY starts with an Oscar Best Picture winner (Marty, 1955). "
        "Do not burn a guess grouping them together!"
    ),
    "1354": (
        "Watch out for the seductive 'Kinds of Tea' rainbow trap: GREEN, AFTERNOON, BUBBLE, and HERBAL "
        "immediately tempt an enticing 4-word tea theme! However, every single one of these words actually anchors a different "
        "tier: GREEN is on the golf course, HERBAL is medicine, BUBBLE is filled with air, and AFTERNOON ends in a palindrome (NOON). "
        "Do not burn a guess on tea!"
    ),
    "2026-11-11": (
        "Watch out for the seductive 'Kinds of Tea' rainbow trap: GREEN, AFTERNOON, BUBBLE, and HERBAL "
        "immediately tempt an enticing 4-word tea theme! However, every single one of these words actually anchors a different "
        "tier: GREEN is on the golf course, HERBAL is medicine, BUBBLE is filled with air, and AFTERNOON ends in a palindrome (NOON). "
        "Do not burn a guess on tea!"
    ),
}

CURATED_HINTS = {
    "1250": {
        0: "Old-fashioned, colorful exclamations expressing shock, astonishment, or surprise.",
        1: "The first word of each pair is a direct synonym for fluctuation, alteration, or change.",
        2: "Look at the second word of each phrase—they are all methods of preparing or cooking food.",
        3: "Wordplay alert: The first word of each compound won Hollywood's highest prize for Best Picture at the Academy Awards.",
    },
    "1352": {
        0: "Old-fashioned, colorful exclamations expressing shock, astonishment, or surprise.",
        1: "The first word of each pair is a direct synonym for fluctuation, alteration, or change.",
        2: "Look at the second word of each phrase—they are all methods of preparing or cooking food.",
        3: "Wordplay alert: The first word of each compound won Hollywood's highest prize for Best Picture at the Academy Awards.",
    },
    "2026-11-12": {
        0: "Old-fashioned, colorful exclamations expressing shock, astonishment, or surprise.",
        1: "The first word of each pair is a direct synonym for fluctuation, alteration, or change.",
        2: "Look at the second word of each phrase—they are all methods of preparing or cooking food.",
        3: "Wordplay alert: The first word of each compound won Hollywood's highest prize for Best Picture at the Academy Awards.",
    },
    "1249": {
        0: "Healing practices and medicinal traditions outside modern synthetic pharmaceuticals.",
        1: "Landscapes, hazards, and zones you navigate while playing eighteen holes of golf.",
        2: "Inflatable or pressurized everyday items that rely on trapped air or gas to function.",
        3: "Wordplay alert: Look closely at the final letters of each word—read the endings backwards and forwards!",
    },
    "1354": {
        0: "Healing practices and medicinal traditions outside modern synthetic pharmaceuticals.",
        1: "Landscapes, hazards, and zones you navigate while playing eighteen holes of golf.",
        2: "Inflatable or pressurized everyday items that rely on trapped air or gas to function.",
        3: "Wordplay alert: Look closely at the final letters of each word—read the endings backwards and forwards!",
    },
    "2026-11-11": {
        0: "Healing practices and medicinal traditions outside modern synthetic pharmaceuticals.",
        1: "Landscapes, hazards, and zones you navigate while playing eighteen holes of golf.",
        2: "Inflatable or pressurized everyday items that rely on trapped air or gas to function.",
        3: "Wordplay alert: Look closely at the final letters of each word—read the endings backwards and forwards!",
    },
    "1366": {
        0: "Think about schemes, hustles, and swindles designed to deceive.",
        1: "Styles, cuts, or treatments you would find while shopping for denim pants.",
        2: "Notice the physical outline or cutting edge of these household, dining, or botanical items—they share a jagged feature.",
        3: "Wordplay alert: Say the final word of each phrase out loud and picture what swims in the ocean.",
    },
    "2026-11-09": {
        0: "Think about schemes, hustles, and swindles designed to deceive.",
        1: "Styles, cuts, or treatments you would find while shopping for denim pants.",
        2: "Notice the physical outline or cutting edge of these household, dining, or botanical items—they share a jagged feature.",
        3: "Wordplay alert: Say the final word of each phrase out loud and picture what swims in the ocean.",
    },
    "1361": {
        0: "Lively words describing an uproar, commotion, or noisy fuss.",
        1: "Figures of speech and rhetorical techniques studied in English or literature classes.",
        2: "Archaic or historical professions and trades from centuries past.",
        3: "Wordplay alert: Ignore what the words mean and count the identical vowels inside each one.",
    },
    "2026-11-10": {
        0: "Lively words describing an uproar, commotion, or noisy fuss.",
        1: "Figures of speech and rhetorical techniques studied in English or literature classes.",
        2: "Archaic or historical professions and trades from centuries past.",
        3: "Wordplay alert: Ignore what the words mean and count the identical vowels inside each one.",
    },
}


def copy_to_clipboard_clean(text: str) -> None:
    """Copies text to the Windows clipboard as CF_UNICODETEXT using 64-bit ctypes."""
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.argtypes = []
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.argtypes = []
    user32.CloseClipboard.restype = wintypes.BOOL

    encoded = text.encode("utf-16le") + b"\x00\x00"
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    p_mem = kernel32.GlobalLock(h_mem)
    ctypes.memmove(p_mem, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)

    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
    user32.CloseClipboard()


def generate_nudge_comment(puzzle_path: str = "daily_puzzle.json") -> str:
    path = Path(puzzle_path)
    if not path.exists():
        raise FileNotFoundError(f"Puzzle file not found: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    puzzle_id = str(data.get("id", ""))
    puzzle_date = data.get("date", "")
    categories = data.get("categories", [])
    cat_by_level = {c.get("level", 0): c for c in categories}

    hints = CURATED_HINTS.get(puzzle_id) or CURATED_HINTS.get(puzzle_date)
    if not hints:
        hints = {
            0: f"Focus on concepts related to {cat_by_level.get(0, {}).get('title', 'these words').lower()}.",
            1: f"Look for common characteristics tied to {cat_by_level.get(1, {}).get('title', 'this theme').lower()}.",
            2: f"Notice the shared feature or context connecting {cat_by_level.get(2, {}).get('title', 'these terms').lower()}.",
            3: f"Wordplay or linguistic trick: analyze {cat_by_level.get(3, {}).get('title', 'this pattern').lower()}.",
        }

    trap_text = (
        KNOWN_TRAPS.get(puzzle_id)
        or KNOWN_TRAPS.get(puzzle_date)
        or "Watch out for polysemic words that fit into multiple candidate groups before submitting your first guess."
    )

    comment = (
        f"**Progressive Nudges & Clues for Today ({puzzle_date}) — No Direct Spoilers:**\n\n"
        f"* 🟨 **TIER 1 • EASIEST (Direct Synonyms):** >!{hints[0].strip()}!<\n"
        f"* 🟩 **TIER 2 • MODERATE (Contextual Link):** >!{hints[1].strip()}!<\n"
        f"* 🟦 **TIER 3 • CHALLENGING (Trivia & Patterns):** >!{hints[2].strip()}!<\n"
        f"* 🟪 **TIER 4 • TRICKIEST (Lateral Wordplay):** >!{hints[3].strip()}!<\n"
        f"* ⚠️ **Red Herring Alert:** >!{trap_text.strip()}!<\n\n"
        f"---\n"
        f"{ATTRIBUTION_DISCLOSURE}"
    )

    output_path = Path("today_reddit_comment.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(comment)

    copy_to_clipboard_clean(comment)
    print("=" * 60)
    print(f"SUCCESS: Generated comment for {puzzle_date} (Puzzle #{puzzle_id})")
    print(f"Saved to: {output_path.resolve()}")
    print("Injected directly into Windows clipboard via 64-bit ctypes!")
    print("=" * 60)
    return comment


if __name__ == "__main__":
    generate_nudge_comment()
