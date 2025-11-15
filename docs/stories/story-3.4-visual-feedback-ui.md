# Story 3.4: Visual Feedback & UI Integration

**Epic:** Epic 3 - Gesture Control System  
**Story Points:** 5  
**Status:** Planning Complete  
**Assigned:** Dev Agent  
**Created:** November 15, 2025

---

## Story Description

**As a** store manager using Reachy Mini's gesture control  
**I want** immediate visual confirmation when my gesture is recognized  
**So that** I know the system detected my command without looking away from my work

---

## Acceptance Criteria

- [ ] On-screen icon displays detected gesture (emoji: 👍👋✋)
- [ ] Icon appears within 0.2 seconds of gesture recognition
- [ ] Brief animation (fade-in, pulse, fade-out over 1 second)
- [ ] Screen returns to normal state after confirmation
- [ ] Icons clearly visible from 3 meters
- [ ] No UI blocking (non-modal overlay)
- [ ] Smooth 30 FPS animation
- [ ] Thread-safe implementation

---

## Technical Requirements

### Performance Targets
- **Display Latency:** < 200ms from gesture detection to icon display
- **Animation FPS:** 30 FPS minimum
- **Total Duration:** 1.0 second (fade-in + pulse + fade-out)
- **Resource Usage:** Non-blocking, separate thread for animation

### Dependencies
- **Input:** `GestureResult` from `GestureRecognizer`
- **Output:** Visual overlay on camera frame or separate display
- **Libraries:** OpenCV (rendering), Pillow (emoji/text), threading

### Integration Points
- Called by `GestureCoordinator` after gesture validation
- Renders over camera feed or on separate UI canvas
- Thread-safe for concurrent gesture events

---

## Implementation Design

### File Structure

```
src/ui/
└── feedback_manager.py         # NEW (300-350 lines)
    ├── FeedbackAnimation (enum)
    ├── FeedbackState (dataclass)
    └── FeedbackManager (class)

src/config/
└── feedback_ui.yaml            # NEW (~80 lines)

tests/
├── test_story_3_4_feedback_ui.py        # NEW (18 tests)
└── test_story_3_4_integration.py        # NEW (5 tests)
```

### Key Components

#### 1. FeedbackAnimation Enum
```python
class FeedbackAnimation(Enum):
    FADE_IN = "fade_in"       # 0.0-0.2s: alpha 0→1
    PULSE = "pulse"           # 0.2-0.8s: scale 1.0→1.2→1.0
    FADE_OUT = "fade_out"     # 0.8-1.0s: alpha 1→0
    COMPLETE = "complete"     # Animation finished
```

#### 2. FeedbackState Dataclass
```python
@dataclass
class FeedbackState:
    gesture_type: GestureType
    icon: str                          # Emoji character
    animation_phase: FeedbackAnimation
    start_time: float
    elapsed_time: float
    alpha: float                       # Transparency 0-1
    scale: float                       # Size multiplier
    position: Tuple[int, int]          # (x, y) on screen
```

#### 3. FeedbackManager Class

**Initialization:**
- `__init__(config_path=None, display_duration=1.0, icon_size=200, position="center")`
- `_load_config()` - Load YAML configuration
- `_initialize_display()` - Setup rendering canvas
- `_start_animation_thread()` - Launch non-blocking animation loop

**Core Methods:**
- `show_gesture_feedback(gesture_result: GestureResult) -> None`
  - Main entry point, triggers visual feedback
  - Non-blocking, returns immediately
  - Queues animation in separate thread

- `_render_frame(overlay: np.ndarray) -> np.ndarray`
  - Draw current animation frame
  - Returns overlay image to composite on camera feed

- `_get_icon_for_gesture(gesture_type: GestureType) -> str`
  - Map gesture type to emoji icon
  - THUMBS_UP → "👍", WAVE → "👋", PALM_STOP → "✋"

- `_update_animation_state(state: FeedbackState) -> FeedbackState`
  - Advance animation phase based on elapsed time
  - Calculate alpha and scale for current phase

**Animation Phase Methods:**
- `_animate_fade_in(state: FeedbackState) -> FeedbackState`
  - Duration: 0.0-0.2s
  - Alpha: 0 → 1 (linear)
  - Scale: 0.8 → 1.0 (ease-out)

