# BASIN claim inventory

Updated: 2026-09-11 (status-reconciliation pass; corrected the custom-evidence export row below and added the native/PDF/Review section) | Source baseline: `5679637` on `main`. Rows not touched by this update still describe the state at their original date; check `TODO.md`'s B-board for the current status of any specific item.

This inventory separates what the current product implements, what automated checks verify, what a human has observed, and what remains proposed or unvalidated. Historical submission wording is preserved in `submission_record.md`; it is not automatically a current capability claim.

Claim states used here:

- **Implemented:** present in the current source or tracked release artifact.
- **Internally verified:** recomputed or exercised by the named automated checks within their declared scope.
- **Observed locally:** inspected on this development computer; not established on the presentation device.
- **Pending human review:** requires a practitioner, teammate, recipient or organizer confirmation.
- **Excluded:** deliberately outside the product or verification claim.

## Product, data and method claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| BASIN is a local rainfall-scenario decision-support workbench. | Implemented | `app.py`, `basin_core/`, README and the tracked Windows launcher. It does not host a shared cloud service. |
| Core runtime AI is local KMeans plus deterministic weighted ranking; no LLM is required for core workflows. | Implemented and internally verified | `basin_core/analysis.py`, pinned scikit-learn, deterministic tests and offline smoke. Development used AI assistance and is disclosed separately. |
| Built-in analyst assistant routes supported questions through an embedded deterministic intent engine. | Implemented; regression tested | `basin_core/assistant.py`, read-only tools, and fixed templates. No model server or download required. Not a general-purpose LLM; excluded from verified rainfall packets. |
| The bundled observations cover 1991-2025 at Corpus Christi, Victoria and San Antonio airport stations. | Internally verified | `data/manifest.json`, snapshot SHA-256 and fresh-checkout verification. These are provisional regional proxies, not validated source-catchment rainfall. |
| BASIN builds complete synchronized historical windows and applies explicit rainfall-retention transformations. | Implemented and internally verified | Engine, methodology, numerical tests and bundle replay. Retention scales rainfall only; it is not a streamflow, inflow or shortage multiplier. |
| Scenarios cover configured 30-365 day durations and declared onset months/stations. | Implemented and internally verified | Parameter validation and replay. The product does not answer multi-year hydrologic drought questions outside this range. |
| Scenario groups and ranking are explainable. | Implemented with limited verification | Feature values, scores and normalized components are recomputed. KMeans labels, semantic profile names and saved comparison results are recorded/hash-checked but not replay-certified as scientific truth. |
| Exact score ties are deterministic, and increasing a weight need not improve a scenario's rank. | Internally verified | B06.7 regression cases use stable scenario-ID tie-breaking and a nondiscriminating duration-weight example. Priority values remain illustrative pending practitioner review. |
| Users can challenge, edit, reject, replace and approve rainfall revisions. | Implemented and internally verified | Workspace history, revision invalidation, AppTest workflow and bundle replay. Acceptance is local rainfall-content review, not engineering certification. |

## Evidence, uploads and export claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| Users can trace assumptions, compare evidence records and preserve unresolved disagreements. | Implemented and internally verified | Schema 2.0 evidence/conflict records, save/restore tests and privacy-aware export. The app does not decide which source is true. |
| Local rainfall CSVs can be previewed without changing the workspace. | Implemented and internally verified | Bounded parser and Streamlit tests. The parser, README and `.streamlit/config.toml` are aligned to 10 MB (`maxUploadSize = 10`). |
| Uploaded rainfall can be compared descriptively with one selected bundled NOAA station. | Implemented and internally verified | Same-date paired-valid-day calculation, blocking declarations, zero-reference handling and opt-in JSON report. Geography and observation-day compatibility are user declarations, not independent validation. |
| Upload comparison results enter saved scenarios and the verified ZIP. | Implemented and internally verified (B14, corrected 2026-09-11; this row was stale) | Normalized observations, source metadata, review rationale and all saved comparison versions are persisted, linked to scenarios, included in the ZIP's `audit.json` under explicit custom-data consent, and replayed against the bundled snapshot. Original CSV bytes/filenames stay excluded. No independent teammate has exercised this with their own sample (B14's one remaining subtask). |
| The evidence packet is internally consistent and replayable within a declared scope. | Internally verified | File inventory/hashes, source identity, transformations, revisions, accepted IDs, rainfall values, features, ranking components, evidence links, privacy defaults and regenerated brief are checked. Bundles are unsigned and do not prove source authenticity. |
| The packet is directly import-compatible with Texas WAM Run 3 or HEC-ResSim. | Pending human/tool validation | The Stage 1 submission commits to interoperable open handoff. Current CSV/Markdown files support human transfer, but no direct importer/exporter interoperability test is recorded. Do not say “verified WAM export.” |
| The recipient can independently use the CSV and brief in their workflow. | Pending human review | B04.10 and B09.6 require an independent recipient exercise. Automated replay is insufficient evidence. |

