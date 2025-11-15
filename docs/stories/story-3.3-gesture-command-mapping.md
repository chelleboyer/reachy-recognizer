# Story 3.3: Gesture-to-Command Mapping

**Epic:** Epic 3 - Gesture Control System  
**Story Points:** 5  
**Priority:** P0 (Must Have)  
**Status:** Ready for Development

---

## Story Description

**As a** Reachy Mini robot  
**I want to** map recognized gestures to robot commands  
**So that** users can control the robot through intuitive hand gestures

---

## Acceptance Criteria

### AC1: Command Mapping
- [ ] 👍 Thumbs Up → "Approve" command
- [ ] 👋 Wave → "Skip" command
- [ ] ✋ Palm Stop → "Pause" command
- [ ] UNKNOWN gesture → No command (ignored)
- [ ] Configurable command mappings via YAML

### AC2: Event System Integration
- [ ] Extend EventType enum with GESTURE_DETECTED
- [ ] GestureEvent emitted when valid gesture detected
- [ ] Event includes gesture type, command, confidence, timestamp
- [ ] Integration with existing EventManager
- [ ] Callbacks registered for gesture events

### AC3: Command Dispatch
- [ ] GestureCoordinator processes recognized gestures
- [ ] Commands dispatched to appropriate handlers
- [ ] Thread-safe command execution
- [ ] Commands logged for debugging

### AC4: Duplicate Prevention
- [ ] Track recent gestures (3-second window)
- [ ] Prevent duplicate commands for same gesture
- [ ] Per-hand tracking (left/right independent)
- [ ] Automatic cleanup of expired gesture history

### AC5: Feedback Integration
- [ ] Visual feedback triggered <0.2s after gesture
- [ ] Optional audio confirmation (beep/tone)
- [ ] Configurable feedback per command type
- [ ] Non-blocking feedback execution

### AC6: Configuration System
- [ ] gesture_control section in config.yaml
- [ ] Per-command configuration (enabled, audio, beep settings)
- [ ] Duplicate prevention window configurable
- [ ] Target latency settings

### AC7: Unit Tests
- [ ] Test gesture-to-command mapping logic
- [ ] Test duplicate prevention
- [ ] Test event emission
- [ ] Test command dispatch
- [ ] Test configuration loading
- [ ] Test statistics tracking
- **Target:** 20 unit tests

### AC8: Integration Tests
- [ ] End-to-end: gesture → event → feedback
- [ ] Test EventManager integration
- [ ] Test callback registration and execution
- [ ] Test concurrent gesture processing
- [ ] Validate <0.2s feedback latency
- **Target:** 7 integration tests

---

## Technical Specification

### Input
```python
# GestureResult from Story 3.2
gesture_result: GestureResult
```

### Output
```python
from enum import Enum

class GestureCommand(Enum):
    """Robot commands mapped from gestures."""
    APPROVE = "approve"
    SKIP = "skip"
    PAUSE = "pause"

@dataclass
class GestureEvent:
    """Event emitted when gesture detected."""
    command: GestureCommand
    gesture_result: GestureResult
    timestamp: float
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "command": self.command.value,
            "gesture_type": self.gesture_result.gesture_type.value,
            "confidence": self.gesture_result.confidence,
            "hand_id": self.gesture_result.hand_id,
            "handedness": self.gesture_result.handedness,
            "timestamp": self.timestamp,
            "processed": self.processed
        }
```

### GestureCoordinator Class
```python
class GestureCoordinator:
    """Coordinates gesture recognition with command execution."""
    
    def __init__(
        self,
        hand_detector: HandDetector,
        gesture_recognizer: GestureRecognizer,
        event_manager: EventManager,
        config_path: str
    ):
        """Initialize coordinator with dependencies."""
        ...
    
    def process_frame(self, frame: np.ndarray) -> List[GestureEvent]:
        """Process frame and emit gesture events.
        
        Args:
            frame: Camera frame
            
        Returns:
            List of GestureEvent objects emitted
        """
        ...
    
    def _map_gesture_to_command(self, gesture_type: GestureType) -> Optional[GestureCommand]:
        """Map gesture type to command."""
        ...
    
    def _check_duplicate(self, gesture_result: GestureResult) -> bool:
        """Check if gesture is duplicate within window."""
        ...
    
    def _emit_gesture_event(self, gesture_result: GestureResult, command: GestureCommand):
        """Emit GESTURE_DETECTED event."""
        ...
    
    def _execute_command(self, command: GestureCommand, gesture_result: GestureResult):
        """Execute command and trigger feedback."""
        ...
    
    def _trigger_feedback(self, gesture_result: GestureResult, command: GestureCommand):
        """Trigger visual and audio feedback."""
        ...
    
    def _update_recent_gestures(self, gesture_result: GestureResult, command: GestureCommand):
        """Track recent gesture for duplicate prevention."""
        ...
    
    def _clear_expired_gestures(self):
        """Remove gestures older than duplicate window."""
        ...
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get command execution statistics."""
        ...
    
    def reset_statistics(self):
        """Reset statistics counters."""
        ...
```

