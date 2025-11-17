#!/bin/bash
# Quick install script for local TTS options

echo "=========================================="
echo "Local TTS Installation"
echo "=========================================="
echo ""

# Option 1: eSpeak-ng (Fast, always works)
echo "Option 1: eSpeak-ng (Simple, fast)"
echo "  Quality: Basic ⭐⭐"
echo "  Speed: Very fast (50-100ms)"
echo "  Size: ~5MB"
echo ""
read -p "Install eSpeak-ng? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt-get update
    sudo apt-get install -y espeak-ng
    echo "✓ eSpeak-ng installed!"
    echo "  Test: espeak-ng 'Hello from Reachy'"
fi

echo ""

# Option 2: Piper (High quality but needs model download)
echo "Option 2: Piper TTS (High quality, local)"
echo "  Quality: Excellent ⭐⭐⭐⭐"
echo "  Speed: Fast (200-400ms)"
echo "  Size: ~60MB (library + voice)"
echo ""
read -p "Install Piper TTS? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip install piper-tts
    
    # Try to download voice
    echo "Downloading default voice (amy)..."
    mkdir -p ~/.local/share/piper
    cd ~/.local/share/piper
    
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx
    wget -q https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json
    
    if [ -f "en_US-amy-medium.onnx" ]; then
        echo "✓ Piper installed with amy voice!"
        echo "  Test: echo 'Hello from Reachy' | piper --model en_US-amy-medium --output_file test.wav && aplay test.wav"
    else
        echo "⚠️  Piper installed but voice download failed"
        echo "  Try manual download from: https://huggingface.co/rhasspy/piper-voices"
    fi
fi

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Now run with local TTS:"
echo "  python3 conversation_demo.py --reachy --llm ollama --no-cloud"
echo ""
