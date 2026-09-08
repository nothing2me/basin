# BASIN team TODO

Updated: 2026-09-07 | Planning baseline: `ebd8d59` on `main` | Status reconciled against `f78d692` on `origin/main`

This is the shared task board for BASIN. Subdivide work here using stable IDs rather than maintaining separate TODO documents per person. A GitHub issue or PR may discuss implementation, but link its ID here and keep this board's owner/status current. This plan proposes work; it does not claim team approval of new product scope or assign real people without their agreement.

## Active implementation — September 6

User authorized completing this board. Implementation owner: Codex on `codex/demo-ready`.
Intended independent reviewer: a TAMUCC professional identified by the user; name and review evidence pending.
User explicitly selected B08 Path B: retain an illustrative reservoir experiment. Paths A/C are not selected.
Primary workflow: rural-serving analyst prepares three reviewed rainfall scenarios, inspects evidence, records an unresolved assumption, and exports a packet for expert review.
Implement B02/B04 baseline first, B03/B05 evidence next, then B06 comparison. One implementer owns the shared schema and app integration.
Presentation device is a different Windows laptop. The actual Stage 1 submission, finalist tie-breaker Q&A, August 10 rules and resource packet are available; finalist-specific presentation length/format instructions, freeze and device verification remain pending.

## Product objective and scope

Proposed objective for team confirmation in B01: help rural-serving water analysts assemble traceable evidence, compare rainfall stress scenarios and assumptions, and prepare a reviewed packet for deeper drought-planning analysis.

The existing documented core is rainfall scenario generation, grouping, ranking, review, and export. Evidence-conflict workflows are proposed extensions. Reservoir impact prediction is a separate scope decision, because the current technical design excludes it even though the code contains a simulation. A numerical check, hash, or user acceptance does not establish hydrologic validity or professional certification.

## How to claim and finish work

1. Replace `Unclaimed` with one person's name and name a different reviewer. Suggested lanes below are not assignments.
2. Set status to `In progress` and add the branch/PR before editing. Keep one major task in progress per person; claim a ready subtask when a larger task is blocked.
3. Check dependencies. A team decision remains pending until explicitly recorded; elapsed time is not approval.
4. Before coding, fetch the canonical remote, inspect divergence and teammate changes, and read the existing implementation. Preserve unrelated local changes.
5. Agree on shared fields before changing them. In particular, B03 owns evidence fields, B04 owns audit/export schema changes, and B05 owns the first evidence UI integration in `app.py`.
6. Check a subtask only when its stated work is verified. Mark a major task `Done` only when its acceptance criteria pass and its reviewer has reviewed the result.
7. Update this board with verification/PR links and record blockers plus the next action in `HANDOFF.md`. Do not copy the entire board into the handoff.

Statuses: `Ready`, `In progress`, `Needs decision`, `Blocked`, `In review`, `Done`, `Deferred`. An unchecked box is outstanding work, not proof that the entire capability is absent.

Suggested three-person lanes:

- **A: Evidence and data.** Scientific definitions, evidence records, data checks; partner with C for practitioner feedback.
- **B: Core and verification.** Reproducibility, audit/export integrity, numerical correctness, packaging.
- **C: Analyst workflow and demo.** Interface, comparison, validation sessions, pitch and rehearsal.

Any teammate may claim another lane's work after coordinating. Existing team ownership takes precedence. Communication tasks below are for the team; this board does not authorize an agent to send outreach or submissions.

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

## Shared board

| ID | Task | Priority | Suggested lead | Owner / reviewer | Status | Dependencies |
|---|---|---|---|---|---|---|
| B01 | Confirm scope and claim work | P0 | All | Unclaimed / Unclaimed | In progress | None |
| B02 | Establish a reproducible working baseline | P0 | B | Codex / TAMUCC reviewer (name pending) | In review | None |
| B03 | Define evidence and assumption records | P1 | A | Unclaimed / Unclaimed | In review | B01 for new scope; inventory can start |
| B04 | Complete audit and export verification | P0 | B | Unclaimed / Unclaimed | In review | B02 for runtime verification; B03 for new fields |
| B05 | Build evidence inspection and conflict review | P1 | C | Unclaimed / Unclaimed | In review | B01, B03, B04 schema agreement |
| B06 | Add scenario comparison and explain selection | P1 | C | Unclaimed / Unclaimed | In review | B01, B02; coordinate app.py with B05 |
| B07 | Validate geography and scenario definitions | P0 | A | Unclaimed / Unclaimed | In progress | None for review; expert input for validation |
| B08 | Resolve reservoir simulation and engineering claims | P0 | B | Unclaimed / Unclaimed | In review | B01; source review can start |
| B09 | Demonstrate analyst usefulness | P0 | C | Unclaimed / Unclaimed | Ready | Plan now; run exercise after B02 and selected features |
| B10 | Prove packaging and offline operation | P0 | B | Unclaimed / Unclaimed | In progress | B02; final repeat after accepted changes |
| B11 | Reconcile docs and prepare the demonstration | P0 | C | Unclaimed / Unclaimed | In progress | Inventory now; finalize after B01/B09/B10 |
| B12 | Freeze and accept the demo build | P0 | All | Unclaimed / Unclaimed | Blocked | All P0 tasks and approved demo features |
| B13 | Streamline the analyst workflow | P0 | C | Unclaimed / Unclaimed | In review | B01 objective; validate through B09 and B10 |

