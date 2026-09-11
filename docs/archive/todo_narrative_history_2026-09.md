# BASIN TODO narrative archive — through 2026-09-11

Archived by the September 11 status-reconciliation pass
(`docs/status_reconciliation_handoff.md`). These are dated checkpoint narratives that
were previously interleaved in `TODO.md`. They are preserved verbatim as historical
evidence; `TODO.md` keeps only the live task board (the B-numbered sections, the shared
board table, and a reconciled current-status summary) plus links back here. Where a
narrative below states a "next step" or claims a task is outstanding, check `TODO.md`'s
current B-board first — several of these were already completed by the time of this
archival pass (for example, an "Ollama client pinning" next step mentioned in the task-3
review below refers to an old numbering scheme; that pinning is done under SEC.6/7/8).

---

### September 9 Rural Usability, Data Sovereignty, Agronomics & Optional AI Installer — COMPLETE
- [x] **Setup & Installer Choice (`Setup BASIN.cmd`)**: Added interactive prompt `[y/N]` and `--with-ai` / `--no-ai` CLI flags. Clearly documents that the 2.1 GB embedded Qwen model download requires internet, while skipping allows 100% offline installation with instant direct tools.
- [x] **US Customary Units Default & Global Toggle (`app.py`, `basin_core/summary.py`, `basin_core/visualizers.py`)**: US customary units default (`in`, `ac-ft`, `GPM`) with immediate global toggle in header. Dual-unit text summaries and unit-aware chart visualizers preserve 100% test compatibility.
- [x] **Storage Preset Default & Dynamic Emergency Pipeline (`basin_core/water_system.py`, `app.py`)**: "Small Municipal District (12k ac-ft)" and "Rural Farm Pond (1.5k ac-ft)" presets available with active emergency pipeline/intertie modeling (`demand_no_pipeline_acft_day`).
- [x] **Unrestricted Navigation (`app.py`)**: All 4 tabs (Data, Workspace, Review, Export) accessible without artificial "Accept" lock gates.
- [x] **Data Sovereignty Core Engine (`basin_core/data.py`, `basin_core/engine.py`, `app.py`)**: User-uploaded local rainfall CSVs can be activated as the driving gauge to generate candidate scenarios and run reservoir simulations.
- [x] **Agronomics & Wildfire Danger Panel (`basin_core/agronomics.py`, `app.py`, `tests/test_agronomics.py`)**: Texas Reference ET ($ET_o$), crop water demand ($ET_c = ET_o \times K_c$) for 5 staple crops (cotton, sorghum, corn, pasture, row crops), and Keetch-Byram Drought Index (KBDI 0–800) with county burn ban detection (KBDI > 600).
- [x] **Instant UI Chips & CPU Prompt Optimization (`basin_ui.py`, `basin_core/assistant.py`)**: 6 instant analysis chips (0.01s latency, zero LLM overhead); dynamic tool candidate pruning drops prompt tokens by 75% and speeds CPU inference by 3.3x (from 30.4s to 9.0s).
- [x] **Honest Environmental Footprint Accounting (`app.py`)**: Separate reporting of Data Processing (K-Means) energy and active Assistant AI inference energy.
- [x] **Full test suite pass rate: 308 / 308 passed (100.0%) across all 25 test modules!**

## September 8 team-context reconciliation

### September 9 task 3 independent review

Completed the task 3 layout/isolation scope, with review fixes for a single note spanning multiple pages, width measurement after symbol transliteration, wide WinAnsi punctuation, readable HTML table columns, and wrapped vector spectrum labels. B17.7 is complete. **B17.3 remains partial** because browser-renderer failure/degraded-output reporting is not finished; Unicode fonts are also not implemented. Task 4 is still needed: test and pin the optional Ollama Python client, verify its real loopback/proxy/redirect behavior using a controlled local fixture, and record a scoped dependency-advisory report. Do that on a separate branch from updated main; do not merge it without review. It does not establish daemon egress behavior.

Manual acceptance instructions: [Report and device checklist](../report_device_acceptance.md). Security/dependency/live-model and actual-device gates remain open. Final suite: **268 passed**; snapshot, smoke, explicit replay and source packaging passed. Visual-review scope is recorded in the newest HANDOFF checkpoint.

### September 9 task 2 independent review (historical)

B17.1/B17.2 now include additional review fixes: preview identity covers current workspace contents (including changed consented notes and weights), no-accepted-scenario previews are removed, changing workspaces clears prior report/configuration state, and Review settings survive navigation. A missing configured scenario or mismatched revision now makes the experiment unavailable until reconfigured instead of simulating another accepted scenario. Custom tier labels correctly show 50% retention as -50% rainfall; calculations are unchanged. The export success message distinguishes the verified ZIP from its separate unverified PDF.

