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
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)

    try:
        res = subprocess.run(["py", "-3.12", "-c", "import sys; print(sys.executable)"],
                             capture_output=True, text=True, check=True,
                             creationflags=0x08000000)
        found = res.stdout.strip()
        if found and Path(found).exists():
            return found
    except Exception:
        pass

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


def find_free_port(start_port: int = 8501) -> int:
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
        port += 1
    return start_port


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
            "Please run 'Setup BASIN.cmd' once to initialize the local environment.",
            "BASIN — Setup Required"
        )
        sys.exit(1)

    app_py = root / "app.py"
    if not app_py.exists():
        show_error(f"app.py not found in:\n{root}", "BASIN — Missing Core Files")
        sys.exit(1)

    port = find_free_port(8501)
    target_url = f"http://127.0.0.1:{port}"

    CREATE_NO_WINDOW = 0x08000000

    cmd = [
        python_exe, "-m", "streamlit", "run", "app.py",
        "--server.address=127.0.0.1",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]

    server_proc = subprocess.Popen(
        cmd,
        cwd=str(root),
        creationflags=CREATE_NO_WINDOW
    )

    def terminate_server():
        try:
            server_proc.terminate()
            server_proc.wait(timeout=3.0)
        except Exception:
            server_proc.kill()

    ready = wait_for_server(f"{target_url}/_stcore/health", timeout=25.0)
    if not ready:
        terminate_server()
        show_error("The BASIN calculation engine timed out during startup.", "BASIN — Startup Timeout")
        sys.exit(1)

    # Launch native desktop window using pywebview (WebView2 embedded in native Win32 window)
    try:
        import webview
        window = webview.create_window(
            title="BASIN — Basin Analysis and Scenario Intelligence Navigator",
            url=target_url,
            width=1600,
            height=950,
            min_size=(1050, 700),
            resizable=True,
            confirm_close=False,
            background_color="#F7F9F8"
        )
        window.events.closed += terminate_server
        webview.start(gui="edgechromium")
    except Exception as e:
        # Fallback if WebView2 is missing: try standalone app mode
        terminate_server()
        show_error(f"Could not initialize desktop application window:\n{e}", "BASIN — Desktop Error")
        sys.exit(1)

    terminate_server()


if __name__ == "__main__":
    main()
