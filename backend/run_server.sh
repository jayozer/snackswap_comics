#!/bin/bash
# Run the SnackSwap Comics backend server

set -e

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run server
echo "Starting SnackSwap Comics API..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