B17.1/B17.2 completion is for current-session configuration and export wiring, not B16 saved/replayable simulations. The task 3 layout/isolation work is now completed as recorded above; renderer degradation handling and device checks remain open. SEC.4/SEC.5, B09 human validation, B10 installer/device/offline checks, B19 area modeling and B21 document ingestion remain open. B17.4's basic CLI consent flags were implemented under SEC.2; its broader cross-output/device checks still need completion. Independent review: **241 tests passed**, snapshot, offline Python smoke, explicit replay (implementation matches current) and source packaging passed. See the newest HANDOFF checkpoint for scope and evidence.

September 9 follow-up: B17.6 independently reviewed and accepted for integration with upstream `21f98db`. Original Claude branch: 191 passing tests; combined build plus short-window report regression: **192 passed**. Snapshot, Python offline smoke, explicit replay and source packaging passed. Fixed leftover six-month no-breach wording; adapted the security mock to exercise the optional Ollama route. PDF fixture isolation is already done, so task 3 should not redo it. **Superseded next step: B17.1/B17.2 are now complete in the task 2 review above.** Long-text/pagination, domain review, live model/network and native installer/device acceptance remain open. New upstream installer functionality is not certified by this report review.

### Combined-build verification after Noah's update

Merged Noah's `40a7023` into the security branch (merge `502824a`). **172 tests passed in 122.44 s**, including the 13 security tests and the previously failing PDF/UI export workflows. Fresh-checkout snapshot, Python offline smoke and independent replay passed; run `0d51fc36a996`, five scenarios, 500 audit records, implementation matches. No custom comparisons in that smoke packet. A generated two-page Windows PDF was rendered and visually inspected. Security client restrictions, HTML escaping, CLI consent and tracked-only packaging survived the merge.

The previous four test failures are resolved in this combined build. **B15.1's passing-suite gate is complete at this revision.** The report-content defects listed here on September 8 are corrected in B17.6 below (branch `fix/b17-report-content-accuracy`): the hard-coded 963,600 ac-ft total, the substituted example spectrum rows, the unconditional audit/PASS wording and the unsupported policy/benefit assertions. `tests/test_pdf_report.py` no longer depends on an existing local session; it builds an isolated workspace from the shared fixture. B17 still remains partial: settings propagation from `app.py` (B17.1), the consent preview (B17.2), CLI opt-ins (B17.4) and device checks (B17.5) are untouched by that work. Live Ollama/device checks remain open.

Security follow-up: [September 8 security review](../security_review_2026-09-08.md) records findings, fixes, tests and remaining gates. Application-level hardening is implemented; live Ollama/network validation and dependency advisory review remain open. Do not mark the entire application "secure" from these checks.

- [x] **SEC.1** Fix assistant client destination/proxy/redirect configuration, model-name filtering, tool argument validation and bounded calls/history; add mocked boundary and invalid-call tests.
- [x] **SEC.2** Make CLI notes/custom exports opt-in, escape model-name HTML, and prevent untracked files being swept into source packages; test consent propagation and package exclusion.
- [ ] **SEC.4** Validate live Ollama and daemon egress on the presentation laptop. **Partially complete.** The dependency advisory review and the optional-stack pin are done (see SEC.6); embedded Qwen offline assistant inference is implemented and rehearsed locally. Observing daemon outbound traffic on the presentation machine remains open.
- [x] **SEC.6** Pin and test the optional assistant client, and run a dependency advisory review. `requirements.txt` moves from `ollama>=0.4.0` to `ollama==0.6.2` after testing 0.4.0/0.4.9/0.5.4/0.6.2 with `scripts/probe_ollama_client.py`; `requirements-assistant.txt` pins the transitive closure that actually implements the proxy/redirect/timeout behaviour. `tests/test_ollama_client.py` verifies against the real installed client that BASIN's options reach the transport, that a hostile `OLLAMA_HOST`/proxy environment does not move the endpoint, and that a local 307 fixture is not followed, all on loopback with no external calls and no model download. [Advisory review](../dependency_advisories_2026-09-09.md) records commands, date, scope, findings and limits; [setup doc](../ollama_setup.md) separates the Python package, the Ollama service and the model. Finding A-1 was corrected during integration under SEC.8; active chat has since moved to embedded Qwen.
- [ ] **SEC.5** Complete actual-device browser/native/download/PDF checks, frozen-package privacy inspection and broader adversarial/session-input testing. Earlier B15 export test failures are resolved; these device/privacy acceptance checks remain open.

