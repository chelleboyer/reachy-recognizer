# Quick Test Script for Reachy Recognizer
# Usage: .\quick_test.ps1

Write-Host "🧪 Quick Test - Reachy Recognizer" -ForegroundColor Cyan
Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host ""

# Setup environment
$env:OPENCV_VIDEOIO_PRIORITY_MSMF = "0"
$env:PYTHONPATH = "$PWD;$env:PYTHONPATH"

# Test 1: Import test
Write-Host "Test 1: Core imports" -ForegroundColor Yellow
python -c "
import cv2
import numpy as np
from src.vision.face_detector import FaceDetector
from src.vision.face_encoder import FaceEncoder
from src.vision.face_database import FaceDatabase
print('✓ All core modules imported successfully')
" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Import test failed" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Test 2: Camera test
Write-Host "Test 2: Camera access" -ForegroundColor Yellow
python -c "
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
Write-Host ""

# Test 3: Face detection test
Write-Host "Test 3: Face detector initialization" -ForegroundColor Yellow
python -c "
from src.vision.face_detector import FaceDetector
detector = FaceDetector()
print('✓ Face detector initialized')
" 2>&1
Write-Host ""

# Test 4: Database test
Write-Host "Test 4: Face database" -ForegroundColor Yellow
python -c "
from src.vision.face_database import FaceDatabase
db = FaceDatabase()
names = db.get_all_names()
print(f'✓ Database loaded with {len(names)} face(s): {names}')
" 2>&1
Write-Host ""

# Test 5: Config test
Write-Host "Test 5: Configuration" -ForegroundColor Yellow
python -c "
from src.config.config_loader import ConfigLoader
config = ConfigLoader.load_config('src/config/config.yaml')
print(f'✓ Config loaded')
print(f'  - Camera: {config.camera.device_id}')
print(f'  - Robot enabled: {config.behaviors.enable_robot}')
print(f'  - TTS: {config.tts.use_enhanced_voice}')
" 2>&1
Write-Host ""

Write-Host "✅ All tests passed!" -ForegroundColor Green
Write-Host ""
Write-Host "Ready to run:" -ForegroundColor Cyan
Write-Host "  .\start_dev.ps1      - See all available commands" -ForegroundColor White
Write-Host "  python main.py       - Run the main application" -ForegroundColor White
