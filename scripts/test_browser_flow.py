import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    artifacts_dir = Path(r"C:\Users\Noahw\.gemini\antigravity\brain\76b8cb76-d4bc-465a-921c-86ccf0a31ef7")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 950})
        page = await context.new_page()
        
        print("1. Navigating to http://127.0.0.1:8501...")
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)
        
        title = await page.title()
        print(f"Page title: {title}")
        
        # Check Step 1 heading
        step1_heading = page.locator("text=Step 1: Observation Baseline")
        print(f"Step 1 heading visible: {await step1_heading.is_visible()}")
        await page.screenshot(path=str(artifacts_dir / "roleplay_step1_baseline.png"))
        
        # Click Accept Baseline & Proceed to Step 2
        btn_step2 = page.locator("button:has-text('Accept Baseline & Proceed to Step 2')")
        if await btn_step2.is_visible():
            print("Clicking 'Accept Baseline & Proceed to Step 2'...")
            await btn_step2.click()
            await page.wait_for_timeout(3000)
        
        # Check Step 2
        step2_heading = page.locator("text=Step 2: Scenario Builder")
        print(f"Step 2 heading visible: {await step2_heading.is_visible()}")
        await page.screenshot(path=str(artifacts_dir / "roleplay_step2_builder.png"))
        
        # Click Create rainfall scenarios
        btn_create = page.locator("button:has-text('Create rainfall scenarios')")
        if await btn_create.is_visible():
            print("Clicking 'Create rainfall scenarios'...")
            await btn_create.click()
            # Wait for scenarios to compute
            print("Waiting for generation to finish...")
            await page.wait_for_selector("text=scenarios selected for review", timeout=45000)
            print("Scenarios successfully generated!")
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(artifacts_dir / "roleplay_step2_generated.png"))
        
        # Navigate to Step 3: Review Selections
        nav_review = page.locator("button:has-text('Review Selections')")
        print(f"Nav review visible: {await nav_review.is_visible()}")
        await nav_review.click()
        await page.wait_for_timeout(3000)
        
        # Check if setup focus modal/card is there
        btn_focus_skip = page.locator("button:has-text('Skip for now')")
        if await btn_focus_skip.is_visible():
            print("Clicking 'Skip for now' on focus card...")
            await btn_focus_skip.click()
            await page.wait_for_timeout(2000)
        
        await page.screenshot(path=str(artifacts_dir / "roleplay_step3_review.png"))
        print("Step 3 captured successfully!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
