import os
import sys
import json
import urllib.request
import ctypes
from ctypes import wintypes
from datetime import datetime

def copy_to_clipboard_clean(text):
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    # 64-bit explicit signatures
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

def generate_nudge_comment():
    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.nytimes.com/svc/connections/v2/{today_str}.json"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Failed to fetch live NYT data for {today_str}: {e}")
        return

    groups = {g.get("level", 0): g for g in data.get("categories", [])}
    
    hints = {
        0: f">!Think about {groups.get(0, {}).get('title', '').lower()}.!<",
        1: f">!Items associated with {groups.get(1, {}).get('title', '').lower()}.!<",
        2: f">!Look for shared connections to {groups.get(2, {}).get('title', '').lower()}.!<",
        3: f">!Wordplay alert: {groups.get(3, {}).get('title', '').lower()}.!<"
    }
    
    comment = f"""**Progressive Nudges & Clues for Today ({today_str}) — No Direct Spoilers:**

* 🟨 **Yellow Group Hint:** {hints[0]}
* 🟩 **Green Group Hint:** {hints[1]}
* 🟦 **Blue Group Hint:** {hints[2]}
* 🟪 **Purple Group Hint:** {hints[3]}

---
*(Full disclosure: Built a free interactive scratchboard at [connectionsassistant.com](https://connectionsassistant.com) to test candidate groupings without burning your 4 guesses. Daily visual video breakdowns: [@ConnectionsAssistant](https://www.youtube.com/@ConnectionsAssistant))*"""

    with open("today_reddit_comment.txt", "w", encoding="utf-8") as f:
        f.write(comment)
        
    copy_to_clipboard_clean(comment)
    print("==================================================")
    print("SUCCESS: Today's Reddit comment generated and copied directly to your clipboard!")
    print("==================================================")

if __name__ == "__main__":
    generate_nudge_comment()
