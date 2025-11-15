# Epic 3: Gesture Control System - Implementation Plan

**Epic:** Gesture Control System  
**Story Points:** 26 points (Stories 3.1-3.4)  
**Duration:** Weeks 2-3 (Development Phase)  
**Status:** Planning Complete  
**Version:** 1.0  
**Date:** November 15, 2025

---

## Executive Summary

Epic 3 implements gesture-based control for Reachy Mini using MediaPipe Hands, enabling store managers to interact with the robot through three core gestures: thumbs up (approve), wave (skip), and palm/stop (pause). This provides faster, more natural interaction than voice commands, especially when managers' hands are busy with inventory tasks.

### Key Requirements
- **Performance:** <1 second gesture-to-action response time
- **Recognition Rate:** 95%+ gesture accuracy
- **False Positives:** <5% accidental trigger rate
- **FPS Target:** 10+ FPS hand detection on Raspberry Pi 5
- **User Experience:** Visual feedback within 0.2 seconds

### Integration Points
- **Event System:** Extends `EventManager` with new `GESTURE_DETECTED` event type
- **Coordination:** Integrates with `GreetingCoordinator` pattern for command dispatch
- **Behaviors:** Triggers robot actions via existing `BehaviorManager`
- **Configuration:** Follows existing YAML config pattern (`config.yaml`)

---

## Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Epic 3: Gesture Control                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Story 3.1: MediaPipe Hand Detection Setup             │ │
│  │  • HandDetector class                                  │ │
│  │  • MediaPipe Hands integration                         │ │
│  │  • 21 landmarks per hand (10+ FPS)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Story 3.2: Three-Gesture Recognition                  │ │
│  │  • GestureRecognizer class                             │ │
│  │  • Thumbs up / Wave / Palm detection                   │ │
│  │  • Hold time validation (0.5s)                         │ │
│  │  • Distance filtering (1-3m)                           │ │
│  │  • False positive prevention (<5%)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Story 3.3: Gesture-to-Command Mapping                 │ │
│  │  • GestureCoordinator class                            │ │
│  │  • Command dispatch (Approve/Skip/Pause)               │ │
│  │  • Integration with event system                       │ │
│  │  • Optional audio confirmation                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           │                                   │
│                           ▼                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Story 3.4: Visual Feedback & UI Integration           │ │
│  │  • FeedbackManager class                               │ │
│  │  • On-screen icons (👍👋✋)                            │ │
│  │  • Fade-in/pulse/fade-out animation (1s)               │ │
│  │  • <0.2s display latency                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
        ┌────────────────────────────────────┐
        │   Existing Systems Integration      │
        ├────────────────────────────────────┤
        │ • EventManager (GESTURE_DETECTED)  │
        │ • BehaviorManager (robot actions)  │
        │ • Configuration (gesture.yaml)     │
        └────────────────────────────────────┘
```

### Data Flow

```
Camera Frame
    │
    ▼
HandDetector (MediaPipe)
    │ (21 landmarks per hand)
    ▼
GestureRecognizer
    │ (classify gesture type)
    ▼
Validation (hold time, distance, confidence)
    │
    ▼
GestureCoordinator
    │ (map to command)
    ▼
┌───────────────────────┐
│ EventManager          │ ──► GestureEvent → Callbacks
│ (GESTURE_DETECTED)    │
└───────────────────────┘
    │
    ├──► FeedbackManager (visual icon, <0.2s)
    │
    ├──► BehaviorManager (optional robot reaction)
    │
    └──► Application Logic (approve/skip/pause action)
