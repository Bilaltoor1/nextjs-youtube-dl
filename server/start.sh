#!/bin/bash

# YTTMP3.com Flask API Server Startup Script

set -e

echo "🐍 Starting YTTMP3.com Flask API Server..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    print_error "pip is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Check if cookies file exists
if [ ! -f "../cookies.txt" ]; then
    print_warning "cookies.txt not found in parent directory!"
    print_warning "Some age-restricted videos may not work without cookies."
    print_warning "See ../cookies.txt for instructions on how to get YouTube cookies."
fi

# Check if ffmpeg is installed (required for audio conversion)
if ! command -v ffmpeg &> /dev/null; then
    print_error "ffmpeg is not installed!"
    print_error "Please install ffmpeg: sudo apt install ffmpeg"
    exit 1
fi

# Set environment variables
export FLASK_ENV=production
export FLASK_DEBUG=false
export FLASK_PORT=${FLASK_PORT:-5000}

print_status "Starting Flask server on port $FLASK_PORT..."

# Start the Flask server
python3 app.py