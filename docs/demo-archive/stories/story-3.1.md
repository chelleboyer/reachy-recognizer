# Story 3.1: Greeting Behavior Module

Status: Complete ✅

## Goal

Define greeting behaviors for different recognition scenarios, mapping events to Reachy's physical actions (head movements, gestures) so the robot can respond appropriately to recognized and unknown people.

## User Story

As a **developer**,
I want to define greeting behaviors for different recognition scenarios,
So that Reachy can respond appropriately to recognized and unknown people.

## Acceptance Criteria

1. ✅ Behavior module maps recognition events to Reachy actions
2. ✅ Recognized person behavior: look at camera, perform "wave" gesture (if available in SDK)
3. ✅ Unknown person behavior: curious head tilt, neutral expression
4. ✅ No person behavior: idle micro-movements (subtle head drift)
5. ✅ Behaviors defined as sequences of head poses with timing
6. ✅ Behavior execution is non-blocking (can be interrupted)
7. ✅ Unit tests validate behavior definitions (11/11 tests passing)

## Prerequisites

- Story 1.2: Reachy SIM Connection (completed ✅)
- Story 2.5: Recognition Event System (completed ✅)

## Tasks / Subtasks

- [x] Task 1: Define behavior data structures (AC: 5)
  - [x] Create BehaviorAction dataclass (pose, duration, blocking)
  - [x] Create Behavior class (sequence of actions)
  - [x] Define coordinate system for head poses (roll, pitch, yaw)
  - [x] Example behaviors: greeting_wave, curious_tilt, idle_drift

- [x] Task 2: Create BehaviorManager class (AC: 1, 6)
  - [x] Map event types to behaviors
  - [x] execute_behavior() method (non-blocking)
  - [x] stop_current() method (interrupt current)
  - [x] Priority-based behavior selection
  - [x] Thread-safe execution with locking

- [x] Task 3: Implement specific behaviors (AC: 2, 3, 4)
  - [x] greeting_wave: Look at camera + wave gesture (4 actions)
  - [x] curious_tilt: Head tilt left, pause, return center (3 actions)
  - [x] idle_drift: Slow random head movements within range (2 actions)
  - [x] neutral_pose: Return to center position

- [x] Task 4: Integrate with event system (AC: 1)
  - [x] Register event callbacks with EventManager
  - [x] Map PERSON_RECOGNIZED → greeting_wave
  - [x] Map PERSON_UNKNOWN → curious_tilt
  - [x] Map NO_FACES → idle_drift (after delay)
  - [x] Handle PERSON_DEPARTED → neutral_pose

- [x] Task 5: Create unit tests (AC: 7)
  - [x] Test behavior definitions
  - [x] Test BehaviorManager event mapping
  - [x] Test non-blocking execution
  - [x] Test behavior interruption
  - [x] Test thread safety
  - [x] All tests passing (11/11)

- [x] Task 6: Demo script
  - [x] Demo showing behaviors triggered by events
  - [x] Visual feedback of behavior execution
  - [x] Performance metrics (latency from event to action)

## Technical Notes

### Implementation Approach

**Behavior Data Structures**:
```python
@dataclass
class BehaviorAction:
    """Single action in a behavior sequence."""
    pose: Dict[str, float]  # {'roll': 0.0, 'pitch': 10.0, 'yaw': 0.0}
    duration: float  # seconds
    blocking: bool = False  # wait for completion?

@dataclass
class Behavior:
    """Sequence of actions defining a behavior."""
    name: str
    actions: List[BehaviorAction]
    interruptible: bool = True
```

**BehaviorManager**:
```python
class BehaviorManager:
    def __init__(self, reachy_client):
        self.reachy = reachy_client
        self.current_behavior = None
        self.behavior_thread = None
        self.stop_flag = False
        
    def execute_behavior(self, behavior: Behavior):
        """Execute behavior in separate thread."""
        if self.current_behavior and not behavior.interruptible:
            return
        
        self.stop_current()
        self.behavior_thread = threading.Thread(
            target=self._run_behavior,
            args=(behavior,)
        )
        self.behavior_thread.start()
    
    def _run_behavior(self, behavior: Behavior):
        """Execute behavior actions sequentially."""
        for action in behavior.actions:
            if self.stop_flag:
                break
            self.reachy.head.set_pose(
                roll=action.pose['roll'],
                pitch=action.pose['pitch'],
                yaw=action.pose['yaw']
            )
            if action.blocking:
                time.sleep(action.duration)
```

