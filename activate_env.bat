@echo off
setlocal EnableExtensions

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

if not exist "%PROJECT_DIR%.venv\Scripts\activate.bat" (
    echo [ERROR] .venv was not found.
    echo Run this first:
    echo   py -3.11 -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

set "PYTHONIOENCODING=utf-8"
set "HF_HOME=%PROJECT_DIR%.hf_cache"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"
set "TRANSFORMERS_CACHE="

call "%PROJECT_DIR%.venv\Scripts\activate.bat"

echo.
echo [OK] AI Subtitle Assistant environment is active.
echo Project: %CD%
echo Python:
python -c "import sys; print('  ' + sys.executable)"
echo.
echo Common commands:
echo   ai-sub doctor
echo   ai-sub video\input.mp4 --overwrite
echo   ai-sub-gui
echo   open_ui.bat
echo   python -m pytest -q
echo.

if /I "%~1"=="--no-shell" (
    endlocal & (
        set "PATH=%PATH%"
        set "VIRTUAL_ENV=%VIRTUAL_ENV%"
        set "PYTHONIOENCODING=%PYTHONIOENCODING%"
        set "HF_HOME=%HF_HOME%"
        set "HF_HUB_DISABLE_SYMLINKS_WARNING=%HF_HUB_DISABLE_SYMLINKS_WARNING%"
        set "TRANSFORMERS_CACHE="
        set "PROMPT=%PROMPT%"
    )
    exit /b 0
)

cmd /k
