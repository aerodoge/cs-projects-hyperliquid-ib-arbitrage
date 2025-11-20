#!/bin/bash

# Quickstart script for Hyperliquid NVDA Data Collector

echo "=========================================="
echo "Hyperliquid NVDA Data Collector"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "=========================================="
echo "Testing data fetching..."
echo "=========================================="
echo ""

# Run test
python src/test_final.py

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To start the collector, run:"
echo ""
echo "  1. Copy and edit configuration:"
echo "     cp .env.example .env"
echo "     # Edit .env and set PUSH_GATEWAY_URL"
echo ""
echo "  2. Run the collector:"
echo "     python src/main.py"
echo ""
echo "Or run with custom parameters:"
echo "  python src/main.py --push-gateway YOUR_GATEWAY:9091 --interval 60"
echo ""
