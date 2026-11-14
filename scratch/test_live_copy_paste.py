import asyncio
from playwright.async_api import async_playwright

async def test_live_copy_quick_paste():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()
        
        await page.goto("https://connectionsassistant.com/index.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Click Copy 16 Words
        copy_btn = page.locator("#copyTodayBtn")
        await copy_btn.click()
        await page.wait_for_timeout(500)

        # 2. Click Quick Paste
        paste_btn = page.locator("#autoFillBtn")
        await paste_btn.click()
        await page.wait_for_timeout(500)

        # 3. Check values
        w1 = await page.locator("#word-1").input_value()
        w4 = await page.locator("#word-4").input_value()
        w16 = await page.locator("#word-16").input_value()

        print(f"LIVE w1: '{w1}'")
        print(f"LIVE w4: '{w4}' (should be WATER SKIER)")
        print(f"LIVE w16: '{w16}' (should be BROWSE)")

        assert w4 == "WATER SKIER"
        assert w16 == "BROWSE"
        print("LIVE COPY -> QUICK PASTE VERIFICATION PASSED!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_live_copy_quick_paste())
