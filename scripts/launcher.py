"""BASIN Native Desktop Application Launcher.
Runs BASIN entirely inside a native desktop window (pywebview with embedded EdgeChromium WebView2).
Zero browser window launches.
"""
from pathlib import Path
import ctypes
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request


def show_error(message: str, title: str = "BASIN — Application Error"):
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        pass


def find_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def ensure_credentials(root: Path):
    """Permanently suppress Streamlit's first-time onboarding email prompt."""
    cred_file = root / ".streamlit" / "credentials.toml"
    cred_file.parent.mkdir(parents=True, exist_ok=True)
    if not cred_file.exists():
        cred_file.write_text('[general]\nemail = ""\n', encoding="utf-8")

    try:
        user_cred = Path.home() / ".streamlit" / "credentials.toml"
        user_cred.parent.mkdir(parents=True, exist_ok=True)
        if not user_cred.exists():
            user_cred.write_text('[general]\nemail = ""\n', encoding="utf-8")
    except Exception:
        pass


def find_python(root: Path) -> str:
    # 1. Bundled standalone portable runtime (for offline setup installations)
    bundled_py = root / "runtime" / "python.exe"
    if bundled_py.exists():
        return str(bundled_py)

    bundled_venv = root / "runtime" / "Scripts" / "python.exe"
    if bundled_venv.exists():
        return str(bundled_venv)

    # 2. Local developer virtual environment
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)

    # 3. System Python launcher (py -3.12)
    try:
        res = subprocess.run(["py", "-3.12", "-c", "import sys; print(sys.executable)"],
                             capture_output=True, text=True, check=True,
                             creationflags=0x08000000)
        found = res.stdout.strip()
        if found and Path(found).exists():
            return found
    except Exception:
        pass

    # 4. Standard PATH python
    try:
        res = subprocess.run(["python", "-c", "import sys; print(sys.executable)"],
                             capture_output=True, text=True, check=True,
                             creationflags=0x08000000)
        found = res.stdout.strip()
        if found and Path(found).exists():
            return found
    except Exception:
        pass

    return ""


def find_free_port(start_port: int = 8501, count: int = 50) -> int:
    for port in range(start_port, min(start_port + count, 65536)):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
    raise RuntimeError(f"No free local port found in range {start_port}-{start_port + count - 1}.")


def wait_for_server(url: str, timeout: float = 25.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


def main():
    root = find_root()
    os.chdir(str(root))

    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    ensure_credentials(root)

    python_exe = find_python(root)
    if not python_exe:
        show_error(
            "Python 3.12 environment not found.\n\n"
            "Please run 'Setup BASIN.cmd' or install via 'Setup-BASIN.exe' to initialize.",
            "BASIN — Setup Required"
        )
        sys.exit(1)

    app_py = root / "app.py"
    if not app_py.exists():
        show_error(f"app.py not found in:\n{root}", "BASIN — Missing Core Files")
        sys.exit(1)

    try:
        port = find_free_port(8501)
    except RuntimeError as err:
        show_error(
            f"{err}\n\n"
            "Please close older BASIN or Streamlit processes occupying local ports.",
            "BASIN — Port Unavailable"
        )
        sys.exit(1)

    target_url = f"http://127.0.0.1:{port}"

    CREATE_NO_WINDOW = 0x08000000

    cmd = [
        python_exe, "-m", "streamlit", "run", "app.py",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false"
    ]

    server_proc = subprocess.Popen(
        cmd,
        cwd=str(root),
        creationflags=CREATE_NO_WINDOW
    )

    def terminate_server():
        try:
            if sys.platform == "win32" and server_proc.poll() is None:
                # Force kill the entire process tree (/T) to prevent zombie workers
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(server_proc.pid)],
                    capture_output=True,
                    creationflags=CREATE_NO_WINDOW
                )
        except Exception:
            pass
        try:
            server_proc.terminate()
            server_proc.wait(timeout=2.0)
        except Exception:
            server_proc.kill()

    ready = wait_for_server(f"{target_url}/_stcore/health", timeout=25.0)
    if not ready:
        terminate_server()
        show_error("The BASIN calculation engine timed out during startup.", "BASIN — Startup Timeout")
        sys.exit(1)

    # Launch native desktop window using pywebview (WebView2 embedded in native Win32 window)
    window_opened = False
    try:
        import webview
        webview.settings["ALLOW_DOWNLOADS"] = True
        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
        window = webview.create_window(
            title="BASIN — Basin Analysis and Scenario Intelligence Navigator",
            url=target_url,
            width=1600,
            height=950,
            min_size=(1050, 700),
            resizable=True,
            confirm_close=False,
            background_color="#FFFFFF"
        )
        window.events.closed += terminate_server
        webview.start(gui="edgechromium")
        window_opened = True
    except Exception:
        # Fallback if WebView2 is missing on older/offline Windows: open in default browser
        pass

    if not window_opened:
        try:
            import webbrowser
            webbrowser.open(target_url)
            # Keep process alive while user is browsing
            while server_proc.poll() is None:
                time.sleep(1.0)
        except Exception as e:
            terminate_server()
            show_error(f"Could not open application interface:\n{e}", "BASIN — Interface Error")
            sys.exit(1)

    terminate_server()


if __name__ == "__main__":
    main()

