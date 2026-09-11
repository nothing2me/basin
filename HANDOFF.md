# BASIN current handoff

Full dated checkpoint history (every prior entry, verbatim) is archived at
[docs/archive/handoff_history_through_2026-09-11.md](docs/archive/handoff_history_through_2026-09-11.md).
This file now carries only the reconciled current status. See `TODO.md` for the live
task board and `docs/status_reconciliation_handoff.md` for how this reconciliation was
done, its evidence, and unresolved contradictions it found.

## Current status — September 11, 2026 (status-reconciliation pass)

Base for this reconciliation: `origin/main` at `5679637145560d7d5ed6b9831255a0877ec699d8`.
This pass is documentation-only; it changed no application code. Distinctions below
follow one convention throughout: **implemented** (code exists), **automatically
tested** (a named test suite exercises it), **device-tested** (run on the actual
presentation laptop, not this development machine), **human/domain-reviewed** (a named
person other than the implementing agent inspected it). No box below claims a level it
hasn't reached — an "implemented, automatically tested" item is not device-tested or
reviewed unless separately stated.

### Merged and current

- **Rainfall scenario workflow (B01–B14).** Generation, ranking, comparison, evidence/
  conflict review, custom-rainfall evidence (persisted, versioned, linked to scenarios,
  included in export under consent), and export/replay verification are implemented and
  automatically tested (full suite below). Practitioner review (B07.1/B07.8/B09.x),
  named independent replay (B04.10), and presentation-device rehearsal (B10.3–B10.5,
  B10.8) remain open — see `TODO.md`'s B-board for exact subtasks.
- **Saved/replayable illustrative simulations (B16) — implemented and automatically
  tested, not device- or human-reviewed.** Contrary to older board wording, this is
  **not** unimplemented: `basin_core/simulation.py` + `basin_core/workspace.py` version
  settings (initial storage, conservation, pipeline, tiers, model/threshold identity),
  link runs to exact scenario revisions, mark a run stale when its scenario or evidence
  changes (`is_current`/`validate_run`), and the export bundle/brief include saved,
  reviewed simulations under their own declared verification scope (schema 2.2: "saved
  simulation baselines, settings, trajectories and inclusive threshold replay"), never
  claiming physical calibration. `tests/test_simulation_contract.py` (16 tests) includes
  negative cases (`test_settings_and_input_changes_require_new_review`,
  `test_replay_detects_changed_results_even_with_rehashed_record`). No named human has
  reviewed the simulation contract or a replayed simulation packet; that gate stays open.
- **Numerical/label meaning across surfaces (B15.2, most of B15.3/B18.3) — implemented
  and automatically tested.** Tier labels, day-0/threshold-inclusive wording, absent-year/
  scenario clarification instead of silent defaults, and cross-surface (tool/assistant/
  app/PDF) agreement are fixed and covered by `tests/test_numerical_meaning.py` (28
  tests) plus a revised 50/50 routing benchmark. **Not done:** B15.4 (operational-sounding
  wording — "Stage 2 restrictions," "Conservation Benefit" cards — outside the touched
  renderers); the assistant's reservoir tools still always use the Region N system even
  when Review has selected a different one; legacy fractional PDF arguments (unused by
  any product path) keep an inconsistent 1.0-vs-1.5 reading; conservation input ranges
  differ by surface (app 0–30%, model 0/>1–50, direct tool 0–100). None of these were
  touched by this reconciliation pass. See `docs/numerical_meaning_handoff.md` §4.
- **PDF renderer selection and disclosure (B17.1–B17.4, B17.6, B17.7) — implemented and
  automatically tested.** Renderer choice (browser vs. BASIN's vector fallback) and any
  degraded fallback are disclosed via `RenderOutcome`, never silently swapped; consent
  (private notes / custom data) is checked identically across the ZIP and both PDF
  renderers, including revocation; Windows deliberately never attempts the browser path
  (a disclosed choice, not a bug) — see `docs/pdf_failure_handoff.md` for why that
  wasn't changed. **Not done:** B17.5 (actual browser/native download, write-failure and
  recovery testing on the presentation laptop).
- **Optional native Qwen runtime (Task 1) — implemented and automatically tested, not
  device-tested.** A hash-locked install/repair path (`scripts/install_native_runtime.py`)
  separates the runtime wheel from model weights, refuses silent online fallback when
  `--wheelhouse` is explicit, and classifies real failure modes (absent, wrong version,
  DLL/VC++ failure, illegal instruction, crash, timeout) rather than a boolean.
  **Not done:** clean-laptop installation, live offline inference/timing/recovery,
  native egress observation, and model license/provenance review — all listed in
  `docs/native_runtime_handoff.md` §8–9 as open, not attempted here.
- **Optional Ollama compatibility helpers (SEC.6/SEC.7/SEC.8) — done; do not repeat.**
  Client pinning, dependency-advisory review and the A-1 fix are complete and merged.
  This does not establish anything about the embedded Qwen runtime above, which is a
  separate, newer code path with its own open gates.
- **Tailored Review focus panel (B13/"Part A") — implemented and automatically tested
  (51 `tests/test_review_preferences.py` cases); light/narrow/keyboard/tutorial
  acceptance is genuinely open, not verified, despite an earlier claim of completion.**
  Four goals exist today (`compare`, `storage`, `operations`, `handoff` — not three), each
  reordering the five Review tabs with `provenance` always leading; a focus is
  presentation-only and provably leaves calculations, ranking, shortlist, revisions and
  export consent unchanged. **The pre-run questionnaire is a separate, additional entry
  point** added in Scenario Builder (`app.py` around the "Analysis Focus (Tailors
  Review)" control on Data Dashboard and the "⚙️ Analysis Focus & Settings" expander in
  Scenario Builder) on top of the original Review-page setup panel — both write the same
  sidecar, and reconciling the two into one place is an open product question, not
  resolved by either task. A follow-up branch (`task/review-acceptance-checks`,
  commit `864d95f`, **not yet merged**) drove the app in a real browser and: confirmed all
  four focuses, Show all tools, Change focus, and navigation persistence work; found and
  fixed two real accessibility defects (light-theme header-logo contrast, and no visible
  keyboard-focus ring on toggle/checkbox controls); and could **not** verify narrow-viewport
  reflow or the Saved-Runs/tutorial popovers in that session (tooling limitation, not a
  product failure — see that branch's own `docs/review_acceptance_handoff.md`, which is
  not present on `main` until it merges). Until that branch
  merges, treat light/dark and keyboard-focus fixes as pending, and narrow-viewport/
  saved-run-reopening/tutorial-target claims as unverified by any human this session.

