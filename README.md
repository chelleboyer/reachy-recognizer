# Reachy Mini Store Assistant

**Computer Vision + AI for Store Inventory Management** - An intelligent store assistant system that uses the Reachy Mini robot with edge AI (Raspberry Pi 5 + Hailo-8L) for privacy-first inventory analysis and staff interaction.

## 🎯 Project Status: **PLANNING COMPLETE** ✅

**PRD & Architecture Ready** - Ready for Week 1 implementation
- ✅ Complete PRD with Top 3 quick-win features
- ✅ Brainstorming session results (26+ features, SCAMPER techniques)
- ✅ Hailo PoC documentation and test scripts
- ✅ Demo project archived
- ⏳ Week 1: Multi-Angle Capture System (NEXT)
- ⏳ Weeks 2-3: Uniform Recognition + Gesture Controls
- ⏳ Week 4: Integration & Store Pilot

## Overview

Reachy Mini Store Assistant is an edge AI system for convenience stores that prioritizes privacy while providing intelligent inventory management and staff interaction capabilities.

### 🎭 Core Features (MVP - 4 weeks)

**1. Multi-Angle Capture System** (Week 1)
- Robot head automatically captures 3-5 angles of cigarette shelves
- Eliminates glare and occlusion on shiny packaging
- Frame quality assessment and best-frame selection
- 90%+ successful pack identification

**2. Uniform Recognition System** (Weeks 2-3)
- Privacy-friendly staff vs customer identification
- Color-pattern detection (no face recognition)
- 85%+ classification accuracy
- No PII storage - embeddings only

**3. Gesture Control System** (Weeks 2-3)
- Fast interaction: 👍 Approve, 👋 Skip, ✋ Stop
- MediaPipe hand detection on Raspberry Pi 5
- <1 second response time
- 95%+ gesture recognition rate

### 🚀 Key Principles
- **Privacy-First**: Embeddings only, no face recognition or photo storage
- **Quick Wins**: 4-week MVP timeline with practical features
- **Edge AI**: Raspberry Pi 5 + Hailo-8L AI HAT (26 TOPS)
- **Store Ready**: Convenience store deployment for tobacco inventory

## Quick Start

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Reachy Mini** (physical robot, tethered version)
- **Raspberry Pi 5** (8GB RAM recommended)
- **Hailo-8L AI HAT** (26 TOPS AI accelerator)
- **Camera** (Reachy built-in camera)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chelleboyer/reachy-recognizer.git
   cd reachy-mini-dev
   ```

2. **Set up Raspberry Pi 5 + Hailo:**
   Follow the complete setup guide:
   ```bash
   # See hailo_poc/ for detailed instructions
   cd hailo_poc
   cat QUICK_START.md
   ```

3. **Install Hailo software:**
   ```bash
   # On Raspberry Pi 5
   git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
   cd hailo-rpi5-examples
   ./install.sh
   ```

4. **Install Python dependencies:**
   ```bash
   # Core packages
   pip install opencv-python mediapipe scikit-image pyyaml
   
   # Reachy SDK
   pip install reachy-mini
   
   # Hailo integration
   pip install hailo_platform
   ```

5. **Download YOLO model:**
   ```bash
   # Get YOLOv8 nano model for Hailo (.hef format)
   # See hailo_poc/MANUAL_MODEL_DOWNLOAD.md for instructions
   ```

### Running the System

#### Option 1: Full Face Recognition & Greeting System (Recommended)

**Complete system with face recognition, greetings, and coordinated behaviors:**

1. **Start the Reachy simulator** (optional - skip if no robot):
   ```bash
   # Windows PowerShell
   uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim
   
   # macOS/Linux
   uvx --from 'reachy-mini[mujoco]' reachy-mini-daemon --sim
   ```
   
   Or disable robot movements in `src/config/config.yaml`:
   ```yaml
   behaviors:
     enable_robot: false
   ```

2. **Run the main system:**
   ```bash
   python main.py
   ```

**What it does:**
- Initializes all subsystems (vision, events, behaviors, voice, coordination)
- Loads face database from `data/faces.json`
- Continuously monitors camera for faces
- Greets recognized people by name with gestures and Shimmer voice
- Displays camera feed with detection boxes and confidence scores
- Logs all events and performance metrics

**Controls:**
- Press `Ctrl+C` to stop
- Press `q` in the camera window to exit

#### Option 2: Voice Conversation Demo

**Interactive voice conversation with continuous movements:**

1. **Start the Reachy simulator** (if using robot movements)

2. **Run the voice demo:**
   ```bash
   python voice_demo.py
   ```
   
   Enter your name when prompted, then start talking!

**Features:**
- Speech-to-text using Whisper API
- Conversational AI with GPT-4o-mini
- Text-to-speech with Shimmer voice (1.15x speed)
- Continuous head movements and tilts
- Natural idle antenna drifts (every 0.8s)

**Exit:** Say "goodbye" or "bye"

#### Option 3: Comprehensive System Demo

**Full demonstration with statistics and benchmarking:**

```bash
python demo.py --duration 60
```

**Options:**
- `--duration N`: Run for N seconds (default: 60)
- `--no-display`: Run without camera window
- `--benchmark`: Include detailed performance metrics

#### Option 4: Add More Faces to Database

**Capture and store faces for recognition:**

```bash
python add_face.py
```

**Process:**
- Camera opens with live preview
- Face is automatically detected
- Enter person's name when prompted
- Face encoding is saved to `data/faces.json`
- Visual feedback during capture

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

## Performance Metrics

- **Face Recognition**: 95-98% confidence on known faces
- **Recognition Speed**: 30 FPS with every-frame processing
- **Greeting Coordination**: ~4.9s total (3ms initial response)
- **Voice Response Time**: <1s for conversation (optimized)
- **TTS Generation**: ~1.3-2.0s (OpenAI Shimmer voice)
- **STT Transcription**: ~0.7-2.6s (Whisper API)
- **LLM Response**: ~1s (GPT-4o-mini, 35 tokens)

## Configuration

All system parameters are configurable via `src/config/config.yaml`:

```yaml
camera:
  device_id: 0
  fps: 30
  
