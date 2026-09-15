# Gemini implementation plan: policy comparison and document evidence

Pull the latest `main` before editing. Do not recreate or restyle the recent theme, logo,
Data Dashboard disclosure, crisis-demo, or assistant-tool changes. Keep the current BASIN
visual language: restrained controls, plain wording, progressive disclosure, and one clear
primary action per section.

## Workstream 1 — Advanced demand-policy comparison

### Product outcome

Let an advanced user compare the currently selected Region N storage system under its
configured sector-curtailment assumptions with the same system and rainfall under no
sector-specific curtailment. The result must explain the modeled difference without
claiming that either configuration is current law, adopted policy, or a forecast.

### Existing foundation to reuse

- `basin_core.water_system.WaterSystemConfig` already stores domestic, industrial,
  outdoor, and wholesale demand shares.
- `REGION_N_MODERN_PRESET` already enables stage curtailment and inactive storage.
- `simulate_reservoir_drawdown()` already produces served and curtailed volumes by sector.
- Review, assistant calculations, saved simulations, reports, and replay already share
  `Workspace.water_system_selection` and `ExperimentConfig.system_config`.

Do not add a second independent storage-system selector or parallel simulation model.

### Implementation steps

1. Add a compact comparison control inside **Advanced View → Storage Drawdown & Water
   System**. Keep it below the primary trajectory, collapsed until requested.
2. Compare two configurations with every input held constant: selected rainfall revision,
   starting storage, pipeline availability, aggregate demand reduction, capacities,
   inflow assumptions, evaporation assumptions, and stage thresholds.
3. The only allowed difference is the sector-curtailment configuration. Build the alternate
   immutable `WaterSystemConfig` with `dataclasses.replace`; do not mutate the selected
   workspace configuration in place.
4. Use neutral labels such as **Configured sector schedule** and **No sector-specific
   curtailment**. Do not label a case “DSEF repeal,” “fair policy,” or “current policy” unless
   a reviewed source and an explicit mapping contract are added later.
5. Calculate all comparison values at runtime. Never hardcode a days-gained value, demand
   share, breach date, or benefit claim.
6. Show no more than four outputs initially:
   - day the configured critical band is first reached;
   - day the active-storage limit is reached;
   - total unmet modeled demand;
   - domestic and industrial curtailed volume.
7. Display a delta only when both cases make the comparison meaningful. Use “not reached
   in this window” when appropriate. Never turn a missing crossing into an invented day.
8. Add one short visible boundary statement: the comparison is an illustrative numerical
   experiment using configured shares and is not an adopted allocation or forecast.
9. Keep the comparison read-only at first. It must not silently change the active selected
   policy, scenario review status, shortlist, evidence, or export configuration.

### Required tests

- Both cases use the same scenario revision and selected storage system.
- Enabling the comparison does not mutate `Workspace.water_system_selection`.
- Displayed deltas equal direct calculations from both simulation frames.
- Missing threshold crossings render honestly.
- Switching Simple/Advanced views changes presentation only.
- Opening the comparison does not invalidate a reviewed simulation or export.
- Existing `test_water_system.py`, `test_simulation_contract.py`, `test_report_config.py`,
  `test_review_preferences.py`, and assistant consistency tests remain green.

## Workstream 2 — T5 document-evidence interface

### Product outcome

Expose the existing typed document lifecycle through one contained interface so a user can
upload a local PDF or text file, inspect extracted text, make a human review decision, and
promote only reviewed material to evidence.

### Existing foundation to reuse

- `Workspace.ingest_document()`
- `Workspace.extract_document()`
- `Workspace.submit_document_for_review()`
- `Workspace.review_and_accept_document()`
- `Workspace.reject_document()`
- `DocumentLimits`, `DocumentState`, and the typed validation/security errors in
  `basin_core.document_ingestion`
- Existing workspace save, restore, evidence-link, privacy, integrity, and export filtering

Do not create another document model, storage directory, evidence schema, or raw-byte
export path.

### Implementation steps

1. Put the UI inside the existing **Data Sources, Station Catalogs & Snapshot Metadata**
   expander as a new **Supporting documents** tab. Do not add another large Step 1 card.
2. Accept only PDF and plain-text files supported by the domain layer. Enforce the existing
   byte, signature, encryption, script, page, and character limits before showing success.
3. Collect only the metadata required by the existing API: file, provider/source name, and
   privacy classification. Default to private.
4. Process a file only after an explicit **Add document** action. Do not re-read, re-hash,
   extract, or render the file on every Streamlit rerun.
5. Show a compact document list with filename, provider, state, privacy, and shortened
   content digest. Let the user select one document for details.
6. Present extracted text as a bounded plain-text excerpt with page/block references. Do not
   embed a PDF viewer, execute document links, interpret document instructions, or send the
   document to the assistant automatically.
7. Drive the existing lifecycle with one next action at a time:
   **Extract → Submit for review → Accept as evidence / Reject**.
8. Require a reviewer rationale and explicit confirmed statement before acceptance. Surface
   prohibited-claim errors in plain language and keep the document unaccepted.
9. Make it clear that extraction is not verification and acceptance is a local human review
   decision. Use the existing document disclaimer rather than adding repeated legal text.
10. Preserve the existing consent rules: private originals and unreviewed material must not
    enter normal exports. Do not alter note or custom-rainfall consent behavior.

### Performance requirements

- No extraction during ordinary page rendering.
- Cache only results that are safe to cache by immutable document digest.
- Render a bounded excerpt instead of every extracted block at once.
- Keep upload and review widgets inside the collapsed source-details area.
- Do not add animation, polling, background threads, network calls, or an embedded PDF.

### Required tests

- Valid text and PDF uploads enter the correct initial state.
- Duplicate content keeps deterministic identity and does not create conflicting copies.
- Oversized, encrypted, scripted, signature-mismatched, and unsupported files fail closed.
- Illegal lifecycle transitions remain unavailable in the UI and fail in the domain layer.
- A document cannot become evidence without extraction, submission, rationale, and human
  acceptance.
- Rejected and unreviewed documents never become evidence.
- Save/restore preserves identity, state, privacy, and reviewed citations.
- Default exports exclude private raw bytes and unreviewed documents.
- The interface does not process the same upload again during unrelated widget reruns.
- Run `tests/test_document_ingestion.py`, integrity/export/privacy tests, and the full UI
  workflow suite before pushing.

## Delivery order

1. Implement and test Workstream 1 in one commit.
2. Pull/rebase if `main` moved.
3. Implement and test Workstream 2 in a separate commit.
4. Run the full test suite.
5. Inspect Data, Simple Review, Advanced Review, assistant, Notes, and Export in both light
   and dark mode at 1280×720.
6. Push directly to `main` only after the branch is synchronized and the required checks
   pass. Report exact test counts and any deferred limitation; do not claim completion for
   untested paths.
