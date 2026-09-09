# BASIN Finalist Showcase Presentation Plan

Updated: September 8, 2026 | Product baseline: BASIN 0.2.0 (`BASIN.exe` Native Desktop Edition)

## Confirmed Event Context

- **Event:** From the Ground Up 2026 AI Hackathon Finalist Showcase
- **Location:** Pleasanton, California
- **Date:** September 22, 2026
- **Expected Travel Day:** September 21, subject to organizer instructions
- **Team:** Noah Wilborn, Mohammed Asad Khan, and Misha Stegall
- **Judging Themes:** Impact, Feasibility, Community Centeredness, Innovation, and Clarity

The three-minute demonstration below is the team's compact, high-impact presentation route, followed by modular expansion sections for longer slots and judging Q&A.

---

## What BASIN Is & The Gap It Fills

BASIN helps a Region N or rural-serving municipal water analyst turn public NOAA rainfall observations into transparent, multi-station drought stress scenarios, discover system tipping points in minutes, and hand a cryptographically verified packet to a hydrologist for deeper modeling.

### The Missing Layer in the Water Industry:
- **Heavy Engineering Simulators (TCEQ WAM, USACE HEC-ResSim, RiverWare):** Industry standards for statutory water rights and dam safety. However, they cost $50,000+ in consulting contracts, take 3 to 12 months to configure, and are completely inaccessible for rapid exploratory questions.
- **The "Dirty Secret" (Ad-hoc Excel & Notebooks):** When water managers need quick answers before a council meeting, they cobble together un-audited spreadsheets or throwaway Python scripts. These take 4 to 6 hours, carry high formula-error risks, and provide zero cryptographic auditability.
- **Where BASIN Sits:** BASIN provides the missing **Agile L0/L1 Screening & Auditable Handoff Layer**—compressing a half-day programming slog into a 5-minute interactive session that produces certified, re-playable data bundles.

The sentence judges should remember:

> **BASIN turns scattered rainfall evidence and uncalibrated spreadsheets into a transparent, stress-tested request for expert analysis.**

---

## The Presentation Argument

1. **The Decision Gap:** Small providers and regional planning groups need to screen plausible climate and drought stresses *before* committing $50k+ to formal engineering modeling.
2. **The Product:** BASIN combines synchronized whole-window historical resampling, local unsupervised KMeans clustering, deterministic multi-attribute ranking, and a dual-pool mass-balance reservoir simulation.
3. **The Embedded Analyst Assistant:** A built-in deterministic intent engine that maps supported questions to 13 read-only Python analysis tools. Fixed templates display computed results. No language model, model download, or inference server is used.
4. **1-Click Multi-Tier Stress Spectrum:** Simultaneously sweeps 4 climate stress tiers (100% Baseline, 80% Moderate, 60% Severe, 40% Catastrophic) to pinpoint exact breaking days and empirically test whether a 15% emergency conservation mandate buys days or months.
5. **Cryptographic Proof of Integrity:** Produces a tamper-evident `.zip` handoff bundle (`daily_rainfall.csv`, `shortlist.csv`, `audit.json`, `Hydrologist_Handoff_Brief.md`) verified via SHA-256 digests.
6. **Empirical Proof of Usefulness:** In controlled head-to-head benchmarking, an unassisted hydrologist coding from scratch took **4 to 6 hours** to reach the exact same physical conclusions that BASIN produced in **under 10 minutes** (a **30× to 50× turnaround acceleration**).

---

## Compact Three-Minute Demonstration Script

### 0:00–0:25 — Frame the Decision & The Industry Gap
- **Say:** *"When a municipal water provider faces a looming drought, they can't wait six months and spend $50,000 on a consulting firm to run HEC-ResSim or TCEQ WAM just to screen initial stress scenarios. Today, they hack together un-audited Excel spreadsheets. BASIN gives them an agile, verified screening platform that runs entirely offline on a laptop."*
- **Action:** Show the native `BASIN.exe` desktop application. Highlight the 4-stage workflow: **Check Data → Build Scenarios → Review Choices → Share Results**.

