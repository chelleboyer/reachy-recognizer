# Reachy Recognizer

**Face Recognition System for Reachy Mini Robot** - A human-aware AI companion that recognizes and greets people using computer vision, running on Raspberry Pi with cross-platform development support.

## 🎯 Project Status: **FACE RECOGNITION WORKING** ✅

**Core System Operational**
- ✅ Face detection, encoding, and recognition pipeline
- ✅ Face database management with add/update/delete
- ✅ Cross-platform support (Windows dev, Linux Pi deployment)
- ✅ Reachy camera integration (direct SDK access)
- ✅ Real-time recognition test script
- ✅ Raspberry Pi setup automation
- 🚧 Full integration with behaviors and voice (in progress)

## Overview

Reachy Recognizer is a face recognition system for the Reachy Mini robot that enables human-aware interactions. The system detects, encodes, and recognizes faces in real-time using OpenCV's SFace model, storing face encodings (not images) for privacy.

### ✨ Current Features

**1. Face Recognition Pipeline**
- Real-time face detection using Haar Cascade (fast on Pi)
- Face encoding with OpenCV SFace model (128-D embeddings)
- Face matching with configurable similarity threshold
- JSON-based face database (embeddings only, no images stored)

**2. Cross-Platform Development**
- **Windows**: Development environment with webcam testing
- **Raspberry Pi**: Production deployment with Reachy camera
- Automatic platform detection and Qt backend configuration
- Git-based deployment workflow

**3. Face Database Management**
- Add faces via camera capture (`add_face.py`)
- Automatic face detection and encoding
- Preview window with visual feedback
- Support for both webcam and Reachy camera

**4. Real-Time Testing**
- Live recognition with confidence scores (`test_face_recognition.py`)
- FPS monitoring and performance stats
- Visual bounding boxes with name labels
- Green for recognized, red for unknown

### 🚀 Key Design Principles
- **Privacy-First**: Store face encodings only, never images
- **Cross-Platform**: Develop on Windows, deploy to Pi
- **Simple Workflow**: Git push/pull between dev and production
- **Modular Architecture**: Clean separation of vision components

## Quick Start

### Prerequisites

- **Python 3.10+** (3.12 recommended)
- **Reachy Mini Robot** (optional - can develop with webcam only)
- **Raspberry Pi 4/5** (for production deployment with Reachy)
- **Camera** (Webcam for development, Reachy camera for deployment)

### Installation

#### Windows (Development)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/chelleboyer/reachy-recognizer.git
   cd reachy-recognizer
   ```

2. **Set up environment:**
   ```powershell
   .\start_dev.ps1
   # This will:
   # - Create/activate virtual environment
   # - Install missing packages
   # - Set environment variables
   ```

3. **Download face recognition model:**
   ```powershell
   mkdir models
   # Download SFace model (see models/README.md for link)
   ```

#### Raspberry Pi (Production)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chelleboyer/reachy-recognizer.git
   cd reachy-recognizer
   ```

2. **Run automated setup:**
   ```bash
   ./setup_pi.sh
   # This will:
   # - Install system dependencies (opencv, numpy, etc.)
   # - Create virtual environment
   # - Install Python packages from requirements-pi.txt
   # - Download face recognition model
   # - Configure system
   ```

   Or manually:
   ```bash
   source ./start_dev.sh
   pip install -r requirements-pi.txt
   ```

### Running the System

#### Step 1: Add Faces to Database

Before testing recognition, add at least one face:

**On Windows (Webcam):**
```powershell
python add_face.py "YourName"
```

**On Raspberry Pi (Reachy Camera):**
```bash
# Make sure daemon is running first
reachy-mini-daemon
# Or use helper script: ./start_daemon.sh

# Then add face
python add_face.py "YourName" --reachy
```

**What it does:**
- Opens camera preview window
- Detects your face automatically
- Press SPACE to capture when face is clearly visible
- Saves encoding to `data/faces.json`
- Press ESC to cancel

#### Step 2: Test Face Recognition

**Real-time recognition test:**

**On Windows (Webcam):**
```powershell
python test_face_recognition.py
```

**On Raspberry Pi (Reachy Camera):**
```bash
python test_face_recognition.py --reachy
```

**What it does:**
- Shows live video with face detection boxes
- Displays recognized names with confidence scores
- Shows FPS and performance stats
- Green boxes for recognized faces
- Red boxes for unknown faces
- Press ESC to exit and see summary

#### Optional: Full Integration Demo

**Note:** Currently requires additional packages not in standard deployment.

