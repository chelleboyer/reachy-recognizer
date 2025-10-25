# Configuration Guide

Reachy Recognizer uses a centralized YAML configuration system that allows you to customize all aspects of the system without modifying code.

## Configuration File Location

The main configuration file is located at:
```
src/config/config.yaml
```

## Configuration Sections

### Camera Settings

```yaml
camera:
  device_id: 0          # Camera device index (0 = default webcam)
  width: 1280           # Frame width in pixels
  height: 720           # Frame height in pixels
  fps: 30               # Target frames per second
  auto_exposure: true   # Enable auto-exposure
```

### Face Recognition Settings

```yaml
face_recognition:
  # Recognition threshold (0.0-1.0)
  # Lower = stricter matching, Higher = more lenient
  threshold: 0.6
  
  # Tolerance for face comparison (lower = stricter)
  tolerance: 0.6
  
  # Database path
  database_path: "faces_database.json"
  
  # Model selection
  model: "sface"  # Options: "hog", "cnn", "sface"
```

### Event System Settings

```yaml
events:
  # Debounce: seconds a person must be visible before triggering event
  debounce_seconds: 3.0
  
  # Departed threshold: seconds of absence before DEPARTED event
  departed_threshold_seconds: 3.0
  
  # Maximum event history to keep in memory
  max_event_history: 100
```

### Behavior Settings

```yaml
behaviors:
  # Enable real robot control (false = simulation mode)
  enable_robot: true
  
  # Timing settings
  timing:
    gesture_duration: 2.0           # Duration of greeting gesture (seconds)
    look_at_duration: 1.5           # Duration to look at person (seconds)
    idle_drift_duration: 3.0        # Duration of idle drift movement (seconds)
    neutral_return_duration: 0.5    # Time to return to neutral (seconds)
  
  # Delay between gesture start and speech start (seconds)
  gesture_speech_delay: 0.3
  
  # Idle behavior settings
  idle:
    activation_threshold: 5.0   # Seconds with no faces before activating idle
    movement_interval: 3.0      # Seconds between idle movements
    roll_range: [-5, 5]         # Idle roll angle range (degrees)
    pitch_range: [-5, 5]        # Idle pitch angle range (degrees)
    yaw_range: [-10, 10]        # Idle yaw angle range (degrees)
```

### Text-to-Speech Settings

```yaml
tts:
  # Use enhanced voice system with OpenAI TTS
  use_enhanced_voice: true
  
  # Voice backend priority (tried in order)
  backend_priority:
    - "openai"
    - "pyttsx3"
  
  # OpenAI TTS settings
  openai:
    model: "tts-1"    # Model: "tts-1" (fast) or "tts-1-hd" (quality)
    voice: "nova"     # Voice: alloy, echo, fable, onyx, nova, shimmer
    speed: 1.0        # Speech speed (0.25 to 4.0)
  
  # Pyttsx3 (local TTS) settings
  pyttsx3:
    rate: 150         # Words per minute
    volume: 0.9       # Volume (0.0 to 1.0)
    voice_index: 1    # Voice selection (system dependent)
  
  # Greeting cache settings
  cache:
    enabled: true     # Enable caching of generated speech
    max_size: 50      # Maximum cached greetings
    ttl_seconds: 3600 # Cache entry lifetime (1 hour)
```

### Greeting Template Settings

```yaml
greetings:
  # Greeting personality: 'warm', 'professional', 'casual', 'enthusiastic'
  personality: "warm"
  
  # Non-repetition window (remember last N greetings to avoid duplicates)
  repetition_window: 5
  
  # Time-based greeting adjustments
  time_of_day:
    morning_start: 6     # Hour (24h format)
    afternoon_start: 12
    evening_start: 18
    night_start: 22
```

### Performance Settings

```yaml
performance:
  # Target response latency (milliseconds)
  target_latency_ms: 400
  
  # Performance monitoring interval (seconds)
  stats_interval: 60
  
  # Frame processing timeout (seconds)
  frame_timeout: 5.0
  
  # Process every Nth frame (1 = every frame, 2 = every other frame)
  process_every_n_frames: 1
```

### Logging Settings

```yaml
logging:
  # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # Log file path (null = console only)
  file_path: "logs/reachy_recognizer.log"
  
  # Log rotation settings
  max_bytes: 10485760  # 10 MB
  backup_count: 5
  
  # Log format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Enable structured JSON logging
  json_format: false
```

### System Settings

```yaml
system:
  # Reachy daemon connection
  reachy_host: "localhost"
  reachy_port: 50055
  
  # Graceful shutdown timeout (seconds)
  shutdown_timeout: 5.0
  
  # Enable debug visualization (show camera feed with overlays)
  debug_display: false
```

## Environment Variable Overrides

Any configuration value can be overridden using environment variables with the format:
```
REACHY_<SECTION>_<KEY>=<VALUE>
```

### Examples

```bash
# Override camera device
export REACHY_CAMERA_DEVICE_ID=1

# Change recognition threshold
export REACHY_FACE_RECOGNITION_THRESHOLD=0.5

# Disable enhanced voice
export REACHY_TTS_USE_ENHANCED_VOICE=false

# Change log level
export REACHY_LOGGING_LEVEL=DEBUG
```

## Using Configuration in Code

The configuration system provides automatic loading with graceful fallbacks:

```python
from src.config import get_config

# Load configuration
config = get_config()

# Access settings
fps = config.camera.fps
threshold = config.face_recognition.threshold
personality = config.greetings.personality
```

### Optional Configuration Loading

All modules support optional configuration loading with defaults:

```python
from src.events.event_system import EventManager

# Will load from config if available, otherwise use defaults
event_manager = EventManager()

# Or override with explicit parameters
event_manager = EventManager(debounce_seconds=5.0)
```

## Configuration Best Practices

1. **Start with defaults**: The provided `config.yaml` has sensible defaults for most use cases

2. **Adjust recognition threshold**: If getting false positives, lower the threshold. If missing valid matches, raise it.

3. **Tune event debouncing**: Increase `debounce_seconds` in noisy environments to prevent false triggers

4. **Optimize performance**: Adjust `process_every_n_frames` if frame rate is too low (2 = process every other frame)

5. **Use environment variables for testing**: Override settings temporarily without modifying files

6. **Enable debug display**: Set `system.debug_display: true` to see detection overlays during development

## Troubleshooting

### Configuration not loading
- Check that `src/config/config.yaml` exists
- Verify YAML syntax is valid (use YAML validator)
- Check console for config loading errors

### Settings not taking effect
- Verify you're modifying the correct config section
- Check for environment variable overrides
- Restart the application after config changes

### OpenAI TTS not working
- Verify `OPENAI_API_KEY` environment variable is set
- Check `tts.use_enhanced_voice` is `true`
- System will automatically fall back to pyttsx3 if OpenAI fails

### Robot not moving
- Check `behaviors.enable_robot` setting (true = real robot, false = simulation)
- Verify Reachy daemon is running
- Check connection settings in `system` section

## Configuration Schema

The configuration is validated on load using Python dataclasses. Invalid configurations will fail fast with descriptive error messages indicating:
- Missing required fields
- Invalid value types
- Out-of-range values

See `src/config/config_loader.py` for the complete schema definition.