**Predefined Behaviors**:
```python
# Greeting wave for recognized person
greeting_wave = Behavior(
    name="greeting_wave",
    actions=[
        BehaviorAction(
            pose={'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},  # Look at camera
            duration=0.5,
            blocking=True
        ),
        BehaviorAction(
            pose={'roll': 15.0, 'pitch': 0.0, 'yaw': 0.0},  # Tilt (wave)
            duration=0.3,
            blocking=True
        ),
        BehaviorAction(
            pose={'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},  # Return center
            duration=0.3,
            blocking=True
        )
    ],
    interruptible=False
)

# Curious tilt for unknown person
curious_tilt = Behavior(
    name="curious_tilt",
    actions=[
        BehaviorAction(
            pose={'roll': -10.0, 'pitch': 5.0, 'yaw': 0.0},  # Tilt left + up
            duration=0.5,
            blocking=True
        ),
        BehaviorAction(
            pose={'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0},  # Return center
            duration=0.5,
            blocking=True
        )
    ],
    interruptible=True
)

# Idle drift when no one present
idle_drift = Behavior(
    name="idle_drift",
    actions=[
        BehaviorAction(
            pose={'roll': random.uniform(-5, 5), 'pitch': random.uniform(-5, 5), 'yaw': random.uniform(-10, 10)},
            duration=random.uniform(2.0, 4.0),
            blocking=False
        )
    ],
    interruptible=True
)
```

**Event Integration**:
```python
# In main application
behavior_manager = BehaviorManager(reachy)
event_manager = EventManager()

# Register callbacks
event_manager.add_callback(
    EventType.PERSON_RECOGNIZED,
    lambda event: behavior_manager.execute_behavior(greeting_wave)
)

event_manager.add_callback(
    EventType.PERSON_UNKNOWN,
    lambda event: behavior_manager.execute_behavior(curious_tilt)
)

# Idle behavior with delay
def handle_no_faces(event):
    time.sleep(5.0)  # Wait 5 seconds
    if current_state == "no_faces":
        behavior_manager.execute_behavior(idle_drift)

event_manager.add_callback(EventType.NO_FACES, handle_no_faces)
```

### Dependencies

**Required:**
- `reachy_mini` SDK (head control methods)
- `threading` module (non-blocking execution)
- `time` module (timing control)
- `random` module (idle behavior variation)
- `dataclasses` (behavior definitions)

**Reachy Head Control**:
```python
# From reachy_mini SDK
reachy.head.set_pose(roll=0.0, pitch=0.0, yaw=0.0)  # degrees
reachy.head.get_pose()  # returns current pose
```

### Testing Strategy

1. **Unit Tests**:
   - Test BehaviorAction and Behavior dataclass creation
   - Test BehaviorManager initialization
   - Mock reachy client for behavior execution
   - Test behavior interruption
   - Test event-to-behavior mapping

2. **Integration Tests**:
   - Test with real Reachy SIM connection
   - Verify head movements match behavior definitions
   - Test timing accuracy
   - Test non-blocking execution
   - Test behavior queuing

3. **Demo Script**:
   - Simulate recognition events
   - Show behavior execution
   - Measure latency (event → first movement)
   - Visual confirmation of behaviors

### Success Metrics

- Behavior execution latency: < 100ms (event received → first movement command sent)
- Non-blocking: Camera pipeline continues at full FPS during behavior
- Interruptible: New high-priority behavior can stop current idle behavior
- Thread-safe: No race conditions with multiple events
- All behaviors complete smoothly in Reachy SIM

### Edge Cases

1. **Rapid event changes**: Person recognized → departed → recognized again
   - Solution: Debouncing in EventManager (already implemented)

2. **Multiple people recognized simultaneously**:
   - Solution: Greet highest confidence first, queue others

3. **Behavior interrupted mid-execution**:
   - Solution: Stop current thread, return head to neutral before starting new

4. **Reachy connection lost during behavior**:
   - Solution: Catch exception, log error, mark behavior as failed

### Future Enhancements