Message (7) is the latest supplied backlog. It starts at item 2; its closing recommendation mentions baseline/units/scenario-selection repairs without supplying item 1. B15 records that prerequisite from inspected code rather than inventing a missing attachment section. Message (6) is the earlier backlog; messages (4)/(5) are duplicate efficiency guidance, not feature requirements. The private Discord transcript is context, not evidence of tests or authorization to contact people, publish, deploy or book travel.

- Team-stated lanes: Mohammed volunteered for UI/UX and security; Misha stated a focus on information/data; Noah reported assistant, spectrum, native and presentation work and proposed a download website. These are context, not invented acceptance or reviewer assignments. Reviewers remain unassigned.
- Team target: feature readiness before September 18–19, with rehearsal time protected ahead of the September 22 showcase. This is a planning target, not an organizer deadline. The proposed meeting was moved toward Thursday; confirmation and professional-review arrangements remain with the team. Travel-form completion is individual and outside this engineering board.
- Implemented: historical scenarios/review/export; schema 2.1 saved custom evidence with consent, versioning and replay; optional Ollama assistant; stress-spectrum charts; separate PDF output; native download handling. Implementation is not proof of usability, scientific validation, offline isolation or executable self-containment.
- Corrected since earlier backlog: PDF breach arithmetic and PDF note opt-in have code/tests; do not reopen these as wholly absent. Selected-settings propagation and report cache invalidation are now done under B17.1/B17.2; fallback/degraded-render reporting (B17.3), CLI opt-ins (B17.4), device checks (B17.5) and independent PDF verification remain open.
- Current checks: snapshot checkout, Python offline smoke and explicit replay passed; run `21fac96ba217`, five scenarios, 500 audit records, implementation matches. That smoke packet contains **zero custom comparisons**; it is not a custom-data acceptance exercise. Full-suite result is recorded in HANDOFF.md when the current run finishes.
- Priority order: B15 correctness → B16 persistence/B17 report alignment → B18 assistant/privacy hardening → B19 one area model → B20 geographic views. B21 document ingestion can proceed after its evidence contract is agreed. Human validation and event confirmation should proceed alongside technical work.

The duplicate custom-evidence B13 heading is renamed B14 below; B13 remains the UI workflow task. Earlier checkpoint counts are historical, not current test totals. All new unchecked items are open work, with completed portions stated explicitly.

## Active implementation — September 6

User authorized completing this board. Implementation owner: Codex on `codex/demo-ready`.
Intended independent reviewer: a TAMUCC professional identified by the user; name and review evidence pending.
User explicitly selected B08 Path B: retain an illustrative reservoir experiment. Paths A/C are not selected.
Primary workflow: rural-serving analyst prepares three reviewed rainfall scenarios, inspects evidence, records an unresolved assumption, and exports a packet for expert review.
Implement B02/B04 baseline first, B03/B05 evidence next, then B06 comparison. One implementer owns the shared schema and app integration.
Presentation device is a different Windows laptop. The actual Stage 1 submission, finalist tie-breaker Q&A, August 10 rules and resource packet are available; finalist-specific presentation length/format instructions, freeze and device verification remain pending.

## CSV preview checkpoint — 2026-09-06

The custom single-station CSV preview is implemented and verified with 97 integrated tests. See README for setup and docs/local_upload_and_research_plan.md for the next slices. This preview does not persist uploads or connect them to scenario generation; those tasks remain open. The user authorized publication of this checkpoint. Existing evidence and comparison work from main is retained.

## Tutorial layout checkpoint — 2026-09-06 (published in `83d593d`, review pending)

B11 usability fix: a single guide now appears at the top of the main area, with grouped navigation and explicit target locations. Real Streamlit containers outline the actual widgets; the disconnected HTML strips and decorative arrows were removed. Sidebar instructions no longer displace the controls. The export step explains the review gate, and manual navigation offers a return to the current step.

Implementation: `app.py`; regression coverage: `tests/test_app.py`. Local browser inspection covers the guide and target layout. Teammate review is still pending; this does not complete B11's pitch, video or event-format tasks. Refresh BASIN and restart the tutorial to review.

## Appearance checkpoint — 2026-09-06 (published in `83d593d`, review pending)

