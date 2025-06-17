@echo off
echo ========================================
echo Deploying Backend with Tunnel
echo ========================================
echo.

REM Check if localtunnel is installed
where lt >nul 2>nul
if %errorlevel% neq 0 (
    echo Localtunnel not found. Installing...
    npm install -g localtunnel
    echo.
)

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

echo Backend server is running. Starting tunnel...
echo.
echo Starting localtunnel on port 8000 with subdomain zoom-backend-1...
echo Your backend will be available at: https://zoom-backend-1.loca.lt
echo.
echo NOTE: If you see a password page, the password is usually displayed in this terminal.
echo.
lt --port 8000 --subdomain zoom-backend-1 --print-requests