```bash
# If you have the full conversation app installed:
python main.py        # Complete system with greetings
python demo.py        # Comprehensive demo
python voice_demo.py  # Voice conversation
```

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Main Application                     │
│                      (main.py)                          │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────▼─────┐         ┌──────▼──────┐
    │ Vision   │         │   Events    │
    │ Pipeline │────────▶│   Manager   │
    └──────────┘         └──────┬──────┘
         │                      │
         │              ┌───────▼────────┐
         │              │  Coordination  │
         │              │  (Greetings)   │
         │              └───────┬────────┘
         │                      │
    ┌────▼──────┐      ┌───────▼────────┐
    │  Camera   │      │   Behaviors    │
    │ Interface │      │    Manager     │
    └───────────┘      └───────┬────────┘
                               │
                       ┌───────▼────────┐
                       │  Voice System  │
                       │ (TTS/STT/LLM)  │
                       └────────────────┘
```

### Core Modules

- **Vision** (`src/vision/`): Face detection, encoding, recognition, database
- **Events** (`src/events/`): Event-driven architecture with debouncing
- **Behaviors** (`src/behaviors/`): Robot gestures, idle movements
- **Voice** (`src/voice/`): OpenAI TTS, greeting selection, conversation
- **Conversation** (`src/conversation/`): Speech-to-text, LLM responses
- **Coordination** (`src/coordination/`): Synchronizes gestures + speech
- **Config** (`src/config/`): YAML configuration management
- **Logging** (`src/logging/`): Structured JSON logging

## Performance

### Face Recognition

- **Detection Speed**: 20-30ms per frame (Haar Cascade on Pi)
- **Encoding Speed**: 30-40ms per face (SFace ONNX on Pi)
- **Recognition Speed**: <1ms per face (cosine similarity)
- **Overall FPS**: 15-20 FPS on Raspberry Pi 5
- **Confidence**: 0.5-0.8 threshold (configurable)

### Platform Performance

| Platform | Detection | Encoding | FPS |
|----------|-----------|----------|-----|
| Desktop PC | 5-10ms | 10-15ms | 40-60 |
| Raspberry Pi 5 | 20-30ms | 30-40ms | 15-20 |
| Raspberry Pi 4 | 60-100ms | 100-150ms | 4-6 |

## Configuration

System parameters in `src/config/config.yaml`:

```yaml
robot:
  enable_robot: false  # Set to true when robot is connected
  port: /dev/ttyACM0
  
camera:
  source: 0           # 0 for webcam, adjust for Pi Camera
  width: 640
  height: 480
  fps: 30
  
face_recognition:
  threshold: 0.5      # Lower = more strict matching
  detection_interval_frames: 5  # Process every Nth frame (performance)
```

Face recognition model configuration in `src/vision/face_encoder.py`:
- Model: SFace (OpenCV Zoo)
- Encoding dimension: 128-D
- Input size: 112x112 pixels
- Distance metric: Cosine similarity

## Project Structure

```
reachy-recognizer/
├── src/                          # Main source code
│   ├── vision/                   # Face recognition pipeline
│   │   ├── face_detector.py     # Haar Cascade face detection
│   │   ├── face_encoder.py      # SFace encoding (128-D)
│   │   ├── face_database.py     # JSON face storage
│   │   ├── face_recognizer.py   # Face matching logic
│   │   └── recognition_pipeline.py  # Complete pipeline
│   ├── config/                   # Configuration management
│   │   ├── config.yaml          # Main config file
│   │   └── config_loader.py     # Config utilities
│   ├── behaviors/                # Robot movement coordination
│   ├── events/                   # Event system
│   ├── voice/                    # TTS/voice systems
│   ├── conversation/             # STT/LLM integration
│   └── logging/                  # Structured logging
├── docs/                         # Documentation
│   ├── RASPBERRY_PI_SETUP.md    # Pi deployment guide
│   ├── PI_QUICK_START.md        # Quick Pi setup
│   ├── CONFIGURATION.md         # Config reference
│   └── PROJECT_STRUCTURE.md     # Architecture docs
├── data/                         # Face database
│   └── faces.json               # Stored face encodings
├── models/                       # Face recognition models
│   └── face_recognition_sface_2021dec.onnx
├── tests/                        # Test suite
├── add_face.py                  # Add faces to database
├── test_face_recognition.py     # Real-time recognition test
├── requirements.txt             # Python dependencies (Windows)
├── requirements-pi.txt          # Python dependencies (Raspberry Pi)
├── setup_pi.sh                  # Automated Pi setup
├── start_dev.sh / .ps1          # Dev environment setup
├── start_daemon.sh / .ps1       # Start Reachy daemon
└── quick_test.sh / .ps1         # Quick system tests
```

## Development

See [docs/SETUP.md](docs/SETUP.md) for detailed development environment setup instructions.

### Key Dependencies

- **opencv-python**: Face detection and image processing (>=4.8.0)
- **numpy**: Array operations for encodings (>=1.24.0)
- **pyyaml**: Configuration file parsing (>=6.0)
- **reachy-mini**: Robot SDK (>=1.0.0rc5) - optional, for robot integration

**Note**: This project uses OpenCV's SFace model, NOT the `face-recognition` library. SFace works better on Raspberry Pi (no dlib/CMake required).

### Development Workflow

#### Windows to Pi Deployment

1. **Develop on Windows:**
   ```powershell
   # Edit code, test with webcam
   python add_face.py "Test"
   python test_face_recognition.py
   
   # Commit and push
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. **Deploy to Pi:**
   ```bash
   # On Raspberry Pi
   cd ~/reachy-recognizer
   git pull
   
   # Test with Reachy
   python add_face.py "Person" --reachy
   python test_face_recognition.py --reachy
   ```

