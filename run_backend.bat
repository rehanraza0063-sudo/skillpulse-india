@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate
echo Backend on http://localhost:8000  (API docs: http://localhost:8000/docs)
uvicorn app.main:app --reload