```

---

## Story Breakdown

### Story 3.1: MediaPipe Hand Detection Setup (3 points)

**Goal:** Integrate MediaPipe Hands on Raspberry Pi 5 with real-time hand tracking.

#### Acceptance Criteria
- [ ] MediaPipe Hands installed and running on Pi5
- [ ] Hand detection at 10+ FPS
- [ ] 21 landmarks tracked per hand
- [ ] Left/right hand differentiated
- [ ] Configuration for model complexity (lite/full)

#### Implementation Details

**File:** `src/vision/hand_detector.py` (200-250 lines)

**Key Components:**
1. **HandLandmarks dataclass**
   - `hand_id: str` (unique identifier)
   - `handedness: str` ("Left" or "Right")
   - `landmarks: List[Tuple[float, float, float]]` (21 landmarks, normalized x/y/z)
   - `world_landmarks: Optional[List[Tuple[float, float, float]]]` (3D world coords)
   - `confidence: float` (detection confidence 0-1)
   - `timestamp: float` (detection time)
   - `to_dict()` method

2. **HandDetector class**
   - `__init__(model_complexity, min_detection_confidence, min_tracking_confidence, max_num_hands)`
   - `_load_config()` - load from YAML
   - `_initialize_mediapipe()` - create MediaPipe Hands solution
   - `detect(frame)` - detect hands in frame, return List[HandLandmarks]
   - `get_statistics()` - FPS, detection count, avg landmarks
   - `reset_statistics()` - clear stats
   - `cleanup()` - release MediaPipe resources

**Dependencies:**
- `mediapipe` (pip install mediapipe)
- `numpy` (array operations)
- `opencv-python` (frame processing)
- `yaml` (configuration)

**Configuration:** `src/config/hand_detection.yaml`
```yaml
hand_detection:
  model_complexity: 0  # 0 (lite, fast) or 1 (full, accurate)
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
  max_num_hands: 2
  performance:
    target_fps: 10
    max_latency_ms: 100
```

**Testing:** `tests/test_story_3_1_hand_detection.py` (15 tests)
- Unit tests: config loading, MediaPipe initialization, landmark extraction
- Integration tests: real frame processing, FPS validation, left/right differentiation
- Performance tests: 10+ FPS on Pi5 (mocked for CI)

---

### Story 3.2: Three-Gesture Recognition (13 points)

**Goal:** Recognize thumbs up, wave, and palm/stop gestures with high accuracy and low false positives.

#### Acceptance Criteria
- [ ] Thumbs up recognized (thumb extended, 4 fingers curled)
- [ ] Wave recognized (hand side-to-side motion, 2+ swings)
- [ ] Palm/Stop recognized (open hand, 5 fingers extended)
- [ ] Recognition within 0.5 seconds
- [ ] False positive rate <5%
- [ ] Hold time validation (0.5s minimum)
- [ ] Distance validation (1-3 meters)

#### Implementation Details

**File:** `src/vision/gesture_recognizer.py` (500-600 lines)

**Key Components:**

1. **GestureType enum**
   - `THUMBS_UP` = "thumbs_up"
   - `WAVE` = "wave"
   - `PALM_STOP` = "palm_stop"
   - `UNKNOWN` = "unknown"

2. **GestureResult dataclass**
   - `gesture_type: GestureType`
   - `confidence: float` (0-1)
   - `hand_id: str` (which hand performed gesture)
   - `handedness: str` ("Left" or "Right")
   - `is_valid: bool` (passed hold time + distance checks)
   - `hold_duration: float` (seconds gesture held)
   - `distance_estimate: Optional[float]` (meters from camera)
   - `timestamp: float`
   - `processing_time_ms: float`
   - `landmarks: Optional[HandLandmarks]` (original landmarks)
   - `to_dict()` method

3. **GestureRecognizer class**
   - **Initialization:**
     - `__init__(hold_time, min_distance, max_distance, confidence_threshold)`
     - `_load_config()` - load from YAML
     - `_initialize_gesture_buffers()` - track gesture history per hand
   
   - **Gesture Classification (Core Methods):**
     - `recognize(landmarks_list)` - main entry point, returns List[GestureResult]
     - `_classify_gesture(landmarks)` - classify single hand, returns (GestureType, confidence)
     - `_is_thumbs_up(landmarks)` - thumb extended, fingers curled heuristic
     - `_is_wave(hand_id, landmarks)` - detect side-to-side motion in buffer
     - `_is_palm_stop(landmarks)` - all fingers extended, palm facing camera
   
   - **Validation:**
     - `_validate_hold_time(hand_id, gesture_type)` - check gesture held for min duration
     - `_estimate_distance(landmarks)` - estimate hand distance from wrist-to-fingertip size
     - `_validate_distance(distance)` - check 1-3m range
     - `_check_false_positive_heuristics(landmarks, gesture_type)` - additional filtering
   
   - **Tracking & Statistics:**
     - `_update_gesture_buffer(hand_id, gesture_type, timestamp)` - maintain history
     - `_clear_expired_buffers()` - remove old tracking data
     - `get_statistics()` - recognition counts, false positives, avg confidence
     - `reset_statistics()` - clear stats

**Gesture Detection Heuristics:**

**Thumbs Up:**
- Thumb tip y < thumb IP y (thumb pointing up)
- Thumb tip x distance from wrist > threshold (thumb extended)
- All finger tips y > finger MCPs y (fingers curled)
- Confidence: 0.8 if all conditions met, 0.0 otherwise

**Wave:**
- Track wrist x position over last 1 second
- Detect oscillation: positive → negative → positive (or reverse)
- Minimum 2 direction changes
- Amplitude > threshold (10% of frame width)
- Confidence: based on oscillation count and amplitude

**Palm Stop:**
- All 5 fingertips y < MCPs y (fingers extended upward)
- Fingertip spread (x distance between fingers) > threshold
- Palm facing camera (z-coordinates of palm landmarks similar)
- Confidence: 0.8 if all conditions, 0.6 if 4/5 fingers extended

**Distance Estimation:**
- Measure wrist-to-middle-finger-tip Euclidean distance in normalized coords
- Inverse relationship: smaller distance = farther hand
- Calibration factors in config (camera FOV dependent)

**Configuration:** `src/config/gesture_recognition.yaml`
```yaml
gesture_recognition:
  # Hold time validation
  min_hold_time_seconds: 0.5
  gesture_buffer_duration: 1.0  # Track last 1 second of gestures
  
  # Distance validation
  min_distance_meters: 1.0
  max_distance_meters: 3.0
  distance_estimation:
    # Hand size calibration (normalized coords)
    reference_hand_size: 0.3  # Expected size at 2 meters
    size_distance_factor: 0.6  # Inverse relationship factor
  
  # Confidence thresholds
  min_confidence: 0.7
  wave_min_oscillations: 2
  wave_min_amplitude: 0.1  # 10% of frame width
  
  # False positive prevention
  false_positive_checks:
    require_stable_wrist: true  # Wrist position stable during recognition
    max_wrist_movement: 0.05  # Max normalized movement during hold
    ignore_during_movement: true  # Ignore gestures if person moving fast
  
  # Performance
  max_tracking_hands: 2
  buffer_cleanup_interval: 5.0  # Seconds
