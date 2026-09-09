"""Compile standalone Setup-BASIN.exe with embedded offline payload."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST_DIR = ROOT / "dist"
PAYLOAD_ZIP = DIST_DIR / "basin_payload.zip"
ICON_PATH = ROOT / "assets" / "basin.ico"
WIZARD_SCRIPT = ROOT / "scripts" / "installer_wizard.py"


def package_setup_exe():
    print("=== Building BASIN Standalone Offline Setup Executable ===", flush=True)

    # 1. Build offline bundle and payload archive if needed
    if not PAYLOAD_ZIP.exists():
        print("Payload archive missing. Running build_offline_bundle.py...", flush=True)
        from scripts.build_offline_bundle import build_bundle
        build_bundle()

    if not PAYLOAD_ZIP.exists():
        raise FileNotFoundError(f"Failed to produce {PAYLOAD_ZIP}")

    # 2. Compile Setup-BASIN.exe via PyInstaller
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        f"--icon={ICON_PATH}",
        f"--add-data={PAYLOAD_ZIP};.",
        "--name=Setup-BASIN",
        "--distpath=.",
        str(WIZARD_SCRIPT),
    ]

    print("Running PyInstaller for Setup-BASIN.exe...", flush=True)
    print("Command:", subprocess.list2cmdline(cmd), flush=True)
    subprocess.run(cmd, check=True)

    # Clean up build artifacts
    build_dir = ROOT / "build"
    spec_file = ROOT / "Setup-BASIN.spec"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    if spec_file.exists():
        spec_file.unlink(missing_ok=True)

    target_exe = ROOT / "Setup-BASIN.exe"
    if target_exe.exists():
        size_mb = target_exe.stat().st_size / (1024 * 1024)
        print(f"\n[SUCCESS] Compiled standalone installer: {target_exe} ({size_mb:.2f} MB)", flush=True)
    else:
        raise FileNotFoundError(f"Setup-BASIN.exe was not produced at {target_exe}")


if __name__ == "__main__":
    package_setup_exe()
