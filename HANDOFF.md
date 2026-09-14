# BASIN current handoff

## September 14 — Community/provider context and credibility correction

- Added a Data Dashboard intake for a Region N-wide run or a named city/provider. Specific runs record organization type/name, county or counties, optional service-area label, supply relationship, and planning purpose.
- Preserved that context in session save/load, Review, verified audit and Markdown handoff, and both HTML and vector PDF reports. The contract remains `context_only`: it does not silently claim that bundled gauges or a storage preset represent the named community.
- Wired the full Region N observation catalog into the satellite map: 191 NOAA rainfall stations, 228 USGS water sites, streams, lakes/reservoirs, HUC8 subbasins, county boundaries, and the Region N outline. Catalog presence does not imply an active gauge or modeling suitability.
- Replaced unsupported summary and assistant claims. Rainfall percentiles are described as sample comparisons; gauge concurrence no longer implies basin-wide supply failure; 35% storage is an illustrative input rather than Stage 3; and the 75,000 ac-ft reserve remains a configurable assumption.

Verification: 144 cross-surface context/map/report/replay/scientific-contract tests passed, followed by the complete suite at 719 passed with 2 expected optional-runtime skips. Browser rehearsal completed Data → Builder → Review for City of Alice, Alice service area, Jim Wells County, and displayed the same context in Review.

Remaining acceptance: map a provider's actual supply/catchment and representative gauges with a practitioner, confirm the correct adopted plan/contract, complete presentation-laptop testing, and review Esri offline-tile redistribution terms before release packaging.

## September 13–14 — Offline satellite basemap, Windows PDF visuals, and hydrologist assistant routing

Delivered offline-first satellite imagery, restored full visual PDF generation on Windows, and implemented robust natural language query handling for the built-in AI assistant.

1. **Offline Region N Satellite Basemap (`basin_core/region_n_map.py`)**:
   - Pre-cached 340 high-resolution satellite tiles (zoom levels 6–11, total 4.28 MB) at `static/tiles/World_Imagery/{z}/{y}/{x}.jpg` covering the Region N bounding box (`[-98.80, 26.59, -96.71, 28.78]`).
   - Enabled `enableStaticServing = true` in `.streamlit/config.toml` for zero-latency local HTTP serving with MapLibre GL overzooming at zoom 12+.
   - Defaulted heavy stream/lake vectors (10,669 features) to an on-demand checkbox, reducing initial JSON payload from 10.01 MB to 495 KB (95% drop) and figure generation from 3.73s to 0.03s (100x speedup).
   - Added `scripts/download_region_n_tiles.py` and updated `scripts/build_offline_bundle.py`.

2. **Windows PDF Visual Export (`basin_core/pdf_report.py`)**:
   - Removed the hardcoded `if sys.platform == "win32"` fallback bypass in `generate_pdf_report_with_status`.
   - Headless Microsoft Edge (`msedge.exe`) renders the HTML report directly to PDF on Windows in ~2 seconds (~335 KB), preserving all Kaleido visual charts (Pareto frontier, Stage milestone timelines), 3-way ML model comparison tables, and diagnostic scorecards.
   - Clean degradation to the 24 KB vector fallback preserved if headless browser rendering fails.

3. **AI Assistant Natural Language & Intent Enhancements (`basin_core/assistant.py`)**:
   - **Workspace Run & Shortlist Overview (`_render_workspace_summary`)**: Responds to queries about scenarios just run with a structured table of shortlisted scenarios, candidate counts, water system capacity, and key extremes (peak shortfall, longest chronic drought, highest concurrence).
   - **Worst / Top / Longest Auto-Resolution**: Intelligently identifies and profiles target scenarios when no ID is provided (e.g. "What is the worst scenario?").
   - **Comparative Ranking Breakdown (`_render_rank_comparison`)**: Generates side-by-side component score tables explaining why scenario A beat scenario B.
   - **9 Domain Hydrologic & Rural Council FAQs**: Multi-station concurrence, illustrative storage inputs, inactive-storage assumptions, Mary Rhodes Pipeline context, clustering diversity, rural council review checklist, scenarios versus forecasts, point rainfall versus reservoir volume, and summer timing boundaries. Unsupported operational conclusions added in the original routing pass were corrected on September 14.
   - Verified across 55 assistant tests (16 tests in `tests/test_assistant_hydrologist_queries.py`).

