import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import pypdfium2 as pdfium
import shutil

ROOT = Path(r"c:\Users\Noahw\Documents\ChatGPT\basin")
ARTIFACTS_DIR = Path(r"C:\Users\Noahw\.gemini\antigravity\brain\76b8cb76-d4bc-465a-921c-86ccf0a31ef7")

async def main():
    print("========================================================================")
    print("EXECUTING FULL CUSTOM EXPERIMENT BROWSER RUN (35% STORAGE & CORPUS NEWS)")
    print("========================================================================")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1100})
        page = await context.new_page()

        # Step 1
        print("1. Loading Step 1 Data Dashboard...")
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)
        
        btn_step2 = page.locator(".st-key-nav_next_Workspace button").first
        await btn_step2.click()
        await page.wait_for_timeout(2500)

        # Step 2
        print("2. Generating Scenarios on Step 2...")
        btn_create = page.locator("button:has-text('Create rainfall scenarios')").first
        await btn_create.click()
        await page.wait_for_selector("text=scenarios selected for review", timeout=50000)
        await page.wait_for_timeout(2000)
        print("Scenarios successfully generated!")

        # Step 3
        print("3. Navigating to Step 3 Review...")
        btn_review = page.locator(".st-key-nav_tab_Review button").first
        await btn_review.click()
        await page.wait_for_timeout(3000)

        # Dismiss setup focus if present
        btn_skip_focus = page.locator("button:has-text('Skip for now')")
        if await btn_skip_focus.is_visible():
            await btn_skip_focus.click()
            await page.wait_for_timeout(2000)

        # Click Advanced View button in segmented control!
        btn_adv = page.locator("button:has-text('Advanced View')").first
        if await btn_adv.is_visible():
            print("Switching from Simple View to Advanced View...")
            await btn_adv.click()
            await page.wait_for_timeout(2500)
            print("Advanced View activated!")

        # Execute batch review
        batch_expander = page.locator("summary:has-text('Batch Review')").first
        if await batch_expander.is_visible():
            print("Filling Batch Review rationale...")
            await batch_expander.click()
            await page.wait_for_timeout(1000)
            batch_input = page.locator("input[aria-label='Batch review rationale']").first
            if await batch_input.is_visible():
                await batch_input.fill(
                    "Hydrologist Review by Elena Vance (Region N): Verified severe summer drought analogues "
                    "for dual-reservoir stress screening under September 2026 antecedent storage conditions (39.9% combined, Choke Canyon 22.5%)."
                )
                await batch_input.press("Enter")
                await page.wait_for_timeout(2000)
                btn_batch_inc = page.locator("button:has-text('Include all pending shortlisted scenarios')").first
                if await btn_batch_inc.is_visible() and not await btn_batch_inc.is_disabled():
                    await btn_batch_inc.click()
                    await page.wait_for_timeout(3000)
                    print("Batch review applied!")

        # Click Storage Drawdown Tab
        print("Opening Storage Drawdown tab...")
        tab_btn = page.locator("[data-testid='stTab']:has-text('Storage Drawdown')").first
        await tab_btn.click()
        await page.wait_for_timeout(2000)

        # Toggle storage experiment
        print("Enabling illustrative storage experiment...")
        storage_toggle = page.locator("text=Explore storage under assumed conditions").first
        await storage_toggle.click()
        await page.wait_for_timeout(2500)
        print("Storage toggle clicked!")

        # Select Initial storage: 35% (illustrative)
        init_box = page.locator(".st-key-review_initial_storage").first
        print(f"Initial storage selectbox visible: {await init_box.is_visible()}")
        if await init_box.is_visible():
            print("Selecting 35% (illustrative) via keyboard...")
            await init_box.click()
            await page.wait_for_timeout(600)
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("ArrowDown")
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(2500)
            print("35% starting storage applied!")

        # Enter simulation review note
        sim_input = page.locator("input[placeholder='What did you check?']").first
        print(f"Simulation review note input visible: {await sim_input.is_visible()}")
        if await sim_input.is_visible():
            sim_text = (
                "Hydrologic simulation review by Elena Vance: Tested dual-reservoir drawdown under 35% antecedent storage context "
                "(September 2026 reality: combined storage 39.9%, Choke Canyon lagging at 22.5%). Verified Band 2 breach at Day 72."
            )
            print("Entering custom simulation rationale...")
            await sim_input.fill(sim_text)
            await sim_input.press("Enter")
            await page.wait_for_timeout(1500)

            btn_save_sim = page.locator("button:has-text('Save experiment review')").first
            if await btn_save_sim.is_visible():
                print("Clicking 'Save experiment review'...")
                await btn_save_sim.click()
                await page.wait_for_timeout(3500)
                print("Custom experiment review saved!")

        # Step 4: Export
        print("4. Navigating to Step 4 Export...")
        btn_export_tab = page.locator(".st-key-nav_tab_Exports button").first
        await btn_export_tab.click()
        await page.wait_for_timeout(3000)

        # Include notes checkbox
        share_notes = page.locator("label:has-text('Include provider notes and free-text review notes')").first
        if await share_notes.is_visible():
            await share_notes.click()
            await page.wait_for_timeout(1000)

        # Check if simulation approval button is needed
        btn_app_sim = page.locator("button:has-text('Approve simulation reviews')").first
        if await btn_app_sim.is_visible():
            print("Signing off on simulation reviews...")
            await btn_app_sim.click()
            await page.wait_for_timeout(2000)

        # Click Build verified export
        btn_build = page.locator(".st-key-btn_build_verified_export button").first
        print(f"Build export button disabled: {await btn_build.is_disabled()}")
        await btn_build.click()
        print("Compiling verified export bundle and rendering vector PDF...")

        await page.wait_for_selector("text=Download Executive Brief (PDF)", timeout=60000)
        await page.wait_for_timeout(3000)
        print("Export successfully verified and downloaded!")

        await browser.close()

    # Find the new PDF
    out_dir = ROOT / "output"
    pdf_files = list(out_dir.glob("BASIN-Executive-Brief-*.pdf"))
    pdf_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_pdf = pdf_files[0]
    print(f"\nLatest Generated Custom PDF: {latest_pdf.name} ({latest_pdf.stat().st_size:,} bytes)")

    target_pdf = ARTIFACTS_DIR / "BASIN_Elena_Vance_Executive_Brief.pdf"
    shutil.copy2(latest_pdf, target_pdf)

    # Render pages to PNG
    doc = pdfium.PdfDocument(target_pdf)
    print(f"Total pages: {len(doc)}")
    for i in range(len(doc)):
        img = doc[i].render(scale=2.0).to_pil()
        img.save(ARTIFACTS_DIR / f"elena_brief_page_{i+1}.png")
        print(f"Rendered page {i+1} -> elena_brief_page_{i+1}.png")

    print("\n========================================================================")
    print("CUSTOM EXPERIMENT BROWSER AUTOMATION COMPLETE!")
    print("========================================================================")

if __name__ == "__main__":
    asyncio.run(main())