---

## Implementation Details

### Files to Create

1. **src/coordination/gesture_coordinator.py** (~400 lines)
   - GestureCommand enum
   - GestureEvent dataclass
   - GestureCoordinator class
   - Command mapping logic
   - Duplicate prevention
   - Event emission
   - Statistics tracking

2. **tests/test_story_3_3_command_mapping.py** (~350 lines)
   - 20 unit tests
   - Test fixtures for mocking dependencies
   - Command mapping tests
   - Duplicate prevention tests
   - Configuration tests

3. **tests/test_story_3_3_integration.py** (~300 lines)
   - 7 integration tests
   - End-to-end pipeline tests
   - EventManager integration tests
   - Performance validation

### Files to Modify

1. **src/events/event_system.py**
   - Add GESTURE_DETECTED to EventType enum
   - Update documentation

2. **src/config/config.yaml**
   - Add gesture_control section
   - Command configuration
   - Duplicate prevention settings

---

## Key Algorithms

### Gesture-to-Command Mapping
```python
GESTURE_COMMAND_MAP = {
    GestureType.THUMBS_UP: GestureCommand.APPROVE,
    GestureType.WAVE: GestureCommand.SKIP,
    GestureType.PALM_STOP: GestureCommand.PAUSE,
    GestureType.UNKNOWN: None  # Ignored
}

def _map_gesture_to_command(self, gesture_type: GestureType) -> Optional[GestureCommand]:
    """Map gesture type to command.
    
    Returns None for UNKNOWN gestures or disabled commands.
    """
    command = GESTURE_COMMAND_MAP.get(gesture_type)
    
    if command and self._is_command_enabled(command):
        return command
    
    return None
```

### Duplicate Prevention
```python
def _check_duplicate(self, gesture_result: GestureResult) -> bool:
    """Check if gesture is duplicate within window.
    
    Algorithm:
    1. Get recent gestures for this hand_id
    2. Find gestures of same type within duplicate window
    3. Return True if duplicate found, False otherwise
    """
    hand_id = gesture_result.hand_id
    gesture_type = gesture_result.gesture_type
    current_time = gesture_result.timestamp
    
    # Get recent gestures for this hand
    recent = self.recent_gestures.get(hand_id, [])
    
    # Check for duplicates within window
    for prev_gesture, prev_time in recent:
        if prev_gesture == gesture_type:
            time_delta = current_time - prev_time
            if time_delta < self.duplicate_window:
                return True  # Duplicate found
    
    return False  # Not a duplicate
```

### Event Emission
```python
def _emit_gesture_event(self, gesture_result: GestureResult, command: GestureCommand):
    """Emit GESTURE_DETECTED event.
    
    Creates GestureEvent and publishes via EventManager.
    """
    event = GestureEvent(
        command=command,
        gesture_result=gesture_result,
        timestamp=time.time(),
        processed=False
    )
    
    # Emit event via EventManager
    self.event_manager.emit(EventType.GESTURE_DETECTED, event)
    
    # Update statistics
    self.command_counts[command] += 1
    self.total_commands += 1
    
    # Log if enabled
    if self.enable_logging:
        logger.info(
            f"Gesture command: {command.value} "
            f"(gesture: {gesture_result.gesture_type.value}, "
            f"confidence: {gesture_result.confidence:.2f})"
        )
```

