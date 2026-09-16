@echo off
setlocal
cd /d "%~dp0"
echo ======================================================================
echo   BASIN AI Model Setup - Qwen 2.5 3B GGUF (~2.1 GB)
echo ======================================================================
echo Downloading official pinned weights from Hugging Face...
echo Repository: Qwen/Qwen2.5-3B-Instruct-GGUF
echo Target:     models\qwen2.5-3b-instruct-q4_k_m.gguf
echo.

if exist "runtime\python.exe" (
    ".\runtime\python.exe" "scripts\fetch_model.py"
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "scripts\fetch_model.py"
) else (
    py -3.12 "scripts\fetch_model.py"
)

if errorlevel 1 (
    echo.
    echo [ERROR] Model download or SHA-256 verification failed.
    echo Note: BASIN core remains fully operational using deterministic tools.
) else (
    echo.
    echo [SUCCESS] Qwen 2.5 AI Model is installed and cryptographically verified.
    echo You can now launch BASIN to use conversational AI tool dispatch.
)

echo.
pause
