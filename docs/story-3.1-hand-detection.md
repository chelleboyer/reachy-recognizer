# Story 3.1: MediaPipe Hand Detection Setup

**Epic:** Epic 3 - Gesture Control System  
**Story Points:** 3  
**Priority:** P0 (Must Have)  
**Status:** ✅ Complete (2025-11-15)

---

## Story Description

**As a** Reachy Mini robot  
**I want to** detect hands in camera frames using MediaPipe  
**So that** I can recognize gestures for command input

---

## Acceptance Criteria

### AC1: MediaPipe Hands Integration ✅
- [x] MediaPipe Hands library integrated
- [x] Hand detection model loaded and initialized
- [x] Detection runs on CPU (Pi5 compatible)
- [x] Configurable detection parameters (confidence, model complexity)

### AC2: Hand Landmark Extraction ✅
- [x] Extract 21 hand landmarks per detected hand
- [x] Landmarks include normalized coordinates (0-1 range)
- [x] World landmarks included for distance estimation
- [x] Left/right hand differentiation working

### AC3: HandLandmarks Data Structure ✅
- [x] HandLandmarks dataclass with all required fields
- [x] hand_id field for tracking
- [x] handedness field ("Left" or "Right")
- [x] landmarks list (21 x/y/z tuples)
- [x] world_landmarks list (21 3D coordinates in meters)
- [x] confidence score included
- [x] timestamp field for temporal processing

### AC4: Performance Metrics ✅
- [x] Target: 10+ FPS on Pi5
- [x] Latency tracking per frame
- [x] Detection count statistics
- [x] FPS calculation and logging

### AC5: Configuration ✅
- [x] hand_detection.yaml config file
- [x] MediaPipe parameters (model_complexity, min_detection_confidence, min_tracking_confidence)
- [x] Performance settings (target_fps, max_num_hands)
- [x] Output settings (include_world_landmarks, normalize_coordinates)
- [x] Debug settings (enable_logging, log_level)

### AC6: Unit Tests ✅
- [x] Test HandLandmarks dataclass creation
- [x] Test HandDetector initialization
- [x] Test single-hand detection with mock frames
- [x] Test multi-hand detection (left + right)
- [x] Test performance tracking
- [x] Test configuration loading
- [x] Test error handling (invalid config, no hands detected)
- **Result:** 15/15 unit tests passing

### AC7: Integration Tests ✅
- [x] End-to-end detection with synthetic frames
- [x] Performance validation (<100ms per frame)
- [x] Multi-hand scenario testing
- [x] Context manager resource cleanup
- [x] Left/right hand differentiation validation
- **Result:** 9/9 integration tests passing

---

## Technical Specification

### Input
```python
# Camera frame
frame: np.ndarray  # (H, W, 3) RGB image
config_path: str  # Path to hand_detection.yaml
```

### Output
```python
@dataclass
class HandLandmarks:
    """Represents detected hand landmarks from MediaPipe."""
    hand_id: int
    handedness: str  # "Left" or "Right"
    landmarks: List[Tuple[float, float, float]]  # 21 landmarks (x, y, z)
    world_landmarks: List[Tuple[float, float, float]]  # 21 landmarks in meters
    confidence: float  # Detection confidence (0.0-1.0)
    timestamp: float  # Unix timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        ...
```

### HandDetector Class
```python
class HandDetector:
    """MediaPipe-based hand detector."""
    
    def __init__(self, config_path: str):
        """Initialize detector with config."""
        ...
    
    def detect(self, frame: np.ndarray) -> List[HandLandmarks]:
        """Detect hands in frame."""
        ...
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get FPS, latency, detection counts."""
        ...
    
    def reset_statistics(self):
        """Reset performance tracking."""
        ...
    
    def __enter__(self) / __exit__():
        """Context manager for resource cleanup."""
        ...
```

---

## Implementation Details

### Files Created
1. **src/vision/hand_detector.py** (~350 lines)
   - HandLandmarks dataclass
   - HandDetector class with MediaPipe integration
   - Performance tracking and statistics
   - Context manager support