## Deployment, privacy and appearance claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| Python calculation paths can run with network sockets blocked. | Internally verified | `scripts/demo_smoke.py`. Browser/native UI network isolation remains untested on the presentation laptop. |
| A branded native Windows executable exists. | Implemented and observed locally | Tracked `BASIN.exe` matches `origin/main`; browser launcher remains a fallback. Clean reproducible build dependencies are pinned in `requirements-build.txt`; presentation-device execution remains open. |
| Local notes and uploads stay on the operator's device unless explicitly exported. | Implemented with stated limits | Loopback server, ignored local storage, no telemetry, private-note opt-in. Local files are not encrypted and the app is single-operator, not an authenticated multiuser service. |
| Application controls are readable in coordinated light/dark themes and plots retain distinct colors. | Implemented and observed locally | Current Streamlit theme/CSS, prior desktop visual review and UI tests. Projector and presentation-resolution review remain open. |
| The source kit excludes private sessions, notes and correspondence. | Internally verified for the recorded package | Package inspection is historical and must be repeated for the frozen kit. The tracked executable is a separate release artifact. |
| BASIN has a measured low environmental footprint. | Not established broadly | Individual runs record time and completion-time memory. The 15-65 W energy range is an illustrative assumption, not a power measurement; water impact and full lifecycle footprint are unquantified. |

## Reservoir and impact claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| The two-pool reservoir view conserves its defined daily accounting quantities. | Internally verified as an experiment | Wet/dry/empty/full tests cover inflow, evaporation, served demand, unmet demand and spill under the stated toy assumptions. |
| Reservoir levels, safe yield, deliveries or restriction dates are forecast. | Excluded | The reservoir view is uncalibrated and illustrative, is excluded from evidence packets, and cannot support official timing or performance claims. |
| BASIN improves analyst productivity or water outcomes. | Proposed benefit; pending human review | Three anonymous discovery responses support the problem framing. No completed product-use baseline, practitioner session, recipient exercise or measured outcome exists yet. |
| Community users control scenario priorities and final selections. | Implemented; practical usefulness pending | Controls, shortlist preservation, review and rejection exist. B09 must show that intended users understand and can use them without coaching. |

## Competition and presentation claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| The event is September 22, 2026 in Pleasanton, with September 21 expected for travel. | Confirmed in supplied organizer material | Official rules and finalist Q&A record. Later organizer instructions can modify logistics. |
| Judging considers impact, feasibility, community centeredness, innovation and clarity. | Confirmed in supplied organizer material | Official rules. Weights and additional Stage 2 guidance may change. |
| The presentation is three minutes or sixty minutes. | Unknown | Those are internal drafts. The supplied August 10 materials do not specify the finalist presentation length or detailed format. B11.7 remains open. |
| The team has four speakers or a lead hydrologist. | False for the current roster | The team has three named students. Roles must be claimed by those teammates; do not invent credentials. |

## Agronomic and wildfire index claims

