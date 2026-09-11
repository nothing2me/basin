# Numerical meaning across surfaces — task handoff (B15.2, B15.3, B18.3)

| | |
|---|---|
| Branch | `fix/numerical-meaning` (not merged, not pushed) |
| Worktree | `C:\Users\moham\Documents\GitHub\basin-numerical-meaning` |
| Base | `origin/main` at `0b3d9031b89674ef7279381284a70edb06f850bb` (fetched 2026-09-10; unchanged since Task 1) |
| Implementation commit | `9332b2b3dfa53b60c0cb9bdd4721470de8d6eb24` (this document is committed separately on top of it) |
| For | Astra review and integration. `TODO.md` and `HANDOFF.md` were not edited. Not run concurrently with Tasks 3/4. |

Scope: I traced original observations → constructed scenario → edited revision →
spectrum tier → tool/assistant, app Review, HTML and vector PDF. I fixed specific label and
input-interpretation errors. The storage arithmetic is unchanged. **No scientific
validity, calibration, or expert approval is claimed.** "Old" behaviour below was reproduced
by running the same script against a pristine `git archive` of the base commit; see §3.

## 1. Interpretation changes, old → new

| # | Surface | Old interpretation (base `0b3d903`) | New interpretation |
|---|---|---|---|
| 1 | Assistant spectrum summary | When every tier crossed 20%: "Even at **100% historical baseline**, critical 20% threshold is breached on Day 0". The 100% tier is the scenario revision, which for B-009 is 40.2% of observed rainfall. | "Every tested tier reached the assumed 20% band…; the 100% tier (the highest tested) did so at Day 0 (at/below at start)." Every reservoir answer names the input: `scenario B-009 revision 1, constructed at 40.2% of observed rainfall (source window …)` and "100% … is not the unmodified historical record". |
| 2 | Tier labels (saved runs, tools, app, PDF, charts) | `Selected scenario (100%)`, `20% additional rainfall reduction`…. These were also applied to **observed-window** runs, whose 100% tier *is* the observations. Non-default tiers read `50% (-50% Rain)`. The chart fallback used `int(m*100)`, so 0.29 became `28% Rain`. | One function, `rainfall_tier_label`: `100% of input rainfall`, `50% of input rainfall (50% reduction)`, `110% … (10% increase)`, rounded. What "input" means is stated beside every table (`describe_input_rainfall`). |
| 3 | Tier as % of observations | Not shown anywhere. | App table, assistant table and reservoir answer add "≈ % of observed" = tier × construction retention × scale edits. It is shown only when that is a single number; station-specific retention or a CSV replacement gives "n/a". |
| 4 | Assistant "Survived"/"Breached", "catastrophic 40% rainfall", "Severe infrastructure deficit" | Stored status `✅ Survived` / `❌ Breached (Stage 3)`; operational wording in the assistant. | Stored status `Above 20% throughout window` / `At or below 20% in window`. Assistant text reports the first day each assumed band is reached and says "these assumed inputs only". |
| 5 | Day 0 (storage already at/below a band at the start) | `threshold_crossing_day` returned 0, but truthiness checks rendered it absent. Assistant spectrum: `Not reached ✓` at 35% initial storage for the 40% band. HTML `—`, vector `--`, app table "Not reached in window". The app single-run metric used strict `<` over rows from day 1, so it reported **Day 1**. The UI offers 35% initial storage, so this was reachable. | `threshold_day_label`: `Day 0 (at/below at start)`, used by the app table, the app metrics (now `threshold_crossing_day`), the assistant, HTML (`…*`) and vector (`Day 0 (start)`). |
| 6 | Threshold equality | Crossing days inclusive (`<=`), but `stage_num` strict (`<`): storage of exactly 20.0% was band 2 while also a 20% crossing. The PDF band table says "≤ 20%". Timeline legend: exactly 40% = "At least 40%". | Bands inclusive in `simulate_reservoir_drawdown` (20.0% → band 3) and in the timeline ("Above 30% to 40%" contains 40.0). **Only exact equality changes; storage values are unchanged.** |
| 7 | Report default scenario | With no Review experiment, the report computed on `accepted[0]` while its configuration row said "Not tied to a specific scenario". | Row reads `B-009 (revision 1) - first accepted scenario; not chosen in Review`. The existing "No experiment was configured in Review" notice stays. |
| 8 | PDF 20%-crossing for conservation comparison | `compute_report_metrics` scanned rows `<= 20.0` from day 1, ignoring day 0 and the system's configured band. | Shared `threshold_crossing_day` with the configured band. |
| 9 | Model-facing `initial_storage_pct` | Schema said "a fraction (e.g. 0.48 for 48%)" and validation required 0.05–1, but the tool reads percentage points. A model following the schema ran **0.48% initial storage** (saved fraction `0.0048`). | Schema says percentage points. 0 < value ≤ 1 is refused as ambiguous (same rule as conservation). 48 runs at 48%. |
| 10 | "Show me recent drought scenarios" (both routers) | Silently answered for **2011** ("Scenarios matching year 2011 — 2 found"). | Asks for a year and lists the start years present. |
| 11 | `find_scenarios_by_year` | Default `year=2011`. String-prefix match: `year=201` returned **11** windows from 2010–2019. | Year required, exact four-digit integer, start-year match. An absent year returns no rows, "No other year was substituted" and the years present. |
| 12 | `describe_cluster` | Missing group → group+1 or the first group; `describe_cluster(0)` returned **group 1**. Schema said groups "0, 1, 2, or 3". | Unknown group → error listing the actual groups (numbered from 1). Schema corrected. |
| 13 | Scenario-specific chat answers without an ID (concurrence, ranking, evidence, describe, compare) | Answered for the first shortlisted scenario(s): "What is the station stress?" → "Station stress analysis for **B-009**". | "Please clarify: name a scenario ID … Current shortlist: …". |
| 14 | Rainfall question without dates/station | "Show daily rainfall observations for station USW00012924" → **2011-01-01 to 2011-12-31**. No station → first manifest station. One date → that date to 31 December. | Asks for dates or a year, and for a station. A single date is that one day. Station aliases use word boundaries (`sat` no longer matches "saturday"). |
| 15 | Unlabelled percentages in the assistant router | "Run spectrum on B-009 at 35% initial storage with conservation" → conservation **35%** (the word "conservation" claimed the first percentage). "48% capacity/pool" was read as storage. | The labelled parser from `basin_ui` is now shared: every percentage must be labelled or the router asks. Listing the standard 100/80/60/40 tiers is accepted as a restatement. Result above: storage 35%, conservation 0%. |
| 16 | Sensitivity in chat | Always previewed `duration=25`, whatever was asked; "doubled" was the constant 50. | Explicit `<weight> to/is N`, or doubling/halving the **current** weight. Otherwise asks, listing current weights. Tool rejects weights outside 0–100, NaN or booleans (it accepted 150 when called directly). |
| 17 | `query_rainfall` dates | Any string passed to pandas slicing (`"2011"`, reversed ranges, `2011-02-30` gave odd or empty results). | ISO `YYYY-MM-DD`, real dates, start ≤ end. |
| 18 | Custom storage system demand (ac-ft/day) | UI built `WaterSystemConfig(..., demand_acft_day=12)` and inherited `demand_no_pipeline_acft_day=554`. Unchecking pipeline requested **554 ac-ft/day** (reproduced; ≈46× the entry, as the 2026-09-09 audit reported). | Custom systems set no no-pipeline demand. A caption says the pipeline setting does not change demand when none is configured. |
| 19 | Depth units | App metric branch: `100.0 mm (100.0 in)`, the mm value printed as inches. Crop deficit labelled `in/acre`. | `(abs(difference)/25.4) in`, e.g. 100 mm → 3.94 in. Irrigation depth shown as `in` with "acre-inches per acre". |
| 20 | Assistant router duplication | `basin_ui.fallback_query_route` and `assistant.semantic_query_route` parsed the same question differently. | `fallback_query_route` delegates to the one router. Also, the app's "Direct Tool Runner" no longer invents 2011 dates, group 0 or empty experiment settings; it states which shortlisted scenario it used. |

