# Task 5 handoff — status board consolidation

Worktree: `C:\Users\moham\Documents\GitHub\basin-status-reconciliation`
Branch: `task/status-reconciliation`
Base: `origin/main` at `5679637145560d7d5ed6b9831255a0877ec699d8` (not merged, not pushed)

Documentation-only pass, as scoped. No application code, test, or dependency file was
touched — see the `git diff --stat` output below.

## What I read before editing

`TODO.md` and `HANDOFF.md` in full (601 and 444 lines respectively at the base commit),
`docs/next_tasks/05_status_reconciliation.md` (this task's own prompt, matches what I was
given), and the merged-work evidence: `docs/tasks_1_3_integration_review.md`,
`docs/native_runtime_handoff.md`, `docs/numerical_meaning_handoff.md`,
`docs/pdf_failure_handoff.md`. I also read `basin_core/simulation.py`,
`basin_core/workspace.py`, `basin_core/exporter.py` and `tests/test_simulation_contract.py`
directly to independently confirm the B16 (saved simulations) claim below, rather than
trusting either the old "fully open" board line or a handoff's self-report on its own.

I confirmed via `git merge-base --is-ancestor` that my own prior Task 3 work (PDF,
`105d715`) is merged into this base, but my prior Task 4 work
(`task/review-acceptance-checks`, `864d95f`) is **not** — the two CSS accessibility fixes
and the real-browser verification evidence from that branch exist only there. I treated
its claims as real but unmerged, not as part of "current" `main` capability, and said so
explicitly everywhere I referenced it.

## What I changed and why

### `HANDOFF.md` (rewritten)

Archived the entire prior file verbatim to
`docs/archive/handoff_history_through_2026-09-11.md` (444 lines, byte-for-byte except a
new introductory note explaining it's an archive). Replaced `HANDOFF.md` with a single
current-status section that:

- States what's merged and current, per task area, with the
  implemented/automatically-tested/device-tested/human-reviewed distinction the task
  asked for, and cites the specific test files/modules backing each "automatically
  tested" claim.
- Explicitly corrects the record on B16 (saved simulations): it was carried as fully
  open across three checkpoints after P0-C actually implemented it on 2026-09-10. I
  independently verified this by reading the code and tests (see above), not by trusting
  the P0-C handoff's own claim.
- Explicitly does **not** upgrade Task 4's UI-acceptance claims. The archived HANDOFF
  said "Verified across desktop (1280px) and narrow viewports (375px/640px)... Verified
  Step 5 & 6 tutorial targets" for the tailored Review panel. My own Task 4 session
  (recorded in `docs/review_acceptance_handoff.md`, which lives only on the unmerged
  `task/review-acceptance-checks` branch) could not reproduce the narrow-viewport or
  tutorial-popover parts of that claim — window resize had no effect in that browser
  session (confirmed with a control test on an unrelated page) and two `st.popover`
  menus wouldn't open under automation. I did not delete the old claim (it's preserved
  verbatim in the archive) but I did not carry it forward as current-status fact either;
  the new HANDOFF says plainly that it "could not be independently corroborated."
- Lists the open, unresolved, and organizer-format items as explicit questions rather
  than assumed defaults, per the task's instruction to preserve missing
  organizer-format/submission information as questions for the team.

### `TODO.md` (rewritten)

Archived the dated narrative checkpoints (CSV-preview, tutorial/appearance checkpoints,
the September 8 security follow-up and its embedded task-2/task-3 independent reviews,
board-audit corrections, and the two "work session" planning notes) verbatim to
`docs/archive/todo_narrative_history_2026-09.md`. Kept and updated in `TODO.md`:

- A new, short "Current status" section at the top mirroring HANDOFF's, plus an explicit
  "do not repeat" line naming Ollama-client-pinning and PDF-fixture-isolation as done —
  the task's own example of an obsolete next step. That exact obsolete instruction
  ("test and pin the optional Ollama Python client... Task 4 is still needed") is still
  visible in the archive (it's dated evidence of a since-completed step under an old
  numbering scheme), but it no longer appears as live guidance.
- The full B01–B14, B19–B21 board, essentially unchanged (I found no incorrect claims in
  it beyond what's listed below), with status lines refreshed to point at the current
  commit/suite rather than repeating stale per-checkpoint counts.
- **B15**: re-stated per `docs/numerical_meaning_handoff.md`'s own §6 "suggested board
  updates" (B15.2 done; B15.3 done for listed inputs with two named remainders left
  unchecked, not silently closed; B15.4 still open) — I used the handoff's own suggested
  wording rather than inventing my own judgment about scope.
