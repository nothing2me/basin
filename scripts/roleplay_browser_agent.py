import asyncio
import os
import re
import shutil
import time
from pathlib import Path
from playwright.async_api import async_playwright
import pypdfium2 as pdfium

ROOT = Path(r"c:\Users\Noahw\Documents\ChatGPT\basin")
ARTIFACTS_DIR = Path(r"C:\Users\Noahw\.gemini\antigravity\brain\76b8cb76-d4bc-465a-921c-86ccf0a31ef7")

async def run_roleplay_agent():
    print("========================================================================")
    print("ROLEPLAY AGENT: ELENA VANCE (LEAD HYDROLOGIST, REGION N PLANNING GROUP)")
    print("EXECUTING LIVE BROWSER RUN START TO FINISH ON BASIN")
    print("========================================================================")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 1020})
        page = await context.new_page()

        # ----------------------------------------------------------------------
        # STEP 1: OBSERVATION BASELINE & DATA SOURCES
        # ----------------------------------------------------------------------
        print("\n>>> [Step 1] Loading Observation Baseline & Data Sources...")
        await page.goto("http://127.0.0.1:8501", wait_until="networkidle", timeout=40000)
        await page.wait_for_timeout(3000)
        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step1_data_baseline.png"))
        print("Captured elena_step1_data_baseline.png")

        # Click 'Accept Baseline & Proceed to Step 2'
        btn_step2 = page.locator(".st-key-nav_next_Workspace button")
        if await btn_step2.is_visible():
            print("Elena Vance accepts observation baseline and proceeds to Step 2...")
            await btn_step2.click()
            await page.wait_for_timeout(2500)

        # ----------------------------------------------------------------------
        # STEP 2: SCENARIO BUILDER & SHORTLIST ENGINE
        # ----------------------------------------------------------------------
        print("\n>>> [Step 2] Scenario Builder & Shortlist Engine...")
        await page.wait_for_selector("text=Step 2: Scenario Builder", timeout=20000)
        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step2_scenario_builder.png"))
        print("Captured elena_step2_scenario_builder.png")

        # Click 'Create rainfall scenarios'
        btn_create = page.locator("button:has-text('Create rainfall scenarios')")
        await btn_create.wait_for(state="visible", timeout=10000)
        print("Elena Vance initiates multi-station scenario sampling (300 candidates, seed 22)...")
        await btn_create.click()

        # Wait for generation to finish
        print("Computing multi-criteria shortlist ranking across 1991-2025 records...")
        await page.wait_for_selector("text=scenarios selected for review", timeout=60000)
        await page.wait_for_timeout(2000)
        print("Shortlist generated successfully!")
        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step2_scenarios_generated.png"))
        print("Captured elena_step2_scenarios_generated.png")

        # Navigate to Step 3: Review Selections
        print("\n>>> Navigating to Step 3: Review Selections...")
        btn_nav_review = page.locator(".st-key-nav_tab_Review button")
        await btn_nav_review.click()
        await page.wait_for_timeout(3000)

        # ----------------------------------------------------------------------
        # STEP 3: REVIEW, RATIONALE NOTES & RESERVOIR STORAGE EXPERIMENT
        # ----------------------------------------------------------------------
        print("\n>>> [Step 3] Review & Refine Selections...")
        btn_focus_skip = page.locator("button:has-text('Skip for now')")
        if await btn_focus_skip.is_visible():
            print("Dismissing review focus setup card...")
            await btn_focus_skip.click()
            await page.wait_for_timeout(2000)

        # Batch Review: provide overarching hydrologist rationale
        batch_expander = page.locator("summary:has-text('Batch Review')")
        if await batch_expander.is_visible():
            print("Expanding Batch Review panel...")
            await batch_expander.click()
            await page.wait_for_timeout(1000)
            
            batch_input = page.locator("input[aria-label='Batch review rationale']")
            if await batch_input.is_visible():
                batch_rationale = (
                    "Hydrologist Review by Elena Vance (Region N): Verified severe summer drought analogues "
                    "across NOAA index gauges (Corpus Christi, Victoria, San Antonio). Multi-station concurrence "
                    "and precipitation deficits confirm acute stress conditions suitable for dual-reservoir safe-yield screening."
                )
                print(f"Entering batch review rationale ({len(batch_rationale)} chars)...")
                await batch_input.fill(batch_rationale)
                await batch_input.press("Enter")
                await page.wait_for_timeout(2500)
                
                btn_batch_inc = page.locator("button:has-text('Include all pending shortlisted scenarios')")
                if await btn_batch_inc.is_visible() and not await btn_batch_inc.is_disabled():
                    print("Clicking 'Include all pending shortlisted scenarios'...")
                    await btn_batch_inc.click()
                    await page.wait_for_timeout(3000)
                    print("Batch inclusion applied!")

        # Also write a specific review note on the current scenario
        note_area = page.locator("textarea[aria-label='Review note']")
        if await note_area.is_visible():
            indiv_note = (
                "Primary screening candidate evaluation (Elena Vance): Peak summer drought sequence with 83% "
                "multi-station concurrence and 7.39-inch precipitation shortfall. Climatological anomaly exceeds "
                "the 96th percentile of historical records. Formally approved for reservoir depletion modeling."
            )
            print("Adding detailed individual review note...")
            await note_area.fill(indiv_note)
            await page.wait_for_timeout(500)
            btn_include = page.locator("button:has-text('Include')").first
            if await btn_include.is_enabled():
                await btn_include.click()
                await page.wait_for_timeout(2000)
                print("Individual review note saved!")

        # Turn on the storage experiment toggle
        print("Toggling illustrative reservoir storage experiment...")
        storage_toggle = page.locator("label:has-text('Explore storage under assumed conditions')")
        if await storage_toggle.is_visible():
            await storage_toggle.click()
            await page.wait_for_timeout(2000)
            print("Storage experiment enabled.")

            # Scroll down to view the storage experiment
            await page.evaluate("window.scrollBy(0, 700)")
            await page.wait_for_timeout(1000)

            # Check for simulation review note input
            sim_rationale_input = page.locator("input[placeholder='What did you check?']")
            if await sim_rationale_input.is_visible():
                sim_note = (
                    "Hydrologic depletion review by E. Vance: Tested dual-reservoir drawdown under 35% starting storage "
                    "and 15% emergency conservation mandate. Critical Band 2 threshold breached at Day 72."
                )
                print("Entering simulation review rationale...")
                await sim_rationale_input.fill(sim_note)
                await sim_rationale_input.press("Enter")
                await page.wait_for_timeout(1500)
                
                btn_save_sim = page.locator("button:has-text('Save experiment review')")
                if await btn_save_sim.is_visible():
                    print("Saving experiment review...")
                    await btn_save_sim.click()
                    await page.wait_for_timeout(3000)
                    print("Experiment review saved successfully!")

        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step3_review_completed.png"))
        print("Captured elena_step3_review_completed.png")

        # ----------------------------------------------------------------------
        # STEP 4: VERIFIED EXPORT
        # ----------------------------------------------------------------------
        print("\n>>> [Step 4] Navigating to Step 4: Export...")
        btn_nav_export = page.locator(".st-key-nav_tab_Exports button")
        await btn_nav_export.click()
        await page.wait_for_timeout(3000)

        # Check 'Include provider notes and free-text review notes'
        share_notes_checkbox = page.locator("label:has-text('Include provider notes and free-text review notes')")
        if await share_notes_checkbox.is_visible():
            print("Checking 'Include provider notes and free-text review notes'...")
            await share_notes_checkbox.click()
            await page.wait_for_timeout(1000)

        # Sign off on any simulation reviews if button appears
        btn_approve_sims = page.locator("button:has-text('Approve simulation reviews')")
        if await btn_approve_sims.is_visible():
            print("Approving simulation reviews...")
            await btn_approve_sims.click()
            await page.wait_for_timeout(2000)

        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step4_export_ready.png"))
        print("Captured elena_step4_export_ready.png")

        # Click 'Build verified export'
        btn_build_export = page.locator(".st-key-btn_build_verified_export button")
        await btn_build_export.wait_for(state="visible", timeout=10000)
        
        is_disabled = await btn_build_export.is_disabled()
        print(f"Build verified export button disabled: {is_disabled}")
        if is_disabled:
            raise RuntimeError("Build verified export button is unexpectedly disabled!")

        print("Clicking 'Build verified export'...")
        await btn_build_export.click()
        
        print("Waiting for export compilation, vector PDF rendering, and cryptographic verification...")
        # Wait for export completion (either Download Executive Brief button or Verified Export Package Ready)
        await page.wait_for_selector("text=Download Executive Brief (PDF), text=Verified Export Package Ready", timeout=60000)
        await page.wait_for_timeout(3000)
        print("Export completed successfully!")

        await page.screenshot(path=str(ARTIFACTS_DIR / "elena_step4_export_complete.png"))
        print("Captured elena_step4_export_complete.png")

        await browser.close()

    # Find the newly generated PDF in ROOT / output
    out_dir = ROOT / "output"
    pdf_files = list(out_dir.glob("BASIN-Executive-Brief-*.pdf"))
    if not pdf_files:
        raise RuntimeError("No exported PDF found in output directory!")
    
    # Sort by modification time to get the latest
    pdf_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    latest_pdf = pdf_files[0]
    print(f"\n>>> Latest Generated PDF: {latest_pdf} ({latest_pdf.stat().st_size:,} bytes)")

    # Copy to artifacts directory
    target_artifact_pdf = ARTIFACTS_DIR / "BASIN_Elena_Vance_Executive_Brief.pdf"
    shutil.copy2(latest_pdf, target_artifact_pdf)
    print(f"Copied PDF to artifact: {target_artifact_pdf}")

    # Render PDF pages to PNG using pypdfium2
    print("\n>>> Rendering PDF pages to high-resolution PNG artifacts...")
    doc = pdfium.PdfDocument(target_artifact_pdf)
    num_pages = len(doc)
    print(f"Total pages: {num_pages}")
    for i in range(num_pages):
        page_doc = doc[i]
        # Render at 2.0x scale (144 dpi)
        image = page_doc.render(scale=2.0).to_pil()
        page_png_path = ARTIFACTS_DIR / f"elena_brief_page_{i+1}.png"
        image.save(page_png_path)
        print(f"Rendered Page {i+1} -> {page_png_path}")

    # Also copy the Markdown handoff brief
    brief_files = list(out_dir.glob("Hydrologist_Handoff_Brief_*.md"))
    brief_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    if brief_files:
        latest_brief = brief_files[0]
        target_artifact_brief = ARTIFACTS_DIR / "Hydrologist_Handoff_Brief_Elena_Vance.md"
        shutil.copy2(latest_brief, target_artifact_brief)
        print(f"Copied Brief to artifact: {target_artifact_brief}")

    print("\n========================================================================")
    print("ROLEPLAY BROWSER EXECUTION AND DELIVERABLE GENERATION COMPLETE!")
    print("========================================================================")

if __name__ == "__main__":
    asyncio.run(run_roleplay_agent())
