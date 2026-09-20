# Ranking stability and feature-importance limits

Updated: 2026-09-19. Answers the question: *"How stable is your ranking, and can you
trust the feature contributions?"* — relevant for judge Q&A and for any claim that
BASIN ranks scenarios by hydrologic importance.

## Why the ranking is stable by construction

The shortlist ranking is **fully deterministic**:

- Fixed PCG64 generation seed (`seed=22` in `ScenarioParams`) → the same candidate
  set is produced on every rerun.
- `ScenarioClusterer` uses `KMeans(n_clusters=6, random_state=22, n_init=10)` and
  canonicalized cluster labels → identical clusters.
- `WeightedSumRanking` applies fixed, user-visible weights
  (defaults: severity 40 / duration 25 / concurrence 25 / season 10).

Consequence: rerunning the pipeline produces **bit-identical rankings** — stability
is guaranteed by design, not merely observed. This is a deliberate contrast to
stochastic ML pipelines where "rerun a few times" changes the leaderboard.

## How weight sensitivity can be probed

The Review page exposes the four ranking weights as sliders with an instant
**rerank** control (and a weight-preview comparison). A user can:

1. Raise/lower severity vs. duration and watch which scenario leads change.
2. Use `scripts/evaluate_selection.py` / the built-in selection comparison to
   compare the weighted shortlist against a score-only and a seeded-random
   shortlist (diversity trade-off is disclosed in the report).

This makes the ranking **auditable**: any reviewer can reproduce how the shortlist
responds to priorities, which is the governance feature the tool is built around.

## Known limit: collinear predictors

The five ranking features are hydrologically related and therefore **correlated** —
for example a deeper cumulative deficit tends to come with longer duration and
higher summer exposure. For geoscience models, explainable-AI (XAI) attributions
over collinear predictors are unstable: small input changes can reallocate credit
between correlated features without changing the outcome.

Implications BASIN honors:

- The weight **components shown per scenario are arithmetic contributions under the
  chosen weights** — they are not claimed to be independent causal importance.
- No feature-importance or SHAP-style attribution is computed or claimed.
- The shortlist is selected primarily by **cluster diversity** (one exemplar per
  cluster) with ranking used to order candidates *within* the pool — so correlated
  features cannot silently collapse the shortlist into one archetype.

## Empirical consequence: duration skew in the shortlist

Measured 2026-09-19 across six generation seeds (22, 7, 101, 3, 55, 99) with the
default weights (severity 40 / duration 25 / concurrence 25 / season 10):

- The candidate pool is roughly balanced by duration class (90d ≈ 97, 180d ≈ 118,
  270d ≈ 85 of 300), yet **every seed produced a shortlist with 4–5 of 6 scenarios
  at 270 days** and only one at 90 or 180.
- Mean cumulative deficit grows strongly with window length in the pool:
  **90d ≈ 91 mm, 180d ≈ 156 mm, 270d ≈ 236 mm**. Cumulative deficit is not a
  duration-independent severity measure.
- The ranking's severity component is already duration-normalized
  (`historical_percentile` against matched windows of the same duration), but the
  **duration component (default 25% weight) is raw `duration_days / 365`**, which
  gives a 270-day window a structural ≈ 12-point advantage over a 90-day window
  (0.74 vs 0.25 × 25). This, not severity, is the dominant driver of the skew.

**Consequence:** with default weights the shortlist concentrates on longer modeled
windows while still spanning multiple cluster archetypes. This is disclosed in the
export report ("Shortlist duration mix: …"). It is **not** a bug in clustering —
clusters form on the full feature vector — but a structural consequence of
expressing the user's duration preference as a raw fraction of 365 days. If a
reviewer wants duration-balanced shortlists, lower the duration weight (e.g., the
"illustrative rural provider" preset) or raise severity. A duration-diversity
selection guarantee was considered and deliberately **not** implemented, because
it would override the user's stated ranking priorities and would replace a
cluster-maximum exemplar with a lower-scored candidate; the honest disclosure in
the report is preferred over silently altering the selection contract.

## Q&A talking point

> "Our ranking is deterministic — same seed, same weights, same candidates, so the
> shortlist is bit-identical on every rerun, which is what lets reviewers audit it.
> We don't claim the per-feature contributions are independent causal importance:
> severity, duration, and concurrence are hydrologically correlated, and we treat
> the weighted components as arithmetic under chosen priorities, not XAI
> attributions. That's also why the shortlist is picked by cluster diversity first —
> so correlated features can't collapse it into a single drought archetype."

## Status

- [x] Deterministic pipeline (seed 22, fixed weights) — verified by tests.
- [x] Weight sliders + rerank + selection comparison in the product.
- [x] This documented position for reviewer/judge Q&A.
- [ ] Optional future work: a bootstrap/leave-one-out sensitivity run over the
  candidate generation seed to empirically quantify cluster-label stability
  (not required for current claims).