- `_animate_pulse(state: FeedbackState) -> FeedbackState`
  - Duration: 0.2-0.8s
  - Alpha: 1.0 (constant)
  - Scale: 1.0 → 1.2 → 1.0 (sine wave)

- `_animate_fade_out(state: FeedbackState) -> FeedbackState`
  - Duration: 0.8-1.0s
  - Alpha: 1 → 0 (linear)
  - Scale: 1.0 → 1.2 (continue scaling)

**Rendering Methods:**
- `_draw_icon(canvas, icon, position, alpha, scale) -> np.ndarray`
  - Render emoji character at position
  - Apply transparency (alpha) and scaling
  - Use Pillow for text rendering (OpenCV lacks emoji support)

- `_draw_background(canvas, position, alpha, scale) -> np.ndarray`
  - Optional: Draw semi-transparent circle behind icon
  - Configurable background color and radius

- `_apply_overlay(frame, overlay) -> np.ndarray`
  - Composite overlay onto camera frame
  - Alpha blending for smooth transparency

**Thread Management:**
- `_animation_thread() -> None`
  - Runs in separate thread
  - Processes animation queue
  - Updates FeedbackState at 30 FPS

- `start() -> None`
  - Start animation thread
  - Called during initialization

- `stop() -> None`
  - Gracefully stop animation thread
  - Wait for current animation to complete

- `cleanup() -> None`
  - Release resources
  - Close display windows

**Statistics:**
- `get_statistics() -> dict`
  - Animation count
  - Average display latency
  - Dropped frames

- `reset_statistics() -> None`
  - Clear stats

---

## Configuration

### feedback_ui.yaml

```yaml
feedback_ui:
  # Animation settings
  animation:
    total_duration_seconds: 1.0
    fade_in_duration: 0.2       # Seconds
    pulse_duration: 0.6         # Seconds
    fade_out_duration: 0.2      # Seconds
  
  # Visual settings
  icons:
    thumbs_up: "👍"
    wave: "👋"
    palm_stop: "✋"
    size_pixels: 200            # Base icon size
    scale_pulse_max: 1.2        # Maximum scale during pulse
  
  # Display position
  position:
    x: "center"                 # "center", "left", "right", or pixel value
    y: "center"                 # "center", "top", "bottom", or pixel value
    offset_x: 0                 # Horizontal offset from position
    offset_y: -50               # Vertical offset (negative = up)
  
  # Colors (RGBA format)
  colors:
    icon_color: [255, 255, 255, 255]       # White icon
    background_color: [0, 0, 0, 128]       # Semi-transparent black
    background_enabled: true               # Draw circle behind icon
    background_radius: 120                 # Circle radius in pixels
  
  # Performance
  target_latency_ms: 200        # Max latency from gesture to display
  frame_rate: 30                # Animation FPS
  max_queue_size: 3             # Max pending animations
```

---

## Animation Timeline

### Total Duration: 1.0 second

```
Time (s) │ Phase      │ Alpha │ Scale │ Description
─────────┼────────────┼───────┼───────┼─────────────────────────
0.0-0.2  │ FADE_IN    │ 0→1   │ 0.8→1.0│ Icon appears, grows
0.2-0.8  │ PULSE      │ 1.0   │ 1.0→1.2→1.0│ Icon pulses (attention)
0.8-1.0  │ FADE_OUT   │ 1→0   │ 1.0→1.2│ Icon disappears, grows
1.0+     │ COMPLETE   │ 0     │ 1.2   │ Animation finished
```

### Interpolation Functions

**Fade-in (0.0-0.2s):**
- Alpha: `t / 0.2` (linear)
- Scale: `0.8 + 0.2 * ease_out(t / 0.2)` (ease-out cubic)

**Pulse (0.2-0.8s):**
- Alpha: `1.0` (constant)
- Scale: `1.0 + 0.2 * sin(π * (t - 0.2) / 0.6)` (sine wave)

**Fade-out (0.8-1.0s):**
- Alpha: `1.0 - (t - 0.8) / 0.2` (linear)
- Scale: `1.0 + 0.2 * (t - 0.8) / 0.2` (linear)

