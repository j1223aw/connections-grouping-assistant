import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

html = open("public/breakdowns.html", encoding="utf-8").read()
html = html.replace("max-width: 960px;", "max-width: 860px;")

old_daily_layout = """.daily-layout {
            display: grid;
            grid-template-columns: 320px minmax(0, 1fr);
            gap: 24px;
            align-items: start;
        }
        .daily-video-wrapper {
            min-width: 0;
            width: 100%;
        }
        .daily-tactics {
            min-width: 0;
            width: 100%;
        }"""

new_daily_layout_520 = """.daily-layout {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .daily-video-wrapper {
            max-width: 520px;
            margin: 0 auto;
            width: 100%;
        }
        .daily-tactics {
            width: 100%;
        }"""

html_520 = html.replace(old_daily_layout, new_daily_layout_520)
Path("scratch/test_520.html").write_text(html_520, encoding="utf-8")

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(f"file:///{Path('scratch/test_520.html').resolve().as_posix()}", wait_until="networkidle")
        await page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/test_520_viewport.png")
        await page.click("#tab-masterclass")
        await page.wait_for_timeout(300)
        await page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/test_520_masterclass_viewport.png")
        await browser.close()
    print("520 captured")

asyncio.run(test())
