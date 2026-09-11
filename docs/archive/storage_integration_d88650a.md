# BASIN current handoff

## September 11 — Tailored Review and storage experiment integration complete

Current state: `codex/part-b` is rebased on `origin/main` at `5c0412a` and includes Gemini's tailored pre-run Review workflow, the later native-runtime/PDF/unit/navigation work, and the reconciled Part B storage experiment. Review focus changes presentation only. Reservoir runs now use explicit rainfall identity and percentage-point inputs, inclusive threshold/day-zero semantics, configurable storage and sector assumptions, content-addressed replay, and fail-closed malformed-session validation.

The modern Region N preset retains inactive storage, sector delivery, estuary pass-through and pipeline-case sensitivity outputs. Its interface describes these as configured assumptions. It no longer claims pump cavitation, guaranteed supply, adopted restriction actions, a live TCEQ determination, or implementation of a ballot proposal. Dated City context cites the reported 7.8% April 16 combined storage, the 180-day Level 1 supply condition, and the reported 72–79 MGD pipeline operation while keeping those facts outside the model contract.

Files changed in the final reconciliation: `app.py`, `basin_core/analysis.py`, `basin_core/integrity.py`, `basin_core/simulation.py`, `basin_core/summary.py`, `basin_core/water_system.py`, `basin_core/workspace.py`, `docs/post_2015_hydrology_and_simulation_plan.md`, `tests/test_simulation_contract.py`, `tests/test_summary.py`, and `tests/test_water_system.py`.

Verified commands:

- `python -m pytest -q --tb=short`: **554 passed, 3 skipped** in 856.84s. Skips are opt-in/genuine runtime or absent-model cases.
- Focused cross-integration suite: **93 passed** in 96.20s.
- `scripts/evaluate_routing_quality.py`: **50/50 passed (100.0%)** in 0.91s.
- `scripts/demo_smoke.py`: `verified: true`, five scenarios and 500 audit records replayed, `implementation_matches_current: true`.
- `python -m compileall -q basin_core` and `git diff --check`: passed.

Blocker: none. Next action: fast-forward the main checkout and push `main`, then perform optional visual/device acceptance in the browser. These checks establish implementation consistency and deterministic replay; they do not establish physical calibration, source suitability, forecast skill, professional approval, or official policy meaning.
