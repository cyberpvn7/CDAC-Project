#!/bin/bash

# SecGuys Dashboard Setup & Runner

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"

echo "🛡️  SecGuys Dashboard Setup"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi

# Check main.py exists
if [ ! -f "$PROJECT_ROOT/main.py" ]; then
    echo "❌ SecGuys main.py not found. Run from project root."
    exit 1
fi

# Create virtual environment if needed
if [ ! -d "$DASHBOARD_DIR/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$DASHBOARD_DIR/venv"
fi

# Activate virtual environment
source "$DASHBOARD_DIR/venv/bin/activate"

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -q -r "$DASHBOARD_DIR/requirements.txt"

# Also install main project dependencies
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    echo "📥 Installing main project dependencies..."
    pip install -q -r "$PROJECT_ROOT/requirements.txt" 2>/dev/null || true
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting dashboard server..."
echo "📊 Open: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Flask app
cd "$PROJECT_ROOT"
python3 "$DASHBOARD_DIR/app.py"