### ac-ft/day versus MGD; rainfall depth versus storage volume

- No MGD or GPM value or conversion exists in the code. Demand, evaporation, inflow and
  storage are ac-ft/day or ac-ft throughout, so there was no MGD mix-up to fix. Older
  TODO/HANDOFF text claiming a GPM default is not supported by the code. For reference, if
  MGD is ever shown, 1 MGD ≈ 3.0689 ac-ft/day.
- Rainfall enters storage only through `inflow = base + sensitivity × mean station rainfall
  (mm/day)`, an ac-ft-per-mm coefficient with no catchment area. The units are consistent
  and labelled illustrative. No change; see §4.

## 2. Saved-run compatibility (integration decision)

Tier labels, status text and `stage_num` are stored inside saved simulation results, and
replay compares them exactly. `THRESHOLD_VERSION` is therefore now
`inclusive-daily-endpoints-with-day-zero-2`. A run saved under `-1` is refused with
"Unsupported simulation version; do not reinterpret older results", which is the existing
mechanism; a test covers it. **Consequence:** a session containing an active, reviewed
version-1 run cannot be exported until that experiment is re-run and re-reviewed. Saved runs
first appeared in P0-C on 2026-09-10. Input descriptions (`describe_input_rainfall`) are
computed at display time and are **not** stored, so run identity does not depend on them.

