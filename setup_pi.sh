#!/bin/bash
# Raspberry Pi Setup Script
# Automated setup for Reachy Recognizer on Raspberry Pi 4/5

set -e  # Exit on error

echo "=========================================="
echo "Reachy Recognizer - Raspberry Pi Setup"
echo "=========================================="
echo ""

# Detect OS
if [[ ! -f /etc/os-release ]]; then
    echo "❌ Cannot detect OS. Is this a Raspberry Pi with Raspberry Pi OS?"
    exit 1
fi

source /etc/os-release
echo "✓ Detected: $PRETTY_NAME"

# Check if running on Pi
if [[ ! "$ID" =~ ^(raspbian|debian)$ ]]; then
    echo "⚠️  Warning: Not running on Raspberry Pi OS"
    echo "   This script is optimized for Raspberry Pi 4/5"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check architecture
ARCH=$(uname -m)
echo "✓ Architecture: $ARCH"
if [[ "$ARCH" != "aarch64" ]] && [[ "$ARCH" != "armv7l" ]]; then
    echo "⚠️  Warning: Not ARM architecture (expected aarch64 or armv7l)"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "Step 1: System Update"
echo "=========================================="
echo ""

read -p "Update system packages? (recommended) (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt update
    echo "✓ Package list updated"
else
    echo "⏭️  Skipped system update"
fi

echo ""
echo "=========================================="
echo "Step 2: Install System Dependencies"
echo "=========================================="
echo ""

echo "Installing Python and development tools..."
sudo apt install -y python3-pip python3-venv python3-dev git

echo ""
echo "Installing OpenCV and numeric libraries (system packages - faster on Pi)..."
sudo apt install -y python3-opencv python3-numpy python3-pil python3-yaml

echo ""
read -p "Install audio support libraries? (optional - for voice features) (y/n) " -n 1 -r
echo
INSTALL_AUDIO=false
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install audio development libraries (needed for pip packages)
    echo "Installing audio development libraries..."
    sudo apt install -y portaudio19-dev libsndfile1 libsndfile1-dev
    sudo apt install -y ffmpeg  # For pydub/audio processing
    echo "✓ Audio libraries installed (Python packages will be installed via pip)"
    INSTALL_AUDIO=true
else
    echo "⏭️  Skipped audio support"
fi

echo ""
echo "=========================================="
echo "Step 3: Python Virtual Environment"
echo "=========================================="
echo ""

if [[ -d ".venv" ]]; then
    echo "✓ Virtual environment already exists at .venv"
    read -p "Recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        echo "✓ Recreated virtual environment"
    fi
else
    python3 -m venv .venv
    echo "✓ Created virtual environment"
fi

source .venv/bin/activate
echo "✓ Activated virtual environment"

echo ""
echo "=========================================="
echo "Step 4: Install Python Packages"
echo "=========================================="
echo ""

echo "Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Installing from requirements-pi.txt (optimized for Raspberry Pi)..."
if [[ -f "requirements-pi.txt" ]]; then
    pip install -r requirements-pi.txt
    echo "✓ Installed Pi requirements"
    
    # Install audio packages if user opted in
    if [[ "$INSTALL_AUDIO" = true ]]; then
        echo ""
        echo "Installing audio packages via pip..."
        pip install pygame pyaudio librosa pyttsx3 pydub
        echo "✓ Audio Python packages installed (pygame, pyaudio, librosa, pyttsx3, pydub)"
    fi
else
    echo "⚠️  requirements-pi.txt not found, using requirements.txt"
    pip install -r requirements.txt
fi

echo ""
echo "=========================================="
echo "Step 5: Download Face Recognition Models"
echo "=========================================="
echo ""

mkdir -p models

if [[ -f "models/face_recognition_sface_2021dec.onnx" ]]; then
    echo "✓ SFace model already exists"
else
    echo "Downloading SFace model from OpenCV Zoo..."
    wget -O models/face_recognition_sface_2021dec.onnx \
        https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
    echo "✓ Downloaded SFace model"
fi

echo ""
echo "=========================================="
echo "Step 6: Configuration"
echo "=========================================="
echo ""

if [[ -f "src/config/config.yaml" ]]; then
    echo "✓ Configuration file exists"
    
    # Check if robot is disabled
    if grep -q "enable_robot: false" src/config/config.yaml; then
        echo "✓ Robot mode disabled (good for testing without hardware)"
    else
        read -p "Disable robot mode? (recommended for testing) (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sed -i 's/enable_robot: true/enable_robot: false/' src/config/config.yaml
            echo "✓ Disabled robot mode"
        fi
    fi
else
    echo "⚠️  Configuration file not found at src/config/config.yaml"
fi

echo ""
echo "=========================================="
echo "Step 7: Verify Installation"
echo "=========================================="
echo ""

echo "Testing Python imports..."
python3 << 'EOF'
import sys
try:
    import cv2
    print("✓ OpenCV:", cv2.__version__)
except:
    print("❌ OpenCV not found")
    sys.exit(1)

try:
    import numpy as np
    print("✓ NumPy:", np.__version__)
except:
    print("❌ NumPy not found")
    sys.exit(1)

try:
    import yaml
    print("✓ PyYAML: OK")
except:
    print("❌ PyYAML not found")
    sys.exit(1)

try:
    from pathlib import Path
    model_path = Path("models/face_recognition_sface_2021dec.onnx")
    if model_path.exists():
        size_mb = model_path.stat().st_size / 1024 / 1024
        print(f"✓ SFace model: {size_mb:.1f} MB")
    else:
        print("❌ SFace model not found")
        sys.exit(1)
except Exception as e:
    print(f"❌ Model check failed: {e}")
    sys.exit(1)

print("\n✅ All core dependencies verified!")
EOF

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Activate environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Test camera and face detection:"
echo "   python add_face.py --name TestUser"
echo ""
echo "3. Run tests:"
echo "   ./quick_test.sh"
echo ""
echo "4. Start main app:"
echo "   python main.py"
echo ""
echo "For more info, see:"
echo "  - PI_QUICK_START.md"
echo "  - docs/RASPBERRY_PI_SETUP.md"
echo ""
echo "=========================================="