Status meanings used after the 2026-09-06 reconciliation: `In review` means the described work is implemented and covered by automated checks but still needs the named human review in its acceptance criteria; `In progress` means part of the task is verified and part is untouched; a checked box records verified work, not approval. P0 means required to resolve before presenting the affected capability. P1 means valuable feature work after scope confirmation. Fixes within B04 can proceed without waiting for a new evidence schema; split the PRs accordingly.

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

## B01 - Confirm scope and claim work

Owner: Unclaimed | Reviewer: Unclaimed | Integration: this file and existing README/methodology

Status 2026-09-07: B01.3 (reservoir Path B) and B01.4 (evidence inspection first) are recorded in this board and visible in the implementation. B01.6 is now complete because the submitted Stage 1 answers, tie-breaker response and supplied August 10 organizer documents are available. B01.1, B01.2, B01.5, B01.7 and B01.8 still need recorded team decisions or later finalist instructions. The team is Mohammed Asad Khan, Noah Wilborn and Misha Stegall. Lanes and reviewers stay `Unclaimed` in the table until each person claims their own, and nobody may be entered as owner or reviewer by anyone else.

- [ ] **B01.1** Agree on primary user and first decision: for example, a rural-serving provider selecting three rainfall scenarios to request deeper analysis.
- [ ] **B01.2** Confirm or revise the product objective above. Distinguish observations, constructed stress scenarios, and modeled impacts.
- [x] **B01.3** Choose the reservoir path: exclude from the demo, retain an explicitly illustrative experiment, or approve a validated impact-modeling expansion. Record the rationale and owner under B08.
- [x] **B01.4** Choose the first feature: evidence inspection/conflict review (recommended), scenario comparison, or another explicitly described slice. Do not start every P1 task at once.
- [ ] **B01.5** Fill owner/reviewer names in the board. Agree on `app.py` integration order and ownership of persisted fields.
- [x] **B01.6** Locate the actual submitted Stage 1 answers, finalist tie-breaker response, August 10 official rules and resource packet. `docs/submission_record.md` preserves the submitted wording; the supplied PDFs provide event/judging context.
- [ ] **B01.7** Confirm the team's freeze target. The supplied build plan proposes September 17-18 bug-fix/rehearsal time and September 19-20 buffer before September 21 travel. These are planning targets, not newly verified organizer deadlines.
- [ ] **B01.8** Obtain and record any finalist-specific instructions issued after the supplied materials, especially presentation length, required deck/demo format, A/V constraints, submission mechanism and travel/event logistics. Coordinate with B11.7.

Acceptance: one recorded scope decision, named owners/reviewers, agreed first feature, and a bounded demo workflow. Missing submission material stays explicitly unresolved.

## B02 - Establish a reproducible working baseline

Owner: Unclaimed | Reviewer: Unclaimed | Files: requirements.txt, tests/, data/, launch/setup scripts, CI

Status 2026-09-07: current working source passed 105 tests, snapshot checkout, offline smoke and bundle replay. Line-ending stability is owned by `.gitattributes` plus `scripts/check_snapshot_checkout.py`; failure behaviour is covered by `tests/test_failures.py`; `.github/workflows/tests.yml` repeats the fresh-checkout path. Clean-environment wheel installation remains the recorded 2026-09-06 result rather than a new run. Local `main` now equals `origin/main` at `f78d692`; the prior equivalent branding commit is preserved at `codex/pre-reconcile-20260907`, and unrelated working changes/artifacts remain intact. A named reviewer and presentation-device check remain open.

- [x] **B02.1** Record commit, Python version, OS, clean/dirty state, and exact install commands in existing build-validation documentation. Refresh this record at the freeze (B12.5).
- [x] **B02.2** Create an isolated Python 3.12 environment and install pinned requirements; record actual installation failures rather than silently substituting versions. Recorded historical result; not re-run in the 2026-09-06 reconciliation.
- [x] **B02.3** Run `python -m pytest -q` from that environment and classify failures by owning module.
- [x] **B02.4** Run `python scripts/demo_smoke.py` and `python scripts/replay_bundle.py output/BASIN-rehearsal.zip`; record current results separately from prior build claims.
- [x] **B02.5** Make observation bytes stable on a fresh Windows checkout. The present clone needed a local line-ending correction; implement a repository-owned solution, such as a narrowly scoped Git attribute, and prove the manifest hash survives a new checkout. Never change the manifest merely to accept corrupted data.
- [x] **B02.6** Exercise malformed snapshot, failed save, invalid replacement, and unavailable session behavior; ensure useful errors and no false success messages.
- [x] **B02.7** Turn reproducible failures into assigned subtasks/PRs. Verify the fresh-clone path in CI where practical.
- [x] **B02.8** Reconciled local `main` to `origin/main` at `f78d692` with a mixed reset after confirming the local/remote branding trees matched. Preserved the old commit at `codex/pre-reconcile-20260907`; unrelated logo-reference work and generated artifacts remain in place. The already completed 105-test run exercised the same working source, and post-reset source diffs are limited to documentation and the preserved media work.