2. **src/config/hand_detection.yaml** (~60 lines)
   - MediaPipe configuration (model_complexity: 0, min_detection_confidence: 0.7)
   - Performance settings (target_fps: 15, max_num_hands: 2)
   - Output settings (include_world_landmarks: true)
   - Debug settings (enable_logging: false)

3. **tests/test_story_3_1_hand_detection.py** (~400 lines)
   - 15 unit tests covering all components
   - Mock fixtures for frames and landmarks
   - Performance validation tests

4. **tests/test_story_3_1_integration.py** (~350 lines)
   - 9 integration tests
   - End-to-end detection scenarios
   - Multi-hand validation
   - Resource cleanup verification

### Key Features
- **MediaPipe Hands Integration:** Uses model_complexity=0 for Pi5 performance
- **21 Landmark Points:** Full hand skeleton including palm, fingers, wrist
- **World Coordinates:** 3D landmarks in meters for distance estimation
- **Left/Right Detection:** Automatic handedness classification
- **Performance Tracking:** FPS, latency, detection counts
- **Context Manager:** Automatic resource cleanup

### Performance Results
- **FPS:** 10+ FPS achieved on test hardware
- **Latency:** <100ms per frame
- **Accuracy:** Robust detection with 0.7 confidence threshold
- **Memory:** Efficient with single model instance

---

## Dependencies

```toml
[project.dependencies]
mediapipe = ">=0.10.8"
opencv-python = ">=4.8.0"
numpy = ">=1.24.0"
pyyaml = ">=6.0"
```

---

## Configuration Reference

### hand_detection.yaml
```yaml
# MediaPipe Hands Configuration
mediapipe:
  model_complexity: 0  # 0=fast, 1=balanced (use 0 for Pi5)
  min_detection_confidence: 0.7  # 0.0-1.0
  min_tracking_confidence: 0.5  # 0.0-1.0
  static_image_mode: false  # false=video mode (tracking)

# Performance Settings
performance:
  target_fps: 15
  max_num_hands: 2  # Detect up to 2 hands

# Output Settings
output:
  include_world_landmarks: true
  normalize_coordinates: true

# Debug Settings
debug:
  enable_logging: false
  log_level: "INFO"
```

---

## Testing Summary

### Unit Tests (15 passing)
- TestHandLandmarks: dataclass creation, to_dict()
- TestHandDetectorInit: config loading, parameter validation
- TestHandDetection: single hand, multiple hands, no hands
- TestPerformanceTracking: FPS, latency, statistics
- TestContextManager: resource cleanup

### Integration Tests (9 passing)
- End-to-end detection with synthetic frames
- Multi-hand scenarios (left + right)
- Performance validation (<100ms target)
- Left/right hand differentiation
- Context manager resource cleanup

**Total:** 24/24 tests passing ✅

---

## Usage Example

```python
from src.vision.hand_detector import HandDetector
import cv2

# Initialize detector
detector = HandDetector("src/config/hand_detection.yaml")

# Detect hands in frame
frame = cv2.imread("test_frame.jpg")
hands = detector.detect(frame)

# Process results
for hand in hands:
    print(f"Detected {hand.handedness} hand (confidence: {hand.confidence:.2f})")
    print(f"  Landmarks: {len(hand.landmarks)} points")
    print(f"  World coordinates available: {len(hand.world_landmarks)} points")

# Get performance stats
stats = detector.get_performance_stats()
print(f"FPS: {stats['fps']:.1f}, Latency: {stats['avg_latency_ms']:.1f}ms")

# Cleanup
detector.close()
```

---

## Next Steps

Story 3.2: Three-Gesture Recognition (13 points)
- Build on HandLandmarks output from Story 3.1
- Implement thumbs up, wave, and palm stop gesture detection
- Add temporal validation and false positive prevention

---

_Story completed: 2025-11-15_  
_Implementation: src/vision/hand_detector.py (~350 lines)_  
_Tests: 24 passing (15 unit + 9 integration)_  
_Commit: 51cc162_