| Claim | Current state | Evidence and boundary |
|---|---|---|
| Regional Reference Evapotranspiration ($ET_o$) reflects long-term South Texas / Region N monthly normals. | Implemented and internally verified | `basin_core/agronomics.py`, Texas ET Network (Texas A&M AgriLife) published normals for Corpus Christi/Coastal Bend totaling ~58.1 inches (~1476 mm) annually. Normals are fixed regional monthly averages; they are not real-time station micrometeorological measurements. |
| Crop water demand ($ET_c = ET_o \times K_c$) and irrigation gap quantify agricultural water stress for regional staple crops. | Implemented and internally verified | FAO-56 / Texas A&M AgriLifeExtension crop coefficients ($K_c$) for Cotton (1.10), Grain Sorghum (1.05), Corn (1.15), Pasture (0.85), and General Row Crop (0.95). Excludes complex soil moisture profile dynamics, root-zone depth transitions, and groundwater contributions. Serves as illustrative exploratory decision support, not certified irrigation scheduling. |
| Keetch-Byram Drought Index (KBDI) tracks soil moisture depletion from 0 (saturated) to 800 (extreme drought). | Implemented and internally verified | Standard Keetch-Byram (1968) formula using South Texas monthly temperature approximations, 32-inch annual precipitation, and 0.20-inch initial rainfall interception threshold. Unit tested across wet, dry, boundary-clipping, and multi-day scenarios. |
| KBDI $\ge 600$ indicates county burn ban consideration. | Implemented as illustrative decision support; non-regulatory | Texas A&M Forest Service guidelines recommend county burn ban evaluation around KBDI 575–600. BASIN displays this as an illustrative decision-support indicator. Official burn bans are statutory acts enacted exclusively by County Commissioners Courts under Texas Local Government Code § 352.081; BASIN never issues regulatory or legal declarations. |

## Current conflicts to resolve before freeze

1. Confirm finalist presentation length, deck/demo submission mechanism, A/V constraints and travel instructions.
2. Reconcile the documented 10 MB CSV limit with Streamlit's current 5 MB application limit.
3. Pin native build-only dependencies and rebuild/test the executable on the presentation laptop.
4. Obtain practitioner review of station/catchment suitability, method language and the illustrative reservoir framing.
5. Run the novice and recipient exercises; record actual comprehension and format changes.
6. Review AI-use and third-party disclosures as a team.

No claim above converts discovery evidence, automated checks or local acceptance into professional validation.

## Saved-simulation and multi-sector integration

The optional local assistant returns deterministic tool results or clarification/boundary messages; it does not append unconstrained numerical interpretations. This is not a blanket network-isolation or zero-hallucination certification. Simulation requests explicitly create an unreviewed saved result, but cannot approve it through the assistant.

Schema 2.2 numerical replay includes saved illustrative simulations, matched conservation comparisons, and provenance-linked review tokens. Neither the UI nor reports claim a calibrated forecast, official restriction date, exact breaking point, certified signature, or generic system survival. Missing source-year scenarios fail; multiple matches require selection. The PDF remains a readable companion to the replayable ZIP, with privacy opt-ins and no fabricated fallback outcomes.

## Native runtime, PDF renderer and tailored Review claims (added 2026-09-11)

| Claim | Current state | Evidence and boundary |
|---|---|---|
| An optional native Qwen runtime can be installed/repaired independently of model weights, with hash-locked pins. | Implemented and internally verified | `scripts/install_native_runtime.py`, `docs/native_runtime_handoff.md`. Not device-tested: clean-laptop install, live offline inference timing, native egress observation and model license/provenance review are explicitly open, not attempted. |
| PDF generation discloses which renderer actually produced the file and any degraded fallback, and consent is honored identically across the ZIP and both PDF renderers. | Implemented and internally verified | `basin_core/pdf_report.py`'s `RenderOutcome`; `docs/pdf_failure_handoff.md`'s cross-output consent tests. Windows deliberately never attempts the browser renderer (disclosed choice); actual browser/native download and write-failure recovery on the presentation laptop (B17.5) is untested. |
| A Review focus panel tailors which tools lead, without changing calculations, ranking, shortlist, revisions or export consent. | Implemented and internally verified (51 tests) | `basin_core/review_preferences.py`. Four goals exist (`compare`, `storage`, `operations`, `handoff`); a separate, additional pre-run entry point exists in Scenario Builder alongside the original Review-page panel — the two are not reconciled into one place. |
| The Review focus panel is usable in light theme, at a narrow viewport, and by keyboard only, and its tutorial targets work. | Partially observed; not established broadly | An unmerged branch (`task/review-acceptance-checks`, `864d95f`) drove a real browser and confirmed focus/toggle/navigation behavior, light theme, and keyboard focus (fixing two real accessibility defects in the process), but could not exercise narrow-viewport reflow or the Saved-Runs/Settings popovers in that automation session. An earlier HANDOFF claim of full desktop/narrow/keyboard/tutorial verification could not be independently corroborated. Details are in that branch's own `docs/review_acceptance_handoff.md`, which is not present on `main` until the branch merges. |

