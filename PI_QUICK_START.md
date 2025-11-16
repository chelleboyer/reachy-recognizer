# Raspberry Pi Quick Start Guide

## One-Line Setup (For Raspberry Pi 4/5 with Raspberry Pi OS 64-bit)

```bash
# Clone and setup
git clone https://github.com/chelleboyer/reachy-recognizer.git && cd reachy-recognizer && ./setup_pi.sh
```

## Manual Setup

### 1. System Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system packages (recommended - faster than pip on Pi)
sudo apt install -y python3-opencv python3-numpy python3-pip python3-venv
sudo apt install -y python3-yaml python3-pil

# Optional audio support (libraries for pip packages)
sudo apt install -y portaudio19-dev libsndfile1 libsndfile1-dev ffmpeg
```

### 2. Clone Repository

```bash
git clone https://github.com/chelleboyer/reachy-recognizer.git
cd reachy-recognizer
```

### 3. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Python Packages

```bash
# Use Pi-specific requirements (lighter dependencies)
pip install -r requirements-pi.txt

# Optional: Install audio packages if needed for voice features
pip install librosa pyttsx3 pydub

# OR if you want full desktop version:
# pip install -r requirements.txt
```

### 5. Download Face Recognition Model

```bash
# Create models directory
mkdir -p models

# Download SFace model (required for face recognition)
wget -O models/face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

### 6. Configure for Pi

```bash
# Edit config to disable robot mode (if testing without Reachy hardware)
cat > src/config/config.yaml << 'EOF'
robot:
  enable_robot: false
  port: /dev/ttyACM0
  
camera:
  source: 0  # 0 for USB camera, adjust for Pi Camera
  width: 640
  height: 480
  fps: 30
  
face_recognition:
  threshold: 0.5
  detection_interval_frames: 5  # Process every 5th frame for better Pi performance
EOF
```

### 7. Test Installation

```bash
# Use the helper script
./start_dev.sh

# Or manual activation
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Quick tests
python quick_test.sh
```

### 8. Add Your Face to Database

```bash
source .venv/bin/activate
python add_face.py --name "YourName"
# Or if using Reachy camera:
python add_face.py --name "YourName" --reachy
```

## Performance Optimization for Raspberry Pi

### Reduce Frame Processing
Edit `src/config/config.yaml`:
```yaml
face_recognition:
  detection_interval_frames: 10  # Process every 10th frame instead of 5
```

### Lower Camera Resolution
```yaml
camera:
  width: 320   # Down from 640
  height: 240  # Down from 480
  fps: 15      # Down from 30
```

### Expected Performance
- **Raspberry Pi 5**: 15-20 FPS (real-time capable)
- **Raspberry Pi 4**: 5-10 FPS (usable)
- **Raspberry Pi 3**: 2-5 FPS (slow but functional)

## Troubleshooting

### "No module named cv2"
```bash
# Use system opencv (faster on Pi)
sudo apt install python3-opencv
# Then DON'T install opencv-python via pip
```

### "Camera not found"
```bash
# List available cameras
v4l2-ctl --list-devices

# Test camera
libcamera-hello  # For Pi Camera
ffplay /dev/video0  # For USB camera
```

### "Permission denied" for camera
```bash
sudo usermod -a -G video $USER
# Logout and login again
```

### Models not found
```bash
# Redownload models
cd models
wget https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

### Out of memory
```bash
# Increase swap (Pi 4 with 2GB RAM)
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## What Works on Pi

✅ All face recognition features (using OpenCV SFace model)  
✅ Camera capture (USB webcam or Pi Camera)  
✅ Face detection (Haar Cascade - fast on Pi)  
✅ Face encoding (ONNX runtime optimized for ARM)  
✅ Face database (JSON storage)  
✅ Configuration system  
✅ All Python scripts  

## What's Different from Desktop

⚠️ **No `face-recognition` library** - We use OpenCV SFace model instead (already implemented!)  
⚠️ **Lighter dependencies** - Use `requirements-pi.txt` instead of `requirements.txt`  
⚠️ **System packages preferred** - Install opencv, numpy via apt for better performance  
⚠️ **Lower frame rates** - Process every 5-10 frames instead of every frame  

## Integration with Reachy Robot

If running on Reachy's onboard Raspberry Pi:

```bash
# Enable robot mode in config
sed -i 's/enable_robot: false/enable_robot: true/' src/config/config.yaml

# Start daemon (in separate terminal)
./start_daemon.sh

# Run main app
python main.py
```

## System Service (Auto-start on Boot)

Create systemd service:
```bash
sudo nano /etc/systemd/system/reachy-recognizer.service
```

Add:
```ini
[Unit]
Description=Reachy Recognizer Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/reachy-recognizer
ExecStart=/home/pi/reachy-recognizer/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable reachy-recognizer
sudo systemctl start reachy-recognizer
sudo systemctl status reachy-recognizer
```

## Next Steps

1. Test face recognition with `python add_face.py`
2. Verify recognition works: `python main.py` (or your test script)
3. Optimize performance based on your Pi model
4. Integrate with Reachy robot if available
5. Set up auto-start service if deploying permanently
