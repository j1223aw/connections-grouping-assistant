import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def capture_all():
    html_path = Path("public/breakdowns.html").resolve()
    file_url = f"file:///{html_path.as_posix()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # 1. Desktop - 1280x900
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(file_url, wait_until="networkidle")
        
        # Capture Desktop Viewport
        await page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/narrow_desktop_viewport.png")
        
        # Capture Spotlight Card (Short mode)
        spotlight = page.locator("#today")
        await spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/narrow_desktop_spotlight_short.png")
        
        # Switch to Masterclass tab
        await page.click("#tab-masterclass")
        await page.wait_for_timeout(300)
        await spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/narrow_desktop_spotlight_masterclass.png")
        
        # 2. Mobile - 390x844 (iPhone 13/14)
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto(file_url, wait_until="networkidle")
        await mobile_page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/narrow_mobile_viewport.png")
        
        mobile_spotlight = mobile_page.locator("#today")
        await mobile_spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/narrow_mobile_spotlight.png")
        
        await browser.close()
    print("All screenshots captured successfully.")

asyncio.run(capture_all())