---

## Rendering Approach

### Option 1: Overlay on Camera Feed (Recommended)
- Render emoji on transparent overlay
- Composite over camera frame before display
- Pros: Single display, integrated UX
- Cons: Requires access to camera frame buffer

### Option 2: Separate UI Window
- Create OpenCV window for feedback
- Display emoji in standalone window
- Pros: Simple implementation, independent
- Cons: Two windows, less integrated

### Option 3: Web Dashboard (Future)
- Render in HTML/CSS via Flask endpoint
- Display in browser or embedded webview
- Pros: Rich styling, responsive design
- Cons: More complex, network latency

**Selected:** Option 1 for MVP (overlay on camera feed)

---

## Emoji Rendering with Pillow

OpenCV doesn't support emoji rendering directly. Use Pillow:

```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def render_emoji(emoji: str, size: int, color: tuple) -> np.ndarray:
    """Render emoji character using Pillow, return as numpy array."""
    # Create PIL image
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Use system emoji font (platform-dependent)
    # Windows: Segoe UI Emoji
    # macOS: Apple Color Emoji
    # Linux: Noto Color Emoji
    font = ImageFont.truetype("seguiemj.ttf", size=int(size * 0.8))
    
    # Draw emoji centered
    bbox = draw.textbbox((0, 0), emoji, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size - text_width) // 2, (size - text_height) // 2)
    draw.text(position, emoji, font=font, fill=color, embedded_color=True)
    
    # Convert to numpy array
    return np.array(img)
```

**Platform-Specific Font Paths:**
- Windows: `C:\Windows\Fonts\seguiemj.ttf` (Segoe UI Emoji)
- macOS: `/System/Library/Fonts/Apple Color Emoji.ttc`
- Linux: `/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf`

**Fallback:** If emoji font not found, use colored circles with letters (T, W, P)

---

## Testing Strategy

### Unit Tests (18 tests)

**Icon Mapping (3 tests):**
- `test_icon_mapping_thumbs_up()` - THUMBS_UP → "👍"
- `test_icon_mapping_wave()` - WAVE → "👋"
- `test_icon_mapping_palm_stop()` - PALM_STOP → "✋"

**Animation State Transitions (5 tests):**
- `test_fade_in_phase()` - Alpha 0→1, scale 0.8→1.0
- `test_pulse_phase()` - Scale oscillation 1.0→1.2→1.0
- `test_fade_out_phase()` - Alpha 1→0, scale 1.0→1.2
- `test_phase_progression()` - Automatic phase transitions
- `test_animation_completion()` - COMPLETE phase reached at 1.0s

**Rendering (4 tests):**
- `test_render_emoji()` - Emoji rendered at correct size
- `test_render_background()` - Optional circle background
- `test_alpha_blending()` - Transparency applied correctly
- `test_position_calculation()` - Center/offset positioning

**Performance (3 tests):**
- `test_display_latency()` - <200ms from gesture to render
- `test_animation_fps()` - Smooth 30 FPS
- `test_thread_safety()` - Concurrent gestures handled

**Configuration (3 tests):**
- `test_load_config()` - YAML parsing
- `test_custom_icons()` - Override default emojis
- `test_custom_colors()` - Override colors

### Integration Tests (5 tests)

**End-to-End Display (2 tests):**
- `test_end_to_end_feedback()` - GestureResult → visual feedback
- `test_multiple_gestures()` - Queue multiple animations

**Coordination (2 tests):**
- `test_coordinator_integration()` - GestureCoordinator triggers feedback
- `test_event_system_integration()` - EventManager callback

**Performance (1 test):**
- `test_total_latency()` - <1s gesture → feedback → action

### Mock Strategy

**Mock Components:**
- Camera frame: Use synthetic 640x480 numpy array
- Display: Capture rendered frames to list (no actual window)
- Font: Use fallback rendering if emoji font unavailable
- Time: Use controlled time advancement for animation tests

