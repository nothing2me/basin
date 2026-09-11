# Review acceptance handoff

## Identity

- Release base: `d88650ae13aaa1da9787927b5f4fa0845cec786e`
- Date and platform: September 11, 2026; Windows; Codex in-app Chromium browser
- Application: local Streamlit server at `http://127.0.0.1:8504/`
- Browser sizes inspected: default desktop **1280 × 720** and explicit narrow viewport **375 × 812**

## Browser results

| Check | Result | Evidence observed |
|---|---|---|
| Optional example setup | Pass | `Try an example` opened Review with the three-question optional setup and retained access to the scenario decision surface. |
| Comparison focus | Pass | Primary tabs were Rainfall Deficit and Source Evidence; three other tools remained under `More tools (3)`. |
| Storage focus | Pass | Primary tabs were Storage Drawdown and Source Evidence; storage experiment remained opt-in. |
| Agronomics focus | Pass | Primary tabs were Crop Irrigation & Wildfire Risk and Source Evidence; ETc and KBDI remained accessible as nested tabs. |
| Handoff focus | Pass | Primary tabs were Edit Rainfall and Source Evidence. |
| Show all tools | Pass | All five Review tools appeared in one tab row and the selected focus remained unchanged. |
| Skip setup | Pass | A fresh browser session displayed all five tools and explicitly reported `Showing all Review tools (setup skipped)`. |
| Change focus | Pass | Focus label, primary tabs and guidance changed together. Scenario `B-209`, revision 1 and `0 of 6` review decisions remained unchanged during presentation-only changes. |
| Saved-run reopening | Pass | Reopening the newest saved workspace restored `Prepare a reviewed handoff`, the selected scenario and Show all tools state. |
| Tutorial target | Pass | The tutorial advanced to Step 5, enabled storage exploration, exposed the storage tab, and focused `tour-review_simulation`. |
| Keyboard focus | Pass | Tab navigation visibly focused the Units combobox at desktop and narrow sizes. |
| Dark desktop | Pass | Header, controls, focus panels and logo were readable at 1280 × 720. |
| Dark narrow | Pass | Navigation stacked without horizontal page overflow at 375 × 812; the five-tab strip provided its scroll control. |
| Light narrow | Pass after fix | The header logo was initially nearly invisible. A fixed dark backing now preserves logo contrast while the remainder of the page stays in the native light theme. |

## Changes

- `basin_theme.py`: give the white bitmap header logo a fixed dark backing, padding and radius so it remains visible in Light, Dark and System appearances.
- `app.py`: describe the tutorial storage model as a `storage-balance experiment`; the selected preset may contain one or multiple pools.

## Automated checks

- `pytest tests/test_review_preferences.py tests/test_app.py tests/test_ui_improvements.py`: 60 passed; `test_full_user_workflow` hit its 60-second AppTest timeout while the live Streamlit browser server was running.
- After stopping the live server, `pytest tests/test_app.py::test_full_user_workflow`: **1 passed in 51.87s**.
- The release base previously passed the complete suite: **554 passed, 3 skipped**.

## Limits and next action

This is browser acceptance on the current Windows machine, not the separate presentation laptop and not intended-user validation. No private notes were entered, no scenario was accepted or excluded, no export consent was changed, and no download was performed. The next ordered work is status/documentation reconciliation, followed by the physical presentation-laptop and intended-user checks that require the user or team.
