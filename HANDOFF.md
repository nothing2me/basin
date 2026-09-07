# BASIN current handoff

Updated: 2026-09-06

## Current state

Fetched and fast-forwarded main to 5e17706, preserving theme/tour, video and documentation reconciliation commits. Reviewed source and current gaps; upstream baseline passed 97 tests. Added the first Part B uploaded-versus-public rainfall comparison in the existing preview.

The user explicitly selects a bundled NOAA station and declares station relationship and daily observation compatibility. Unknown declarations/no overlapping valid dates block calculation. Totals use paired valid days only. UI shows differences, gaps and an opt-in numerical comparison report. This does not save uploads, mutate scenarios or create a verified scenario packet.

## Changes

- basin_core/rainfall_comparison.py: pure paired-day calculation and eligibility checks.
- app.py: comparison review controls, daily chart, totals and report download.
- tests/test_rainfall_comparison.py and tests/test_uploads.py: arithmetic, gaps, blocking, zero denominator, bad reference and UI state-reset checks.
- README.md, TODO.md, docs/local_upload_and_research_plan.md and docs/build_validation.md: current scope and verification.

## Remaining work and team gates

Full Part B remains incomplete: persisted evidence/disposition, scenario linkage and packet replay integration are next. User declarations are not independent spatial validation. Preserve upstream open gates: team owner/reviewer assignments, reconciliation against the newly added docs/submission_record.md, demonstration format/script reconciliation, practitioner exercise and presentation-laptop verification. The simulation video is not an accepted-build backup recording.

## Next action

Try the 2024 illustrative example in the upload preview and review the NOAA comparison limitations. Then attach reviewed comparison evidence through the existing schema 2.0 contract, with appropriate approval/privacy behavior. Keep private inputs out of Git.

## Verification

105 full-suite tests passed; expanded upload/comparison UI subset passed 28 tests. Fresh snapshot checkout, offline smoke, explicit scenario replay and source packaging passed. No private samples staged. See docs/build_validation.md for boundaries and exact results.

## Concurrent upstream update

Integrated 106842a during publication: docs/submission_record.md now records Stage 1 answers and finalist Q&A, with new logo concepts. Submission material is now available for reconciliation, rather than missing. This documentation/media-only commit changed no tested application code; comparison changes rebased cleanly.
