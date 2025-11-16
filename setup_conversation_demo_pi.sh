#!/bin/bash
# Deploy Conversation Demo to Raspberry Pi
# Run this FROM the Pi after transferring files manually
# Usage: ./setup_conversation_demo_pi.sh

set -e  # Exit on error

echo "========================================"
echo "  Conversation Demo Setup on Pi5       "
echo "========================================"
echo ""

# Check if we're on a Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Continuing anyway..."
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[1/6] Checking required files..."
REQUIRED_FILES=(
    "conversation_demo.py"
    "src/"
    "models/vosk-model-small-en-us-0.15/"
    ".env"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        echo "✗ Missing: $file"
        MISSING=1
    fi
done

if [ $MISSING -eq 1 ]; then
    echo ""
    echo "✗ Some required files are missing!"
    echo "   Please transfer files to Pi first using SCP:"
    echo "   scp -r conversation_demo.py src/ models/ .env pi@<pi-ip>:~/reachy-mini-dev/"
    exit 1
fi
echo "✓ All required files present"
echo ""

# Update package list
echo "[2/6] Updating package list..."
sudo apt-get update -qq
echo "✓ Package list updated"
echo ""

# Install system dependencies for PyAudio
echo "[3/6] Installing system dependencies..."
sudo apt-get install -y -qq portaudio19-dev python3-pyaudio 2>&1 | grep -v "is already the newest version" || true
echo "✓ System dependencies installed"
echo ""

# Install Python packages
echo "[4/6] Installing Python packages..."
pip install --quiet vosk pyaudio openai python-dotenv mediapipe 2>&1 | grep -v "Requirement already satisfied" || true
echo "✓ Python packages installed"
echo ""

# Verify Vosk model
echo "[5/6] Verifying Vosk model..."
if [ ! -f "models/vosk-model-small-en-us-0.15/am/final.mdl" ]; then
    echo "✗ Vosk model appears incomplete"
    echo "   The model directory exists but critical files are missing"
    echo "   Please re-download the model: https://alphacephei.com/vosk/models"
    exit 1
fi
echo "✓ Vosk model verified"
echo ""

# Test imports
echo "[6/6] Testing imports..."
python3 -c "
import vosk
import pyaudio
import openai
import mediapipe
import cv2
print('✓ All imports successful')
" || {
    echo "✗ Import test failed"
    echo "   Some packages may not have installed correctly"
    exit 1
}
echo ""

# Check if daemon is running
echo "========================================"
echo "  Checking Reachy Mini Setup           "
echo "========================================"
echo ""

if pgrep -f "reachy-mini-daemon" > /dev/null; then
    echo "✓ Reachy Mini daemon is running"
else
    echo "⚠️  Reachy Mini daemon is NOT running"
    echo "   Start it with: reachy-mini-daemon"
    echo "   Or in background: nohup reachy-mini-daemon > daemon.log 2>&1 &"
fi
echo ""

# Check for serial port
if ls /dev/ttyUSB* 1> /dev/null 2>&1 || ls /dev/ttyACM* 1> /dev/null 2>&1; then
    echo "✓ Serial port detected:"
    ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true
else
    echo "⚠️  No serial port detected (/dev/ttyUSB* or /dev/ttyACM*)"
    echo "   Make sure Reachy is connected via USB"
fi
echo ""

# Test microphone
echo "Testing microphone..."
if arecord -l 2>/dev/null | grep -q "card"; then
    echo "✓ Microphone detected:"
    arecord -l 2>/dev/null | grep "card" | head -n 1
else
    echo "⚠️  No microphone detected"
    echo "   Speech recognition requires a microphone"
fi
echo ""

# Test camera
echo "Testing camera..."
if python3 -c "import cv2; cap = cv2.VideoCapture(0); ret, _ = cap.read(); cap.release(); exit(0 if ret else 1)" 2>/dev/null; then
    echo "✓ Camera is working"
else
    echo "⚠️  Camera test failed"
    echo "   Check camera connection"
fi
echo ""

echo "========================================"
echo "  Setup Complete!                      "
echo "========================================"
echo ""
echo "To run the conversation demo:"
echo ""
echo "  1. Start Reachy daemon (if not running):"
echo "     reachy-mini-daemon"
echo ""
echo "  2. In another terminal, run:"
echo "     cd $SCRIPT_DIR"
echo "     python3 conversation_demo.py --reachy --headless"
echo ""
echo "  3. Or with display (if X11 forwarding enabled):"
echo "     python3 conversation_demo.py --reachy"
echo ""
echo "To test gesture demo instead:"
echo "     python3 gesture_voice_demo.py --reachy --headless"
echo ""
echo "Press Ctrl+C to stop the demo when running"
echo ""
