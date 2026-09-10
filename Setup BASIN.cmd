@echo off
setlocal enabledelayedexpansion
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

echo.
echo ======================================================================
echo Optional Component: Embedded Local AI Assistant (Qwen2.5-3B)
echo ======================================================================
echo The assistant can run an embedded 2.1 GB local AI model for natural
echo language questions.
echo - Downloading the model requires an active internet connection (~2.1 GB).
echo - If skipped, BASIN operates 100%% offline with instant direct calculators.
echo.

set "DO_DOWNLOAD=N"
if "%~1"=="--with-ai" set "DO_DOWNLOAD=Y"
if "%~1"=="--no-ai" set "DO_DOWNLOAD=N"
if "%~1"=="" (
  set /p "INSTALL_AI=Download and activate embedded AI model now? [y/N]: "
  if /i "!INSTALL_AI!"=="y" set "DO_DOWNLOAD=Y"
  if /i "!INSTALL_AI!"=="yes" set "DO_DOWNLOAD=Y"
)

if "%DO_DOWNLOAD%"=="Y" (
  echo.
  echo Downloading Qwen2.5-3B-Instruct model (~2.1 GB)...
  ".venv\Scripts\python.exe" scripts\fetch_model.py
  if errorlevel 1 (
    echo Model download encountered an issue. BASIN will run in offline mode.
  ) else (
    echo Model downloaded and verified successfully!
  )
) else (
  echo Skipping model download. BASIN will run in instant offline mode.
  echo (You can download the model anytime later by running: python scripts\fetch_model.py)
)

echo.
echo Setup complete. Double-click Start BASIN.cmd.
pause

