# Tailored Review proposal

Status: proposed, not implemented. Based on Noah's pre-run questionnaire idea. Implement after the installation/security integration; use one owner for app.py.

## Short setup, with a skip option

1. What are you trying to do? Compare rainfall scenarios / Explore an illustrative storage scenario / Prepare a reviewed handoff.
2. Which data will you use? Bundled regional observations / My rainfall data / Not sure, start with an example.
3. How much guidance do you want? Guided explanations / Technical detail. This is a presentation preference, not a measure of expertise.

Show a concise, editable summary before creating a run. Preserve choices on navigation and provide an always-visible Change focus / Show all tools control. Do not require completing a questionnaire for every repeat run.

## Default Review content

| Goal | Show first | Keep under More tools |
|---|---|---|
| Compare rainfall | Source period, rainfall change, rainfall/reference comparison, side-by-side differences, interpretation limits | Alternative chart types, numerical diagnostics |
| Explore storage | Explicit assumptions, selected storage/conservation/pipeline settings, illustrative trajectory, sensitivity comparison | Additional spectrum and timeline views |
| Prepare handoff | Selected revisions, review decisions and reasons, unresolved evidence conflicts, export readiness | Exploratory charts and diagnostics |

Source identity, uncertainty, illustrative-model warnings and consent controls must never disappear because of a profile. Unavailable data must be labelled; selecting a use case cannot create missing evidence or establish suitability.

## State and correctness boundaries

Keep a separate versioned ReviewPreferences/profile record for display choices. ExperimentConfig remains numerical inputs; do not silently alter it when switching focus. If a focus recommends ranking weights, show the recommendation and require an explicit apply action.

Persist the profile with the run through the existing saved-state contract, with compatibility tests for older saved runs. Label display profile separately from calculation settings in the report. A UI profile must not silently change selected scenarios, accepted revisions, calculations, custom-data inclusion or private-note consent. Exports contain the authorized reviewed content regardless of hidden UI panels; they do not contain everything indiscriminately.

## Acceptance

- A user can skip setup, edit their focus and reach every tool without losing work.
- Changing display focus leaves numerical results, ranking and consent unchanged.
- Missing data/assumptions remain explicit; illustrative storage is never described as predicted restriction dates.
- Save/reopen, old saved runs, navigation, narrow screens, keyboard focus and both themes work.
- Run short sessions with intended users. Record observed confusion and changes; do not call AI-authored personas community validation.

The goal is fewer initial choices and a clearer next action, not a new scientific model or a promise of operational advice.
