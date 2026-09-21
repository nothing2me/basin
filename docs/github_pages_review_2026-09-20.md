# BASIN GitHub Pages review

Live site reviewed: `https://nothing2me.github.io/basin/`

Reviewed September 20, 2026 against the current application, professor-feedback changes, and presentation script v4.

## Main finding

The page is visually polished but explains the secondary storage experiment before it explains BASIN's primary contribution. A first-time visitor sees “hydrologic screening,” reservoir drawdown, curtailment policies, solver precision, and mass conservation. That framing makes BASIN look like the reservoir-reliability model the project now explicitly says it is not.

The page should answer four questions in order:

1. What is BASIN?
2. What does a reviewer do with it?
3. What does replay verification prove?
4. What still requires a formal water-supply model?

## Release blocker

The two installer buttons point to:

`https://github.com/nothing2me/basin/releases/download/v1.0.0/Setup-BASIN.exe`

That URL returns HTTP 404. The public repository currently has no published releases and no tags. Until the final installer is built, hashed, tested, tagged, and published:

- Remove “Official Release v1.0.0.”
- Remove the installer SHA-256.
- Replace both download buttons with **View prototype source** linking to the repository.
- Replace the footer release link with **Release status** linking to the repository or remove it.

Do not publish the existing installer hash for a future rebuild.

## Recommended page structure

### 1. Hero

**Eyebrow**

> Zoho “From the Ground Up” AI Hackathon 2026 finalist

**Headline**

> Rainfall scenarios worth carrying into formal water-supply analysis

**Subhead**

> BASIN turns a pinned NOAA rainfall snapshot and explicit assumptions into a transparent shortlist for internal review and professional handoff. It screens questions before formal modeling; it does not forecast reservoir operations.

**Primary action before release**

> View prototype source

**Secondary action**

> See the workflow

**Four short facts**

- 1991–2025 rainfall snapshot
- 21-station registry
- Runs locally
- Replayable ZIP handoff

Remove solver precision and “0 KB egress” from the hero. Those details do not help a visitor understand the product.

### 2. Three-step workflow

**Heading**

> From rainfall records to a reviewable shortlist

**Step 1 — Screen rainfall history**

> Build repeatable, synchronized rainfall candidates from selected point gauges. Observed and proxy-filled coverage remain separate.

**Step 2 — Review the shortlist**

> K-Means reduces repetition. A named internal reviewer records Include or Exclude decisions and explains why.

**Step 3 — Hand off the evidence**

> Export a hash-checked ZIP that replays its declared calculations, plus a readable companion PDF for professional follow-up.

### 3. Verification boundary

**Heading**

> Replay checks consistency, not hydrology

**Replay checks**

- Declared files and SHA-256 identities
- Scenario transformations and calculations
- Internal review decisions

**Replay does not establish**

- Source authenticity or a digital signature
- Catchment rainfall, runoff, or reservoir inflow
- Forecast skill, scientific validation, or professional approval

### 4. Product boundary

**Heading**

> Where BASIN stops and formal modeling begins

**BASIN supports**

- Rainfall-scenario screening
- Traceable assumptions
- Internal review and expert handoff

**Formal operational analysis still requires**

- Calibrated rainfall-runoff and routing
- Observed inflow and storage validation
- Actual demand, transfers, releases, and operating rules
- Uncertainty analysis, hindcasting, and independent review

The storage experiment can appear as one small footnote or expandable section labeled **Illustrative assumption sensitivity**. It should not lead the page.

### 5. Local assistant

**Heading**

> Core workflow first. Local assistant optional.

> BASIN's Python tools perform the calculations. An optional local Qwen model can route plain-language questions to those tools. The rainfall workflow works without the model, and no AI system is presented as incapable of error.

Keep installer and model sizes only in the eventual download section.

### 6. Release section

Before publication:

> The Windows release is being finalized and tested on the presentation device. Source code and documentation are available now.

After publication, replace this with the verified release asset, exact size, fresh SHA-256, system requirements, and release notes.

## Copy that should be removed or rewritten

| Current wording | Why it causes confusion | Recommended direction |
|---|---|---|
| “Decision-support hydrologic screening” | Suggests calibrated hydrologic modeling | “Rainfall-scenario screening and expert handoff” |
| “screen reservoir drawdown risks and multi-tiered drought curtailment policies” | Makes storage and policy look like the primary validated result | Lead with rainfall scenarios and internal review |
| “Rigorous hydrologic physics” | Overstates an uncalibrated accounting experiment | “Transparent rainfall screening with explicit assumptions” |
| “Zero calculation hallucinations” | Absolute AI claim; the professor asked for precise boundaries | “Calculations come from BASIN tools” |
| “mass conservation is guaranteed” | Numerical convergence is narrower than physical validity | “Solver checks arithmetic mass balance” |
| “municipal water data … never leave” | The shipped prototype primarily uses bundled public data, and absolute privacy language needs device-level verification | “Core workflow runs locally without a cloud analysis service” |
| “Core Hydrologic Engine” | Reinforces the wrong product category | “Core rainfall-screening workflow” |
| “13 deterministic hydrologic calculation tools” | Many tools inspect rainfall, rankings, provenance, or assumptions rather than hydrology | “13 application-owned analysis tools” |
| Comparison-table latency claims | Unsourced, environment-specific, and distracting | Remove the table or replace it with the product-boundary comparison above |
| “Severe hallucinations” for cloud chatbots | Broad unsupported characterization | Remove |
| “Cryptographic Audit Brief” | The PDF is outside the replay/hash contract | “Replayable ZIP and companion PDF” |
| “Official Release v1.0.0” | No public release or tag exists | Use release-in-progress wording |

## Mobile and readability

The 390-pixel viewport clips the hero headline and right side of the header. Add a small-screen breakpoint around 480 pixels:

- Reduce container padding to 16 pixels.
- Reduce the hero minimum font size below 2.4rem.
- Allow long headline words to wrap safely.
- Hide the header GitHub text button or replace the header actions with one compact button.
- Stack hero facts vertically or reduce them to two rows.
- Verify the comparison table is removed or usable without horizontal scrolling.

## What already works

- Strong visual identity and professional dark theme.
- Clear calls to action and compact navigation.
- Fast static page with no unnecessary interaction.
- Accurate current wording for the replay bundle and companion PDF in one feature card.
- Clear disclosure that arithmetic mass balance does not prove forecast accuracy.

## Recommended concise page length

Keep the homepage to five sections:

1. Hero
2. Three-step workflow
3. Replay boundary
4. BASIN versus formal modeling
5. Source/release status

That structure explains the product faster than the current engineering-first architecture and benchmark sections.