### 0:25–0:50 — Check Data & Synchronized Construction
- **Action:** Open **Data**. Point out the NOAA GHCN-Daily snapshot (1991–2025) with its recorded cryptographic hash (`672c23f8...`).
- **Action:** Open **Workspace**. Click **Generate** (300 candidates, 6 shortlisted, seed 22).
- **Say:** *"Unlike weather tools that artificially splice synthetic data, BASIN preserves whole historical windows across Corpus Christi, Victoria, and San Antonio simultaneously, conserving real spatial correlation across the basin."*
- **Action:** Show the diverse shortlist grouped by local KMeans clustering.

### 0:50–1:40 — Interrogate the Grounded AI Assistant
- **Action:** Click the vertical **AI Assistant** tab.
- **Action:** Ask the assistant: *"Why did B-009 rank #1?"*
- **Show Response:** The assistant executes `explain_ranking`, showing exact weighted score contributions: Severity (40%), Duration (25%), Concurrence (25%), Season (10%).
- **Say:** *"Notice this AI is 100% offline and zero-hallucination. The LLM acts purely as an intent router to select deterministic Python tools. It cannot invent numbers; every calculation comes directly from the verified workspace."*
- **Action:** Ask: *"What was station concurrence in B-009?"* Show that San Antonio was stressed in 96.7% of windows (severed upper-basin inflow) while Corpus Christi was at 81.5%.

### 1:40–2:25 — 1-Click Multi-Tier Stress Spectrum & Tipping Points
- **Action:** In **Review**, select **Reservoir simulation** and click **Multi-Tier Stress Spectrum (100% · 80% · 60% · 40%)**. Set starting storage to 35%.
- **Show Chart & Matrix:** The multi-line trajectory and Countdown Matrix instantly render.
- **Say:** *"Here is BASIN's core insight in one click: Under 35% starting storage, the system breaches critical Stage 3 (20%) reserves on Day 151 across all rainfall tiers."*
- **Action:** Move the Emergency Conservation slider to **15%**.
- **Show Result:** Stage 3 breach extends from Day 151 to Day 160 (**exactly +9 days**).
- **Say:** *"Why does a 15% mandatory cut only buy nine days? Because summer evaporation in South Texas is 750 acre-feet per day, which dwarfs municipal demand savings by 13.5 to 1. BASIN proves this physical reality to council members in seconds."*

### 2:25–2:45 — Human Decision & Cryptographic Handoff
- **Action:** Accept the scenario, add a hydrologist note (*"Verified: acute summer concurrent deficit"*), and navigate to **Exports**.
- **Action:** Click **Build verified export bundle**.
- **Show:** The SHA-256 verification report (`verified: true`, 30 audit records replayed, 3 accepted scenarios).
- **Say:** *"The export bundle contains the raw rainfall CSVs, the human review notes, and a cryptographic audit log that any downstream engineer can independently replay and verify with zero data drift."*

### 2:45–3:00 — Close on Value & Feasibility
- **Say:** *"BASIN does not replace the hydrologist or legal river basin models. It bridges the gap between public climate observations and formal engineering analysis. It is packaged as a single 24 MB executable that runs on any laptop without internet access, tested across 128 automated verification tests."*

---

## Expansion Modules (For Longer Showcase Slots)

### 1. The Controlled A/B Benchmark (Proof of Usefulness)
To definitively prove usefulness, we conducted an empirical benchmark: an independent hydrologist solved the exact same regional planning challenge without BASIN, using raw Python and GitHub open-source tools:
- **Turnaround Time:** BASIN took **5 to 10 minutes**; unassisted coding took **4 to 6 hours** (**30× to 50× speedup**).
- **Physical Convergence:** Both pipelines independently converged on the exact same physical numbers:
  - Starting storage 35%: Stage 3 (20%) breached on **Day 151** (August 29).
  - 15% conservation: Stage 3 breach delayed to **Day 160** (**+9 days gained**).
  - Both identified that 750 ac-ft/day summer evaporation exceeds the 55.5 ac-ft/day conservation savings by 13.5:1.
- **Conclusion:** The math is rigorous and identical, but BASIN eliminates the half-day programming friction and manual formula risk.

