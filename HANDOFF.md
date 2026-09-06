# BASIN current handoff

Updated: 2026-09-06

## Current state

BASIN is cloned from https://github.com/nothing2me/basin.git at ebd8d59 on main. The latest fetch completed successfully; compare output is recorded below. The shared TODO.md now divides outstanding work into 12 workstreams with subtask IDs, proposed ownership lanes, dependencies, acceptance criteria, a first parallel session, and a final demo gate. Real owners/reviewers remain unclaimed. New evidence features and reservoir scope remain proposals for team confirmation, not approved architecture changes.

The existing core generates, groups, ranks, reviews and exports rainfall scenarios from a verified NOAA snapshot. Local JSON/JSONL stores sessions and audit snapshots. The main unresolved product mismatch is rainfall-only documented scope versus reservoir/engineering claims in the implementation. Evidence conflict review is not yet implemented. Prior review reproduced a surplus-inflow conservation defect in the reservoir function.

## Files changed

- TODO.md: added the shared team task board requested by the user.
- HANDOFF.md: replaced onboarding state with the current planning checkpoint.
- No application source, dependencies, tests or data changed. The user authorized committing and pushing these two planning documents to Basin.

## Verification

- git fetch origin completed successfully before planning.
- Reviewed current git status, handoff and validation notes; used the previously reviewed implementation and supplied design/build-plan/audit/event documents.
- Documentation validation passed: 12 workstreams, 97 unique subtasks, all workstream references and board entries resolved, no trailing whitespace. git diff --check passed; the pre-commit fetch confirmed HEAD was 0 ahead / 0 behind origin/main. This documentation change contains only TODO.md and HANDOFF.md.
- Full pytest, offline rehearsal and GUI remain unrun in this clone; B02 owns establishing the executable baseline. Prior documented test counts are not newly verified results.
- The earlier Windows CSV checksum issue is corrected in this clone only; B02.5 assigns the portable fresh-checkout fix. No committed CSV content was changed.

## Blockers

- Team must confirm scope, claim owner/reviewer names, choose the first P1 feature, and resolve the reservoir path in B01/B08.
- Actual submitted Stage 1 answers and any newer organizer instructions remain to be located/confirmed.
- The target demo environment and practitioner validation still require evidence; the board does not assume they are complete.

## Next action

Team completes B01's short scope/ownership discussion. In parallel, lane A reviews assumptions/geography (B07) and drafts the evidence contract (B03); lane B establishes a reproducible test baseline (B02); lane C prepares the analyst exercise (B09) and claim inventory (B11). Coordinate shared app.py and audit-schema edits before implementation. Keep task status in TODO.md and only current state here.
