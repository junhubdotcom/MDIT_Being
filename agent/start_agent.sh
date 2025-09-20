#!/bin/bash
# Being Agent Service Startup Script

echo "🤖 Starting Being Agent Service..."
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if Ollama is running
echo "🦙 Checking Ollama status..."
if ! curl -s http://localhost:11434/api/version > /dev/null; then
    echo "⚠️  Ollama is not running. Please start it with:"
    echo "   ollama serve"
    echo "   ollama pull llama3.2"
    echo ""
fi

# Start FastAPI server
echo "🚀 Starting Being Agent FastAPI server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
python fastapi_server.py