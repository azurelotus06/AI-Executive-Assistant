@echo off
echo Starting backend tunnel...
cd /d %~dp0
echo Current directory: %cd%
echo.
echo Starting localtunnel on port 8000...
lt --port 8000  --subdomain zoom-backend-1 --print-requests
