@echo off
setlocal
cd /d "%~dp0"
echo Setting up BASIN. Python 3.12 must already be installed.
py -3.12 -m venv .venv
if errorlevel 1 (
  echo Python 3.12 was not found. Install it from python.org before the event.
  pause
  exit /b 1
)
if exist "wheelhouse" (
  ".venv\Scripts\python.exe" -m pip install --no-index --find-links wheelhouse -r requirements.txt
) else (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
if errorlevel 1 (
  echo Installation failed. Keep the error above for troubleshooting.
  pause
  exit /b 1
)
echo Setup complete. Double-click Start BASIN.cmd.
pause