**Test Fixtures:**
```python
@pytest.fixture
def feedback_manager():
    """Create FeedbackManager with test config."""
    config = {
        'animation': {'total_duration_seconds': 1.0},
        'icons': {'size_pixels': 200},
        'position': {'x': 'center', 'y': 'center'}
    }
    return FeedbackManager(config=config, headless=True)

@pytest.fixture
def mock_gesture_result():
    """Create mock GestureResult for testing."""
    return GestureResult(
        gesture_type=GestureType.THUMBS_UP,
        confidence=0.95,
        hand_id="hand_0",
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.6,
        distance_estimate=2.0,
        timestamp=time.time(),
        processing_time_ms=45.0
    )
```

---

## Implementation Checklist

### Phase 1: Core Implementation
- [ ] Create `src/ui/` directory
- [ ] Create `feedback_manager.py` with dataclasses
- [ ] Implement FeedbackManager class skeleton
- [ ] Implement animation phase methods
- [ ] Implement emoji rendering with Pillow
- [ ] Add configuration loading

### Phase 2: Animation System
- [ ] Implement animation thread
- [ ] Implement animation queue
- [ ] Implement frame rendering loop
- [ ] Add alpha blending
- [ ] Add scale transformation

### Phase 3: Configuration
- [ ] Create `feedback_ui.yaml`
- [ ] Document all configuration options
- [ ] Add validation for config values

### Phase 4: Testing
- [ ] Write 18 unit tests
- [ ] Write 5 integration tests
- [ ] Run all tests, ensure 23/23 passing
- [ ] Validate performance targets (<200ms, 30 FPS)

### Phase 5: Documentation & Integration
- [ ] Add docstrings to all classes/methods
- [ ] Update `bmm-workflow-status.md`
- [ ] Test integration with GestureCoordinator
- [ ] Commit Story 3.4

---

## Performance Validation

### Latency Breakdown

Target: < 200ms from gesture detection to display

```
Component                    Target    Notes
─────────────────────────────────────────────────────────────
Gesture validation          50ms      From GestureRecognizer
Coordinator dispatch        20ms      GestureCoordinator
Feedback trigger            10ms      Method call overhead
Emoji rendering             80ms      Pillow text rendering
Overlay compositing         30ms      Alpha blending
Display update              10ms      Frame buffer write
─────────────────────────────────────────────────────────────
Total                       200ms     Maximum acceptable
```

### Memory Usage

```
Component                    Memory    Notes
─────────────────────────────────────────────────────────────
Emoji image (200x200 RGBA)  160KB     Per icon, cached
Animation state             <1KB      FeedbackState instance
Frame overlay (640x480)     1.2MB     Temporary buffer
Total per animation         ~1.4MB    Acceptable on Pi5 (8GB)
```

---

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Emoji font missing | High | Medium | Fallback to colored circles with letters |
| Rendering too slow | Medium | Medium | Cache rendered emojis, reduce size |
| Thread synchronization bugs | Medium | Low | Use thread-safe queue, proper locks |
| Animation stuttering | Low | Medium | Prioritize animation thread, reduce FPS if needed |
| Overlay blocks camera view | Low | Low | Use semi-transparent background, short duration |

---

## Success Metrics

- ✅ 23/23 tests passing (18 unit + 5 integration)
- ✅ Display latency < 200ms (measured in tests)
- ✅ Animation FPS ≥ 30 (smooth transitions)
- ✅ Icons visible from 3 meters (manual test)
- ✅ No blocking (non-modal overlay)
- ✅ Thread-safe (concurrent gestures)

---

## Next Steps After Story 3.4

1. **Epic 3 Complete:** All 4 stories done (26/26 points)
2. **Integration Testing:** Test full gesture pipeline
3. **Epic 4 Planning:** Integration & Testing epic
4. **Field Testing:** Validate with store managers

---

## References

- **Epic 3 Plan:** `docs/epic-3-gesture-control-plan.md`
- **Story 3.3:** Gesture-to-Command Mapping (upstream)
- **MediaPipe Hands:** Hand landmark documentation
- **Pillow Docs:** https://pillow.readthedocs.io/

---

**Status:** Ready for Implementation  
**Estimated Duration:** 2 days  
**Complexity:** Medium (emoji rendering, threading)  
**Dependencies:** Story 3.3 complete ✅

**Command to Start:** `*develop` (Story 3.4)