### Command Execution
```python
def _execute_command(self, command: GestureCommand, gesture_result: GestureResult):
    """Execute command and trigger feedback.
    
    Algorithm:
    1. Check if command is enabled in config
    2. Trigger visual feedback (via FeedbackManager)
    3. Trigger audio feedback if enabled
    4. Log command execution
    5. Update statistics
    """
    # Visual feedback (non-blocking)
    self._trigger_feedback(gesture_result, command)
    
    # Audio feedback if enabled
    if self._is_audio_enabled(command):
        self._play_confirmation_beep(command)
    
    # Command-specific handlers (to be implemented in Story 3.4 or later)
    # These would integrate with BehaviorManager for robot actions
    handler = self.command_handlers.get(command)
    if handler:
        handler(gesture_result)
```

---

## Configuration

### config.yaml (gesture_control section)
```yaml
gesture_control:
  # Enable/disable gesture control
  enabled: true
  
  # Command configuration
  commands:
    approve:
      enabled: true
      audio_confirmation: true
      beep_frequency: 1000  # Hz
      beep_duration: 0.1    # seconds
      # Future: robot behavior (smile, nod, etc.)
    
    skip:
      enabled: true
      audio_confirmation: true
      beep_frequency: 800   # Hz
      beep_duration: 0.1    # seconds
      # Future: robot behavior (look away, etc.)
    
    pause:
      enabled: true
      audio_confirmation: true
      beep_frequency: 600   # Hz
      beep_duration: 0.2    # seconds
      # Future: robot behavior (stop motion, etc.)
  
  # Duplicate prevention
  duplicate_window_seconds: 3.0
  
  # Performance
  target_feedback_latency_ms: 200
  
  # Debug
  enable_logging: true
  log_level: "INFO"
```

---

## Event System Extension

### EventType Enum Update
```python
# In src/events/event_system.py

class EventType(Enum):
    """Types of events in the system."""
    PERSON_RECOGNIZED = "person_recognized"
    PERSON_UNKNOWN = "person_unknown"
    PERSON_DEPARTED = "person_departed"
    NO_FACES = "no_faces"
    GESTURE_DETECTED = "gesture_detected"  # NEW for Story 3.3
```

### Event Usage Example
```python
from src.events.event_system import EventManager, EventType
from src.coordination.gesture_coordinator import GestureCoordinator

# Initialize
event_manager = EventManager()
coordinator = GestureCoordinator(
    hand_detector=hand_detector,
    gesture_recognizer=gesture_recognizer,
    event_manager=event_manager,
    config_path="config.yaml"
)

# Register callback for gesture events
def on_gesture_detected(event_data: GestureEvent):
    print(f"Gesture detected: {event_data.command.value}")
    print(f"  Confidence: {event_data.gesture_result.confidence:.2f}")
    print(f"  Hand: {event_data.gesture_result.handedness}")

event_manager.subscribe(EventType.GESTURE_DETECTED, on_gesture_detected)

# Process frames
while True:
    frame = camera.read()
    events = coordinator.process_frame(frame)
    # Events automatically emitted via EventManager
```

---

## Testing Strategy

### Unit Tests (20 tests)

1. **TestGestureCommand** (3 tests)
   - Enum values
   - String representation
   - Serialization

2. **TestGestureEvent** (3 tests)
   - Event creation
   - to_dict() method
   - Event attributes

3. **TestGestureCoordinatorInit** (3 tests)
   - Valid initialization
   - Config loading
   - Dependency injection

4. **TestCommandMapping** (4 tests)
   - Thumbs up → APPROVE
   - Wave → SKIP
   - Palm stop → PAUSE
   - Unknown → None
   - Disabled command → None

5. **TestDuplicatePrevention** (4 tests)
   - Duplicate within window (blocked)
   - Different gesture (allowed)
   - Expired gesture (allowed)
   - Different hand (allowed)

6. **TestEventEmission** (3 tests)
   - Event emitted with correct data
   - EventManager integration
   - Multiple events

### Integration Tests (7 tests)

1. **TestEndToEndPipeline** (2 tests)
   - Frame → detection → recognition → command → event
   - Multiple gestures in sequence

2. **TestEventManagerIntegration** (2 tests)
   - Callback registration
   - Callback execution with correct data

3. **TestConcurrentProcessing** (1 test)
   - Multiple hands simultaneous gestures