B11 usability: coordinated native Light/Dark/System themes; refreshed spacing, typography, metric cards and first-run invitation. Help & tutorial moved directly below navigation; Settings now holds Appearance. The theme choice is browser-local and does not modify scenarios. Package builder includes `basin_theme.py`. Workflow/tutorial/upload regression checks passed (22 tests); browser visual review and teammate acceptance remain distinct. No P0 scientific or presentation-validation tasks are closed by this visual update.

## Documentation reconciliation — 2026-09-06 (local)

Claim inventory for B11.1/B11.3 against `83d593d`, working tree clean and `origin/main` at the same commit. The board below now separates implemented-and-verified work, work awaiting human review, partial work, untouched work, and paths recorded as not selected. No application code, dependency, scientific claim or product scope changed in this pass.

A follow-up sweep on the same day added `docs/observation_sheet.md` (B09.3), corrected superseded checkpoint wording in `docs/build_validation.md`, fixed broken file references in `docs/presentation_plan.md` (`rainfall.csv` to `daily_rainfall.csv`, `fetch_snapshot.py` to `scripts/fetch_noaa.py`), and added a reconciliation notice at the top of that plan listing the capabilities it advertises that the build does not have. All relative links and backticked paths in `README.md`, `TODO.md`, `HANDOFF.md`, `docs/*.md` and `research/*.md` were checked; the only unresolved names are files that exist inside an exported packet or a built kit rather than in the repository.

Checks re-run during this pass (Windows 11, CPython 3.12.14, repository `.venv`):

