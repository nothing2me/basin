"""BASIN Standalone Offline Setup Wizard.

A native, zero-dependency Windows setup wizard using standard Python tkinter.
Can run as a GUI wizard or headless with --silent / /S.
Includes an optional checkbox to download and configure the local Qwen 2.5 AI model
weights (~2.1 GB from Hugging Face) without bloating the initial setup executable.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import winreg
import zipfile
from pathlib import Path

# In PyInstaller --noconsole mode on Windows, sys.stdout and sys.stderr can be None.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "BASIN"

# Pinned Qwen 2.5 3B Instruct GGUF model metadata
MODEL_REPO = "Qwen/Qwen2.5-3B-Instruct-GGUF"
MODEL_REVISION = "7dabda4d13d513e3e842b20f0d435c732f172cbe"
MODEL_FILENAME = "qwen2.5-3b-instruct-q4_k_m.gguf"
MODEL_SHA256 = "626b4a6678b86442240e33df819e00132d3ba7dddfe1cdc4fbb18e0a9615c62d"
MODEL_BYTES = 2104932768
MODEL_LICENSE = "Qwen Research License"
DOWNLOAD_URL = f"https://huggingface.co/{MODEL_REPO}/resolve/{MODEL_REVISION}/{MODEL_FILENAME}"


def run_native_fallback():
    """Install with Win32 dialogs when tkinter is unavailable in the frozen build."""
    user32 = ctypes.windll.user32
    message = (
        "Install BASIN Drought Scenario Workbench?\n\n"
        f"Destination:\n{DEFAULT_INSTALL_DIR}\n\n"
        "The installer includes its own Python runtime and works offline."
    )
    # MB_OKCANCEL | MB_ICONINFORMATION
    if user32.MessageBoxW(0, message, "BASIN Setup", 0x41) != 1:
        return

    # Ask if user wants to download optional Qwen AI model weights
    ai_message = (
        "Download optional local Qwen 2.5 AI model weights (~2.1 GB)?\n\n"
        "Select YES to download official weights from Hugging Face.\n"
        "Select NO to install core BASIN with instant deterministic tools (100% offline)."
    )
    # MB_YESNO | MB_ICONQUESTION
    download_ai = (user32.MessageBoxW(0, ai_message, "Optional Local AI", 0x24) == 6)

    try:
        perform_install(DEFAULT_INSTALL_DIR, download_ai=download_ai)
    except Exception as exc:
        user32.MessageBoxW(
            0,
            f"BASIN could not be installed:\n\n{exc}",
            "BASIN Setup Error",
            0x10,  # MB_ICONERROR
        )
        raise

    user32.MessageBoxW(
        0,
        f"BASIN was installed successfully to:\n\n{DEFAULT_INSTALL_DIR}",
        "BASIN Setup Complete",
        0x40,  # MB_ICONINFORMATION
    )
    subprocess.Popen([str(DEFAULT_INSTALL_DIR / "BASIN.exe")], cwd=str(DEFAULT_INSTALL_DIR))


def get_payload_path() -> Path:
    """Locate the embedded or companion basin_payload.zip archive."""
    # 1. PyInstaller single-file temp extraction dir
    if hasattr(sys, "_MEIPASS"):
        meipass_zip = Path(sys._MEIPASS) / "basin_payload.zip"
        if meipass_zip.exists():
            return meipass_zip

    # 2. Beside current executable
    exe_dir = Path(sys.executable).parent
    beside_zip = exe_dir / "basin_payload.zip"
    if beside_zip.exists():
        return beside_zip

    # 3. Project dist directory (development mode)
    root_dist = Path(__file__).resolve().parents[1] / "dist" / "basin_payload.zip"
    if root_dist.exists():
        return root_dist

    raise FileNotFoundError("Could not locate basin_payload.zip installer payload.")


def create_shortcut(target_exe: Path, link_path: Path, icon_path: Path, work_dir: Path):
    """Create a Windows .lnk shortcut using PowerShell COM automation."""
    link_path.parent.mkdir(parents=True, exist_ok=True)
    ps_cmd = (
        f"$ws = New-Object -ComObject WScript.Shell; "
        f"$s = $ws.CreateShortcut('{str(link_path)}'); "
        f"$s.TargetPath = '{str(target_exe)}'; "
        f"$s.WorkingDirectory = '{str(work_dir)}'; "
        f"$s.IconLocation = '{str(icon_path)},0'; "
        f"$s.Save()"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def register_uninstaller(install_dir: Path):
    """Register BASIN in Windows HKCU Installed Apps list."""
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\BASIN"
    exe_path = install_dir / "BASIN.exe"
    uninstaller_bat = install_dir / "uninstall.bat"

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "BASIN Drought Workbench")
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f"{exe_path},0")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Coastal Bend Regional Hydrologic Analytics")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{uninstaller_bat}"')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
    except Exception as ex:
        print(f"[WARN] Failed to write registry uninstaller: {ex}", flush=True)


def download_qwen_model(install_dir: Path, progress_cb=None) -> bool:
    """Download and cryptographically verify pinned Qwen 2.5 3B GGUF weights."""
    models_dir = install_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    target_path = models_dir / MODEL_FILENAME
    manifest_path = models_dir / "manifest.json"

    manifest_data = {
        "repo": MODEL_REPO,
        "revision": MODEL_REVISION,
        "filename": MODEL_FILENAME,
        "sha256": MODEL_SHA256,
        "size_bytes": MODEL_BYTES,
        "license": MODEL_LICENSE,
        "quantization": "Q4_K_M",
        "format": "GGUF",
        "chat_template": "qwen",
    }

    # If file already exists with correct size, check hash
    if target_path.exists() and target_path.stat().st_size == MODEL_BYTES:
        if progress_cb:
            progress_cb(100, "Verifying existing AI model weights...")
        hasher = hashlib.sha256()
        with target_path.open("rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        if hasher.hexdigest() == MODEL_SHA256:
            manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
            return True

    tmp_path = models_dir / f"{MODEL_FILENAME}.tmp"
    if progress_cb:
        progress_cb(0, "Connecting to Hugging Face for Qwen AI Model...")

    req = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "BASIN-Setup-Wizard/1.0"})

    hasher = hashlib.sha256()
    downloaded = 0
    start_time = time.time()
    last_ui_update = start_time

    with urllib.request.urlopen(req, timeout=35.0) as resp, tmp_path.open("wb") as out_file:
        total = int(resp.headers.get("Content-Length", MODEL_BYTES))
        while chunk := resp.read(1024 * 256):
            out_file.write(chunk)
            hasher.update(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_ui_update >= 0.25:
                pct = min(99, int((downloaded / total) * 100))
                mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                speed = mb / (now - start_time) if now > start_time else 0
                if progress_cb:
                    progress_cb(pct, f"Downloading Qwen AI: {mb:.1f}/{total_mb:.1f} MB ({pct}%) · {speed:.1f} MB/s")
                last_ui_update = now

    if progress_cb:
        progress_cb(99, "Verifying SHA-256 cryptographic checksum...")

    actual_sha = hasher.hexdigest()
    if actual_sha != MODEL_SHA256:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Integrity check failed: expected {MODEL_SHA256[:12]}..., got {actual_sha[:12]}...")

    if tmp_path.stat().st_size != MODEL_BYTES:
        tmp_path.unlink(missing_ok=True)
        raise ValueError(f"Size mismatch: expected {MODEL_BYTES} bytes, got {tmp_path.stat().st_size}")

    if target_path.exists():
        target_path.unlink()
    tmp_path.rename(target_path)
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    if progress_cb:
        progress_cb(100, "Qwen AI Model verified and installed.")
    return True


def perform_install(
    install_dir: Path,
    desktop_shortcut: bool = True,
    startmenu_shortcut: bool = True,
    download_ai: bool = False,
    progress_cb=None,
    register_app: bool = True,
) -> dict:
    """Extract payload archive, configure shortcuts, and optionally download Qwen model."""
    payload_zip = get_payload_path()
    install_dir.mkdir(parents=True, exist_ok=True)

    # Calculate weights for progress bar: 30% extraction, 70% model download if AI requested
    extract_scale = 0.30 if download_ai else 0.95

    with zipfile.ZipFile(payload_zip, "r") as zf:
        infolist = zf.infolist()
        total_files = len(infolist)

        for idx, item in enumerate(infolist):
            zf.extract(item, install_dir)
            if progress_cb and (idx % 25 == 0 or idx == total_files - 1):
                raw_pct = (idx + 1) / total_files
                pct = int(raw_pct * extract_scale * 100)
                progress_cb(pct, f"Extracting: {item.filename}")

    exe_path = install_dir / "BASIN.exe"
    icon_path = install_dir / "assets" / "basin.ico"

    if desktop_shortcut:
        if progress_cb:
            progress_cb(int(extract_scale * 100) + 1, "Creating Desktop shortcut...")
        desktop_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        create_shortcut(exe_path, desktop_dir / "BASIN Drought Workbench.lnk", icon_path, install_dir)

    if startmenu_shortcut:
        if progress_cb:
            progress_cb(int(extract_scale * 100) + 2, "Creating Start Menu shortcut...")
        appdata_dir = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        programs_dir = appdata_dir / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        create_shortcut(exe_path, programs_dir / "BASIN Drought Workbench.lnk", icon_path, install_dir)

    if register_app:
        register_uninstaller(install_dir)

    ai_installed = False
    if download_ai:
        try:
            def ai_progress(pct, text):
                scaled = 33 + int(pct * 0.65)
                if progress_cb:
                    progress_cb(scaled, text)

            ai_installed = download_qwen_model(install_dir, ai_progress)
        except Exception as exc:
            print(f"[WARN] Optional AI download failed: {exc}", flush=True)
            if progress_cb:
                progress_cb(100, f"AI download skipped ({exc}). Core installed.")

    if progress_cb:
        progress_cb(100, "Installation complete.")

    return {"success": True, "ai_installed": ai_installed}


def run_gui():
    """Launch standard tkinter setup wizard window."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("BASIN Setup Wizard")
    root.geometry("540x470")
    root.resizable(False, False)

    # Window styling
    root.configure(bg="#F8F9FA")
    font_header = ("Segoe UI", 13, "bold")
    font_sub = ("Segoe UI", 9)
    font_small = ("Segoe UI", 8)
    font_btn = ("Segoe UI", 9, "bold")

    # Header Frame
    header_frame = tk.Frame(root, bg="#0F2B48", height=70)
    header_frame.pack(fill=tk.X, side=tk.TOP)
    header_frame.pack_propagate(False)

    title_label = tk.Label(
        header_frame,
        text="BASIN Drought Scenario Workbench",
        font=font_header,
        fg="#FFFFFF",
        bg="#0F2B48",
        anchor="w",
    )
    title_label.pack(side=tk.TOP, fill=tk.X, padx=20, pady=(12, 2))

    sub_label = tk.Label(
        header_frame,
        text="Standard Desktop Setup (Works Offline · No Python Required)",
        font=font_sub,
        fg="#DCE5ED",
        bg="#0F2B48",
        anchor="w",
    )
    sub_label.pack(side=tk.TOP, fill=tk.X, padx=20)

    # Content Frame
    content_frame = tk.Frame(root, bg="#F8F9FA", padx=25, pady=15)
    content_frame.pack(fill=tk.BOTH, expand=True)

    dest_var = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
    desktop_var = tk.BooleanVar(value=True)
    start_var = tk.BooleanVar(value=True)
    ai_var = tk.BooleanVar(value=False)
    launch_var = tk.BooleanVar(value=True)

    tk.Label(content_frame, text="Destination Folder:", font=font_sub, bg="#F8F9FA").pack(anchor="w", pady=(0, 4))
    dir_frame = tk.Frame(content_frame, bg="#F8F9FA")
    dir_frame.pack(fill=tk.X, pady=(0, 14))

    dir_entry = tk.Entry(dir_frame, textvariable=dest_var, font=font_sub, relief=tk.SOLID, bd=1)
    dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

    def browse_dir():
        d = filedialog.askdirectory(initialdir=dest_var.get())
        if d:
            dest_var.set(d)

    browse_btn = tk.Button(dir_frame, text="Browse...", font=font_sub, command=browse_dir)
    browse_btn.pack(side=tk.RIGHT, padx=(8, 0))

    tk.Label(content_frame, text="Installation Options:", font=font_sub, bg="#F8F9FA").pack(anchor="w", pady=(0, 4))
    tk.Checkbutton(content_frame, text="Create Desktop shortcut", variable=desktop_var, font=font_sub, bg="#F8F9FA").pack(anchor="w")
    tk.Checkbutton(content_frame, text="Create Start Menu shortcut", variable=start_var, font=font_sub, bg="#F8F9FA").pack(anchor="w")

    # Optional AI Model Checkbox (Without initial installer bloat)
    ai_check = tk.Checkbutton(
        content_frame,
        text="Download local Qwen 2.5 AI Model weights (~2.1 GB from Hugging Face)",
        variable=ai_var,
        font=font_sub,
        bg="#F8F9FA",
    )
    ai_check.pack(anchor="w", pady=(6, 0))

    ai_desc = tk.Label(
        content_frame,
        text="   Optional. Enables open-ended local AI chat. If unchecked, BASIN\n   uses instant built-in deterministic tools (100% offline, zero internet needed).",
        font=font_small,
        fg="#5A6A78",
        bg="#F8F9FA",
        justify=tk.LEFT,
    )
    ai_desc.pack(anchor="w", pady=(0, 6))

    progress_bar = ttk.Progressbar(content_frame, orient="horizontal", mode="determinate")
    status_label = tk.Label(content_frame, text="Ready to install.", font=font_sub, fg="#555555", bg="#F8F9FA", anchor="w")

    # Bottom Actions Frame
    bottom_frame = tk.Frame(root, bg="#ECEFF1", height=50)
    bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
    bottom_frame.pack_propagate(False)

    def start_installation():
        install_btn.config(state=tk.DISABLED)
        browse_btn.config(state=tk.DISABLED)
        dir_entry.config(state=tk.DISABLED)
        ai_check.config(state=tk.DISABLED)

        progress_bar.pack(fill=tk.X, pady=(12, 4))
        status_label.pack(fill=tk.X)

        target_dir = Path(dest_var.get())
        download_ai_chosen = ai_var.get()

        def worker():
            try:
                def on_progress(pct, text):
                    root.after(0, lambda: (progress_bar.config(value=pct), status_label.config(text=text)))

                result = perform_install(
                    target_dir,
                    desktop_shortcut=desktop_var.get(),
                    startmenu_shortcut=start_var.get(),
                    download_ai=download_ai_chosen,
                    progress_cb=on_progress,
                )
                time.sleep(0.5)
                root.after(0, lambda: show_finished(result.get("ai_installed", False)))
            except Exception as exc:
                root.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install BASIN:\n{exc}"))
                root.after(0, lambda: install_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def show_finished(ai_installed: bool):
        for widget in content_frame.winfo_children():
            widget.destroy()

        success_title = "✓ BASIN installed with Qwen 2.5 Local AI!" if ai_installed else "✓ BASIN is successfully installed!"
        tk.Label(
            content_frame,
            text=success_title,
            font=("Segoe UI", 12, "bold"),
            fg="#007A50",
            bg="#F8F9FA",
        ).pack(anchor="w", pady=(15, 10))

        if ai_installed:
            detail_msg = (
                f"Installed to:\n{dest_var.get()}\n\n"
                "✓ Core calculation engine and all 13 deterministic tools installed.\n"
                "✓ Qwen 2.5 3B GGUF weights downloaded and SHA-256 verified.\n"
                "You can now launch BASIN at any time directly from your Desktop."
            )
        else:
            detail_msg = (
                f"Installed to:\n{dest_var.get()}\n\n"
                "✓ Ready to run offline with instant deterministic hydrologic tools.\n\n"
                "Tip: To add the 2.1 GB Qwen AI model at any time later, simply\n"
                "double-click 'Download AI Model.cmd' inside the installation folder."
            )

        tk.Label(
            content_frame,
            text=detail_msg,
            font=font_sub,
            justify=tk.LEFT,
            bg="#F8F9FA",
        ).pack(anchor="w", pady=(0, 15))

        tk.Checkbutton(content_frame, text="Launch BASIN now", variable=launch_var, font=font_sub, bg="#F8F9FA").pack(anchor="w")

        install_btn.config(text="Finish", state=tk.NORMAL, command=on_finish)

    def on_finish():
        if launch_var.get():
            target_exe = Path(dest_var.get()) / "BASIN.exe"
            if target_exe.exists():
                subprocess.Popen([str(target_exe)], cwd=str(target_exe.parent))
        root.destroy()

    cancel_btn = tk.Button(bottom_frame, text="Cancel", font=font_sub, command=root.destroy, width=10)
    cancel_btn.pack(side=tk.RIGHT, padx=15, pady=10)

    install_btn = tk.Button(bottom_frame, text="Install", font=font_btn, bg="#0F2B48", fg="#FFFFFF", command=start_installation, width=12)
    install_btn.pack(side=tk.RIGHT, padx=(0, 0), pady=10)

    # Center window on screen
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (w // 2)
    y = (root.winfo_screenheight() // 2) - (h // 2)
    root.geometry(f"+{x}+{y}")

    root.mainloop()


def main():
    is_silent = any(arg.lower() in ("--silent", "-s", "/s") for arg in sys.argv[1:])
    with_ai = any(arg.lower() in ("--with-ai", "--download-model", "-ai") for arg in sys.argv[1:])
    target_dir = DEFAULT_INSTALL_DIR
    for idx, arg in enumerate(sys.argv):
        if arg in ("--dir", "-d") and idx + 1 < len(sys.argv):
            target_dir = Path(sys.argv[idx + 1])

    if is_silent:
        no_shortcuts = "--no-shortcuts" in sys.argv
        no_register = "--no-register" in sys.argv
        perform_install(
            target_dir,
            desktop_shortcut=not no_shortcuts,
            startmenu_shortcut=not no_shortcuts,
            download_ai=with_ai,
            register_app=not no_register,
        )
        sys.exit(0)

    try:
        run_gui()
    except (ImportError, ModuleNotFoundError):
        run_native_fallback()


if __name__ == "__main__":
    main()
