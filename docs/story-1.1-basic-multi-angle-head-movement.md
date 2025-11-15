# Story 1.1: Basic Multi-Angle Head Movement

**Story ID:** STORY-1.1  
**Epic:** [Epic 1 - Multi-Angle Capture System](./epic-1-multi-angle-capture.md)  
**Status:** READY  
**Priority:** P0 (Must Have)  
**Story Points:** 5  
**Assigned To:** dev agent  
**Sprint:** Week 1, Days 1-2

---

## User Story

**As a** store manager  
**I want** the robot to automatically capture multiple angles of a cigarette shelf  
**So that** glare doesn't prevent product identification

## Business Context

Single-angle captures of shiny cigarette packaging often fail due to glare, requiring manual repositioning or multiple attempts. Automated multi-angle capture eliminates this friction and ensures at least one clear view is captured.

**User Pain:** "I have to manually tilt products or ask the robot to try again when glare blocks the barcode"

**Value Delivered:** Fast, automated capture from 5 angles in <10 seconds without human intervention

## Acceptance Criteria

### AC1: Predefined Angle Configuration
- [ ] System loads 5 predefined angles from YAML config
- [ ] Angles defined as: [-45°, -22°, 0°, +22°, +45°] horizontal (yaw)
- [ ] Pitch angle configurable (default: -10° to look slightly down at shelf)
- [ ] Config includes per-angle pause duration (default: 100ms)

### AC2: Sequential Head Movement
- [ ] Robot moves head to each angle in sequence
- [ ] Movement completes in <2 seconds per angle
- [ ] Head reaches target angle within ±2° tolerance
- [ ] Movement is smooth (no jerky motion)

### AC3: Camera Stabilization
- [ ] System pauses 100ms at each angle before capture
- [ ] Camera frame buffer cleared after movement
- [ ] Frame timestamp logged per angle

### AC4: Frame Capture
- [ ] One frame captured at each angle
- [ ] Frame resolution: 640x480 (or camera native)
- [ ] Frames stored in memory (not written to disk yet)
- [ ] Frame metadata includes: angle, timestamp, capture_id

### AC5: Performance
- [ ] Total sequence (5 angles) completes in <10 seconds
- [ ] No motor overheating or errors during 10 consecutive runs
- [ ] System returns head to neutral position (0°, 0°) after capture

## Technical Implementation

### Module: `src/vision/multi_angle_capture.py`

#### Class: `MultiAngleCaptureController`

**Purpose:** Orchestrates head movement and frame capture across multiple angles

**Key Methods:**

```python
class MultiAngleCaptureController:
    def __init__(self, reachy_interface, camera_interface, config_path):
        """
        Initialize controller with robot and camera interfaces
        
        Args:
            reachy_interface: ReachyInterface for motor control
            camera_interface: CameraInterface for frame capture
            config_path: Path to YAML config with angles
        """
        
    async def capture_sequence(self, target_roi: Optional[Box] = None) -> List[CapturedFrame]:
        """
        Execute multi-angle capture sequence
        
        Args:
            target_roi: Optional ROI to track across angles
            
        Returns:
            List of CapturedFrame objects with metadata
            
        Raises:
            CaptureSequenceError: If movement or capture fails
        """
        
    async def _move_to_angle(self, yaw: float, pitch: float) -> None:
        """Move head to specified angle and stabilize"""
        
    async def _capture_frame(self, angle_index: int) -> CapturedFrame:
        """Capture single frame with metadata"""
        
    async def _return_to_neutral(self) -> None:
        """Return head to neutral position"""
```

#### Data Models:

```python
@dataclass
class CapturedFrame:
    frame: np.ndarray          # Image data
    angle_yaw: float           # Yaw angle in degrees
    angle_pitch: float         # Pitch angle in degrees
    timestamp: float           # Unix timestamp
    capture_id: str            # Unique sequence ID
    angle_index: int           # Position in sequence (0-4)
```

### Configuration: `src/config/multi_angle_capture.yaml`

```yaml
multi_angle_capture:
  angles:
    yaw: [-45, -22, 0, 22, 45]  # Degrees
    pitch: -10                   # Look slightly down
  
  movement:
    speed_factor: 0.7           # 0-1, slower = smoother
    stabilization_pause_ms: 100 # Wait after movement
    max_movement_time_sec: 2    # Timeout per angle
  
  camera:
    resolution: [640, 480]
    frame_buffer_clear: true    # Clear buffer after movement
  
  performance:
    max_sequence_time_sec: 10   # Total timeout
    return_to_neutral: true     # Reset after capture
```

