import os
import re

# Look for index.html or site HTML files in current or parent directory
candidates = [
    os.path.abspath("../index.html"),
    os.path.abspath("./index.html"),
    os.path.abspath("../public/index.html")
]

target_file = None
for p in candidates:
    if os.path.exists(p):
        target_file = p
        break

if not target_file:
    # Walk directory to find index.html
    root_dir = os.path.abspath("..")
    for root, dirs, files in os.walk(root_dir):
        if "index.html" in files:
            target_file = os.path.join(root, "index.html")
            break

if not target_file:
    print("Could not locate index.html automatically. Please verify the folder structure.")
else:
    with open(target_file, "r", encoding="utf-8") as f:
        html = f.read()

    reddit_snippet = (
        '<a href="https://www.reddit.com/user/ConnectionsCoach/" '
        'target="_blank" rel="noopener noreferrer" '
        'class="text-gray-400 hover:text-amber-400 transition-colors flex items-center gap-1.5">'
        'Reddit: u/ConnectionsCoach</a>'
    )

    if "ConnectionsCoach" in html:
        print(f"Reddit link already present in {target_file}")
    elif "ConnectionsAssistant" in html:
        # Insert right after the YouTube link/mention
        pattern = r'(<a[^>]*youtube\.com/@ConnectionsAssistant[^>]*>.*?</a>)'
        replacement = r'\1\n        ' + reddit_snippet
        new_html, count = re.subn(pattern, replacement, html, flags=re.DOTALL)
        if count > 0:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(new_html)
            print(f"Successfully added Reddit link to footer in {target_file}")
        else:
            print(f"Found {target_file}, but could not find exact YouTube anchor pattern to attach to.")
    else:
        print(f"Located {target_file}, but could not find existing social footer block.")
