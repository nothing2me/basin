# BASIN team TODO

September 8 planning supplement: [September 22 finalist excellence plan](docs/finalist_excellence_plan.md) defines the prioritized repair, validation, deployment and presentation gates arising from the mock-judge assessment. It assumes access to a hydrologist or technical faculty reviewer; rural-serving operator participation remains unconfirmed. The supplement is a plan, not a completion record. Keep task ownership and status on this board.

Updated: 2026-09-09 | Latest review: task 3 (`989dd7a` on `4d79822`) plus independent layout fixes. Earlier dated checkpoints are historical; consult the newest HANDOFF checkpoint for verification.

## September 8 team-context reconciliation

### September 9 task 3 independent review

Completed the task 3 layout/isolation scope, with review fixes for a single note spanning multiple pages, width measurement after symbol transliteration, wide WinAnsi punctuation, readable HTML table columns, and wrapped vector spectrum labels. B17.7 is complete. **B17.3 remains partial** because browser-renderer failure/degraded-output reporting is not finished; Unicode fonts are also not implemented. Task 4 is still needed: test and pin the optional Ollama Python client, verify its real loopback/proxy/redirect behavior using a controlled local fixture, and record a scoped dependency-advisory report. Do that on a separate branch from updated main; do not merge it without review. It does not establish daemon egress behavior.

Manual acceptance instructions: [Report and device checklist](docs/report_device_acceptance.md). Security/dependency/live-model and actual-device gates remain open. Final suite: **268 passed**; snapshot, smoke, explicit replay and source packaging passed. Visual-review scope is recorded in the newest HANDOFF checkpoint.

### September 9 task 2 independent review (historical)

B17.1/B17.2 now include additional review fixes: preview identity covers current workspace contents (including changed consented notes and weights), no-accepted-scenario previews are removed, changing workspaces clears prior report/configuration state, and Review settings survive navigation. A missing configured scenario or mismatched revision now makes the experiment unavailable until reconfigured instead of simulating another accepted scenario. Custom tier labels correctly show 50% retention as -50% rainfall; calculations are unchanged. The export success message distinguishes the verified ZIP from its separate unverified PDF.

B17.1/B17.2 completion is for current-session configuration and export wiring, not B16 saved/replayable simulations. The task 3 layout/isolation work is now completed as recorded above; renderer degradation handling and device checks remain open. SEC.4/SEC.5, B09 human validation, B10 installer/device/offline checks, B19 area modeling and B21 document ingestion remain open. B17.4's basic CLI consent flags were implemented under SEC.2; its broader cross-output/device checks still need completion. Independent review: **241 tests passed**, snapshot, offline Python smoke, explicit replay (implementation matches current) and source packaging passed. See the newest HANDOFF checkpoint for scope and evidence.

September 9 follow-up: B17.6 independently reviewed and accepted for integration with upstream `21f98db`. Original Claude branch: 191 passing tests; combined build plus short-window report regression: **192 passed**. Snapshot, Python offline smoke, explicit replay and source packaging passed. Fixed leftover six-month no-breach wording; adapted the security mock to exercise the optional Ollama route. PDF fixture isolation is already done, so task 3 should not redo it. **Superseded next step: B17.1/B17.2 are now complete in the task 2 review above.** Long-text/pagination, domain review, live model/network and native installer/device acceptance remain open. New upstream installer functionality is not certified by this report review.

### Combined-build verification after Noah's update

Merged Noah's `40a7023` into the security branch (merge `502824a`). **172 tests passed in 122.44 s**, including the 13 security tests and the previously failing PDF/UI export workflows. Fresh-checkout snapshot, Python offline smoke and independent replay passed; run `0d51fc36a996`, five scenarios, 500 audit records, implementation matches. No custom comparisons in that smoke packet. A generated two-page Windows PDF was rendered and visually inspected. Security client restrictions, HTML escaping, CLI consent and tracked-only packaging survived the merge.

