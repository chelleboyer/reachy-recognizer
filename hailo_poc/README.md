# Hailo AI Hat + YOLO nano - Proof of Concept

## Hardware
- Raspberry Pi 5
- Hailo-8L AI Hat (26 TOPS)
- Reachy Mini camera

## Goal
Verify YOLO nano face detection running on Hailo accelerator.

## Setup Steps

### 1. Install Hailo Software Stack

```bash
# On Raspberry Pi 5
# Update system
sudo apt update && sudo apt upgrade -y

# Install Hailo dependencies
sudo apt install -y python3-pip python3-venv

# Install Hailo Runtime & Tappas
# Follow: https://github.com/hailo-ai/hailo-rpi5-examples
```

### 2. Convert YOLO nano to Hailo Format

YOLO models need to be converted to Hailo's `.hef` format for hardware acceleration.

**Options:**
- Use pre-converted model from Hailo Model Zoo
- Convert yourself using Hailo Dataflow Compiler (requires x86 machine)

### 3. Model Selection

**Recommended for face detection:**
- `yolov8n` (YOLO v8 nano) - General object detection
- OR `yolov8n-face` - Face-specific variant (if available)
- OR `retinaface` - Specialized face detector (may need conversion)

### 4. Performance Targets

With Hailo-8L (26 TOPS):
- **Expected FPS:** 30-60+ FPS @ 640x640 input
- **Latency:** <20ms per frame
- **Power:** Low power consumption on Pi 5

## Directory Structure

```
hailo_poc/
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── models/            # Hailo .hef model files
├── test_hailo.py      # Test Hailo is working
├── test_yolo_hailo.py # Run YOLO on Hailo
├── benchmark.py       # FPS and latency testing
└── camera_demo.py     # Live camera feed demo
```

## Next Steps

1. ✅ Create PoC structure
2. ⏳ Install Hailo software stack on Pi
3. ⏳ Get YOLO nano model in .hef format
4. ⏳ Test inference speed
5. ⏳ Integrate with Reachy camera
