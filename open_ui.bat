@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "%PROJECT_DIR%.venv\Scripts\pythonw.exe" (
    echo [ERROR] .venv or PyQt environment was not found.
    echo Run this first:
    echo   %PROJECT_DIR%.venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%PROJECT_DIR%.hf_cache"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE="

start "" "%PROJECT_DIR%.venv\Scripts\pythonw.exe" -m aisrt.gui
endlocal
