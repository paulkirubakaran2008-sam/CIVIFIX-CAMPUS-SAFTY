@echo off
echo ============================================
echo CivicFix Campus - one-time setup
echo ============================================
echo.

cd /d "%~dp0backend"
echo [1/5] Creating Python virtual environment...
py -m venv .venv
if errorlevel 1 (
    echo FAILED: could not create virtual environment. Is Python installed? Try running "py --version" to check.
    pause
    exit /b 1
)

echo [2/5] Installing backend dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo FAILED: pip install had an error, scroll up to see it.
    pause
    exit /b 1
)

echo [3/5] Creating backend\.env from example...
if not exist ".env" copy .env.example .env >nul

cd /d "%~dp0frontend"
echo [4/5] Installing frontend dependencies (this can take a minute)...
call npm install
if errorlevel 1 (
    echo FAILED: npm install had an error, scroll up to see it. Is Node.js installed? Try "node -v" to check.
    pause
    exit /b 1
)

echo [5/5] Creating frontend\.env from example...
if not exist ".env" copy .env.example .env >nul

echo.
echo ============================================
echo Setup complete!
echo Now run start-backend.bat, then in a separate
echo window run start-frontend.bat.
echo ============================================
pause
