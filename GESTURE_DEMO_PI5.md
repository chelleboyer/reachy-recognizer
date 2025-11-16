# Gesture Voice Demo - Pi5 Optimized Guide

## Quick Start

### Basic Usage (Recommended for Pi5)
```bash
# With display (default Pi5 optimized settings)
python gesture_voice_demo.py --reachy

# Headless mode (SSH/remote - no display window)
python gesture_voice_demo.py --reachy --headless

# Maximum performance mode
python gesture_voice_demo.py --reachy --frame-skip 1 --display-scale 0.3 --no-voice --benchmark
```

## Performance Options

### Frame Skip
Process every Nth frame to reduce CPU load:
```bash
# Process every other frame (2x faster)
python gesture_voice_demo.py --reachy --frame-skip 1

# Process every 3rd frame (3x faster)
python gesture_voice_demo.py --reachy --frame-skip 2
```

### Display Scaling
Reduce display window size for better performance:
```bash
# Half resolution (default, good balance)
python gesture_voice_demo.py --reachy --display-scale 0.5

# Quarter resolution (maximum display performance)
python gesture_voice_demo.py --reachy --display-scale 0.25

# Full resolution (may be slow on Pi5)
python gesture_voice_demo.py --reachy --display-scale 1.0
```

### Headless Mode
Run without display window for remote/SSH operation:
```bash
python gesture_voice_demo.py --reachy --headless
```

### Disable Voice
Skip TTS synthesis for testing/benchmarking:
```bash
python gesture_voice_demo.py --reachy --no-voice
```

### Benchmark Mode
Show detailed performance statistics:
```bash
python gesture_voice_demo.py --reachy --benchmark
```

## Recommended Configurations

### Development Testing (Local Display)
Good balance of performance and visual feedback:
```bash
python gesture_voice_demo.py --reachy --display-scale 0.5
```

### Remote SSH Testing
No display, voice enabled:
```bash
python gesture_voice_demo.py --reachy --headless
```

### Performance Benchmarking
Maximum speed, detailed stats:
```bash
python gesture_voice_demo.py --reachy --frame-skip 1 --display-scale 0.3 --no-voice --benchmark
```

### Production Demo
Full features, optimized for Pi5:
```bash
python gesture_voice_demo.py --reachy
```

## Performance Optimizations Applied

### Configuration Changes
1. **Hand Detection** (`src/config/hand_detection.yaml`):
   - `model_complexity: 0` (lite model for faster processing)
   - `target_fps: 20` (increased from 15)
   - `max_latency_ms: 50` (reduced from 66)

2. **Gesture Recognition** (`src/config/gesture_recognition.yaml`):
   - `smoothing_window: 3` (reduced from 5)
   - `min_detection_frames: 2` (reduced from 3)
   - `gesture_cooldown: 1.0` (reduced from 3.0)
   - `wave.min_confidence: 0.45` (reduced from 0.50)
   - `wave.detection_window: 1.0` (reduced from 1.5)
   - `palm_stop.min_confidence: 0.60` (reduced from 0.65)

### Runtime Optimizations
- Frame skipping support
- Scaled display rendering
- Headless mode for SSH operation
- Benchmark mode with detailed timing stats
- Optional voice synthesis disable

## Expected Performance

### Pi5 with Hailo Hat (Optimized Settings)
- **Capture FPS**: 20-30 FPS
- **Processing FPS**: 15-20 FPS (with frame skip)
- **Detection Latency**: 30-50ms per frame
- **Gesture Recognition**: <500ms from gesture start to confirmation

### Performance Metrics Displayed
When `--benchmark` is enabled:
- Capture FPS: Camera frame rate
- Processing FPS: Actual gesture processing rate
- Avg detect time: Average ms per detection
- Processed/Total frames: Frame skip efficiency
- Hand detector stats: Detection rate, latency

## Troubleshooting

### Too Slow
1. Enable frame skip: `--frame-skip 1` or `--frame-skip 2`
2. Reduce display scale: `--display-scale 0.3`
3. Disable voice: `--no-voice`
4. Use headless mode: `--headless`

### Gestures Not Detected
1. Check lighting conditions
2. Hold gesture for at least 0.5 seconds
3. Keep hand 1-3 meters from camera
4. Ensure hand is not at frame edges
5. Try reducing confidence thresholds in config files

### Voice Too Slow
1. Voice synthesis runs in background thread (non-blocking)
2. First synthesis may be slow (model loading)
3. Caching enabled for repeated phrases
4. Use `--no-voice` to test without TTS

## Gesture Reference

### Thumbs Up 👍
- **Action**: "Thumbs Up!" + Reachy waves
- **Detection**: Thumb extended upward, other fingers closed
- **Hold Time**: 0.5 seconds
- **Cooldown**: 1.0 seconds

### Wave 👋
- **Action**: "Hello there!"
- **Detection**: Horizontal hand oscillation, fingers extended
- **Hold Time**: 1.0 seconds (motion detection window)
- **Cooldown**: 1.0 seconds

### Palm Stop ✋
- **Action**: "Okay, I'll wait"
- **Detection**: All fingers extended, palm facing camera
- **Hold Time**: 0.5 seconds
- **Cooldown**: 1.0 seconds

## Development Notes

### Testing Changes
After modifying config files, no restart needed - configs loaded at startup.

### Adding New Gestures
1. Edit `src/config/gesture_recognition.yaml`
2. Implement detection logic in `src/vision/gesture_recognizer.py`
3. Add command mapping in `src/coordination/gesture_coordinator.py`

### Performance Profiling
Use `--benchmark` flag to get detailed timing information:
- Average detection time per frame
- Frame skip efficiency
- Detection rate percentage

## Files Modified

- `src/config/hand_detection.yaml` - MediaPipe hand detection settings
- `src/config/gesture_recognition.yaml` - Gesture recognition thresholds
- `gesture_voice_demo.py` - Demo script with Pi5 optimizations

## Next Steps

1. Test on actual Pi5 with Reachy
2. Adjust `--frame-skip` and `--display-scale` for your needs
3. Fine-tune confidence thresholds if detection is too sensitive/insensitive
4. Monitor performance with `--benchmark` flag
5. Consider disabling display in production with `--headless`
