# BASIN security review — September 8, 2026

Scope: local source review and regression tests of assistant routing, custom-data/export consent, upload and packet boundaries, launchers and source packaging. Baseline f96c28a. This is not a penetration-test certification, scientific review or guarantee of no vulnerabilities. No external targets were scanned and no team messages were sent.

## Findings and changes

| Finding | Impact | Disposition |
|---|---|---|
| Assistant used default Ollama client configuration | Environment host/proxy configuration could route questions/history away from intended local service | Fixed application endpoint to 127.0.0.1:11434; disabled environment proxies and redirects; 30-second timeout. Cloud-named or remote-metadata models filtered; exact preferred tags selected. Mocked client-boundary regression tests added. |
| Malformed assistant arguments were silently defaulted | Wrong year/scenario/settings could be presented as answers to the user's question | Added schema validation, unknown-field rejection, finite/range checks and scenario lookup. Reservoir tools require exact scenario ID; ambiguous conservation fractions rejected. Direct tool entry uses the same validation. |
| Untrusted model calls/history lacked explicit bounds | Excess tool work or forged history roles | Four tool calls per answer; 20,000-character question limit; only last ten user/assistant history entries forwarded with bounded content. Unknown tools cannot execute. This does not prove correct intent interpretation. |
| CLI exports automatically included notes | Private notes could leave local sessions without an explicit export choice | Added --include-notes and --include-custom; defaults are false and passed to exporter. Consent parsing and propagation tested. |
| Model name inserted into unsafe HTML | Untrusted local-service text interpreted as markup | Escaped displayed model name. |
| Source package recursively included untracked eligible files | Private Markdown/JSON/CSV placed under source directories could be distributed | Package candidates filtered to Git-tracked files. Reject symlinks/out-of-repository targets; optional wheel paths also checked. Packaging now requires a Git checkout. Tracked material still needs human release-content review. |

## Inspected existing protections

- Both launchers and Streamlit configuration bind to loopback; no shell=True or eval/exec/pickle deserialization found in the inspected launcher/upload/custom-data/workspace paths.
- CSV parser bounds original bytes (10 MiB), row counts, dates and numerical values; existing upload tests exercise malformed input and identity preservation.
- Bundle verification restricts inventory, rejects duplicate entries and caps declared uncompressed contents at 100 MB. It reads archive members rather than extracting paths into the filesystem.
- Saved custom originals are local JSON data, not encrypted storage. Privacy assumes appropriate Windows account/file permissions. Hashes identify contents, not trustworthy authors or immunity to coordinated tampering.
- PDF HTML escapes dynamic notes/identifiers and note export defaults off. The PDF fallback and UI export failures found before this pass are still separate release blockers.

## Evidence and limits

Focused assistant/security/upload/integrity run: 79 passed before adding the packaging regression. Full-suite result and smoke/package checks are recorded in HANDOFF.md. pip check reported no broken installed dependencies; this is not a CVE audit and does not prove requirements.txt is fully installed. In particular, Ollama is absent from this environment.

Open security/release gates:

- Run real Ollama client/model tests and observe outbound traffic on the presentation machine. A fixed local endpoint does not constrain what a separately managed daemon does; model-name filtering is not daemon attestation. Verify HTTP redirect refusal against the installed client version.
- Audit dependency advisories and pin/test the optional Ollama stack; existing ollama>=0.4.0 is not a reproducible pin. No advisory scan completed in this pass.
- Test actual browser/native networking, download paths and PDF subprocess/fallback behavior. Review frozen package for accidentally tracked private material and symlink/junction behavior on target Windows.
- Run broader adversarial routing evaluation, custom-comparison assistant coverage, and malformed saved-session resource-limit checks. Current tests are bounded regression evidence, not exhaustive fuzzing.
- Fix the pre-existing PDF/export regressions before claiming release readiness. Review the complete app for remaining output-injection surfaces during UI/UX work.

No UI redesign, numerical model change, live cloud test or production deployment was part of this pass.