- **B16**: changed from three fully-unchecked items to three checked items with an
  explicit "still open: named human review" caveat, backed by the code/test citations
  above — this was the task's own explicit example of what not to leave wrong
  ("Saved simulations already exist in upstream P0-C; do not describe all of B16 as
  unimplemented").
- **B17**: B17.3 and B17.4 were already marked done at the base commit (from my own
  earlier Task 3 integration); I left them as-is and added file/test citations rather
  than re-deriving them, and did not mark B17.5 (device testing) done — nothing in the
  merged code touches actual-device downloads.
- **B18.3**: same treatment as B15.3 — left unchecked, with precisely what's done (most
  argument-validation surfaces) versus not done (the assistant's reservoir tools always
  assume the Region N system even when Review has configured a different one) stated
  inline, per `docs/numerical_meaning_handoff.md` §4.
- **B08, B10, B11, B13**: status lines updated to mention the native-runtime, PDF-outcome
  and tailored-Review work without re-litigating their own subtask checkboxes, since
  those were largely accurate already. B13.5/B13.6/B13.9 gained an explicit note that
  narrow-viewport/tutorial verification remains unconfirmed (matching the HANDOFF
  correction above) rather than silently inheriting the old "verified" framing.
- B19, B20, B21 are explicitly noted as untouched by any of Tasks 1–4, since nothing in
  the merged code affects them and I did not want a reader to infer otherwise from
  proximity to updated sections.

### `README.md`

One sentence corrected. It said the reservoir experiment's "settings, results and
conditional storage bands are excluded from saved evidence packets and their
verification" — true before P0-C, false now: `basin_core/exporter.py`'s
`generate_brief()` explicitly includes saved, reviewed simulations (with their own
declared, non-calibration verification scope) when they exist, and
`verification_scope()`'s schema-2.2 branch removes "reservoir experiment and threshold
timing" from its excluded list. I confirmed this by reading the exporter code directly
(see `exporter.py` lines ~31–39 and ~102–127), not by trusting either doc.

### `docs/claim_inventory.md`

- Corrected one row that was flatly wrong and self-contradicted the same document: it
  said "Upload comparison results enter saved scenarios and the verified ZIP" is
  "Excluded from the current slice," while the same file's own "Saved-simulation and
  multi-sector integration" section (added later, without updating this row or the
  file's dated header) already describes schema 2.2 replay including saved
  comparisons. B14, which implements exactly the excluded-sounding claim, predates this
  file's "Updated: 2026-09-07" date by observation of the board, so this was a real
  documentation lag, not a live contradiction requiring a product decision.
- Updated the file's date/baseline header and added a short note that untouched rows
  still describe their original date's state (I did not attempt a full line-by-line
  re-audit of all ~30 rows — see Limitations).
- Added one new table ("Native runtime, PDF renderer and tailored Review claims")
  covering the three areas this inventory had zero rows for, with the same
  implemented/tested/device/human distinction, including the same explicit
  non-corroboration note about narrow-viewport/tutorial claims as HANDOFF.md.

### `docs/tailored_review_proposal.md`, `docs/tailored_review_handoff.md`

