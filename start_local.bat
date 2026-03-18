@echo off
echo =====================================================
echo    GESI AI PREMIUM V4.0 - LOCAL ENGINE LAUNCHER
echo =====================================================
echo.
echo [1/3] Checking dependencies...
pip install -r backend/requirements.txt --quiet

echo [2/3] Verifying frontend build...
if not exist "dist" (
    echo Building frontend for the first time...
    cmd /c npm run build
)

echo [3/3] Starting GESI AI TRADING ENGINE...
echo.
echo >>> Dashboard will be available at http://localhost:5000
echo.
python backend/api.py
pause