### Helper Scripts

- **`start_dev.sh/.ps1`**: Setup development environment
  - Auto-detects/creates virtual environment
  - Installs missing packages
  - Sets environment variables
  - Platform-aware (uses requirements-pi.txt on Pi)

- **`start_daemon.sh/.ps1`**: Start Reachy daemon
  - Checks for reachy-mini SDK
  - Lists available serial ports
  - Starts daemon with proper config

- **`setup_pi.sh`**: One-command Pi setup
  - Installs system dependencies
  - Creates virtual environment
  - Downloads face recognition model
  - Verifies installation

## Documentation

- **[Raspberry Pi Setup Guide](docs/RASPBERRY_PI_SETUP.md)**: Complete Pi deployment instructions
- **[Quick Start for Pi](PI_QUICK_START.md)**: Condensed Pi setup guide
- **[Configuration Guide](docs/CONFIGURATION.md)**: All configuration options
- **[Project Structure](docs/PROJECT_STRUCTURE.md)**: Architecture and module organization
- **[Model Download Guide](models/README.md)**: How to get face recognition models

## Architecture

### Core Vision Pipeline

```
Camera → Face Detector → Face Encoder → Face Recognizer
                ↓              ↓              ↓
           (Locations)    (128-D vector)   (Name + Confidence)
```

**Components:**

1. **Face Detector** (`face_detector.py`)
   - Haar Cascade for fast detection
   - Returns face bounding boxes (top, right, bottom, left)
   - Optimized for real-time performance on Pi

2. **Face Encoder** (`face_encoder.py`)
   - OpenCV SFace model (ONNX)
   - Generates 128-dimensional embeddings
   - L2-normalized for cosine similarity

3. **Face Database** (`face_database.py`)
   - JSON storage of face encodings
   - Add, update, delete, search operations
   - No images stored (privacy-first)

4. **Face Recognizer** (`face_recognizer.py`)
   - Cosine similarity matching
   - Configurable confidence threshold
   - Returns name + confidence score

5. **Recognition Pipeline** (`recognition_pipeline.py`)
   - Complete end-to-end processing
   - Multi-face handling
   - Event generation for integration

## Contributing

This project follows the BMAD (Business Method Agile Development) workflow for structured development:

1. Stories are created from epic breakdown
2. Each story includes acceptance criteria and tasks
3. Implementation follows strict test-driven development
4. All changes are tracked and documented

## License

See LICENSE files in respective subdirectories.

## Why SFace Instead of face-recognition?

This project uses **OpenCV's SFace model** instead of the popular `face-recognition` library:

### Advantages
- ✅ **No CMake required**: Pure Python dependencies
- ✅ **Raspberry Pi friendly**: No dlib compilation issues
- ✅ **Fast on ARM**: ONNX runtime optimized for ARM64
- ✅ **Small model size**: ~10MB vs 100MB+ for face-recognition models
- ✅ **Compatible format**: 128-D embeddings like face-recognition

### Trade-offs
- Slightly lower accuracy than face-recognition (but adequate for most use cases)
- Requires manual model download (automated in setup scripts)

### For Production
The SFace approach is better for embedded deployment on Raspberry Pi, which is why this project uses it.

## Troubleshooting

### "Qt platform plugin" error
- **Fixed automatically** - scripts detect platform and set correct Qt backend
- Windows: `QT_QPA_PLATFORM=windows`
- Linux: `QT_QPA_PLATFORM=xcb`

### "Reachy SDK not available"
```bash
# On Pi, install reachy-mini
pip install reachy-mini

# Or use requirements file
pip install -r requirements-pi.txt
```

### "Model file not found"
```bash
# Download SFace model
wget -O models/face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

### Camera not working on Pi
```bash
# Check camera
libcamera-hello  # For Pi Camera
v4l2-ctl --list-devices  # For USB camera

# Check permissions
sudo usermod -a -G video $USER
# Logout and login again
```

## Contact

- **Repository**: https://github.com/chelleboyer/reachy-recognizer
- **Base Platform**: Reachy Mini by Pollen Robotics

---

**Current Status**: ✅ **Face Recognition Working!**

- ✅ Face detection, encoding, recognition
- ✅ Cross-platform development workflow
- ✅ Raspberry Pi deployment automation
- ✅ Reachy camera integration
- 🚧 Full robot behavior integration (in progress)