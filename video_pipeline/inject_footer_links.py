import os

target_file = os.path.abspath("../public/index.html")

with open(target_file, "r", encoding="utf-8") as f:
    html = f.read()

# Current footer-links section
target_str = '<a href="contact.html">Contact Us</a>'

new_links = (
    '<a href="contact.html">Contact Us</a>\n'
    '      <a href="https://www.reddit.com/user/ConnectionsCoach/" target="_blank" rel="noopener noreferrer">Reddit: u/ConnectionsCoach</a>\n'
    '      <a href="https://www.youtube.com/@ConnectionsAssistant" target="_blank" rel="noopener noreferrer">YouTube: @ConnectionsAssistant</a>'
)

if "ConnectionsCoach" in html:
    print("Reddit link is already present in public/index.html!")
elif target_str in html:
    updated_html = html.replace(target_str, new_links)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("Successfully added Reddit and YouTube community links to the footer in public/index.html!")
else:
    print("Target anchor string not matched.")
