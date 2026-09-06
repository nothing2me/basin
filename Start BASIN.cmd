@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run: double-click Setup BASIN.cmd before starting BASIN.
  pause
  exit /b 1
)
echo BASIN is running locally. Open http://127.0.0.1:8501
echo Keep this window open while using BASIN. Press Ctrl+C to stop.
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.headless false
if errorlevel 1 pause
