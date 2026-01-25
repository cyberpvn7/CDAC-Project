#!/bin/bash

# SecGuys Quick Start Setup
# Run this to initialize everything

set -e  # Exit on error

echo "🚀 SecGuys Integration Setup"
echo "=============================="
echo ""

# Step 1: Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install Python 3.9+."
    exit 1
fi
echo "✅ Python3 found: $(python3 --version)"
echo ""

# Step 2: Install Python dependencies
echo "[2/5] Installing Python dependencies..."
pip install --extra-index-url https://download.pytorch.org/whl/cpu -q -r requirements.txt --break-system-packages
echo "✅ Dependencies installed"
echo ""

# Step 3: Set API key
echo "[3/5] Checking Gemini API key..."
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set!"
    echo ""
    echo "Get your API key from: https://aistudio.google.com/app/apikey"
    echo "Then set it:"
    echo ""
    echo "    export GEMINI_API_KEY='AIza...'"
    echo ""
    echo "Or add to ~/.bashrc / ~/.zshrc for persistence"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ GEMINI_API_KEY is set"
fi
echo ""

# Step 4: Initialize database
echo "[4/5] Initializing database..."
cd "$(dirname "$0")/.." || exit 1
python3 setup/init_db.py
echo ""

# Step 4b: Run migrations (for existing databases)
echo "Running database migrations..."
python3 setup/migrate-db.py
echo ""

# Step 5: Verify setup
echo "[5/5] Verifying setup..."
if [ -f "security_analysis.db" ]; then
    echo "✅ Database created: security_analysis.db"
else
    echo "❌ Database creation failed"
    exit 1
fi

# Check config
if [ -f "config/config.yaml" ]; then
    echo "✅ Configuration file: config/config.yaml"
else
    echo "❌ Configuration file missing"
    exit 1
fi

echo ""
echo "=============================="
echo "✅ SETUP COMPLETE!"
echo "=============================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Scan a single target:"
echo "   python3 main.py 192.168.1.100"
echo ""
echo "2. Scan multiple targets:"
echo "   python3 main.py 192.168.1.100 192.168.1.101"
echo ""
echo "3. Scan from file (one target per line):"
echo "   python3 main.py targets.txt"
echo ""
echo "4. View results:"
echo "   cat db_report.md"
echo ""
echo "5. Read full documentation:"
echo "   cat INTEGRATION.md"
echo ""