Read both; left unedited. Both already correctly describe the pre-run-questionnaire vs.
Review-panel split and are already marked as their own dated historical narratives (the
proposal doc says "Light/narrow-screen/keyboard and intended-user acceptance remain
open," which matches — not contradicts — my Task 4 findings). No fix needed.

### `docs/methodology.md`

Read (grepped for stale numerical-meaning wording, e.g. "100% Historical Baseline");
found none. Left unedited.

## Separating pre-run questionnaire scope from the Review focus panel

Per the task's explicit instruction, I want this distinction stated plainly rather than
buried in prose: **these are two different UI entry points that write the same
underlying `ReviewPreferences` sidecar, not one feature with two names.** The original
implementation put a skippable setup panel at the top of the Review page. Later work
(merged, "Part A") added a second, earlier entry point — a segmented control on the Data
Dashboard page and an expander in Scenario Builder — that pre-fills the same preferences
before a run is even generated. Both still exist; neither was removed by any task I did.
Whether the team wants one entry point or two is a product decision I have not made and
is not implied by anything in this handoff.

## Evidence: commands run

Documentation-only change, so per the task's own instruction I did not run the full
numerical suite. I did verify links and cited paths:

```
git rev-parse origin/main
# 5679637145560d7d5ed6b9831255a0877ec699d8

git worktree add -b task/status-reconciliation ../basin-status-reconciliation origin/main

git diff --stat
#  HANDOFF.md              | 587 +++++++++++------------------------------------
#  README.md               |   2 +-
#  TODO.md                 | 321 +++++++-------------------
#  docs/claim_inventory.md |  13 +-
#  4 files changed, 239 insertions(+), 684 deletions(-)
#  (plus two new files under docs/archive/, not shown by --stat's default rename detection)

# Existence check for every doc path referenced from the new/edited files:
for f in docs/archive/handoff_history_through_2026-09-11.md \
         docs/archive/todo_narrative_history_2026-09.md \
         docs/status_reconciliation_handoff.md docs/tasks_1_3_integration_review.md \
         docs/native_runtime_handoff.md docs/numerical_meaning_handoff.md \
         docs/pdf_failure_handoff.md docs/claim_inventory.md \
         docs/security_review_2026-09-08.md docs/dependency_advisories_2026-09-09.md \
         docs/ollama_setup.md docs/methodology.md docs/presentation_plan.md \
         docs/verification_scope.md docs/validation_notes.md docs/observation_sheet.md \
         docs/build_validation.md docs/demo_runbook.md docs/ai_use_log.md \
         docs/third_party_materials.md docs/submission_record.md \
         docs/local_upload_and_research_plan.md docs/tailored_review_proposal.md \
         docs/tailored_review_handoff.md docs/report_device_acceptance.md; do
  [ -f "$f" ] && echo "$f: OK" || echo "$f: MISSING"
done
# all OK
```

I also independently re-derived (rather than copied) the B16 claim by reading
`basin_core/simulation.py`, `basin_core/workspace.py` (lines ~59–97, ~265–293),
`basin_core/exporter.py` (lines ~31–39, ~95–128) and `tests/test_simulation_contract.py`'s
test names, and the README/exporter contradiction by reading `exporter.py` directly
rather than trusting either document's prose.

No `pytest`, `demo_smoke.py`, or `replay_bundle.py` run was performed in this pass — the
task explicitly says not to run the full numerical suite for prose-only edits, and
nothing here touches code that those checks would exercise differently than the
last-recorded integration run (565 passed, 2 skipped, cited by reference in the new
HANDOFF rather than re-verified).

## Limitations and things I did not do

- **Not a full line-by-line audit of every doc.** `docs/claim_inventory.md` has ~30
  claim rows; I fixed the one that was actively wrong and self-contradicted the same
  file, and added one new table for the three undocumented areas the task named. I did
  not re-verify every other row (organizer/event rows, agronomic/KBDI rows, etc.)
  against current code — they were not flagged by anything I read as contradicted, but
  "not flagged" is not the same as "independently re-confirmed."
- **`docs/presentation_plan.md`, `docs/build_validation.md`, `docs/demo_runbook.md`,
  `docs/methodology.md` beyond the one grep**: read only enough to confirm they weren't
  obviously contradicted by the reconciliation I was doing; not re-derived from code
  line by line.
- **No new test was written or run.** This is a documentation task; nothing here has
  automated coverage of its own, by design.
- **I did not merge or attempt to resolve the two-entry-point tailored-Review overlap**
  (Scenario Builder vs. Review-page setup panel). I stated it as an open product
  question, per the task's instruction to separate pre-run-questionnaire scope from the
  Review focus panel rather than pick one.
- **I did not merge `task/review-acceptance-checks`.** Its two CSS fixes and its own
  handoff document exist only on that unmerged branch; I referenced them by branch/commit
  rather than assuming Astra has already integrated them.
- No expert approval, participant feedback, organizer requirement, or manual device
  check is claimed or implied anywhere in this handoff or in the edited documents beyond
  what was already recorded (and cited) in the source handoffs I read.

## Files changed

- `HANDOFF.md` — rewritten to a current-status summary; full prior content archived.
- `TODO.md` — current-status section added; dated narrative checkpoints archived; B15/
  B16/B18.3 status corrected per merged evidence; B08/B10/B11/B13 status lines updated to
  reference newer work without re-litigating their subtasks.
- `README.md` — one sentence corrected (reservoir-simulation export scope).
- `docs/claim_inventory.md` — one stale row corrected, header date updated, one new
  table added.
- `docs/archive/handoff_history_through_2026-09-11.md` — new; verbatim archive.
- `docs/archive/todo_narrative_history_2026-09.md` — new; verbatim archive.
- `docs/status_reconciliation_handoff.md` — this file (new).

Not edited: `docs/tailored_review_proposal.md`, `docs/tailored_review_handoff.md`,
`docs/methodology.md`, any application code, any test, any dependency file.