face_recognition:
  threshold: 0.6
  
events:
  debounce_seconds: 3.0
  departed_threshold_seconds: 3.0
  
behaviors:
  enable_robot: true
  gesture_speech_delay: 0.3
  
tts:
  use_enhanced_voice: true
  default_voice: "shimmer"
  
greetings:
  personality: "warm"
  repetition_window: 5
```

See `docs/CONFIGURATION.md` for full details.

## Project Structure

```
reachy-mini-dev/
├── src/                      # Main source code (modular architecture)
│   ├── vision/              # Camera, detection, encoding, recognition
│   ├── events/              # Event system with debouncing
│   ├── behaviors/           # Robot movements and idle behaviors
│   ├── voice/               # TTS, greeting selection, adaptive voice
│   ├── conversation/        # Speech-to-text and LLM conversation
│   ├── coordination/        # Greeting coordinator
│   ├── config/              # Configuration loader and settings
│   └── logging/             # Structured JSON logging
├── docs/                     # Documentation and project management
│   ├── prd.md               # Product Requirements Document
│   ├── epics.md             # Epic breakdown with 16 stories
│   ├── stories/             # Individual story implementation files
│   ├── CONFIGURATION.md     # Configuration guide
│   ├── PROJECT_STRUCTURE.md # Architecture documentation
│   └── voice-response-design.md # Voice system design
├── tests/                    # Test suite (all stories validated)
├── archive/                  # Archived demo and test files
├── data/                     # Face database (faces.json)
├── logs/                     # Performance and event logs
├── models/                   # Face recognition models
├── scenes/                   # MuJoCo simulation scenes
├── main.py                  # Main application entry point
├── voice_demo.py            # Voice conversation demo
├── demo.py                  # Comprehensive system demo
├── add_face.py              # Face database management utility
└── pyproject.toml          # Dependency configuration
```

## Development

See [docs/SETUP.md](docs/SETUP.md) for detailed development environment setup instructions.

### Key Dependencies

- **reachy-mini**: Robot SDK with MuJoCo simulation support (>=1.0.0rc5)
- **opencv-python**: Computer vision and camera input (>=4.8.0)
- **face-recognition**: Face detection and recognition (>=1.3.0)
- **openai**: OpenAI API for TTS, STT, and LLM (>=1.0.0)
- **pygame**: Audio playback for MP3 files (>=2.5.0)
- **pyaudio**: Microphone input for voice conversations
- **pyyaml**: Configuration file parsing (>=6.0)
- **python-dotenv**: Environment variable management

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific story tests
pytest tests/test_story_1_1_setup.py
pytest tests/test_story_4_3_integration.py
```

## Documentation

