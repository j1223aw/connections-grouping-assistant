for path in ['public/strategy.html', 'public/faq.html', 'public/nyt-connections-guide.html']:
    c = open(path, encoding='utf-8').read()
    import re
    links = re.findall(r'<link[^>]+>', c)
    print(path, 'links:', [l for l in links if 'stylesheet' in l])
    m = re.findall(r'style\.css', c)
    print(path, 'style.css refs:', len(m))
