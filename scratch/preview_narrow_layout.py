import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def capture():
    html_path = Path("public/breakdowns.html").resolve()
    file_url = f"file:///{html_path.as_posix()}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        # Desktop
        page = await browser.new_page(viewport={"width": 1280, "height": 900})
        await page.goto(file_url, wait_until="networkidle")
        await page.screenshot(path="scratch/current_desktop.png", full_page=False)
        
        spotlight = page.locator("#today")
        if await spotlight.count() > 0:
            await spotlight.screenshot(path="scratch/current_spotlight_desktop.png")
            
        # Mobile
        mobile_page = await browser.new_page(viewport={"width": 390, "height": 844})
        await mobile_page.goto(file_url, wait_until="networkidle")
        mobile_spotlight = mobile_page.locator("#today")
        if await mobile_spotlight.count() > 0:
            await mobile_spotlight.screenshot(path="scratch/current_spotlight_mobile.png")
            
        await browser.close()
    print("Screenshots captured successfully.")

asyncio.run(capture())
