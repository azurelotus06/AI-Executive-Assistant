@echo off
title Starting All Services

:: Frontend Ngrok Tunnel
start "Frontend Ngrok" cmd /k ngrok config add-authtoken 2ydKXuZqLODxjY6qSLGwIR56sSC_2o1MskeR7n4AWFMo43qPo && ngrok http --url=magnetic-thrush-currently.ngrok-free.app 3000

:: Backend Ngrok Tunnel
start "Backend Ngrok" cmd /k ngrok config add-authtoken 2yctB2Q3QJhMjaaFhyyOG2JzwYj_7pD88yGnhkAsb8r8qPWGm && ngrok http --url=bold-chow-trivially.ngrok-free.app 8000

:: Local Frontend
start "Frontend" cmd /k cd frontend && npm start

:: Local Backend
start "Backend" cmd /k cd backend && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
