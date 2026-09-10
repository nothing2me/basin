# Tailored Review — implementation handoff

Branch `feat/tailored-review`, based on `origin/main` at
**`e35a57b59c7b076dc94b0ec9281a3393e039e6b1`** (`e35a57b`). Built in the separate worktree
`C:/Users/moham/Documents/GitHub/basin-tailored-review`. Not merged, not pushed.

Implements `docs/tailored_review_proposal.md`. `TODO.md` and `HANDOFF.md` were left
untouched for whoever integrates this.

## What was built

**A short, skippable setup at the top of Review.** Three questions — goal, data, guidance —
in one bordered panel with **Use this focus** and **Skip for now**. Once answered or
skipped it collapses to a one-line focus bar carrying **Show all tools** and **Change
focus**, so it never asks twice for the same run.

**A focus reorders the page; it never removes a tool.** The five Review tabs are split into
a leading row and a `More tools (N)` drawer:

| Goal | Leads with | Under More tools |
|---|---|---|
| Compare rainfall scenarios | Rainfall Deficit & Historical Context, Source Evidence & Daily Values | Storage, Crop/Wildfire, Edit Rainfall |
| Explore an illustrative storage scenario | Storage Drawdown & Water System, Source Evidence & Daily Values | Crop/Wildfire, Rainfall Deficit, Edit Rainfall |
| Prepare a reviewed handoff | Edit Rainfall & Refine Shortlist, Source Evidence & Daily Values | Storage, Crop/Wildfire, Rainfall Deficit |

Every tab body still renders exactly once; the drawer changes where a tab sits, not
whether it exists. `Source Evidence & Daily Values` leads in **every** focus on purpose, so
source identity, cited evidence and stated limitations are never demoted by a display
choice. Skipping setup, or turning on **Show all tools**, restores the original single row
of five.

**Guidance adds, it never subtracts.** "Guided explanations" prepends one orientation
caption per tab. "Technical detail" omits those captions only. Every existing disclosure —
catchment weighting, the historical-comparison caveat, the illustrative-storage warnings,
consent controls — renders identically either way, and a test asserts it.

## Boundaries held

- **Nothing numerical or consensual moves.** Changing focus leaves ranking weights, the
  selected shortlist, scenario statuses/revisions/approved revisions, `ExperimentConfig`
  and the full workspace record byte-identical. Asserted directly by snapshotting
  `w.record(...)` around focus changes.
- **Display state is not in the audited record.** Preferences are written to a sidecar
  `review-prefs-<run id>.json` beside the saved run, never into `Workspace.record()`, so
  toggling a panel cannot change an exported bundle's digests. A test proves the record is
  unchanged by a save.
- **Ranking weights are recommended, never applied.** Each focus names a matching
  `COMMUNITY_PRESETS` entry in a caption and points at Step 2. Nothing in Review reranks.
- **"My rainfall data" never implies an upload.** Choosing it raises "No file has been
  uploaded and no data has been validated", and the focus bar repeats it afterwards. It
  reuses the existing Step 1 upload and Try-an-example flows; no second data path exists.
- **Older saved runs open unchanged.** A run with no preferences file falls back to
  defaults, which show all five tabs. Damaged, empty, partial or foreign preference files
  fall back rather than raise.

## Files changed

| File | Change |
|---|---|
| `basin_core/review_preferences.py` | New. Validated, versioned `ReviewPreferences`, tab layout, sidecar persistence. |
| `app.py` | Import, two helpers next to `switch_page`, the setup panel / focus bar, and the tab list built from the focus. |
| `tests/test_review_preferences.py` | New. 36 tests. |
| `docs/tailored_review_handoff.md` | This file. |

No protected file was touched: `basin_core/assistant.py`, `basin_core/qwen_runtime.py`,
`basin_ui.py`, dependency files, calculation modules, PDF rendering, `TODO.md` and
`HANDOFF.md` are byte-identical to `e35a57b`. The new module lives in `basin_core/`
specifically so `scripts/package_demo.py` picks it up through its existing directory glob —
no packaging change was needed.

## Test results

**Full suite: 391 passed, 1 skipped** (`test_qwen_inference.py:83`, Qwen GGUF weights not
downloaded — expected, and no weights were downloaded). 36 of those are new.

Covered by automated tests: skipped setup shows all five tabs; each of the three focuses
leads with the right tools and keeps the rest reachable; Show all tools; focus survives
navigation away and back; preferences reload from disk for a reopened run; numerical,
ranking and consent state unchanged across focus changes; own-data wording; guidance adds
without removing disclosures; older runs without a preferences file; damaged files.

## Visual inspection

Driven manually against a local instance on `127.0.0.1:8510`, dark appearance:

1. Setup panel — three labelled radio groups with captions, both buttons.
2. "My rainfall data" selected — the "no file has been uploaded / no data has been
   validated" warning appears inline before the focus is applied.
3. "Prepare a reviewed handoff" applied — the tab row collapses from five tabs to two plus
   `More tools (3)`, with the guided note above the tab content.
4. `More tools (3)` expanded — the other three tabs present and usable, with "Nothing here
   is disabled, and your work is unchanged."
5. Focus bar — summary line, Show all tools toggle, Change focus button, the own-data
   reminder and the ranking-preset advisory.

## Not verified — read this before claiming coverage

- **No user validation.** Everything above is automated tests plus one operator clicking
  through. The proposal's "short sessions with intended users" has not happened, and
  nothing here substitutes for it.
- **Light appearance not visually confirmed.** The Settings popover did not open under
  automation, and starting Streamlit with `--theme.base light` is overridden by BASIN's own
  appearance layer. Structurally the new UI uses only `st.container(border=True)`,
  `st.radio`, `st.caption`, `st.warning`, `st.toggle`, `st.expander` and `st.columns` with
  **no hardcoded colours**, so it should inherit whatever the appearance layer sets — but
  that is reasoning, not an observation. Worth a two-minute manual check.
- **Narrow-screen layout not confirmed.** Resizing the browser window did not change the
  captured viewport, so the three-column setup panel was only seen at full width. It will
  stack under Streamlit's normal column behaviour, but that was not observed. The setup
  panel is the only new multi-column layout.
- **Keyboard access not tested.** No tab-order or focus-ring inspection was performed.
- The default `Compare rainfall scenarios` and `Explore an illustrative storage scenario`
  focuses were exercised by automated tests but not viewed on screen; only the handoff
  focus was inspected visually.

## Integration notes

- **Placement.** The setup panel sits at the top of the Review page rather than before run
  creation. Noah's phrasing was "before a run", but run creation lives in Scenario Builder
  and touching it risks the calculation path this task is meant to leave alone. The panel
  appears the first time a run reaches Review, which is where the clutter is. Moving it
  earlier is a small change if the team prefers it.
- **No protected file needs changing** for this to work as built.
- If a future focus should carry ranking weights rather than recommend them, that belongs
  in Scenario Builder with an explicit apply action, not in Review.