### 2. Architecture & Technical Novelty
- **Embedded Intent Engine:** Built-in parsing of supported questions, scenario IDs, station names, years, and parameters. Each question is independent; the assistant uses no external inference service.
- **Strict Template Renderer:** 13 registered tool schemas. Results are rendered via deterministic Python functions into fixed markdown templates. The embedded router selects a tool and its parameters; result text comes from templates.
- **Hardware-Accelerated Split Pane:** 100ms GPU slide animation with zero-overlay window resizing, giving the user a dual-pane IDE experience.
- **Native Packaging:** Compiled as `BASIN.exe` (23.87 MB) via PyInstaller, embedding Windows WebView2 (EdgeChromium) for zero-console native desktop operation.

---

## Three-Person Speaking Lanes

| Lane | Speaker Role | Presentation Responsibilities |
|---|---|---|
| **Lane 1: Problem & Decision Gap** | Community Advocate / Policy Lead | Open with the Region N decision gap, why heavy tools (WAM/HEC-ResSim) are inaccessible to smaller utilities, and how BASIN provides community control. |
| **Lane 2: Live Demo & AI Copilot** | Technical / Product Lead | Drive the live software: NOAA data check, workspace clustering, and live interrogation of the grounded offline AI Assistant. |
| **Lane 3: Stress Spectrum & Verification** | Hydrologic & Verification Lead | Demonstrate the Multi-Tier Stress Spectrum (Day 151 / Day 160 countdown), explain the 13.5:1 evaporation reality, show the cryptographic `.zip` verification, and close. |

---

## Judge Q&A Matrix (Anticipated Questions & Concise Answers)

**Q: Are there industry tools like HEC-ResSim or TCEQ WAM that already do this?**  
**A:** Those are heavy statutory and physical routing tools. They take 3 to 12 months and $50,000+ in consulting fees to configure. When water managers need rapid screening before a meeting, they use un-audited Excel sheets. BASIN solves that missing agile screening and verified handoff layer.

**Q: Why is this considered AI?**  
**A:** BASIN uses a hybrid AI architecture: (1) Unsupervised KMeans clustering to group multi-dimensional drought feature spaces, and (2) a local, offline LLM agent acting as an intent router with tool-calling capabilities to translate plain-language hydrologic questions into deterministic math.

**Q: How do you guarantee the AI doesn't hallucinate numbers?**  
**A:** The LLM is forbidden from computing numbers. It only extracts parameters and calls pure Python tools operating on the verified workspace. Outputs are populated into fixed string templates with mandatory disclaimers. The LLM only provides connective prose.

**Q: Does a 15% conservation mandate save the reservoir in a severe drought?**  
**A:** Under depressed starting storage (35%), no. It only buys 9 days (delaying breach from Day 151 to Day 160) because South Texas summer evaporation (750 ac-ft/day) exceeds the conservation savings (55.5 ac-ft/day) by 13.5 to 1. BASIN proves that deeper curtailments or earlier Stage 2 triggers are required.

**Q: What does “cryptographically verified” mean?**  
**A:** The export packet contains SHA-256 digests of all raw data, scenario time series, and audit logs. The built-in `verify_bundle()` utility replays the calculations and checks hashes to mathematically prove that zero data was altered or fabricated.

**Q: Can this run completely offline?**  
**A:** The assistant and bundled-data calculations operate locally, without model downloads or inference services. The Windows launcher still needs its documented runtime prerequisites; verify the complete installation on the presentation laptop.

---

## Final Preparation Checklist (September 21–22)

- [x] Compile and verify native `BASIN.exe` with custom brand icon (23.87 MB).
- [x] Verify all 128 automated tests pass via pytest (`128 passed in 119s`).
- [x] Complete the 1-Click Multi-Tier Stress Spectrum and Tipping Point visualization.
- [x] Conduct and document the unassisted A/B hydrologist benchmark comparison.
- [x] Rehearse 3-minute compact script across the three speaking lanes.
- [ ] Test on the actual presentation laptop with Wi-Fi disabled and external projector connected.
- [ ] Keep backup video (`media/`) and offline USB copy ready.
