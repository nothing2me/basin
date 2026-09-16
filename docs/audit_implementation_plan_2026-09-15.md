# BASIN audit implementation plan

This is the build plan to address the [independent audit](project_audit_2026-09-15_independent.md), whose current estimates are Impact 6, Feasibility 6, Community Centeredness 4, Innovation 6, and Clarity 4 out of 10. The official rules do not promise numerical weights or a 10/10 after any particular change. Tonight's video sets the **order and cutoff for work that must be stable before recording**; it does not replace the broader plan.

## Outcome to build toward

A rural-serving provider can select and assess relevant rainfall source records, set its own priorities, generate a defensible shortlist, review or reject each scenario, save and reopen work, then hand a hydrologist a self-contained packet that replays the exact inputs and decisions. BASIN presents this as **rainfall screening for the next modeling question**, with clear limits on supply, crops, fire, and environmental impact. A provider and recipient can complete the exchange without the creators coaching them.

## Assignment protocol for your coding agents

Give each agent one workstream below and an isolated branch/worktree. The present working tree has uncommitted changes in `app.py`, `basin_core/pdf_report.py`, `basin_core/visualizers.py`, and tests; the integration owner must identify a common starting snapshot and preserve that work. Agents may overlap logically but should not edit the same checkout. Merge in the dependency order below. Each agent returns: changed files, a concise before/after example, tests and manual evidence, known limits, and any claim that the UI/report should stop making.

### Agent 1 — local data, saved runs, and trustworthy packets

**Priority:** first; blocker for the advertised community-controlled workflow. **Files:** `basin_core/data.py`, `basin_core/workspace.py`, `basin_core/exporter.py`, `basin_core/integrity.py`, relevant `app.py` activation/exports integration, focused tests.

**Build:** make the activated local-gauge series a versioned, canonical source input. Save enough normalized records and source identity to reopen a run after process restart without re-upload. Export the exact same series, station registry, manifest, and source hashes that drove scenario generation. Replay a bundle in a clean process; fail on tampering. Keep bundled NOAA-only bundles compatible. Require explicit consent for portable gauge-derived data and do not silently include original raw uploads. Fix old disk PDF/ZIP buttons so they are tied to the current run fingerprint and privacy choices; label historic artifacts as historic instead of presenting them as current. Do not suppress the verifier or force the user's original gauge into an export to make it pass.

**Done when:** gauge activation → generated scenario → save → restart → reopen → export → verify/replay succeeds; values match at each step; altered data fails verification; a consent/decision/weight edit removes or regenerates current downloads; NOAA-only replay still works. This directly addresses the audit's three blockers and raises Feasibility and Community Centeredness.

### Agent 2 — truthful scenario selection and community priorities

**Priority:** first wave; parallel with Agent 1 in a separate worktree. **Files:** `app.py` workspace/builder views, `basin_core/engine.py` and ranking/shortlist code as needed, builder tests.

**Build:** split scenario generation into explicit modes: (a) **variations of one chosen source record** and (b) **historical-window search** that really samples multiple eligible windows. Show the number of distinct source windows, date ranges, seasons, duration, stations, missing-data exclusions, and generated variations beside the candidate count. The ordinary date picker must not imply a 1991–2025 search when it selects one interval. Put priority weights before the first shortlist; changing weights must deterministically rebuild or clearly rerank and log the change. Keep source suitability visible: airport gauge location, relationship to catchment, coverage and proxy warning. Limit candidate counts or use clear summary labels so clustering does not make many multipliers of one record look like many historical droughts.

**Done when:** a one-window run visibly says one unique source window; a multi-window run includes distinct eligible historical years and reports how many; changing a provider priority before generation changes the saved shortlist or an explicit documented ranking as expected; a replay produces the same shortlist. This raises Clarity, Community Centeredness, and Innovation.

### Agent 3 — scientific scope, labels, and review accountability

**Priority:** first wave for copy and report; deeper scientific models are later. **Files:** `app.py` review/export panels, `basin_core/agronomics.py` only if changing method, wildfire/storage display code, `basin_core/pdf_report.py`, related tests. Coordinate report-file conflicts with Agent 1/integrator.

**Build before video:** describe crop results as an illustrative fixed-ETo/Kc rainfall-versus-atmospheric-demand calculation. Remove “required to prevent yield reduction.” Describe KBDI as a screening index with fixed-temperature assumptions, replace “Burn-Ban Trigger,” and distinguish threshold crossing day from peak day. Put “uncalibrated, no restriction date” on storage trajectories and move modeled band timings behind the primary rainfall-review conclusion. Correct concurrence's denominator and remove the PDF placeholder and `n ≥ 5` “robust statistical significance” claim. Define empirical rank as comparison with matched rainfall windows, not event probability or drought-of-record severity. Rename “widespread stress” to selected-stations concurrence. Require a substantive batch rationale for “Accept all,” and mark batch inclusion separately from individual review. Lead the first PDF page with source suitability, scenario choice, decision rationale, and next modeling question; keep fixed 35%/15% storage examples clearly illustrative or remove them.

**Done when:** a nonexpert can read the first screen and first PDF page without mistaking BASIN for a farm irrigation order, county burn-ban source, calibrated reservoir forecast, or professional approval; all exported decisions have an attributable rationale and batch decisions are labeled. This is the fastest route to a much higher Clarity estimate.