```

**Testing:** `tests/test_story_3_2_gesture_recognition.py` (25 tests)
- Unit tests: thumbs up/wave/palm detection, confidence scoring, hold time validation
- Integration tests: end-to-end recognition with mock landmarks
- Performance tests: <0.5s recognition time
- False positive tests: random hand positions don't trigger (<5%)

---

### Story 3.3: Gesture-to-Command Mapping (5 points)

**Goal:** Map recognized gestures to robot commands and integrate with event system.

#### Acceptance Criteria
- [ ] 👍 → "Approve" command sent to coordination layer
- [ ] 👋 → "Skip" command sent
- [ ] ✋ → "Pause" command sent
- [ ] Visual feedback appears <0.2 seconds after gesture
- [ ] Optional audio confirmation (short beep/tone)
- [ ] Integration with existing `EventManager`
- [ ] Thread-safe command dispatch

#### Implementation Details

**File:** `src/coordination/gesture_coordinator.py` (350-400 lines)

**Key Components:**

1. **GestureCommand enum**
   - `APPROVE` = "approve"
   - `SKIP` = "skip"
   - `PAUSE` = "pause"

2. **GestureEvent dataclass** (extends RecognitionEvent pattern)
   - `command: GestureCommand`
   - `gesture_result: GestureResult` (full gesture details)
   - `timestamp: float`
   - `processed: bool` (flag for duplicate prevention)
   - `to_dict()` method

3. **GestureCoordinator class** (follows GreetingCoordinator pattern)
   - **Initialization:**
     - `__init__(gesture_recognizer, event_manager, feedback_manager, audio_enabled)`
     - `_load_config()` - load from YAML
     - `_register_callbacks()` - register with EventManager
   
   - **Command Processing:**
     - `process_frame(frame)` - main entry point, returns List[GestureEvent]
     - `_map_gesture_to_command(gesture_type)` - mapping logic
     - `_execute_command(command, gesture_result)` - dispatch to handlers
     - `_trigger_feedback(gesture_result, command)` - visual + audio feedback
   
   - **Event Integration:**
     - `_emit_gesture_event(gesture_result, command)` - publish to EventManager
     - `_handle_approve_command(gesture_result)` - approve action callback
     - `_handle_skip_command(gesture_result)` - skip action callback
     - `_handle_pause_command(gesture_result)` - pause action callback
   
   - **Duplicate Prevention:**
     - `_check_duplicate(gesture_result)` - prevent multiple triggers for same gesture
     - `_update_recent_gestures(gesture_result)` - track last 3 seconds
     - `_clear_expired_gestures()` - cleanup old tracking data
   
   - **Statistics & Monitoring:**
     - `get_statistics()` - command counts, latencies, duplicate blocks
     - `reset_statistics()` - clear stats

**Gesture-to-Command Mapping:**
```python
GESTURE_COMMAND_MAP = {
    GestureType.THUMBS_UP: GestureCommand.APPROVE,
    GestureType.WAVE: GestureCommand.SKIP,
    GestureType.PALM_STOP: GestureCommand.PAUSE,
    GestureType.UNKNOWN: None  # Ignored
}
```

**Event System Integration:**

Extend `EventType` enum in `src/events/event_system.py`:
```python
class EventType(Enum):
    PERSON_RECOGNIZED = "person_recognized"
    PERSON_UNKNOWN = "person_unknown"
    PERSON_DEPARTED = "person_departed"
    NO_FACES = "no_faces"
    GESTURE_DETECTED = "gesture_detected"  # NEW
