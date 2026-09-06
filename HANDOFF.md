# BASIN current handoff

Updated: 2026-09-06

## Current state

User explicitly authorized publishing the complete local CSV preview work and documentation. Integrated with upstream main 8f04091, preserving teammate schema 2.0 evidence/integrity, revised illustrative reservoir behavior and launcher. The previous local-only restriction is superseded for this release; private uploads, sessions and environments remain excluded.

The Data/initial Workspace view now previews one station's date,precipitation CSV with explicit station/location/unit, bounded validation, missing-day counts, chart/table and original hash. Preview does not save inputs or modify scenarios. README provides teammate setup and an illustrative example.

## Release files

- basin_core/uploads.py, app.py, tests/test_uploads.py: preview parser, UI and tests.
- docs/examples/local-rainfall-example.csv: illustrative 30-day, 62.5 mm sample, not verified observations.
- README.md, docs/build_validation.md, docs/local_upload_and_research_plan.md, HANDOFF.md: setup, verified status, updated plan and checkpoint.
- .gitattributes: preserve original research artifact hashes; retain upstream LF snapshot rule.
- TODO.md: current preview checkpoint without marking later work complete.

## Verification

97 tests passed after upstream integration. Fresh-checkout observation hash passed. Offline smoke and explicit replay verified 5 exported scenarios and 500 audit records. Source package built and checked for preview/sample inclusion and absence of local sessions/environment. Diff whitespace checks passed. Python 3.12.14 on Windows; teammate machines still require their own setup/rehearsal.

## Next action

Teammates pull main, run Setup BASIN.cmd and Start BASIN.cmd, then try Data → Preview your local rainfall CSV. Continue local-station reference handling and persistence using existing schema 2.0 evidence/integrity boundaries. PDF ingestion and numerical uploaded-versus-public comparison remain future work. Do not treat illustrative rainfall or the reservoir experiment as validated predictions.
