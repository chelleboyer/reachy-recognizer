# 📁 Project Structure

## Overview

The Reachy Recognizer codebase is organized into modular subsystems under `src/`:

```
c:\code\reachy-mini-dev\
├── src/
│   ├── __init__.py              # Package initialization
│   ├── vision/                  # Epic 2: Vision & Recognition
│   │   ├── __init__.py
│   │   ├── camera_interface.py  # Story 1.3: Camera capture
│   │   ├── face_detector.py     # Story 2.1: Face detection
│   │   ├── face_encoder.py      # Story 2.2: Face encoding
│   │   ├── face_database.py     # Story 2.2: Database management
│   │   ├── face_recognizer.py   # Story 2.3: Recognition engine
│   │   └── recognition_pipeline.py  # Story 2.4: Real-time pipeline
│   │
│   ├── events/                  # Epic 2: Event System
│   │   ├── __init__.py
│   │   └── event_system.py      # Story 2.5: Recognition events
│   │
│   ├── behaviors/               # Epic 3: Behavior Engine
│   │   ├── __init__.py
│   │   ├── behavior_module.py   # Story 3.1: Greeting behaviors
│   │   └── idle_manager.py      # Story 3.4: Idle behaviors
│   │
│   ├── voice/                   # Epic 3: Voice & Speech
│   │   ├── __init__.py
│   │   ├── tts_module.py        # Story 3.2: Text-to-speech
│   │   ├── greeting_selector.py # Story 3.4: Greeting templates
│   │   └── adaptive_tts_manager.py  # Story 3.4: OpenAI TTS
│   │
│   ├── coordination/            # Epic 3: Coordination
│   │   ├── __init__.py
│   │   └── greeting_coordinator.py  # Story 3.3: Behavior coordination
│   │
│   └── config/                  # Epic 4: Configuration
│       ├── __init__.py
│       ├── config_loader.py     # Story 4.1: Config management
│       └── config.yaml          # Story 4.1: System configuration
│
├── tests/                       # Test suite
│   ├── test_story_1_1_setup.py
│   ├── test_story_1_2_connection.py
│   └── ...
│
├── docs/                        # Documentation
│   ├── prd.md
│   ├── epics.md
│   ├── bmm-workflow-status.md
│   └── stories/
│
├── models/                      # ML models
│   └── face_recognition_sface_2021dec.onnx
│
├── main.py                      # Main entry point
├── pyproject.toml               # Project dependencies
└── README.md                    # Project documentation
```

## Subsystem Responsibilities

### 🔍 Vision (`src/vision/`)
Handles all computer vision tasks:
- Camera input capture
- Face detection in frames
- Face encoding/embedding
- Face recognition and matching
- Real-time processing pipeline

**Key Classes:** `CameraInterface`, `FaceDetector`, `FaceRecognizer`, `RecognitionPipeline`

### 📡 Events (`src/events/`)
Manages recognition state changes:
- Event generation (RECOGNIZED, UNKNOWN, DEPARTED, NO_FACES)
- Debouncing and state tracking
- Event callbacks for subsystems

**Key Classes:** `EventManager`, `RecognitionEvent`, `EventType`

### 🤖 Behaviors (`src/behaviors/`)
Controls robot physical actions:
- Greeting gestures (wave, tilt)
- Idle movements (drift, look-around)
- Behavior sequencing and interruption
- Reachy SDK integration

**Key Classes:** `BehaviorManager`, `IdleManager`, `Behavior`

### 🗣️ Voice (`src/voice/`)
Generates speech and greetings:
- Text-to-speech (OpenAI TTS, pyttsx3)
- Greeting template selection
- Voice caching and optimization
- Multi-backend failover

**Key Classes:** `AdaptiveTTSManager`, `GreetingSelector`, `TTSManager`

### 🎯 Coordination (`src/coordination/`)
Orchestrates high-level interactions:
- Coordinates vision → events → behaviors → voice
- Session management
- Timing and synchronization

**Key Classes:** `GreetingCoordinator`

### ⚙️ Config (`src/config/`)
Centralized configuration system (Story 4.1):
- YAML-based settings management
- Environment variable overrides
- Type-safe config access with dataclasses
- Graceful fallbacks to defaults
- Validation on load

**Files:**
- `config.yaml` - Complete system configuration (200+ lines)
- `config_loader.py` - Config loading, validation, singleton access
- `__init__.py` - Exports `get_config()` for easy access

