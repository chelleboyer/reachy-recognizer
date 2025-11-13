# Story 4.1: YAML Configuration System

**Epic**: 4 - Configuration & Monitoring  
**Priority**: High  
**Estimated Effort**: 4-6 hours  
**Status**: ✅ Complete

## Overview

Externalize all system configuration to YAML files to enable customization without code changes. Implement type-safe configuration loading with validation, environment variable overrides, and graceful fallback defaults.

## User Story

**As a** developer  
**I want** to externalize all configuration to YAML files  
**So that** the system can be customized without code changes

## Business Value

- **Easy Customization**: Change parameters without editing code
- **Environment Flexibility**: Override settings per deployment
- **Maintainability**: Centralized configuration management
- **Documentation**: Self-documenting configuration structure
- **Validation**: Type-safe config prevents runtime errors

## Acceptance Criteria

1. ✅ config.yaml created with all configurable parameters
2. ✅ Settings include: camera_device_id, recognition_threshold, greeting_phrases, tts_voice, behavior_timing
3. ✅ Config loader module validates YAML structure and types
4. ✅ Default config values provided for all settings
5. ✅ Config can be overridden via environment variables for testing
6. ✅ Invalid config fails fast at startup with clear error message
7. ✅ Documentation includes config reference with all parameters explained

## Prerequisites

- Story 3.4: Unknown & Idle Behaviors ✅
- All core modules implemented ✅

## Implementation Summary

### Configuration Structure

Created comprehensive `src/config/config.yaml` with 9 main sections:
1. **camera** - Device, resolution, FPS settings
2. **face_recognition** - Threshold, tolerance, model selection
3. **events** - Debounce, departed thresholds, event history
4. **behaviors** - Robot enable, timing, idle behavior settings
5. **tts** - Voice backends, OpenAI/pyttsx3 settings, cache config
6. **greetings** - Personality, repetition window, time-of-day
7. **performance** - Latency targets, frame processing
8. **logging** - Levels, file paths, rotation settings
9. **system** - Daemon connection, debug display

### Config Loader Implementation

**File**: `src/config/config_loader.py`

```python
@dataclass
class Config:
    """Type-safe configuration with dataclass hierarchy"""
    camera: CameraConfig
    face_recognition: FaceRecognitionConfig
    events: EventConfig
    behaviors: BehaviorConfig
    tts: TTSConfig
    greetings: GreetingsConfig
    performance: PerformanceConfig
    logging: LoggingConfig
    system: SystemConfig

class ConfigLoader:
    """Load and validate configuration from YAML"""
    def load_config(self, config_path: Path) -> Config:
        # Load YAML
        # Apply environment variable overrides (REACHY_* prefix)
        # Validate structure
        # Return type-safe Config object
```

### Module Integration Pattern

All 8 core modules updated to support optional config loading:

```python
# Pattern used in all modules:
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False

def __init__(self, param: Optional[Type] = None):
    # Load from config if available
    if _CONFIG_AVAILABLE and param is None:
        try:
            config = get_config()
            param = config.section.parameter
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    # Fallback to default
    if param is None:
        param = default_value
```

### Modules Updated

1. ✅ **event_system.py** - Loads debounce_seconds, departed_threshold_seconds, max_event_history
2. ✅ **face_recognizer.py** - Loads recognition threshold and tolerance
3. ✅ **recognition_pipeline.py** - Loads camera, recognition, performance settings
4. ✅ **behavior_module.py** - Loads enable_robot flag
5. ✅ **idle_manager.py** - Loads idle activation threshold and movement interval
6. ✅ **adaptive_tts_manager.py** - Loads TTS cache configuration
7. ✅ **greeting_selector.py** - Loads personality and repetition window
8. ✅ **greeting_coordinator.py** - Loads gesture_speech_delay and use_enhanced_voice

### Environment Variable Overrides

Format: `REACHY_<SECTION>_<KEY>=<VALUE>`

Examples:
```bash
export REACHY_CAMERA_DEVICE_ID=1
export REACHY_FACE_RECOGNITION_THRESHOLD=0.5
export REACHY_TTS_USE_ENHANCED_VOICE=false
export REACHY_LOGGING_LEVEL=DEBUG
```

### Validation Results

Testing confirmed:
- ✅ Config loads successfully from YAML
- ✅ All modules can access config via `get_config()`
- ✅ EventManager loads: debounce=90 frames (3s × 30fps)
- ✅ GreetingSelector loads: personality="warm", window=5
- ✅ IdleManager loads: activation=5.0s, interval=3.0s
- ✅ Graceful fallback to defaults when config unavailable
- ✅ Type validation prevents invalid values

## Documentation Created

1. ✅ **CONFIGURATION.md** - Complete configuration reference (300+ lines)
   - All sections documented with examples
   - Environment variable override guide
   - Usage patterns and best practices
   - Troubleshooting guide

2. ✅ **README.md** - Updated with config system links

3. ✅ **PROJECT_STRUCTURE.md** - Updated with config subsystem details

## Testing

```bash
# Test config loading
python -c "from src.config import get_config; config = get_config(); print(config.camera.fps)"
# Output: 30

# Test module integration
python -c "from src.events.event_system import EventManager; em = EventManager(); print(em.debounce_frames)"
# Output: 90

# Test environment override
export REACHY_CAMERA_FPS=60
python -c "from src.config import get_config; print(get_config().camera.fps)"
# Output: 60
```

## Files Changed

### New Files
- `src/config/config.yaml` (217 lines)
- `src/config/config_loader.py` (460 lines)
- `src/config/__init__.py`
- `CONFIGURATION.md` (320 lines)

### Modified Files
- `src/events/event_system.py` - Added config integration
- `src/vision/face_recognizer.py` - Added config integration
- `src/vision/recognition_pipeline.py` - Added config integration
- `src/behaviors/behavior_module.py` - Added config integration
- `src/behaviors/idle_manager.py` - Added config integration
- `src/voice/adaptive_tts_manager.py` - Added config integration
- `src/voice/greeting_selector.py` - Added config integration
- `src/coordination/greeting_coordinator.py` - Added config integration
- `README.md` - Updated documentation
- `PROJECT_STRUCTURE.md` - Updated with config details

## Lessons Learned

1. **Optional Pattern Works Well**: Using Optional parameters with config loading allows backwards compatibility
2. **Try/Except for Imports**: Graceful config import failure enables modules to work standalone
3. **Dataclasses for Validation**: Type-safe config structure catches errors early
4. **Environment Overrides Essential**: Critical for testing and deployment flexibility
5. **Document Everything**: Comprehensive config documentation reduces support burden

## Future Enhancements

- Config schema validation with JSON Schema
- Config hot-reload without restart
- Per-user config overrides
- Config migration tools for version updates
- GUI config editor

## Story Complete

**Completion Date**: October 24, 2025  
**Actual Effort**: ~6 hours  
**Status**: ✅ All acceptance criteria met and validated