Verification: `tests/test_assistant_hydrologist_queries.py` (16 passed), `tests/test_geo_map.py` (4 passed), `tests/test_pdf_report.py` (23 passed), `tests/test_qwen_security.py` (16 passed), `tests/test_native_runtime_install.py` (50 passed, 2 skipped). Zero test regressions.

## September 13 — Simple/Advanced Review UI and density pass

The presentation-mode contract from `11bbe6a` is now wired into the live Review workflow. A persistent two-button **Simple View / Advanced View** control changes presentation only; the workspace record, ranking, scenario revisions, review decisions, simulation inputs, saved runs, and exports remain on their existing contracts.

- **Simple View:** keeps at most two focus tabs in the main row, moves the remaining tools under **More tools**, limits the decision area to **Include**, **Exclude**, and **Next scenario**, and hides batch review. Rainfall history/ranking and monthly agronomic detail use compact expanders. Storage uses the selected workspace system and retained settings but presents one static combined-storage trajectory and three decision metrics without playback, sensitivity, per-source bars, delivery diagnostics, or regional context.
- **Advanced View:** exposes all five Review tools in one row, batch review, simulation inputs, animated per-source storage, additional rainfall reductions, band timelines, sector delivery, pipeline comparison, and dated context.
- **Copy:** applied the 17-item copy audit across `app.py` and `basin_ui.py`; long setup, storage, rainfall, agronomic, evidence, and comparison explanations now use shorter labels or captions while required source-date, catchment-weighting, forecast, calibration, and official-action boundaries remain visible.
- **Visualization:** added `storage_trajectory_figure`, which plots the exact `combined_pct` output from the existing simulation dataframe with unobtrusive assumed-band shading and no animation controls.

Files changed: `app.py`, `basin_ui.py`, `basin_core/visualizers.py`, `tests/test_app.py`, `tests/test_failures.py`, `tests/test_presentation_copy_audit.py`, `tests/test_report_invalidation_app.py`, `tests/test_review_preferences.py`, `tests/test_ui_improvements.py`, and `tests/test_visualizers.py`.

Verification: focused mode/copy/visualizer tests passed **70 tests**; UI regression selection passed **35 tests** after updating technical workflows to select Advanced View; the final complete suite passed **695 tests with 2 optional-runtime skips in 436.45s**. Browser verification at `127.0.0.1:8516` confirmed the Simple/Advanced switch, two-tab Simple layout, five-tab Advanced layout, compact decision actions, and the uncluttered Simple storage chart. `git diff --check` passed.

Next action: run Part C external acceptance on the presentation laptop and projector, including screen-reader and intended-user review. No implementation blocker is open.

## September 13 — Simple and Advanced presentation mode contract & copy audit

Implemented the non-UI foundation for **Simple View** and **Advanced View** in `basin_core/review_preferences.py` without modifying calculations, exporters, PDF generation, document ingestion, `app.py`, `basin_ui.py`, `basin_theme.py`, or visualizers.

1. **Mode Contract & Backward Compatibility**:
   - Mapped `"guided"` $\leftrightarrow$ `"simple"` (Simple View) and `"technical"` $\leftrightarrow$ `"advanced"` (Advanced View).
   - Preserved `GUIDANCE` keys `"guided"` and `"technical"` for existing callers while updating user-visible presentation labels to `"Simple View"` and `"Advanced View"`.
   - Added properties `simple: bool`, `advanced: bool`, `mode: str` (`"simple"` | `"advanced"`), `presentation_label: str`, while preserving `guided` and `technical`.
   - Constructor and `replace()` support `mode` and `guidance`.
   - `from_record()` gracefully tolerates old files, missing values, foreign strings, and malformed mode values, safely falling back to Simple View.
   - `to_record()` serializes both `guidance` and `mode`.

2. **Typed Review Pane and Technical Detail Mappings**:
   - `PANE_PRESENTATIONS` defines placement (`"primary"`, `"secondary"`, `"expander"`, `"hidden"`) for all 5 Review panes (`rainfall`, `provenance`, `storage`, `agronomics`, `edits`).
   - In Simple View, primary panes are bounded to at most 2 tabs (`("rainfall", "provenance")` or focus-primary tabs), keeping cognitive load low for first-time reviewers.
   - In Advanced View, every Review tool is primary and directly reachable.
   - Mandatory safety disclosures and evidence provenance (`provenance`) are strictly required to remain primary in both modes.
   - `TECHNICAL_DETAILS` specifies placement (`"primary"`, `"expander"`, `"advanced_only"`, `"tooltip"`) for 23 granular technical tools across all panes.

