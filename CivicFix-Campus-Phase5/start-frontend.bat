@echo off
cd /d "%~dp0frontend"
echo Starting CivicFix frontend.
echo Once you see a "Local:" address below, open it in your browser.
echo Leave this window open. Close it to stop the server.
echo.
npm run dev
pause