Acceptance: installation and baseline checks pass on a clean environment, original CSV checksum matches, and any remaining failures have an explicit disposition before the demo.

## B03 - Define evidence and assumption records

Owner: Unclaimed | Reviewer: Unclaimed | Files: basin_core/data.py, engine.py, workspace.py; coordinate exporter.py with B04

Status 2026-09-06: implemented as schema 2.0 in `basin_core/evidence.py` with persistence in `basin_core/workspace.py`; five seeded records cover the snapshot, station suitability, construction, reference and ranking assumptions. Conflicts link two records with disagreement, comparability, status and disposition. Save/load, privacy and 1.0 migration are covered by `tests/test_integrity.py`. Field agreement with B04/B05 happened inside one implementer's work rather than as a recorded cross-lane agreement.

Proposed extension: start with a small concrete record attached to the existing workflow. Do not introduce a generic evidence platform or a database migration without need.

- [x] **B03.1** Inventory current manifest/provenance fields and reuse them. Identify what is missing for station suitability, reference definitions, ranking presets, and externally sourced claims.
- [x] **B03.2** Agree with B04/B05 on minimal fields: stable ID, title, publisher/source locator, source date/version, retrieval date where applicable, geographic scope, quantity/unit where applicable, and relevant excerpt or description.
- [x] **B03.3** Represent observations, derived calculations, user assumptions, and policy statements distinctly. Record applicability/review status without inventing a numerical trust score.
- [x] **B03.4** Separate public citation metadata from private annotations. Define export inclusion rules for each field.
- [x] **B03.5** Create example records using the existing NOAA snapshot and documented provisional station assumptions. Do not fabricate expert approval or claim airport-to-catchment validation.
- [x] **B03.6** Define a conflict record linking two evidence IDs, the precise disagreement, comparability issues, and a resolution or explicit unresolved status. Preserve both originals.
- [x] **B03.7** Agree on saved-session/export version behavior and handling of old sessions before implementation; pass one example payload to B04 and B05.
- [x] **B03.8** Test invalid links, required fields, unsupported versions, and privacy defaults through the real save/load boundary.

Acceptance: one scenario's important assumptions can be traced to records that survive save/load. Two disagreeing claims remain distinguishable and unresolved until a human records a disposition.

## B04 - Complete audit and export verification

Owner: Unclaimed | Reviewer: Unclaimed | Files: basin_core/workspace.py, exporter.py, scripts/replay_bundle.py, tests/test_pipeline.py

Status 2026-09-06: `basin_core/exporter.py` declares CHECKS/EXCLUDED, recomputes features, scores, components and summaries, and checks accepted IDs, dates, station order, units, revisions, brief and privacy; `docs/verification_scope.md` states the contract. Negative rehash tests are in `tests/test_integrity.py`. B04.6 shows normalized contributions with the raw weight labelled. B04.10 needs a human reviewer and is untouched.

- [x] **B04.1** Inventory every exported claim and specify whether it is recomputed, integrity-checked only, manually reviewed, or outside verification. Make the verifier's success message match that scope.
- [x] **B04.2** Check accepted IDs against the selected list and audit records, reject missing/duplicate records, and verify current approval revision and rainfall digest independently during replay.
- [x] **B04.3** Validate exact dates, station identities/order, units, transformation sequence, and source snapshot identity during replay; array equality alone is insufficient for semantic agreement.
- [x] **B04.4** Recompute score components and summary values. Either verify grouping/selection claims with sufficient replay inputs and software identification or explicitly exclude them from the verification claim.
- [x] **B04.5** Record explicit ranking-weight changes with before/after values. Preserve the distinction between re-ranking and explicitly rebuilding the shortlist.
- [x] **B04.6** Correct raw weights displayed as percentages in the generated brief: use normalized contributions or label raw values as weights.
- [x] **B04.7** Identify the actual implementation version in export metadata; define compatibility for old bundles rather than assuming every run labeled 0.1.0 uses identical code.
- [x] **B04.8** After B03 agreement, include evidence references, assumptions, unresolved conflicts and permitted notes in the packet. Keep public rationale separate from private free text.
- [x] **B04.9** Add meaningful negative tests for mismatched summaries/dates/approvals and missing audit entries. Recompute file hashes in some fixtures to prove semantic checks do more than reject stale hashes. Do not describe unsigned bundles as protection from coordinated tampering.
- [ ] **B04.10** Outstanding; needs a named human. Have the reviewer independently replay a packet containing an edit, replacement, rejection and changed weights; manually inspect its readable brief.

Acceptance: verification rejects internally inconsistent packets within its declared scope; current approved revisions and audit history survive export; private annotations stay excluded by default.

## B05 - Build evidence inspection and conflict review

Owner: Unclaimed | Reviewer: Unclaimed | Files: app.py; consume B03 fields and B04 persistence/export