```

**Configuration:** (add to `src/config/config.yaml`)
```yaml
gesture_control:
  # Command mapping
  commands:
    approve:
      enabled: true
      audio_confirmation: true
      beep_frequency: 1000  # Hz
      beep_duration: 0.1    # seconds
    skip:
      enabled: true
      audio_confirmation: true
      beep_frequency: 800
      beep_duration: 0.1
    pause:
      enabled: true
      audio_confirmation: true
      beep_frequency: 600
      beep_duration: 0.2
  
  # Duplicate prevention
  duplicate_window_seconds: 3.0
  
  # Performance
  target_feedback_latency_ms: 200
```

**Testing:** `tests/test_story_3_3_command_mapping.py` (20 tests)
- Unit tests: gesture-to-command mapping, duplicate prevention
- Integration tests: event emission, callback registration, command dispatch
- Performance tests: <0.2s feedback latency
- Thread safety tests: concurrent gesture processing

---

### Story 3.4: Visual Feedback & UI Integration (5 points)

**Goal:** Display visual confirmation when gesture recognized, with smooth animation.

#### Acceptance Criteria
- [ ] On-screen icon displays detected gesture (emoji: 👍👋✋)
- [ ] Icon appears within 0.2 seconds
- [ ] Brief animation (fade-in, pulse, fade-out over 1 second)
- [ ] Screen returns to normal state after confirmation
- [ ] Icons clearly visible from 3 meters
- [ ] No UI blocking (non-modal overlay)

#### Implementation Details

**File:** `src/ui/feedback_manager.py` (300-350 lines)

**Key Components:**

1. **FeedbackAnimation enum**
   - `FADE_IN` = "fade_in"
   - `PULSE` = "pulse"
   - `FADE_OUT` = "fade_out"
   - `COMPLETE` = "complete"

2. **FeedbackState dataclass**
   - `gesture_type: GestureType`
   - `icon: str` (emoji character)
   - `animation_phase: FeedbackAnimation`
   - `start_time: float`
   - `elapsed_time: float`
   - `alpha: float` (transparency 0-1)
   - `scale: float` (size multiplier)

3. **FeedbackManager class**
   - **Initialization:**
     - `__init__(display_duration, icon_size, position, colors)`
     - `_load_config()` - load from YAML
     - `_initialize_display()` - setup overlay canvas
   
   - **Display Methods:**
     - `show_gesture_feedback(gesture_type)` - main entry point
     - `_render_frame(overlay)` - draw current animation frame
     - `_get_icon_for_gesture(gesture_type)` - map to emoji
     - `_update_animation_state(state)` - advance animation phase
   
   - **Animation Phases:**
     - `_animate_fade_in(state)` - alpha 0 → 1 over 0.2s
     - `_animate_pulse(state)` - scale 1.0 → 1.2 → 1.0 over 0.6s
     - `_animate_fade_out(state)` - alpha 1 → 0 over 0.2s
   
   - **Rendering:**
     - `_draw_icon(canvas, icon, position, alpha, scale)` - render emoji
     - `_draw_background(canvas, position, alpha, scale)` - optional circle bg
     - `_apply_overlay(frame, overlay)` - composite onto camera frame
   
   - **Thread Management:**
     - `_animation_thread()` - non-blocking animation loop
     - `start()` - start animation thread
     - `stop()` - gracefully stop thread
     - `cleanup()` - release resources

**Icon Design:**
- Emoji characters: 👍 (U+1F44D), 👋 (U+1F44B), ✋ (U+270B)
- Size: 200x200 pixels (scalable for animation)
- Background: Semi-transparent circle (optional, configurable)
- Colors: High contrast for visibility (white icon, dark bg or vice versa)
- Position: Center screen or configurable corner

**Animation Timing:**
- Fade-in: 0.0-0.2s (alpha 0 → 1, scale 0.8 → 1.0)
- Pulse: 0.2-0.8s (scale 1.0 → 1.2 → 1.0, alpha constant 1)
- Fade-out: 0.8-1.0s (alpha 1 → 0, scale 1.0 → 1.2)
- Total: 1.0 second

**Configuration:** `src/config/feedback_ui.yaml`
```yaml
feedback_ui:
  # Animation settings
  animation:
    total_duration_seconds: 1.0
    fade_in_duration: 0.2
    pulse_duration: 0.6
    fade_out_duration: 0.2
  
  # Visual settings
  icons:
    thumbs_up: "👍"
    wave: "👋"
    palm_stop: "✋"
    size_pixels: 200
    scale_pulse_max: 1.2
  
  # Display position
  position:
    x: "center"  # "center", "left", "right", or pixel value
    y: "center"  # "center", "top", "bottom", or pixel value
    offset_x: 0
    offset_y: -50  # Slightly above center
  
  # Colors (RGBA)
  colors:
    icon_color: [255, 255, 255, 255]  # White
    background_color: [0, 0, 0, 128]  # Semi-transparent black
    background_enabled: true
    background_radius: 120  # Circle radius
  
  # Performance
  target_latency_ms: 200
  frame_rate: 30  # Animation FPS
