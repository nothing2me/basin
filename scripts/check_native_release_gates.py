"""Deterministic release gate checks for BASIN native release hardening (T6).

Verifies prerequisites and environment readiness without downloading files or altering machine state:
1. Windows OS, CPython 3.12 64-bit, and CPU instruction support (AVX2).
2. Microsoft Visual C++ and OpenMP runtime DLLs (MSVCP140.dll, VCOMP140.dll).
3. Core dependencies, data snapshot integrity, and offline startup readiness.
4. Local loopback port availability (8501-8550).
5. Distribution / frozen package hygiene (no secrets, local sessions, caches, or large model weights).
6. Embedded model license, provenance, expected hash, and advisory limitations.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
import platform
import socket
import struct
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# Model Provenance & Advisory Constants
MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
MODEL_REVISION = "7dabda4d13d513e3e842b20f0d435c732f172cbe"
MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_SHA256 = "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
MODEL_BYTES = 2104932768
MODEL_LICENSE = "Qwen Research License"
QUANTIZATION = "Q4_K_M"

ADVISORY_LIMITATIONS = [
    "diskcache 5.6.3 (GHSA-w8v5-vhqr-4h9v / CVE-2025-69872): Arbitrary code execution if malicious cache file read. Inactive code path: BASIN never enables LlamaDiskCache or prompt cache.",
    "Model weights are optional (~2.1 GB) and never bundled in release packages; must be fetched via scripts/fetch_model.py under explicit operator authorization.",
    "Native inference requires AVX2/FMA/F16C instructions on CPU; machines lacking AVX2 must use instant direct tools without local LLM.",
]

FORBIDDEN_PACKAGE_PATTERNS = [
    ".gguf",
    ".bin",
    ".safetensors",
    ".env",
    "local/session-",
    "local/review-prefs-",
    "__pycache__",
    ".pyc",
    ".pyo",
]


@dataclass
class GateResult:
    name: str
    status: str  # PASS | FAIL | WARN | NOT_RUN
    detail: str = ""
    remediation: str = ""


@dataclass
class ReleaseGateReport:
    platform_system: str
    python_version: str
    is_64bit: bool
    gates: list[GateResult] = field(default_factory=list)
    model_provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def core_passed(self) -> bool:
        return all(g.status != "FAIL" for g in self.gates if "Optional" not in g.name)


def check_cpu_avx2() -> tuple[bool, str]:
    """Check if processor supports AVX2 on Windows using kernel32.IsProcessorFeaturePresent(40)."""
    if sys.platform != "win32":
        return True, "Non-Windows platform; AVX2 kernel check skipped."
    try:
        # PF_AVX2_INSTRUCTIONS_AVAILABLE = 40
        has_avx2 = bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(40))
        if has_avx2:
            return True, "AVX2 instructions supported by processor."
        return False, "Processor lacks AVX2 instruction support. Native llama-cpp-python will fault."
    except Exception as err:
        return False, f"Could not determine AVX2 support: {err}"


def check_vc_runtime_dlls() -> dict[str, bool]:
    """Detect MSVCP140.dll and VCOMP140.dll in System32 / SysWOW64 / PATH without modifying machine."""
    found = {"msvcp140.dll": False, "vcomp140.dll": False}
    if sys.platform != "win32":
        return {k: True for k in found}

    sys_root = os.environ.get("SystemRoot", r"C:\Windows")
    search_dirs = [
        Path(sys_root) / "System32",
        Path(sys_root) / "SysWOW64",
    ]
    path_dirs = [Path(p) for p in os.environ.get("PATH", "").split(os.path.pathsep) if p]
    search_dirs.extend(path_dirs[:20])

    for dll_name in found:
        for directory in search_dirs:
            try:
                candidate = directory / dll_name
                if candidate.is_file():
                    found[dll_name] = True
                    break
            except (OSError, PermissionError):
                continue
    return found


def check_ports(start_port: int = 8501, count: int = 50) -> tuple[int | None, str]:
    """Check availability of local loopback ports (8501-8550)."""
    for port in range(start_port, min(start_port + count, 65536)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
            return port, f"Port {port} is free on loopback."
        except OSError:
            continue
    return None, f"All {count} ports in range {start_port}-{start_port + count - 1} are occupied."


def check_data_snapshot_integrity(root: Path = ROOT) -> tuple[bool, str]:
    """Check observations.csv matches manifest.json SHA-256."""
    obs_file = root / "data" / "observations.csv"
    manifest_file = root / "data" / "manifest.json"
    if not obs_file.is_file():
        return False, f"Missing data file: {obs_file}"
    if not manifest_file.is_file():
        return False, f"Missing manifest file: {manifest_file}"
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        expected_sha = manifest["sha256"]
        actual_sha = hashlib.sha256(obs_file.read_bytes()).hexdigest()
        if actual_sha == expected_sha:
            return True, f"Observations SHA-256 matches manifest ({actual_sha[:12]}...)."
        return False, f"Observations SHA-256 mismatch (expected {expected_sha[:12]}..., got {actual_sha[:12]}...)."
    except Exception as err:
        return False, f"Failed to verify data snapshot: {err}"


def inspect_package_hygiene(target_path: Path) -> list[str]:
    """Inspect a directory or ZIP file for forbidden files (secrets, sessions, caches, large weights)."""
    target = Path(target_path)
    violations: list[str] = []

    if target.is_file() and target.suffix.lower() == ".zip":
        with zipfile.ZipFile(target) as zf:
            names = zf.namelist()
            for name in names:
                name_norm = name.replace("\\", "/")
                # Check for secrets/credentials
                if "credentials.toml" in name_norm:
                    try:
                        content = zf.read(name).decode("utf-8", "replace")
                        if 'email = ""' not in content:
                            violations.append(f"{name}: contains non-empty credentials")
                    except Exception:
                        violations.append(f"{name}: credentials file present")
                for pattern in FORBIDDEN_PACKAGE_PATTERNS:
                    if pattern in name_norm:
                        violations.append(f"{name}: matches forbidden pattern '{pattern}'")
                # Size check: no file > 50 MB in demo package
                info = zf.getinfo(name)
                if info.file_size > 50 * 1024 * 1024:
                    violations.append(f"{name}: file size ({info.file_size:,} bytes) exceeds 50 MB threshold")
        return violations

    if target.is_dir():
        for item in target.rglob("*"):
            if not item.is_file():
                continue
            rel = item.relative_to(target).as_posix()
            if "credentials.toml" in rel:
                try:
                    content = item.read_text(encoding="utf-8", errors="replace")
                    if 'email = ""' not in content:
                        violations.append(f"{rel}: contains non-empty credentials")
                except Exception:
                    violations.append(rel)
            for pattern in FORBIDDEN_PACKAGE_PATTERNS:
                if pattern in rel:
                    violations.append(f"{rel}: matches forbidden pattern '{pattern}'")
            try:
                size = item.stat().st_size
                if size > 50 * 1024 * 1024:
                    violations.append(f"{rel}: file size ({size:,} bytes) exceeds 50 MB threshold")
            except OSError:
                pass
        return violations

    return [f"Target path does not exist: {target}"]


def get_model_provenance() -> dict[str, Any]:
    """Canonical embedded-model license and provenance metadata."""
    return {
        "repository": MODEL_REPO,
        "revision": MODEL_REVISION,
        "filename": MODEL_FILENAME,
        "expected_sha256": MODEL_SHA256,
        "expected_bytes": MODEL_BYTES,
        "license": MODEL_LICENSE,
        "quantization": QUANTIZATION,
        "hash_verification_location": "basin_core/qwen_runtime.py (MODEL_SHA256)",
        "advisories": list(ADVISORY_LIMITATIONS),
    }


def run_all_gates(root: Path = ROOT, package_to_audit: Path | None = None) -> ReleaseGateReport:
    """Run all deterministic release hardening gates."""
    report = ReleaseGateReport(
        platform_system=f"{platform.system()} {platform.release()}",
        python_version=platform.python_version(),
        is_64bit=struct.calcsize("P") == 8,
        model_provenance=get_model_provenance(),
    )

    # Gate 1: Platform & Architecture
    is_win = sys.platform == "win32"
    is_64 = struct.calcsize("P") == 8
    is_py312 = sys.version_info[:2] == (3, 12)

    if is_win and is_64:
        report.gates.append(GateResult("Gate 1A: OS & Architecture", "PASS", f"Windows 64-bit ({platform.machine()})"))
    else:
        report.gates.append(GateResult(
            "Gate 1A: OS & Architecture", "FAIL",
            f"OS: {sys.platform}, Pointer: {struct.calcsize('P')*8}-bit. Windows 64-bit required.",
            "Run on 64-bit Windows."
        ))

    if is_py312:
        report.gates.append(GateResult("Gate 1B: Python Runtime", "PASS", f"CPython {platform.python_version()}"))
    else:
        report.gates.append(GateResult(
            "Gate 1B: Python Runtime", "FAIL",
            f"Python {platform.python_version()} found. CPython 3.12 required.",
            "Install Python 3.12 (64-bit)."
        ))

    # Gate 2: CPU Instruction Support (AVX2)
    avx2_ok, avx2_detail = check_cpu_avx2()
    if avx2_ok:
        report.gates.append(GateResult("Gate 2: CPU AVX2 Instructions", "PASS", avx2_detail))
    else:
        report.gates.append(GateResult(
            "Gate 2: CPU AVX2 Instructions", "WARN", avx2_detail,
            "Native llama-cpp-python requires AVX2. Direct tools will work; native AI will be unavailable."
        ))

    # Gate 3: VC++ & OpenMP Runtimes
    vc_dlls = check_vc_runtime_dlls()
    msvcp = vc_dlls.get("msvcp140.dll", False)
    vcomp = vc_dlls.get("vcomp140.dll", False)

    if msvcp and vcomp:
        report.gates.append(GateResult("Gate 3: VC++ & OpenMP DLLs", "PASS", "MSVCP140.dll and VCOMP140.dll present."))
    elif msvcp and not vcomp:
        report.gates.append(GateResult(
            "Gate 3: VC++ & OpenMP DLLs", "WARN",
            "VCOMP140.dll (OpenMP) is missing. MSVCP140.dll is present.",
            "Install Microsoft Visual C++ 2015-2022 Redistributable (x64) for OpenMP multi-threading in native AI."
        ))
    else:
        report.gates.append(GateResult(
            "Gate 3: VC++ & OpenMP DLLs", "WARN",
            f"MSVCP140.dll: {msvcp}, VCOMP140.dll: {vcomp}.",
            "Install Microsoft Visual C++ 2015-2022 Redistributable (x64) before using native AI."
        ))

    # Gate 4: Core Dependencies
    missing_deps = []
    for dep in ("streamlit", "pandas", "numpy", "scipy", "sklearn"):
        if importlib.util.find_spec(dep) is None:
            missing_deps.append(dep)
    if not missing_deps:
        report.gates.append(GateResult("Gate 4: Core Dependencies", "PASS", "All core packages importable."))
    else:
        report.gates.append(GateResult(
            "Gate 4: Core Dependencies", "FAIL",
            f"Missing packages: {', '.join(missing_deps)}.",
            "Run 'Setup BASIN.cmd' to install requirements."
        ))

    # Gate 5: Data Snapshot Integrity
    snap_ok, snap_detail = check_data_snapshot_integrity(root)
    if snap_ok:
        report.gates.append(GateResult("Gate 5: Data Snapshot Integrity", "PASS", snap_detail))
    else:
        report.gates.append(GateResult(
            "Gate 5: Data Snapshot Integrity", "FAIL", snap_detail,
            "Restore original data/observations.csv from git snapshot."
        ))

    # Gate 6: Local Port Availability
    free_port, port_detail = check_ports(8501, 50)
    if free_port is not None:
        report.gates.append(GateResult("Gate 6: Local Loopback Port", "PASS", port_detail))
    else:
        report.gates.append(GateResult(
            "Gate 6: Local Loopback Port", "FAIL", port_detail,
            "Close older BASIN or Streamlit processes occupying ports 8501-8550."
        ))

    # Gate 7: Offline Startup Configuration
    cred_file = root / ".streamlit" / "credentials.toml"
    if cred_file.is_file() and 'email = ""' in cred_file.read_text(encoding="utf-8", errors="replace"):
        report.gates.append(GateResult("Gate 7: Offline Startup Credentials", "PASS", ".streamlit/credentials.toml suppresses prompt."))
    else:
        report.gates.append(GateResult(
            "Gate 7: Offline Startup Credentials", "WARN",
            "credentials.toml missing or has non-empty email.",
            "Run launcher or write [general] email = '' to .streamlit/credentials.toml."
        ))

    # Gate 8: Optional Package Hygiene Audit (if package provided)
    if package_to_audit is not None:
        violations = inspect_package_hygiene(package_to_audit)
        if not violations:
            report.gates.append(GateResult(
                "Gate 8: Package Hygiene", "PASS",
                f"Audited {package_to_audit.name}: zero leaks, weights, or secrets."
            ))
        else:
            report.gates.append(GateResult(
                "Gate 8: Package Hygiene", "FAIL",
                f"Audited {package_to_audit.name}: {len(violations)} violations found:\n  - " + "\n  - ".join(violations[:5]),
                "Re-run packaging without prohibited files."
            ))

    return report


def render_report(report: ReleaseGateReport) -> str:
    lines = [
        "=" * 70,
        "BASIN Native Release Hardening Gates (T6)",
        "=" * 70,
        f"Environment: {report.platform_system} | Python: {report.python_version} (64-bit: {report.is_64bit})",
        "",
        "Gate Status Summary:",
        "-" * 70,
    ]
    for gate in report.gates:
        status_box = f"[{gate.status}]".ljust(10)
        lines.append(f"{status_box} {gate.name}")
        lines.append(f"           Detail: {gate.detail}")
        if gate.remediation:
            lines.append(f"           Action: {gate.remediation}")
        lines.append("")

    lines.append("-" * 70)
    lines.append("Embedded Model Provenance & Advisory:")
    lines.append(f"  Model:       {report.model_provenance.get('filename')}")
    lines.append(f"  Repo/Rev:    {report.model_provenance.get('repository')} @ {report.model_provenance.get('revision')[:10]}")
    lines.append(f"  SHA-256:     {report.model_provenance.get('expected_sha256')}")
    lines.append(f"  Bytes:       {report.model_provenance.get('expected_bytes'):,} bytes (~2.1 GB)")
    lines.append(f"  License:     {report.model_provenance.get('license')}")
    lines.append("  Advisories:")
    for adv in report.model_provenance.get("advisories", []):
        lines.append(f"    * {adv}")
    lines.append("=" * 70)
    lines.append(f"Overall Core Readiness: {'PASS (Ready for Showcase)' if report.core_passed else 'FAIL (Remediation Required)'}")
    lines.append("=" * 70)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-package", type=Path, help="Audit a release ZIP or bundle folder for hygiene")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args(argv)

    report = run_all_gates(ROOT, args.audit_package)
    if args.json:
        data = asdict(report)
        data["core_passed"] = report.core_passed
        print(json.dumps(data, indent=2))
    else:
        print(render_report(report))

    return 0 if report.core_passed else 1


if __name__ == "__main__":
    sys.exit(main())
