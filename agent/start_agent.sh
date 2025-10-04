#!/bin/bash
# Being Agent Service Startup Script (module mode, Google AI Studio only)

set -e

echo "🤖 Starting Being Agent Service..."
echo "================================="

# Resolve project root (one level up from this script's folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="${SCRIPT_DIR}/.."
cd "${ROOT_DIR}"

# Check/create virtual environment in project root
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment in project root..."
    python -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r agent/requirements.txt

# Start FastAPI server using module execution from project root
echo "🚀 Starting Being Agent FastAPI server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "📚 API documentation at: http://localhost:8000/docs"
echo ""
python -m agent.fastapi_server