```

**UI Integration Options:**
1. **Overlay on camera feed** (recommended for Reachy tablet display)
2. **Separate UI window** (for development/testing)
3. **Web-based dashboard** (future: Flask/FastAPI endpoint)

**Testing:** `tests/test_story_3_4_feedback_ui.py` (18 tests)
- Unit tests: icon mapping, animation state transitions, rendering
- Integration tests: end-to-end feedback display, latency validation
- Performance tests: <0.2s display time, smooth 30 FPS animation
- Visual tests: screenshot capture for manual verification

---

## Testing Strategy

### Unit Testing (60 tests total)
- **Story 3.1 (15 tests):** HandDetector config, MediaPipe init, landmark extraction
- **Story 3.2 (25 tests):** Gesture classifiers, validation, false positives
- **Story 3.3 (20 tests):** Command mapping, event emission, duplicate prevention
- **Story 3.4 (18 tests):** Animation phases, rendering, latency

### Integration Testing (25 tests total)
- **End-to-end pipeline:** Camera → HandDetector → GestureRecognizer → GestureCoordinator → FeedbackManager
- **Event system integration:** GESTURE_DETECTED events, callback triggers
- **Multi-gesture scenarios:** Multiple hands, simultaneous gestures
- **Performance validation:** <1s total response time
- **Coordination with existing systems:** EventManager, BehaviorManager

### Performance Testing (5 benchmarks)
- **Hand detection FPS:** 10+ FPS on Pi5 (or mocked equivalent)
- **Gesture recognition latency:** <0.5s from detection to classification
- **Command dispatch latency:** <0.2s from gesture to feedback
- **Total end-to-end latency:** <1s (acceptance criterion)
- **False positive rate:** <5% (100 random hand positions)

### Mock Strategy
- **MediaPipe:** Mock `mp.solutions.hands` for CI environments without MediaPipe GPU
- **Camera:** Use synthetic frames with known landmark positions
- **Display:** Mock rendering for headless testing
- **Event callbacks:** Track callback invocations without real handlers

### Test Fixtures
```python
@pytest.fixture
def mock_hand_landmarks():
    """Generate realistic HandLandmarks for testing."""
    return create_mock_landmarks(
        handedness="Right",
        gesture_type="thumbs_up"  # or "wave", "palm_stop"
    )

