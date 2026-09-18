import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1050})
        page = await context.new_page()
        
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Step 1 -> Step 2
        btn_step2 = page.locator(".st-key-nav_next_Workspace button")
        if await btn_step2.is_visible():
            await btn_step2.click()
            await page.wait_for_timeout(2000)
            
        # Step 2 -> Create scenarios
        btn_create = page.locator("button:has-text('Create rainfall scenarios')")
        if await btn_create.is_visible():
            await btn_create.click()
            await page.wait_for_selector("text=scenarios selected for review", timeout=45000)
            await page.wait_for_timeout(2000)
            
        # Step 3 -> Go to Review
        btn_nav_review = page.locator(".st-key-nav_tab_Review button")
        await btn_nav_review.click()
        await page.wait_for_timeout(3000)
        
        # In Setup card, select Advanced View!
        radio_adv = page.locator("label:has-text('Advanced View')")
        if await radio_adv.is_visible():
            print("Selecting Advanced View on setup card...")
            await radio_adv.click()
            await page.wait_for_timeout(1000)
            btn_use_focus = page.locator("button:has-text('Use this focus')")
            if await btn_use_focus.is_visible():
                await btn_use_focus.click()
                await page.wait_for_timeout(2500)
                print("Advanced View applied!")
        else:
            # If setup card dismissed, look for segmented control or change focus
            print("Setup card not visible; checking for mode control...")
            btn_change = page.locator("button:has-text('Change focus')")
            if await btn_change.is_visible():
                await btn_change.click()
                await page.wait_for_timeout(1500)
                await page.locator("label:has-text('Advanced View')").click()
                await page.locator("button:has-text('Use this focus')").click()
                await page.wait_for_timeout(2000)

        # Toggle storage experiment
        toggle_exp = page.locator("label:has-text('Explore storage under assumed conditions')")
        if await toggle_exp.is_visible():
            print("Enabling storage experiment...")
            await toggle_exp.click()
            await page.wait_for_timeout(2000)
            
            # Scroll down to storage experiment
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(1000)
            
            # In Advanced View, check Initial Storage selectbox
            print("Checking Initial storage selectbox...")
            # Let's inspect selectboxes
            selects = await page.locator("div[data-testid='stSelectbox']").all_inner_texts()
            print("Selectboxes on page:", selects)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
