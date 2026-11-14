import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

async def test_copy_then_quick_paste():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await context.new_page()
        
        index_file = Path(r"c:\Users\Infinite\Documents\Connections Grouping Assistant\public\index.html").resolve()
        await page.goto(index_file.as_uri())

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
        w2 = await page.locator("#word-2").input_value()
        w3 = await page.locator("#word-3").input_value()
        w4 = await page.locator("#word-4").input_value()
        w5 = await page.locator("#word-5").input_value()
        w16 = await page.locator("#word-16").input_value()

        print(f"w1: '{w1}'")
        print(f"w2: '{w2}'")
        print(f"w3: '{w3}'")
        print(f"w4: '{w4}' (should be WATER SKIER)")
        print(f"w5: '{w5}' (should be SURF)")
        print(f"w16: '{w16}' (should be BROWSE)")

        assert w4 == "WATER SKIER", f"Expected 'WATER SKIER', got '{w4}'"
        assert w5 == "SURF", f"Expected 'SURF', got '{w5}'"
        assert w16 == "BROWSE", f"Expected 'BROWSE', got '{w16}'"
        print("ALL ASSERTIONS PASSED! Multi-word term intact!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_copy_then_quick_paste())
