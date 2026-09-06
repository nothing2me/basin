"""Compile BASIN Native Windows Executable (BASIN.exe) with custom brand icon."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def build_exe():
    os.chdir(str(ROOT))
    icon_script = ROOT / "scripts" / "build_icon.py"
    subprocess.run([sys.executable, str(icon_script)], check=True)

    icon_path = ROOT / "assets" / "basin.ico"
    launcher_path = ROOT / "scripts" / "launcher.py"

    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--paths=.venv/Lib/site-packages",
        "--collect-all=webview",
        f"--icon={icon_path}",
        "--name=BASIN",
        "--distpath=.",
        str(launcher_path)
    ]

    print("\nRunning PyInstaller build for BASIN.exe...")
    print("Command:", " ".join(cmd))
    res = subprocess.run(cmd, check=True)

    # Clean up temporary build directory and spec file
    build_dir = ROOT / "build"
    spec_file = ROOT / "BASIN.spec"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    if spec_file.exists():
        spec_file.unlink(missing_ok=True)

    target_exe = ROOT / "BASIN.exe"
    if target_exe.exists():
        size_mb = target_exe.stat().st_size / (1024 * 1024)
        print(f"\n[SUCCESS] Compiled {target_exe} ({size_mb:.2f} MB) with custom icon!")
    else:
        raise SystemExit("\n[FAILURE] BASIN.exe was not created.")


if __name__ == "__main__":
    build_exe()
