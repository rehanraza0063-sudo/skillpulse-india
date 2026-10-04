@echo off
REM One-time setup for SkillPulse India on Windows. Run by double-clicking or from a terminal.
setlocal
cd /d "%~dp0"

echo.
echo [1/3] Creating Python virtual environment in backend\venv ...
cd backend
if not exist venv ( python -m venv venv || goto :error )
call venv\Scripts\activate || goto :error

echo.
echo [2/3] Installing backend packages ...
python -m pip install --upgrade pip
pip install -r requirements.txt || goto :error
cd ..

echo.
echo [3/3] Installing frontend packages (needs Node.js 18+) ...
cd frontend
call npm install || goto :error
cd ..

echo.
echo Setup complete. Start the app with run_all.bat
echo (the demo data is already in the data folder; regenerate it any time with: python scripts\generate_demo_data.py)
exit /b 0

:error
echo.
echo Setup failed. See the message above. Check that Python 3.10+ and Node.js 18+ are installed and on PATH.
exit /b 1
