#!/bin/bash
# Manual Model Download for Hailo-8L on Raspberry Pi 5
# Run this script on your Raspberry Pi

set -e

MODELS_DIR="$(dirname "$0")/models"
mkdir -p "$MODELS_DIR"

echo "=================================================="
echo "🔍 Hailo Model Download Helper"
echo "=================================================="
echo ""

# Check if we're on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
fi

echo "Target directory: $MODELS_DIR"
echo ""

# Method 1: Check hailo-rpi5-examples
echo "Method 1: Checking hailo-rpi5-examples..."
echo "---------------------------------------------------"
if [ -d "$HOME/hailo-rpi5-examples" ]; then
    echo "✅ hailo-rpi5-examples found"
    
    # Search for .hef files
    HEF_FILES=$(find "$HOME/hailo-rpi5-examples" -name "*.hef" 2>/dev/null || true)
    
    if [ -n "$HEF_FILES" ]; then
        echo "Found .hef files:"
        echo "$HEF_FILES"
        echo ""
        echo "Copy models? [y/N]"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "$HEF_FILES" | while read -r file; do
                cp "$file" "$MODELS_DIR/"
                echo "  ✅ Copied: $(basename "$file")"
            done
        fi
    else
        echo "  ❌ No .hef files found in hailo-rpi5-examples"
    fi
else
    echo "  ❌ hailo-rpi5-examples not found"
    echo "     Install with: git clone https://github.com/hailo-ai/hailo-rpi5-examples.git ~/hailo-rpi5-examples"
fi

echo ""
echo "Method 2: Download from Hailo Model Zoo"
echo "---------------------------------------------------"
echo ""
echo "Option A: Direct wget (if available)"
echo ""

# Try to download YOLOv8n directly
YOLO_URL="https://hailo-model-zoo.s3.eu-west-2.amazonaws.com/ModelZoo/Compiled/v2.13.0/hailo8l/yolov8n.hef"
echo "Attempting to download YOLOv8n..."
echo "URL: $YOLO_URL"
echo ""

if command -v wget &> /dev/null; then
    echo "Downloading with wget..."
    if wget -O "$MODELS_DIR/yolov8n.hef" "$YOLO_URL" 2>&1; then
        echo "✅ Downloaded yolov8n.hef"
    else
        echo "❌ Download failed (URL may have changed)"
        rm -f "$MODELS_DIR/yolov8n.hef"
    fi
elif command -v curl &> /dev/null; then
    echo "Downloading with curl..."
    if curl -L -o "$MODELS_DIR/yolov8n.hef" "$YOLO_URL"; then
        echo "✅ Downloaded yolov8n.hef"
    else
        echo "❌ Download failed (URL may have changed)"
        rm -f "$MODELS_DIR/yolov8n.hef"
    fi
else
    echo "❌ Neither wget nor curl found"
fi

echo ""
echo "Option B: Clone Hailo Model Zoo (large download)"
echo ""
echo "This will download the entire Model Zoo repo (~1-2 GB)"
echo "Continue? [y/N]"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Cloning Model Zoo..."
    cd /tmp
    git clone --depth 1 https://github.com/hailo-ai/hailo_model_zoo.git
    
    echo "Searching for Hailo-8L models..."
    find hailo_model_zoo -path "*/compiled/hailo8l/*.hef" -type f
    
    echo ""
    echo "Copy found models? [y/N]"
    read -r response2
    if [[ "$response2" =~ ^[Yy]$ ]]; then
        find hailo_model_zoo -path "*/compiled/hailo8l/*.hef" -type f -exec cp {} "$MODELS_DIR/" \;
        echo "✅ Models copied"
    fi
    
    rm -rf hailo_model_zoo
fi

echo ""
echo "=================================================="
echo "Manual Download Instructions"
echo "=================================================="
echo ""
echo "If automatic download failed, manually download from:"
echo ""
echo "1. Hailo Model Zoo Website:"
echo "   https://hailo.ai/developer-zone/model-zoo/"
echo ""
echo "2. GitHub Repository:"
echo "   https://github.com/hailo-ai/hailo_model_zoo"
echo "   Navigate to: hailo_model_zoo/compiled/hailo8l/"
echo ""
echo "3. Hailo Developer Zone:"
echo "   https://hailo.ai/developer-zone/"
echo "   (requires free account)"
echo ""
echo "Download YOLOv8n.hef for Hailo-8L and place in:"
echo "   $MODELS_DIR/"
echo ""

echo "=================================================="
echo "Current models in $MODELS_DIR:"
echo "=================================================="
if [ "$(ls -A $MODELS_DIR 2>/dev/null)" ]; then
    ls -lh "$MODELS_DIR"
    echo ""
    echo "✅ Models ready!"
else
    echo "(empty)"
    echo ""
    echo "❌ No models found. Please download manually."
fi

echo ""
echo "=================================================="
echo "Next Steps:"
echo "=================================================="
echo "1. Ensure you have a .hef model in: $MODELS_DIR/"
echo "2. Run: python3 test_yolo_hailo.py"
echo ""