@pytest.fixture
def gesture_coordinator(event_manager):
    """Create GestureCoordinator with test dependencies."""
    return GestureCoordinator(
        gesture_recognizer=MockGestureRecognizer(),
        event_manager=event_manager,
        feedback_manager=MockFeedbackManager(),
        audio_enabled=False
    )
```

---

## File Structure

```
src/
├── vision/
│   ├── hand_detector.py              # NEW: Story 3.1 (250 lines)
│   └── gesture_recognizer.py         # NEW: Story 3.2 (600 lines)
├── coordination/
│   ├── greeting_coordinator.py       # Existing
│   └── gesture_coordinator.py        # NEW: Story 3.3 (400 lines)
├── ui/
│   └── feedback_manager.py           # NEW: Story 3.4 (350 lines)
├── events/
│   └── event_system.py               # MODIFIED: Add GESTURE_DETECTED
├── config/
│   ├── config.yaml                   # MODIFIED: Add gesture_control section
│   ├── hand_detection.yaml           # NEW: Story 3.1
│   ├── gesture_recognition.yaml      # NEW: Story 3.2
│   └── feedback_ui.yaml              # NEW: Story 3.4

tests/
├── test_story_3_1_hand_detection.py        # NEW: 15 tests
├── test_story_3_1_integration.py           # NEW: 8 tests
├── test_story_3_2_gesture_recognition.py   # NEW: 25 tests
├── test_story_3_2_integration.py           # NEW: 10 tests
├── test_story_3_3_command_mapping.py       # NEW: 20 tests
├── test_story_3_3_integration.py           # NEW: 7 tests
├── test_story_3_4_feedback_ui.py           # NEW: 18 tests
└── test_story_3_4_integration.py           # NEW: 5 tests

Total New Code: ~1,600 lines implementation + ~1,200 lines tests + ~150 lines config
```

---

## Dependencies

### Python Packages (add to `pyproject.toml`)
```toml
[project.dependencies]
# Existing dependencies...
mediapipe = "^0.10.8"          # Hand tracking
opencv-python = "^4.8.1"        # Already installed (Story 1)
numpy = "^1.24.0"               # Already installed
pillow = "^10.1.0"              # Image processing for UI
pydub = "^0.25.1"               # Audio feedback (optional)
```

### System Requirements
- **Raspberry Pi 5:** 8GB RAM, 64-bit OS
- **MediaPipe:** GPU acceleration via OpenGL ES (if available)
- **Camera:** Reachy built-in camera (640x480 @ 30 FPS)
- **Display:** Reachy tablet for visual feedback overlay

### Installation Steps
```bash
# Install MediaPipe (Story 3.1)
pip install mediapipe opencv-python pillow pydub

# Verify MediaPipe installation
python -c "import mediapipe as mp; print(mp.__version__)"

