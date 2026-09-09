"""Build standalone offline BASIN distribution directory and compressed installer payload."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
BUNDLE_DIR = DIST_DIR / "BASIN"
RUNTIME_DIR = BUNDLE_DIR / "runtime"
PAYLOAD_ZIP = DIST_DIR / "basin_payload.zip"


def log(msg: str):
    print(f"[OFFLINE-BUILD] {msg}", flush=True)


def copy_runtime():
    """Assemble the isolated CPython runtime without host virtualenv stubs."""
    base_python = Path(sys.base_prefix)
    log(f"Base Python location: {base_python}")

    if RUNTIME_DIR.exists():
        log(f"Cleaning existing runtime at {RUNTIME_DIR}...")
        shutil.rmtree(RUNTIME_DIR, ignore_errors=True)
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy core executables and DLLs from base python
    for item in ["python.exe", "pythonw.exe", "python3.dll"]:
        src = base_python / item
        if src.exists():
            shutil.copy2(src, RUNTIME_DIR / item)

    # Find versioned python DLL (e.g. python312.dll)
    for pydll in base_python.glob("python3*.dll"):
        shutil.copy2(pydll, RUNTIME_DIR / pydll.name)

    for vcdll in base_python.glob("vcruntime*.dll"):
        shutil.copy2(vcdll, RUNTIME_DIR / vcdll.name)

    # Copy msvcp140.dll if available
    sys32 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
    msvcp = sys32 / "msvcp140.dll"
    if msvcp.exists():
        shutil.copy2(msvcp, RUNTIME_DIR / "msvcp140.dll")
        log("Copied msvcp140.dll from System32 into runtime.")

    # 2. Copy DLLs folder
    src_dlls = base_python / "DLLs"
    if src_dlls.exists():
        log("Copying standard C extension DLLs...")
        shutil.copytree(src_dlls, RUNTIME_DIR / "DLLs", dirs_exist_ok=True)

    # 3. Copy standard library Lib/ (excluding test/idlelib to keep bundle compact)
    src_lib = base_python / "Lib"
    target_lib = RUNTIME_DIR / "Lib"
    log("Copying standard library Lib/ (excluding test suites)...")
    
    def ignore_patterns(path, names):
        ignored = set()
        for n in names:
            if n in ("test", "tests", "idlelib", "turtledemo", "__pycache__", "site-packages"):
                ignored.add(n)
        return ignored

    shutil.copytree(src_lib, target_lib, ignore=ignore_patterns, dirs_exist_ok=True)

    # 4. Copy site-packages from active .venv
    venv_site = ROOT / ".venv" / "Lib" / "site-packages"
    target_site = target_lib / "site-packages"
    target_site.mkdir(parents=True, exist_ok=True)

    log(f"Copying site-packages from {venv_site}...")
    def ignore_site(path, names):
        ignored = set()
        is_top_level = Path(path).resolve() == venv_site.resolve()
        for n in names:
            if is_top_level and (n.startswith(("pip", "setuptools", "wheel", "pyinstaller", "_virtualenv")) or n in ("_pytest", "pytest")):
                ignored.add(n)
            elif n == "__pycache__" or n.endswith((".pyc", ".pyo")):
                ignored.add(n)
        return ignored

    shutil.copytree(venv_site, target_site, ignore=ignore_site, dirs_exist_ok=True)
    log("Runtime assembly complete.")


def copy_application_files():
    """Copy application scripts, assets, data, and configs into BUNDLE_DIR."""
    log(f"Copying application files into {BUNDLE_DIR}...")
    
    # 1. Native launcher BASIN.exe
    launcher_exe = ROOT / "BASIN.exe"
    if not launcher_exe.exists():
        log("Compiling BASIN.exe first...")
        from scripts.build_exe import build_exe
        build_exe()
    shutil.copy2(launcher_exe, BUNDLE_DIR / "BASIN.exe")

    # 2. Root Python scripts
    for pyfile in ["app.py", "basin_theme.py", "basin_ui.py"]:
        shutil.copy2(ROOT / pyfile, BUNDLE_DIR / pyfile)

    # 3. Directories
    for d in ["basin_core", "assets", "data", ".streamlit"]:
        src = ROOT / d
        dst = BUNDLE_DIR / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    # 4. Readme and license
    for doc in ["README.md", "LICENSE"]:
        src = ROOT / doc
        if src.exists():
            shutil.copy2(src, BUNDLE_DIR / doc)

    # 5. Create uninstall.bat
    uninstall_bat = BUNDLE_DIR / "uninstall.bat"
    bat_content = """@echo off
