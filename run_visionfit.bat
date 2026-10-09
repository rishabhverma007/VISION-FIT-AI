@echo off
cd /d "%~dp0"
echo Starting VisionFit AI...
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" start_app.py
) else (
    python start_app.py
)
pause
