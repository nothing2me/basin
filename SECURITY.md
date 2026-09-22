# Security policy

## Reporting

Please report suspected vulnerabilities privately to the repository maintainers rather than opening a public issue with exploit details. Include the affected version, reproduction steps, and any relevant logs without private rainfall inputs or exported review notes.

## Supported release

BASIN v1.0.0 is the currently supported release candidate. The core application listens only on local loopback and does not require an account or cloud inference service. The optional Qwen model is downloaded only when the user requests it, from a pinned upstream revision, and is accepted only after its size and SHA-256 match the bundled manifest.

The optional native runtime is supported on 64-bit Windows with CPython 3.12 and AVX2/FMA/F16C. `requirements-native.txt` is hash-locked and refuses source builds. Release checks also verify the required Microsoft C++ and OpenMP DLLs.

`diskcache` is installed as a dependency of `llama-cpp-python`. BASIN does not enable `LlamaDiskCache` or a prompt cache, so the vulnerable malicious-cache-file path described by GHSA-w8v5-vhqr-4h9v is not used. Reassess this decision if disk caching is added.

The current Windows installer is not Authenticode-signed. Verify its SHA-256 against the value in [the release notes](docs/release_draft_v1.0.0.md) before running it.