3. **User-Visible Copy Replacement Inventory**:
   Audited `app.py` and `basin_ui.py` to identify competing explanations, dense multi-sentence disclaimers, and negative assertions. Produced a concrete 17-item replacement inventory:
   | Location | Context | Current Wording | Proposed Concise Wording | Reason | Target Placement |
   |---|---|---|---|---|---|
   | `app.py:1241` | Scenario Builder focus caption | Configures which visuals and tools appear first in Review. Does not change numerical calculations or export consent. | Choose what to focus on first. Does not affect calculations or export. | Reduces pre-run cognitive burden; disclaimers moved to tooltip | Tooltip |
   | `app.py:1252` | Guidance selectbox | How much guidance do you want? Guided explanations add orientation; all scientific limitations remain visible in either mode. | Presentation View (Simple View / Advanced View) | Focuses on view complexity rather than user competence | Tooltip |
   | `app.py:1284` | Retained rainfall slider | Percentage of observed rainfall used by the scenario (e.g. 70% retained = 30% reduction from observed rainfall). Multiplies observed daily rainfall at affected stations. | Retained rainfall percentage (e.g., 70% retained = 30% reduction). | Removes redundant daily multiplication sentence | Tooltip |
   | `app.py:1490-1492` | Review setup card | Three questions decide which tools appear first. Every tool stays reachable, and none of this changes calculations, ranking weights, review decisions or export consent. | Review View: Simple for immediate decision or Advanced for full diagnostics. | Replaces verbose defensive enumeration with clear view description | Expander |
   | `app.py:1552-1553` | Custom data intent caption | Your focus records an intent to use your own rainfall data. Nothing has been uploaded or validated by that choice; add a CSV in Step 1: Data Dashboard. | Note: Focus set for custom data. Upload and validate a CSV in Data Dashboard. | Short action-oriented reminder before tabs | Tooltip |
   | `app.py:1556-1557` | Weight preset suggestion | This focus often pairs with the ranking preset. Ranking weights are not changed by your focus; apply a preset yourself in Step 2: Scenario Builder if you want it. | Tip: Pairs well with the suggested ranking preset in Step 2. | Eliminates repetitive multi-sentence disclaimer | Tooltip |
   | `app.py:1680` | Storage container caption | Optional experiment. These settings affect storage exploration; the handoff decision above concerns the rainfall revision. | Optional illustrative storage experiment. | Repetitive disclaimer; full bounds in disclosures | Tooltip |
   | `app.py:1917` | Agronomics tab top caption | Cross-sector operational impacts calculated from daily scenario rainfall. Illustrative decision-support estimates based on Texas ET Network and Texas A&M Forest Service guidelines; not regulatory declarations or official crop/burn directives. | Decision-support estimates for crop irrigation deficit and wildfire stress. | Prevents dense disclaimer from pushing visual charts below fold | Tooltip |
   | `app.py:1964` | KBDI statutory disclaimer | KBDI and crop water balance models provide exploratory scenario impacts. Official burn bans are enacted exclusively by County Commissioners Courts under Tex. Local Gov't Code § 352.081. Reservoir stages reflect illustrative operating rules, not municipal emergency orders. | Illustrative decision support. Official burn bans are enacted exclusively by County Commissioners Courts. | Move lengthy statutory code citations to Advanced View | Advanced View |
   | `app.py:1985` | Rainfall dashed reference line | The dashed reference uses this station's 1991–2020 monthly mean daily rainfall. The scenario line includes your current edits. | Dashed line: 1991–2020 monthly reference mean. | Shortens visual chart footnote | Tooltip |
   | `app.py:1987` | 30-day deficit axis caption | Above zero means less rainfall than the reference over the preceding 30 days; below zero means more. The first 29 days have no complete window. | Positive: rainfall deficit vs 30-day reference; Negative: surplus. | Converts run-on prose into clear axis legend | Tooltip |
   | `app.py:1995` | Concurrence explanation | Each station must exceed its own historical rainfall-deficit threshold in the same window. This is a frequency over time, not a percentage of stations. | Concurring stress persistence frequency across eligible 30-day windows. | Removes negative assertion; defines technical metric directly | Expander |
   | `app.py:2000` | Ranking score caption | This reflects your priorities; it is not a probability or an evidence-quality score. | Multivariate ranking score based on configured priorities. | Replaces double-negative disclaimer with positive definition | Tooltip |
   | `app.py:2003` | Rainfall edits tab note | Changing rainfall creates a revision and clears its previous acceptance. Add your reason in the review note first. | Edits create a new scenario revision and require review re-approval. | Concise operational rule | Tooltip |
   | `basin_ui.py:25` | Evidence panel disclaimer | Evidence types and applicability are declarations. No numerical trust score or automatic source winner is assigned. | Evidence applicability is qualitative; no automatic trust score is applied. | Clearer phrasing | Tooltip |
   | `basin_ui.py:111` | Candidate comparison caption | Profile names describe feature patterns. With one station, concurrence means that station's stress frequency. Approval concerns rainfall content; it does not endorse later priority settings. | Approval confirms rainfall content validity, not downstream priority weights. | Direct statement of review boundary | Advanced View |
   | `basin_ui.py:123` | Weight preview caption | Rejected candidates are excluded from this preview. No candidates are regenerated and no reviews or shortlist entries change. | Live weight preview: candidates and review statuses remain unchanged. | Concise assurance without multiple negative clauses | Tooltip |

