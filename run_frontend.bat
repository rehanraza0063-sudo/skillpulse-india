@echo off
cd /d "%~dp0frontend"
echo Frontend on http://localhost:5173
call npm run dev