Status 2026-09-06: `basin_ui.evidence_panel` provides metric tracing, side-by-side records, conflict capture and dispositions inside Review then Reference & provenance; the Exports page lists packet contents, warns about unresolved disagreements and keeps private notes opt-in. `tests/test_failures.py::test_evidence_conflict_ui_workflow` walks record, save, restore, accept, export and verify. Whether an intended user can do this unaided belongs to B09 and is not established here.

- [x] **B05.1** Extend the existing Reference & provenance area with an evidence table; do not create a second source registry in UI state.
- [x] **B05.2** Make a selected metric/assumption lead to its source, period, units, geographic scope and applicability status.
- [x] **B05.3** Add side-by-side inspection of two evidence records. Show differences in date, definition, geography and units before calling values contradictory.
- [x] **B05.4** Allow a human to record why a source was used or why a disagreement remains unresolved. Do not automatically pick the newer number as true.
- [x] **B05.5** Display observation, construction, assumption and expert-review status in plain language. Do not conflate the existing Accept button with licensed engineering sign-off.
- [x] **B05.6** Show what will be included in export, including an unresolved-issues section and explicit private-note controls.
- [x] **B05.7** Test the path: inspect source -> record disagreement -> save -> restore -> export -> verify that both claims and privacy choices persist.

Acceptance: an intended user can explain the provenance and an unresolved limitation of a selected scenario without reading raw JSON. One end-to-end record is preferable to broad unfinished ingestion controls.

## B06 - Add scenario comparison and explain selection

Owner: Unclaimed | Reviewer: Unclaimed | Files: app.py, basin_core/analysis.py; audit changes through B04

Status 2026-09-07: `basin_ui.comparison_panel` compares two or three candidates with dates, features, contributions, revision, status and selection reason, and previews alternative weights on the same pool without regenerating. `tests/test_integrity.py` now covers preservation of the reviewed pool, deterministic stable-ID ordering for an exact score tie, and a case where increasing a shared duration weight does not improve the lower-ranked scenario. Saved comparisons are recorded and hash-checked only, per `docs/verification_scope.md`.

- [x] **B06.1** Provide side-by-side comparison of two or three existing candidates with source dates, duration, deficit, concurrence, reference sample size, score contributions, revision and status.
- [x] **B06.2** Explain selection with deterministic text: group representative, global fill, or manual choice. Include the relevant weights and review limitations.
- [x] **B06.3** Label profile names as descriptions; replace unsupported catchment/multi-basin language when the data only represents stations. Handle the single-station case explicitly.
- [x] **B06.4** If accepted for this sprint, compare two weight configurations on the exact same candidate pool. Show changed positions and shortlist membership; do not regenerate silently.
- [x] **B06.5** Preserve the user's reviewed shortlist until they explicitly apply/rebuild it. Distinguish approval of rainfall content from endorsement of a later ranking configuration.
- [x] **B06.6** Save comparison settings/results through the agreed audit path if they are exported. Do not leave an exportable claim only in Streamlit widget state.
- [x] **B06.7** Added explicit regression cases for deterministic stable-ID ordering under an exact score tie and for increasing a nondiscriminating duration weight without improving the lower-ranked candidate. The full integrity module passes 29 tests.

Acceptance: a user can explain why two candidates rank differently and what changed after adjusting priorities. B06.4-B06.6 may be explicitly deferred if comparison alone fills the chosen demo slice.

## B07 - Validate geography and scenario definitions

Owner: Unclaimed | Reviewer: Unclaimed | Files: data/manifest.json, basin_core/engine.py, analysis.py, docs/methodology.md, docs/validation_notes.md

Status 2026-09-06: `docs/methodology.md` now matches the code on sampling, climatology, concurrence denominator, retention semantics, the matched rainfall reference and the 30-365-day limitation, and presets are labelled illustrative. `scripts/evaluate_selection.py` covers seeds 7/22/91 across three profiles. B07.1 and B07.8 need practitioner input that has not occurred; items 1 and 2 of `docs/validation_notes.md` remain open.

- [ ] **B07.1** Documented in `docs/methodology.md` and labelled provisional throughout the app; the practitioner feedback half is untouched. Obtain practitioner feedback on catchment suitability; keep proxies labeled provisional until reviewed.
- [x] **B07.2** Confirm the current quality policy against NOAA documentation and tests, including missing data, trace values and rejected quality flags. Preserve complete simultaneous windows.
- [x] **B07.3** Resolve design/code differences explicitly: whole-window sampling versus multi-block bootstrap; monthly climatology versus daily means; eligible rolling-window denominator; retention fraction versus deficit scaling.
- [x] **B07.4** Retain a comparable rainfall reference with stated stations, onset, duration, years, units and sample size. Do not silently replace it with a hydrologic drought-of-record number.
- [x] **B07.5** Establish the limits of short 30-365-day scenarios relative to multi-year drought questions. Record the unmet use case instead of simply extending the duration limit.
- [x] **B07.6** Identify illustrative ranking presets and summer priorities. Record whether any actual provider informed them; remove unsupported endorsement language.
- [x] **B07.7** Evaluate cluster/shortlist behavior across several predefined seeds and parameter settings, using the existing score-only/random comparisons. Report tradeoffs rather than asserting universal superiority.
- [ ] **B07.8** No expert feedback has been received, so nothing is recorded. Record expert feedback, actual methodology changes, and remaining uncertainty in existing validation notes; keep technical numerical tests separate from scientific validation.

