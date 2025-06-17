@echo off
echo ========================================
echo Deploying Backend with Ngrok
echo ========================================
echo.

REM Check if backend server is running
echo Checking if backend server is running on port 8000...
curl -s http://localhost:8000/health >nul 2>nul
if %errorlevel% neq 0 (
    echo Backend server is not running!
    echo Please run the backend server first in another terminal:
    echo   cd backend
    echo   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo Backend server is running. Starting ngrok tunnel...
echo.
echo Your backend will be available at a URL shown by ngrok
echo Look for the "Forwarding" line that shows https://xxxxx.ngrok.io -> http://localhost:8000
echo.
cd ..
ngrok http 8000
