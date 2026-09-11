# BASIN Day-Of Surprise Requirement: Rapid-Response Playbook

**Event Date:** Tuesday, September 22, 2026  
**Window:** Exactly 2 Hours (**7:00 AM Release – 9:00 AM Submission Deadline**)  
**Submission Location:** Zoho WorkDrive Finalist Folder & Email to `garrett@zohocorp.com` / `ariel@zohocorp.com`  
**Deck Slide Target:** Dedicated **Slide 18** in Master Deck (*"Day-Of Surprise Response"*)

---

## 1. Golden Rules for the 2-Hour Sprint

1. **Do Not Panic or Rewrite the Core Deck:** The surprise requirement is evaluated on *adaptability*, *clarity*, and *relevance*. Keep Slides 1–17 and 19–25 identical. Only update dedicated Slide 18 and make a focused 1-minute live demo adjustment.
2. **Assign Fixed Team Roles at 7:00 AM:**
   - **Lead 1 (Triage & Slide Author - Noah):** Reads prompt, selects response track, drafts slide copy, and manages clock.
   - **Lead 2 (Software Execution & Screenshot - Mohammed):** Runs the specific parameter shock in `app.py`, captures crisp 1080p screenshot, and verifies test assertions.
   - **Lead 3 (Deck Assembly & Submission - Misha):** Inserts screenshot into Slide 18, reviews typography, builds PDF/PPTX, and submits to Zoho WorkDrive by 8:50 AM.
3. **Hard Cutoff at 8:45 AM:** Stop editing at 8:45 AM. Export PDF and upload to WorkDrive. Late submissions after 9:00 AM face severe rubric penalties.

---

## 2. The 4 Pre-Engineered Response Tracks

```
                                +-------------------------------------------+
                                |      7:00 AM Surprise Requirement         |
                                +---------------------+---------------------+
                                                      |
                 +-------------------+----------------+-------------------+
                 |                   |                |                   |
                 v                   v                v                   v
        +-----------------+ +-----------------+ +-----------------+ +-----------------+
        | Track A: Climate| | Track B: Policy | | Track C: Infra- | | Track D: Social |
        | & Wildfire      | | & Governance    | |   structure     | | & Accessibility |
        +-----------------+ +-----------------+ +-----------------+ +-----------------+
```

### Track A: Climate / Wildfire / Extreme Weather Shock
- **Potential Prompts:**
  - *"Model an unprecedented heatwave with 110°F temperatures and high wildfire risk."*
  - *"Simulate an acute 60-day summer flash drought."*
- **Existing BASIN Code Hook:**
  - Module: `basin_core/agronomics.py` -> `calculate_kbdi()` and `calculate_crop_water_deficit()`.
  - Feature: Tracks cumulative Keetch-Byram Drought Index (0–800) and statutory outdoor burn ban threshold ($KBDI \ge 600$ under Tex. Local Gov't Code § 352.081).
- **Execution (5 minutes):**
  - In `app.py`, go to Step 3 Review -> Agronomics -> Wildfire Risk (KBDI).
  - Set starting KBDI slider to 650. Show the exact date burn-ban conditions trigger.
- **Slide 18 Pitch:**
  - *"BASIN seamlessly handles compounding climate shocks. Within minutes, we evaluated the scenario under extreme heat: KBDI crosses the 600 statutory threshold on Day 42, giving county emergency managers three weeks of advance warning to enact burn bans and preposition firefighting assets."*

### Track B: Policy / Regulatory / Economic Shock
- **Potential Prompts:**
  - *"What happens if a major water user or industry suddenly shuts down or faces legal curtailment?"*
  - *"Simulate a sudden 20% mandate on commercial entities."*
- **Existing BASIN Code Hook:**
  - Module: `basin_core/water_system.py` (`stage_curtailment_active`) and `basin_core/analysis.py` (`simulate_reservoir_drawdown`).
  - Feature: Dynamic multi-sector hierarchical curtailment (Domestic vs. Industrial vs. Outdoor).
- **Execution (5 minutes):**
  - In `app.py`, open Review -> Storage -> Toggle **Dynamic Stage Curtailment**.
  - Show the delivered volume breakdown: Domestic baseload is protected at 100%, Outdoor is cut 100%, and Industrial is curtailed 30% in Stage 4.
- **Slide 18 Pitch:**
  - *"BASIN directly models regulatory governance shocks. This simulation demonstrates the exact policy mandate of the November 3 Fair Water Charter Amendment: curtailing industrial cooling by 30% buys the community +24 days of emergency drinking water survival, proving how data empowers policy decisions."*

### Track C: Infrastructure Failure / Pipeline Outage
- **Potential Prompts:**
  - *"What happens if a treatment plant fails, a pipeline bursts, or water imports are cut off?"*
  - *"Model a critical infrastructure supply chain disruption."*
- **Existing BASIN Code Hook:**
  - Module: `basin_core/water_system.py` (`pipeline_capacity_mgd=0.0`) and `app.py` (Pipeline Outage Resilience Counterfactual).
  - Feature: Instantaneous comparison between active pipeline (72 MGD) and total pipeline outage (0 MGD).
- **Execution (5 minutes):**
  - In `app.py`, uncheck **Pipeline active**.
  - Show the **Pipeline Resilience Metric** banner: Stage 3 is breached **48 days sooner** without the Mary Rhodes Pipeline.
- **Slide 18 Pitch:**
  - *"BASIN instantly isolates single-point-of-failure infrastructure vulnerabilities. Simulating a total pipeline outage reveals that western reservoirs enter critical Stage 3 48 days earlier, highlighting why regional interties are the frontline defense against Day Zero."*

### Track D: Social Equity / Multilingual / Citizen Accessibility
- **Potential Prompts:**
  - *"How does a non-technical citizen or non-English-speaking population use this tool?"*
  - *"Make this accessible to underserved community members."*
- **Existing BASIN Code Hook:**
  - Module: `app.py` (Plain-language four-stage workflow, US Customary / Metric toggle, high-contrast monochrome and colorblind themes).
  - Feature: Zero-install executable, instant 2-page executive summary PDF report.
- **Execution (5 minutes):**
  - Switch theme to `appearance_bw` (high-contrast monochrome) or `appearance_colorblind`.
  - Export the executive markdown summary and generate a side-by-side Spanish translation of the executive overview paragraph.
- **Slide 18 Pitch:**
  - *"Community resilience requires universal access. BASIN features accessible colorblind and high-contrast palettes, an intuitive 4-stage interface requiring zero training, and one-click bilingual PDF briefs designed for Spanish-speaking community town halls across South Texas."*

---

## 3. Hour-by-Hour Timeline: 7:00 AM – 9:00 AM

| Time Window | Team Lead | Action Items |
|---|---|---|
| **07:00 – 07:15** | All | Gather in hotel lobby / workspace. Read organizer prompt email. Classify into Track A, B, C, or D. |
| **07:15 – 07:45** | Mohammed | Launch `app.py`. Configure the surprise scenario in the UI. Capture high-res 1080p screenshot. |
| **07:45 – 08:15** | Noah | Write Slide 18 content: Title, Challenge Description, BASIN Solution, Data Evidence, and Impact. |
| **08:15 – 08:40** | Misha | Format Slide 18 into PowerPoint/Google Slides. Verify slide layout, fonts, and contrast. |
| **08:40 – 08:50** | Noah & Misha | Export master PDF / PPTX deck. Review final page count (exactly 25 slides). |
| **08:50 – 09:00** | All | Upload file to Zoho WorkDrive folder. Send confirmation email to Garrett, Ariel, and Sandy. Celebrate and head to presentations! |
