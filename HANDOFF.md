# BASIN current handoff

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

Remaining: B17 report correctness/settings/claims and table truncation, live Ollama and actual-device security gates. The PDF still hard-codes a mismatched capacity and audit badge and substitutes example rows when spectrum data is unavailable; a rendered PDF is not equivalent to independently verified report contents. PDF tests currently rely on an existing local session. (Those three PDF statements are superseded by the B17.6 checkpoint above; the closing point that a rendered PDF is not independently verified content still stands.) Prior failing-suite records below are historical and superseded by this checkpoint. No remote push performed by this integration pass.

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
