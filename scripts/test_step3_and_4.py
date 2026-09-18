import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    artifacts_dir = Path(r"C:\Users\Noahw\.gemini\antigravity\brain\76b8cb76-d4bc-465a-921c-86ccf0a31ef7")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Step 1: Click Accept Baseline
        btn_step2 = page.locator(".st-key-nav_next_Workspace button")
        if await btn_step2.is_visible():
            print("Clicking Accept Baseline...")
            await btn_step2.click()
            await page.wait_for_timeout(2000)
        
        # Step 2: Click Create rainfall scenarios
        btn_create = page.locator("button:has-text('Create rainfall scenarios')")
        if await btn_create.is_visible():
            print("Generating scenarios...")
            await btn_create.click()
            await page.wait_for_selector("text=scenarios selected for review", timeout=45000)
            await page.wait_for_timeout(2000)
            print("Generated!")
        
        # Step 3: Go to Review
        print("Navigating to Review...")
        btn_nav_review = page.locator(".st-key-nav_tab_Review button")
        await btn_nav_review.click()
        await page.wait_for_timeout(3000)
        
        btn_focus_skip = page.locator("button:has-text('Skip for now')")
        if await btn_focus_skip.is_visible():
            print("Skipping focus...")
            await btn_focus_skip.click()
            await page.wait_for_timeout(2000)
        
        print("Review page loaded successfully!")
        
        # Check Batch Review Expander
        batch_expander = page.locator("summary:has-text('Batch Review')")
        if await batch_expander.is_visible():
            print("Expanding Batch Review...")
            await batch_expander.click()
            await page.wait_for_timeout(1000)
            
            # Fill batch rationale and press Enter
            batch_input = page.locator("input[aria-label='Batch review rationale']")
            if await batch_input.is_visible():
                await batch_input.fill("Hydrologist Review by Elena Vance: Verified severe summer drought analogues for dual-reservoir stress screening.")
                await batch_input.press("Enter")
                await page.wait_for_timeout(2500)
                
                btn_batch_inc = page.locator("button:has-text('Include all pending shortlisted scenarios')")
                print("Checking if batch button is enabled...")
                await btn_batch_inc.wait_for(state="visible", timeout=5000)
                print(f"Batch button disabled: {await btn_batch_inc.is_disabled()}")
                await btn_batch_inc.click()
                await page.wait_for_timeout(3000)
                print("Batch inclusion successfully clicked!")

        await page.screenshot(path=str(artifacts_dir / "step3_reviewed.png"))
        
        # Step 4: Go to Exports
        print("Navigating to Exports...")
        btn_nav_export = page.locator(".st-key-nav_tab_Exports button")
        await btn_nav_export.click()
        await page.wait_for_timeout(3000)
        
        await page.screenshot(path=str(artifacts_dir / "step4_ready.png"))
        print("Step 4 loaded! Checking export button...")
        
        btn_export = page.locator(".st-key-btn_build_verified_export button")
        print(f"Export button visible: {await btn_export.is_visible()}, disabled: {await btn_export.is_disabled()}")
        
        await browser.close()
        print("Done test!")

if __name__ == "__main__":
    asyncio.run(main())
