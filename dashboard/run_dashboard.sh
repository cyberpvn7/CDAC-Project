#!/bin/bash

# SecGuys Dashboard - Startup Script

echo "╔════════════════════════════════════════╗"
echo "║   SecGuys Security Dashboard           ║"
echo "║   Starting Dashboard...                ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt -q

# Run the Flask app
echo ""
echo "Dashboard is running at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
