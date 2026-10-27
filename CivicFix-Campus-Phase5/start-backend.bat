@echo off
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
echo Starting CivicFix backend on http://localhost:8000
echo Leave this window open. Close it to stop the server.
echo Health check: http://localhost:8000/health
echo.
uvicorn app.main:app --reload --reload-dir app --port 8000
pause