The previous four test failures are resolved in this combined build. **B15.1's passing-suite gate is complete at this revision.** The report-content defects listed here on September 8 are corrected in B17.6 below (branch `fix/b17-report-content-accuracy`): the hard-coded 963,600 ac-ft total, the substituted example spectrum rows, the unconditional audit/PASS wording and the unsupported policy/benefit assertions. `tests/test_pdf_report.py` no longer depends on an existing local session; it builds an isolated workspace from the shared fixture. B17 still remains partial: settings propagation from `app.py` (B17.1), the consent preview (B17.2), CLI opt-ins (B17.4) and device checks (B17.5) are untouched by that work. Live Ollama/device checks remain open.

Security follow-up: [September 8 security review](docs/security_review_2026-09-08.md) records findings, fixes, tests and remaining gates. Application-level hardening is implemented; live Ollama/network validation and dependency advisory review remain open. Do not mark the entire application “secure” from these checks.

- [x] **SEC.1** Fix assistant client destination/proxy/redirect configuration, model-name filtering, tool argument validation and bounded calls/history; add mocked boundary and invalid-call tests.
- [x] **SEC.2** Make CLI notes/custom exports opt-in, escape model-name HTML, and prevent untracked files being swept into source packages; test consent propagation and package exclusion.
- [x] **SEC.3** Review existing loopback launcher configuration, bounded CSV input, packet inventory/size checks and private original storage; record limitations in the linked review.
- [ ] **SEC.4** Validate live Ollama and daemon egress on the presentation laptop. **Partially complete.** The dependency advisory review and the optional-stack pin are done (see SEC.6); observing the daemon's actual outbound traffic on the presentation machine is the remaining part and is not established by anything in SEC.6.
- [x] **SEC.6** Pin and test the optional assistant client, and run a dependency advisory review. `requirements.txt` moves from `ollama>=0.4.0` to `ollama==0.6.2` after testing 0.4.0/0.4.9/0.5.4/0.6.2 with `scripts/probe_ollama_client.py`; `requirements-assistant.txt` pins the transitive closure that actually implements the proxy/redirect/timeout behaviour. `tests/test_ollama_client.py` verifies against the real installed client that BASIN's options reach the transport, that a hostile `OLLAMA_HOST`/proxy environment does not move the endpoint, and that a local 307 fixture is not followed, all on loopback with no external calls and no model download. [Advisory review](docs/dependency_advisories_2026-09-09.md) records commands, date, scope, findings and limits; [setup doc](docs/ollama_setup.md) separates the Python package, the Ollama service and the model. Finding A-1: the `remote_host`/`remote_model` guards in `check_ollama()` cannot fire against the real client and are reported, not silently changed.
- [ ] **SEC.5** Complete actual-device browser/native/download/PDF checks, frozen-package privacy inspection and broader adversarial/session-input testing. Earlier B15 export test failures are resolved; these device/privacy acceptance checks remain open.

Message (7) is the latest supplied backlog. It starts at item 2; its closing recommendation mentions baseline/units/scenario-selection repairs without supplying item 1. B15 records that prerequisite from inspected code rather than inventing a missing attachment section. Message (6) is the earlier backlog; messages (4)/(5) are duplicate efficiency guidance, not feature requirements. The private Discord transcript is context, not evidence of tests or authorization to contact people, publish, deploy or book travel.

- Team-stated lanes: Mohammed volunteered for UI/UX and security; Misha stated a focus on information/data; Noah reported assistant, spectrum, native and presentation work and proposed a download website. These are context, not invented acceptance or reviewer assignments. Reviewers remain unassigned.
- Team target: feature readiness before September 18–19, with rehearsal time protected ahead of the September 22 showcase. This is a planning target, not an organizer deadline. The proposed meeting was moved toward Thursday; confirmation and professional-review arrangements remain with the team. Travel-form completion is individual and outside this engineering board.
- Implemented: historical scenarios/review/export; schema 2.1 saved custom evidence with consent, versioning and replay; optional Ollama assistant; stress-spectrum charts; separate PDF output; native download handling. Implementation is not proof of usability, scientific validation, offline isolation or executable self-containment.
- Corrected since earlier backlog: PDF breach arithmetic and PDF note opt-in have code/tests; do not reopen these as wholly absent. Selected-settings propagation and report cache invalidation are now done under B17.1/B17.2; fallback/degraded-render reporting (B17.3), CLI opt-ins (B17.4), device checks (B17.5) and independent PDF verification remain open.
- Current checks: snapshot checkout, Python offline smoke and explicit replay passed; run `21fac96ba217`, five scenarios, 500 audit records, implementation matches. That smoke packet contains **zero custom comparisons**; it is not a custom-data acceptance exercise. Full-suite result is recorded in HANDOFF.md when the current run finishes.
- Priority order: B15 correctness → B16 persistence/B17 report alignment → B18 assistant/privacy hardening → B19 one area model → B20 geographic views. B21 document ingestion can proceed after its evidence contract is agreed. Human validation and event confirmation should proceed alongside technical work.

