#!/bin/bash

# AI Executive Panel Simulator - Quick Start Script

echo "🚀 Starting AI Executive Panel Simulator..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Copying template..."
    cp .env.template .env
    echo
    echo "🔧 Please edit .env and add your OpenAI API key:"
    echo "   OPENAI_API_KEY=sk-your-actual-api-key-here"
    echo
    echo "Then run this script again."
    exit 1
fi

# Start the application
echo "✅ Starting the application..."
echo "🌐 Open your browser to: http://localhost:5000"
echo
gunicorn app_v2:app -b 0.0.0.0:${PORT:-5000} --timeout 300
