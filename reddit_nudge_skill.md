# Reddit Nudge Skill Specification

## Purpose
The Reddit Dispatcher node formats and dispatches daily spoiler-shielded clue comments to Reddit word puzzle discussion threads (e.g., `r/NYTConnections`).

## Comment Structure Standard

1. **Header**:
   - Clear announcement with the puzzle date in `YYYY-MM-DD` format.
   - Explicit disclaimer stating: "No Direct Spoilers".

2. **Progressive Clues (4 Tiers)**:
   - Exactly 4 bullet points formatted with official tier emoji badges:
     - 🟨 **Yellow Group Hint:** `>!Progressive conceptual clue!<`
     - 🟩 **Green Group Hint:** `>!Progressive conceptual clue!<`
     - 🟦 **Blue Group Hint:** `>!Progressive conceptual clue!<`
     - 🟪 **Purple Group Hint:** `>!Progressive conceptual clue!<`
   - Strict `>!spoiler!<` syntax: no leading or trailing space inside the spoiler tags to ensure cross-platform Reddit markdown rendering.

3. **Red Herring Alert**:
   - Prominent `* ⚠️ **Red Herring Alert:** >!Trap breakdown!<` detailing false 5-word candidate overlaps or semantic decoys.

4. **Verified Attribution Disclosure**:
   - Standard footer linking to `connectionsassistant.com` (free interactive scratchboard) and `@ConnectionsAssistant` (daily visual video breakdowns).

## Windows Encoding Hygiene
To prevent mojibake corruption on emoji glyphs (🟨, 🟩, 🟦, 🟪, ⚠️), text must be injected directly into the Windows clipboard as `CF_UNICODETEXT` (UTF-16LE) via 64-bit Win32 API ctypes bindings. Do not pipe via PowerShell stdout.
