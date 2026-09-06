# Packet verification contract — BASIN 0.2 / schema 2.0

The verifier reports internal consistency within this contract. It does not establish that supplied sources or audit events are truthful. Bundles are unsigned.

| Exported claim | Verification |
|---|---|
| File inventory and payload bytes | Exact required inventory, no duplicate ZIP entries, SHA-256 for every payload, size limit |
| Run/schema/snapshot identity | Manifest and audit agree; embedded observations match their snapshot hash; supported schema/software version required |
| Original rainfall construction | Declared synchronized source window, duration, station identities and valid retention factors reconstructed for every candidate |
| Edits and approvals | Each scale/replacement and revision transition replayed; previous/current/event digests and final approval state checked |
| Accepted shortlist | Unique existing audit records; selected list fully reviewed; accepted IDs exactly match exported content |
| Daily rainfall | Exact dates, station order, scenario identity, revision, units and values checked against replay |
| Features and ranking | Every candidate feature, score and normalized score component recomputed; summary rows/columns and values checked |
| Evidence and conflicts | Required fields, distinct IDs, scenario references, conflict links/statuses and disposition requirements validated |
| Private annotations | Recursively excluded when the privacy flag is false, including evidence history |
| Readable brief | Regenerated from audited records; must match the included brief |
| Source publisher/date/geographic truth, expert status | Human review needed; content recorded and hash-checked only |
| KMeans groups, profile labels, selection history, saved comparison results | Recorded and hash-checked only; not semantically replay-certified |
| Software identity | Named implementation file hashes and dependency versions recorded; source hash list checked for internal consistency; current-source match reported separately |
| Performance and energy | Recorded measurements/assumptions, not independently reproduced by bundle verification |
| Reservoir experiment | Excluded from the packet and every verification claim |

Negative tests recompute hashes after changing audit records, approval digests, summaries, dates, stations, units, values, evidence references and the brief. This tests semantics beyond stale-checksum rejection. It is not a claim of resistance to coordinated fabrication.

Version 1.0 bundles require re-export from their original sessions. Version 1.0 sessions can migrate after validating source identity, rainfall content and review history. Migration adds provisional evidence and normalizes the CSV index label in digests. It does not invent historical expert approval.

Independent review procedure: create a packet with a multiplier, CSV replacement, rejection, changed weights and unresolved evidence conflict. Have the intended reviewer replay it using the documented environment, inspect the CSV/brief without coaching, and record any disagreement in `validation_notes.md`. Automated checks do not complete that human review gate.
