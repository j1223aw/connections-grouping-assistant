import subprocess
import sys

def copy_to_clipboard_utf8(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    # Uses Windows clip command or PowerShell directly with explicit UTF-8 encoding
    cmd = ["powershell", "-NoProfile", "-Command", "$OutputEncoding = [Console]::InputEncoding = [Text.Encoding]::UTF8; Set-Clipboard -Value $args[0]"]
    subprocess.run(cmd, input=content, text=True, encoding="utf-8")

if __name__ == "__main__":
    copy_to_clipboard_utf8("today_reddit_comment.txt")
    print("Copied today_reddit_comment.txt to clipboard with clean UTF-8 encoding!")
