# Task 4 handoff — Tailored Review visual and interaction acceptance

Worktree: `C:\Users\moham\Documents\GitHub\basin-review-acceptance`
Branch: `task/review-acceptance-checks`
Base: `origin/main` at `5d83fcd8985506399bdee5a056f4040a7a22dca6` (not merged, not pushed)

## Task-premise correction (read this first)

The task brief I was given says the tailored-focus panel "is currently at the top of
Review, not before run creation" and instructs me not to move it in this task. That
matches `docs/tailored_review_handoff.md` (the original implementation) but **not** the
code at this branch's base commit. Between that original implementation and `5d83fcd`,
someone else's work ("September 11 — Part A: Tailored Workflow & Review Interface" in
`HANDOFF.md`) already added a second, earlier entry point: an "⚙️ Analysis Focus &
Settings (Optional)" expander in Scenario Builder (`app.py:1205`), *in addition to* the
original Review-page setup panel (`app.py:1450`), both writing the same
`ReviewPreferences` sidecar. The repository's own current copy of this task's brief,
`docs/next_tasks/04_review_acceptance.md`, already reflects this ("Tailored focus is
selected in Scenario Builder before run creation, with a Review-side fallback for older
runs") — it does not contain the "do not move it" sentence my copy of the brief has.

I treated the current repository state and `docs/next_tasks/04_review_acceptance.md` as
authoritative per the standing instruction to treat older claims as historical until
supported by current evidence, and per "read repository instructions... before editing."
**I did not move, remove, or consolidate either entry point.** I audited what exists today
(both entry points, four focuses, not three — `compare`, `storage`, `operations`,
`handoff`, per `basin_core/review_preferences.py:22`) rather than the three-focus,
Review-only design the older docs describe. Reconciling the two entry points (the
Scenario-Builder one and the Review one now overlap in purpose) is a product decision I'm
flagging for Astra, not something I resolved here.

## What I verified in a real browser, and how

Launched the app from this worktree (`streamlit run app.py --server.port 8611
--server.headless true`, `BASIN_SESSION_DIR` pointed at a throwaway temp directory so no
real local session data was touched) and drove it with the Claude-in-Chrome browser tools
against "Browser 2" (the other connected browser, "Browser 1", could not reach
`127.0.0.1` at all — every navigation on it returned an error page; this is recorded, not
silently worked around).

- **All four focuses** (`Compare rainfall scenarios`, `Explore an illustrative storage
  scenario`, `Assess agricultural & wildfire risk`, `Prepare a reviewed handoff`): each
  applied from the Review-page setup panel leads with the tabs
  `basin_core/review_preferences.py`'s `FOCUS_PRIMARY` maps it to, `Source Evidence &
  Daily Values` leads in every one, and the rest land in a `More tools (N)` expander that
  actually contains the other tabs and renders their content. Confirmed by screenshot for
  each of the four.
- **Skipped setup**: clicking "Skip for now" shows all five tabs in one row.
- **Show all tools**: toggling it while a focus is active shows all five tabs in canonical
  order without discarding the configured focus (the focus summary line stays correct
  underneath).
- **Change focus**: reopens the setup panel pre-filled with the currently saved
  goal/data/guidance (confirmed the previously-applied focus's radio button was still
  selected), and offers Cancel in addition to Use this focus / Skip for now.
- **Navigation persistence**: Data Dashboard → Export → Review preserved both the active
  focus and the Show-all-tools toggle state.
- **Export eligibility/consent unaffected by display changes**: after repeatedly toggling
  focus and Show-all-tools, the Export page still showed "Export verified: All shortlisted
  candidates are reviewed and ready for bundle generation" once accepted, with the same
  Experiment Configuration table (48% storage, 0% conservation, pipeline available,
  100/80/60/40 tiers — BASIN's defaults, correctly labelled as defaults). This is also
  covered by the existing automated test
  `test_changing_focus_changes_nothing_numerical_or_consensual`, which I re-ran (see
  below); I additionally drove the real export flow by hand to see it, not just assert it.
- **Light and dark appearance**, desktop viewport (this machine's actual resolution,
  2560×1271 — see the viewport-size note below for why I couldn't also get a narrow one):
  Verified by relaunching Streamlit with `--theme.base light` and, once I found that a
  stale `stActiveTheme-/-v2` value in the browser's `localStorage` overrides the server
  flag (Streamlit remembers the last theme choice per-origin), clearing it so the light
  theme actually took effect. Screenshotted the setup panel, the applied-focus bar, the
  tabs, and the warning/caption text in both themes — all legible in both.
- **Keyboard-only access and visible focus**: clicked once into the page body, then used
  only Tab/Shift+Tab/Arrow keys/Enter from there. Confirmed visible focus rings on: the
  units selector, all four top-nav buttons, the goal/data/guidance radiogroups (arrow keys
  moved the selection with a visible highlighted row), and the Use this focus/Skip for
  now/Change focus/Cancel buttons. Activated "Use this focus" with only the Enter key and
  watched the page reconfigure correctly.

## Defects found and fixed (both in `basin_theme.py`, CSS only — no Python/logic changed)

1. **BASIN wordmark invisible under the light theme.** `.basin-top-logo-wrap` (the header
   logo used on every page, including Review) had no background, so the light-colored logo
   artwork disappeared against a light page background — confirmed by screenshot
   (essentially blank). The sidebar's own copy of the same logo already carries a
   `background:#20292E` chip for exactly this reason (`basin-theme.py`'s pre-existing
   `.basin-brand img` rule); I gave the header wrapper the same treatment. Verified fixed
   in light theme by screenshot; unaffected in dark theme (also screenshotted).
