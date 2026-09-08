> Publication checkpoint: the user authorized publishing this UI foundation on 2026-09-07. Earlier “local” notes below describe development checkpoints. The foundation checklist still identifies unfinished modeling and validation work.

# BASIN usability research and simplification proposal

Date: 2026-09-07. Scope: research and design proposal, not an implemented redesign. Owner: analyst workflow / B05, B09, B11. Keep private conversation excerpts out of published artifacts; this document records anonymized findings only.

## 1. Main finding

BASIN exposes its mechanisms before establishing the user's purpose. New users face station selection, multiple durations, onset months, retention, reduction extent, candidate count, shortlist size and a seed, followed by ranking and diagnostics. The intended reward—a clear, traceable result and a useful packet—is not the strongest part of the initial experience.

Simplification should change task hierarchy and timing, not merely colors or the number of captions. Preserve analytical depth behind clear, task-specific detail controls. Make the first useful result reachable with a prepared example and one clear action. Then let users inspect assumptions, alter inputs and trace evidence.

## 2. Research method and limits

Reviewed first-party product/design documentation for Google, Linear, Stripe, GitHub, Notion, GOV.UK and Our World in Data, plus NN/g usability research and W3C accessibility guidance. These are selected prominent or particularly relevant services, not a verified world traffic ranking or proof that popularity is caused by their interface. Marketing pages, search experiences and analytical workbenches have different goals.

Inspected BASIN's current app.py, basin_ui.py and theme code, and the existing browser tab's accessibility tree and screenshot. The browser was on a populated, scrolled Workspace and showed a pending file-change notice, so its pixels are not a guaranteed rendering of the newest branding commit. Source inspection corroborates the structural findings. No user session was changed, generated or discarded for this review. This is not a complete responsive/accessibility audit or a fresh expert usability test.

The supplied chat describes one informal novice observation plus teammate reactions. Reported confusion, exploratory clicking and interest in notes are useful signals, not a statistically representative study. Suggested interpretations below are hypotheses to test. Do not claim that an analyst would necessarily struggle in exactly the same way.

## 3. What strong products teach us

| Reference | Documented pattern | BASIN application | What not to copy |
|---|---|---|---|
| Google | Its stated philosophy prioritizes users, speed and simplicity. | Organize the entry around the user's question and first action. | A blank search box that implies BASIN can answer arbitrary water questions. |
| Linear | Its 2026 refresh reduces competition from navigation and decorative structure while preserving work density. | Quiet the sidebar and borders; keep the current task and next action prominent. | Low-contrast text or icon-only controls that novices cannot recognize. |
| Stripe Dashboard | Search gives quick results, then expanded views and advanced filters. | Show a concise scenario summary first; expose filters and technical columns on demand. | Financial-dashboard conventions that do not match rainfall tasks. |
| GitHub | The command palette provides optional fast navigation for experienced users. | Keep expert shortcuts available without putting every action on screen. | Making a command palette the only way to find a feature; unnecessary for the first redesign. |
| Notion | Database views and page-opening modes support different representations of the same content. | A closable notes/details panel can preserve context beside a chart. | Several competing sidebars or a complex workspace builder. |
| GOV.UK | Clear task flows, plain language and a dominant main action support first-time success. | Verb-based actions and concise explanations next to decisions. | Turning back-and-forth scientific exploration into a rigid wizard. |
| Our World in Data | Charts connect to reusable data, metadata and source documentation. | Pair an understandable chart with inspectable evidence and a useful download. | Assuming a polished chart establishes scientific accuracy. |