4. **Verification**:
   - `pytest tests/test_review_preferences.py tests/test_presentation_copy_audit.py`: **61 passed** in 60.70s.
   - Focused test suite (`test_review_preferences.py`, `test_presentation_copy_audit.py`, `test_document_ingestion.py`, `test_custom_data.py`, `test_simulation_contract.py`, `test_rainfall_terminology.py`, `test_custom_observation_language.py`): **172 passed** in 104.53s.
   - Preserved all boundaries: zero modifications made to calculations, exporters, PDF generation, or document ingestion. UI files (`app.py`, `basin_ui.py`, `basin_theme.py`, `visualizers.py`) are avoided for teammate implementation.

Next technical action: Teammate pulls Gemini's contract, implements UI presentation layout and button hierarchy in `app.py`/`basin_ui.py`, verifies 375/640/1280px views, and runs full regression suite.

## September 13 — T5 document ingestion foundation

A safe, typed domain foundation for user-provided PDF and report documents is implemented in `basin_core/document_ingestion.py` and integrated into the workspace, integrity, evidence, and export layers without adding new external parser dependencies.

1. **Document Identity & Strict Boundaries**:
   - Ingested documents receive deterministic, content-addressed IDs (`doc-{sha256}`) and immutable metadata records (`DocumentIdentity`).
   - Magic signature sniffing validates `%PDF-` for PDFs and clean UTF-8 text for `.txt`. Mismatched extensions, archive files (`.zip`, `.gz`, `.tar`, `.7z`), executables (`MZ`, `ELF`, `.exe`), encrypted/password-protected PDFs (`/Encrypt`), active scripts/macros (`/JavaScript`, `/JS`, `/Launch`), empty files, and path-traversal filenames are rejected with typed errors.
   - File size is capped at 30 MB, page count at 100 pages, and text volume at bounded character limits.
   - Original file bytes are stored privately in session state (`document_originals`), outside Git and excluded from exported bundles.

2. **Extraction Modeling & State Machine**:
   - Extraction produces page-level blocks (`ExtractionBlock`) preserving page numbers, deterministic block IDs, text status (`success`, `partial`, `empty`), and content digests.
   - Extracted text is treated as unverified source material and is never automatically promoted to evidence.
   - Strict lifecycle transitions enforced: `uploaded` $\to$ `extracted` $\to$ `needs_review` $\to$ `accepted_as_evidence` / `rejected`.

3. **Human Review, Evidence Connection & Claim Boundaries**:
   - Promotion to evidence strictly requires human review recording reviewer rationale, confirmed statement, cited page/block IDs, and exact source digest match.
   - Accepted material converts to standard BASIN evidence records citing `doc://doc-{sha256}/page/{page_num}` with mandatory non-predictive disclaimers.
   - Attaching or rejecting document evidence invalidates scenario approvals, requiring reviewed re-approval.
   - Review rationales and confirmed statements are strictly validated against BASIN prohibited claims boundaries (rejecting official approval, certified forecasts, calibrated catchment, safe yield, and prompt injection).

4. **Privacy & Verified Replay**:
   - Default exports include accepted evidence citations and provenance while stripping raw document bytes, unreviewed drafts, and private notes (unless consented). Replay verification succeeds with document evidence.

