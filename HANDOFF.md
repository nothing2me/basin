# BASIN current handoff

## Current state

The Data Dashboard can define a Region N-wide analysis or a named city/provider. A local-community target filters the Scenario Builder to stations in the selected county and preselects the strongest place-name, usable-setting, and completeness match. A source-area target requires the user to choose stations deliberately because a city name does not establish a utility's supply catchment.

The reproducible NOAA snapshot contains 20 GHCN-Daily point stations across all 11 Region N counties. Review and every verified output preserve the audience, rainfall target, exact stations, observation period, source type, and geographic limitations. Newly bundled public stations retain the public-evidence completeness rule; only manifest-identified custom observations receive the custom-data exception.

The Scenario Builder combines city-aware station choices with a searchable station picker and one direct **Historical source window** field. The field identifies the observed event to stress and explicitly distinguishes source dates from forecast dates. The range survives saved-run serialization and verified replay.

The station control is labeled **Stations** and supports searching by displayed station name or station ID while retaining multi-selection. The Builder uses one full-width scenario card; ranking weights are collapsed under **Advanced ranking settings**, and the duplicate page introduction was removed. Preset, time, and multi-range date controls are absent from the Builder.

## Files changed

- `app.py`
- `basin_core/engine.py`
- `basin_core/data.py`
- `basin_core/integrity.py`
- `tests/test_app.py`
- `tests/test_analysis_context.py`
- `tests/test_pipeline.py`
- `HANDOFF.md`

## Verification

- `pytest tests/test_pipeline.py tests/test_app.py tests/test_analysis_context.py -q`: 42 passed after reconciling city targeting with the simplified Builder.
- `pytest tests/test_integrity.py tests/test_export_quality.py tests/test_report_invalidation_app.py -q`: 56 passed, including saved-run reconstruction and verified report invalidation.
- Browser rehearsal confirmed the city/provider target, local station filtering, direct historical source window, and selected-station context in the Builder.
- `python -m py_compile app.py basin_core/engine.py basin_core/integrity.py`: passed.

## Blocker

No implementation blocker.

## Next action

Run the final presentation-laptop and uncoached professional workflow rehearsal.
