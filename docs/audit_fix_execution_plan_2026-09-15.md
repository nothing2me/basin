# Audit fix execution plan

This plan closes the five defects found in the post-implementation review. It is ordered by user-visible risk and includes the acceptance evidence required before the recording build is frozen.

## 1. Use one custom-data contract everywhere

- Add `Workspace.has_custom_data`, true for either saved custom evidence or a custom station in the active source manifest.
- Use it for export consent, export enablement, packet freshness, saved-artifact behavior, and reset warnings.
- Preserve the backend rule that custom numerical data enters a portable packet only with explicit consent.
- Verify the exact activation case where `custom_uploads` is empty but the source contains an activated gauge.

**Acceptance:** the live Export screen offers consent for an activated gauge; export remains disabled before consent and becomes available after consent; direct export without consent fails; consented ZIP verification and replay pass.

## 2. Keep interpretation inside rainfall evidence

- Replace the automatic operational/AI narrative with the existing deterministic rainfall summary.
- Remove claims about heatwaves, baseflow, runoff, reservoir inflow, soil response, catchment response, and legal restriction timing when those inputs were not modeled.
- Do not use generated narrative as a PDF or CSV public summary.

**Acceptance:** Review and the PDF describe duration, source dates, rainfall shortfall, matched-window rank, dry spell, and selected-station concurrence; prohibited causal terms do not appear in generated scenario summaries.

## 3. Restore human decision accountability

- Leave review rationale blank for a new scenario.
- Require a substantive human rationale before Include or Exclude is enabled.
- Remove the Review-page one-click action that copied one scenario's generated note to the whole shortlist.
- Keep batch inclusion only at Export, require a specific rationale, and label every resulting audit event as a batch decision.
- Keep generated facts separate from review notes.

**Acceptance:** a blank note cannot approve a scenario; an individual rationale is recorded verbatim; batch review is disabled until a rationale is supplied and every affected audit event identifies the batch decision.

## 4. Remove implicit model inference from the verified pipeline

- Do not call Qwen or any other prose model during workspace creation, lookup, editing, shortlist rebuilding, or swapping.
- Do not serialize generated model text into new scenario audit records or shortlist exports.
- Retain compatibility readers for older sessions, but do not present their generated narrative as verified evidence.

**Acceptance:** creating and using a workspace cannot call the optional model; new saved/exported scenario records contain no AI narrative or draft review note; the core remains deterministic and offline.

## 5. Bound static chart rendering

- Render Plotly PNGs in a killable subprocess with a hard timeout.
- Cache successful chart bytes by complete Plotly JSON and dimensions.
- Treat timeout, renderer failure, and malformed output as an unavailable chart and continue to the readable text/vector report path.
- Retain the existing browser-to-PDF timeout and explicit renderer disclosure.

**Acceptance:** a forced static-chart timeout returns control and still permits report fallback; successful charts remain embedded when the renderer is available; export never waits indefinitely for Kaleido.

## Verification gate

1. Compile all changed Python modules.
2. Run focused summary, app, custom-gauge, integrity, exporter, invalidation, and PDF failure/report tests.
3. Run the broader core suite if the focused gate passes.
4. Execute activated-gauge save/reopen/export/replay with and without consent.
5. Generate and visually inspect one fresh PDF, then replay its companion ZIP in a clean process.
6. Freeze the exact tested commit for recording.