Verification: `pytest tests/test_document_ingestion.py` passed **40 passed in 2.65s**. Focused regression suite passed **174 passed in 60.46s**. The full repository suite passed **657 passed, 3 skipped in 449.87s**. `git diff --check` passed.

Next technical action: implement the PDF extraction adapter and Streamlit document upload/review interface. Presentation-laptop, projector, offline, intended-user, and organizer checks remain Part C external acceptance.

## September 13 — report/export quality and responsive Review polish

The handoff report and verified ZIP now present one consistent, reviewable package. Both HTML and fallback-vector PDFs follow the same eight-section order: executive summary, scenario identity, review rationale, storage assumptions, experiment results, observation provenance, limitations, and verification hashes. Long notes and labels remain inside page bounds; custom observations retain the T3 source, coverage, and catchment language; rainfall percentages retain the T2 baseline language. Verified bundles retain all saved simulation runs with explicit review state, keep note-consent behavior through revocation, and continue to pass manifest and replay verification.

The Review storage illustration is now responsive. The reservoir snapshot and combined-pool trajectory use separate vertical panels, reservoir names wrap onto deliberate word lines, exact capacities remain available in hover details, and storage-band labels occupy a dedicated right gutter beside their matching lines. The single-scenario band timeline no longer reserves an empty label column. At 375×812, the top controls and four-stage navigation form compact grids, Personal Notes and AI become corner controls, and the assistant opens as a full-width drawer.

Browser verification used a clean Streamlit process at 375×812 and 1280×720. The phone view showed distinct reservoir labels, readable band labels, visible playback controls, and an uncluttered scenario-band timeline; the desktop view preserved full-width chart readability. Focused verification passed `14` app/visualizer tests and `152` report/export/terminology tests. The final stable full regression suite passed **617 tests with 3 optional-runtime skips in 461.79s**, including the 10-case export quality matrix in `tests/test_export_quality.py`. `git diff --check` passed.

Next technical action: define T5 document-ingestion provenance, extraction-review, and privacy contracts before accepting PDF/report inputs. Presentation-laptop, projector, offline, intended-user, and organizer checks remain Part C external acceptance.

## September 13 — T2 terminology audit & T3 custom observation provenance

Tasks T2 and T3 have been fully implemented, verified, and integrated:

1. **T2 — Rainfall percentage terminology audit:**
   - Standardized all user-visible and exported rainfall percentages to explicitly state their baseline and whether they denote retained rainfall (e.g. "70% of observed rainfall") or a reduction (e.g. "30% reduction from observed rainfall").
   - Implemented canonical formatters in `basin_core/summary.py` (`format_retained_rainfall`, `format_rainfall_reduction`, `format_rainfall_dual_explanation`) with strict numerical validation rejecting negative, NaN, and infinite values.
   - Audited and updated `app.py`, `basin_core/assistant.py`, `basin_core/exporter.py`, `basin_core/pdf_report.py`, `basin_core/simulation.py`, and `basin_core/scientific_contract.py`.
   - Prohibited isolated or undefined percentage claims via `validate_report_text_against_prohibited_claims`.
   - Verified by `tests/test_rainfall_terminology.py` (9 tests passing).

2. **T3 — Custom-observation source and date language:**
   - Explicitly marked all user-provided datasets as unverified across preview, comparison, saved panels, and exports (`format_custom_source_label`).
   - Standardized observation date bounds with valid record counts (`format_custom_coverage_dates`).
   - Integrated mandatory proxy/catchment disclaimer: `"Custom data represents unverified local observations, not a calibrated catchment model."`
   - Strengthened `validate_report_text_against_prohibited_claims` to strictly reject claims of official, verified, or certified status for custom data.
   - Preserved full backward compatibility with legacy saved evidence records in `custom_data.py`.
   - Verified by `tests/test_custom_observation_language.py` (8 tests passing).

Verification: The full test suite passed **607 passed, 3 skipped in 825.52s**. Zero failures. `git diff --check` clean. Presentation-device and scientific acceptance remain governed by Part C.

## September 12 — T1 shared storage-system contract

Review and assistant tools now consume one versioned workspace water-system selection. New saved simulation records contain the complete preset or custom configuration and replay against that exact snapshot. Save/reopen restores the selection; reports and the verified handoff brief identify it. Changing the selected system deactivates previous active runs without deleting historical records or reviews.

