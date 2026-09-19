@echo off
TITLE MEDGUARD — Medicine Storage Intelligence Platform
COLOR 0A

echo ==============================================================================
echo MEDGUARD — Intelligent Medicine Storage Monitoring & Early Warning System
echo Production IoT & AI Cold-Chain Platform
echo ==============================================================================
echo.

SET VENV_PYTHON=C:\Users\HP\.gemini\antigravity\scratch\medguard\backend\.venv\Scripts\python.exe

IF NOT EXIST "%VENV_PYTHON%" (
    echo [ERROR] Python virtual environment not found at:
    echo %VENV_PYTHON%
    echo Please install dependencies or verify paths.
    pause
    exit /b 1
)

cd /d C:\Users\HP\.gemini\antigravity\scratch\medguard\backend

echo [1/3] Verifying SQLite database and seeding default data...
"%VENV_PYTHON%" seed_data.py

echo.
echo [2/3] Starting MEDGUARD Core FastAPI & WebSocket Server on http://127.0.0.1:8000 ...
echo - Landing Page:      http://127.0.0.1:8000/
echo - Command Dashboard: http://127.0.0.1:8000/dashboard
echo - Interactive Docs:  http://127.0.0.1:8000/docs
echo.

start "" http://127.0.0.1:8000/dashboard

"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
