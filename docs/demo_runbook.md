# September 22 Demo Runbook

Updated: September 19, 2026 | Product baseline: source checkout on `main` + `BASIN.exe` native launcher

> **Read this before anything else:** the previous version of this runbook (Sept 8)
> carried claims the 2026-09-15 independent audit flagged for removal — hardcoded
> B-009 numbers, "$50k and 6 months", "30×–50× acceleration", "Verified:" wording,
> and operational Stage-3 timing. They are gone. Any on-screen number quoted below
> must be **re-read from the live run on the target laptop**, not recalled from
> memory. See [Positioning & Judge Q&A](#positioning--judge-qa) for the honest framings.

## Three-Minute Product Demonstration Sequence

1. **Sidebar / Launch (`BASIN.exe`)**:
   - Show native desktop execution (EdgeChromium WebView2, no terminal flashing).
   - In the Scenario Builder, set **Community footprint → "Watershed"** (one click pre-fills the 10 gauges inside the Nueces/Frio/Atascosa drainage basins — Leakey headwaters through Choke Canyon Dam to Mathis). Keep 90, 180, 270 days; Jan/Apr/Jul/Oct; 35–85% retention; 300 candidates; 6 shortlisted; seed 22.
   - Say: *"In response to our watershed review, we screen on rainfall inside the basins that actually feed Choke Canyon and Lake Corpus Christi — the reservoir-relevant footprint — rather than coastal airport stations. The regional and combined footprints stay one click away for comparison."*
   - Explain the missing layer: statutory and engineering models (WAM / HEC-ResSim) take substantial time and specialized funding to update — the 2026 Region N plan itself notes the supply model's hydrology stops in 2015. BASIN screens drought scenarios *before* commissioning that work. Generate.

2. **Workspace / Clustering & Ranking**:
   - Point out synchronized whole-window resampling (maintaining physical cross-station correlation across the basin).
   - Show how KMeans groups diverse stress patterns across duration, deficit, and season — then the explainable weighted ranking (severity/duration/concurrence/season) picks a diverse shortlist.

3. **Grounded AI Assistant Interrogation**:
   - Click the vertical **AI Assistant** tab. Note the smooth hardware-accelerated drawer.
   - Ask: *"Why did `<top scenario>` rank first?"* — use the **live scenario ID** on screen, not a memorized one. Show the weight breakdown.
   - Explain that the embedded intent engine maps supported questions to **13 deterministic Python tools and fixed templates** — no language model or inference server is used for these answers.
   - Ask a follow-up like *"What was station concurrence in `<id>`?"* and read the value from the screen.

4. **Review / Rainfall Decision**:
   - Compare the shortlisted rainfall scenario with its matched historical reference and inspect its source stations, duration, deficit, concurrence and coverage lineage.
   - Record the internal reviewer name or team, role and rationale. Say: *"This is our team's screening decision about which rainfall content belongs in the handoff. It is not external hydrologic approval."*
   - Keep the storage experiment closed during the core demo. Open it only for a judge question about assumptions, and describe every number as a consequence of the configured uncalibrated accounting inputs.

5. **Replayable Handoff**:
   - Accept the scenario and log a hydrologist note (*"Reviewed: acute summer concurrent deficit"* — use "Reviewed", not "Verified").
   - Open **Exports** and click **Build replayable handoff**.
   - Spotlight the **Executive Technical Brief (PDF)** and the companion deliverables: replay-verified ZIP bundle, Markdown handoff brief, and **Open Output Folder** with SHA-256 integrity results.
   - Say: *"The ZIP is replay-verified end-to-end. The PDF is the readable companion and is stamped as outside that verification contract."* — that honesty is a feature, not a caveat.

6. **Close on Impact & Usefulness**:
   - The A/B benchmark exists in `research/benchmark_no_basin_packet/` (audit trail, checksums, scenario outputs). You may describe it as *"an internal benchmark comparing from-scratch coding against BASIN"* — **do not cite a multiple unless you re-measure it on the target laptop first**. Lead with correctness and provenance instead: *"the exported packet lets a hydrologist trace every scenario back to its inputs."*
   - Close with: *"Would this packet help you identify and document rainfall scenarios worth carrying into a formal water-supply model? What additional data and validation would you require before relying on its outputs for an operational drought decision?"*

---

## Positioning & Judge Q&A

### The reservoir simulation question (most likely hard question)

> **Judge:** *"Your submission says BASIN does NOT predict reservoir levels. You're
> showing me reservoir drawdown charts. Which is it?"*

**Answer (memorize the shape, adapt the words):**
> "We kept that promise — BASIN doesn't predict. What you're seeing is an
> *illustrative* mass-balance screening run: the same rainfall-stress scenario fed
> through a strict conservation equation with evaporation and demand, to show which
> shortlisted scenarios would be worth deep modeling. It is stamped inside the PDF
> as an exploratory sensitivity tool, not an operational forecast, and it is not a
> safe-yield or restriction-date claim. The exportable artifact — the thing a
> hydrologist takes away — is the replay-verified rainfall-stress scenario bundle.
> The simulation is a visualization aid for triage, which is exactly the screening
> layer we proposed."

Backing you can point to: the PDF stamps "exploratory sensitivity tool, not an
operational delivery forecast" and "PDF NOT VERIFIED"; `basin_core/scientific_contract.py`
auto-rejects overclaims; the export has **no verdict field**.

### The survey question (second likely question)

> **Judge:** *"You said you surveyed professionals. How many? Can I see it?"*

**Answer:**
> "We ran a discovery survey with Region N professionals before the finalist round.
> Three consented responses, consistently pointing at the same pain: not a lack of
> data, but conflicting data with no trustworthy way to tell what's credible. We
> treat that as directional input — not a representative study — and it directly
> shaped the product's provenance guarantees. The raw responses stay private; the
> evidence record is in the repo (`research/survey_evidence.md`), and we're running
> an uncoached intended-user exercise this week to build on it."

**Do not say:** "a survey showed", "many professionals", "verified with professionals."

### The ranking-stability question (from professor/geoscience review)

> **Judge/Reviewer:** *"How stable is your ranking? With correlated features, can
> you trust the feature-importance breakdown?"*

**Answer:**
> "The ranking is deterministic — fixed seed and fixed, user-visible weights — so
> the shortlist is bit-identical on every rerun, which is what lets reviewers
> audit it. We don't claim the per-feature contributions are independent causal
> importance: severity, duration, and concurrence are hydrologically correlated,
> and we treat the weighted components as arithmetic under chosen priorities, not
> XAI attributions. That's also why the shortlist is selected by cluster diversity
> first — so correlated features can't collapse it into a single drought
> archetype. Weights are adjustable on the Review screen so anyone can probe
> sensitivity live." (Full reasoning: `docs/ranking_stability.md`.)

### The watershed-footprint question (from the professor's feedback)

> **Judge/Reviewer:** *"Your earlier runs used coastal stations. Why screen on
> watershed gauges now?"*

**Answer:**
> "After our watershed review, we added 10 NOAA gauges inside the Nueces/Frio/
> Atascosa drainage basins that feed the reservoirs — from Leakey in the
> headwaters through Choke Canyon Dam to Mathis at the reservoir pools — and made
> that footprint one click away in the builder. It is a more relevant set of point
> observations for screening rainfall over the source basins than coastal airport
> stations. We keep the regional and combined footprints available for comparison.
> These gauges are not calibrated catchment rainfall, and BASIN has not established
> a rainfall-runoff relationship from them."

**Demo discipline:** commit to **one footprint per run** and never compare numbers
across footprints — different station sets produce different (not wrong) scenarios.

### Demo discipline (from the audit)

- **Lead with the deterministic assistant, keep Qwen optional.** The optional 2.1 GB
  model adds weight and failure modes to a demo that does not need it for correctness.
- Do not claim energy numbers as measured — the footprint panel reports an estimated
  15–65 W range. If you want a "measured" label, run one no-model pass on the target
  laptop and record wall/CPU time and energy first.
- Any Stage/Band breach day, percentage, or ratio quoted on stage must be read from
  the live run.

---

## Before Travel Checklist

- **Presentation Laptop:** 64-bit Windows with BASIN and its documented runtime prerequisites.
- **Offline Smoke Test:** run the full suite once on the target laptop:
  `.venv\Scripts\python.exe -m pytest -q` (817 passed / 2 expected skips as of 2026-09-19).
- **Re-measure on the target laptop:** (a) one no-model run time + energy for the footprint panel, (b) the A/B benchmark multiple if you intend to cite it, (c) the exact breach-day and drawdown values **using the Watershed footprint** (the footprint used in the live demo), (d) confirm the Community footprint preset renders and pre-fills correctly on the presentation build.
- **Projector Rehearsal:** connect external display at 1920×1080 and 1600×900 to ensure high-DPI scaling and split-pane layout render sharply.
- **Backup Assets:** USB stick containing:
  1. `BASIN.exe` standalone build (rebuilt from current `main`).
  2. Offline `.venv` wheelhouse.
  3. A pre-exported replay-verified `BASIN-Export-*.zip`.
  4. Video recording of the 3-minute sequence.

---

## Recovery Procedures

- If a question is not recognized by the assistant: use a Quick Query or the Direct Tool Runner. Include scenario IDs and ask a complete question.
- If port 8501 is occupied: the native launcher cycles through ports 8501–8550 to find the first open port.
- On browser/webview refresh: saved sessions persist in `output/workspaces/` and can be reloaded in one click.

---

## Quick Judge Reference

- **AI Method:** Unsupervised KMeans clustering + deterministic intent routing to 13 read-only tools and fixed templates.
- **Grounded Responses:** numbers come from workspace calculations; routing accuracy still needs evaluation.
- **Why Not Existing Tools:** WAM / HEC-ResSim are heavy, static engineering models requiring months and specialized funding to update. BASIN is the missing agile, replay-verified screening and handoff layer before that investment.
- **Evidence of Usefulness:** internal A/B benchmark in `research/benchmark_no_basin_packet/` (re-measure the multiple before citing); provenance guarantees are the primary differentiator.
- **Community Evidence:** `research/survey_evidence.md` — three consented discovery responses, directional; uncoached intended-user exercise pending.
