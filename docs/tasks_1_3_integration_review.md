# Tasks 1–3 integration review

Base: origin/main 0b3d903. Integrated native-runtime-install 568271e (implementation 51084b7), numerical-meaning 1d80285 (implementation 9332b2b), and pdf-report-failure-handling 105d715. Existing upstream P0-A through P0-D changes are preserved; their older claims are not blanket endorsements by this review.

## Review fixes

- Explicit --wheelhouse requests now fail without running pip if no native wheel exists; they cannot silently switch online.
- Native import probes require both a successful exit and a success payload.
- Both PDF download locations disclose the renderer; degraded previews use a warning. Browser output must have a PDF signature rather than just a minimum size. Signature checking is not a complete PDF parser/validity check.
- Fallback wording does not guarantee identical layout or character support. Windows remains explicitly vector-only; no untested browser-path activation.
- Pipeline availability is a declared boolean tool argument. JSON-schema checks still reject booleans as percentages; the generic finite-number check no longer rejects legitimate pipeline flags.
- The assistant setup hint names both runtime and weights.
- pytest creates the configured temporary-directory parent on a fresh worktree. The first focused invocation failed on missing tmp/ before application tests could execute; this was corrected.
- Diskcache's documented rationale is an inactive code path, not invented named-human risk acceptance.

## Evidence and limits

See newest HANDOFF entry for final test count. A focused run initially reported 110 passed, one genuine-wheel skip and one fixture failure: the mock renderer wrote HTML without a PDF signature. Corrected the protocol fixture; its consent-forwarding test is not evidence of actual browser rendering. Final full-suite results supersede this preliminary run.

Snapshot, smoke (5acf2b4ebdfe, five scenarios, 500 audit records, zero custom comparisons), explicit replay with implementation_matches_current true, source packaging and installation-consistency checks passed. Routing: 50/50 against the branch's revised expectations; four examples require clarification, so this is not 50 successful numerical answers or a comparison to the old benchmark.

Independently checked GitHub release metadata for the v0.3.35 Windows wheel: 7,086,788 bytes and SHA-256 31590ea000d5aff6f05f1e428048e72318a83709288159a5bd4dabec530080bb match the pin. Source: https://api.github.com/repos/abetlen/llama-cpp-python/releases/tags/v0.3.35 . No fresh native binary installation, model download or live inference was performed in this integration pass. Claude's separate developer-machine wheel-install evidence remains in its handoff and does not certify the presentation laptop.

The diskcache advisory remains listed for <=5.6.3 with no patched release: https://github.com/advisories/GHSA-w8v5-vhqr-4h9v . BASIN's runtime does not enable the disk cache. This is a scoped code-path rationale, not absence of a vulnerable dependency. The previous advisory scan and its native-component exclusions were not replaced by a new binary scan here.

## Compatibility and next work

Version-1 saved simulation results are not silently migrated: rerun and re-review the experiment before exporting under the new threshold contract. Do not delete sessions to bypass validation.

Continue Task 4 (actual UI acceptance), Task 5 (current-status reconciliation), and Task 6 (presentation laptop/offline/user/rehearsal acceptance). Keep these follow-ups visible: Region N assistant simulations versus selectable Review systems; operational-sounding takeaways; legacy report argument percentage ambiguity; custom-observation source wording; VC++/CPU requirements and offline vcomp140.dll; model license/provenance. Storage timing remains illustrative and needs a separate calibration/domain decision for operational use.


## Upstream follow-up before push

Origin advanced through 5d83fcd while verification was running. Merged the six upstream commits, preserving the newer Review intake, hydrology/sector delivery and unit displays. Resolved capacity selection using the sum of the configured regional capacities. Retained inclusive/day-zero threshold calculations rather than restoring the old truthiness checks, including the new pipeline comparison. These integration checks are not independent scientific certification of the newly merged hydrology assumptions.

The initial full run finished after 9:10:39 wall time with 550 passed, two skips and one AppTest 90-second timeout in Show all tools. No root cause for that timeout is asserted. After upstream integration, the focused Review/numerical/water-system suite passed 92 tests in 81.06s without raising the timeout. The final full-suite result is recorded in HANDOFF.md and supersedes that preliminary failure. Final snapshot/smoke/replay were rerun because the upstream simulator changed.

Final combined verification: **565 passed, 2 skipped in 572.43s**, with explicit skips for genuine native wheels and Qwen model weights. Final smoke run a57f4a988ade and explicit replay passed with implementation_matches_current true. No full-suite failures remain.
