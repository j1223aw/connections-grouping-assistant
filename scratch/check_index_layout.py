with open('public/index.html', 'r', encoding='utf-8') as f:
    c = f.read()
import re
print("index.html container:")
for m in re.finditer(r'<([a-z0-9]+)\s+class="([^"]+)"', c):
    tag, cls = m.group(1), m.group(2)
    if any(k in cls for k in ['container', 'layout', 'grid', 'card', 'board', 'solver', 'main']):
        print(f"<{tag} class='{cls}'>")
