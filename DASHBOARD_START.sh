#!/bin/bash
# SecGuys Dashboard - Quick Start Script

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🛡️  SecGuys Security Dashboard - Starting...           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to dashboard
cd "$(dirname "$0")/dashboard"

echo "📍 Current Directory: $(pwd)"
echo ""
echo "Starting Flask server..."
echo "────────────────────────────────────────────────────────────────"
echo ""
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt --break-system-packages
# Run the dashboard
./run_dashboard.sh