# Test hand detection on Pi5
python -m src.vision.hand_detector
```

---

## Implementation Order

### Phase 1: Story 3.1 - Hand Detection (Day 1-2)
1. Create `hand_detector.py` with HandLandmarks dataclass
2. Implement HandDetector class with MediaPipe integration
3. Create `hand_detection.yaml` configuration
4. Write unit tests (15 tests)
5. Write integration tests (8 tests)
6. Validate 10+ FPS on Pi5 (or mock for CI)
7. **Deliverable:** HandDetector module with tests passing

### Phase 2: Story 3.2 - Gesture Recognition (Day 3-5)
1. Create `gesture_recognizer.py` with GestureResult dataclass
2. Implement GestureRecognizer class
3. Implement gesture classification heuristics:
   - Thumbs up detection
   - Wave detection (motion tracking)
   - Palm stop detection
4. Implement validation (hold time, distance)
5. Create `gesture_recognition.yaml` configuration
6. Write unit tests (25 tests) - test each gesture independently
7. Write integration tests (10 tests) - end-to-end recognition
8. Validate <0.5s recognition time and <5% false positives
9. **Deliverable:** GestureRecognizer module with tests passing

### Phase 3: Story 3.3 - Command Mapping (Day 6-7)
1. Extend EventType enum with GESTURE_DETECTED
2. Create `gesture_coordinator.py` with GestureCommand enum
3. Implement GestureCoordinator class (follows GreetingCoordinator pattern)
4. Implement command dispatch and event emission
5. Add gesture_control section to `config.yaml`
6. Write unit tests (20 tests) - mapping, duplicate prevention
7. Write integration tests (7 tests) - event system integration
8. Validate <0.2s feedback latency
9. **Deliverable:** GestureCoordinator module with tests passing

### Phase 4: Story 3.4 - Visual Feedback (Day 8-9)
1. Create `feedback_manager.py` with FeedbackState dataclass
2. Implement FeedbackManager class
3. Implement animation phases (fade-in, pulse, fade-out)
4. Implement overlay rendering with emoji icons
5. Create `feedback_ui.yaml` configuration
6. Write unit tests (18 tests) - animation, rendering
7. Write integration tests (5 tests) - end-to-end display
8. Validate <0.2s display latency and 30 FPS animation
9. **Deliverable:** FeedbackManager module with tests passing

### Phase 5: Epic Integration & Testing (Day 10)
1. Run all 108 tests (78 unit + 30 integration)
2. End-to-end validation: camera → gesture → feedback
3. Performance benchmarking: <1s total response time
4. False positive validation: <5% on 100 random frames
5. Update documentation:
   - `bmm-workflow-status.md` - mark Epic 3 complete
   - `README.md` - add gesture control usage examples
   - `CONFIGURATION.md` - document gesture configs
6. **Deliverable:** Epic 3 complete with all acceptance criteria met

---

## Success Criteria

### Technical KPIs
- ✅ Hand detection: 10+ FPS on Raspberry Pi 5
- ✅ Gesture recognition: <0.5s latency
- ✅ Command dispatch: <0.2s feedback latency
- ✅ Total response time: <1s (gesture → action)
- ✅ Recognition accuracy: 95%+ on test gestures
- ✅ False positive rate: <5%

### Testing KPIs
- ✅ 108 total tests passing (78 unit + 30 integration)
- ✅ 100% code coverage on core gesture logic
- ✅ Performance benchmarks passing on Pi5 (or mocked)
- ✅ Integration tests passing with EventManager

### User Experience KPIs
- ✅ Visual feedback visible within 0.2 seconds
- ✅ Animation smooth (30 FPS) and non-blocking
- ✅ Icons clearly visible from 3 meters
- ✅ No accidental triggers during normal hand movements

### Documentation KPIs
- ✅ All modules documented with docstrings
- ✅ Configuration YAMLs with inline comments
- ✅ Test files with clear test names and descriptions
- ✅ README updated with gesture control usage

---

## Risk Assessment & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| MediaPipe too slow on Pi5 (<10 FPS) | High | Medium | Use model_complexity=0 (lite), reduce resolution, use CPU-only mode |
| Gesture recognition false positives | High | Medium | Require 0.5s hold time, distance validation, stable wrist check |
| Wave detection unreliable | Medium | Medium | Adjust oscillation thresholds, increase buffer duration, add amplitude filtering |
| UI rendering blocks camera | Medium | Low | Use separate thread for animation, render on copy of frame |
| Distance estimation inaccurate | Low | High | Calibrate with real-world tests, use conservative 1-3m range, add manual override |

### Integration Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| EventManager incompatible with gesture events | Medium | Low | Follow existing RecognitionEvent pattern, test callbacks thoroughly |
| Gesture commands conflict with voice | Low | Medium | Add command source tracking, prioritize based on timing |
| Display overlay interferes with other UI | Low | Medium | Use non-modal overlay, configurable position, disable when not active |

### User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Managers find gestures awkward | Medium | Medium | Offer voice fallback, make gestures optional, collect user feedback |
| Gestures not recognized when hands busy | High | High | Design gestures for one-handed use, detect partial gestures |
| False triggers while handling inventory | Medium | High | Require deliberate hold time, ignore fast movements, add confirmation step |

---

## Configuration Summary

### Main Configuration (`src/config/config.yaml`)
```yaml
gesture_control:
  enabled: true
  
  commands:
    approve:
      enabled: true
      audio_confirmation: true
      beep_frequency: 1000
      beep_duration: 0.1
    skip:
      enabled: true
      audio_confirmation: true
      beep_frequency: 800
      beep_duration: 0.1
    pause:
      enabled: true
      audio_confirmation: true
      beep_frequency: 600
      beep_duration: 0.2
  
  duplicate_window_seconds: 3.0
  target_feedback_latency_ms: 200