### Agent 4 — laptop deployment and export performance

**Priority:** first wave if reports are slow on the recording laptop; finish before showing export. **Files:** `app.py` Export UI, `basin_core/pdf_report.py`, `scripts/start_browser.py`, setup/package scripts, rendering tests. Keep report work isolated from Agent 3 until merge.

**Build:** lazily generate preview/chart images only when requested or exported, cache by a complete report/input fingerprint, set a bounded renderer failure path, and preserve a readable PDF/text report path if a chart fails. Make the no-model local core the default path. Check Windows 3.12 install/setup and the frozen checkout on the actual laptop, with and without network if offline operation is claimed. Produce a small, repeatable setup and launch path; avoid the optional multi-gigabyte model as a hidden prerequisite. Ensure `scripts/package_demo.py` contains all required *tracked* files from the frozen build.

**Done when:** fresh example → review → Export screen → current PDF/ZIP completes at a measured acceptable time on target hardware; the files inspect and replay cleanly; a new operator can launch core without special agent assistance. This raises Feasibility and access equity.

### Agent 5 — actual provider-to-hydrologist handoff

**Priority:** starts now but cannot be completed by code alone; follow the stable core. **Files:** review/export UI, CSV schema/documentation, `docs/validation_notes.md`, handoff tests. The integration owner should assign a human research lead alongside this coding agent.

**Build:** a one-page task flow for a rural-serving provider: “Which rainfall sequences merit professional modeling, why, and what source information is uncertain?” Make weights, gauge choice, decision reasons and privacy choice visible in ordinary language. Add a concise recipient manifest and CSV field guide so a hydrologist can identify units, date windows, stations, retention, revisions and uncertainty without BASIN open. Record an uncoached provider exercise and an independent recipient import with task time, confusion points, rejected scenarios, and requested changes. Have the recipient judge station/catchment suitability and whether the packet answers a real modeling question. Revise the UI/schema from those observations. Do not claim direct WAM/HEC import until the correct target format is identified and tested.

**Done when:** one intended user completes the task without creator coaching and one hydrologist independently opens the handoff, traces one scenario back to its input, and states whether it is useful for the next model run. This is the essential evidence for a high Community Centeredness and Impact score; three discovery responses alone cannot supply it.

### Agent 6 — measured value, environmental accounting, and narrow innovation

**Priority:** after the core contract and practitioner task stabilize. **Files:** benchmarks/scripts, documentation/claim inventory, footprint UI and tests.

**Build:** compare the same scenario-selection/handoff task with and without BASIN: time, errors, number of defensible scenarios and whether the hydrologist can replay inputs. Measure core no-model runtime, report rendering, and optional-model runtime/energy separately on the target laptop with a stated measurement method. State that water/lifecycle cost remains unknown where it cannot be measured. Define BASIN's differentiator as a replayable, community-controlled decision trail plus recipient handoff, not KMeans alone or a replacement for TWDB/Texas ET/Forest Service portals. Build direct WAM/HEC linkage only if a recipient specifies the right import boundary and tests it. Update claims and demo materials with measured numbers, not guesses.

**Done when:** Impact and footprint claims have dated comparative evidence, while all unknowns remain explicit. This is the path toward 10/10 Impact and defensible Innovation.

## Dependency and delivery order

```text
Shared snapshot / integration owner
       ├── Agent 1: gauge + packet contract ──┐
       ├── Agent 2: builder + priorities ──────┤── Agent 3: claims/review/report ── Agent 4: frozen laptop build
       └── Agent 4: rendering/deployment ─────┘
                                            └── Agent 5: provider + hydrologist test ── Agent 6: measured impact
```

Agent 3 can draft copy independently, but its final report/UI changes should be merged after the data and builder semantics are known. Agent 4 may investigate rendering in parallel, then integrate with Agent 3's report patch serially. Agent 5 can schedule users and draft tasks now; the definitive test must use a stable build. Agent 6's comparison needs the same final task and recipient format.

## Tonight's cutoff: prioritization, not a new product definition

Before recording, target **Agent 1's source/packet blockers**, **Agent 2's truthful builder labels and priority behavior**, **Agent 3's scientific/decision copy**, and **Agent 4's export performance on the recording laptop**. Choose a code freeze with enough time to run the actual example, inspect the new PDF, replay the ZIP, and rehearse. If a larger change cannot pass by freeze, keep it out of the claims and recorded workflow; note it as unfinished rather than rewriting the whole implementation plan around the video.

The demo should explain the product's true role and show source → generated options → human rationale → verified handoff. Do not reuse exact B-009 values, `$50k/6 months`, `30–50x`, “verified hydrologist,” or operational Stage-3 timing from the stale `docs/demo_runbook.md` unless newly measured and source-supported. A passing NOAA path is useful evidence, but it does not erase a visible broken local-gauge promise; either complete/gate Agent 1's feature or disclose its current limit.

**Integrator's minimum verification:** targeted tests for changed contracts; bundled NOAA and activated-gauge save/reopen/export/replay; artifact invalidation after an edit/consent change; actual-laptop Export timing; visual inspection of every fresh PDF page; one clean-process ZIP replay; source/control claims read aloud. Then record the frozen commit and test results. Schedule the provider/recipient exercises and benchmark after the video; those remain necessary to substantiate a 10/10 estimate.
