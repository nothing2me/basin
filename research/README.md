# BASIN data research and documentation

Owner: BASIN research/evidence workstream (B03), with policy review B07 and validation B09. Updated 2026-09-06.

**Start with [review findings](review_findings.md). The imported AI packet contains factual errors and unverified claims. Its own `reviewed` and `adopted` labels are inherited claims, not team approval. Nothing in this folder changes the application or authorizes automatic ingestion.**

## Read in this order

1. [Review findings and immediate team tasks](review_findings.md): corrections, policy extraction, gaps and acceptance criteria.
2. [Research agent brief](research_agent_brief.md): detailed assignment, website/evidence requirements and primary-source shortlist. The review supersedes its earlier PDF-access checkpoint.
3. [Source review register](source_review.json): one assessment for each imported E001–E011 record, with outstanding verification requirements.
4. [Original Markdown packet](incoming/BASIN_Research_Packet.md), [HTML rendition](incoming/BASIN_Research_Packet.html), and [original source register](incoming/source_register.json): preserved research inputs, including their errors. Open the HTML locally to view its styled layout. Read the review alongside it.
5. [Supplied City drought plan](sources/wat-drought-contingency-plan.pdf): 77-page policy snapshot, cover amended June 2026. [Import manifest](import_manifest.json) records exact hashes and sizes.

## Scope and provenance

This folder is an evidence library for the rainfall-scenario prototype. Research proposals are not implemented features or validated forecasts. The root [README](../README.md), [methodology](../docs/methodology.md) and [team TODO](../TODO.md) describe the software and work plan.

The three files in the supplied `Javascript example` directory are byte-identical duplicates of the packet files. There is no JavaScript implementation in that example: its HTML is static and the remaining file is a dummy text file. The supplied `basin_repo` has the same application content as the existing clone after line-ending normalization; its older handoff adds no feature. Neither duplicate tree nor Git metadata is copied here.

Original packet bytes are preserved for audit, not silently corrected. All new corrections live outside `incoming/`. The PDF was supplied by the user; its hash identifies these bytes, not a verified match to today's municipal download. Public accessibility does not establish blanket redistribution rights for every linked dataset. Record source-specific terms before redistributing additional material.

The PDF is retained for offline page-level verification. Research material is separate from application observations and is not a new runtime dependency. Keep future raw datasets, credentials and machine-generated bulk downloads out of Git; publish compact provenance and reproducible retrieval instructions instead.

## Contributing

For each new claim record: publisher, direct URL, exact artifact/version, publication and effective dates separately, retrieval date, page or dataset selector, geographic and temporal scope, variable, unit, quality flags, transformation and denominator, limitations, and reviewer status. Hash only bytes actually obtained. Use `null` for unknowns. A landing page is not proof that its linked document was read.

Separate observations, modeled outputs, policy text, assumptions and practitioner judgments. Preserve disagreement until date, geography, metric and denominator explain it. Never resolve conflicts by choosing whichever value looks more plausible.
