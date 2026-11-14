import asyncio
from playwright.async_api import async_playwright

async def verify_live():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Test live Firebase URL
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto("https://connectionsassistant.com/breakdowns.html", wait_until="networkidle")
        await page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/live_narrow_desktop.png")
        
        spotlight = page.locator("#today")
        if await spotlight.count() > 0:
            await spotlight.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/live_narrow_spotlight.png")
            
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto("https://connectionsassistant.com/breakdowns.html", wait_until="networkidle")
        await mobile_page.screenshot(path="C:/Users/Infinite/.gemini/antigravity/brain/deba67d0-cd17-4201-8eac-06f483d25f88/live_narrow_mobile.png")
        
        await browser.close()
    print("Live verification screenshots taken!")

asyncio.run(verify_live())
