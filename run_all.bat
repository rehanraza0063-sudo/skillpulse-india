@echo off
cd /d "%~dp0"
start "SkillPulse backend" cmd /k run_backend.bat
start "SkillPulse frontend" cmd /k run_frontend.bat
echo Two windows were opened. Open http://localhost:5173 in your browser (login: planner / demo123).
