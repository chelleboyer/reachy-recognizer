#!/bin/bash
# Quick Test Script for Reachy Recognizer
# Usage: ./quick_test.sh

echo "🧪 Quick Test - Reachy Recognizer"
echo "============================================================"
echo ""

# Setup environment
export OPENCV_VIDEOIO_PRIORITY_MSMF=0
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Test 1: Import test
echo "Test 1: Core imports"
python3 -c "
import cv2
import numpy as np
from src.vision.face_detector import FaceDetector
from src.vision.face_encoder import FaceEncoder
from src.vision.face_database import FaceDatabase
print('✓ All core modules imported successfully')
" 2>&1

if [ $? -ne 0 ]; then
    echo "❌ Import test failed"
    exit 1
fi
echo ""

# Test 2: Camera test
echo "Test 2: Camera access"
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f'✓ Camera working: {frame.shape[1]}x{frame.shape[0]}')
    else:
        print('✗ Camera opened but failed to read frame')
    cap.release()
else:
    print('✗ Could not open camera')
" 2>&1
echo ""

# Test 3: Face detection test
echo "Test 3: Face detector initialization"
python3 -c "
from src.vision.face_detector import FaceDetector
detector = FaceDetector()
print('✓ Face detector initialized')
" 2>&1
echo ""

# Test 4: Database test
echo "Test 4: Face database"
python3 -c "
from src.vision.face_database import FaceDatabase
db = FaceDatabase()
names = db.get_all_names()
print(f'✓ Database loaded with {len(names)} face(s): {names}')
" 2>&1
echo ""

# Test 5: Config test
echo "Test 5: Configuration"
python3 -c "
from src.config.config_loader import ConfigLoader
config = ConfigLoader.load_config('src/config/config.yaml')
print(f'✓ Config loaded')
print(f'  - Camera: {config.camera.device_id}')
print(f'  - Robot enabled: {config.behaviors.enable_robot}')
print(f'  - TTS: {config.tts.use_enhanced_voice}')
" 2>&1
echo ""

echo "✅ All tests passed!"
echo ""
echo "Ready to run:"
echo "  source ./start_dev.sh  - See all available commands"
echo "  python3 main.py        - Run the main application"
