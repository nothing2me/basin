# BASIN current handoff

Updated: 2026-09-06

## Current state

CSV preview release ae6ec27 is published. The running app subsequently encountered missing Workspace.selection_reason/evidence attributes after an in-place code update. Current source has the members; restarting the old server resolved the stale-runtime condition. No application source patch was required.

## Files changed

- README.md: stop/pull/restart instructions, stale Workspace troubleshooting and legacy executable distinction.
- docs/build_validation.md: restart diagnosis and fresh-process UI test results.
- HANDOFF.md: current checkpoint.

## Verification

Fresh import confirms Workspace.selection_reason exists. Server restarted on 127.0.0.1:8501. `python -m pytest -q tests/test_app.py --basetemp=tmp/pytest-restart-check --tb=short`: 2 passed. Previous integrated release passed 97 tests and offline replay; these were not rerun for documentation-only changes. Unsaved in-memory work is not preserved by restart.

## Next action

Teammates stop the server before pulling, restart via Start BASIN.cmd and refresh the browser. Continue local-station reference/persistence work from docs/local_upload_and_research_plan.md. Private uploads and environments remain excluded from Git.
