with open('public/breakdowns.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
m = re.search(r'<!-- PAST PUZZLE BREAKDOWNS & HISTORY SECTION -->([\s\S]*?)</section>', text)
if m:
    links = re.findall(r'href="([^"]+)"', m.group(1))
    print('Archive links in breakdowns.html:', links[:10])
