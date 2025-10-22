# Raspberry Pi 5 Setup Guide

## Prerequisites

- Raspberry Pi 5 (4GB or 8GB recommended)
- Raspberry Pi OS (64-bit) - Bookworm or newer
- Pi Camera Module V2/V3 or USB webcam
- Internet connection for package installation

## Installation Steps

### 1. System Update
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python Dependencies
```bash
# Install system packages
sudo apt install -y python3-pip python3-venv python3-opencv
sudo apt install -y libatlas-base-dev libhdf5-dev libhdf5-serial-dev
sudo apt install -y libharfbuzz-dev libwebp-dev libjasper-dev
sudo apt install -y libilmbase-dev libopenexr-dev libgstreamer1.0-dev

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install numpy opencv-python onnxruntime
```

### 3. For Pi Camera Module (Optional)
```bash
# Install picamera2
sudo apt install -y python3-picamera2
pip install picamera2
```

### 4. Clone Repository
```bash
git clone https://github.com/chelleboyer/reachy-recognizer.git
cd reachy-recognizer
```

### 5. Download Models
```bash
# Create models directory
mkdir -p models

# Download SFace model
wget -O models/face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

### 6. Configure Camera (for Pi Camera Module)

Edit `camera_interface.py` to use picamera2:

```python
from picamera2 import Picamera2
import cv2

class CameraInterface:
    def __init__(self, camera_id=0, width=640, height=480, fps=30):
        # For Pi Camera Module
        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={"size": (width, height), "format": "RGB888"}
        )
        self.camera.configure(config)
        self.camera.start()
        
    def read_frame(self):
        frame = self.camera.capture_array()
        # Convert RGB to BGR for OpenCV
        return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
```

## Performance Optimization for Pi 5

### 1. Use Smaller Frame Size
```python
camera = CameraInterface(width=320, height=240)  # Instead of 640x480
```

### 2. Reduce Detection Frequency
```python
# Only detect faces every 5th frame
if frame_count % 5 == 0:
    faces = detector.detect_faces(frame)
```

### 3. Use Haar Cascade (Not DNN)
Haar Cascade is faster on Pi - it's already your fallback:
```python
# This is what you're using now - keep it!
⚠ DNN models not found, using Haar cascade fallback
```

### 4. Lower Camera FPS
```python
camera = CameraInterface(fps=15)  # Instead of 30
```

## Expected Performance

### Raspberry Pi 5 Benchmarks:
- **Face Detection (Haar)**: 20-30ms per frame
- **Face Encoding (SFace)**: 30-40ms per face
- **Face Recognition**: 0.5-1ms per face
- **Total Pipeline**: 50-70ms → **~15-20 fps real-time**

### Comparison:
| Component | Laptop | Pi 5 | Pi 4 |
|-----------|--------|------|------|
| Detection | 5-10ms | 20-30ms | 60-100ms |
| Encoding | 10-15ms | 30-40ms | 100-150ms |
| Recognition | 0.1-0.5ms | 0.5-1ms | 1-2ms |
| **Total** | **15-25ms** | **50-70ms** | **160-250ms** |
| **FPS** | **40-60** | **15-20** | **4-6** |

## Testing on Pi

### 1. Test Camera
```bash
python camera_interface.py
```

### 2. Test Face Detection
```bash
python face_detector.py
```

### 3. Test Face Recognition
```bash
python face_recognizer.py
```

### 4. Add Your Face to Database
```bash
python -c "
from face_database import FaceDatabase
import cv2

db = FaceDatabase()
camera = cv2.VideoCapture(0)
ret, frame = camera.read()
db.add_face('YourName', frame)
db.save_database('faces.json')
camera.release()
"
```

## Troubleshooting

### Issue: "No module named 'cv2'"
```bash
pip install opencv-python
# Or use system package:
sudo apt install python3-opencv
```

### Issue: "Camera not found"
```bash
# List cameras
v4l2-ctl --list-devices

# Test camera
libcamera-hello
```

### Issue: "ONNX Runtime error"
```bash
# Install ARM64 version
pip install onnxruntime --extra-index-url https://www.piwheels.org/simple
```

### Issue: "Permission denied" for camera
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Logout and login again
```

## Memory Usage

Typical memory footprint on Pi 5:
- Python process: ~100-150 MB
- OpenCV: ~50-80 MB
- ONNX Runtime: ~30-50 MB
- Models loaded: ~10-20 MB
- **Total**: ~200-300 MB

Safe to run on 4GB Pi 5, comfortable on 8GB.

## Tips for Best Performance

1. **Use 64-bit Raspberry Pi OS** (not 32-bit)
2. **Overclock cautiously** (Pi 5 can handle 2.6-3.0 GHz)
3. **Use active cooling** (keeps CPU from throttling)
4. **Run headless** (save GPU resources)
5. **Disable unnecessary services**
6. **Use lightweight display** (if needed, use LXDE not full Raspberry Pi Desktop)

## What Works Out of the Box

✅ All Python code (platform-independent)
✅ NumPy vectorized operations
✅ OpenCV image processing
✅ ONNX model inference
✅ JSON database storage
✅ Face recognition pipeline
✅ USB webcam support

## What Needs Modification

⚠️ Camera interface (if using Pi Camera Module)
⚠️ Performance tuning (lower resolution/fps)
⚠️ Optional: GPIO integration for Reachy robot

## Next Steps After Pi Setup

Once running on Pi 5, you can:
1. Integrate with Reachy robot motors (see `reachy_mini/` folder)
2. Add GPIO triggers for recognition events
3. Connect to robot behavior system
4. Deploy as systemd service for auto-start
