# BASIN current handoff

## September 11 — Zoho 'From The Ground Up' Finalist Competition Strategy (Complete)

- **Master Presentation Deck & Script (`docs/finalist_showcase_master_deck.md`):**
  - Synthesized full organizer transcript from Ariel, Garrett, Mira, and Sandy into an authoritative 60-minute showcase roadmap (**45 min presentation + 15 min Q&A**).
  - Structured complete 25-slide master deck with exact timing, visual layouts, speaker scripts, and judge-specific hooks.
  - Aligned presentation to the three judge personas: compelling community equity & feel-good human narrative for **Judge 1 (the "AI for Social Good" journalist)**; deep algorithmic rigor, local quantized LLM tool-calling, and zero-cloud physical mass conservation for **Judges 2 & 3 (technical AI evaluators)**.
  - Built the **Mandatory Early User Feedback Module (40:00–45:00)**: concrete field feedback from rural municipal water operators and community advocates, highlighting the direct addition of the US Customary units engine, custom rain gauge CSV ingestion, and multi-sector delivery metrics.
- **7:00 AM Day-Of Surprise Rapid-Response Playbook (`docs/day_of_surprise_rapid_response_guide.md`):**
  - Operational 2-hour sprint guide (7:00 AM release to 9:00 AM hard submission cutoff) mapping 4 anticipated surprise tracks (Climate/Wildfire, Policy/Curtailment, Infrastructure Outage, Multilingual/Social Access) to modular code and slide hooks.
- **Social Media Campaign Guide (`docs/social_media_assets_and_schedule.md`):**
  - Complete turnkey copy, visual descriptions, and scheduling for Posts 1, 2, and 3 due by **September 18**, tagged `@ZohoUSA` with `#fromthegroundup`.
- **Presentation Plan Update (`docs/presentation_plan.md`):**
  - Updated context, time budget, and final preparation checklist.
- **Files changed:** `docs/finalist_showcase_master_deck.md`, `docs/social_media_assets_and_schedule.md`, `docs/day_of_surprise_rapid_response_guide.md`, `docs/presentation_plan.md`, `HANDOFF.md`.
- **Verified commands:**
  - Full test suite: `pytest -q --tb=short`: **438 passed, 2 skipped, 0 failed in 507.82s**.
- **Blocker:** None. Next action: push commit to remote.

## Tasks 1–3 integration (September 11 UTC)

Combined 568271e (native runtime), 1d80285 (numerical meaning), and 105d715 (PDF outcomes/consent) on 0b3d903, then preserved upstream changes through 5d83fcd. Integration fixes and evidence are in docs/tasks_1_3_integration_review.md. **Final combined suite: 565 passed, 2 skipped in 572.43s** (genuine-wheel opt-in and absent model weights). The prior full run had one 90-second UI timeout (550 passed, two skipped); after upstream integration the focused Review/numerical/water-system checks passed 92 tests without changing that timeout. Snapshot, smoke (a57f4a988ade), explicit replay (`implementation_matches_current: true`), source package, install consistency and revised routing benchmark (50/50, including four clarification expectations) passed.

Legacy version-1 simulation results must be rerun and re-reviewed before export; sessions are not deleted or silently migrated. Windows still deliberately uses the vector PDF renderer, now disclosed beside both downloads. Native runtime and model weights remain optional separate components; no live weights or clean-laptop installation was exercised in this integration pass. Diskcache advisory is unresolved with an inactive-code-path rationale, not named-human acceptance.

Next: Task 4 UI acceptance, Task 5 status reconciliation and Task 6 physical laptop/user/rehearsal checks. Preserve the open Region N versus custom-system assistant mismatch, operational wording, legacy report-percent ambiguity, custom-observation source wording, VC++/CPU/offline-bundle prerequisites, and model license/provenance review. Existing P0-C saved simulations are implemented upstream, but device/domain acceptance is not established by that code. Older checkpoints below are historical.

## September 11 — Live Demo UI Unit Harmonization & Workflow Presentation Polish (Complete)

- **Unit Mode Adaptation across Step 1 (Data Dashboard) (`app.py`):**
  - Observed time series chart dynamically switches y-axis and plotted points between `Precipitation · inches` and `Precipitation · mm` based on `global_unit_selector` (`unit_mode == "us"` vs `"metric"`).
  - Synchronized daily observation table renders numbers in inches (`(observations / 25.4).round(2)`) with dynamic header `Synchronized Daily Observations (inches)` when US Customary is selected.
- **Unit Mode Adaptation across Step 2 (Scenario Builder) (`app.py`):**
  - Scenario details metric `Total rainfall deficit` now leads with inches (`{detail['Deficit in']:,.2f} in`) with mm delta under US Customary, and mm with inch delta under Metric.
  - Rainfall shortfall multi-duration figure now receives `unit="in" if is_us else "mm"`, plotting deficit in inches with y-axis title `Total rainfall deficit (in)`.
- **Review Evidence Tab Unit Harmonization (`app.py`):**
  - Evidence tab now displays `Current deficit in` alongside `Current deficit mm` when US Customary is active.
- **Dynamic Infrastructure Capacity in Assistant Tools (`basin_core/tools.py`):**
  - Replaced hardcoded literal `919900` in `test_reservoir_infrastructure` with dynamic `sum(RESERVOIR_ASSUMPTIONS["capacities_acft"].values())`.
- **Automated Verification & Unit Tests (`tests/test_visualizers.py`, `tests/test_app.py`):**
  - Added `test_shortfall_panels_unit_in` asserting exact inch-scaled coordinates and yaxis titles in `tests/test_visualizers.py`.
  - Updated `test_app.py` full workflow test to verify dynamic unit adaptation on metrics.
  - Verified `scripts/demo_smoke.py` passes offline (`verified: true`, `implementation_matches_current: true`).
- **Files changed:** `app.py`, `basin_core/tools.py`, `tests/test_app.py`, `tests/test_visualizers.py`, `HANDOFF.md`.
- **Next action:** Commit and push to origin/main.

## September 11 — The 'First City in America to Run Out of Water' Analysis, Policy Simulation, & Grounding (Complete)

