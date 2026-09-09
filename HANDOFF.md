# BASIN current handoff

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