```

### Hand Detection Configuration (`src/config/hand_detection.yaml`)
```yaml
hand_detection:
  model_complexity: 0  # 0 = lite, 1 = full
  min_detection_confidence: 0.5
  min_tracking_confidence: 0.5
  max_num_hands: 2
  performance:
    target_fps: 10
    max_latency_ms: 100
```

### Gesture Recognition Configuration (`src/config/gesture_recognition.yaml`)
```yaml
gesture_recognition:
  min_hold_time_seconds: 0.5
  gesture_buffer_duration: 1.0
  
  min_distance_meters: 1.0
  max_distance_meters: 3.0
  
  min_confidence: 0.7
  wave_min_oscillations: 2
  wave_min_amplitude: 0.1
  
  false_positive_checks:
    require_stable_wrist: true
    max_wrist_movement: 0.05
    ignore_during_movement: true
```

### Feedback UI Configuration (`src/config/feedback_ui.yaml`)
```yaml
feedback_ui:
  animation:
    total_duration_seconds: 1.0
    fade_in_duration: 0.2
    pulse_duration: 0.6
    fade_out_duration: 0.2
  
  icons:
    thumbs_up: "👍"
    wave: "👋"
    palm_stop: "✋"
    size_pixels: 200
    scale_pulse_max: 1.2
  
  position:
    x: "center"
    y: "center"
    offset_y: -50
  
  colors:
    icon_color: [255, 255, 255, 255]
    background_color: [0, 0, 0, 128]
    background_enabled: true
```

---

## Epic 3 Summary

**Total Scope:**
- **Stories:** 4 (3.1, 3.2, 3.3, 3.4)
- **Story Points:** 26 points
- **Code:** ~1,600 lines implementation
- **Tests:** ~1,200 lines (108 tests)
- **Config:** ~150 lines (4 YAML files)
- **Duration:** 10 days (2 weeks)

**Key Deliverables:**
1. HandDetector with MediaPipe integration (10+ FPS)
2. GestureRecognizer with 3 gestures (95%+ accuracy, <5% false positives)
3. GestureCoordinator with command dispatch (<0.2s feedback)
4. FeedbackManager with visual animations (1s duration)
5. EventManager integration (GESTURE_DETECTED events)
6. 108 tests passing (78 unit + 30 integration)
7. Complete documentation and configuration

**Next Steps After Epic 3:**
- **Epic 4:** Integration & Testing (Stories 4.1-4.4)
- **Final Validation:** End-to-end system testing
- **Field Deployment:** Pilot test at convenience store
- **User Feedback:** Collect manager and staff input

---

## References

- **PRD:** `docs/prd.md` - Full product requirements
- **Workflow Status:** `docs/bmm-workflow-status.md` - Project tracking
- **MediaPipe Hands:** https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
- **Existing Patterns:** `src/events/event_system.py`, `src/coordination/greeting_coordinator.py`

---

**Status:** ✅ Planning Complete - Ready for Implementation  
**Version:** 1.0  
**Last Updated:** November 15, 2025  
**Next Action:** Issue `*develop` command for Story 3.1 to begin implementation
