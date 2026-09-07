# BASIN current handoff

Updated: 2026-09-06

## Current checkpoint — documentation reconciliation

`main` is at `83d593d`, the working tree is clean, and `origin/main` points at the same commit. The theme and guided-tour work described in the two earlier checkpoints is published, not local-only as previously written here.

This pass reconciled `TODO.md` with the implementation: board statuses now separate implemented-and-verified work from work awaiting a named human, partial work, untouched work, and the reservoir paths recorded as not selected. Each task carries a dated status line pointing at the code, tests or documents behind it. No application code, dependency, scientific claim or product scope changed.

A follow-up sweep on the same day added the B09.3 observation sheet, checked every relative link and backticked path across `README.md`, `TODO.md`, `HANDOFF.md`, `docs/*.md` and `research/*.md`, and reconciled `docs/presentation_plan.md`, which turned out to be the largest documentation gap in the repository: it scripts a live demonstration of the climate-warming and data-centre stressors removed in `0be1933`, runs the demo inside the excluded `BASIN.exe`, describes GIS pipeline and corridor overlays the Data view does not have, and calls the packet a verified WAM export with engineering sign-off. A dated notice now heads that file listing each contradiction, and two broken file references were corrected; the pitch narrative itself was left for the team.

Documentation corrections made in this pass: the two TODO checkpoints no longer claim to be unpushed; `README.md` no longer says browser network isolation is described in `docs/build_validation.md`, because that document records no such run, and now points at `scripts/browser_rehearsal.mjs` instead; `docs/build_validation.md` gained a section recording the checks actually run today, kept separate from the earlier recorded results.

Interface claims checked against the running source: Help & tutorial sits directly below the sidebar view navigation (`app.py:417-431`); the first-run Workspace offers **Take a tour** (`app.py:540-546`); Settings holds Appearance with Light/Dark/System (`app.py:519-522`, `basin_theme.py`); the browser launcher is the supported release path (`README.md`, `scripts/start_browser.py`); local CSV uploads remain preview-only with no persistence, scenario link or export (`basin_core/uploads.py`, `README.md`); and the reservoir view is labelled an uncalibrated illustrative experiment excluded from packets and verification (`app.py:659-685`, `docs/verification_scope.md`).

## Verification

Re-run today at `83d593d` on Windows 11, CPython 3.12.14, repository `.venv`:

- `python -m pytest -q --basetemp=tmp/pytest-doc-reconcile`: 97 passed in 60.3 s.
- `python scripts/check_snapshot_checkout.py`: verified; fresh clone reproduces the snapshot hash under `eol=lf`.
- `python scripts/demo_smoke.py`: verified, network-blocked rehearsal.
- `python scripts/replay_bundle.py output/BASIN-rehearsal.zip`: verified; run `5cf371d39eb2`, 5 accepted scenarios, 500 audit records, `implementation_matches_current: true`.
- `python scripts/evaluate_selection.py`: 9 configurations (seeds 7/22/91 across three profiles), silhouettes 0.246-0.416.

Earlier numbers in `docs/build_validation.md` — the 49-wheel offline installation, the 500-candidate timing and memory figures, the browser inspections — are recorded results from their own runs and were not repeated here. These automated checks establish internal consistency and regression status only. They are not practitioner validation, teammate review, presentation-device verification or scientific approval.

## Files changed in this pass

- `TODO.md`: reconciliation section, board statuses, per-task status lines, subtask boxes, not-selected annotations, team roster note and the sweep summary.
- `HANDOFF.md`: this checkpoint.
- `README.md`: browser-rehearsal cross-reference corrected.
- `docs/build_validation.md`: new section recording today's checks; superseded checkpoint wording corrected.
- `docs/demo_runbook.md`: one line distinguishing the simulation film from the missing backup recording.
- `docs/presentation_plan.md`: reconciliation notice added; `rainfall.csv` corrected to `daily_rainfall.csv` and `fetch_snapshot.py` to `scripts/fetch_noaa.py`.
- `docs/observation_sheet.md`: new, for B09.3.

## Next actions

1. **B01.5 — put real names on the board.** Every task except B02 still reads `Unclaimed / Unclaimed`, so nothing implemented can move past `In review`. This blocks B04.10, B08.B5 and B12 as much as any code does.
2. **B11.7 — resolve the demonstration format.** `docs/demo_runbook.md` describes a three-minute demo on September 22 while `docs/presentation_plan.md` describes a 60-minute finalist block. Check the latest organizer communication and retire whichever document is wrong.
3. **B04.10 / B08.B5 — run the independent review.** Export a packet containing a multiplier, a CSV replacement, a rejection, changed weights and an unresolved conflict; have a teammate replay it and read the brief without coaching, and record the reservoir presentation judgement at the same time. Record the outcome in `docs/validation_notes.md`.
4. **B10.3/B10.4 — test the presentation laptop.** Install from the packaged kit on the actual device, start through `Start BASIN.cmd`, and rehearse with Wi-Fi off including the coordinate overview. `scripts/browser_rehearsal.mjs` covers browser-level isolation but has no recorded run.
5. **B11.4 — decide what happens to `docs/presentation_plan.md`.** Its demo script, mass-balance equation, case study and Q&A still sell removed stressor features, the excluded executable and a verified WAM export. Either rewrite it around what the build does or retire it in favour of `docs/demo_runbook.md`. Until then, no one should rehearse from it.

## Blockers and cautions

- B12 stays blocked. No freeze, commit, push or submission is authorized by this board.
- B01.6 (actual Stage 1 commitments) is still unlocated; B01.7 dates remain planning targets, not verified organizer deadlines.
- Teammates: stop the server with Ctrl+C before pulling, run Setup BASIN.cmd if dependencies changed, then Start BASIN.cmd and refresh. Unsaved in-memory work does not survive a restart.
- `media/BASIN_Simulation_Demonstration.mp4` is a rendered simulation film. The B11.9 backup recording of the accepted demo build does not exist.
- The team is Mohammed Asad Khan, Noah Wilborn and Misha Stegall. The board still reads `Unclaimed` on purpose: each person claims their own lane and names a different reviewer, and nobody is entered by anyone else.
- `docs/observation_sheet.md` exists but has never been used in a session.
