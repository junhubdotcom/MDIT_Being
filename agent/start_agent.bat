@echo off
REM Being Agent Service Startup Script for Windows (module mode)

setlocal enabledelayedexpansion

echo 🤖 Starting Being Agent Service...
echo =================================

REM Resolve project root (one level up from this script's folder)
set SCRIPT_DIR=%~dp0
set ROOT_DIR=%SCRIPT_DIR%..

REM Change to project root
pushd "%ROOT_DIR%"

REM Create virtual environment in project root if missing
if not exist ".venv" (
    echo 📦 Creating virtual environment in project root...
    python -m venv .venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call .venv\Scripts\activate

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r agent\requirements.txt

REM Start FastAPI server using module execution from project root
echo 🚀 Starting Being Agent FastAPI server...
echo 📡 Server will be available at: http://localhost:8000
echo 📚 API documentation at: http://localhost:8000/docs
echo.
python -m agent.fastapi_server

popd

pause