with open('public/breakdowns/2026-11-12.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
rows = re.findall(r'<div class="solved-tier-row (tier-[a-z]+)">([\s\S]*?)</div>\s*</div>', text)
print(f"Found {len(rows)} rows")
for cls, content in rows:
    title_m = re.search(r'<span class="tier-title">(.*?)</span>', content)
    words = re.findall(r'<div class="solved-tile[^"]*">(.*?)</div>', content)
    print(cls, title_m.group(1) if title_m else "No title", words)
