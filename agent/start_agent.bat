@echo off
REM Being Agent Service Startup Script for Windows

echo 🤖 Starting Being Agent Service...
echo =================================

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Check if Ollama is running
echo 🦙 Checking Ollama status...
curl -s http://localhost:11434/api/version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Ollama is not running. Please start it with:
    echo    ollama serve
    echo    ollama pull llama3.2
    echo.
)

REM Start FastAPI server
echo 🚀 Starting Being Agent FastAPI server...
echo 📡 Server will be available at: http://localhost:8000
echo 📚 API documentation at: http://localhost:8000/docs
echo.
python fastapi_server.py

pause