### Known contradictions this pass found and fixed (documentation only)

- `README.md` said the reservoir experiment's "settings, results and conditional storage
  bands are excluded from saved evidence packets and their verification." That was true
  before P0-C; it is no longer accurate once a simulation is saved and reviewed — see
  B16 above. Corrected in README.
- `docs/claim_inventory.md` (dated 2026-09-07) still listed "Upload comparison results
  enter saved scenarios and the verified ZIP" as **excluded**; B14 (merged well before
  this pass) implements exactly that, with tests. Corrected.
- Several TODO.md checkpoint entries repeated "pin the optional Ollama client" as
  upcoming Task-4 work; that referred to an old numbering scheme (today's Task 4 is UI
  acceptance) and the pinning itself is done under SEC.6/7/8. That checkpoint prose is
  now archived rather than edited in place, since it's dated historical narrative, not a
  live instruction — but it should not be read as current open work.

### Open, unresolved, or needing a team decision (not new — carried forward)

- Practitioner/domain review: B07.1/B07.8 (catchment suitability), B08.B5 (reservoir
  presentation framing), B04.10 (independent packet replay), B09.4–B09.10 (novice/
  practitioner/recipient sessions) — no session has occurred; none may be scheduled on
  the team's behalf.
- Actual-device work (Task 6): clean presentation-laptop install, offline rehearsal
  including the optional assistant and PDF/download paths, native egress observation,
  projector/resolution check, and recovery drill. Nothing above substitutes for this.
- Organizer/format facts still missing, not guessed: finalist presentation length,
  required deck/demo submission mechanism, A/V constraints, and any instructions issued
  after the supplied August 10 materials (B01.7, B01.8, B11.7, B11.12). These are
  explicit open questions for the team, not defaults to assume.
- B19 (one custom-data-driven area model), B20 (geographic views) and B21 (reviewed
  document ingestion) remain entirely proposed; nothing in this pass or in merged code
  implements them. B18.2/B18.4/B18.5 (assistant degraded-state, ambiguous-question, and
  read-only-explanation behavior) remain open.
- Model license/provenance review and the diskcache advisory (inactive-code-path
  rationale, not a named-human risk acceptance) remain unresolved.

### Verification evidence carried forward from the last integration

Tasks 1–3 integration (native runtime + numerical meaning + PDF outcomes/consent) on top
of P0-A–D and the Sept 11 UI/hydrology work: **565 passed, 2 skipped in 572.43s**
(skips: genuine-native-wheel opt-in test, absent Qwen model weights). Snapshot checkout,
offline smoke (`a57f4a988ade`), explicit replay (`implementation_matches_current: true`),
source packaging and install-consistency checks passed. Full detail, including the
individual task branches' own evidence, is in `docs/tasks_1_3_integration_review.md` and
the three task handoffs it cites (`docs/native_runtime_handoff.md`,
`docs/numerical_meaning_handoff.md`, `docs/pdf_failure_handoff.md`) — all preserved,
unedited, and still current. This reconciliation pass did not re-run that suite (it made
no application-code change); see `docs/status_reconciliation_handoff.md` for exactly what
was run instead.

### Next

Task 4 (merge the UI-acceptance branch, or redo its still-open narrow-viewport/tutorial/
saved-run checks), Task 6 (presentation-laptop acceptance — the only remaining gate for
most "not device-tested" items above), and the practitioner/recipient sessions under B09.
Freeze (B12) is blocked until those complete.
