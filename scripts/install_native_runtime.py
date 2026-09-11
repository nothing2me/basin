"""Install, repair or check BASIN's OPTIONAL native runtime for the embedded Qwen assistant.

BASIN's core never needs any of this. Local AI inference needs three separate things, and
this script reports each one on its own line so none is mistaken for another:

  runtime    the pinned llama-cpp-python CPU wheel, importable in this environment
  weights    the pinned Qwen GGUF file. This script NEVER downloads weights; use
             scripts/fetch_model.py for that, with an internet connection.
  readiness  runtime and weights both in place. Still not a live inference test.

Run it with the BASIN virtual environment, after the core requirements are installed:

    .venv\\Scripts\\python.exe scripts\\install_native_runtime.py            install
    .venv\\Scripts\\python.exe scripts\\install_native_runtime.py --repair   reinstall the pinned wheel
    .venv\\Scripts\\python.exe scripts\\install_native_runtime.py --check    report only, change nothing

When ``wheelhouse/`` contains the runtime wheel, installation is offline from that folder.
Otherwise pip uses the sources named in requirements-native.txt. Every package that step
may install is hash-locked, so it cannot install anything else or change the core pins.

Only the standard library is used, so the check still works in a damaged environment.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_REQUIREMENTS = ROOT / "requirements-native.txt"
RUNTIME_DISTRIBUTION = "llama-cpp-python"
RUNTIME_WHEEL_GLOB = "llama_cpp_python-*.whl"
PROBE_TIMEOUT_SECONDS = 120

# Windows NTSTATUS values a crashing native import can surface as a process exit code.
_STATUS_ILLEGAL_INSTRUCTION = 0xC000001D
_STATUS_DLL_NOT_FOUND = 0xC0000135
_STATUS_ENTRYPOINT_NOT_FOUND = 0xC0000139
_STATUS_ACCESS_VIOLATION = 0xC0000005

VC_REDIST_HINT = (
    "The runtime DLLs need MSVCP140.dll and VCOMP140.dll, which Python does not ship. "
    "Install the Microsoft Visual C++ 2015-2022 Redistributable (x64) from Microsoft, "
    "then run: \"Setup BASIN.cmd\" --repair-ai")

# Imported in a fresh interpreter so a crashing DLL cannot take this process down with it.
_PROBE_CODE = r"""
import json, sys
try:
    import llama_cpp
except BaseException as err:
    print(json.dumps({"ok": False, "error_type": type(err).__name__, "error": str(err)[:800]}))
    sys.exit(3)
info = {"ok": True, "version": str(getattr(llama_cpp, "__version__", "unknown"))}
try:
    raw = llama_cpp.llama_print_system_info()
    info["system_info"] = (raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)).strip()
except BaseException as err:
    info["system_info"] = "unavailable: " + type(err).__name__