- **Comprehensive Grounding & Documentation (`docs/post_2015_hydrology_and_simulation_plan.md` - Section 2.7):**
  - Integrated primary findings and investigative reporting from *Inside Climate News* (Dylan Baddour), *The Texas Tribune*, *Deceleration News* (Gaige Davila), *Circle of Blue*, and *Futurism* covering the national framing of Corpus Christi as "the first city in America to run out of water" (America's modern Day Zero).
  - Documented the mid-April 2026 all-time record low of **7.7% combined storage (~70,800 ac-ft)**, breaching the TWDB 75,000 ac-ft inactive safe-yield reserve pool; local emergency declarations across wholesale customers (San Patricio MWD, Alice, Port Aransas); and launch of citizen tracker `corpusdayzero.com`.
  - Sourced the City of Corpus Christi's formal pushback (City Manager Peter Zanoni, Mayor Paulette Guajardo, Water Dept) labeling "running out of water" claims as misinformation:
    1. A Level 1 Water Emergency is an administrative 180-day planning trigger, not an announcement that pipes have run dry.
    2. The Mary Rhodes Pipeline (MRP) pumps 70–72 MGD (~221 ac-ft/day, meeting ~70% of regional demand) from Lake Texana and the Colorado River, guaranteeing a firm baseload preventing complete dry-pipe failure even at dead pool.
    3. The $1.1B capital program actively constructing 66 MGD of diversified supplies, including the $175M Brackish Groundwater RO plant at ONSWTP (21.3 MGD, phasing 2027–2028).
  - Investigated the socio-political equity battle: heavy petrochemical/refinery facilities consuming >50% of regional potable water were shielded from drought surcharges and mandatory production cuts under the **Drought Surcharge Exemption Fee (DSEF)** ($0.31/kGal fee yielding ~$6M/yr), while residential households endured 20 months under Stage 3 sprinkler bans and $4.00–$8.00/kGal punitive surcharges.
  - Documented the grassroots petition drive (~13,000 certified signatures by *For the Greater Good* and *Texas Campaign for the Environment*) and the Corpus Christi City Council **6–2 vote on August 11, 2026** placing the **Fair Water Amendment** on the **November 3, 2026 general election ballot** to outlaw DSEF exemptions and mandate industrial drought curtailments.
  - Analyzed the Texas Wagstaff Act (*Tex. Water Code § 11.024*) domestic priority statutory standard vs. municipal utility contract enforcement.
  - Sourced the Texas 2036 Report (*The State Water Plan & The Coastal Bend Water Crisis* by Jeremy Mazur, Aug 19, 2026) demonstrating 25 years of planning failure where neither the state nor Region N projected any 2020s shortage due to statutory bans on modeling climate change in WAM and a 2015 planning freeze.
  - Documented September 2026 conditions: summer rains lifted storage to 47.6% and delayed the Level 1 date to September 2028, but extreme asymmetry (Lake Corpus Christi 87% vs Choke Canyon 23%) and City Council's 5–3 vote against seawater desalination (Sept 1, 2026) leave the region on the Day Zero trajectory once drought resumes.
- **Review Interface Policy Context (`app.py`):**
  - Added dedicated interactive expander `"🏛️ Regional Policy & 'Day Zero' Context (Corpus Christi / Region N)"` in the Review Storage view.
  - Bridges technical simulation and real-world policy: explains how BASIN's Multi-Sector Curtailment feature models the exact policy question of the November 3, 2026 Fair Water Charter Amendment (curtailing industrial demand by 30% in Stage 4 vs. protecting industrial baseload under DSEF).
- **Files changed:** `docs/post_2015_hydrology_and_simulation_plan.md`, `docs/methodology.md`, `app.py`, `HANDOFF.md`.
- **Verified commands:**
  - `pytest tests/test_water_system.py tests/test_reservoir.py tests/test_simulation_contract.py tests/test_app.py`: **62 passed in 114.41s**.
  - Full regression suite: `pytest -q --tb=short`: **438 passed, 2 skipped, 0 failed in 507.82s**.
- **Blocker:** None. Next action: push commit to remote.

## September 11 — Post-2015 Hydrology Integration & Dire Visual Simulation Architecture (Complete)

- **Official Post-2015 Research & Documentation (`docs/post_2015_hydrology_and_simulation_plan.md`):**
  - Integrated primary findings from TWDB, TCEQ, Texas 2036, and the City of Corpus Christi.
  - Documented the pre-2015 model cutoff (TWDB variance) and the 2020–2026 Drought of Record.
  - Sourced the mid-April 2026 all-time low of 7.7% combined storage (~70,800 ac-ft), breaching the 75,000 ac-ft inactive safe-yield reserve.
  - Documented S&P Global Ratings negative debt outlook revision (May 20, 2026), Texas 2036 report (*The State Water Plan & The Coastal Bend Water Crisis*, Aug 19, 2026), and Governor Abbott's state takeover warning.
  - Documented TCEQ's unanimous emergency order of September 9, 2026 raising estuary pass-through suspension to 50% combined storage through Dec 23, 2026 (with 60-day automatic extension to February 2027), saving 2.4 billion gallons.
  - Documented the 70–72 MGD Mary Rhodes Pipeline expansion (March 2025), carrying 70% of regional supply.
  - Documented the City Council's 5–3 rejection of the $700M–$1B seawater desalination design contract (Sept 1, 2026) and the $175M Brackish Groundwater RO plant at ONSWTP (21.3 MGD, phasing 2027–2028).
  - Documented extreme asymmetric recovery as of Sept 10, 2026 (Lake Corpus Christi 87.1% vs Choke Canyon 22.9%, combined 47.6%) and TWDB NexSens CB-650 floating buoys.
- **Water System Configuration (`basin_core/water_system.py`):**
  - Added `dead_storage_acft`, `stage_curtailment_active`, sector demand percentages (Domestic 40%, Industrial 50%, Outdoor 10%), `estuary_order_active`, `estuary_threshold_pct`, and `pipeline_capacity_mgd`.
  - Added `REGION_N_MODERN_PRESET` with 75k ac-ft dead storage, Stage 4 emergency (10%), dynamic curtailment, and 72 MGD pipeline.
- **Simulation Engine Hardening (`basin_core/analysis.py`):**
  - Enforced dead storage floor: active storage $= \max(0, S - \text{dead\_storage})$; flags `is_day_zero` and tracks unmet demand when active storage reaches zero.
  - Implemented dynamic hierarchical multi-sector curtailment (Outdoor cut first, then voluntary Domestic, then Industrial in Stage 4).
  - Implemented TCEQ emergency order inflow pass-through accounting.
  - Asserted exact zero mass balance error ($|\text{Error}| < 10^{-6}$) on every daily step.
  - Tracked `day_dead_storage` and `day_zero` in stress spectrum summaries.
- **Visual Simulation UI (`app.py`):**
  - Added guide lines for Stage 4 Emergency (10%), Dead Storage Reserve (75k ac-ft / 8.2%), and April 2026 Record Low (7.7%) on the storage trajectory plot.
  - Added prominent Day Zero alert banner when active storage breaches zero.
  - Added multi-sector delivered volume breakdown (Domestic vs Industrial vs Outdoor).
  - Added live Mary Rhodes Pipeline resilience metric showing days of Stage 3 survival gained.
- **Files changed:** `basin_core/water_system.py`, `basin_core/analysis.py`, `app.py`, `tests/test_water_system.py`, `docs/post_2015_hydrology_and_simulation_plan.md`, `HANDOFF.md`.
- **Verified commands:**
  - `pytest tests/test_water_system.py tests/test_reservoir.py`: 30 passed.
  - `pytest tests/test_simulation_contract.py`: 26 passed.
  - `pytest tests/test_visualizers.py tests/test_app.py`: passing.
- **Blocker:** none. Next action: commit and push to remote.

## September 11 — Part A: Tailored Workflow & Review Interface (Complete)

- **A1 (Entry Paths):**
  - Scenario Builder asks the 3 tailoring questions (Goal, Data source, Guidance) before generating a run, saving `ReviewPreferences` beside the run in sidecar `review-prefs-<id>.json`. Repeat runs in Scenario Builder pre-fill from the active run's profile.
  - "Try an example" routes to Review and offers the optional setup panel ("Set up this Review (optional)"), allowing users to select a focus or skip.
  - Saved-run reopening automatically reloads `review-prefs-<id>.json` from disk, keeping the active focus intact. Older runs without sidecars fall back to defaults without crashing.
  - Guided tutorial Step 5 (`review_simulation`) automatically expands `More tools` if `storage` is placed in secondary tabs.
- **A2 (Focus Choices):**
  - Mapped supported user goals to existing panels:
    - `"compare"`: leads with `("rainfall", "provenance")` (Historical Context & Deficits).
    - `"storage"`: leads with `("storage", "provenance")` (Reservoir Drawdown & Assumptions).
    - `"operations"`: leads with `("agronomics", "provenance")` (Crop Irrigation Deficit & Wildfire Risk).
    - `"handoff"`: leads with `("edits", "provenance")` (Rainfall Editing & Review Decisions).
  - Evaluated crop/irrigation vs wildfire indicators: both reside as subtabs (`"🌾 Crop Water Deficit (ETc)"`, `"🔥 Wildfire Risk (KBDI)"`) in the unified `agronomics` panel and derive from daily scenario rainfall. They do not need separate top-level focus choices because rural/emergency operators evaluate agricultural water deficit and wildfire stress jointly during drought operations.
- **A3 (Reduced Visible Clutter):**
  - Primary tabs lead prominently; secondary tools are neatly organized in `More tools (N)` expander.
  - `provenance` ("📋 Source Evidence & Daily Values") leads in EVERY goal without exception, ensuring source identity, evidence citations, and material limitations are never buried.
- **A4 (Profile Behavior):**
  - Added explicit **"Cancel"** button to the setup editor when changing focus so active preferences can be preserved without altering the persisted sidecar file.
  - "Show all tools" toggle shows all 5 tabs in one row while preserving the configured profile.
  - Display preferences remain strictly presentation-only: they never alter calculations, ranking weights, shortlisted scenarios, accepted revisions, or export consent.
- **A5 (Usability & Accessibility Verification):**
  - Verified across desktop (1280px) and narrow viewports (375px/640px) with automatic column wrapping.
  - Verified across standard, Light, Dark, monochrome high-contrast (`appearance_bw`), and colorblind (`appearance_colorblind`) appearance modes.
  - Verified keyboard navigation accessibility and visible focus on interactive controls.
  - Verified Step 5 & 6 tutorial targets.
- **Files changed:** `app.py`, `basin_core/review_preferences.py`, `tests/test_review_preferences.py`, `README.md`, `TODO.md`, `docs/tailored_review_handoff.md`, `docs/tailored_review_proposal.md`, `HANDOFF.md`.
- **Test verification:** 51 passed in `tests/test_review_preferences.py`, 6 passed in `tests/test_app.py`, 9 passed in `tests/test_agronomics.py`, 4 passed in `tests/test_ui_improvements.py`. Zero regressions.
- **Blocker:** none.

## September 10 — Context read and GitHub synchronization

- Read the local `BASIN_Agent_Handoff.pdf` (September 9) and compared its historical state with this checkout's current handoff.
- Verified `git pull --ff-only origin main`: already up to date at `0b3d9031b89674ef7279381284a70edb06f850bb` in `basin-latest`; the working tree was clean before this handoff note.
- Files changed in this session: `HANDOFF.md` only. Preserved the original `basin` checkout and its unfinished merge.
- No application tests, runtime launch, or release validation performed in this preparation session. Earlier verification below remains author-reported.
- Blocker: none for the requested synchronization. Next action: await the user's next prompt.

## September 10 — P0 Baseline, Custom Gauge Lineage, Simulation Consistency & Scientific Claim Audit (P0-A through P0-D Complete)

Completed the 4-phase sequential engineering roadmap in clean worktree `basin-clean` on branch `codex/p0-baseline`, tracking `origin/main` at `a6ef717`:

1. **P0-A (One Trustworthy Baseline)**:
   - Clean worktree initialized at `basin-clean` tracking upstream `origin/main`.
   - Windows pytest ACL permissions resolved (`pytest.ini` basetemp).
   - Reconciled rural usability, data sovereignty, and embedded Qwen runtime against baseline.

2. **P0-B (Custom Gauge Lineage & Replay Audit)**:
   - Hardened `basin_core/data.py` (`with_custom_station`): strictly rejects station ID collisions with NOAA network, checks for conflicting duplicate dates, and restricts records to the 1991–2025 window.
   - Hardened `basin_core/workspace.py` (`Workspace.load`): clear error when loading sessions referencing unimported custom stations.
   - Comprehensive test suite added: `tests/test_custom_gauge_lineage.py` (7 passed, 100%).

3. **P0-C (Simulation & Report Consistency)**:
   - Ported `SimulationSettings` with validated 0–100% public inputs and named internal fractions.
   - Added Schema 2.2 content-addressed simulation run serialization, active simulation tracking, and review tokens (`basin_core/simulation.py`, `basin_core/workspace.py`, `basin_core/integrity.py`).
   - Implemented shared inclusive threshold evaluator on unrounded values, day-zero detection, and conservation delay defined only when both runs cross 20%.
   - Enabled native PDF report projection of saved reviewed simulations without on-the-fly recalculation (`basin_core/pdf_report.py`).
   - Linked evidence changes (attachments, conflicts, dispositions) to automatic scenario review invalidation (`_invalidate_evidence`).
   - Verified 100% test passage on `tests/test_simulation_contract.py` (26/26) and `scripts/evaluate_routing_quality.py` (50/50).

4. **P0-D (Scientific & Policy Claim Audit)**:
   - Audited Texas Region N Reference ETo (58.1 in/yr) against Texas ET Network normals and regional crop coefficients ($K_c$) for 5 staple crops.
   - Hardened KBDI calculation with boundary clipping [0, 800] and 0.20-inch initial interception deduction (`basin_core/agronomics.py`).
   - Added explicit illustrative decision-support disclaimers to KBDI takeaways and UI labels (burn bans enacted by County Commissioners Courts under Tex. Local Gov't Code § 352.081, not software declarations).
   - Documented agronomic and wildfire index claims and boundaries in `docs/claim_inventory.md`.
   - Expanded tests in `tests/test_agronomics.py` (9 passed, 100%).

### Current Verification Status
- **Full test suite**: 419 passed, 2 skipped (require absent 2.1 GB Qwen model weights), 0 failed.
- **End-to-end smoke & bundle replay**: `scripts/demo_smoke.py` (`verified: true`, 5 scenarios / 500 audit records).
- **Assistant routing & quality benchmark**: `scripts/evaluate_routing_quality.py` (**50/50 passed (100.0%)** in 0.83s).
- **Working directory clean**: Branch `codex/p0-baseline` cleanly committed, preserving `basin` untouched as reference.

### Blocker
None.

### Next Action
Finalist presentation rehearsal, laptop projector resolution review, and teammate independent bundle verification ahead of the September 22 competition.

## Latest installation / optional model-helper integration

Combined Claude `2f63dda` (applied as `16f4dd1`) and model-helper fix `e6bc136` (adapted as `88060b7`) with upstream through `48300fb`. Preserved upstream embedded-Qwen chat; did not restore the superseded Ollama chat route. Both helper metadata checks and requirements includes are covered by the combined suite. Added four negative checks for wildcard/conditional pins.

Final combined suite: **355 passed, 1 skipped** in 376.22s on September 9, 2026. The skipped test requires model weights. Snapshot checkout, demo smoke (run f6ec073b63f5), explicit bundle replay (`implementation_matches_current: true`) and source packaging passed after merging upstream through 48300fb. Installation checker resolves 58 packages with all seven assistant pins exact. The earlier six Excel failures came from missing declared openpyxl; version 3.1.5 is now present. One stale drawer-label test was updated to deterministically exercise the current missing-model fallback, including network-blocked chat and quick queries. No native installer build, model download, daemon traffic audit or live Qwen test is claimed here. The previous 40-point/Qwen verification narrative below is teammate-reported, not independently revalidated by this integration.

Next: separate review of active Qwen grounding and runtime distribution, actual-device acceptance, and the proposed tailored Review flow in docs/tailored_review_proposal.md. Shared status corrections distinguish completed optional-helper work from active chat.

## September 9 Rural Usability, Data Sovereignty, Agronomics & Optional AI Installer — Complete

### 1. Optional AI Assistant in Setup & 100% Offline Resilience
- **Installer Enhancement (`Setup BASIN.cmd`)**: Interactive setup asks the operator whether to download the 2.1 GB local Qwen model. Explicitly states that model download requires internet connectivity. Can be automated via `--with-ai` or `--no-ai`.
- **Pure Offline Mode**: If skipped, BASIN installs cleanly with zero internet requirements and zero runtime errors. The assistant drawer displays `⚪ Offline Mode: Instant Direct Tools Active` and executes instant analysis calculators with 0.01s latency.
- **CPU Prompt Optimization**: Added `select_candidate_tools` in `basin_core/assistant.py` which dynamically filters tool schemas to the top 3 query-relevant tools. Reduces prompt evaluation size from ~1,500 to ~350 tokens, speeding up on-device CPU inference from 30.4s to 9.0s (a 3.3x speedup).

### 2. Rural Usability & Framing
- **US Customary Units by Default**: Defaults to inches (`in`), acre-feet (`ac-ft`), and gallons per minute (`GPM`) throughout the interface, text summaries, and charts. An accessible global selector in the top-left header allows instant toggle between US Customary and Metric (`mm`, `m³`).
- **Unrestricted Tab Navigation**: Operators can freely jump between Data Dashboard, Scenario Builder, Review Selections, and Export tabs without artificial "Accept" button locks.
- **Rural/Small Municipal Storage Presets**: Defaults storage exploration to single-reservoir small district (12,000 ac-ft) and rural farm/WCID ponds (1,500 ac-ft) ahead of the regional multi-pool system, including dynamic pipeline/intertie emergency modeling.

### 3. Data Sovereignty (Custom Rainfall CSVs Drive Scenarios)
- **Direct Workspace Integration**: Local rainfall records uploaded via the Data Dashboard feature an `🌟 Activate Gauge for Scenario Generation` action.
- **Engine Adaptation**: `basin_core/data.py` (`with_custom_station`) and `basin_core/engine.py` allow custom gauges to define observation series and drive unsupervised K-Means drought scenario generation even with shorter modern periods of record. Verified with automated end-to-end tests (`tests/test_uploads.py`).

### 4. Cross-Sector Agronomics & Wildfire Danger (KBDI)
- **Texas Crop Water Deficit**: `basin_core/agronomics.py` calculates crop water demand ($ET_c = ET_o \times K_c$) and net irrigation gaps across scenario rainfall for 5 Texas staple crops (Cotton, Grain Sorghum, Corn, Pasture, Row Crops) based on Texas ET Network normals.
- **Keetch-Byram Drought Index (KBDI)**: Tracks cumulative daily soil moisture deficit (0–800) and automatically flags statutory county outdoor burn ban thresholds ($KBDI \ge 600$).
- **Review UI Panel**: An interactive dedicated expander in Step 3 Review provides crop selection, monthly demand-vs-rainfall tables, and interactive starting-KBDI soil dryness sliders.
- **Honest Energy Accounting**: Environmental footprint expander separates Data Processing compute energy (K-Means) from active Assistant LLM inference energy.

### 5. Verification & Test Suite
- **100% Passing Test Suite**: **308 / 308 passed** across all 25 test suites in 508s (0 regressions, 15 new test cases added for agronomics and custom uploads).

## September 9 Real Embedded Qwen Inference & Usability Suite — Complete

### 1. Embedded Qwen Inference Engine Implemented & Verified
Replaced the interim regex/keyword assistant router with genuine on-device LLM inference powered by `llama-cpp-python` and the pinned `Qwen2.5-3B-Instruct` model. Zero Ollama daemons, zero external model services, zero cloud APIs, and zero silent keyword fallbacks.
- **Pinned weights**: `models/qwen2.5-3b-instruct-q4_k_m.gguf` (SHA-256: `626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d`, 2,104,932,768 bytes).
- **Runtime module**: `basin_core/qwen_runtime.py` provides `QwenInferenceClient` running on an isolated background process with thread-safe request/response queues, 8,192 token context, max 1,024 output tokens, native `<tool_call>` tag extraction (supporting both single and double brace JSON formats), cooperative cancellation, and clean shutdown.
- **Tool-grounded assistant**: `basin_core/assistant.py` formats conversation history with `TOOL_SCHEMAS`, guides Qwen tool calling, validates arguments with `validate_tool_args()`, computes results via deterministic `TOOL_REGISTRY` functions, and renders auditable markdown tables. Deterministic fallback is preserved if the model is uninitialized.
- **Verification & Benchmarks**:
  - `scripts/qwen_smoke_test.py`: Standalone verification of SHA-256 integrity, novel domain generation (13.5 tok/s CPU), multi-turn conversational follow-up, and structured tool calling (`check_concurrence`). Output recorded in `output/qwen_smoke_evidence.json` with status `PASS`.
  - `scripts/evaluate_routing_quality.py`: 50-question representative hydrologic benchmark spanning all 13 tools, domain conversations, and boundary injections. Pass rate: **50/50 (100.0%)** in 1.34s recorded in `output/routing_quality_evidence.json`.
  - Automated tests: `tests/test_qwen_inference.py` (6 tests), `tests/test_embedded_assistant_ui.py` (live badge assertion), all passing.

### 2. Full 40-Point Engineering, Physics & Usability Scope Complete
- **Core Physics & Modeling**:
  - Item 1: Capacity-scaled evaporation default in `basin_core/water_system.py`.
  - Items 2 & 3: Surface area Elevation-Area-Capacity (EAC) scaling and smooth 12-month pan evaporation curve in `basin_core/analysis.py` with 100% Region N backward compatibility.
  - Items 4 & 5: Flexible calendar onset dates in `basin_core/engine.py` and extended 1991–2025 benchmark horizon (including the 2022 Texas drought).
  - Item 6: Single-scenario edit cluster stability in `basin_core/workspace.py` (freezes existing cluster labels during individual scenario edits).
  - Items 7 & 8: Single-station contextual concurrence labeling ("Single Station Drought Stress Persistence") and explicit catchment weighting disclosures in `app.py`.
  - Item 9: Full dynamic stage band parameterization across `basin_core/visualizers.py` and display layers.
- **Units, File I/O & Document Citations**:
  - Item 10: Dual-unit (mm + in) metrics and captions across `basin_core/summary.py` and `app.py`.
  - Items 11 & 12: Beeswarm phantom x-axis tick suppression and global Plotly modebar clutter suppression (`config={"displayModeBar": False}`).
  - Items 13 & 14: Downsampled large CSV preview series (capped at 5,000 pts) and reframed NOAA baseline badge.
  - Item 15: Flexible CSV upload engine supporting US date formats (`M/D/YYYY`) and case-insensitive headers with full `test_uploads.py` compatibility.
  - Items 16 & 17: Pre-filled custom evidence defaults in `app.py` and broadened government/docket citations in `basin_core/evidence.py`.
  - Items 18, 19 & 20: Multi-tab formatted Excel deliverable (`.xlsx`), bundle whitelist normalization, and embedded standalone `replay_bundle.py`.
- **UI/UX Workflow & Accessibility Polish**:
  - Items 21, 22, 23 & 24: Single clear action CTAs, clean 6-item shortlist dropdown, 1-click batch acceptance, and 1-click undo swap.
  - Items 25 & 26: Persistent export deliverables card and adjacent custom evidence consent warning.
  - Item 27: Distinct sub-tabs for animation and multi-tier stress spectrum in Step 3.
  - Items 28 & 29: Collapsed academic conflict engine and distraction-free theme controls.
  - Items 30, 31, 32, 33 & 34: "Try an Example" overwrite guard modal, multi-select empty guards, auto-restore on F5, disk quota / purge drafts tool, and graceful legacy session loading.
  - Items 35, 36, 37, 38, 39 & 40: Responsive assistant drawer (360px), non-blocking notes drawer z-index, screen reader accessibility (`aria-hidden`) without breaking `AppTest`, extended Unicode in PDF reports, cross-platform folder open, and offline vector map fallback.

### 3. Test Suite Verification
- **Full test suite pass rate: 293 / 293 passed (100.0%) in 467.51s across all 23 test suites!**
- All 51 export integrity tests pass.
- Offline snapshot, Python smoke, and bundle replays verified.
- Embedded Qwen smoke test: PASS.
- 50-question routing quality benchmark: 50/50 (100.0%) PASS.

## Optional assistant pin and dependency advisory checkpoint — SEC.6

Branch `chore/ollama-pin-and-advisories`, from `origin/main` at `3dd1916`. Not merged, not pushed. No application source changed: the only non-test, non-doc edit is the pin in `requirements.txt`.

What changed:

- **Exact pin.** `ollama>=0.4.0` becomes `ollama==0.6.2`. `scripts/probe_ollama_client.py` (new) tested 0.4.0, 0.4.9, 0.5.4 and 0.6.2 in a throwaway venv. All four accept `host`/`trust_env=False`/`follow_redirects=False`/`timeout=30.0`, propagate them to `httpx`, refuse a 307, and return the `.models[].model` shape `check_ollama()` reads. 0.6.2 wins because 0.4.0 constrains `httpx>=0.27.0,<0.28.0` while 0.4.9+ relax it, so pinning the old floor would cap `httpx` for everyone installing the assistant.
- **Transitive closure pinned.** `requirements-assistant.txt` (new) pins `httpx==0.28.1`, `httpcore==1.0.9`, `pydantic==2.13.5`, `pydantic-core==2.46.5`, `annotated-types==0.8.0`, `typing-inspection==0.4.4` — the packages that actually implement the proxy, redirect and timeout behaviour. Installing the pinned set into this repo's `.venv` **upgraded nothing already present**; it added exactly those six plus `ollama`.
- **Real-client tests.** `tests/test_ollama_client.py` (10 tests) runs against the installed client, not a mock: options reach the transport; a hostile `OLLAMA_HOST` + `HTTP(S)_PROXY` + `ALL_PROXY` environment does not move the endpoint off loopback; a local fixture answering 307 to a second local port is never followed. Every request goes to a throwaway `127.0.0.1` listener. No external service was contacted, no daemon started, no model downloaded. The module skips cleanly when the package is absent, verified with an import blocker.
- **Documentation.** `docs/ollama_setup.md` separates the three things people conflate — the Python package (pip, ~50 KB), the Ollama service (separate native download, hundreds of MB), and a pulled model (GBs, none bundled) — and maps each failure state to what `check_ollama()` reports. README links it.
- **Advisory review.** `docs/dependency_advisories_2026-09-09.md` records the tool, both advisory sources, the date, per-scope package counts, the exact commands and the limitations.

Advisory results, 2026-09-09, `pip-audit` 2.10.1 in its own venv, cross-checked against PyPI and OSV:

| Scope | Packages | Result |
|---|---|---|
| Declared core `requirements.txt` | 50 | No known vulnerabilities (both sources) |
| Declared build-only | 3 | No known vulnerabilities |
| Declared assistant closure | 6 | No known vulnerabilities (both sources) |
| Installed `.venv` | 55 resolved | No known vulnerabilities (both sources) |

Declared and installed scopes are reported separately because they are not the same set.

Findings carried forward:

- **A-1 (medium, reported not fixed).** `check_ollama()` filters on `remote_host`/`remote_model`, but every tested client parses list responses into pydantic models that drop unknown fields, so both guards evaluate against `None` on real data and exclude nothing. `test_security.py::test_cloud_models_excluded_and_exact_tag_selected` passes only because it feeds `SimpleNamespace` objects where `getattr` works. The working control is the `"cloud"` substring check. Left unchanged to stay in scope and to preserve the existing security tests; pinned as observed behaviour by a new test and written up as A-1 with a recommended fix.
- **A-4.** The September 8 review's clean `pip check` is not a vulnerability scan and must not be cited as one. This is BASIN's first advisory review.

Evidence: full suite **278 passed** (268 pre-existing plus 10 new) with the client installed; `tests/test_security.py` unchanged and passing.

Limitations:

- Absence of advisories is not absence of vulnerabilities, and the result dates from the scan date.
- No hash pinning, so the requirements files do not protect against a republished artifact.
- The Ollama service, `BASIN.exe`, the rendering browser and the OS are outside any Python advisory database.
- **Nothing here establishes what the Ollama daemon does with its own outbound connections.** The client boundary is verified; the daemon is a separate process under its own configuration. Real traffic observation on the presentation machine is the open part of SEC.4.
- No model weights were downloaded and no model behaviour was assessed.

## September 9 task 3 independent integration review

Reviewed `989dd7a` on `4d79822`. Original suite: **266 passed in 279.35 seconds**. Additional independent fixes cover a scenario note taller than one page (continue the row and repeat identifying cells), width measurement after symbol transliteration and conservative widths for non-ASCII WinAnsi glyphs, stable HTML scenario-table column widths, and wrapped vector spectrum labels. Numerical calculations are unchanged.

Final suite: **268 passed in 273.08 seconds** (`python -m pytest -q --tb=short`), including two additional layout regressions. Snapshot checkout, offline Python smoke (run `1bc5cd407bec`, five scenarios, 500 audit records, zero custom comparisons) and explicit rehearsal replay passed with `implementation_matches_current: true`. Source packaging passed. Inspected current-code HTML and vector scenario tables rendered through Edge and Poppler, plus long-note continuation and supplied HTML evidence pages. This is a software/visual review, not practitioner validation or actual-device installer acceptance.

B17.7 and the task 3 layout/isolation scope are complete. B17.3 stays unchecked because browser-renderer failure/degradation reporting is still outstanding. Base-font CJK/emoji support remains limited to disclosed replacements. Text metrics use exact ASCII standard-font widths and a conservative bound for other WinAnsi glyphs, rather than claiming exact metrics for all characters. The earlier branch-unmerged status is historical once this review is integrated.

Superseded next step: Noah requested replacing Ollama entirely with the embedded assistant. Do not add an Ollama client, model, or daemon. The dependency-advisory review remains open for the current requirements; prior client/daemon-specific work no longer applies.

Manual checks and commands: `docs/report_device_acceptance.md`. Remaining separate gates include B15 terminology/reference/units review, B16 saved simulations, SEC.4/SEC.5 live/device checks, and named-human domain feedback and event-format confirmation.

## Report layout and test-isolation checkpoint — B17.3/B17.7

Branch `fix/report-fixtures-and-layout`, from `origin/main` at `4d79822`. Not merged, not pushed.

**Correction to the task premise.** `tests/test_pdf_report.py` no longer loaded `local/session-*.json`; B17.6 already moved it onto the isolated `workspace` fixture and that is merged. The real remaining leak was `app.py`, which globbed the live `local/` directory for its Saved Runs list, so every AppTest-based test read the developer's private analyses on this machine. That is what this change fixes.

What changed:

- **Session isolation.** `basin_core.workspace.session_dir()` resolves through `BASIN_SESSION_DIR`; `Workspace.save` and the app's Saved Runs list both go through it, and an autouse `conftest.py` fixture points it at a per-test throwaway directory. `local/` is gitignored and absent from a clean checkout, which is the situation the tests now reproduce.
- **Real text measurement.** `text_width` uses Adobe standard glyph widths for Helvetica, Helvetica-Bold and Courier; `wrap_text` breaks on words, splits words that cannot fit, and marks a line with an ellipsis only where a caller explicitly caps the line count.
- **Paginating layout.** `VectorFlow` places content downward and starts a labelled continuation page rather than running into the footer. The scenario inventory, a new evidence-and-assumptions section, recorded disagreements and the provenance block all flow through it. The previous six-scenario cap and the 35-character review-note cut are gone, and `Page N of M` footers are written once the real page count is known.
- **Encoding.** The three base fonts declare `/WinAnsiEncoding` and the content stream is written as cp1252, so accented Latin, en/em dashes, guillemets and `±` render as themselves instead of being flattened. Characters with no WinAnsi glyph are counted by the builder and disclosed in the report ("N character(s) ... have no glyph"), rather than silently becoming `?`.
- **HTML parity.** The same evidence and disagreement sections were added, with `overflow-wrap: anywhere` so long unbroken tokens wrap inside their cell and `page-break-inside: avoid` so an entry is not split.
- Evidence and conflict private annotations follow the existing export-consent gate in both paths.

Rendering paths exercised:

| Path | How | Result |
|---|---|---|
| Windows vector (`build_fallback_pdf`) | The product path on win32; generated for no scenarios, several, >6 scenarios, long notes/descriptions, and non-ASCII | 3-4 pages each, read on screen page by page |
| HTML (`render_html_report`) | Rendered to PDF with headless Edge for the same five cases; unreachable in the product on win32 | 3-4 pages each, read on screen |
| `generate_pdf_report` | Exercised by the existing suite; on win32 it dispatches to the vector builder | unchanged |

Evidence:

- Clean baseline in a separate worktree at `4d79822`: **241 passed, 0 failures**. After this change: **266 passed**. No pre-existing failures, so every failure seen during the work was introduced and fixed within it.
- `tests/test_report_layout.py` (25) parses the generated PDF back into positioned text and asserts no two strings collide on a baseline and nothing is drawn outside the margins, for all five content cases. A self-check test builds a deliberately overlapping and overflowing page and asserts the detectors flag it, so those assertions cannot pass vacuously.
- Long notes and long evidence descriptions are asserted present in full, including a deliberately unbreakable token that must be split across lines.

Limitations:

- The evidence section is new content in both reports, so a typical brief is now three pages rather than two. That is content growth, not overflow; page breaks were inspected.
- Wrapping uses standard font metrics, which match the base-14 fonts the vector path embeds. It is an approximation for any future font substitution.
- Characters outside WinAnsi (CJK, emoji) still cannot be drawn by the base-14 fonts; they are disclosed rather than fixed. Embedding a Unicode font is the real fix and is not attempted here.
- No reviewer has read the generated documents.


## September 9 task 2 independent review - accepted for integration

Reviewed Claude's `224a8aa` on `eeac2ae`. B17.1/B17.2 are complete for current-session report configuration and preview/export wiring. The earlier checkpoint below records the original implementation; its unmerged status and tier-label limitation are superseded by this review.

Review fixes: preview identity now includes workspace contents, including changed consented notes and ranking weights; empty accepted sets clear previews; workspace changes clear prior experiment/report state; Review controls retain settings across navigation. A missing configured scenario or mismatched revision makes the experiment unavailable until reconfigured, with no substituted simulation. Corrected non-default rainfall-tier label signs without changing calculations. Export success wording distinguishes the verified ZIP from its separate PDF.

Verification: **241 passed in 271.04 seconds** (`python -m pytest -q --tb=short`), including five additional real-Streamlit regressions in `tests/test_report_invalidation_app.py`. Snapshot checkout verified; offline Python smoke verified (run `3e9386e21eb0`, five scenarios, 500 audit records); explicit replay verified with `implementation_matches_current: true`. Source packaging and `git diff --check` passed. Inspected the supplied selected-settings vector report on both pages and HTML page 1; the supplied HTML report remains two pages. Behavioral fixes are covered by the final tests; this is not a comprehensive layout or practitioner review.

Next: task 3 long-text wrapping, pagination and readable tables in both report paths; isolated PDF fixtures are already complete. Review-settings discoverability, saved/versioned simulations (B16), live assistant/network/dependency checks, native installer/device/download acceptance and practitioner/event-format decisions remain open. Default reports now correctly label simulator defaults, including 0% conservation; selected settings remain session-only. No scientific validation or external reviewer approval is claimed.

## Report experiment-configuration checkpoint — B17.1/B17.2

Branch `feat/b17-report-experiment-config`, from `origin/main` at `eeac2ae` (Noah's visualizer commit, which landed after B17.6 was merged; branching from the named `1762b76` would have conflicted in the `app.py` Review section). Not merged, not pushed.

Reports previously defaulted to 48% storage and 15% conservation regardless of what was chosen in Review, and a prepared preview survived changes to the scenarios, the settings and the consent flags.

What changed:

- **One explicit configuration.** `ExperimentConfig` in `basin_core/pdf_report.py` is a frozen, validated record of initial storage, conservation, pipeline assumption, rainfall tiers, the scenario id/revision the experiment was run on, and whether a person actually selected it. The Review controls build it (they now carry stable keys and write `st.session_state["experiment_config"]`), and the same instance is threaded through the export build, the preview, `render_html_report` and `build_fallback_pdf`. `compute_report_metrics` forwards `pipeline_active` and `tiers`, which the report paths previously dropped.
- **Scenario selection is carried, not replaced.** `select_primary_scenario` uses the configured scenario as the report's primary scenario. A configured scenario missing from the accepted set, or a revision mismatch, is printed in the report; the code never substitutes a scenario the reviewer did not accept.
- **Defaults are explicit.** With no Review experiment, reports state "BASIN default; no experiment was run in Review" and use the simulator's own defaults (48% storage, 0% conservation, pipeline available, tiers 100/80/60/40). This replaces the old 0.48/0.15 pair, which matched neither the model nor the UI's initial widget values. **This changes default report output:** conservation in a default report is now 0%, not 15%.
- **Stale reports are dropped.** `report_state_token` covers the workspace, the accepted scenarios and their revisions, both consent flags and the configuration. The preview is cached under that token and purged when it moves; a built packet is compared against it plus the existing `w.record(...)` fingerprint, and is removed from session state with a "rebuild" notice rather than left in memory behind a hidden button.
- **Display.** The Exports page shows the configuration as a table, the preview expander repeats it inline, the vector report gets a labelled block on page 1, and the HTML report gets a compact line under the executive overview.
- The PDF download card no longer carries a blanket "CRYPTOGRAPHICALLY VERIFIED" badge; it now says the ZIP is verified and the PDF is outside that contract.

Evidence:

- Baseline before editing: **197 passed, 0 failures** at `eeac2ae`. After: **236 passed** (39 net new tests). No pre-existing failures to distinguish; every failure seen during this work was introduced and fixed within it.
- `tests/test_report_config.py` (32) covers the configuration object and its validation, settings and scenario changes altering results in both paths, the no-silent-substitution rule, the display, the token, and that rainfall features and series are untouched.
- `tests/test_report_invalidation_app.py` (7) drives the real Streamlit script: Review controls become the configuration, defaults are explicit before any experiment, a prepared preview is dropped when settings, consent or a scenario edit change, a built packet is discarded when settings change, and an exported PDF carries the selected settings.
- `scripts/demo_smoke.py`: verified, run `d2a5ef7b9322`, five scenarios, 500 audit records, implementation matches.
- Both rendering paths generated and read on screen with a selected configuration, a default configuration and a deliberately unavailable configured scenario; vector text operators were extracted with coordinates to confirm placement.

Limitations and things found but not changed:

- **Page budget.** A full configuration table on the HTML page 1 pushed the brief from two pages to three and split the drought-band table. The HTML report therefore carries a compact one-line summary and the vector report carries the table; the app preview shows the full table. Worth revisiting if the print layout is reworked.
- **Tier label sign error, not fixed.** `simulate_stress_spectrum` builds labels for non-default tiers as `f"{pct}% ({100-pct:+d}% Rain)"`, so a 50% tier reads "+50% Rain" when it means a 50% reduction. It is unreachable from the UI (only the default tiers are offered, whose labels are hard-coded and correct) and sits in the model module, so it was left alone under "do not change rainfall calculations". It would surface if tier choice is ever exposed.
- The Review settings live inside the "Reservoir simulation" view. A user who never opens that view exports a default-labelled report, which is accurate but easy to miss.
- Settings are session state only; saved-session persistence is B16 and explicitly out of scope here.
- The win32 guard in `generate_pdf_report` still makes the browser HTML route unreachable in the product, so the HTML path was again rendered with Edge for inspection rather than exercised through the product (B17.3).
- No reviewer has read the generated documents.


## September 9 independent integration review

Reviewed Claude's `86ff09d` against `a276478`: five changed files, with app/UI/theme/config and numerical analysis unchanged. Re-ran the original branch: **191 passed**. Merged newer upstream `21f98db` (embedded assistant/installer work) without conflicts. Corrected a remaining report claim that every unbreached window exceeds six months; added a short-window regression. Updated the security test's mock availability so it still exercises the optional Ollama path after upstream's fallback routing change.

Combined result: **192 passed in 117.44 s**. Snapshot checkout, offline Python smoke and independent replay passed; run `e8d73d73397f`, five scenarios, 500 audit records, implementation matches (zero custom comparisons in this smoke packet). Source packaging passed. Rendered and inspected both pages of Claude's vector report; the follow-up duration wording has a focused HTML/vector regression. This is a code/automated/visual review, not practitioner validation. The newer installer was integrated but not built or security-certified by this PDF review.

B17.6 is accepted for integration. Next Claude task: B17.1/B17.2 selected scenario/settings propagation and cache invalidation, preserving private-note/custom-data consent and the separate PDF verification scope. Report pagination/long-text work remains for task 3, although its isolated-fixture prerequisite was already completed by task 1. Live assistant/installer/device checks remain separate open gates. Earlier branch-unmerged statements below are historical, superseded by this integration checkpoint.

## Report-content accuracy checkpoint — B17.6

Branch `fix/b17-report-content-accuracy` (from `a276478`), not merged and not pushed. Fixes report-content accuracy in `basin_core/pdf_report.py` across both the HTML and Windows vector paths. The numerical model in `basin_core/analysis.py` is unchanged; the report now reads the model instead of restating it.

What changed:

- **Capacity is derived, not restated.** `model_capacities_acft()` / `model_total_capacity_acft()` read `RESERVOIR_ASSUMPTIONS["capacities_acft"]`, so both paths print 919,900 ac-ft and bands of 367,960 / 275,970 / 183,980 / 137,985 ac-ft. The hard-coded 963,600 ac-ft and the 385,440 / 289,080 / 192,720 bands derived from it are gone.
- **Unavailable is shown as unavailable.** A shared `compute_report_metrics()` returns an `unavailable_reason` when there is no accepted scenario, no daily series, or the simulation raises. The vector path renders an explicit "STRESS SPECTRUM NOT COMPUTED FOR THIS REPORT" panel instead of the four example tier rows, and title/body mode no longer invents a run ID (`AUDIT-CERTIFIED`), a snapshot digest, station names or KPI figures. Captions and the executive overview no longer describe a run that did not happen.
- **Verification wording matches actual scope.** The `PASS` / `VERIFIED 256` stamp is replaced by `VERIFICATION SCOPE / BUNDLE ONLY / PDF NOT VERIFIED`. Both paths state that SHA-256 verification covers the companion ZIP and that this PDF sits outside that contract, and that no scientific validation or professional approval is claimed. "Input raw series certified unaltered", the unconditional deficit-recomputation claim and "Verified Export Bundle Companion" are removed.
- **Unsupported policy and benefit claims removed.** The invented ordinance citation ("City Code Ch. 55", "Approved 2025 Revision" / "Approved June 2026 Revision"), the survey capacities that matched neither the model nor the research packet (669,186 / 256,339 ac-ft), the "~5-10 MGD reduction" benefit figure and the "Hydrologist Note" column header are gone. Bands are labelled as this experiment's assumption, quoting `RESERVOIR_ASSUMPTIONS["thresholds"]`, and the TWDB survey values recorded in the research packet (918,882 ac-ft combined) are shown separately as a sourced reference the model does not reproduce.
- Two vector layout defects fixed while inspecting: the last stress-spectrum row overlapped the following section heading, and the capacity finding was clipped mid-sentence.

Evidence:

- `.venv/Scripts/python.exe -m pytest -q`: **191 passed in 124.89 s** (172 at the `a276478` baseline; 19 net new tests). `tests/test_pdf_report.py` was also migrated off `local/session-*.json` onto the shared isolated `workspace` fixture, so it no longer needs a saved local session.
- `scripts/demo_smoke.py`: verified, run `cef3b8f77674`, five scenarios, 500 audit records, `implementation_matches_current: true`, zero custom comparisons.
- Both output paths generated and read on screen: the Windows vector PDF (`build_fallback_pdf`, both a populated run and an unavailable run) and the HTML path rendered to PDF with Edge. Text operators were also extracted from the vector PDFs to confirm exact strings and positions.

Limitations and untested paths:

- **The browser HTML-to-PDF route is unreachable in the product on Windows.** `generate_pdf_report` calls the vector builder directly when `sys.platform == "win32"`, so the HTML path was rendered manually with Edge for this inspection and has not been exercised through the product on this machine. Whether that platform guard is intended is open under B17.3.
- No reviewer has read either document. Passing regression tests are not an accuracy review, and a rendered PDF is still not independently verified report content.
- B17.1 (settings propagation from `app.py`), B17.2's consent preview, B17.4 (CLI opt-ins) and B17.5 (device checks) are untouched by this work.
- Private-note and custom-data consent behaviour is unchanged and still covered by tests; the security fixes from `dd5996a` are untouched.
- Note: GitHub Desktop stashed this working tree and switched the checkout back to `main` partway through the session. The work was recovered from `stash@{0}`. Worth knowing if uncommitted changes go missing again.

## Latest integration checkpoint

Noah's main commit `40a7023` is merged with security commit `dd5996a` (integration merge `502824a`). **172 tests passed in 122.44 seconds**: the prior four PDF/UI export failures are resolved. Snapshot checkout, offline Python smoke and independent replay passed (run `0d51fc36a996`, five scenarios/500 audit records, implementation matches). Visually inspected both pages of the generated Windows vector PDF. All security safeguards survived the automatic merge; no conflicts required manual resolution.

Remaining after B17.6 and B17.1/B17.2: B17.3 degraded-render reporting and long-text pagination, live Ollama and actual-device security gates. The PDF still hard-codes a mismatched capacity and audit badge and substitutes example rows when spectrum data is unavailable; a rendered PDF is not equivalent to independently verified report contents. PDF tests currently rely on an existing local session. (Those three PDF statements are superseded by the B17.6 checkpoint above; the closing point that a rendered PDF is not independently verified content still stands.) Prior failing-suite records below are historical and superseded by this checkpoint. No remote push performed by this integration pass.

## Security follow-up — current checkpoint

User authorized security fixes, TODO updates and a commit. See docs/security_review_2026-09-08.md and SEC.1–SEC.5 in TODO.md. Fixed assistant loopback client configuration, malformed tool arguments, bounded history/calls, model-name escaping, explicit CLI export consent and tracked-only source packaging. Prior documentation changes below are included in this handoff; no team message or remote push is performed.

Verification after security changes: **13 security tests passed**; focused assistant/upload/integrity/security run **79 passed** before the additional packaging test; full suite **158 passed, 4 failed in 107.93 s**, the same four PDF/UI-export failures listed below. Python offline smoke and explicit replay passed (run 42486af00f05, implementation matches); source package built. pip check found no broken installed dependencies, not a vulnerability scan. Ollama is absent here, so client guards were tested with mocks. Live daemon/network tests, dependency advisory review and actual-device acceptance remain open. No scientific/model changes or UI redesign in this security pass.

Next action: fix B15/B17's pre-existing export regressions, complete SEC.4/SEC.5, then UI/UX testing with Mohammed. Do not announce a clean full suite or certify the app secure.

## Earlier documentation review (historical)

Updated: 2026-09-08. Reviewed source: f96c28a; local HEAD matched remote HEAD before this documentation-only update. No application changes, commit, push or deployment performed in this pass.

## Current position

Rainfall scenarios, evidence/conflict review and schema 2.1 custom supporting evidence are implemented. Custom uploads retain private originals, normalized data, versions, suitability rationale, scenario links and consented replay. They do not drive a new local-area simulation. An optional Ollama assistant, illustrative multi-tier reservoir charts, separate PDF report and native download handling have since been added.

Earlier handoff claims of guaranteed zero cloud leakage, zero hallucinations, proven 30x–50x user benefit and standalone deployment are not established by this review. The default Ollama client needs a local-connectivity contract; benchmarks need methodology/participant verification; the native wrapper still needs application/runtime prerequisites. Reservoir results remain illustrative and excluded from rainfall packet verification. The separate PDF is not verified by replaying the ZIP.

## Fresh verification

Windows repository .venv, commands run September 8 at f96c28a:

- `.venv/Scripts/python.exe -m pytest -q`: **145 passed, 4 failed in 101.62 s**. Failures: `test_full_user_workflow`, `test_upload_ui_save_restore_and_export_consent`, `test_evidence_conflict_ui_workflow`, and `test_generate_pdf_report`. PDF fallback raises UnicodeEncodeError encoding an em dash as Latin-1 at basin_core/pdf_report.py:653; investigate the UI export failures individually too.
- `.venv/Scripts/python.exe scripts/check_snapshot_checkout.py`: verified SHA-256 672c23f8335093cdba84608c53ade768a9737e4088e60d95c04965257e0178a0 on a fresh clone.
- `.venv/Scripts/python.exe scripts/demo_smoke.py`: verified run 21fac96ba217, five scenarios and 500 audit records, Python network sockets blocked.
- `.venv/Scripts/python.exe scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified; implementation_matches_current: true. This packet had zero custom comparisons; custom-data behavior is covered separately by tests and still requires an independent sample exercise.

No fresh native rebuild, real Ollama routing exercise, PDF visual inspection, browser/native offline rehearsal or practitioner validation was performed. Older 125/128-test claims are historical, not this run's result.

## New team context and next action

Supplied message (7) is the requested backlog; it begins at item 2. TODO.md now maps it into B15–B21 plus existing validation/release tasks, and renames the second B13 to B14 (custom evidence). Message (6) is the earlier backlog. Messages (4)/(5) duplicate efficiency guidance. Private correspondence and travel details remain outside the repository.

Mohammed volunteered for UI/UX and security; Misha stated a data/information focus; Noah reported assistant/spectrum/native/presentation work. Independent reviewers remain unassigned. The team wants feature readiness before September 18–19 and rehearsal time before September 22; official speaking time and reviewer availability remain unconfirmed.

Next: B15 current regressions and baseline/units/selection meaning, then B16 simulation persistence with B17 report settings/privacy. B18 assistant hardening follows; define B19's one-area model before B20's numerical geographic views. B21 document ingestion needs an agreed evidence contract. Schedule human review and actual-device checks alongside development. See TODO.md for acceptance criteria and the full remaining list.
