#!/bin/bash
# Setup Development Environment for Reachy Recognizer
# Usage: source ./start_dev.sh  (or . ./start_dev.sh)

echo "🚀 Setting up Reachy Recognizer Development Environment"
echo "============================================================"
echo ""

# Check Python version
echo "Checking Python environment..."
if command -v python3 &> /dev/null; then
    python3 --version
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    python --version
    PYTHON_CMD=python
else
    echo "❌ Python not found"
    return 1 2>/dev/null || exit 1
fi
echo "✓ Python ready"
echo ""

# Check for and activate virtual environment
echo "Checking for virtual environment..."
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment already active: $VIRTUAL_ENV"
elif [ -d ".venv" ]; then
    echo "Found .venv directory, activating..."
    source .venv/bin/activate
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
elif [ -d "venv" ]; then
    echo "Found venv directory, activating..."
    source venv/bin/activate
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "No virtual environment found. Create one? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Creating virtual environment..."
        $PYTHON_CMD -m venv .venv
        source .venv/bin/activate
        echo "✓ Virtual environment created and activated"
    else
        echo "⚠️  No virtual environment active"
        echo "   Consider creating one: python3 -m venv .venv"
    fi
fi
echo ""

# Set environment variables for OpenCV
echo "Setting environment variables..."
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "✓ OpenCV video backend configured"
echo "✓ PYTHONPATH set to include project root"
echo ""

# Detect if running on Raspberry Pi
IS_PI=false
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    IS_PI=true
    echo "🥧 Detected Raspberry Pi"
fi

# Check for required packages and install if missing
echo "Checking required packages..."
missing_packages=()

# Base packages (always needed)
packages=("numpy" "pyyaml")

# Add opencv and face-recognition based on platform
if [ "$IS_PI" = true ]; then
    # On Pi, check for system opencv first
    if $PYTHON_CMD -c "import cv2" 2>/dev/null; then
        echo "✓ opencv (system package)"
    else
        packages+=("opencv-python")
    fi
    # Skip face-recognition on Pi - we use OpenCV SFace model
    echo "○ face-recognition (not needed - using OpenCV SFace)"
else
    # On desktop, include both
    packages+=("opencv-python")
    # face-recognition is optional even on desktop
fi

for package in "${packages[@]}"; do
    module_name=$(echo $package | tr '-' '_')
    if $PYTHON_CMD -c "import $module_name" 2>/dev/null; then
        echo "✓ $package"
    else
        echo "✗ $package (not installed)"
        missing_packages+=("$package")
    fi
done

# Check for Reachy SDK (optional)
echo ""
echo "Checking optional packages..."
if $PYTHON_CMD -c "import reachy_mini" 2>/dev/null; then
    echo "✓ reachy-mini (for robot control)"
else
    echo "○ reachy-mini (optional - for robot control)"
fi
echo ""

# Install missing packages
if [ ${#missing_packages[@]} -gt 0 ]; then
    echo "⚠️  ${#missing_packages[@]} package(s) missing"
    echo "Install missing packages? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Installing missing packages..."
        
        # Choose requirements file based on platform
        if [ "$IS_PI" = true ] && [ -f "requirements-pi.txt" ]; then
            echo "Using requirements-pi.txt (optimized for Raspberry Pi)..."
            pip install -r requirements-pi.txt
        elif [ -f "requirements.txt" ]; then
            echo "Installing from requirements.txt..."
            pip install -r requirements.txt
        else
            echo "Installing individual packages..."
            for pkg in "${missing_packages[@]}"; do
                pip install "$pkg"
            done
        fi
        echo "✓ Package installation complete"
        echo ""
    else
        echo "⚠️  Some packages are missing. Install them manually:"
        if [ "$IS_PI" = true ] && [ -f "requirements-pi.txt" ]; then
            echo "   pip install -r requirements-pi.txt"
        else
            echo "   pip install ${missing_packages[*]}"
        fi
        echo ""
    fi
fi

# Show available commands
echo "Available commands:"
echo "  python3 main.py                    - Run main recognition system"
echo "  python3 demo.py                    - Run demo with Reachy robot"
echo "  python3 add_face.py 'Name'         - Add face to database (webcam)"
echo "  python3 add_face.py 'Name' --reachy - Add face to database (Reachy camera)"
echo "  python3 integrated_demo.py         - Run integrated demo"
echo ""
echo "Configuration:"
echo "  Edit: src/config/config.yaml"
echo "  Enable robot: Set 'enable_robot: true' in config.yaml"
echo ""
echo "✨ Environment ready! Happy coding!"
echo ""