Review calculation is deliberately split into a side-effect-free preview and an explicit persistence action. Navigating between scenarios no longer creates active simulations. Choosing **Record experiment review** saves and reviews the exact preview identity; later changes to the scenario, system or settings prevent that run from being silently substituted. Assistant experiment requests continue to save runs automatically using the same workspace selection.

Gemini's native-release work is integrated at `b1c51ac`, and its T4 scientific contract is integrated at `3a03ebd`. The T4 module defines and tests the data, calibration, review and prohibited-claim boundaries without changing the current illustrative calculation. Physical presentation-laptop, offline, projector, intended-user and organizer gates remain open; calibrated hydrology still requires approved source data and expert review.

Verification: the final combined suite passed **590 tests with 3 optional-runtime skips in 403.10s**. A fresh browser at 127.0.0.1:8508 confirmed the Region N default, selection of the 12,000 ac-ft municipal preset, changed one-pool trajectory/metrics/wording, explicit experiment rationale, and the saved-review success state. `git diff --check` passed. Presentation-device and scientific acceptance are not implied.

## September 11 — Part C status and development-device checkpoint

Current state: Review browser acceptance is merged at `cf374bd`; the status reconciliation is pushed at `0098dad`. The active release documents now separate implementation, automated verification, development-machine observation and external acceptance. The 601-line historical TODO is preserved under `docs/archive/`; the active `TODO.md` is a concise ordered queue.

The documentation reconciliation identified the former split between assistant-created Region N runs and Review’s transient selectable-system configuration. The September 12 T1 work above resolves that split.

Part C checks completed on this development Windows machine:

- Actual Chromium Review acceptance at 1280×720 and 375×812 in Dark and Light, including four focus profiles, skip/show-all/change-focus, saved-session restoration, visible keyboard focus and tutorial targeting.
- Browser launcher selected port 8505 and reached readiness when requested port 8504 was occupied.
- Development environment recorded as Windows NT 10.0.26200.0 AMD64, CPython 3.12.14 and Streamlit 1.63.0.
- Tracked `BASIN.exe`: 14,869,768 bytes, SHA-256 `838ee698c8ec3d879af622818fb566fcd30c496833b0a2057e0c9dad1e195809`. Identity recorded only; the executable was not accepted in this pass.
- A real browser generated a six-scenario PDF/ZIP, replay verified six scenarios and 300 audit records, and all three PDF pages were visually inspected. The consent cycle exposed and corrected missing workspace-level provider notes in PDF output. With consent on, `PRIVATE-DEMO-123` appeared in ZIP and PDF; after revocation/rebuild it appeared in neither and the PDF disclosed omission.

Changed files are listed in `docs/status_reconciliation_handoff.md`. No production code, dependencies, configuration, data or model artifacts changed during status reconciliation.

Verification:

- `git diff --check`: passed.
- Relative links in every changed Markdown file: passed.
- Diff inspection found no `.py`, `.cmd`, `.sh`, `.toml`, `.txt` or `.json` changes.
- Part B regression baseline remains **554 passed, 3 skipped**; routing **50/50**; demo replay verified.
- Focused PDF/privacy regression after the correction: **39 passed**.

The earlier GitHub fetch limitation is resolved; upstream was fetched and integrated in this review. Actual presentation-laptop install/offline/native/download/PDF/projector checks, intended-user exercise, organizer format and final rehearsal remain not run. No weights were downloaded and no network/firewall settings were changed.

Next action: run Task 6 on the actual presentation laptop with the user controlling connectivity and model download authorization.

## Task-branch integration

Task branches `864d95f` and `127a344` are integrated with newer upstream `0098dad`. The newer live board, source/persistence distinctions, browser evidence and presentation disclaimers take precedence. Original branch handoffs are retained in `docs/archive/task_branch_review_acceptance_handoff.md` and `docs/archive/task_branch_status_reconciliation_handoff.md`. The newer logo styling is preserved without a second padded wrapper; the original checkbox/radio keyboard-focus rule is retained. Task 6 remains external acceptance; its new-chat prompt is in `docs/next_tasks/06_laptop_and_people.md`.

Final combined verification after the provider-note correction and teammate integration: Review preferences, AppTest workflow, UI improvements, cross-output consent and both PDF paths passed **100 tests in 102.89s**. The teammate integration had separately passed its 61-test UI set; an earlier focused UI/storage run passed 119 tests before the last upstream reconciliation. Neither is a final full-suite result. `git diff --check` passed. No fresh physical-device acceptance is claimed by this integration review.