Sources: [Google philosophy](https://about.google/company-info/philosophy/), [Linear refresh](https://linear.app/now/behind-the-latest-design-refresh), [Stripe search](https://docs.stripe.com/dashboard/search), [GitHub command palette](https://docs.github.com/en/get-started/accessibility/github-command-palette), [Notion views](https://www.notion.com/help/views-filters-and-sorts), [GOV.UK service simplicity](https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use), [OWID data reuse](https://ourworldindata.org/easier-to-reuse-our-data).

These products are distinctive through consistent interaction and useful outcomes as well as visual identity. My inference for BASIN: trustworthy evidence, comprehensible comparisons and a well-organized packet should be the distinctive experience. Animation is optional supporting feedback.

## 4. Principles supported by usability guidance

**Progressive disclosure:** put frequent, necessary choices first; expose specialized controls through a clearly labeled secondary surface. Do not hide everything in nested accordions. [NN/g](https://www.nngroup.com/articles/progressive-disclosure/).

**One dominant action:** avoid several equally emphasized calls to action in the same decision context. Secondary navigation and undo can remain visible. This is a hierarchy guideline, not a literal one-button-per-page law. [GOV.UK button guidance](https://design-system.service.gov.uk/components/button/).

**Contextual help:** instruction is more useful when the user encounters the relevant task. A tour must be optional, short and connected to actual controls; it cannot compensate for an unclear task flow. [NN/g onboarding research](https://www.nngroup.com/articles/onboarding-tutorials/).

**Scrolling:** prioritize the initial viewport, but permit readable continuation. Banning vertical scrolling can create cramped controls, hidden content or multiple competing scroll regions. [NN/g scrolling research](https://www.nngroup.com/articles/scrolling-and-attention/). Accessibility reflow aims to avoid unnecessary two-dimensional scrolling at narrow equivalent widths; genuine data tables/charts have specific exceptions. Do not use fixed screen heights to conceal overflow. [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html).

## 5. BASIN-specific audit

| Finding | Evidence | Priority / recommendation |
|---|---|---|
| Setup competes with the current result | New run contains eight setup concepts; ranking expands on Workspace. Browser showed generation controls beside charts and a dense table. | P0: move setup into a deliberate Create scenario flow; keep current settings summarized on results. |
| The first-use action emphasizes learning the interface | Welcome/tour and sidebar generation are separate entry paths. | P0: primary Try an example; secondary Use my data; Open saved analysis as a quiet action. |
| Tables expose jargon and redundant units | Visible columns include group, profile, score, deficit mm/in, concurrence and percentile. | P0: initial table shows scenario description, period, rainfall difference and review state. Keep full columns available. |
| Notes are useful but buried | Private notes is a sidebar expander, available only with a workspace. | P1: persistent Notes entry, desktop side panel and explicit save state. Preserve private default. |
| Appearance is hidden low in settings | appearance_picker is inside Settings after Saved runs. | P1: top-level labeled Appearance control with System/Light/Dark. |
| Tour explanation and target are separate | render_tour_guide appears separately; target has outline/anchor and a Go to highlighted area link. | P1: task-local instruction; open correct surface, reveal target and position help next to it. |
| Part B adds more vertical content to Data | Upload and reference comparison live before the public station overview. | P0: give My data its own task surface; do not append every feature to one screen. |
| Multiple exports mean different things | Comparison JSON and scenario ZIP have different verification scopes. | P0: name and preview each distinctly; never imply both are equivalent reviewed packets. |
| Experiment can distract from accepted scope | Reservoir view is alongside rainfall chart modes. | P0: move to clearly marked Experiments or exclude from the novice route; do not sell it as the primary validated result. |

Code locators: app.py functions local_rainfall_preview, uploaded_reference_comparison, render_tour_guide and tour_target; sidebar generation/ranking blocks; basin_ui.py evidence_panel/comparison_panel. These are inspection findings, not code changes made in this pass.

## 6. Decisions on the team's suggestions

### Keep and refine

- Appearance near the top: make the label and current choice visible without taking over the header.
- Notes beside the analysis: a closable panel, not a permanently cramped third column. At narrow widths it can become a full-width task view. Preserve drafts across navigation, show saving/saved/error states and offer recovery after a failed save.
- Tutorial next to its target: reveal the correct page/expander first, then place help where it fits without covering the control. Move focus predictably; Escape/Skip/Back must work. If positioning is unreliable in Streamlit, prefer an inline instruction immediately above the control over brittle DOM overlays.
- Fewer competing buttons: reserve strong styling for the next meaningful step. Secondary options remain discoverable but quieter.
- Better export: preview the actual artifact before download; explain what it contains and what was not verified.

### Adjust rather than adopt literally

- **No scrolling:** replace with “the current question, principal chart/result and next action are easy to find.” Test a typical laptop and zoomed/narrow layouts. Permit vertical reading; avoid trapped nested scroll areas.
- **No hamburger anywhere:** visible labeled navigation is preferable for BASIN's few desktop destinations. On a narrow device, a clearly labeled Menu can be reasonable. The user task matters more than banning an icon.
- **Notes automatically exported:** do not silently switch existing private annotations into shared content. Proposed split: Private notes plus an explicitly chosen Report summary. Let a user promote selected text, show exactly what will be included, and require review. Automatic linking of a note to its scenario is different from automatic disclosure in an export.
- **Remove subtext:** remove repetitive/pitch/implementation narration, but keep essential units, reference basis, incomplete coverage and warnings where they affect interpretation. Expandable “How calculated” can hold full detail.
- **Wow factor:** demonstrate useful understanding, not a spectacle. A newcomer should see what happened, what it means within scope and what to do next.

These chats are stakeholder proposals, not authorization to change export privacy defaults or proof of customer requirements.

## 7. Proposed information architecture

Use one product and one data model with two levels of detail. Avoid a separate beginner engine and expert engine, which can drift scientifically.

### Entry

Headline: **Explore rainfall evidence for your area.**

Supporting sentence: **Compare observations, explore drier rainfall scenarios, and prepare a source-backed report.**

Primary: **Try an example**. Secondary: **Use my data**. Quiet link: **Open saved analysis**. Explain once that BASIN does not forecast water supply. Expert users may open full analysis directly.

### Main workspace

Suggested labeled destinations: **My data · Scenarios · Review & report**. Keep global navigation separate from the current task's controls. Appearance, Notes and Help sit in stable locations.

Within a task: a plain-language question, a short answer/status, one main visualization, the next meaningful action, and a details area. Analyst controls remain available through clearly named sections such as Scenario settings, Ranking priorities, Source details and Full table. Do not put every advanced feature under one vague gear.

Layout concept, not a fixed-height requirement:

```text
BASIN       My data | Scenarios | Review & report     Appearance  Notes

Compare your rainfall with a reference
30 matching days | Reference: Corpus Christi | Regional proxy

[ Main daily-rainfall chart                         ] [Notes, if open]
[ Result in plain language + limits                 ]

Source details     View data table                 Review comparison
```

Guided progression should help a novice, while a trained analyst can revisit data and settings without replaying a wizard. Preserve unsaved work across navigation and distinguish edits from regeneration.

## 8. First meaningful result and report experience

Use the supplied illustrative June 2024 local example only with a clear illustrative label. It totals 62.5 mm. The bundled Corpus Christi comparison total previously checked is 182.8 mm for the same month. Thus the example differs by -120.3 mm (about -65.8%) on a complete paired interval. Recompute from current pinned inputs before using these numbers in a live demo. This does not establish an observed regional drought: the upload is unverified, and a nearby reference is not a validated local normal.

Suggested result structure:

- **What was compared:** uploaded example and selected public station, on the same valid dates.
- **What differs:** signed rainfall difference and coverage, with a chart.
- **What that means:** descriptive comparison between the specified records.
- **What remains uncertain:** source authenticity, location/day-basis suitability and any missing data.
- **Next action:** review the comparison or inspect a supported rainfall scenario.

A report preview should show title/question, data window, selected scenarios, main findings, charts, citations, assumptions, unresolved issues and inclusion controls. Plain summary first; detailed tables and reproducibility files second. A download should feel like the understandable conclusion of the work, not an unexplained ZIP button. Do not call the comparison JSON a verified scenario packet or turn policy targets into predicted savings.

## 9. Plain-language labels to prototype

| Current | Proposed main label | Detail retained |
|---|---|---|
| Generate | Create rainfall scenarios | Historical windows and scaling method |
| Rainfall retained | Rainfall compared with original (%) | 60% means multiply selected rainfall by 0.60, not retained reservoir water |
| Onset months | Starting months | Historical calendar basis |
| Candidates | Scenarios to generate | Advanced setting |
| Seed | Repeatable run seed | Advanced reproducibility setting |
| Deficit mm | Rainfall shortfall from reference (mm) | Per-station clipping/averaging and named reference |
| Concurrence | Overlapping dry periods | Definition and single-station special case |
| Reference percentile | Position among historical comparisons | Percentage of matched deficits smaller than or equal; not probability |
| Approval invalidated | Rainfall changed — review again | Previous approval applies to an older revision |
| Build verified export | Review and download packet | Exactly what replay checks and excludes |

These are proposed labels, not a license to alter calculations. Same-date uploaded-minus-reference difference must not be renamed a climatological deficit.

## 10. Delivery order and acceptance

1. **Stop adding new visible controls temporarily.** Stabilize one novice workflow and retain current regression coverage. This is a recommendation to reprioritize UI work, not abandonment of Part B's evidence integration.
2. **Prototype first-use and result hierarchy locally.** One example path, top appearance access, quiet navigation, focused settings, representative report preview.
3. **Test before rewriting every screen.** Use the same task with the current app and the prototype; counterbalance order where practical to reduce learning effects.
4. **Implement the shell and disclosure.** Preserve settings, scenario revisions, source identity, evidence and privacy contracts. No numerical changes required for most simplification.
5. **Add notes and local help carefully.** Verify save/error behavior, focus, zoom, narrow layout and export inclusion.
6. **Refine report/persistence integration.** Resume Part B linkage under the clearer workflow, then update guides and only afterward record the demo.

Suggested first test group: 3–5 newcomers for orientation and 2–3 domain-informed participants for analytical work, subject to availability. These small rounds reveal usability issues; they do not estimate population success rates or validate the hydrology.

Tasks: explain the app after 30 seconds; reach an example result without coaching; identify what a rainfall difference does not mean; find and save a note; change an assumption and recognize re-review; identify exactly what an export includes. Analysts additionally check citations, reference coverage, unavailable comparisons and reproducibility.

Proposed acceptance targets, not measured results: most participants find the first action within 15 seconds; a prepared example is understood within 2 minutes; no participant mistakes the output for a water-supply forecast; every participant can identify private versus exported notes. Record raw outcomes, wrong turns, requests for help and quotes, not only likes/dislikes. Treat a failure of the forecast/privacy understanding tasks as a release-blocking design issue for that flow.

Check keyboard navigation, visible focus, text contrast, light/dark/system behavior, reduced motion and zoom/reflow. Use a 1366×768 laptop viewport as one test condition, not the only supported size. Never shrink text to force all content into one frame.

## 11. Immediate recommendation

Build the guided example and result/report preview before adding another advanced panel. Keep analytical controls accessible, but reveal them when a person knows what question they are changing and why. Preserve the current source/evidence integrity work; make its value visible in a simpler result.

No app, privacy setting or calculation changed during this research pass. This document is a local proposal for team review; no private chat transcript is copied into it. An accessibility assessment, authenticated walkthroughs of the reference products and measured novice/expert usability outcomes remain outside this review's evidence.


## Implemented first polish pass — 2026-09-07

Owner: BASIN interface work. Kept local for review.

- First use now offers Try an example, Use my data, and an optional tour. Detailed observations and uploads live on Data instead of filling the welcome screen.
- The deterministic example opens the first shortlisted scenario in Review (300 candidates, six shortlisted, seed 22). It does not approve scenarios or bypass export review.
- Appearance is near the top of the sidebar. Native Light/Dark/System choices remain browser-persisted. Neutral surfaces and one muted blue accent reduce competing emphasis; the white logo has a dark backing in both themes.
- Scenario settings and ranking controls start collapsed, except when the tutorial targets them. Starting months and rainfall percentage labels use plainer language.
- Workspace emphasizes shortlist and approval counts, with a single main scatter chart. Score composition is expandable. Group numbers no longer use a continuous color scale that might imply risk. Scores are explicitly described as priorities, not likelihood or safety.
- Upload comparison, calculations, private-note consent and verified export contracts are unchanged.

Validation: existing full suite 105 passed after first-use changes; all three application tests passed again after workspace simplification, including a new first-use test proving the example stays unapproved and export remains locked. The upload UI test now explicitly visits Data. Browser inspection verified the welcome screen and working Light/Dark controls on a fresh server at localhost:8502. Configured main text contrast is 11.75–14.81:1; primary white labels are 6.68:1. These checks are not a complete accessibility audit.

Next: test this starting point with newcomers; refine the detailed Review screen and report preview, move tutorial guidance adjacent to targets, and consider a persistent notes surface while keeping export opt-in. A future custom appearance panel should offer a small set of contrast-tested palettes and reset-to-default, preserve semantic chart colors, and avoid exposing raw color pickers in the primary workflow. Full mobile/zoom/keyboard and practitioner validation remain open. Part B evidence linkage remains separate and unfinished.


## Custom appearance and guided navigation — 2026-09-07

Added a session-scoped accent color picker, reset control and color-blind-friendly chart toggle in Appearance. Native light/dark/system preferences still persist in the browser. Custom accents apply to primary buttons, selected tags/navigation and the welcome panel; their label color selects the higher-contrast black/white choice. Chart colors remain independently meaningful. Light mode uses pale blue-gray backgrounds with stronger panel separation. The full-width logo retains its dark backing for readability.

Color-blind-friendly charts use distinct colors plus line dashes, marker shapes and bar patterns, including reservoir animation frames. This is an accessibility aid, not a guarantee for every type of color vision deficiency; user testing remains needed. No data, scores, approval state or export privacy behavior is changed by appearance controls.

Tutorial instructions now render inside the target area. Each navigation step automatically reveals containing expanders, scrolls the target into view and focuses its anchor. A bounded DOM observer handles delayed rendering and disconnects afterward. Repeated widget edits do not continually steal focus. Manual navigation retains Return to this step. Sidebar guidance is compact so controls remain reachable. The manual jump link is removed.

Verification: 24 application/upload tests passed, including custom accent reset, color-blind reservoir rendering, unchanged scores/status, the seven-step tutorial and export approval gate. Browser verified automatic navigation/focus to Data and scrolling into the sidebar generator. Preview uses localhost:8503 so existing in-memory sessions on earlier ports are preserved. Full mobile, zoom and color-vision user validation remain open. Changes remain local.


## Three-color Apply workflow and review readability — 2026-09-07

Appearance now offers Button color, Selected option color and Sidebar accent color in a form. Edits remain drafts until Apply colors; Reset restores all three defaults. Color-blind mode is one immediate on/off toggle for interface accents and chart styling; turning it off restores the applied custom palette. It does not recolor scientific status messages or change their meaning. Choices remain session-scoped. Native Light/Dark/System is still browser-persisted.

Renamed the Data uploader section to “Upload and observe your custom CSV.” Reduced the welcome heading size and panel tint. Browser testing exposed clipped Review metrics/buttons at an 887px window: Review now has two main metrics, expandable reference/ranking details and full-width chart and decision sections. Removed the green delta treatment on the inches conversion because a unit conversion is not an improvement.

Verified 24 application/upload tests with `.venv/Scripts/python.exe -m pytest tests/test_app.py tests/test_uploads.py -q --basetemp=tmp/colors-review-layout-0907 --tb=short` and `git diff --check`. Tests cover draft-versus-applied colors, reset, color-blind reservoir rendering and approval invariants. Browser confirmed the light-mode scenario chart renders with color-blind mode enabled and visibly different line styles. Latest local preview remains localhost:8503; select Rerun for pending file changes. No push. Next: user review of the revised layout, then report polish and remaining accessibility checks.


## Foundation checkpoint — horizontal colors, notes and report preview

Implemented: three horizontally arranged color pickers with Apply; Personal notes in a top-right popover available on every page of an active analysis; local save with error rollback; and a readable Exports preview generated by the same brief function as the packet. No approved scenarios produces a clear next action. Preview does not waive review gates. Notes still require explicit export opt-in. The popover is a compact first implementation, not the proposed always-open right-hand notes dock.

| Foundation capability | Current status | Remaining acceptance work |
|---|---|---|
| First-use example, upload entry, quieter controls | Implemented | Novice/practitioner task testing |
| Three custom colors, Apply/reset, color-blind chart styling | Implemented | Broad color-vision, zoom and keyboard review |
| Tutorial navigation and adjacent guidance | Implemented | Narrow/mobile navigation exercise |
| Personal notes across analysis pages | Implemented as popover | Optional persistent desktop dock |
| Readable report preview and verified packet | Implemented | Recipient usability review |
| Custom CSV validation and public-reference comparison | Implemented with reviewed persistence, scenario evidence links and schema 2.1 replay | Independent teammate exercise; numerical local-station models remain separate |
| User document ingestion | Not implemented | File types, provenance, review and private export handling |
| Area-specific simulation visuals | Not implemented | Define area geometry, model inputs/units, baseline, policy assumptions, calibration and uncertainty; then render baseline-versus-scenario results |

Next modeling milestone: a single bounded area and a clearly labeled baseline-versus-scenario view connected to a reviewed evidence record. Existing reservoir animation is illustrative and excluded from verified evidence packets; it is not a calibrated geographic forecast. Avoid rendering synthetic damage or land-condition imagery as measured or predicted output.

Validation: 24 application/upload tests passed (tmp/foundation-ui-0907); expanded application suite passed four tests (tmp/notes-preview-0907) including note saving, report preview and private-note export default. Git fetch failed due connectivity; cached origin/main equals HEAD but remote freshness is unknown. All changes remain local. The only identified Required Reading attachment is the original user-supplied instructions; identity of the separately approved pasted proposal remains unresolved.
