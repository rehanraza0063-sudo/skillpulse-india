#!/usr/bin/env bash
# macOS / Linux helper (Windows users: use run_all.bat)
set -e
cd "$(dirname "$0")"
( cd backend && [ -d venv ] || python3 -m venv venv )
( cd backend && . venv/bin/activate && pip install -q -r requirements.txt && uvicorn app.main:app --reload ) &
( cd frontend && npm install && npm run dev ) &
wait