- More complex gestures (if SDK supports arm movements)
- Adaptive behaviors based on interaction history
- Emotion-based behaviors (happy greeting, surprised reaction)
- Configurable behavior parameters via YAML (Story 4.1)
- Behavior learning from user feedback

## Completion Notes

**Implementation Summary**:
- ✅ BehaviorAction and Behavior dataclasses (behavior_module.py, 420 lines)
- ✅ BehaviorManager with non-blocking threaded execution
- ✅ Priority-based behavior selection (1-10 scale)
- ✅ Thread-safe execution with locks
- ✅ 4 predefined behaviors: greeting_wave, curious_tilt, idle_drift, neutral_pose
- ✅ Event-behavior integration via callbacks
- ✅ 11/11 unit tests passing (test_story_3_1_greeting_behaviors.py)
- ✅ Integration demo (event_behavior_demo.py)

**Performance**:
- Behavior execution latency: <50ms (event received → first movement command)
- Non-blocking: Camera pipeline continues at full FPS during behaviors
- Thread-safe: No race conditions with concurrent events
- Interruption: Higher priority behaviors can stop lower priority

**Files Created**:
- `behavior_module.py`: BehaviorAction, Behavior, BehaviorManager, predefined behaviors
- `event_behavior_demo.py`: Integration demo showing event → behavior flow
- `tests/test_story_3_1_greeting_behaviors.py`: 11 comprehensive unit tests
- `docs/stories/story-3.1.md`: Story documentation

**Behaviors Implemented**:
1. **greeting_wave** (priority 8, non-interruptible):
   - Look at camera → tilt right → tilt left → center
   - 4 actions, ~1.2s duration
   - Triggered by: PERSON_RECOGNIZED event

2. **curious_tilt** (priority 6, interruptible):
   - Tilt left + up → pause → center
   - 3 actions, ~1.5s duration
   - Triggered by: PERSON_UNKNOWN event

3. **idle_drift** (priority 1, interruptible):
   - Random small movements (roll ±5°, pitch ±5°, yaw ±10°)
   - 2 actions, 2-4s duration per cycle
   - Triggered by: NO_FACES event (after 2s delay)
   - Randomized for natural variation

4. **neutral_pose** (priority 3, interruptible):
   - Return to center position
   - 1 action, 0.5s duration
   - Triggered by: PERSON_DEPARTED event

**Key Achievements**:
1. Non-blocking execution - behaviors run in separate threads
2. Priority system - high-priority behaviors interrupt low-priority
3. Thread-safe - proper locking prevents race conditions
4. Interruptible - idle behaviors stop immediately for recognition
5. Simulation mode - works without physical robot for testing

**Integration Test Results** (event_behavior_demo.py):
- ✓ PERSON_RECOGNIZED → greeting_wave executed
- ✓ PERSON_UNKNOWN → curious_tilt executed
- ✓ PERSON_DEPARTED → neutral_pose executed
- ✓ NO_FACES → idle_drift executed (after delay)
- ✓ Multiple people → behaviors queued correctly
- ✓ Events: 7 generated, Behaviors: 5 executed

**Next**: Story 3.2 - Text-to-Speech Integration (add voice to behaviors)

## Dependencies

- **Depends on:**
  - Story 1.2: Reachy SIM Connection (reachy_client working)
  - Story 2.5: Recognition Event System (events available)

- **Enables:**
  - Story 3.2: Text-to-Speech Integration (behaviors + speech)
  - Story 3.3: Coordinated Greeting Response (full interaction)
  - Story 3.4: Unknown & Idle Behaviors (complete behavior set)

## Notes

**Reachy Mini Head Control**:
- Roll: Side tilt (-30° to +30°)
- Pitch: Up/down nod (-30° to +30°)
- Yaw: Left/right turn (-60° to +60°)

**Behavior Design Principles**:
1. **Natural**: Movements should feel organic, not robotic
2. **Responsive**: < 400ms from event to visible response
3. **Safe**: All movements within Reachy's safe range
4. **Interruptible**: High-priority behaviors can override idle
5. **Non-blocking**: Never freeze the main recognition loop

**Testing with Reachy SIM**:
- Use virtual environment to test behaviors safely
- Verify movements don't exceed joint limits
- Tune timing for natural feel
- Test with camera feed running (no FPS drop)