4. **TestPerformanceValidation** (2 tests)
   - Feedback latency <200ms
   - Processing time <100ms per frame

---

## Performance Requirements

- **Feedback Latency:** <0.2s from gesture detection to feedback display
- **Processing Time:** <100ms per frame for command mapping
- **Duplicate Window:** 3.0s (configurable)
- **Event Emission:** Immediate (non-blocking)
- **Memory:** Minimal overhead for gesture tracking

---

## Integration Points

### With Story 3.1 (HandDetector)
```python
# HandDetector provides hand landmarks
hands = hand_detector.detect(frame)
```

### With Story 3.2 (GestureRecognizer)
```python
# GestureRecognizer provides gesture classification
for hand in hands:
    result = gesture_recognizer.recognize(hand)
    if result.is_confirmed:
        # Process confirmed gesture
```

### With Story 3.4 (FeedbackManager)
```python
# Trigger visual feedback (to be implemented in Story 3.4)
feedback_manager.show_gesture_feedback(gesture_result.gesture_type)
```

### With Existing EventManager
```python
# Emit events via existing EventManager
event_manager.emit(EventType.GESTURE_DETECTED, gesture_event)
```

---

## Dependencies

```toml
[project.dependencies]
# From previous stories
mediapipe = ">=0.10.8"
opencv-python = ">=4.8.0"
numpy = ">=1.24.0"
pyyaml = ">=6.0"

# New for audio feedback (optional)
pydub = ">=0.25.1"  # Audio beep generation
simpleaudio = ">=1.0.4"  # Audio playback (cross-platform)
```

---

## Usage Example

```python
from src.vision.hand_detector import HandDetector
from src.vision.gesture_recognizer import GestureRecognizer
from src.coordination.gesture_coordinator import GestureCoordinator
from src.events.event_system import EventManager, EventType
import cv2

# Initialize components
event_manager = EventManager()
hand_detector = HandDetector("src/config/hand_detection.yaml")
gesture_recognizer = GestureRecognizer("src/config/gesture_recognition.yaml")

coordinator = GestureCoordinator(
    hand_detector=hand_detector,
    gesture_recognizer=gesture_recognizer,
    event_manager=event_manager,
    config_path="src/config/config.yaml"
)

# Register callback
def handle_approve_command(event_data):
    print(f"✓ Approved! (confidence: {event_data.gesture_result.confidence:.2f})")
    # Execute approval action...

def handle_skip_command(event_data):
    print(f"→ Skipped! (confidence: {event_data.gesture_result.confidence:.2f})")
    # Execute skip action...

def handle_pause_command(event_data):
    print(f"⏸ Paused! (confidence: {event_data.gesture_result.confidence:.2f})")
    # Execute pause action...

# Subscribe to gesture events
event_manager.subscribe(EventType.GESTURE_DETECTED, 
    lambda e: handle_approve_command(e) if e.command == GestureCommand.APPROVE else None)
event_manager.subscribe(EventType.GESTURE_DETECTED,
    lambda e: handle_skip_command(e) if e.command == GestureCommand.SKIP else None)
event_manager.subscribe(EventType.GESTURE_DETECTED,
    lambda e: handle_pause_command(e) if e.command == GestureCommand.PAUSE else None)

# Main loop
camera = cv2.VideoCapture(0)
while True:
    ret, frame = camera.read()
    if not ret:
        break
    
    # Process frame (automatically emits events)
    events = coordinator.process_frame(frame)
    
    # Display frame
    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
```

---

## Success Metrics

- ✅ All 27 tests passing (20 unit + 7 integration)
- ✅ <0.2s feedback latency
- ✅ Zero duplicate commands within 3-second window
- ✅ EventManager integration working
- ✅ Thread-safe command execution
- ✅ Configuration system functional
- ✅ Statistics tracking accurate

---

## Next Steps

**Story 3.4: Visual Feedback & UI Integration (5 points)**
- Implement FeedbackManager for visual gesture feedback
- Display gesture icons (👍👋✋) with animation
- <0.2s display latency
- Non-blocking overlay rendering

---

_Story Status: Ready for Development_  
_Dependencies: Stories 3.1 ✅, 3.2 ✅_  
_Estimated Duration: 2-3 days_  
_Target: 27 tests passing, <0.2s latency_
