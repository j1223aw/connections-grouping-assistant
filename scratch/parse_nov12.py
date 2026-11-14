with open('public/breakdowns/2026-11-12.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Header:")
for h in re.findall(r'<h2[^>]*>.*?</h2>', text):
    print(" ", h)

print("\nWords & Categories:")
categories = re.findall(r'<span class="tier-label-name">([^<]+)</span>', text)
print("Categories:", categories)

words = re.findall(r'<span class="word-pill"[^>]*>([^<]+)</span>', text)
print(f"Words ({len(words)}):", words)

red_herring = re.findall(r'<div class="trap-advisory-box">([\s\S]*?)</div>', text)
if red_herring:
    print("Red Herring:", red_herring[0].strip()[:200])

video_src = re.findall(r'<iframe[^>]+src="([^"]+)"', text)
print("Video iframe:", video_src)
video_config = re.findall(r'const VIDEO_CONFIG = \{[\s\S]*?\};', text)
print("Video config:", video_config)
