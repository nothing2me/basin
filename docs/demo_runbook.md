# September 22 Demo Runbook

Updated: September 8, 2026 | Product baseline: BASIN 0.2.0 (`BASIN.exe`)

## Three-Minute Product Demonstration Sequence

1. **Sidebar / Launch (`BASIN.exe`)**:
   - Show native desktop execution (EdgeChromium WebView2, no terminal flashing).
   - Use default settings: three provisional stations (`USW00012924`, `USW00012912`, `USW00012921`); 90, 180, 270 days; Jan/Apr/Jul/Oct; 35–85% retention; 300 candidates; 6 shortlisted; seed 22.
   - Explain the missing layer: small utilities cannot afford $50k and 6 months for HEC-ResSim/WAM to screen early drought stresses. Generate.

2. **Workspace / Clustering & Ranking**:
   - Point out synchronized whole-window resampling (maintaining physical cross-station correlation across the basin).
   - Show how KMeans groups diverse stress patterns across duration, deficit, and season.

3. **Grounded AI Assistant Interrogation**:
   - Click the vertical **AI Assistant** tab (`◀ AI Assistant`). Note the smooth hardware-accelerated drawer and zero-overlay split-pane resize.
   - Ask: `"Why did B-009 rank #1?"` Show the instant breakdown: Severity (40%), Duration (25%), Concurrence (25%), Season (10%).
   - Explain that the embedded intent engine maps supported questions to deterministic Python tools and fixed templates. No language model or inference server is used.
   - Ask: `"What was station concurrence in B-009?"` Show 96.7% stress in San Antonio (upper basin) and 81.5% in Corpus Christi (lower basin).

4. **Review / 1-Click Multi-Tier Stress Spectrum**:
   - Switch Series to **Reservoir simulation** $\rightarrow$ **Multi-Tier Stress Spectrum (100% · 80% · 60% · 40%)**.
   - Set Initial Storage to **35% (illustrative)**.
   - Reveal the **Countdown Matrix**: under all tiers, critical Stage 3 (20%) reserves are breached on **Day 151**.
   - Move Emergency Conservation slider to **15%**: Stage 3 breach extends to **Day 160** (**+9 days gained**).
   - Highlight the physical cause: summer reservoir surface evaporation in South Texas is **750 ac-ft/day**, which exceeds the 15% conservation savings (55.5 ac-ft/day) by **13.5 to 1**.

5. **Review & Verified Export**:
   - Accept the scenario and log a hydrologist note (*"Verified: acute summer concurrent deficit"*).
   - Open **Exports** and click **Build verified export**.
   - Spotlight the main-stage **Executive Technical Brief (PDF)**: click **Download Executive Brief (PDF)** to show the council-ready two-tier report (plain-language takeaways, policy trigger matrix, and quantitative stress spectrum).
   - Show companion deliverables: full replay ZIP bundle, verified Markdown brief, and 1-click **Open Output Folder** on disk with green SHA-256 verification.

6. **Close on Impact & Usefulness**:
   - Cite the A/B benchmark: unassisted from-scratch coding took 4–6 hours; BASIN took <10 minutes (30×–50× turnaround acceleration) while converging on the exact same physical numbers.

---

## Before Travel Checklist

- **Presentation Laptop:** 64-bit Windows with BASIN and its documented runtime prerequisites. The embedded assistant needs no model installation or server.
- **Offline Smoke Test:** Run `.venv\Scripts\python.exe -m pytest tests/` (verify all 128 tests pass offline with network disabled).
- **Projector Rehearsal:** Connect external display at 1920×1080 and 1600×900 to ensure high-DPI scaling and split-pane layout render sharply.
- **Backup Assets:** Keep USB stick containing:
  1. `BASIN.exe` standalone build.
  2. Offline `.venv` wheelhouse.
  3. Pre-exported `BASIN-Export-dbca22eba5eb.zip`.
  4. Video recording of the 3-minute sequence.

---

## Recovery Procedures

- If a question is not recognized: use a Quick Query or the Direct Tool Runner. Include scenario IDs and ask a complete question; the embedded engine handles a defined set of intents.
- If port 8501 is occupied: The native launcher automatically cycles through ports 8501–8550 to find the first open port.
- On browser/webview refresh: Saved sessions persist in `output/workspaces/` and can be reloaded in one click.

---

## Quick Judge Reference

- **AI Method:** Unsupervised KMeans clustering + embedded deterministic intent routing to read-only tools and fixed templates.
- **Grounded Responses:** The embedded engine routes supported queries to Python functions and fixed templates. Numbers come from workspace calculations; routing accuracy still needs evaluation.
- **Why Not Existing Tools:** HEC-ResSim and TCEQ WAM are heavy, static engineering models requiring months and tens of thousands of dollars. BASIN provides the missing agile screening and cryptographically verified handoff layer.
- **Evidence of Usefulness:** Controlled A/B benchmark demonstrated a 30×–50× speedup (10 min vs. 5 hours) with zero formula errors.
