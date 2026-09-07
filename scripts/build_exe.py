"""Compile BASIN Native Windows Executable (BASIN.exe) with custom brand icon."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def output_name() -> str:
    """Use a staged name when Windows has the installed executable open."""
    target = ROOT / "BASIN.exe"
    if not target.exists():
        return "BASIN"
    try:
        with target.open("r+b"):
            pass
    except PermissionError:
        print("BASIN.exe is running; building BASIN-updated.exe beside it.")
        return "BASIN-updated"
    return "BASIN"


def build_exe():
    os.chdir(str(ROOT))
    icon_script = ROOT / "scripts" / "build_icon.py"
    subprocess.run([sys.executable, str(icon_script)], check=True)

    icon_path = ROOT / "assets" / "basin.ico"
    launcher_path = ROOT / "scripts" / "launcher.py"
    name = output_name()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onefile",
        "--noconsole",
        "--collect-all=webview",
        f"--icon={icon_path}",
        f"--name={name}",
        "--distpath=.",
        str(launcher_path)
    ]

    print("\nRunning PyInstaller build for BASIN.exe...")
    print("Command:", subprocess.list2cmdline(cmd))
    res = subprocess.run(cmd, check=True)

    # Clean up temporary build directory and spec file
    build_dir = ROOT / "build"
    spec_file = ROOT / f"{name}.spec"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    if spec_file.exists():
        spec_file.unlink(missing_ok=True)

    target_exe = ROOT / f"{name}.exe"
    if target_exe.exists():
        size_mb = target_exe.stat().st_size / (1024 * 1024)
        print(f"\n[SUCCESS] Compiled {target_exe} ({size_mb:.2f} MB) with custom icon!")
    else:
        raise SystemExit("\n[FAILURE] BASIN.exe was not created.")


if __name__ == "__main__":
    build_exe()
