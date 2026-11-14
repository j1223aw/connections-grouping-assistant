import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

html = open("public/breakdowns.html", encoding="utf-8").read()

# Replace container max-width with 860px
html_variant = html.replace("max-width: 960px;", "max-width: 860px;")

# Replace daily-layout CSS
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

new_daily_layout = """.daily-layout {
            display: flex;
            flex-direction: column;
            gap: 24px;
        }
        .daily-video-wrapper {
            max-width: 480px;
            margin: 0 auto;
            width: 100%;
        }
        .daily-tactics {
            width: 100%;
        }"""

html_variant = html_variant.replace(old_daily_layout, new_daily_layout)

temp_path = Path("scratch/test_narrow.html")
temp_path.write_text(html_variant, encoding="utf-8")

async def test():
    file_url = f"file:///{temp_path.resolve().as_posix()}"
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(file_url, wait_until="networkidle")
        
        spotlight = page.locator("#today")
        await spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/test_narrow_short_desktop.png")
        
        # Click Masterclass tab
        await page.click("#tab-masterclass")
        await page.wait_for_timeout(300)
        await spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/test_narrow_masterclass_desktop.png")
        
        # Mobile view
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto(file_url, wait_until="networkidle")
        mobile_spotlight = mobile_page.locator("#today")
        await mobile_spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/test_narrow_mobile.png")
        
        await browser.close()
    print("Variant A captured")

asyncio.run(test())
