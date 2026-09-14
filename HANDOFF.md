# BASIN current handoff

## Current state

The Scenario Builder now combines duration and starting-month choices into one **Date range** selector. Quick seasonal choices preserve the established resampling defaults. **Custom date ranges** opens a calendar editor for one to four exact historical ranges, with start/end date and time. Exact dates constrain the source observations; times are retained in the audit record while calculations remain daily. The selected ranges survive saved-run serialization and verified replay.

The station control is labeled **Search and select stations** and supports searching by displayed station name or station ID while retaining multi-selection.

## Files changed

- `app.py`
- `basin_core/engine.py`
- `basin_core/integrity.py`
- `tests/test_app.py`
- `tests/test_pipeline.py`
- `HANDOFF.md`

## Verification

- `pytest tests/test_pipeline.py tests/test_app.py -q`: 35 passed.
- `pytest tests/test_integrity.py tests/test_export_quality.py tests/test_report_invalidation_app.py -q`: 55 passed and one timeout during a long combined run; the timed-out test passed alone in 22.68 seconds.
- Browser rehearsal at `http://127.0.0.1:8516/`: searchable station selector, quick date menu, custom calendar popover, exact date/time fields, and range summary rendered correctly.
- `python -m py_compile app.py basin_core/engine.py basin_core/integrity.py`: passed.

## Blocker

No implementation blocker. The broader combined report run experienced one transient AppTest timeout under sustained resource load; the same test passed immediately when rerun alone.

## Next action

Review the calendar interaction with the user, then commit and push after any requested wording or spacing adjustments.
