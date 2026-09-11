@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem Optional embedded AI choices. BASIN's core never depends on them.
rem   no option     ask about the native AI runtime and the model weights separately
rem   --no-ai       core only, no AI questions
rem   --ai-runtime  core + native AI runtime; never downloads model weights
rem   --with-ai     core + native AI runtime + model weights download, about 2.1 GB
rem   --repair-ai   core + force-reinstall the pinned native AI runtime
set "AI_MODE=ASK"
if "%~1"=="--no-ai" set "AI_MODE=NONE"
if "%~1"=="--ai-runtime" set "AI_MODE=RUNTIME"
if "%~1"=="--with-ai" set "AI_MODE=FULL"
if "%~1"=="--repair-ai" set "AI_MODE=REPAIR"
if not "%~1"=="" if "!AI_MODE!"=="ASK" goto usage

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
echo Core BASIN installation complete. BASIN works fully offline without the AI assistant.
echo.
echo ======================================================================
echo Optional component: embedded local AI assistant - Qwen2.5-3B
echo ======================================================================
echo Local AI needs two separate pieces. BASIN itself needs neither.
echo   1. Native AI runtime - llama-cpp-python CPU wheel, about 7 MB, hash-pinned.
echo      Needs internet, or a wheelhouse folder that already contains the wheel.
echo   2. Model weights - about 2.1 GB from Hugging Face, hash-pinned. Needs internet.
echo Weights alone do NOT enable the assistant, and neither does the runtime alone.
echo Without both, the assistant uses BASIN's instant direct tools.
echo.

set "DO_RUNTIME=N"
set "DO_WEIGHTS=N"
set "RUNTIME_ARGS=--no-summary"
if "%AI_MODE%"=="RUNTIME" set "DO_RUNTIME=Y"
if "%AI_MODE%"=="FULL" set "DO_RUNTIME=Y"
if "%AI_MODE%"=="FULL" set "DO_WEIGHTS=Y"
if "%AI_MODE%"=="REPAIR" set "DO_RUNTIME=Y"
if "%AI_MODE%"=="REPAIR" set "RUNTIME_ARGS=--repair --no-summary"
if not "%AI_MODE%"=="ASK" goto ai_runtime

set "ANSWER="
set /p "ANSWER=Install the native AI runtime now? [y/N]: "
if /i "!ANSWER!"=="y" set "DO_RUNTIME=Y"
if /i "!ANSWER!"=="yes" set "DO_RUNTIME=Y"
set "ANSWER="
set /p "ANSWER=Download the 2.1 GB model weights now? [y/N]: "
if /i "!ANSWER!"=="y" set "DO_WEIGHTS=Y"
if /i "!ANSWER!"=="yes" set "DO_WEIGHTS=Y"

:ai_runtime
if "%DO_RUNTIME%"=="N" goto ai_weights
echo.
echo [AI 1/2] Native AI runtime
".venv\Scripts\python.exe" scripts\install_native_runtime.py %RUNTIME_ARGS%
if errorlevel 1 (
  echo Native AI runtime is NOT installed or NOT usable. BASIN core is unaffected.
  echo Retry later with: "Setup BASIN.cmd" --repair-ai
) else (
  echo Native AI runtime installed and importable.
)

:ai_weights
if "%DO_WEIGHTS%"=="N" goto ai_summary
echo.
echo [AI 2/2] Model weights - downloading about 2.1 GB
".venv\Scripts\python.exe" scripts\fetch_model.py
if errorlevel 1 (
  echo Model weights were NOT downloaded or did NOT verify. BASIN core is unaffected.
) else (
  echo Model weights downloaded and SHA-256 verified.
)

:ai_summary
echo.
if "%DO_RUNTIME%%DO_WEIGHTS%"=="NN" goto ai_skipped
".venv\Scripts\python.exe" scripts\install_native_runtime.py --check
goto done

:ai_skipped
echo Optional AI skipped. The assistant will use BASIN's instant direct tools.
echo To add local AI later, run: "Setup BASIN.cmd" --ai-runtime
echo and then, with internet: .venv\Scripts\python.exe scripts\fetch_model.py

:done
echo.
echo Setup complete. Double-click Start BASIN.cmd.
pause
exit /b 0

:usage
echo Unknown option: %~1
echo Usage: "Setup BASIN.cmd" [--no-ai ^| --ai-runtime ^| --with-ai ^| --repair-ai]
exit /b 2