Acceptance: methodology agrees with code, material assumptions are explicit, and validation claims have attributable evidence. If expert input is unavailable, present an unvalidated prototype with the limitation clearly recorded.

## B08 - Resolve reservoir simulation and engineering claims

Owner: Unclaimed | Reviewer: Unclaimed | Files: basin_core/analysis.py, exporter.py, app.py, tests/, methodology/runbook

Status 2026-09-07: Path B is the selected path. Paths A and C are recorded as not selected and their subtasks stay unchecked deliberately. The two-pool experiment tracks inflow, evaporation, served demand, unmet demand and spill; `tests/test_reservoir.py` asserts daily conservation across wet, dry, empty and full states plus invalid settings and rainfall. Assumptions are surfaced through `RESERVOIR_ASSUMPTIONS`, and the experiment is excluded from packets and every verification claim. `docs/presentation_plan.md` now keeps it out of the compact route and answers reservoir questions with the illustrative boundary. B08.B5 still needs a human reviewer.

- [x] **B08.1** Audit all reservoir, restriction-stage, WAM, streamflow-translation and engineering-sign-off statements against their sources and B01's scope decision.
- [ ] **B08.2** Corrected in code and text (`0be1933`; the rainfall-method evidence record and the handoff brief both state that retention is not streamflow scaling), but the domain review half has not happened. Remove or correct unsupported instructions that rainfall retention can directly scale naturalized streamflow. Distinguish modeling applications and approval requirements; obtain domain review for engineering guidance.
- [x] **B08.3** Reconciled UI, tutorial, export, README and `docs/presentation_plan.md` around selected Path B. The compact demo excludes the reservoir view; optional/Q&A wording identifies it as uncalibrated, illustrative and outside packet verification.

Path A - not selected (2026-09-06). These subtasks stay unchecked because the path was not taken, not because work is outstanding:

- [ ] **B08.A1** Remove access and associated claims from the demo workflow, with explicit team agreement on whether source code is retained or removed.
- [ ] **B08.A2** Verify the remaining rainfall workflow, tutorial and exports are coherent without reservoir output.

Path B - retain as an illustrative experiment:

- [x] **B08.B1** Correct mass balance, including surplus inflow, depleted storage, capacity limits and explicit spill/unmet-demand accounting as appropriate to the chosen model.
- [x] **B08.B2** Prove conservation with deterministic wet/dry/empty/full examples and invalid-input tests; current nonnegative-storage tests are insufficient.
- [x] **B08.B3** Surface every material assumption, define thresholds and scope, and make clear that simulated threshold timing is conditional, not a forecast or official restriction date.
- [x] **B08.B4** Persist/version simulation settings and results and integrate review/export verification, or explicitly exclude the experiment from the evidence packet and its verification claim.
- [ ] **B08.B5** Outstanding; needs a named human. Obtain reviewer agreement that the presentation does not imply calibrated system performance.

Path C - not selected (2026-09-06). These subtasks stay unchecked because the path was not taken:

- [ ] **B08.C1** First define required inflow, storage, demand, evaporation, transfers, operating rules, time horizon, calibration observations and validation criteria with a domain expert.
- [ ] **B08.C2** Estimate scope and separate acceptance criteria. Do not treat this path as complete through new sliders or a repaired toy model; defer if evidence/time is insufficient.

Acceptance: the selected path is recorded; alternatives are marked not selected rather than left ambiguously unfinished; no presented output overstates the demonstrated model.

## B09 - Demonstrate analyst usefulness

Owner: Unclaimed | Reviewer: Unclaimed | Files: docs/validation_notes.md and existing demo materials

Status 2026-09-06: the task definition (item 3 of `docs/validation_notes.md`) and the observation sheet (`docs/observation_sheet.md`) now exist. No session, participant or recipient test has happened, and none may be arranged on the team's behalf.

