"""BASIN Standalone Offline Setup Wizard.

A native, zero-dependency Windows setup wizard using standard Python tkinter.
Can run as a GUI wizard or headless with --silent / /S.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
import winreg
import zipfile
from pathlib import Path

# In PyInstaller --noconsole mode on Windows, sys.stdout and sys.stderr can be None.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

DEFAULT_INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "BASIN"


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


def perform_install(install_dir: Path, desktop_shortcut: bool = True, startmenu_shortcut: bool = True, progress_cb=None):
    """Extract payload archive and configure shortcuts and uninstaller."""
    payload_zip = get_payload_path()
    install_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(payload_zip, "r") as zf:
        infolist = zf.infolist()
        total_files = len(infolist)

        for idx, item in enumerate(infolist):
            zf.extract(item, install_dir)
            if progress_cb and (idx % 25 == 0 or idx == total_files - 1):
                pct = int((idx + 1) / total_files * 100)
                progress_cb(pct, f"Extracting: {item.filename}")

    exe_path = install_dir / "BASIN.exe"
    icon_path = install_dir / "assets" / "basin.ico"

    if desktop_shortcut:
        if progress_cb:
            progress_cb(96, "Creating Desktop shortcut...")
        desktop_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
        create_shortcut(exe_path, desktop_dir / "BASIN Drought Workbench.lnk", icon_path, install_dir)

    if startmenu_shortcut:
        if progress_cb:
            progress_cb(98, "Creating Start Menu shortcut...")
        appdata_dir = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
        programs_dir = appdata_dir / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        create_shortcut(exe_path, programs_dir / "BASIN Drought Workbench.lnk", icon_path, install_dir)

    register_uninstaller(install_dir)

    if progress_cb:
        progress_cb(100, "Installation complete.")


def run_gui():
    """Launch standard tkinter setup wizard window."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("BASIN Setup Wizard")
    root.geometry("520x400")
    root.resizable(False, False)

    # Window styling
    root.configure(bg="#F8F9FA")
    font_header = ("Segoe UI", 13, "bold")
    font_sub = ("Segoe UI", 9)
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
        text="Offline Installation Package (No Internet or Python Required)",
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
    launch_var = tk.BooleanVar(value=True)

    tk.Label(content_frame, text="Destination Folder:", font=font_sub, bg="#F8F9FA").pack(anchor="w", pady=(0, 4))
    dir_frame = tk.Frame(content_frame, bg="#F8F9FA")
    dir_frame.pack(fill=tk.X, pady=(0, 15))

    dir_entry = tk.Entry(dir_frame, textvariable=dest_var, font=font_sub, relief=tk.SOLID, bd=1)
    dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

    def browse_dir():
        d = filedialog.askdirectory(initialdir=dest_var.get())
        if d:
            dest_var.set(d)

    browse_btn = tk.Button(dir_frame, text="Browse...", font=font_sub, command=browse_dir)
    browse_btn.pack(side=tk.RIGHT, padx=(8, 0))

    tk.Label(content_frame, text="Options:", font=font_sub, bg="#F8F9FA").pack(anchor="w", pady=(0, 4))
    tk.Checkbutton(content_frame, text="Create Desktop shortcut", variable=desktop_var, font=font_sub, bg="#F8F9FA").pack(anchor="w")
    tk.Checkbutton(content_frame, text="Create Start Menu shortcut", variable=start_var, font=font_sub, bg="#F8F9FA").pack(anchor="w")

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

        progress_bar.pack(fill=tk.X, pady=(15, 4))
        status_label.pack(fill=tk.X)

        target_dir = Path(dest_var.get())

        def worker():
            try:
                def on_progress(pct, text):
                    root.after(0, lambda: (progress_bar.config(value=pct), status_label.config(text=text)))

                perform_install(target_dir, desktop_var.get(), start_var.get(), on_progress)
                time.sleep(0.5)
                root.after(0, show_finished)
            except Exception as exc:
                root.after(0, lambda: messagebox.showerror("Installation Error", f"Failed to install BASIN:\n{exc}"))
                root.after(0, lambda: install_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def show_finished():
        for widget in content_frame.winfo_children():
            widget.destroy()

        tk.Label(
            content_frame,
            text="✓ BASIN is successfully installed!",
            font=("Segoe UI", 12, "bold"),
            fg="#007A50",
            bg="#F8F9FA",
        ).pack(anchor="w", pady=(15, 10))

        tk.Label(
            content_frame,
            text=f"Installed to:\n{dest_var.get()}\n\nYou can launch BASIN at any time from your Desktop\nor Start Menu even completely offline.",
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
    target_dir = DEFAULT_INSTALL_DIR
    for idx, arg in enumerate(sys.argv):
        if arg in ("--dir", "-d") and idx + 1 < len(sys.argv):
            target_dir = Path(sys.argv[idx + 1])

    if is_silent:
        perform_install(target_dir)
        sys.exit(0)

    run_gui()


if __name__ == "__main__":
    main()
