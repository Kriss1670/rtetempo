#!/bin/bash
# Script to run tests in GitHub Codespaces or CI environment
# This script sets up the Python environment and runs the test suite

set -e

echo "🔧 Setting up Python environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo "📦 Installing dependencies..."

# Upgrade pip
pip install --upgrade pip --quiet

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov hypothesis --quiet

# Install Home Assistant and other dependencies
pip install homeassistant oauthlib requests-oauthlib python-dateutil --quiet

echo "🧪 Running tests..."

# Run tests with coverage
python -m pytest tests/ -v --tb=short --cov=custom_components/rtetempo --cov-report=term-missing

echo "✅ Tests completed!"
