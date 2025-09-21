#!/bin/bash

# PurdueAI Startup Script

echo "🚂 Starting PurdueAI Web Server..."
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create one with your API keys:"
    echo "   OPENAI_API_KEY=your_openai_api_key_here"
    echo "   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here"
    exit 1
fi

# Start the Flask server
echo "✅ Starting server on http://localhost:5001"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python app.py
