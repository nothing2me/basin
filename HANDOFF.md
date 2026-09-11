# BASIN current handoff

## September 11 — Part C status and development-device checkpoint

Current state: Review browser acceptance is merged at `cf374bd`. The active release documents now separate implementation, automated verification, development-machine observation and external acceptance. The 601-line historical TODO is preserved under `docs/archive/`; the active `TODO.md` is a concise ordered queue.

The documentation reconciliation corrected a material boundary: assistant-created Region N experiments are the schema 2.2 saved/replayed path. Review’s selectable storage-system experiment is a separate transient session/report configuration. Aligning these paths remains the first technical follow-up.

Part C checks completed on this development Windows machine:

- Actual Chromium Review acceptance at 1280×720 and 375×812 in Dark and Light, including four focus profiles, skip/show-all/change-focus, saved-session restoration, visible keyboard focus and tutorial targeting.
- Browser launcher selected port 8505 and reached readiness when requested port 8504 was occupied.
- Development environment recorded as Windows NT 10.0.26200.0 AMD64, CPython 3.12.14 and Streamlit 1.63.0.
- Tracked `BASIN.exe`: 14,869,768 bytes, SHA-256 `838ee698c8ec3d879af622818fb566fcd30c496833b0a2057e0c9dad1e195809`. Identity recorded only; the executable was not accepted in this pass.

Changed files are listed in `docs/status_reconciliation_handoff.md`. No production code, dependencies, configuration, data or model artifacts changed during status reconciliation.

Verification:

- `git diff --check`: passed.
- Relative links in every changed Markdown file: passed.
- Diff inspection found no `.py`, `.cmd`, `.sh`, `.toml`, `.txt` or `.json` changes.
- Part B regression baseline remains **554 passed, 3 skipped**; routing **50/50**; demo replay verified.

Blocker: GitHub fetch initially failed because sandbox network access was unavailable; repeat immediately before commit. Actual presentation-laptop install/offline/native/download/PDF/projector checks, intended-user exercise, organizer format and final rehearsal remain not run. No weights were downloaded and no network/firewall settings were changed.

Next action: compare any new `origin/main` commits, integrate safely, commit/push the documentation checkpoint, then run Task 6 on the actual presentation laptop with the user controlling connectivity and model download authorization.