### New Store Deployment Project
- **[Product Requirements](docs/prd.md)**: Complete PRD for store assistant with Top 3 features
- **[Brainstorming Results](docs/brainstorming-session-results-2025-11-02.md)**: 26+ features from SCAMPER session
- **[Workflow Status](docs/bmm-workflow-status.md)**: Current project status and next steps
- **[Hailo PoC Status](hailo_poc/STATUS.md)**: Hardware setup and testing status
- **[Setup Guide](docs/SETUP.md)**: Development environment setup

### Demo Project Archive
- **[Demo Archive](docs/demo-archive/)**: Original face recognition demo project documentation
- **[Demo PRD](docs/demo-archive/prd.md)**: Original Reachy Recognizer PRD
- **[Demo Epics](docs/demo-archive/epics.md)**: 16 stories across 4 epics (completed demo)

## Architecture

The system is organized into 8 main subsystems under `src/`:

1. **Vision System** (`src/vision/`): Camera interface, face detection, encoding, recognition pipeline
2. **Event System** (`src/events/`): Recognition event management with debouncing
3. **Behavior System** (`src/behaviors/`): Robot movement coordination and idle behaviors  
4. **Voice System** (`src/voice/`): Multi-backend TTS, greeting selection, adaptive voice (OpenAI Shimmer)
5. **Conversation System** (`src/conversation/`): Speech-to-text (Whisper) and LLM conversation (GPT-4o-mini)
6. **Coordination** (`src/coordination/`): Greeting coordinator integrating all subsystems
7. **Configuration** (`src/config/`): YAML-based centralized settings management
8. **Logging** (`src/logging/`): Structured JSON logging with performance metrics

## Contributing

This project follows the BMAD (Business Method Agile Development) workflow for structured development:

1. Stories are created from epic breakdown
2. Each story includes acceptance criteria and tasks
3. Implementation follows strict test-driven development
4. All changes are tracked and documented

## License

See LICENSE files in respective subdirectories.

## Project Pivot

This project evolved from **Reachy Recognizer** (face recognition demo) to **Reachy Mini Store Assistant** (store deployment system):

### What Changed
- **From:** Simulation-based face recognition demo
- **To:** Privacy-first store inventory and staff interaction system
- **Why:** Real-world deployment needs, privacy requirements, quick-win focus

### What Was Preserved
- Core infrastructure (event system, behavior coordination, configuration)
- Reachy SDK integration
- Testing patterns
- Development workflow

### Demo Project Status
The original Reachy Recognizer demo (face recognition system) is **100% complete** with all 16 stories implemented. Documentation archived in `docs/demo-archive/`.

## Contact

- **Repository**: https://github.com/chelleboyer/reachy-recognizer
- **Base Platform**: Reachy Mini by Pollen Robotics

---

**Current Project Status**: ✅ **PLANNING COMPLETE** - Ready for Week 1 implementation!

- ✅ **Phase 0: Discovery & Planning**
  - Brainstorming session (SCAMPER) - 26+ features
  - Feature prioritization
  - PRD creation with 4-week timeline
  - Hailo PoC documentation
  - Demo project archived

- ⏳ **Epic 1: Multi-Angle Capture System** (Week 1 - NEXT)
  - Story 1.1: Basic Multi-Angle Head Movement (5 pts)
  - Story 1.2: Frame Quality Assessment (8 pts)
  - Story 1.3: Best Frame Selection & OCR (8 pts)

- ⏳ **Epic 2: Uniform Recognition System** (Weeks 2-3)
  - Story 2.1: Person Detection with Torso ROI (5 pts)
  - Story 2.2: Color-Pattern Feature Extraction (5 pts)
  - Story 2.3: Staff vs Customer Classification (13 pts)

- ⏳ **Epic 3: Gesture Control System** (Weeks 2-3)
  - Story 3.1: MediaPipe Hand Detection Setup (3 pts)
  - Story 3.2: Three-Gesture Recognition (13 pts)
  - Story 3.3: Gesture-to-Command Mapping (5 pts)
  - Story 3.4: Visual Feedback & UI Integration (5 pts)

- ⏳ **Epic 4: Integration & Testing** (Week 4)
  - Story 4.1: End-to-End Integration Testing
  - Story 4.2: Store Pilot Deployment Prep
  - Story 4.3: Performance Optimization & Documentation

**Next Milestone**: Week 1 - Multi-Angle Capture working! 🚀