setlocal
echo ===================================================
echo   Uninstalling BASIN Drought Workbench...
echo ===================================================

:: Remove shortcuts
set "DESKTOP_LNK=%USERPROFILE%\\Desktop\\BASIN Drought Workbench.lnk"
if exist "%DESKTOP_LNK%" del /f /q "%DESKTOP_LNK%"

set "START_LNK=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\BASIN Drought Workbench.lnk"
if exist "%START_LNK%" del /f /q "%START_LNK%"

:: Remove registry entry
reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\BASIN" /f >nul 2>&1

echo Shortcuts and registry entries removed.
echo To complete uninstallation, this folder will now be scheduled for deletion.

:: Self-deleting directory trick
cd /d "%TEMP%"
rmdir /s /q "%~dp0" >nul 2>&1
echo Done! BASIN has been uninstalled.
exit /b 0
"""
    uninstall_bat.write_text(bat_content, encoding="utf-8")
    log("Copied all application files and generated uninstaller.")


def verify_runtime_isolation():
    """Verify that runtime/python.exe executes isolated without host env vars."""
    log("Verifying runtime isolation...")
    python_exe = RUNTIME_DIR / "python.exe"
    if not python_exe.exists():
        raise FileNotFoundError(f"Runtime python missing: {python_exe}")

    clean_env = {
        "SystemRoot": os.environ.get("SystemRoot", "C:\\Windows"),
        "WINDIR": os.environ.get("WINDIR", "C:\\Windows"),
        "PATH": f"{RUNTIME_DIR};{RUNTIME_DIR}\\DLLs;{os.environ.get('SystemRoot', 'C:\\Windows')}\\System32",
        "TEMP": os.environ.get("TEMP", "C:\\Windows\\Temp"),
        "TMP": os.environ.get("TMP", "C:\\Windows\\Temp"),
    }

    test_cmd = [
        str(python_exe),
        "-c",
        "import sys, streamlit, pandas, numpy, scipy, sklearn; "
        "print('ISOLATION_PREFIX:', sys.prefix); "
        "print('CORE_MODULES_LOADED: SUCCESS')"
    ]
    
    res = subprocess.run(test_cmd, env=clean_env, cwd=str(BUNDLE_DIR), capture_output=True, text=True)
    if res.returncode != 0:
        log(f"Runtime isolation verification FAILED!\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
        raise RuntimeError("Runtime isolation verification failed")
    
    log(f"Runtime verification succeeded:\n{res.stdout.strip()}")


def create_payload_archive():
    """Compress BUNDLE_DIR into dist/basin_payload.zip."""
    log(f"Creating compressed installer payload at {PAYLOAD_ZIP}...")
    if PAYLOAD_ZIP.exists():
        PAYLOAD_ZIP.unlink()

    file_count = 0
    with zipfile.ZipFile(PAYLOAD_ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for root, dirs, files in os.walk(BUNDLE_DIR):
            for file in files:
                file_path = Path(root) / file
                archive_name = file_path.relative_to(BUNDLE_DIR)
                zf.write(file_path, archive_name)
                file_count += 1

    size_mb = PAYLOAD_ZIP.stat().st_size / (1024 * 1024)
    log(f"Payload archive created: {file_count} files, {size_mb:.2f} MB.")


def build_bundle():
    log("=== Starting BASIN Standalone Offline Bundle Build ===")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    copy_runtime()
    copy_application_files()
    verify_runtime_isolation()
    create_payload_archive()
    log("=== Offline Bundle Build Complete ===")


if __name__ == "__main__":
    build_bundle()