## 3. Evidence (commands as run)

Python: `C:\Users\moham\Documents\GitHub\basin\.venv\Scripts\python.exe` (CPython 3.12.14), run from the worktree.

1. **Old vs new on identical inputs.** `git archive 0b3d903 | tar -x` into the scratchpad,
   then `PYTHONDONTWRITEBYTECODE=1 python old_vs_new_evidence.py` in that copy and in the
   worktree. The workspace was `ScenarioParams(all stations, candidates=30)`, size 3; first
   shortlisted scenario B-009; groups 1, 2, 3. Results:

   | Probe | Base | Branch |
   |---|---|---|
   | Model args `initial_storage_pct=0.48` | accepted; saved fraction `0.0048` | refused as ambiguous |
   | `find_scenarios_by_year(201)` | 11 matches | ValueError (four-digit year) |
   | "Show me recent drought scenarios" | "Scenarios matching year 2011 — 2 found" | "Please clarify: give a four-digit source start year…" |
   | `describe_cluster(0)` | returned group 1 | "No drought profile group 0. Groups in this workspace: 1, 2, 3" |
   | "What is the station stress?" | "Station stress analysis for B-009" | "Please clarify: name a scenario ID…" |
   | "Show daily rainfall observations for station USW00012924" | 2011-01-01 to 2011-12-31 | "Please clarify: give a date range…" |
   | "Run spectrum on B-009 at 35% initial storage with conservation" | storage 0.35, conservation **0.35** | storage 0.35, conservation 0.0 |
   | 100 ac-ft pool at 25%, 5 ac-ft/day demand → 20.0%, 15.0% | `stage_num` [2, 3] | [3, 4] |
   | Spectrum B-009, 35% initial, 100% tier row | `Selected scenario (100%) \| 100.0% \| 16.7% … \| Not reached ✓ \| Day 65 \| Day 151 \| … \| ❌ Breached (Stage 3)` | `100% of input rainfall \| 40.2% \| 16.7% … \| Day 0 (at/below at start) \| Day 65 \| Day 151 \| … \| At or below 20% in window` |
   | Spectrum B-009, 20% initial, summary | "Even at 100% historical baseline, critical 20% threshold is breached on Day 0." | "Every tested tier reached the assumed 20% band…; the 100% tier … did so at Day 0 (at/below at start)." |
   | `WaterSystemConfig(demand 12)` with the dataclass default, pipeline off | 554.0 | 554.0 (model unchanged; the **app** no longer builds this config, row 18) |

   The storage numbers in the matching rows (16.7%, 153,175 ac-ft, Day 65, Day 151) are
   identical: the arithmetic did not change.