**All Modules Support Config:**
All 8 core modules automatically load from config with fallback defaults:
- `EventManager` - debounce, departed thresholds
- `FaceRecognizer` - recognition threshold
- `RecognitionPipeline` - camera, performance settings
- `BehaviorManager` - enable_robot flag
- `IdleManager` - activation threshold, intervals
- `AdaptiveTTSManager` - cache settings
- `GreetingSelector` - personality, repetition window
- `GreetingCoordinator` - timing, voice settings

## Import Patterns

### Within Same Subsystem (Relative Imports)
```python
# In src/vision/recognition_pipeline.py
from .camera_interface import CameraInterface
from .face_recognizer import FaceRecognizer
```

### Across Subsystems (Relative Imports)
```python
# In src/coordination/greeting_coordinator.py
from ..events.event_system import EventManager
from ..behaviors.behavior_module import BehaviorManager
from ..voice.adaptive_tts_manager import AdaptiveTTSManager
```

### From Main Application (Absolute Imports)
```python
# In main.py
from src.config import load_config
from src.vision import RecognitionPipeline
from src.coordination import GreetingCoordinator
```

## Running the System

### Main Application
```bash
python main.py
```

### With Custom Config
```bash
# Set config path via environment variable
export REACHY_CONFIG_PATH=/path/to/config.yaml
python main.py
```

### Debug Mode
```bash
# Enable visual display
export REACHY_SYSTEM_DEBUG_DISPLAY=true
python main.py
```

## Testing

Tests are organized by story:
```bash
# Run all tests
pytest tests/

# Run specific story tests
pytest tests/test_story_2_1_face_detection.py
```

## Configuration

All system parameters are centralized in `src/config/config.yaml` (Story 4.1 ✅):

**Configuration Sections:**
- `camera` - Device, resolution, FPS
- `face_recognition` - Threshold, tolerance, model selection
- `events` - Debounce, departed thresholds, history
- `behaviors` - Robot enable, timing, idle settings
- `tts` - Voice backends, OpenAI settings, cache
- `greetings` - Personality, repetition window, time-of-day
- `performance` - Latency targets, frame processing
- `logging` - Levels, file paths, rotation
- `system` - Daemon connection, debug display

**Environment Variable Overrides:**
```bash
# Format: REACHY_<SECTION>_<KEY>=<VALUE>
export REACHY_CAMERA_DEVICE_ID=1
export REACHY_FACE_RECOGNITION_THRESHOLD=0.5
export REACHY_TTS_USE_ENHANCED_VOICE=false
export REACHY_LOGGING_LEVEL=DEBUG
```

**Usage in Code:**
```python
from src.config import get_config

# All modules auto-load config with graceful fallback
config = get_config()
fps = config.camera.fps
threshold = config.face_recognition.threshold
```

See [CONFIGURATION.md](./CONFIGURATION.md) for complete reference.

## Development Workflow

1. **Make changes** in appropriate subsystem (`src/vision/`, `src/behaviors/`, etc.)
2. **Update tests** in `tests/`
3. **Run tests** to verify changes
4. **Update config** if adding new parameters
5. **Test integration** with `main.py`

## Epic Progress

- ✅ Epic 1: Foundation (Stories 1.1-1.4) - 4/4 complete
- ✅ Epic 2: Vision Pipeline (Stories 2.1-2.5) - 5/5 complete
- ✅ Epic 3: Behavior Engine (Stories 3.1-3.4) - 4/4 complete
- 🔄 Epic 4: Configuration & Monitoring - 2/3 complete
  - ✅ Story 4.1: YAML Configuration System
  - ✅ Story 4.2: Performance Logging & Analytics
  - ⏳ Story 4.3: End-to-End Demo & Documentation

**Overall Progress: 15/16 stories (94%)**

## File Migration Status

All core modules migrated to modular structure with config integration:
- ✅ Vision modules → `src/vision/` (6 modules)
- ✅ Behavior modules → `src/behaviors/` (2 modules)
- ✅ Voice modules → `src/voice/` (3 modules)
- ✅ Event system → `src/events/` (1 module)
- ✅ Coordination → `src/coordination/` (1 module)
- ✅ Configuration → `src/config/` (config.yaml + loader)
- ✅ Logging infrastructure → `src/logging/` (JSON formatter, metrics)
- ✅ Package initialization files created (`__init__.py`)
- ✅ Imports updated to relative paths
- ✅ Main entry point updated
- ✅ All 8 core modules load config with graceful fallback
- ✅ Configuration validated and tested
- ✅ Performance logging with metrics tracking operational

## Next Steps

- ⏳ Story 4.3: End-to-End Demo & Documentation
