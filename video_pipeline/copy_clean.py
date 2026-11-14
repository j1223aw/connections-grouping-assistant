import os
import ctypes

def set_clipboard_utf8_direct(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return
        
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    # Direct Windows Win32 API UTF-16LE clipboard copy
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    encoded = text.encode("utf-16le") + b"\x00\x00"
    h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(encoded))
    p_mem = kernel32.GlobalLock(h_mem)
    ctypes.memmove(p_mem, encoded, len(encoded))
    kernel32.GlobalUnlock(h_mem)
    
    user32.OpenClipboard(None)
    user32.EmptyClipboard()
    user32.SetClipboardData(CF_UNICODETEXT, h_mem)
    user32.CloseClipboard()
    print("Clean UTF-8 text copied to clipboard successfully!")

if __name__ == "__main__":
    set_clipboard_utf8_direct("today_reddit_comment.txt")