2. **Hand-calculable fixtures:** `tests/test_numerical_meaning.py`, 28 tests, including one
   for the Direct Tool Runner's `direct_tool_arguments` helper. Each docstring carries its
   arithmetic:
   - **Transformed scenario:** retention 0.5, then ×0.8 → 40% of observed; a 50% tier → 20%.
     A real B-scenario edited ×0.5 was verified with `np.allclose(series, observed ×
     retention × 0.5)`, and its answer shows the observed column and no "historical
     baseline", "survived", "catastrophic" or "breached".
   - **Non-default tiers:** 1,000 ac-ft pool, 10 ac-ft/mm inflow, 30 ac-ft/day demand, 1 mm/day:
     - 100% tier: 480, 460, 440;
     - 50% tier: 475, 450, 425;
     - 25% tier: 472.5, 445, 417.5 ac-ft.
     Also 0.29 → "29%".
   - **Absent year:** zero rows, no substitution, exact start years. Types `201`, `"2011"`,
     `2011.0`, `True` and `None` are refused. Clarifications are required for year, station,
     dates, group and scenario.
   - **Invalid percentages:** 0.48 and 1 are refused as model arguments; 48 runs at 48%.
     Weights 150, −5, `True` and NaN are refused. An unlabelled "25%" creates no run.
   - **Threshold boundary:** 25% → 20.0 → 15.0 → 10.0 gives crossing days (0, 0, 1, 2) and
     bands [3, 4, 4]. 20.1% on day 1 is not a crossing. A flat 40.0% sits in the 40% band.
   - **Cross-surface agreement:** for B-009 with 35% storage, 20% conservation and Region N:
     - the app's calculation (`simulate_stress_spectrum(s.series, …)`), the deterministic
       tool's saved run and `compute_report_metrics` return identical tier labels, retention,
       min/final storage, crossing days and status;
     - the HTML report prints those crossing days and the input description;
     - a reachable day-0 case (35% initial storage) appears in HTML
       (`Day 0 (at/below at start)*`) and in extracted vector text (`Day 0 (start)`).
3. **Existing suites after the change:**
   `python -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-existing tests/test_assistant.py tests/test_assistant_adversarial.py tests/test_report_config.py tests/test_simulation_contract.py tests/test_pdf_report.py tests/test_visualizers.py tests/test_security.py tests/test_qwen_security.py tests/test_qwen_inference.py tests/test_embedded_assistant_ui.py tests/test_summary.py tests/test_agronomics.py tests/test_water_system.py tests/test_reservoir.py tests/test_report_layout.py`
   → 215 passed, 1 failed, 1 skipped. The failure was `test_legacy_percentage_arguments_still_resolve`,
   caused by my first attempt to make legacy report arguments fraction-only. I **reverted**
   that change (see §4); afterwards `tests/test_numerical_meaning.py tests/test_report_config.py`
   → **59 passed**. Qwen grounding and security tests (`test_qwen_security`, `test_security`,
   `test_assistant_adversarial`, `test_embedded_assistant_ui`) pass unchanged.
   - Tests changed deliberately: `test_assistant.py::test_semantic_query_route` now expects a
     clarification for "Compare scenarios", "What is the station stress?" and "Sensitivity of
     weights", and a result when IDs/values are given. `test_all_templates…` uses an existing
     group. `test_report_config.py` expects the new tier label.
4. **Full suite on the implementation commit `9332b2b`:**
   `python -m pytest -q -p no:cacheprovider --basetemp=tmp/pytest-final` → **480 passed,
   1 skipped in 416.74 s**, exit 0.
   - The skip was not re-listed with `-rs`. The only skip condition expected in this
     environment is `test_real_qwen_inference`, which needs model weights.
   - An earlier full run was stopped before it finished because files changed during it
     (the Direct Tool Runner helper and its test); its result is not used.
   - No baseline full run at `0b3d903` was made in this worktree, so test-count differences
     from older checkpoints are not interpreted.
5. **Routing benchmark:** `python scripts/evaluate_routing_quality.py` → **50/50**. Four
   expectations changed from a tool answer to `clarification`:
   - rainfall without dates;
   - "Run sensitivity test on ranking weights";
   - "Sensitivity test: how do weight changes impact ranks?";
   - "What defines drought group 0?".
   The earlier 50/50 counted silent defaults as passes. It is the repository's own routing
   check, not an evaluation of answer quality.
