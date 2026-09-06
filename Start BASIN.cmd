@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run: double-click Setup BASIN.cmd before starting BASIN.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\start_browser.py
if errorlevel 1 pause