- [x] **B09.1** The consented discovery evidence is summarized anonymously in `docs/validation_notes.md`, and the submitted Stage 1 commitments and finalist Q&A are recorded in `docs/submission_record.md`. Raw responses and contact details remain outside the repository and release kit.
- [x] **B09.2** Define a short task: choose three scenarios, explain choices, challenge one assumption, and send a packet to a hydrologist for deeper analysis.
- [x] **B09.3** `docs/observation_sheet.md` covers consent and anonymity, timing, assistance log, misread terms, rejected assumptions, missing evidence, the four explain-back questions, recipient handoff and close-out. It has not been used in a session. Prepare a consistent observation sheet: completion time, assistance needed, misunderstood terms, rejected assumptions, missing evidence, and ability to explain the result.
- [ ] **B09.4** Have a team member arrange an appropriate session with an intended user and recipient. Contact suggestions in supplied documents are leads, not confirmed participants.
- [ ] **B09.5** Compare with the user's current preparation method where feasible; record participant count and order/learning limitations. Do not claim measured time savings without a baseline.
- [ ] **B09.6** Ask the recipient to open and interpret the CSV/brief independently. Record specific format changes needed for their workflow.
- [ ] **B09.7** Convert observed problems into owned tasks, prioritize them over speculative additions, and retest the important fixes.
- [ ] **B09.8** Run the current task once with the teammate least familiar with BASIN before the workflow refactor. Capture the unassisted baseline and distinguish novice feedback from practitioner validation.
- [ ] **B09.9** Ask the TAMUCC professional to review station/catchment assumptions, scenario interpretation, the unresolved-assumption step and the exported packet. Record what they actually reviewed, requested changes and remaining uncertainty.
- [ ] **B09.10** After B13, repeat the same task without coaching. Record whether the participant can finish within the team's three-minute target and explain what BASIN produced, what it did not establish, and what the recipient should do next.

Acceptance: report distinguishes discovery from actual product use, demonstrates what the participant could do, and states limitations. If no external session occurs, label internal rehearsal honestly.

## B10 - Prove packaging and offline operation

Owner: Unclaimed | Reviewer: Unclaimed | Files: scripts/, setup/start scripts, requirements.txt, CI, docs/build_validation.md

Status 2026-09-07: the browser launcher remains the fallback path and the rebuilt native `BASIN.exe` is also supported. The tracked executable matches `origin/main`; `scripts/build_exe.py` and `scripts/launcher.py` describe the native build/launch path. PyInstaller and pywebview build versions are not pinned in `requirements.txt`, and no clean native rebuild or actual presentation-device run is recorded. Python-level offline rehearsal, wheel-only app installation and source-package content checks remain recorded. Browser/native network isolation, projector, launcher recovery and final-device footprint checks are open.

- [x] **B10.1** Record the supported Windows paths: rebuilt `BASIN.exe` for the native WebView2 window and `Start BASIN.cmd`/browser as the fallback. Both require the Python 3.12 application environment; the native path also requires WebView2.
- [x] **B10.2** Recorded exact PyInstaller (6.21.0), pyinstaller-hooks-contrib (2026.6), and pywebview (6.2.1) versions in `requirements-build.txt` for reproducible compilation of `BASIN.exe` via `scripts/build_exe.py`. Branded windowed executable matches `origin/main`; final presentation laptop execution check remains with B10.3.
- [ ] **B10.3** Test the clean installation package on the actual laptop; verify optional offline wheels match the supported Python/OS.
- [ ] **B10.4** Python-socket-level isolation is covered by `scripts/demo_smoke.py`; `scripts/browser_rehearsal.mjs` exists for the browser level but no run is recorded. Test with network disabled in the actual browser/native UI, including maps. Python socket-mocked tests do not cover browser requests for geographic assets.
- [ ] **B10.5** Exercise save/restore, downloads, snapshot mismatch, missing prerequisites and occupied-port handling through the supported launcher.
- [x] **B10.6** Recorded in `docs/build_validation.md` for the 2026-09-06 source package; repeat against the frozen kit under B12.5. Inspect package contents for private notes, sessions, credentials, source correspondence and generated artifacts. The currently tracked empty Streamlit onboarding file is not a secret, but packaging must not blindly include future credential contents.
- [x] **B10.7** Labels and limits are stated in `docs/methodology.md` (completion-time resident memory, no peak claim, illustrative 15-65 W energy range, unquantified water impact, network counters explicitly not instrumented). Re-measure on the presentation device with B10.3. Record wall/CPU time and memory with accurate labels; distinguish measured values, illustrative energy estimates, and unquantified water impact. Do not describe hardcoded network counters as instrumentation.
- [ ] **B10.8** Keep a versioned release copy and backup on the team's chosen media; test projector readability, the guided path at the presentation laptop's actual resolution, and download locations. Do not claim tablet/LAN support for the loopback-only configuration.

Acceptance: another teammate can install/start the supported build and complete the chosen demo workflow offline on the presentation machine, with accurate prerequisite and footprint claims.

## B11 - Reconcile docs and prepare the demonstration

Owner: Unclaimed | Reviewer: Unclaimed | Files: README.md, docs/methodology.md, validation_notes.md, build_validation.md, demo_runbook.md, ai_use_log.md

Status 2026-09-07: `docs/claim_inventory.md` now covers the current app, submission record, upload comparison, packet/brief, native executable, privacy, reservoir and competition claims with evidence boundaries. `docs/presentation_plan.md` is rewritten for the actual three-person roster and implemented evidence-to-packet workflow, with a compact three-minute team target plus optional expansion modules. Removed stressors, absent GIS overlays, direct WAM/HEC import, engineering sign-off and calibrated reservoir claims are excluded. The August 10 organizer PDFs confirm judging criteria and the September 22 event, but not presentation length or detailed format; B11.7-B11.9 remain open.