- `python -m pytest -q --basetemp=tmp/pytest-doc-reconcile`: **97 passed** in 60.3 s.
- `python scripts/check_snapshot_checkout.py`: verified; a fresh clone reproduces snapshot SHA-256 `672c23f8…78a0` under the `eol=lf` attribute.
- `python scripts/demo_smoke.py`: verified, network-blocked rehearsal.
- `python scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified; run `5cf371d39eb2`, 5 accepted scenarios, 500 audit records replayed, `implementation_matches_current: true`.
- `python scripts/evaluate_selection.py`: 9 configurations (seeds 7/22/91 across three profiles), silhouettes 0.246–0.416, written to `output/selection-evaluation.json`.

Documentation changed in this pass (branch `docs/reconcile-status-2026-09-06`; no application code, dependency, scientific claim or product scope touched):

- `TODO.md`: at that 2026-09-06 checkpoint, board statuses B01, B02, B03, B04, B05, B06, B07, B08, B10 and B11 were updated and 61 subtask boxes were checked with qualifiers where a claim was partial. B08 Paths A and C were annotated as not selected; B08.2, B06.7, B07.1, B07.8, B09.1, B10.4, B11.6 and B11.9 were left unchecked with the reason recorded. The 2026-09-07 audit below supersedes that count and those current-status statements.
- `HANDOFF.md`: rewritten as the current checkpoint with today's verification separated from recorded history, files changed, five next actions, and blockers.
- `README.md`: browser network isolation no longer said to be described in `docs/build_validation.md`, which records no such run; now points at `scripts/browser_rehearsal.mjs`.
- `docs/build_validation.md`: new section recording the checks actually run today; two earlier sections no longer claim to be local and unpushed, and the superseded upload checkpoint says so.
- `docs/demo_runbook.md`: one line distinguishing the rendered simulation film from the missing B11.9 backup recording.
- `docs/presentation_plan.md`: dated reconciliation notice listing the removed stressor features, the excluded `BASIN.exe`, absent GIS overlays, the overstated WAM/sign-off claim and the format conflict; `rainfall.csv` corrected to `daily_rainfall.csv`, `fetch_snapshot.py` to `scripts/fetch_noaa.py`, and the untested WAM/HEC-ResSim interoperability claim marked. The pitch narrative itself is untouched and belongs to B11.4.
- `docs/observation_sheet.md`: new, closing B09.3.

These are automated internal-consistency and regression checks on one machine. They are not practitioner validation, teammate review, presentation-device verification or scientific approval, and they close none of those gates. Earlier figures in `docs/build_validation.md` remain recorded historical results from their own runs.

## Board audit checkpoint - 2026-09-07

Audited the checked items against the working source, `origin/main` at `f78d692`, current documentation and the supplied official competition PDFs. The current source passed **105 tests** in 91.23 seconds. Fresh-checkout snapshot verification reproduced SHA-256 `672c23f8...78a0`; the network-blocked demo smoke and independent bundle replay both passed with 5 scenarios and 500 audit records. These checks support the existing implementation/integrity boxes but do not establish practitioner approval, presentation-device readiness or user benefit.

Current root-board count after correction, branch reconciliation, B06.7 verification and presentation reconciliation: **65 checked and 46 unchecked subtasks**. The unchecked count includes Path A/C reservoir alternatives that are explicitly not selected; use the major-task status table and dependency notes to determine active work.

Corrections made by this audit:

- Stage 1 answers and the finalist tie-breaker response are no longer missing; they are recorded in `docs/submission_record.md`. The August 10 rules and resource packet confirm the September 22 event and judging categories, but do not state the finalist presentation length or detailed demonstration format.
- The native wrapper is no longer excluded. `BASIN.exe` is tracked at `origin/main` and matches the working copy; the current README and build scripts support it. Reproducible build-only dependencies and clean presentation-device execution are still open, so B10.2 is reopened.
- The earlier claim inventory and obsolete presentation plan were replaced by `docs/claim_inventory.md` and a current three-person, format-flexible `docs/presentation_plan.md`. Unsupported stressors, GIS overlays, engineering sign-off and verified direct-model-import claims are now explicit exclusions rather than scripted demonstration steps.
- The local `main` pointer was reconciled to `origin/main` at `f78d692` without discarding working changes. The superseded local commit remains recoverable at `codex/pre-reconcile-20260907`; unrelated logo-reference work and generated artifacts remain intact.
- The current default is a readable neutral light theme with a dark option and distinct colored charts. B13 no longer describes the application as having a completely black/white theme.
- The upload parser, README, and `.streamlit/config.toml` are aligned to a 10 MB CSV upload limit (`maxUploadSize = 10`).

## First parallel work session

- **All:** complete B01.1-B01.4 together and put actual names into the shared board.
- **A:** inventory source assumptions for B07 and draft B03's example record without changing persisted schemas.
- **B:** run B02 and record failures; investigate B04's existing replay checks.
- **C:** prepare B09's user exercise and B11's claim inventory; sketch B05/B06 without competing edits to `app.py`.
- **End of session:** agree on one small feature slice, one shared data contract, and the next integration checkpoint.

## Immediate work session - analyst utility and clarity

The 2026-09-07 teammate discussion agreed on the problem: the interface presents too much at once, labels need to be clearer, and the product's practical purpose and demonstration value need to be obvious. The next milestone is a first-time user selecting and justifying three rainfall scenarios and exporting a reviewable packet in under three minutes without verbal coaching or a misleading interpretation. This is a working target to validate in B09, not a completed usability claim or an official event time limit.

Complete this sequence before starting another speculative visualization or model input:

1. **Team decisions:** complete B01.1, B01.2, B01.5 and B01.7. Claim the UI/workflow, data/method review, and demo/release lanes.
2. **Unassisted baseline:** run B09's task once with the teammate least familiar with the current interface. Record time, assistance, misunderstood terms, unnecessary content and interpretation errors in `docs/observation_sheet.md`.
3. **Workflow refactor:** complete B13 around the four existing stages: Check data -> Build scenarios -> Review choices -> Share results.
4. **Practitioner validation:** have the TAMUCC professional review station suitability, scenario interpretation and the exported packet under B07/B09. Do not record professional approval without their actual feedback.
5. **Current demonstration:** complete B11.4 and rewrite the stale pitch around the implemented evidence-to-packet workflow. Treat the illustrative reservoir experiment as secondary.
6. **Presentation device:** complete B10.3-B10.5 and B10.8 on the different Windows presentation laptop, using its actual display resolution and the projector.
7. **Retest and freeze:** convert observations into owned fixes under B09.7, repeat the important tasks, then complete B12.

Suggested 90-minute library planning agenda:

- **15 minutes:** agree on the primary user, first decision, purpose statement, success measure and freeze target.
- **15 minutes:** watch an unassisted novice attempt the current workflow; do not teach during the attempt.
- **20 minutes:** identify every unclear label, unnecessary default chart/control and avoidable scroll in the guided path.
- **20 minutes:** sketch one main question and action for each of the four stages, including the decision summary card.
- **10 minutes:** explicitly retain, make secondary or defer proposed features.
- **10 minutes:** claim owners and independent reviewers, define the next integration checkpoint, and schedule the practitioner and presentation-device sessions.

## Part B upload-comparison checkpoint — 2026-09-06

Historical first slice: descriptive uploaded-versus-NOAA comparison began as preview only. Superseded by B14: saved evidence, versioned scenario links and consented packet replay are implemented. Seasonal baseline validation, independent real-sample review and custom-data-driven area simulations remain open. See docs/local_upload_and_research_plan.md for the implementation history.
