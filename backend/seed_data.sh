#!/bin/bash
# Seed Qdrant with sample data

set -e

cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Check for .env file
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys."
    exit 1
fi

# Run seeding script
echo "Seeding SnackSwap Comics data..."
python ../data/seeds/seed_data.py