- [x] **B11.1** `docs/claim_inventory.md` inventories claims across README, tutorial/workflow, generated brief and verification scope, methodology, `docs/submission_record.md`, upload comparison, executable/deployment documentation, privacy, reservoir experiment and pitch. Each claim is classified as implemented, internally verified, locally observed, pending human review or excluded.
- [x] **B11.2** Record the accepted design corrections in existing methodology. Do not reintroduce outdated draft formulas merely to match the attached document.
- [x] **B11.3** Update installation instructions and reported tests to the verified release; remove the fresh-checkout claim that an environment is already installed.
- [x] **B11.4** Rewrote `docs/presentation_plan.md` around rainfall evidence -> transparent scenario shortlist -> selection explanation -> challenged assumption -> reviewable hydrologist packet. The judging-criteria map separates demonstrated evidence from proposed benefits, and the illustrative reservoir experiment is excluded from the compact route.
- [x] **B11.5** A walk-through exists in `docs/demo_runbook.md`; its length depends on the unresolved B11.7 format question. Prepare a concise walk-through: source/assumption -> scenario comparison -> human challenge/edit -> approved packet -> recipient's next action.
- [ ] **B11.6** `docs/ai_use_log.md` and `docs/third_party_materials.md` exist; no team review of them is recorded. Review AI-use disclosure and third-party attribution; record actual team review rather than claiming approval from the existence of an AI log.
- [ ] **B11.7** Verify presentation length, submission format and event logistics against the latest organizer communication. Do not treat the repo's three-minute demo suggestion as an official limit.
- [ ] **B11.8** Rehearse questions on proxy stations, reference periods, probabilities, model limitations, privacy and why clustering adds value. Every teammate explains the complete workflow.
- [ ] **B11.9** `media/BASIN_Simulation_Demonstration.mp4` is a rendered simulation film and is not this recording. Record the backup video from the exact accepted demo release and prepare final pitch materials after the workflow is stable.

Acceptance: all visible claims agree with implementation and evidence; a timed rehearsal and backup exist; deferred features are clearly described as deferred.

## B12 - Freeze and accept the demo build

Owner: Unclaimed | Reviewer: All teammates | Files: release documentation and handoff

Status 2026-09-06: unchanged and still blocked. No freeze, acceptance, commit, push or submission is authorized by this board.

- [ ] **B12.1** Resolve every P0 item and explicitly accept/defer each P1 item. Do not mark an excluded feature implemented.
- [ ] **B12.2** Review all team changes and run the established pytest, offline rehearsal and replay checks on the final source revision.
- [ ] **B12.3** Complete B10's actual-device offline check and B11's timed rehearsal; repeat affected checks after any release change.
- [ ] **B12.4** Inspect one final exported packet manually: chosen revisions, assumptions, references, privacy, readable summary and replay result.
- [ ] **B12.5** Record release commit, exact package identity/checksum, verified commands, known limitations, and recovery instructions in existing release documentation.
- [ ] **B12.6** Confirm teammates can recover from a failed demo using saved input, a working release copy and the backup video.
- [ ] **B12.7** Update HANDOFF.md with final state, remaining blocker if any, and next action. Commit/push/submission require the team's applicable authorization; this task list alone grants none.

Acceptance: the team agrees the frozen build is demonstrable as delivered, with no unsupported readiness, forecast or validation claim.

## B13 - Streamline the analyst workflow

Owner: Unclaimed | Reviewer: Unclaimed | Files: `app.py`, `basin_ui/`, tutorial and relevant UI tests

Status 2026-09-07: in review. The four-stage plain language workflow (1. Check data -> 2. Build scenarios -> 3. Review choices -> 4. Share results) is implemented in `app.py` and covered by 110 automated tests (`tests/test_app.py`, `tests/test_failures.py`). Compact decision summary card surfaces lead scenario ID, selection reason, evidence count, material limitations, and next action. Specialist labels replaced with plain language throughout. Compact viewport layout with expanders for secondary details and diagnostics. Coordinated accessible light/dark themes in `basin_theme.py`. B13.9 remains open pending unassisted novice and practitioner observation sessions under B09.

- [x] **B13.1** Use the existing persistent navigation and order the user-facing stages as **1. Check data**, **2. Build scenarios**, **3. Review choices**, and **4. Share results**. Keep navigation visible; do not introduce a hamburger menu.
- [x] **B13.2** Give each stage one clear question and one primary action. Limit the initial view to the information needed for that decision; move audit detail, large tables, score decomposition and diagnostics into clearly named detail sections.
- [x] **B13.3** Add a compact decision summary showing the selected scenario, why it ranked, evidence used, material limitation or unresolved assumption, and the next recipient action.
- [x] **B13.4** Replace or explain specialist labels. At minimum review: **Rainfall retained %** -> **Scenario rainfall (% of observed)**, **Candidates** -> **Scenarios to test**, **Shortlist** -> **Scenarios to review**, **Concurrence** -> **Stations stressed at the same time**, **Historical percentile** -> **How unusual compared with history**, and **Score contributions** -> **Why this scenario ranked here**. Verify each replacement remains scientifically accurate in context.
- [x] **B13.5** Make the guided demo fit one viewport per stage at the actual presentation resolution. Reduce avoidable whitespace and vertical stacking while allowing detailed evidence and tables to scroll when needed; do not claim zero scrolling across every device and workflow.
- [x] **B13.6** Keep controls, selector values, focus indicators, legends and chart series readable in both supported themes. Test selected/unselected, enabled/disabled and hover/focus states rather than checking only static screenshots.
- [x] **B13.7** Preserve the full traceability path through the simplified interface: source and applicability -> scenario construction/comparison -> human challenge/edit -> approval -> export and replay.
- [x] **B13.8** Add focused regression coverage for navigation, plain-language labels, decision summary contents and retained review/export behavior. Avoid screenshot-only assertions for usability claims.
- [ ] **B13.9** Review the result at the presentation resolution with a novice and practitioner under B09. Convert observed failures into owned follow-ups before marking this task done.

