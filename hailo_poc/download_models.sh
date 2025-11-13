#!/bin/bash
# Download pre-converted YOLO models for Hailo-8L on Raspberry Pi 5

set -e  # Exit on error

echo "=================================================="
echo "Hailo Model Downloader for Raspberry Pi 5"
echo "=================================================="

# Create models directory
MODELS_DIR="$(dirname "$0")/models"
mkdir -p "$MODELS_DIR"

echo ""
echo "📂 Models directory: $MODELS_DIR"
echo ""

# Check if hailo-rpi5-examples exists
if [ -d "$HOME/hailo-rpi5-examples" ]; then
    echo "✅ Found hailo-rpi5-examples repo"
    
    # Copy available models
    echo "📦 Copying models from hailo-rpi5-examples..."
    
    # Common model locations
    EXAMPLE_MODELS=(
        "$HOME/hailo-rpi5-examples/resources/yolov8n.hef"
        "$HOME/hailo-rpi5-examples/resources/yolov5n.hef"
        "$HOME/hailo-rpi5-examples/resources/yolov8s.hef"
    )
    
    FOUND_MODELS=0
    for model in "${EXAMPLE_MODELS[@]}"; do
        if [ -f "$model" ]; then
            cp "$model" "$MODELS_DIR/"
            echo "  ✅ Copied: $(basename $model)"
            FOUND_MODELS=$((FOUND_MODELS + 1))
        fi
    done
    
    if [ $FOUND_MODELS -eq 0 ]; then
        echo "  ⚠️  No .hef models found in hailo-rpi5-examples/resources/"
        echo "     The examples repo might not include pre-compiled models."
    fi
else
    echo "⚠️  hailo-rpi5-examples not found at $HOME/hailo-rpi5-examples"
    echo "   Run: git clone https://github.com/hailo-ai/hailo-rpi5-examples.git ~/hailo-rpi5-examples"
fi

echo ""
echo "=================================================="
echo "Alternative: Download from Hailo Model Zoo"
echo "=================================================="
echo ""
echo "If models are not available locally, download from:"
echo "  https://github.com/hailo-ai/hailo_model_zoo"
echo ""
echo "Or use the Hailo Model Zoo browser:"
echo "  https://hailo.ai/developer-zone/model-zoo/"
echo ""
echo "For YOLOv8n face detection, you can also try:"
echo "  https://github.com/hailo-ai/hailo_model_zoo/tree/master/hailo_model_zoo/cfg/networks"
echo ""

# List downloaded models
echo "=================================================="
echo "Available models in $MODELS_DIR:"
echo "=================================================="
ls -lh "$MODELS_DIR" || echo "  (empty)"
echo ""

if [ "$(ls -A $MODELS_DIR)" ]; then
    echo "✅ Models ready! Update test_yolo_hailo.py with the model path."
else
    echo "⚠️  No models found. Please download manually or check Hailo resources."
fi

echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo "1. If no models found, visit Hailo Model Zoo"
echo "2. Download YOLOv8n.hef for Hailo-8L"
echo "3. Place in: $MODELS_DIR/"
echo "4. Run: python3 test_yolo_hailo.py"
echo ""
