"""Supported Windows browser launcher; Python 3.12 x64 and installed requirements required."""
from pathlib import Path
import argparse
import importlib.util
import socket
import struct
import subprocess
import sys
import time
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


def find_port(start=8501, count=50):
    for port in range(start, min(start + count, 65536)):
        try:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
    raise RuntimeError("No free local port. Close an older BASIN process or choose another port.")


def prerequisites():
    if sys.version_info[:2] != (3, 12) or struct.calcsize("P") != 8:
        raise RuntimeError("Use Python 3.12 (64-bit), then run Setup BASIN.cmd.")
    if importlib.util.find_spec("streamlit") is None:
        raise RuntimeError("Streamlit is not installed. Run Setup BASIN.cmd first.")
    if not (ROOT / "app.py").exists():
        raise RuntimeError("app.py is missing. Extract the complete BASIN package.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=8501)
    args = parser.parse_args()
    process = None
    try:
        prerequisites()
        if not 1024 <= args.port <= 65486:
            raise RuntimeError("Choose a starting port between 1024 and 65486.")
        port = find_port(args.port)
        credentials = ROOT / ".streamlit" / "credentials.toml"
        credentials.parent.mkdir(exist_ok=True)
        if not credentials.exists():
            credentials.write_text('[general]\nemail = ""\n', encoding="utf-8")
        process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
                                    "--server.address=127.0.0.1", f"--server.port={port}",
                                    "--server.headless=true", "--browser.gatherUsageStats=false"], cwd=ROOT)
        url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("BASIN could not start. Read the engine error above.")
            try:
                with urllib.request.urlopen(url + "/_stcore/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.25)
        else:
            raise RuntimeError("BASIN startup timed out. Retry after checking the engine output.")
        print(f"BASIN is ready at {url}. Keep this console open; Ctrl+C stops it.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        return process.wait()
    except KeyboardInterrupt:
        return 0
    except (RuntimeError, OSError) as error:
        print(f"BASIN: {error}", file=sys.stderr)
        return 1
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    raise SystemExit(main())