Acceptance: a first-time participant can identify the next action at each stage, select and justify three scenarios, state one limitation, and export the intended packet without verbal coaching. The guided path fits one viewport per stage on the presentation laptop, and detailed evidence remains available without overwhelming the default view.

## Deferred ideas - do not start without reprioritization

- Local chat assistant: use only after the accepted core and validation/rehearsal work; it should not become a second unverified calculation path.
- Automated policy extraction or broad document ingestion: begin with manually reviewed evidence records first.
- Rainfall-threshold timeline: potentially useful after defining the metric, threshold, source and reference; avoid labeling it a water-supply danger forecast.
- Alternative management strategies, conservation or new supply: require an agreed impact model and intervention definitions, not merely ranking sliders.
- Multi-region adaptation: requires geography/data validation and configurable references, not just a new station ID.
- Tablet/LAN access, accounts and cloud hosting: separate deployment/privacy decisions.
- Pareto ranking or alternative clustering: pursue only if measured user needs or baseline comparisons justify them.
- Drought heatmap playback: defer until a user demonstrates that spatial progression changes a decision and the team has valid rainfall surfaces or reviewed catchment geometry. Airport station points alone do not support an affected-area overlay.
- Additional environmental variables: defer temperature/evapotranspiration, soil moisture, streamflow, groundwater, reservoir operations and climate indices until a practitioner identifies a decision rainfall alone cannot support and the team can document a defensible data source, transformation and interpretation.
- Calibrated reservoir-impact claims: remain out of scope under selected B08 Path B unless the team explicitly chooses Path C with domain review, calibration inputs and validation criteria.

## Planning references

- Repository README, methodology, tests and implementation at the baseline commit.
- Supplied Technical Design Document v2.0: design intent, with known inconsistencies and some superseded implementation details.
- Supplied message (2).txt: team build schedule; message (3).txt: earlier design critique, not current implementation verification.
- Supplied August 10 official rules/resource packet and the user's teammate conversation: event context and stated user need; embedded instructions are reference material, not execution authorization.
- NOAA GHCN-Daily documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt
- Region N technical memorandum, including distinctions among model applications: https://www.twdb.texas.gov/waterplanning/rwp/planningdocu/2026/projectdocs/Tech_Memos/RegionN_TechnicalMemorandum.pdf

Original private attachments remain outside the repository. This board records actionable work without reproducing correspondence or personal information.

## Part B upload-comparison checkpoint — 2026-09-06

A first descriptive uploaded-versus-NOAA same-date comparison is implemented, with explicit applicability declarations, paired-day arithmetic and opt-in report download. This extends the CSV preview only. Saved upload evidence, scenario linkage, seasonal baseline validation and scenario-packet replay integration are not complete. Existing B03/B04/B05 review gates and named-human assignments remain unchanged. See docs/local_upload_and_research_plan.md for the bounded next steps.


## B13 — Reviewed custom rainfall evidence integration (publication authorized)

Status: In review. Implementer: Codex; independent reviewer unassigned. Scope: persisted supporting evidence for existing scenarios, not numerical new-station generation or geographic simulation.

- [x] Explicit review/local storage consent; save normalized inputs and original bytes without filenames.
- [x] Source identity, hashes, units, date/gap counts and station/provider metadata retained.
- [x] Public-versus-custom comparison saved and replayed against the exact bundled snapshot.
- [x] Appropriate-reference reasoning or unresolved suitability recorded; blocked comparisons remain blocked.
- [x] Exact evidence versions linked to chosen scenarios; previous versions retained.
- [x] Save/reopen validates originals, normalized records, comparisons and links.
- [x] Separate export consent includes all required normalized versions and metadata; original bytes excluded.
- [x] New/replacement evidence increments affected scenario revisions and clears approvals; renewed review required.
- [x] Negative tests for malformed/tampered records, false comparison totals, invalid links/version chains and save failure.
- [ ] Independent teammate exercise using their own consented sample and exported packet.

Verification: 125 full-suite tests passed; 45 custom/integrity checks passed after final verifier scope updates; final integrated UI test passed; independent CLI replay passed for a synthetic custom-data packet. Updated README, methodology, verification contract and upload plan explain schema 2.1 and backward compatibility. User authorized publication of this integration. Existing P0 practitioner and presentation-device gates remain open.