The duplicate custom-evidence B13 heading is renamed B14 below; B13 remains the UI workflow task. Earlier checkpoint counts are historical, not current test totals. All new unchecked items are open work, with completed portions stated explicitly.

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

The implemented core includes rainfall scenario generation, grouping, ranking, review, evidence conflicts, custom supporting evidence and export. An optional Ollama assistant and illustrative reservoir spectrum now exist. Custom evidence does not yet drive a local-area impact model. A numerical check, hash, or user acceptance does not establish hydrologic validity or professional certification.

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

- Local chat assistant: implemented since this original deferral; hardening and evaluation are tracked in B18. Additional assistant scope remains lower priority than correctness and rehearsal.
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

Historical first slice: descriptive uploaded-versus-NOAA comparison began as preview only. Superseded by B14: saved evidence, versioned scenario links and consented packet replay are implemented. Seasonal baseline validation, independent real-sample review and custom-data-driven area simulations remain open. See docs/local_upload_and_research_plan.md for the implementation history.


## B14 — Reviewed custom rainfall evidence integration (formerly duplicate B13)

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

## B15 — Repair numerical meaning and current regressions (P0)

Owner / independent reviewer: Unclaimed. Added prerequisite from message (7)'s closing sequence and source inspection; this is not a reconstruction of its missing item 1.

- [x] **B15.1** Restore a passing current suite. The four September 8 PDF/UI export failures were resolved in earlier integrations. See the newest HANDOFF checkpoint for the current suite result; this does not complete the numerical/domain tasks below.
- [ ] **B15.2** Define the spectrum's reference correctly. `run_stress_spectrum` passes `scenario.series`; `simulate_stress_spectrum` multiplies that already-constructed series and labels 1.0 “100% Historical Baseline.” Use original observations for a true historical baseline or label it as the selected scenario. Trace compounded multipliers and revisions consistently across UI, assistant and PDF.
- [ ] **B15.3** Audit fractions versus percentages, rainfall mm versus volume, ac-ft/day versus MGD, threshold equality and scenario-year selection across all surfaces. Tools currently clamp ambiguous percentages and select the first scenario if a requested year has no matches. Return explicit validation/clarification instead of silently substituting another interpretation.
- [ ] **B15.4** Replace unsupported “catastrophic,” “survived,” and operational threshold interpretations with descriptions appropriate to an illustrative experiment. Test no-breach and partial-breach cases without claiming predicted restrictions.

## B16 — Save and reproduce illustrative simulations (message 7 item 2)

Owner / reviewer: Unclaimed. Open; rainfall/custom-evidence replay does not cover this experiment.

- [ ] **B16.1** Version settings: initial storage, conservation, pipeline, rainfall tiers, model identity and units.
- [ ] **B16.2** Link exact scenario revisions and evidence versions; restore inputs/results and mark results stale after changes.
- [ ] **B16.3** Define a separate simulation export and independent recomputation contract with negative tests. Label verified rainfall evidence separately from internally reproducible illustrative calculations.

## B17 — Align PDF, privacy and download behavior (message 7 item 3, P0)

Owner / reviewer: Unclaimed; B17.6 implemented by Claude on `fix/b17-report-content-accuracy` and reviewed/merged; B17.1/B17.2 implemented by Claude on `feat/b17-report-experiment-config`, reviewer unassigned. Dynamic breach arithmetic and `include_notes=False` already exist; remaining integration is open.

