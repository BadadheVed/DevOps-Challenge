#!/bin/bash

# Quick start script for FastAPI Telemetry Application

set -e

echo "🚀 FastAPI Telemetry Application - Quick Start"
echo "=============================================="
echo

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python version: $PYTHON_VERSION"

# Check if Python 3.14
if [[ "$PYTHON_VERSION" == 3.14.* ]]; then
    echo "❌ ERROR: Python 3.14 is not compatible with this application"
    echo "   Please use Python 3.9 - 3.13"
    echo "   You can install Python 3.13 via:"
    echo "   brew install python@3.13"
    exit 1
fi

# Check if version is between 3.9 and 3.13
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -ne 3 ] || [ "$MINOR" -lt 9 ] || [ "$MINOR" -gt 13 ]; then
    echo "⚠️  WARNING: This application is tested with Python 3.9-3.13"
    echo " Your version: $PYTHON_VERSION"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ Python version compatible"


# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi
echo

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo

# Set default OTEL collector URL if not set
if [ -z "$OTEL_COLLECTOR_URL" ]; then
    export OTEL_COLLECTOR_URL="otel-collector.monitoring.svc.cluster.local:4317"
    echo "📡 Using default OTEL Collector: $OTEL_COLLECTOR_URL"
else
    echo "📡 Using OTEL Collector: $OTEL_COLLECTOR_URL"
fi
echo

echo "✨ Setup complete! Starting application..."
echo "🌐 The app will be available at: http://localhost:8000"
echo "📚 API docs will be at: http://localhost:8000/docs"
echo
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo

# Start the application
uvicorn main:app --host 0.0.0.0 --port 8000
