import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
from PIL import Image

ARTIFACTS_DIR = Path(r"C:\Users\Infinite\.gemini\antigravity\brain\deba67d0-cd17-4201-8eac-06f483d25f88")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

async def test_live():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 1. Desktop Test
        context = await browser.new_context(
            viewport={"width": 1280, "height": 950},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()
        
        print("Loading live index.html...")
        await page.goto("https://connectionsassistant.com/index.html", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # Screenshot initial deck
        desktop_initial_path = ARTIFACTS_DIR / "live_index_desktop_initial.png"
        await page.screenshot(path=str(desktop_initial_path), full_page=False)
        print("Desktop initial screenshot saved.")

        # Test Fill Board button
        fill_btn = page.locator("#fillTodayBtn")
        await fill_btn.wait_for(state="visible")
        await fill_btn.click()
        await page.wait_for_timeout(1000)

        # Verify tiles filled
        first_input = page.locator("#word-1")
        val0 = await first_input.input_value()
        print(f"First tile input after fill: '{val0}'")

        desktop_filled_path = ARTIFACTS_DIR / "live_index_desktop_filled.png"
        await page.screenshot(path=str(desktop_filled_path), full_page=False)
        print("Desktop filled screenshot saved.")

        # Test Copy button
        copy_btn = page.locator("#copyTodayBtn")
        await copy_btn.click()
        await page.wait_for_timeout(1000)

        desktop_copied_path = ARTIFACTS_DIR / "live_index_desktop_copied.png"
        await page.screenshot(path=str(desktop_copied_path), full_page=False)
        print("Desktop copied screenshot saved.")

        # Test Find Groups button
        find_btn = page.locator("#findBtn")
        await find_btn.click()
        await page.wait_for_timeout(1500)

        desktop_solved_path = ARTIFACTS_DIR / "live_index_desktop_solved.png"
        await page.screenshot(path=str(desktop_solved_path), full_page=False)
        print("Desktop solved screenshot saved.")
        await context.close()

        # 2. Mobile Test
        mobile_context = await browser.new_context(
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            permissions=["clipboard-read", "clipboard-write"]
        )
        mobile_page = await mobile_context.new_page()
        await mobile_page.goto("https://connectionsassistant.com/index.html", wait_until="networkidle")
        await mobile_page.wait_for_timeout(2000)

        mobile_initial_path = ARTIFACTS_DIR / "live_index_mobile_initial.png"
        await mobile_page.screenshot(path=str(mobile_initial_path), full_page=False)

        # Mobile Fill
        m_fill_btn = mobile_page.locator("#fillTodayBtn")
        await m_fill_btn.click()
        await mobile_page.wait_for_timeout(1000)

        mobile_filled_path = ARTIFACTS_DIR / "live_index_mobile_filled.png"
        await mobile_page.screenshot(path=str(mobile_filled_path), full_page=False)
        print("Mobile filled screenshot saved.")

        await browser.close()

        # Crops for presentation
        img_desk = Image.open(desktop_filled_path)
        # Crop to the Today Board and Grid
        crop_desk = img_desk.crop((180, 150, 1100, 850))
        crop_desk.save(ARTIFACTS_DIR / "crop_live_today_deck.png")

        img_mob = Image.open(mobile_filled_path)
        crop_mob = img_mob.crop((0, 100, 390, 750))
        crop_mob.save(ARTIFACTS_DIR / "crop_live_today_mobile.png")
        print("Crops generated successfully.")

if __name__ == "__main__":
    asyncio.run(test_live())
