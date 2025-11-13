# Hailo Setup Instructions for Raspberry Pi 5

## Prerequisites

- Raspberry Pi 5 with Hailo-8L AI Hat installed
- Raspberry Pi OS (64-bit, Bookworm or later)
- Internet connection

## Step 1: Install Hailo Software Stack

```bash
# SSH into your Raspberry Pi
ssh pi@<your-pi-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y git python3-pip python3-venv cmake

# Clone Hailo RPi5 examples repo
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples

# Run the installation script
./install.sh
```

This will:
- Install HailoRT (runtime library)
- Install Hailo Python API
- Setup PCIe drivers
- Install Tappas (optional, for GStreamer integration)

**Note:** You may need to reboot after installation.

```bash
sudo reboot
```

## Step 2: Verify Installation

```bash
# Check Hailo device is detected
lspci | grep Hailo
# Should see: Hailo-8 AI Processor

# Test Python API
python3 -c "from hailo_platform import Device; print('Hailo OK')"
```

## Step 3: Get YOLO Model in Hailo Format

### Option A: Download Pre-Converted Model

Check Hailo Model Zoo:
- https://github.com/hailo-ai/hailo_model_zoo

```bash
# Example: Download YOLOv8n
cd ~/hailo-rpi5-examples/models
# Download .hef file (Hailo Executable Format)
```

### Option B: Convert Your Own Model

**Requirements:**
- x86/x64 Linux machine (conversion cannot run on Pi)
- Hailo Dataflow Compiler installed
- ONNX model of YOLO nano

```bash
# On x86 machine with Hailo SDK installed
hailo parser onnx yolov8n.onnx
hailo optimize yolov8n.har
hailo compile yolov8n.har --hw-arch hailo8l
# Output: yolov8n.hef
```

Then copy `.hef` file to Raspberry Pi:

```bash
scp yolov8n.hef pi@<your-pi-ip>:~/reachy-mini-dev/hailo_poc/models/
```

## Step 4: Setup Python Environment

```bash
# On Raspberry Pi
cd ~/reachy-mini-dev/hailo_poc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Note: Hailo Python API should already be installed system-wide
# If needed, install in venv:
pip install /opt/hailo/hailo_platform-*.whl
```

## Step 5: Run Tests

```bash
# Test 1: Verify Hailo hardware
python3 test_hailo.py

# Expected output:
# ✅ Hailo Python API imported successfully
# ✅ Found 1 Hailo device(s)
# ✅ All tests passed!

# Test 2: Benchmark YOLO inference
python3 test_yolo_hailo.py

# Expected output:
# 📊 Benchmark Results:
# Average inference time: ~15-25 ms
# Throughput: 40-60 FPS
```

## Troubleshooting

### "No Hailo devices found"
```bash
# Check PCIe connection
lspci | grep Hailo

# Check kernel module
lsmod | grep hailo

# Check dmesg for errors
dmesg | grep -i hailo

# Try reseating the AI Hat
sudo poweroff
# Power off, reseat hat, power on
```

### "Cannot import hailo_platform"
```bash
# Install Hailo Python package
pip install /opt/hailo/hailo_platform-*.whl

# Or add to system path
export PYTHONPATH=/opt/hailo:$PYTHONPATH
```

### "Model not found"
```bash
# Ensure .hef file is in correct location
ls -la ~/reachy-mini-dev/hailo_poc/models/

# Update path in test_yolo_hailo.py
```

## Next Steps

Once tests pass:
1. ✅ Hailo hardware verified
2. ✅ YOLO inference working
3. ⏳ Integrate with Reachy camera
4. ⏳ Add FaceNet for face recognition
5. ⏳ Build complete recognition pipeline

## Resources

- Hailo Developer Zone: https://hailo.ai/developer-zone/
- Hailo Model Zoo: https://github.com/hailo-ai/hailo_model_zoo
- Hailo RPi5 Examples: https://github.com/hailo-ai/hailo-rpi5-examples
- Documentation: https://hailo.ai/developer-zone/documentation/