- [x] **B17.1** Pass the actual selected scenario, storage, conservation, pipeline and tiers to PDF generation. One frozen `ExperimentConfig` (`basin_core/pdf_report.py`) is built from the Review controls, stored in session state and threaded through the preview, `render_html_report` and `build_fallback_pdf`; `compute_report_metrics` now forwards `pipeline_active` and `tiers` to both simulators. The configured scenario becomes the report's primary scenario, and a configured scenario that is not in the accepted set is stated in the report rather than silently swapped. Defaults are the simulator's own (48% storage, 0% conservation, pipeline available, tiers 100/80/60/40) and are labelled as defaults, replacing the old unexplained 0.48/0.15 pair. **Not covered:** saved-session persistence of settings (B16), and the Review controls still only appear in the Reservoir-simulation view, so a report can carry defaults simply because that view was never opened.
- [x] **B17.2** Preview included scenarios, assumptions, data and consent; state that the separately generated PDF is outside ZIP verification unless a new contract covers it. The Exports page shows the configuration as a table, the preview expander repeats it inline, and both report paths print it. Generated previews and built packets are now keyed to a `report_state_token` over the workspace, accepted scenarios and revisions, both consent flags and the configuration, and stale bytes are dropped from session state rather than merely hidden. The export card no longer carries a blanket "cryptographically verified" badge over the PDF. **Not covered:** a new verification contract for the PDF; it remains outside the bundle's.
- [ ] **B17.3** **Partial: layout and encoding disclosure completed; browser-renderer failure reporting remains open.** Fix fallback encoding and make renderer failure/degraded output explicit. Do not silently substitute the short generic fallback for the full report. Inspect page breaks, tables and long evidence descriptions in both rendering paths. The vector report now measures text with real Helvetica/Courier metrics and wraps it (`text_width`, `wrap_text`), flows the scenario inventory, a new evidence/disagreement section and the provenance block through a paginating `VectorFlow` with labelled continuation pages and `Page N of M` footers computed from the real total. The six-scenario cap and the 35-character note cut are gone. Fonts declare `/WinAnsiEncoding` and content is written as cp1252, so accented Latin, dashes and guillemets render as themselves; characters with no glyph are counted and disclosed in the report instead of being silently replaced. The HTML path gained the same evidence section, `overflow-wrap: anywhere` and `page-break-inside: avoid`. **Not covered:** degraded-render reporting when the browser path itself fails is still open, and the win32 guard in `generate_pdf_report` still makes that path unreachable in the product.
- [x] **B17.7** Stop the test suite reading real user sessions. `tests/test_pdf_report.py` was already isolated by B17.6, but `app.py` globbed the live `local/` directory for its Saved Runs list, so every AppTest-based test read the developer's private analyses. `basin_core.workspace.session_dir()` now resolves through `BASIN_SESSION_DIR`, `Workspace.save` and the app's Saved Runs list both use it, and an autouse `conftest.py` fixture points it at a throwaway directory for every test.
- [ ] **B17.4** CLI note/custom-data opt-ins are implemented: `scripts/hydrologist_harness.py::cmd_export` forwards `args.include_notes` and `args.include_custom` (SEC.2). Still complete broader cross-output/device checks with private sentinel data and consent revocation.
- [ ] **B17.5** Test browser/native downloads, destination paths, write failures and recovery on the actual laptop. Native download-handling code exists; that is not a completed device test.
- [x] **B17.6** Correct report content in `basin_core/pdf_report.py` across both the HTML and Windows vector paths. Capacity and band volumes are now read from `RESERVOIR_ASSUMPTIONS` rather than restated (919,900 ac-ft, bands 367,960 / 275,970 / 183,980 / 137,985); the vector path renders an explicit unavailable state instead of substituting example rows, an invented run ID, snapshot digest or KPI figures; the audit stamp and footers state that SHA-256 verification covers the companion bundle and not the PDF; the fabricated ordinance citation, survey capacities and MGD benefit figures are removed, with the model's assumption and the research packet's TWDB values shown as distinct, labelled statements. Regression coverage in `tests/test_pdf_report.py` pins the model-derived capacity and bands to the simulator's own output, the unavailable states, and the verification wording. **Not covered:** the browser HTML-to-PDF route is unreachable on Windows (`generate_pdf_report` calls the vector builder directly when `sys.platform == "win32"`), so it was rendered manually with Edge for inspection rather than through the product path; no reviewer has read either document.

## B18 — Harden optional assistant (message 7 item 4, P0)

