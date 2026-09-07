# BASIN current handoff

Updated: 2026-09-06

## Latest local checkpoint — appearance and onboarding

Added coordinated native Light/Dark/System themes in `.streamlit/config.toml`, with styles and browser theme shortcuts in `basin_theme.py`. Updated `app.py` typography, brand, metric cards and first-run invitation. Help & tutorial now sits below page navigation; Settings contains Appearance. Charts inherit native theme colors. Packaging includes the new module.

Workflow/tutorial/upload checks: 22 passed. Source package built and new theme module inclusion checked. Local browser inspection verified the light and dark layouts and the native theme shortcut. Changes remain local and unpushed. Refresh the browser to load the update, then use Settings → Appearance. Teammate review remains pending.

## Earlier local checkpoint — tutorial layout

The user reported tutorial arrows pointing at empty strips and cards jumping between the sidebar and main columns. `app.py` now uses actual Streamlit target containers and one consistent main-area guide. Navigation buttons are grouped, each target is named, and a jump link locates it. Export guidance explains outstanding reviews; the tour never grants approval. Tests cover the walkthrough, review gate, and recovery after manually switching pages.

Refresh the browser and restart the tutorial to review. Changes are local and unpushed. Named teammate review and broader B11 presentation reconciliation remain outstanding. The earlier published checkpoint is retained below.

## Previous published state

CSV preview release ae6ec27 is published. The running app subsequently encountered missing Workspace.selection_reason/evidence attributes after an in-place code update. Current source has the members; restarting the old server resolved the stale-runtime condition. No application source patch was required.

## Files changed

- README.md: stop/pull/restart instructions, stale Workspace troubleshooting and legacy executable distinction.
- docs/build_validation.md: restart diagnosis and fresh-process UI test results.
- HANDOFF.md: current checkpoint.

## Verification

Fresh import confirms Workspace.selection_reason exists. Server restarted on 127.0.0.1:8501. `python -m pytest -q tests/test_app.py --basetemp=tmp/pytest-restart-check --tb=short`: 2 passed. Previous integrated release passed 97 tests and offline replay; these were not rerun for documentation-only changes. Unsaved in-memory work is not preserved by restart.

## Next action

Teammates stop the server before pulling, restart via Start BASIN.cmd and refresh the browser. Continue local-station reference/persistence work from docs/local_upload_and_research_plan.md. Private uploads and environments remain excluded from Git.