6. `python scripts/demo_smoke.py` → exit 0; `python scripts/replay_bundle.py output/BASIN-rehearsal.zip`
   → `verified: true`, run `ba84dfffcb1d`, 5 scenarios replayed, `implementation_matches_current: true`,
   0 simulations and 0 custom comparisons in this packet.
7. `git diff --check` → clean.

Not exercised: the Streamlit Review screen was not opened in a browser. App changes are
covered only by the existing AppTest workflows in the full suite (which open both simulation
subviews without exceptions) and by the shared-function tests above. The custom-system
caption and the Direct Tool Runner messages were not rendered in a browser.

## 4. Not changed, and proposals needing human review

- **Legacy report arguments (decision needed).** `render_html_report(..., initial_pct=…)`
  still reads 1.0 as 100% but 1.5 as 1.5% (`_as_fraction`). An existing reviewed test
  (`test_legacy_percentage_arguments_still_resolve`) intentionally keeps percentage support,
  and no product path uses these arguments. I reverted my stricter version and documented the
  boundary. Recommendation: remove the positional arguments or make them fraction-only.
- **Assistant tools always use the Region N preset.** The app's Review screen can simulate a
  small-municipal, farm-pond or custom system, but `run_stress_spectrum` /
  `test_reservoir_infrastructure` have no system argument. A chat answer can therefore
  describe a different system than the Review view. Proposal: carry the selected
  `WaterSystemConfig` identity into saved runs and tools (B16 scope).
- **Custom no-pipeline demand.** The fix removes the silent 554 ac-ft/day. Whether custom
  systems should *collect* a separate no-pipeline demand is a product/domain decision.
- **Rainfall-to-inflow physics.** The linear `ac-ft per mm of mean airport rainfall` has no
  catchment area, losses or routing. It needs calibration before any storage timing is
  interpreted beyond an illustrative experiment. Not changed.
- **B15.4 wording outside the touched renderers.** `basin_core/summary.reservoir_summary`
  (app "Operational Takeaway") still says "Stage 2 restrictions", "voluntary conservation",
  "emergency curtailments". The PDF still has "Conservation Benefit"/"Dominant loss driver"
  cards and "Depletion ~N months (Toy Model)". These interpretations need a reviewed wording
  pass, with no-breach and partial-breach cases (B15.4 remains open).
- **Result keys still say `day_stage3_20` / `survived_critical_20pct`.** The values follow
  the configured band, and every preset uses 40/30/20/15%. The names were kept to avoid
  breaking stored runs and callers.
- **Conservation limits differ by surface:** app 0–30%, model-facing validation 0 or >1–50,
  direct tool 0–100. They are consistent in unit (percentage points) but not in range.
- **Scenario "year" means source start year.** A window starting in late 2010 and running
  into 2011 is not found by "2011". This is stated in the tool, but domain users may expect
  overlap semantics.
- B15.2/B15.3/B18.3 are addressed for the paths listed above. B18.2, B18.4 (misleading
  supplied text, answer-quality evaluation) and B18.5 are not in this task.

## 5. Changed files

`basin_core/analysis.py`, `basin_core/simulation.py`, `basin_core/tools.py`,
`basin_core/assistant.py`, `basin_core/pdf_report.py`, `basin_core/visualizers.py`,
`basin_core/agronomics.py` (label only), `app.py`, `basin_ui.py`,
`scripts/evaluate_routing_quality.py`, `tests/test_assistant.py`, `tests/test_report_config.py`,
`tests/test_numerical_meaning.py` (new), this document.

## 6. Suggested board updates at integration (for Astra)

- B15.2: done for tools, assistant, app Review table and both PDF paths (§1 rows 1–3, 7). The
  100% tier is described as the input rainfall, with its observed multiple where one exists.
- B15.3 and B18.3: done for the listed inputs (§1 rows 5, 6, 9–17, 19). Remaining: legacy
  report arguments, the tools' fixed Region N system, and conservation range differences (§4).
- B15.4: still open (§4).
- Integration note: the threshold version bump invalidates version-1 saved runs (§2).