print(json.dumps(info))
"""


# --------------------------------------------------------------------------------------
# Pin and environment
# --------------------------------------------------------------------------------------

def pinned_runtime_version(requirements: Path = NATIVE_REQUIREMENTS) -> str | None:
    """The exact llama-cpp-python version requirements-native.txt pins, or None."""
    try:
        text = requirements.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^\s*llama[-_]cpp[-_]python==([0-9][^\s;\\]*)", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1) if match else None


def unsupported_reason(sys_platform: str | None = None, machine: str | None = None,
                       pointer_bits: int | None = None, version: tuple[int, int] | None = None,
                       implementation: str | None = None, in_venv: bool | None = None) -> str | None:
    """Why this interpreter is not the supported install target, or None when it is."""
    sys_platform = sys.platform if sys_platform is None else sys_platform
    machine = platform.machine() if machine is None else machine
    pointer_bits = (64 if sys.maxsize > 2**32 else 32) if pointer_bits is None else pointer_bits
    version = sys.version_info[:2] if version is None else version
    implementation = platform.python_implementation() if implementation is None else implementation
    in_venv = (sys.prefix != sys.base_prefix) if in_venv is None else in_venv

    if sys_platform != "win32":
        return ("the pinned native wheel is for Windows x64 only; this is "
                f"{sys_platform}. No other platform has a reviewed runtime pin.")
    if machine.upper() not in ("AMD64", "X86_64") or pointer_bits != 64:
        return (f"a 64-bit x64 Python is required; this Python is {pointer_bits}-bit on {machine}. "
                "Install 64-bit Python 3.12 and re-run Setup BASIN.cmd.")
    if implementation != "CPython" or tuple(version) != (3, 12):
        return (f"CPython 3.12 is required; this is {implementation} "
                f"{version[0]}.{version[1]}.")
    if not in_venv:
        return ("this is not a virtual environment. Run it with BASIN's own interpreter, "
                ".venv\\Scripts\\python.exe, so nothing is installed into a system Python.")
    return None


def select_wheelhouse(root: Path = ROOT, override: Path | None = None) -> Path | None:
    """The offline wheel folder to install from, or None to use online sources."""
    folder = override if override is not None else root / "wheelhouse"
    if folder.is_dir() and any(folder.glob(RUNTIME_WHEEL_GLOB)):
        return folder
    return None


def pip_commands(python: str, requirements: Path, wheelhouse: Path | None,
                 repair: bool) -> list[list[str]]:
    """The pip invocations for an install or repair, in order."""
    base = [python, "-m", "pip", "install", "--disable-pip-version-check", "--no-input",
            "--require-hashes", "--only-binary", ":all:"]
    if wheelhouse is not None:
        base += ["--no-index", "--find-links", str(wheelhouse)]
    else:
        base += ["--retries", "2", "--timeout", "30"]
    commands = []
    if repair:
        # Reinstall only the hash-locked native packages; never touch core dependencies.
        commands.append(base + ["--force-reinstall", "--no-deps", "--no-cache-dir",
                                "-r", str(requirements)])
    # The normal install doubles as a dependency check after a repair: hash-checking mode
    # refuses to fetch any missing core dependency instead of silently installing one.
    commands.append(base + ["-r", str(requirements)])
    return commands


# --------------------------------------------------------------------------------------
# Status
# --------------------------------------------------------------------------------------

@dataclass
class RuntimeStatus:
    state: str  # ok | wrong_version | absent | import_error | crashed | timeout
    version: str | None = None
    detail: str = ""
    hint: str = ""
    system_info: str = ""

    @property
    def usable(self) -> bool:
        return self.state == "ok"


@dataclass
class WeightsStatus:
    state: str  # verified | present_unverified | absent | size_mismatch | hash_mismatch | unreadable
    path: str | None = None
    detail: str = ""

    @property
    def usable(self) -> bool:
        return self.state in ("verified", "present_unverified")


@dataclass
class Report:
    runtime: RuntimeStatus
    weights: WeightsStatus
    pinned_version: str | None
    notes: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return self.runtime.usable and self.weights.usable


def _crash_hint(code: int) -> tuple[str, str]:
    if code == _STATUS_ILLEGAL_INSTRUCTION:
        return ("the native library stopped on an illegal CPU instruction",
                "The pinned CPU wheel was built with AVX2/FMA/F16C enabled; this processor "
                "probably lacks one of them. No reviewed alternative wheel exists. Leave the "
                "runtime uninstalled; BASIN keeps using its direct tools.")
    if code in (_STATUS_DLL_NOT_FOUND, _STATUS_ENTRYPOINT_NOT_FOUND):
        return ("a DLL the native library needs could not be loaded", VC_REDIST_HINT)
    if code == _STATUS_ACCESS_VIOLATION:
        return ("the native library crashed while loading (access violation)",
                "Run \"Setup BASIN.cmd\" --repair-ai. If it persists, leave the runtime "
                "uninstalled and record the Windows version and CPU model.")
    return (f"the import process exited with code {code:#x}",
            "Run \"Setup BASIN.cmd\" --repair-ai and keep this output for troubleshooting.")


def probe_runtime(python: str | None = None, pinned_version: str | None = None,
                  timeout: float = PROBE_TIMEOUT_SECONDS) -> RuntimeStatus:
    """Import llama_cpp in a separate, isolated interpreter and classify the outcome."""
    python = python or sys.executable
    try:
        # -I: ignore PYTHON* variables, user site-packages and the working directory, so
        # only the packages actually installed in this environment are imported.
        result = subprocess.run([python, "-I", "-c", _PROBE_CODE], capture_output=True,
                                text=True, timeout=timeout, cwd=str(ROOT))
    except subprocess.TimeoutExpired:
        return RuntimeStatus("timeout", detail=f"importing llama_cpp did not finish within {timeout:.0f} s",
                             hint="Run \"Setup BASIN.cmd\" --repair-ai, then check again.")
    except OSError as err:
        return RuntimeStatus("import_error", detail=f"could not start {python}: {err}")

    payload = None
    for line in reversed(result.stdout.strip().splitlines()):
        try:
            payload = json.loads(line)
            break
        except ValueError:
            continue

    if isinstance(payload, dict) and payload.get("ok"):
        version = payload.get("version")
        status = RuntimeStatus("ok", version=version, system_info=payload.get("system_info", ""))
        if pinned_version and version != pinned_version:
            status.state = "wrong_version"
            status.detail = f"installed {version}, but the reviewed pin is {pinned_version}"
            status.hint = "Run \"Setup BASIN.cmd\" --repair-ai to install the reviewed version."
        return status

    if result.returncode == 3 and isinstance(payload, dict):
        error_type = payload.get("error_type", "")
        error = payload.get("error", "")
        if error_type == "ModuleNotFoundError" and "llama_cpp" in error:
            return RuntimeStatus("absent", detail="llama-cpp-python is not installed in this environment",
                                 hint="Install it with: \"Setup BASIN.cmd\" --ai-runtime")
        hint = VC_REDIST_HINT if (error_type in ("OSError", "FileNotFoundError")
                                  or "DLL" in error or "Could not find module" in error) else (
            "Run \"Setup BASIN.cmd\" --repair-ai and keep this output for troubleshooting.")
        return RuntimeStatus("import_error", detail=f"{error_type}: {error}", hint=hint)

    detail, hint = _crash_hint(result.returncode & 0xFFFFFFFF)
    stderr_tail = result.stderr.strip()[-400:]
    return RuntimeStatus("crashed", detail=detail + (f" ({stderr_tail})" if stderr_tail else ""), hint=hint)


def _load_runtime_pins():
    """Load basin_core/qwen_runtime.py by path: its model pin is the single authority.

    Loading by path avoids importing the basin_core package (and its dependencies), and the
    module imports only the standard library at top level; it never imports llama_cpp here.
    """
    path = ROOT / "basin_core" / "qwen_runtime.py"
    spec = importlib.util.spec_from_file_location("_basin_qwen_runtime_pins", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def weights_status(verify_hash: bool = False, pins=None) -> WeightsStatus:
    """Report the pinned GGUF file without downloading or modifying anything."""
    try:
        pins = pins or _load_runtime_pins()
    except Exception as err:  # a damaged checkout must still produce a report
        return WeightsStatus("unreadable", detail=f"could not read the model pin: {err}")

    path = pins.resolve_model_path()
    if path is None:
        default = Path(pins.DEFAULT_MODEL_PATH)
        if default.is_file():
            return WeightsStatus("size_mismatch", str(default),
                                 f"{default.stat().st_size:,} bytes, expected {pins.MODEL_BYTES:,}")
        return WeightsStatus("absent", str(default), "no model weights found")
    try:
        size = Path(path).stat().st_size
    except OSError as err:
        return WeightsStatus("unreadable", str(path), str(err))
    if size != pins.MODEL_BYTES:
        return WeightsStatus("size_mismatch", str(path), f"{size:,} bytes, expected {pins.MODEL_BYTES:,}")
    if not verify_hash:
        return WeightsStatus("present_unverified", str(path),
                             "size matches the pin; SHA-256 not recomputed in this step "
                             "(the assistant verifies it before every model load)")
    try:
        pins.verify_model_file(Path(path))
    except ValueError as err:
        return WeightsStatus("hash_mismatch", str(path), str(err))
    except OSError as err:
        return WeightsStatus("unreadable", str(path), str(err))
    return WeightsStatus("verified", str(path), "size and SHA-256 match the application pin")


def collect_report(verify_hash: bool = False, python: str | None = None) -> Report:
    pinned = pinned_runtime_version()
    return Report(probe_runtime(python, pinned), weights_status(verify_hash), pinned)


def render_report(report: Report) -> str:
    runtime, weights = report.runtime, report.weights
    lines = ["", "BASIN optional embedded AI status", "-" * 34]

    if runtime.state == "ok":
        lines.append(f"Runtime:   INSTALLED - llama-cpp-python {runtime.version} imports successfully")
        if runtime.system_info:
            lines.append(f"           {runtime.system_info}")
    else:
        label = {"absent": "NOT INSTALLED", "wrong_version": "UNREVIEWED VERSION"}.get(runtime.state, "NOT USABLE")
        lines.append(f"Runtime:   {label} - {runtime.detail}")
        if runtime.hint:
            lines.append(f"           {runtime.hint}")

    if weights.state == "verified":
        lines.append(f"Weights:   VERIFIED - {weights.path}")
    elif weights.state == "present_unverified":
        lines.append(f"Weights:   PRESENT - {weights.path}")
        lines.append(f"           {weights.detail}")
    elif weights.state == "absent":
        lines.append("Weights:   NOT DOWNLOADED - this step never downloads them.")
        lines.append("           With internet: .venv\\Scripts\\python.exe scripts\\fetch_model.py (about 2.1 GB)")
    else:
        lines.append(f"Weights:   NOT USABLE - {weights.detail}")
        lines.append("           Re-download with: .venv\\Scripts\\python.exe scripts\\fetch_model.py --force")

    if report.ready:
        lines.append("Readiness: READY TO TRY - runtime and weights are both in place.")
        lines.append("           No live model test was run by this check. Start BASIN and open the AI")
        lines.append("           Assistant, or run scripts\\qwen_smoke_test.py, to confirm on this device.")
    else:
        missing = [name for name, ok in (("runtime", runtime.usable), ("weights", weights.usable)) if not ok]
        lines.append(f"Readiness: NOT READY - missing or unusable: {', '.join(missing)}.")
        lines.append("           The assistant uses BASIN's instant direct tools instead.")
    lines.append("BASIN core does not depend on any of the above and works offline either way.")
    lines.extend(report.notes)
    return "\n".join(lines)


# --------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------

def run_install(repair: bool, wheelhouse_override: Path | None) -> int:
    """Run pip for install/repair. Returns pip's exit code (0 on success)."""
    wheelhouse = select_wheelhouse(override=wheelhouse_override)
    if wheelhouse is not None:
        print(f"Installing from local wheelhouse (offline): {wheelhouse}")
    else:
        if wheelhouse_override is not None or (ROOT / "wheelhouse").is_dir():
            print("The wheelhouse folder has no llama-cpp-python wheel; using internet sources.")
        print("Installing from the internet: the upstream CPU wheel index named in requirements-native.txt.")
    for command in pip_commands(sys.executable, NATIVE_REQUIREMENTS, wheelhouse, repair):
        print("> " + " ".join(command[1:]), flush=True)
        try:
            code = subprocess.run(command, cwd=str(ROOT)).returncode
        except OSError as err:
            print(f"Could not run pip: {err}")
            return 1
        if code != 0:
            print(f"\npip exited with code {code}.")
            if wheelhouse is None:
                print("Check the internet connection, or place the pinned wheels in wheelhouse\\ and retry.")
            print("If pip reported THESE PACKAGES DO NOT MATCH THE HASHES, the file is not the reviewed "
                  "artifact. Do not bypass the hash check.")
            print("If pip reported that requirements must be pinned, the core install is incomplete: "
                  "run \"Setup BASIN.cmd\" first.")
            return code
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true", help="report runtime/weights/readiness; change nothing")
    action.add_argument("--repair", action="store_true", help="force-reinstall the pinned native runtime")
    parser.add_argument("--verify-weights", action="store_true", help="recompute the model SHA-256 (slow)")
    parser.add_argument("--wheelhouse", type=Path, help="install offline from this folder")
    parser.add_argument("--no-summary", action="store_true", help="print only the runtime result")
    args = parser.parse_args(argv)

    pinned = pinned_runtime_version()
    if args.check:
        report = collect_report(args.verify_weights)
        print(render_report(report))
        return 0 if report.ready else 1

    print(f"BASIN optional native AI runtime: {'repair' if args.repair else 'install'}")
    reason = unsupported_reason()
    if reason:
        print(f"Native AI runtime NOT installed: {reason}")
        print("BASIN core is unaffected; the assistant uses its direct tools.")
        return 2
    if pinned is None:
        print(f"Native AI runtime NOT installed: {NATIVE_REQUIREMENTS.name} is missing or has no exact "
              "llama-cpp-python pin. Re-extract the complete BASIN package.")
        return 2

    code = run_install(args.repair, args.wheelhouse)
    runtime = probe_runtime(sys.executable, pinned)
    if code != 0:
        print(f"\nNative AI runtime installation FAILED. Only the hash-locked native packages could "
              f"have been changed; BASIN core packages were not.")
    if args.no_summary:
        if runtime.usable:
            print(f"Runtime: llama-cpp-python {runtime.version} imports successfully.")
        else:
            print(f"Runtime: not usable - {runtime.detail}")
            if runtime.hint:
                print(f"         {runtime.hint}")
    else:
        print(render_report(Report(runtime, weights_status(args.verify_weights), pinned)))
    return 0 if (code == 0 and runtime.usable) else 1


if __name__ == "__main__":
    sys.exit(main())
