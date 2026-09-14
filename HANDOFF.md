# BASIN current handoff

## Current state

The Scenario Builder now shows one direct **Dates** field in place of duration and starting-month controls. Users can click it to choose a start/end range on the calendar or type both dates directly. The selected historical range constrains source observations and survives saved-run serialization and verified replay.

The station control is labeled **Stations** and supports searching by displayed station name or station ID while retaining multi-selection. The Builder uses one full-width scenario card; ranking weights are collapsed under **Advanced ranking settings**, and the duplicate page introduction was removed. Preset, time, and multi-range date controls are absent from the Builder.

## Files changed

- `app.py`
- `basin_core/engine.py`
- `basin_core/integrity.py`
- `tests/test_app.py`
- `tests/test_pipeline.py`
- `HANDOFF.md`

## Verification

- `pytest tests/test_pipeline.py tests/test_app.py -q`: 35 passed before the simplification pass.
- `pytest tests/test_app.py -q`: 7 passed after the direct-calendar pass.
- `pytest tests/test_integrity.py tests/test_export_quality.py tests/test_report_invalidation_app.py -q`: 55 passed and one timeout during a long combined run; the timed-out test passed alone in 22.68 seconds.
- Browser rehearsal at `http://127.0.0.1:8516/`: full-width Builder, searchable Stations control, one directly editable date range, opened calendar, and collapsed ranking settings rendered correctly.
- `python -m py_compile app.py basin_core/engine.py basin_core/integrity.py`: passed.

## Blocker

No implementation blocker. The broader combined report run experienced one transient AppTest timeout under sustained resource load; the same test passed immediately when rerun alone.

## Next action

Review the calendar interaction with the user, then commit and push after any requested wording or spacing adjustments.
