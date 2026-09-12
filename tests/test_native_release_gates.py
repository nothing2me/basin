"""Automated tests for BASIN T6 native release hardening gates.

Validates deterministic checks for:
- Windows VC++ / OpenMP runtimes (MSVCP140, VCOMP140)
- CPU architecture and instruction sets (AVX2)
- Port scanning and port exhaustion handling
- Data snapshot integrity verification
- Frozen package hygiene inspection (leak, secret, cache, and weight detection)
- Embedded model provenance, license, hash, and advisory metadata
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_native_release_gates as gates  # noqa: E402
import launcher  # noqa: E402
import install_native_runtime as native  # noqa: E402


# --------------------------------------------------------------------------------------
# 1. CPU & Instruction Support (AVX2)
# --------------------------------------------------------------------------------------

def test_check_cpu_avx2_real():
    ok, msg = gates.check_cpu_avx2()
    if sys.platform == "win32":
        assert isinstance(ok, bool)
        assert "AVX2" in msg
    else:
        assert ok is True


def test_check_cpu_avx2_mock_missing(monkeypatch):
    if sys.platform != "win32":
        pytest.skip("Windows-specific kernel32 check")
    mock_kernel32 = MagicMock()
    mock_kernel32.IsProcessorFeaturePresent.return_value = 0
    monkeypatch.setattr(gates.ctypes.windll, "kernel32", mock_kernel32)

    ok, msg = gates.check_cpu_avx2()
    assert ok is False
    assert "lacks AVX2" in msg


def test_unsupported_reason_flags_missing_avx2():
    reason = native.unsupported_reason(
        sys_platform="win32",
        machine="AMD64",
        pointer_bits=64,
        version=(3, 12),
        implementation="CPython",
        in_venv=True,
        has_avx2=False,
    )
    assert reason is not None
    assert "AVX2" in reason


# --------------------------------------------------------------------------------------
# 2. VC++ and OpenMP Runtime Components (MSVCP140, VCOMP140)
# --------------------------------------------------------------------------------------

def test_check_vc_runtime_dlls_structure():
    dlls = gates.check_vc_runtime_dlls()
    assert "msvcp140.dll" in dlls
    assert "vcomp140.dll" in dlls
    for name, found in dlls.items():
        assert isinstance(found, bool)


def test_vc_runtime_diagnostic_hints_when_vcomp_missing(monkeypatch):
    monkeypatch.setattr(gates, "check_vc_runtime_dlls", lambda: {"msvcp140.dll": True, "vcomp140.dll": False})
    report = gates.run_all_gates(ROOT)
    gate3 = next(g for g in report.gates if "Gate 3" in g.name)
    assert gate3.status == "WARN"
    assert "VCOMP140.dll (OpenMP) is missing" in gate3.detail
    assert "Microsoft Visual C++ 2015-2022 Redistributable" in gate3.remediation


def test_vc_runtime_diagnostic_hints_when_both_missing(monkeypatch):
    monkeypatch.setattr(gates, "check_vc_runtime_dlls", lambda: {"msvcp140.dll": False, "vcomp140.dll": False})
    report = gates.run_all_gates(ROOT)
    gate3 = next(g for g in report.gates if "Gate 3" in g.name)
    assert gate3.status == "WARN"
    assert "Microsoft Visual C++ 2015-2022 Redistributable" in gate3.remediation


def test_install_native_runtime_probe_hints_missing_vcomp(monkeypatch):
    monkeypatch.setattr(native, "check_vc_runtime_dlls", lambda: {"msvcp140.dll": True, "vcomp140.dll": False})
    # Probe result simulating DLL not found exit code
    completed = native.subprocess.CompletedProcess(["python"], returncode=0xC0000135, stdout="", stderr="")
    monkeypatch.setattr(native.subprocess, "run", lambda *a, **k: completed)

    status = native.probe_runtime("python", "0.3.35")
    assert status.state == "crashed"
    assert "VCOMP140.DLL" in status.detail
    assert "Visual C++ 2015-2022 Redistributable" in status.hint


# --------------------------------------------------------------------------------------
# 3. Port Allocation & Exhaustion Handling
# --------------------------------------------------------------------------------------

def test_check_ports_finds_free_port():
    port, msg = gates.check_ports(8501, 50)
    assert port is not None
    assert 8501 <= port <= 8550
    assert f"Port {port} is free" in msg


def test_check_ports_detects_exhaustion(monkeypatch):
    class MockSocket:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def bind(self, addr):
            raise OSError("Address already in use")

    monkeypatch.setattr(gates.socket, "socket", lambda *a, **k: MockSocket())
    port, msg = gates.check_ports(8501, 10)
    assert port is None
    assert "All 10 ports" in msg
    assert "occupied" in msg


def test_launcher_find_free_port_exhaustion_raises(monkeypatch):
    class MockSocket:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass
        def bind(self, addr):
            raise OSError("Port in use")

    monkeypatch.setattr(launcher.socket, "socket", lambda *a, **k: MockSocket())
    with pytest.raises(RuntimeError) as exc:
        launcher.find_free_port(8501, 5)
    assert "No free local port found" in str(exc.value)


# --------------------------------------------------------------------------------------
# 4. Data Snapshot Integrity
# --------------------------------------------------------------------------------------

def test_data_snapshot_integrity_passes_on_real_repo():
    ok, msg = gates.check_data_snapshot_integrity(ROOT)
    assert ok is True
    assert "matches manifest" in msg


def test_data_snapshot_integrity_fails_on_corrupted_data(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "observations.csv").write_bytes(b"date,value\n2020-01-01,1.23\n")
    (data_dir / "manifest.json").write_text(json.dumps({"sha256": "00000000000000000000000000000000"}), encoding="utf-8")

    ok, msg = gates.check_data_snapshot_integrity(tmp_path)
    assert ok is False
    assert "mismatch" in msg


# --------------------------------------------------------------------------------------
# 5. Frozen Package Hygiene Audit
# --------------------------------------------------------------------------------------

def test_package_hygiene_clean_zip(tmp_path):
    zip_path = tmp_path / "clean_package.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("BASIN/app.py", "# clean code")
        zf.writestr("BASIN/README.md", "# BASIN")
        zf.writestr("BASIN/data/observations.csv", "date,val\n")
        zf.writestr("BASIN/.streamlit/credentials.toml", '[general]\nemail = ""\n')
    violations = gates.inspect_package_hygiene(zip_path)
    assert violations == []


def test_package_hygiene_catches_leaks_and_weights(tmp_path):
    zip_path = tmp_path / "dirty_package.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("BASIN/app.py", "# code")
        zf.writestr("BASIN/models/weights.gguf", b"fake heavy weights" * 100)
        zf.writestr("BASIN/.env", "SECRET_KEY=12345")
        zf.writestr("BASIN/local/session-abc.json", '{"private": true}')
        zf.writestr("BASIN/.streamlit/credentials.toml", '[general]\nemail = "user@example.com"\n')
        zf.writestr("BASIN/basin_core/__pycache__/app.cpython-312.pyc", b"bytecode")

    violations = gates.inspect_package_hygiene(zip_path)
    assert any(".gguf" in v for v in violations)
    assert any(".env" in v for v in violations)
    assert any("local/session-" in v for v in violations)
    assert any("credentials.toml" in v for v in violations)
    assert any("__pycache__" in v for v in violations)


def test_package_hygiene_clean_directory(tmp_path):
    pkg_dir = tmp_path / "clean_dir"
    pkg_dir.mkdir()
    (pkg_dir / "app.py").write_text("# clean code", encoding="utf-8")
    (pkg_dir / "credentials.toml").write_text('[general]\nemail = ""\n', encoding="utf-8")

    violations = gates.inspect_package_hygiene(pkg_dir)
    assert violations == []


# --------------------------------------------------------------------------------------
# 6. Embedded Model Provenance & Advisory Metadata
# --------------------------------------------------------------------------------------

def test_embedded_model_provenance_metadata():
    prov = gates.get_model_provenance()
    assert prov["repository"] == "Qwen/Qwen2.5-3B-Instruct-GGUF"
    assert prov["revision"] == "7dabda4d13d513e3e842b20f0d435c732f172cbe"
    assert prov["filename"] == "qwen2.5-3b-instruct-q4_k_m.gguf"
    assert prov["expected_sha256"] == "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
    assert prov["expected_bytes"] == 2104932768
    assert prov["license"] == "Qwen Research License"
    assert prov["quantization"] == "Q4_K_M"
    assert "basin_core/qwen_runtime.py" in prov["hash_verification_location"]
    assert len(prov["advisories"]) >= 3
    assert any("diskcache 5.6.3" in adv for adv in prov["advisories"])


# --------------------------------------------------------------------------------------
# 7. End-to-End Gates Evaluation & Reporting
# --------------------------------------------------------------------------------------

def test_run_all_gates_and_render_report():
    report = gates.run_all_gates(ROOT)
    assert len(report.gates) >= 7
    # Verify core gates status
    core_names = [g.name for g in report.gates]
    assert any("OS & Architecture" in n for n in core_names)
    assert any("Python Runtime" in n for n in core_names)
    assert any("CPU AVX2" in n for n in core_names)
    assert any("VC++ & OpenMP DLLs" in n for n in core_names)
    assert any("Core Dependencies" in n for n in core_names)
    assert any("Data Snapshot Integrity" in n for n in core_names)
    assert any("Local Loopback Port" in n for n in core_names)

    rendered = gates.render_report(report)
    assert "BASIN Native Release Hardening Gates" in rendered
    assert "Embedded Model Provenance & Advisory:" in rendered
    assert "Qwen Research License" in rendered

    # JSON serialization must work cleanly
    data = json.loads(json.dumps(gates.asdict(report)))
    assert "gates" in data
    assert "model_provenance" in data
