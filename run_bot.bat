@echo off
echo.
echo ==========================================
echo AI FOREX TRADING BOT - INITIALIZATION
echo ==========================================
echo.

:: 1. Check for .env file
if not exist ".env" (
    echo [ERROR] .env file missing! Creating from .env.example...
    copy .env.example .env
    echo [ACTION] PLEASE FILL IN YOUR CREDENTIALS IN .env BEFORE RUNNING AGAIN.
    pause
    exit /b
)

:: 2. Install Python dependencies
echo [1/3] Checking Python dependencies...
python -m pip install -r backend/requirements.txt

:: 3. Start Backend
echo [2/3] Starting Backend API...
start "Trading Bot Backend" cmd /k "set PYTHONPATH=. && python backend/api.py"

:: 4. Instructions for Frontend
echo [3/3] Dashboard Backend started on http://localhost:5000
echo.
echo ==============================================
echo IMPORTANT: Ensure MetaTrader 5 Terminal is OPEN
echo and logged in to your account.
echo ==============================================
echo.
echo NEXT STEP: Open a new terminal and run:
echo    cd frontend
echo    npm run dev
echo ==============================================
echo.
pause
