#!/bin/bash
# Setup Development Environment for Reachy Recognizer
# Usage: source ./start_dev.sh  (or . ./start_dev.sh)

echo "🚀 Setting up Reachy Recognizer Development Environment"
echo "============================================================"
echo ""

# Set environment variables for OpenCV
echo "Setting environment variables..."
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "✓ OpenCV video backend configured"
echo "✓ PYTHONPATH set to include project root"
echo ""

# Check Python version
echo "Checking Python environment..."
python3 --version
echo "✓ Python ready"

# Check if virtual environment is active
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✓ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment active"
    echo "   Consider activating one for isolation"
fi
echo ""

# Check for required packages
echo "Checking required packages..."
packages=("opencv-python" "numpy" "face-recognition" "pyyaml")

for package in "${packages[@]}"; do
    module_name=$(echo $package | tr '-' '_')
    if python3 -c "import $module_name" 2>/dev/null; then
        echo "✓ $package"
    else
        echo "✗ $package (not installed)"
    fi
done
echo ""

# Check for Reachy SDK (optional)
echo "Checking optional packages..."
if python3 -c "import reachy_mini" 2>/dev/null; then
    echo "✓ reachy-mini (for robot control)"
else
    echo "○ reachy-mini (optional - for robot control)"
fi
echo ""

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
