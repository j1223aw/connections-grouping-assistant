import re

html = open('public/breakdowns.html', encoding='utf-8').read()
sec_match = re.search(r'(<section class="daily-spotlight" id="today">.*?</section>)', html, re.DOTALL)
if sec_match:
    sec_html = sec_match.group(1)
    open_divs = len(re.findall(r'<div\b', sec_html))
    close_divs = len(re.findall(r'</div\b', sec_html))
    print(f"Open divs: {open_divs}, Close divs: {close_divs}")
    
    # Check open vs close balance incrementally line by line
    balance = 0
    for line_no, line in enumerate(sec_html.splitlines(), start=815):
        o = len(re.findall(r'<div\b', line))
        c = len(re.findall(r'</div\b', line))
        balance += (o - c)
        if 'chapters-box' in line or 'daily-tactics' in line or 'lexical-accordion' in line:
            print(f"Line {line_no} balance={balance}: {line.strip()[:60]}")
else:
    print("Not found")