### Integration Points

**Upstream Dependencies:**
- `src/coordination/reachy_interface.py` - Motor control via Reachy SDK
- `src/vision/camera.py` - Frame capture from camera

**Downstream Consumers:**
- Story 1.2 - Frame Quality Assessor will consume captured frames
- Story 1.3 - Best Frame Selector will process frame list

## Testing Plan

### Unit Tests

**File:** `tests/test_story_1_1_multi_angle_capture.py`

```python
class TestMultiAngleCaptureController:
    def test_load_config_from_yaml(self):
        """Verify angles loaded from config correctly"""
        
    def test_angle_sequence_order(self):
        """Verify angles executed in correct order"""
        
    async def test_movement_timing(self):
        """Verify each angle completes in <2 seconds"""
        
    async def test_stabilization_pause(self):
        """Verify 100ms pause between movement and capture"""
        
    async def test_frame_metadata(self):
        """Verify captured frames have correct metadata"""
        
    async def test_return_to_neutral(self):
        """Verify head returns to 0,0 after sequence"""
```

### Integration Tests

```python
async def test_end_to_end_capture_sequence(reachy_sim):
    """
    Full sequence test:
    1. Initialize controller
    2. Trigger capture
    3. Verify 5 frames captured
    4. Verify total time <10 seconds
    5. Verify head at neutral after
    """
    
async def test_repeated_sequences(reachy_sim):
    """Run 10 consecutive sequences, verify no errors or degradation"""
```

### Manual Testing Checklist

- [ ] Run sequence on real Reachy Mini hardware
- [ ] Verify head movements visually smooth
- [ ] Measure total time with stopwatch (<10 sec)
- [ ] Check captured frames display correctly
- [ ] Test with different config angle sets (3 angles, 7 angles)
- [ ] Verify no motor overheating after 10 runs

## Definition of Done

- [ ] Code implemented in `src/vision/multi_angle_capture.py`
- [ ] Configuration file created at `src/config/multi_angle_capture.yaml`
- [ ] Unit tests pass (>90% coverage on new code)
- [ ] Integration tests pass on Reachy SIM
- [ ] Manual test passes on real hardware
- [ ] Performance validated: <10 sec total sequence time
- [ ] Code reviewed and merged to main branch
- [ ] Documentation added to module docstrings

## Open Questions / Blockers

- **Q1:** Should we support simultaneous pitch+yaw movement, or sequential?
  - **Decision:** Sequential for simplicity in MVP, optimize later if needed
  
- **Q2:** What happens if movement times out (>2 sec per angle)?
  - **Decision:** Log error, skip that angle, continue to next
  
- **Q3:** Should we add a "preview mode" to visualize angles before capture?
  - **Decision:** Nice-to-have, defer to Story 1.3 or future iteration

## Dependencies

### Prerequisites (Must Complete First)
- ✅ Story 1.2 - Reachy SIM Connection (motor control working)
- ✅ Story 1.3 - Camera Input Pipeline (frame capture working)

### Blocked By
- None (ready to start)

### Blocks
- Story 1.2 - Frame Quality Assessment (needs captured frames)
- Story 1.3 - Best Frame Selection (needs captured frames)

## Estimated Effort

- **Implementation:** 3 hours
- **Testing:** 2 hours
- **Documentation:** 1 hour
- **Total:** 6 hours (1-2 days)

## Success Metrics

### Quantitative
- Capture sequence completes in <10 seconds (100% of runs)
- Head reaches target angles within ±2° tolerance (>95% of movements)
- Zero motor errors in 10 consecutive runs
- 5 frames captured per sequence (100% success rate)

### Qualitative
- Movement appears smooth and natural (human observer assessment)
- No jarring or jerky motion (developer judgment)
- Frames visually distinct across angles (visual inspection)

## Related Resources

- [Reachy SDK Motor Control Guide](https://docs.pollen-robotics.com/sdk/motor-control/)
- [PRD Section 4.1.1: FR-MAC-1 Head Movement Control](./prd.md#fr-mac-1-head-movement-control)
- [Epic 1: Multi-Angle Capture System](./epic-1-multi-angle-capture.md)

---

**Created:** 2025-11-14  
**Last Updated:** 2025-11-14  
**Version:** 1.0  
**Ready for Development:** ✅