Owner / reviewer: Unclaimed. Ollama routing and deterministic tools exist. Their presence does not establish zero hallucinations or zero cloud leakage.

- [ ] **B18.1** Enforce local-only model connectivity and test remote-host configuration; show actual selected model/tag and availability. Current code uses the default Ollama client, and model preference matches family prefixes rather than exact tags.
- [ ] **B18.2** Verify missing/stopped/no-model/slow-model behavior while keeping core workflows usable.
- [ ] **B18.3** Validate argument names, types, ranges, dates and IDs. Remove silent malformed-year fallback to 2011 and implicit scenario substitution; expose interpreted inputs and units.
- [ ] **B18.4** Test ambiguous/unsupported questions and misleading supplied text; ensure final answers match tool data and retain limitations. Evaluate routing as well as arithmetic.
- [ ] **B18.5** Add read-only explanations of saved custom comparisons, suitability, missingness and uncertainty using the existing evidence contract.

## B19 — One custom-data-driven area model (message 7 item 5)

Owner / domain reviewer: Unclaimed. Proposed expansion; B14 stores supporting evidence and does not complete this task.

- [ ] **B19.1** Team selects one area, boundary and modeling question; reviewer agrees appropriate observation sources and representativeness.
- [ ] **B19.2** Define inputs, units, equations, baseline, period, assumptions and missing/unsuitable-data behavior before connecting reviewed datasets to numerical inputs.
- [ ] **B19.3** Link model outputs to evidence/settings, establish baseline-versus-scenario comparisons, domain review, validation criteria and visible uncertainty. Calibrated claims require the separate B08 scope decision.

## B20 — Geographic views (message 7 item 6)

UI lead volunteered in team context: Mohammed. Independent reviewer: Unclaimed. Numerical map claims depend on B19; visual prototypes may proceed earlier with explicit placeholder labels.

- [ ] **B20.1** Area boundary, station map and relevant reservoir/infrastructure layers with documented sources and reuse terms.
- [ ] **B20.2** Baseline/scenario views and timeline linked to saved simulation results; distinguish measured, assumed, simulated and unavailable information.
- [ ] **B20.3** Accessible legends, keyboard/selection controls and static exports. Station points and stress-spectrum charts alone do not establish an area visualization.

## B21 — Reviewed document ingestion (message 7 item 7)

Owner / reviewer: Unclaimed. Separate from generating a PDF report; not implemented by PDF export.

- [ ] **B21.1** Define supported types/limits and private storage with exact source identity; handle scanned, malformed and unsupported documents explicitly.
- [ ] **B21.2** Extract text with page references; require human inspection/correction before promoting extracted statements to model inputs.
- [ ] **B21.3** Link reviewed document evidence to assumptions/simulations with versioning and explicit export inclusion controls. Agree the evidence contract before parallel ingestion work.

## Remaining reconciliation and acceptance (message 7 item 8)

- [x] **B11.10** Incorporate messages (4)–(7) and team context, remove duplicate B13 heading, and correct current custom-evidence/assistant status on this board. No private transcript copied into Git.
- [ ] **B11.11** Complete cross-document reconciliation of README, claim inventory, methodology, upload plan and presentation against current implementation. “No LLM required for core workflows” remains accurate; distinguish it from “no LLM exists.” Separate wrapper executable from its Python/WebView2/Ollama prerequisites.
- [ ] **B09.11** Audit benchmark protocol, authorship, participant qualifications, task equivalence, timings and independent reproduction before claiming 30×–50× user benefit. Team-reported numbers and matching hashes are not proof of professional certification or representative time savings.
- [ ] **B10.9** Actual-laptop offline rehearsal must now include optional Ollama, PDF rendering, native downloads and fallback behavior in addition to the existing rainfall workflow.
- [ ] **B11.12** Confirm official event format and speaking time, complete novice/analyst/recipient exercises (B09), then rehearse and freeze under B12. Keep the September 18–19 readiness target separate from organizer requirements. Download-site proposal remains unverified/planned; do not publish unverified offline or standalone-install claims.

Acceptance: current automated regressions fixed, output/settings/consent contracts consistent, named human reviews recorded, and actual-device rehearsal completed. A source-code review or a green core replay alone does not satisfy these gates.