2. **"Show all tools" toggle had no visible keyboard focus indicator.** Tabbing to it
   (confirmed via `document.activeElement` that the toggle's `<input type="checkbox"
   role="switch">` really had focus) produced no visible ring at all — a real
   keyboard-accessibility gap, since sighted keyboard users had no way to tell the control
   was focused. Root cause: the file's existing `button:focus-visible,a:focus-visible`
   rule only covers `<button>`/`<a>`, and Streamlit's toggle/checkbox is neither. Added
   `[data-testid="stCheckbox"]:has(input:focus-visible),[data-testid="stRadio"]:has(input:focus-visible){outline:...}`,
   matching the existing button/link treatment. Verified visible in both dark and light
   theme by screenshot after the fix, and confirmed no double-outline/visual clash on the
   already-working radiogroups.

Both fixes are CSS-only and scoped to the exact elements involved; neither touches
`review_preferences.py`, `app.py`, or any calculation/consent path. I did not find, and
did not go looking to invent, any other layout/focus/persistence defects beyond these two.

## What I could not verify, and why (tooling limitations, not inferred as passing)

- **Narrow viewport.** `resize_window` had no effect in this browser session: I confirmed
  this both on the app and, as a control, on `https://example.com` in a fresh tab —
  `window.innerWidth`/`innerHeight` stayed at the full 2560×1271 desktop size after
  requesting 900×700, 500×850, and 420×850. This browser's window appears to be
  fixed/maximized at the environment level and does not respond to resize requests from
  the extension, regardless of the target page. I also tried a CSS-zoom-based workaround
  (`document.documentElement.style.zoom`) as a substitute for a real resize: it visibly
  magnifies content, but does **not** change `window.innerWidth`, so it never triggers
  Streamlit's own column-stacking logic (verified: the setup panel's three columns stayed
  side-by-side even at 600% zoom). I therefore did not obtain a genuine narrow-viewport
  screenshot this session and am not inferring a pass from the standard `st.columns()`
  usage — I only confirmed by reading `app.py` that the setup panel and other new layout
  use plain `st.columns()`/`st.tabs()` with no fixed pixel widths, which is what Streamlit
  itself stacks responsively, and is the same mechanism already used elsewhere in this app.
  **This is the same gap the original implementation's handoff (`docs/tailored_review_handoff.md`)
  already flagged as unresolved** ("Narrow-screen layout not confirmed... resizing the
  browser window did not change the captured viewport"). I was not able to independently
  confirm the later claim in `HANDOFF.md` ("verified across desktop (1280px) and narrow
  viewports (375px/640px)") — I'm not asserting that claim is wrong, only that I could not
  reproduce or corroborate it myself this session, for the reasons above.
- **`st.popover` menus ("Saved Runs", "Settings") do not open under this browser-automation
  session.** Clicking the trigger button (verified via multiple approaches: direct click,
  clicking by accessibility-tree reference, and a keyboard Enter after focusing it)
  produces no visible change and no new interactive elements in the accessibility tree.
  This matches what the original implementation's handoff already reported for the
  Settings popover specifically ("did not open under automation"); I additionally found it
  applies to the Saved Runs popover. Root cause not identified (no console errors were
  logged). This blocks two of the requested live-browser checks:
  - **Reopening a saved run** through the Saved Runs menu.
  - **Tutorial targets**, since restarting the tutorial is also inside the (equally
    unreachable) Settings popover, and the only other tutorial entry point
    (`"Take interactive walkthrough tour"`) is on the welcome screen, which only appears
    with no active workspace — reachable, but doing so tears down the workspace I was
    using for the other checks, and I still could not exercise the *reopening* case this
    way since that's specifically the saved-run-from-disk path.

  Both of these remain verified only by the existing automated test suite (which I ran and
  which passed — see below), not by first-hand browser observation this session:
  `test_focus_survives_navigation_and_is_persisted_for_reopening` (loads
  `ReviewPreferences` back from a sidecar file for a workspace re-created from a fresh
  `Workspace.load`) and `test_tutorial_step5_auto_expands_storage_in_more_tools`.

## Manual checklist for anything left (exact steps)

Run these on an actual machine/browser that can resize its window and open Streamlit
popovers (i.e., not this session's automation environment):

1. **Narrow viewport.** Open BASIN in a normal desktop browser, generate an example run,
   reach Review, resize the browser window down to roughly 640px and then 375px wide (or
   use DevTools' device toolbar, Ctrl+Shift+M). Confirm the "Set up this Review" panel's
   three columns stack vertically without overlapping text or cut-off buttons, and that
   the post-setup focus bar (summary text, Show all tools, Change focus) wraps sensibly
   instead of clipping.
2. **Reopening a saved run.** Generate a run, apply a focus (e.g. "Prepare a reviewed
   handoff"), let it save (any action that calls `save(w)`, e.g. accepting a scenario).
   Click "Saved Runs" in the header, select that run, click "Open run". Confirm the
   reopened workspace shows the same focus and tab layout as when it was saved, not the
   default.
3. **Tutorial targets.** Click "Take interactive walkthrough tour" from the welcome screen
   (no active workspace), or "Start tutorial" from Settings. Step to the Review stage
   (Step 5/6) and confirm the "More tools" expander auto-opens when the tour is pointing at
   the storage tool and that tool has landed in the secondary group, and that the
   highlighted target actually outlines a real control (not empty space).
4. **Settings popover on the actual device.** Since I could not open it here at all, do a
   basic smoke check that clicking "Settings" opens the appearance picker and it does not
   throw an error, independent of anything in this task.

## Commands run and results

```
git rev-parse origin/main
# 5d83fcd8985506399bdee5a056f4040a7a22dca6

git worktree add -b task/review-acceptance-checks ../basin-review-acceptance origin/main

# Focused re-run after the two CSS fixes:
.venv/Scripts/python.exe -m pytest -q tests/test_review_preferences.py tests/test_app.py tests/test_ui_improvements.py --basetemp=tmp/pytest
# 61 passed in 125.66s

# Full suite after the two CSS fixes:
.venv/Scripts/python.exe -m pytest -q --basetemp=tmp/pytest
# 466 passed, 1 skipped in 456.16s   (1 skip is the pre-existing Qwen-weights-absent skip)
```

(`.venv` is the main checkout's shared virtualenv at
`C:\Users\moham\Documents\GitHub\basin\.venv`; invoked with this worktree as the working
directory, matching the pattern used by other task worktrees in this repo. No CSS-only
change can be meaningfully pinned by `AppTest`, which doesn't render real CSS, so I did not
add a test for either fix — the evidence is the browser screenshots taken this session.)

I did not run `scripts/demo_smoke.py` or `scripts/replay_bundle.py`: this task touched
display/CSS only, not the export/replay/audit path.

## Files changed

- `basin_theme.py` — two CSS-only fixes described above.
- `docs/review_acceptance_handoff.md` — this file (new).

Not edited: `TODO.md`, `HANDOFF.md`, `app.py`, `basin_core/review_preferences.py`, any
calculation module, chart/visualization code, or the export/audit schema. No expert
approval, participant feedback, organizer requirement, or additional manual check beyond
what's described above is claimed anywhere in this handoff.
