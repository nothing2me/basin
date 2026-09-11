"""Optional native Qwen runtime: pinned requirements, installer, setup script and package.

Nothing here downloads model weights or reaches the network. Real pip runs only offline,
against local fixture wheelhouses with proxies pointed at a closed port. The setup script
runs as shipped against a stub pip and a stub model fetcher, apart from the one line that
creates the virtual environment. None of this is a clean-laptop installation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_install_consistency as consistency  # noqa: E402
import install_native_runtime as native  # noqa: E402
import package_demo  # noqa: E402

WINDOWS_ONLY = pytest.mark.skipif(sys.platform != "win32", reason="Windows setup path")
PIN = native.pinned_runtime_version()
NATIVE_FILE = ROOT / "requirements-native.txt"


# --------------------------------------------------------------------------------------
# The pinned requirements file
# --------------------------------------------------------------------------------------

def test_native_requirements_are_exact_hash_locked_binary_only_and_additive():
    assert consistency.native_problems(ROOT) == []
    resolved = consistency.resolve_requirements(NATIVE_FILE)
    assert resolved == {"llama-cpp-python": f"llama-cpp-python=={PIN}", "diskcache": "diskcache==5.6.3"}
    assert PIN == "0.3.35"


def test_core_requirements_never_pull_in_the_native_runtime():
    """The no-AI install path must stay free of the native runtime and its extra dependency."""
    core = consistency.resolve_requirements(ROOT / "requirements.txt")
    assert "llama-cpp-python" not in core and "diskcache" not in core
    # llama-cpp-python's remaining dependencies are satisfied by existing core pins.
    for dependency in ("numpy", "jinja2", "markupsafe", "typing-extensions"):
        assert core[dependency].startswith(f"{dependency}==")


def _native_tree(tmp_path: Path, text: str) -> Path:
    (tmp_path / "requirements.txt").write_text("numpy==2.5.2\n", encoding="utf-8")
    (tmp_path / "requirements-native.txt").write_text(text, encoding="utf-8")
    return tmp_path


LLAMA_LINE = next(line for line in NATIVE_FILE.read_text(encoding="utf-8").splitlines()
                  if line.startswith("llama-cpp-python=="))


@pytest.mark.parametrize("mutate, expected", [
    (lambda t: t.replace(LLAMA_LINE, LLAMA_LINE.split(" --hash")[0]), "no --hash=sha256"),
    (lambda t: t.replace("llama-cpp-python==", "llama-cpp-python>="), "not pinned"),
    (lambda t: t.replace("--only-binary :all:\n", ""), "--only-binary :all: missing"),
    (lambda t: t.replace("--require-hashes\n", ""), "--require-hashes missing"),
    (lambda t: t.replace("https://abetlen.github.io/llama-cpp-python/whl/cpu",
                         "https://example.invalid/simple"), "unreviewed package source"),
    (lambda t: t + "numpy==2.5.2 --hash=sha256:" + "0" * 64 + "\n", "also pinned by requirements.txt"),
    (lambda t: "-r requirements.txt\n" + t, "option not allowed"),
    (lambda t: t.replace(LLAMA_LINE, ""), "llama-cpp-python: absent"),
])
def test_native_checker_rejects_weakened_pins(tmp_path, mutate, expected):
    original = NATIVE_FILE.read_text(encoding="utf-8")
    assert consistency.native_problems(_native_tree(tmp_path, original)) == []  # control
    problems = consistency.native_problems(_native_tree(tmp_path, mutate(original)))
    assert any(expected in problem for problem in problems), problems


def test_resolver_strips_hash_options_and_joins_continuations(tmp_path):
    (tmp_path / "r.txt").write_text(
        "--require-hashes\nalpha==1.0 \\\n    --hash=sha256:" + "a" * 64 + "\n"
        "beta==2.0 --hash=sha256:" + "b" * 64 + "  # trailing comment\n", encoding="utf-8")
    assert consistency.resolve_requirements(tmp_path / "r.txt") == {"alpha": "alpha==1.0", "beta": "beta==2.0"}


def test_runtime_does_not_enable_the_llama_cpp_disk_cache():
    """Advisory guard: diskcache 5.6.3 (GHSA-w8v5-vhqr-4h9v) unpickles cache files.

    llama-cpp-python only creates a diskcache.Cache through LlamaDiskCache/set_cache. The
    accepted-risk rationale in docs/native_runtime_handoff.md depends on BASIN never doing so;
    revisit that note before this assertion is changed.
    """
    source = (ROOT / "basin_core" / "qwen_runtime.py").read_text(encoding="utf-8")
    assert "set_cache" not in source and "LlamaDiskCache" not in source and "diskcache" not in source


def test_runtime_and_downloader_share_one_model_pin():
    """Installing the runtime must not weaken or fork the model hash the worker enforces."""
    import fetch_model

    pins = native._load_runtime_pins()
    assert pins.MODEL_SHA256 == fetch_model.MODEL_SHA256
    assert pins.MODEL_BYTES == fetch_model.MODEL_BYTES


# --------------------------------------------------------------------------------------
# Real pip, offline, against controlled wheelhouses
# --------------------------------------------------------------------------------------

def _fake_wheel(folder: Path, distribution: str, version: str, tag: str) -> Path:
    stem = distribution.replace("-", "_")
    path = folder / f"{stem}-{version}-{tag}.whl"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(f"{stem}-{version}.dist-info/METADATA",
                         f"Metadata-Version: 2.1\nName: {distribution}\nVersion: {version}\n")
        archive.writestr(f"{stem}-{version}.dist-info/WHEEL",
                         f"Wheel-Version: 1.0\nGenerator: basin-test\nRoot-Is-Purelib: false\nTag: {tag}\n")
        archive.writestr(f"{stem}-{version}.dist-info/RECORD", "")
    return path


def _offline_pip(wheelhouse: Path) -> subprocess.CompletedProcess:
    command = native.pip_commands(sys.executable, NATIVE_FILE, wheelhouse, repair=False)[0] + ["--dry-run"]
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PIP_")}
    # Any attempt to reach an index fails immediately instead of silently succeeding.
    env.update(HTTP_PROXY="http://127.0.0.1:9", HTTPS_PROXY="http://127.0.0.1:9", NO_PROXY="",
               PIP_RETRIES="0", PIP_TIMEOUT="3")
    return subprocess.run(command, capture_output=True, text=True, env=env, timeout=180)


@WINDOWS_ONLY
def test_substituted_runtime_wheel_is_rejected_by_hash(tmp_path):
    _fake_wheel(tmp_path, "llama-cpp-python", PIN, "py3-none-win_amd64")
    _fake_wheel(tmp_path, "diskcache", "5.6.3", "py3-none-any")
    result = _offline_pip(tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "DO NOT MATCH THE HASHES" in output, output[-3000:]
    assert "Looking in indexes" not in output, "offline install must not consult any index"


@WINDOWS_ONLY
def test_source_only_runtime_is_refused_instead_of_built(tmp_path):
    (tmp_path / f"llama_cpp_python-{PIN}.tar.gz").write_bytes(b"not a real sdist")
    result = _offline_pip(tmp_path)
    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert "from versions: none" in output or "No matching distribution" in output, output[-3000:]
    assert "Building wheel" not in output and "setup.py" not in output


@WINDOWS_ONLY
@pytest.mark.skipif(not os.environ.get("BASIN_NATIVE_WHEELHOUSE"),
                    reason="set BASIN_NATIVE_WHEELHOUSE to a folder holding the genuine pinned wheels")
def test_genuine_pinned_wheels_resolve_offline():
    """Positive control for the two rejections above, using the real upstream artifacts."""
    result = _offline_pip(Path(os.environ["BASIN_NATIVE_WHEELHOUSE"]))
    output = result.stdout + result.stderr
    assert result.returncode == 0, output[-3000:]
    assert f"llama_cpp_python-{PIN}" in output or "llama-cpp-python" in output


# --------------------------------------------------------------------------------------
# Installer logic, in process
# --------------------------------------------------------------------------------------

def test_supported_target_is_windows_x64_cpython_312_venv():
    ok = dict(sys_platform="win32", machine="AMD64", pointer_bits=64, version=(3, 12),
              implementation="CPython", in_venv=True)
    assert native.unsupported_reason(**ok) is None
    for change, words in [({"sys_platform": "linux"}, "Windows x64 only"),
                          ({"pointer_bits": 32}, "64-bit"),
                          ({"machine": "ARM64"}, "64-bit x64"),
                          ({"version": (3, 11)}, "CPython 3.12"),
                          ({"version": (3, 13)}, "CPython 3.12"),
                          ({"implementation": "PyPy"}, "CPython 3.12"),
                          ({"in_venv": False}, "virtual environment")]:
        reason = native.unsupported_reason(**{**ok, **change})
        assert reason and words in reason, (change, reason)


def test_pip_commands_are_hash_locked_and_never_touch_core_requirements(tmp_path):
    online = native.pip_commands("py", NATIVE_FILE, None, repair=False)
    offline = native.pip_commands("py", NATIVE_FILE, tmp_path, repair=False)
    repair = native.pip_commands("py", NATIVE_FILE, None, repair=True)
    assert len(online) == len(offline) == 1 and len(repair) == 2
    for command in online + offline + repair:
        assert command[:4] == ["py", "-m", "pip", "install"]
        assert "--require-hashes" in command
        assert command[command.index("--only-binary") + 1] == ":all:"
        assert command[-2:] == ["-r", str(NATIVE_FILE)]
        assert not any("requirements.txt" in part for part in command)
        assert "--trusted-host" not in command and "--no-binary" not in command
    assert "--no-index" not in online[0]
    assert offline[0][offline[0].index("--find-links") + 1] == str(tmp_path) and "--no-index" in offline[0]
    assert {"--force-reinstall", "--no-deps"} <= set(repair[0]) and "--force-reinstall" not in repair[1]


def test_wheelhouse_is_used_only_when_it_holds_the_runtime_wheel(tmp_path):
    assert native.select_wheelhouse(tmp_path) is None
    (tmp_path / "wheelhouse").mkdir()
    _fake_wheel(tmp_path / "wheelhouse", "numpy", "2.5.2", "cp312-cp312-win_amd64")
    assert native.select_wheelhouse(tmp_path) is None
    _fake_wheel(tmp_path / "wheelhouse", "llama-cpp-python", PIN, "py3-none-win_amd64")
    assert native.select_wheelhouse(tmp_path) == tmp_path / "wheelhouse"


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(["python"], returncode, stdout, stderr)


@pytest.mark.parametrize("result, state, hint_words", [
    (_completed(0, json.dumps({"ok": True, "version": "0.3.35", "system_info": "CPU : AVX2 = 1"})), "ok", ""),
    (_completed(0, json.dumps({"ok": True, "version": "0.3.30"})), "wrong_version", "--repair-ai"),
    (_completed(3, json.dumps({"ok": False, "error_type": "ModuleNotFoundError",
                               "error": "No module named 'llama_cpp'"})), "absent", "--ai-runtime"),
    (_completed(3, json.dumps({"ok": False, "error_type": "OSError",
                               "error": "Could not find module 'llama.dll' (or one of its dependencies)"})),
     "import_error", "Visual C++ 2015-2022 Redistributable"),
    (_completed(0xC000001D), "crashed", "AVX2"),
    (_completed(0xC0000135), "crashed", "Visual C++ 2015-2022 Redistributable"),
    (_completed(-11, stderr="Segmentation fault"), "crashed", "--repair-ai"),
])
def test_runtime_probe_classifies_each_failure(monkeypatch, result, state, hint_words):
    monkeypatch.setattr(native.subprocess, "run", lambda *a, **k: result)
    status = native.probe_runtime("python", "0.3.35")
    assert status.state == state
    assert hint_words in status.hint
    assert status.usable is (state == "ok")


def test_runtime_probe_timeout(monkeypatch):
    def hang(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs.get("timeout"))
    monkeypatch.setattr(native.subprocess, "run", hang)
    assert native.probe_runtime("python", "0.3.35", timeout=1).state == "timeout"


@pytest.mark.skipif(__import__("importlib.util").util.find_spec("llama_cpp") is not None,
                    reason="this environment has the native runtime installed")
def test_runtime_probe_really_reports_absence():
    """A real isolated interpreter, not a mock: this test environment has no runtime."""
    status = native.probe_runtime(sys.executable, PIN)
    assert status.state == "absent", status


@pytest.fixture
def small_pins(tmp_path, monkeypatch):
    """The real runtime pin module, pointed at a small file so the real verifier runs."""
    pins = native._load_runtime_pins()
    model = tmp_path / "model.gguf"
    model.write_bytes(b"GGUF" + b"\0" * 60)
    import hashlib
    monkeypatch.setattr(pins, "MODEL_BYTES", model.stat().st_size)
    monkeypatch.setattr(pins, "MODEL_SHA256", hashlib.sha256(model.read_bytes()).hexdigest())
    monkeypatch.setattr(pins, "DEFAULT_MODEL_PATH", tmp_path / "absent.gguf")
    monkeypatch.setattr(pins, "resolve_model_path", lambda: model)
    return pins, model


def test_weights_states_use_the_application_pin(small_pins, monkeypatch, tmp_path):
    pins, model = small_pins
    assert native.weights_status(pins=pins).state == "present_unverified"
    assert native.weights_status(verify_hash=True, pins=pins).state == "verified"

    model.write_bytes(b"GGUF" + b"\1" * 60)  # same size, different bytes
    assert native.weights_status(pins=pins).state == "present_unverified"
    assert native.weights_status(verify_hash=True, pins=pins).state == "hash_mismatch"

    model.write_bytes(b"short")
    assert native.weights_status(pins=pins).state == "size_mismatch"

    monkeypatch.setattr(pins, "resolve_model_path", lambda: None)
    assert native.weights_status(pins=pins).state == "absent"
    (tmp_path / "absent.gguf").write_bytes(b"partial download")
    assert native.weights_status(pins=pins).state == "size_mismatch"


def test_report_keeps_runtime_weights_and_readiness_distinct():
    ok = native.RuntimeStatus("ok", version="0.3.35")
    absent = native.RuntimeStatus("absent", detail="llama-cpp-python is not installed", hint="--ai-runtime")
    present = native.WeightsStatus("present_unverified", "m.gguf", "size matches")
    missing = native.WeightsStatus("absent", "m.gguf")

    weights_only = native.render_report(native.Report(absent, present, "0.3.35"))
    assert "Runtime:   NOT INSTALLED" in weights_only and "Weights:   PRESENT" in weights_only
    assert "Readiness: NOT READY - missing or unusable: runtime." in weights_only

    runtime_only = native.render_report(native.Report(ok, missing, "0.3.35"))
    assert "Runtime:   INSTALLED" in runtime_only and "never downloads" in runtime_only
    assert "Readiness: NOT READY - missing or unusable: weights." in runtime_only

    both = native.Report(ok, present, "0.3.35")
    assert both.ready
    text = native.render_report(both)
    assert "READY TO TRY" in text and "No live model test was run" in text
    for report in (weights_only, runtime_only, text):
        assert "BASIN core does not depend" in report


def _fake_subprocess(monkeypatch, pip_code=0, probe=None):
    calls = []
    probe = probe or _completed(3, json.dumps({"ok": False, "error_type": "ModuleNotFoundError",
                                               "error": "No module named 'llama_cpp'"}))

    def run(command, *args, **kwargs):
        calls.append(list(command))
        if "-I" in command:
            return probe
        return _completed(pip_code)
    monkeypatch.setattr(native.subprocess, "run", run)
    return calls


@pytest.fixture
def no_network(monkeypatch):
    import socket
    import urllib.request

    def refuse(*args, **kwargs):
        raise AssertionError("network access attempted")
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def test_check_changes_nothing_and_downloads_nothing(monkeypatch, capsys, no_network):
    calls = _fake_subprocess(monkeypatch)
    assert native.main(["--check"]) == 1
    assert calls and all("-I" in call for call in calls), "check must only probe"
    assert "Runtime:   NOT INSTALLED" in capsys.readouterr().out


def test_unsupported_interpreter_installs_nothing(monkeypatch, capsys, no_network):
    calls = _fake_subprocess(monkeypatch)
    monkeypatch.setattr(native, "unsupported_reason", lambda: "a 64-bit x64 Python is required")
    assert native.main([]) == 2
    assert calls == []
    out = capsys.readouterr().out
    assert "NOT installed" in out and "BASIN core is unaffected" in out


def test_failed_pip_is_reported_as_failure(monkeypatch, capsys, no_network):
    monkeypatch.setattr(native, "unsupported_reason", lambda: None)
    calls = _fake_subprocess(monkeypatch, pip_code=1)
    assert native.main([]) == 1
    out = capsys.readouterr().out
    assert "installation FAILED" in out and "core packages were not" in out
    assert "Runtime:   NOT INSTALLED" in out
    assert sum("pip" in call for call in calls) == 1


def test_pip_success_alone_is_not_success(monkeypatch, capsys, no_network):
    monkeypatch.setattr(native, "unsupported_reason", lambda: None)
    _fake_subprocess(monkeypatch, pip_code=0, probe=_completed(
        3, json.dumps({"ok": False, "error_type": "OSError", "error": "DLL load failed"})))
    assert native.main(["--no-summary"]) == 1
    assert "Visual C++" in capsys.readouterr().out


def test_successful_install_requires_the_reviewed_version_to_import(monkeypatch, capsys, no_network):
    monkeypatch.setattr(native, "unsupported_reason", lambda: None)
    _fake_subprocess(monkeypatch, probe=_completed(0, json.dumps({"ok": True, "version": PIN})))
    assert native.main(["--no-summary"]) == 0
    assert f"llama-cpp-python {PIN} imports successfully" in capsys.readouterr().out


# --------------------------------------------------------------------------------------
# Setup BASIN.cmd, run by cmd.exe against a stub pip and stub model fetcher
# --------------------------------------------------------------------------------------

STUB_PIP = textwrap.dedent('''
    import json, os, sys, sysconfig
    from pathlib import Path
    args = sys.argv[1:]
    with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"pip": args}) + "\\n")
    native = any(a.endswith("requirements-native.txt") for a in args)
    code = int(os.environ.get("STUB_NATIVE_PIP_EXIT" if native else "STUB_CORE_PIP_EXIT", "0"))
    if native and code == 0:
        bodies = {
            "ok": "__version__ = %r\\ndef llama_print_system_info():\\n    return b'CPU : STUB'\\n"
                  % os.environ["STUB_RUNTIME_VERSION"],
            "dll": "raise OSError(\\"Could not find module 'llama.dll' (or one of its dependencies)\\")\\n",
            # STATUS_ILLEGAL_INSTRUCTION as a signed exit code, as a real AVX2 fault reports.
            "illegal": "import os\\nos._exit(0xC000001D - (1 << 32))\\n",
        }
        package = Path(sysconfig.get_paths()["purelib"]) / "llama_cpp"
        package.mkdir(parents=True, exist_ok=True)
        (package / "__init__.py").write_text(bodies[os.environ.get("STUB_RUNTIME", "ok")])
    sys.exit(code)
''')

STUB_FETCH = textwrap.dedent('''
    import json, os, sys
    with open(os.environ["STUB_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps({"fetch_model": sys.argv[1:]}) + "\\n")
    sys.exit(int(os.environ.get("STUB_FETCH_EXIT", "0")))
''')

VENV_LINE = "py -3.12 -m venv .venv"


@pytest.fixture
def setup_tree(tmp_path):
    tree = tmp_path / "BASIN copy"
    (tree / "scripts").mkdir(parents=True)
    (tree / "basin_core").mkdir()
    (tree / "home").mkdir()
    text = (ROOT / "Setup BASIN.cmd").read_text(encoding="utf-8")
    assert text.count(VENV_LINE) == 1
    base_python = getattr(sys, "_base_executable", sys.executable)
    text = text.replace(VENV_LINE, f'"{base_python}" -m venv --without-pip .venv')
    (tree / "Setup BASIN.cmd").write_bytes(text.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    for name in ("requirements.txt", "requirements-assistant.txt", "requirements-native.txt"):
        (tree / name).write_bytes((ROOT / name).read_bytes())
    (tree / "scripts" / "install_native_runtime.py").write_bytes((ROOT / "scripts/install_native_runtime.py").read_bytes())
    (tree / "basin_core" / "qwen_runtime.py").write_bytes((ROOT / "basin_core/qwen_runtime.py").read_bytes())
    (tree / "scripts" / "fetch_model.py").write_text(STUB_FETCH, encoding="utf-8")
    (tree / "pip").mkdir()
    (tree / "pip" / "__init__.py").write_text("", encoding="utf-8")
    (tree / "pip" / "__main__.py").write_text(STUB_PIP, encoding="utf-8")
    return tree


def run_setup(tree: Path, *args: str, stdin_text: str | None = None, **stub_env: str):
    log = tree / "calls.jsonl"
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("PIP_", "PYTHON"))}
    env.update(STUB_LOG=str(log), STUB_RUNTIME_VERSION=PIN, USERPROFILE=str(tree / "home"),
               HOME=str(tree / "home"), **stub_env)
    command = ["cmd.exe", "/d", "/c", str(tree / "Setup BASIN.cmd"), *args]
    if stdin_text is None:
        result = subprocess.run(command, cwd=tree, env=env, capture_output=True, text=True,
                                stdin=subprocess.DEVNULL, timeout=300)
    else:
        answers = tree / "answers.txt"
        answers.write_bytes(stdin_text.replace("\n", "\r\n").encode("ascii"))
        with answers.open("rb") as stdin:
            result = subprocess.run(command, cwd=tree, env=env, capture_output=True, text=True,
                                    stdin=stdin, timeout=300)
    calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
    pip_calls = [call["pip"] for call in calls if "pip" in call]
    return SimpleNamespace(
        code=result.returncode, out=result.stdout + result.stderr,
        core=[c for c in pip_calls if not any(a.endswith("requirements-native.txt") for a in c)],
        native=[c for c in pip_calls if any(a.endswith("requirements-native.txt") for a in c)],
        fetches=[call for call in calls if "fetch_model" in call],
        runtime_dir=tree / ".venv" / "Lib" / "site-packages" / "llama_cpp")


def _assert_core_completed(run):
    assert run.code == 0, run.out
    assert len(run.core) == 1 and run.core[0][-2:] == ["-r", "requirements.txt"]
    assert "Core BASIN installation complete" in run.out and "Setup complete" in run.out


@WINDOWS_ONLY
@pytest.mark.parametrize("args, stdin_text", [(("--no-ai",), None), ((), None), ((), "n\nn\n")])
def test_setup_without_ai_installs_core_only(setup_tree, args, stdin_text):
    run = run_setup(setup_tree, *args, stdin_text=stdin_text)
    _assert_core_completed(run)
    assert run.native == [] and run.fetches == []
    assert not run.runtime_dir.exists()
    assert "Optional AI skipped" in run.out
    assert "BASIN optional embedded AI status" not in run.out


@WINDOWS_ONLY
def test_setup_ai_runtime_installs_runtime_but_never_weights(setup_tree):
    run = run_setup(setup_tree, "--ai-runtime")
    _assert_core_completed(run)
    assert len(run.native) == 1 and "--require-hashes" in run.native[0]
    assert run.fetches == []
    assert "Native AI runtime installed and importable." in run.out
    assert f"Runtime:   INSTALLED - llama-cpp-python {PIN}" in run.out
    assert "Weights:   NOT DOWNLOADED" in run.out
    assert "Readiness: NOT READY - missing or unusable: weights." in run.out


@WINDOWS_ONLY
def test_setup_interactive_answers_are_separate(setup_tree):
    run = run_setup(setup_tree, stdin_text="y\nn\n")
    _assert_core_completed(run)
    assert len(run.native) == 1 and run.fetches == []


@WINDOWS_ONLY
@pytest.mark.parametrize("stub_env, message", [
    ({"STUB_NATIVE_PIP_EXIT": "1"}, "pip exited with code 1"),
    ({"STUB_RUNTIME": "dll"}, "Visual C++ 2015-2022 Redistributable"),
    ({"STUB_RUNTIME": "illegal"}, "illegal CPU instruction"),
])
def test_setup_runtime_failure_is_honest_and_keeps_core(setup_tree, stub_env, message):
    run = run_setup(setup_tree, "--ai-runtime", **stub_env)
    _assert_core_completed(run)
    assert message in run.out
    assert "Native AI runtime is NOT installed or NOT usable. BASIN core is unaffected." in run.out
    assert "Native AI runtime installed and importable." not in run.out
    assert "Readiness: NOT READY" in run.out and run.fetches == []


@WINDOWS_ONLY
def test_setup_with_ai_reports_weights_failure_separately(setup_tree):
    run = run_setup(setup_tree, "--with-ai", STUB_FETCH_EXIT="1")
    _assert_core_completed(run)
    assert len(run.native) == 1 and len(run.fetches) == 1
    assert "Native AI runtime installed and importable." in run.out
    assert "Model weights were NOT downloaded or did NOT verify." in run.out
    assert "Readiness: NOT READY - missing or unusable: weights." in run.out


@WINDOWS_ONLY
def test_setup_repair_force_reinstalls_only_the_native_packages(setup_tree):
    run = run_setup(setup_tree, "--repair-ai")
    _assert_core_completed(run)
    assert len(run.native) == 2 and run.fetches == []
    assert {"--force-reinstall", "--no-deps"} <= set(run.native[0])


@WINDOWS_ONLY
def test_setup_uses_the_wheelhouse_for_the_runtime_when_present(setup_tree):
    (setup_tree / "wheelhouse").mkdir()
    _fake_wheel(setup_tree / "wheelhouse", "llama-cpp-python", PIN, "py3-none-win_amd64")
    run = run_setup(setup_tree, "--ai-runtime")
    assert run.code == 0, run.out
    assert "--no-index" in run.core[0]
    assert "--no-index" in run.native[0] and "wheelhouse" in run.native[0][run.native[0].index("--find-links") + 1]


@WINDOWS_ONLY
def test_setup_core_failure_stops_before_any_ai_step(setup_tree):
    run = run_setup(setup_tree, "--with-ai", STUB_CORE_PIP_EXIT="1")
    assert run.code == 1
    assert "Installation failed" in run.out
    assert run.native == [] and run.fetches == []


@WINDOWS_ONLY
def test_setup_rejects_unknown_option_before_changing_anything(setup_tree):
    run = run_setup(setup_tree, "--with-a1")
    assert run.code == 2 and "Unknown option" in run.out
    assert not (setup_tree / ".venv").exists()
    assert run.core == [] and run.native == [] and run.fetches == []


# --------------------------------------------------------------------------------------
# Packaging and the core without the runtime
# --------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def source_package(tmp_path_factory):
    target = tmp_path_factory.mktemp("native-package") / "BASIN-demo-source.zip"
    package_demo.build_package(ROOT, target=target)
    return target


def test_source_package_ships_the_optional_install_path(source_package, tmp_path):
    with zipfile.ZipFile(source_package) as archive:
        names = set(archive.namelist())
        for required in ("BASIN/requirements-native.txt", "BASIN/scripts/install_native_runtime.py",
                         "BASIN/Setup BASIN.cmd", "BASIN/basin_core/qwen_runtime.py",
                         "BASIN/scripts/fetch_model.py"):
            assert required in names, required
        setup = archive.read("BASIN/Setup BASIN.cmd")
        for name in ("requirements.txt", "requirements-assistant.txt", "requirements-native.txt"):
            (tmp_path / name).write_bytes(archive.read(f"BASIN/{name}"))
    assert b"install_native_runtime.py" in setup
    assert b"\n" not in setup.replace(b"\r\n", b""), "Setup BASIN.cmd must ship with CRLF line endings"
    assert consistency.native_problems(tmp_path) == []  # hash lines survive packaging
    assert not any(name.endswith(".gguf") for name in names), "weights must never be packaged"


def test_core_and_model_metadata_work_when_the_native_runtime_cannot_load(tmp_path):
    """Simulate a runtime whose DLLs fail to load, as on a laptop missing VC++ runtimes."""
    (tmp_path / "sitecustomize.py").write_text(textwrap.dedent('''
        import sys

        class _BrokenNativeRuntime:
            def find_spec(self, name, path=None, target=None):
                if name == "llama_cpp" or name.startswith("llama_cpp."):
                    raise OSError("Could not find module 'llama.dll' (or one of its dependencies)")
                return None

        sys.meta_path.insert(0, _BrokenNativeRuntime())
    '''), encoding="utf-8")
    program = textwrap.dedent('''
        import sys
        from basin_core.data import CachedSource
        from basin_core.engine import ScenarioParams
        from basin_core.workspace import Workspace
        from basin_core.qwen_runtime import get_model_info
        source = CachedSource()
        workspace = Workspace(source, ScenarioParams(tuple(source.daily.columns), candidates=10), size=2)
        assert workspace.scenarios
        info = get_model_info()
        assert info["installed"] is False, info
        assert "llama_cpp" not in sys.modules
        print("core-ok")
    ''')
    env = {**os.environ, "PYTHONPATH": f"{tmp_path}{os.pathsep}{ROOT}"}
    result = subprocess.run([sys.executable, "-c", program], capture_output=True, text=True,
                            cwd=str(ROOT), env=env, timeout=300)
    assert "core-ok" in result.stdout, result.stderr[-2000:]
