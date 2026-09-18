import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import pypdfium2 as pdfium
import shutil

ROOT = Path(r"c:\Users\Noahw\Documents\ChatGPT\basin")
ARTIFACTS_DIR = Path(r"C:\Users\Noahw\.gemini\antigravity\brain\76b8cb76-d4bc-465a-921c-86ccf0a31ef7")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1050})
        page = await context.new_page()
        
        print("1. Opening Step 1...")
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        # Check 'Skip tailoring and show every Review tool' on Step 1
        skip_checkbox = page.locator("label:has-text('Skip tailoring and show every Review tool')")
        if await skip_checkbox.is_visible():
            print("Enabling full technical review tools on Step 1...")
            await skip_checkbox.click()
            await page.wait_for_timeout(1000)
            
        # Click 'Accept Baseline & Proceed to Step 2'
        btn_step2 = page.locator(".st-key-nav_next_Workspace button").first
        if await btn_step2.is_visible():
            print("Accepting baseline...")
            await btn_step2.click()
            await page.wait_for_timeout(2500)
            
        # Step 2: Create scenarios
        print("2. Generating scenarios...")
        btn_create = page.locator("button:has-text('Create rainfall scenarios')").first
        await btn_create.click()
        await page.wait_for_selector("text=scenarios selected for review", timeout=45000)
        await page.wait_for_timeout(2000)
        print("Scenarios generated!")
        
        # Step 3: Go to Review
        print("3. Navigating to Step 3 Review...")
        btn_review = page.locator(".st-key-nav_tab_Review button").first
        await btn_review.click()
        await page.wait_for_timeout(3000)
        
        # Check if focus modal is visible
        btn_skip_focus = page.locator("button:has-text('Skip for now')")
        if await btn_skip_focus.is_visible():
            await btn_skip_focus.click()
            await page.wait_for_timeout(2000)
            
        # Batch review
        batch_expander = page.locator("summary:has-text('Batch Review')")
        if await batch_expander.is_visible():
            print("Executing batch review...")
            await batch_expander.click()
            await page.wait_for_timeout(1000)
            batch_input = page.locator("input[aria-label='Batch review rationale']")
            if await batch_input.is_visible():
                await batch_input.fill("Hydrologist Review by Elena Vance: Verified severe summer drought analogues for dual-reservoir stress screening under 39.9% antecedent storage context.")
                await batch_input.press("Enter")
                await page.wait_for_timeout(2000)
                btn_batch_inc = page.locator("button:has-text('Include all pending shortlisted scenarios')")
                if await btn_batch_inc.is_visible():
                    await btn_batch_inc.click()
                    await page.wait_for_timeout(3000)
                    print("Batch review accepted!")

        # Illustrative storage experiment
        print("Enabling illustrative storage experiment...")
        storage_toggle = page.locator("label:has-text('Explore storage under assumed conditions')")
        if await storage_toggle.is_visible():
            await storage_toggle.click()
            await page.wait_for_timeout(2500)
            
            # Scroll down to storage section
            await page.evaluate("window.scrollBy(0, 800)")
            await page.wait_for_timeout(1000)
            
            # Look for Initial storage selectbox
            # In Streamlit, selectbox for initial storage has label 'Initial storage'
            init_storage_container = page.locator("div[data-testid='stSelectbox']:has-text('Initial storage')")
            if await init_storage_container.is_visible():
                print("Selecting 35% (illustrative) initial storage...")
                await init_storage_container.click()
                await page.wait_for_timeout(800)
                opt_35 = page.locator("li[role='option']:has-text('35% (illustrative)')")
                if await opt_35.is_visible():
                    await opt_35.click()
                    await page.wait_for_timeout(2000)
                    print("35% selected!")

            # Simulation review note
            sim_input = page.locator("input[placeholder='What did you check?']")
            if await sim_input.is_visible():
                print("Entering custom simulation rationale...")
                sim_text = "Hydrologic depletion review by E. Vance: Tested dual-reservoir drawdown under 35% antecedent storage context (September 2026 reality: Choke Canyon at 22.5%). Verified Band 2 breach."
                await sim_input.fill(sim_text)
                await sim_input.press("Enter")
                await page.wait_for_timeout(1000)
                
                btn_save_sim = page.locator("button:has-text('Save experiment review')")
                if await btn_save_sim.is_visible():
                    print("Clicking 'Save experiment review'...")
                    await btn_save_sim.click()
                    await page.wait_for_timeout(3000)
                    print("Custom experiment review recorded successfully!")

        # Step 4: Export
        print("4. Navigating to Step 4 Export...")
        btn_export_tab = page.locator(".st-key-nav_tab_Exports button").first
        await btn_export_tab.click()
        await page.wait_for_timeout(3000)
        
        # Include notes checkbox
        share_notes = page.locator("label:has-text('Include provider notes and free-text review notes')")
        if await share_notes.is_visible():
            await share_notes.click()
            await page.wait_for_timeout(1000)
            
        # Click Build verified export
        btn_build = page.locator(".st-key-btn_build_verified_export button").first
        print(f"Build export button disabled: {await btn_build.is_disabled()}")
        await btn_build.click()
        print("Building export bundle and rendering vector PDF...")
        
        # Wait for download button to appear
        await page.wait_for_selector("text=Download Executive Brief (PDF)", timeout=60000)
        await page.wait_for_timeout(3000)
        print("Verified export complete!")
        
        await browser.close()
        
    # Check latest generated PDF
    out_dir = ROOT / "output"
    pdf_files = list(out_dir.glob("BASIN-Executive-Brief-*.pdf"))
    pdf_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_pdf = pdf_files[0]
    print(f"\nGenerated PDF: {latest_pdf.name} ({latest_pdf.stat().st_size:,} bytes)")
    
    # Copy to artifacts
    shutil.copy2(latest_pdf, ARTIFACTS_DIR / "BASIN_Elena_Vance_Executive_Brief.pdf")
    
    # Render page 3 to verify configuration source
    doc = pdfium.PdfDocument(latest_pdf)
    print(f"Total pages: {len(doc)}")
    for i in range(len(doc)):
        img = doc[i].render(scale=2.0).to_pil()
        img.save(ARTIFACTS_DIR / f"elena_brief_page_{i+1}.png")
    print("Rendered all pages to artifacts!")

if __name__ == "__main__":
    asyncio.run(main())
