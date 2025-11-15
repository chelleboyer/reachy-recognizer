# Story 2.1: Person Detection with Torso ROI

**Epic:** Epic 2 - Uniform Recognition System  
**Story Points:** 5  
**Priority:** P0 (Must Have)  
**Status:** Ready for Development

---

## Story Description

**As a** Reachy Mini robot  
**I want to** detect people in camera frames and extract their torso regions  
**So that** I can analyze uniform patterns for staff identification

---

## Acceptance Criteria

### AC1: YOLOv8n Integration
- [ ] YOLOv8n person detector integrated and running
- [ ] Model loaded from local file or downloaded automatically
- [ ] Inference runs on Pi5 (no GPU required for nano model)
- [ ] Detection confidence configurable via YAML config

### AC2: Torso ROI Extraction
- [ ] Torso bounding box extracted from person detection
- [ ] ROI is upper 50-70% of person bbox (configurable)
- [ ] ROI centered horizontally within person bbox
- [ ] Invalid ROIs (too small, out of bounds) filtered out

### AC3: ROI Preprocessing
- [ ] ROI resized to standard size (224x224 default)
- [ ] Pixel values normalized (0-255 → 0-1 or -1 to 1)
- [ ] Preprocessing configurable (resize size, normalization method)

### AC4: Confidence Threshold
- [ ] Configurable detection confidence threshold (default 0.7)
- [ ] Only detections above threshold processed
- [ ] Low-confidence detections logged for debugging

### AC5: Multiple People Handling
- [ ] All person detections in frame processed
- [ ] Each person gets unique ID for tracking
- [ ] Results returned as list of TorsoROI objects

### AC6: Unit Tests
- [ ] Test ROI extraction with various bbox sizes
- [ ] Test preprocessing (resize, normalize)
- [ ] Test confidence filtering
- [ ] Test edge cases (no detections, bbox at frame edge)

### AC7: Integration Test
- [ ] End-to-end test with real camera frame
- [ ] Synthetic test with mock person bboxes
- [ ] Performance test (<200ms per frame target)

---

## Technical Specification

### Input
```python
# Camera frame from Epic 1
frame: np.ndarray  # (H, W, 3) RGB image
config: PersonDetectionConfig  # Detection parameters
```

### Output
```python
@dataclass
class TorsoROI:
    """Extracted torso region of interest."""
    person_bbox: Tuple[int, int, int, int]  # x, y, width, height (full person)
    torso_bbox: Tuple[int, int, int, int]  # x, y, width, height (torso only)
    torso_image: np.ndarray  # (224, 224, 3) preprocessed ROI
    confidence: float  # Detection confidence (0-1)
    person_id: str  # Unique ID for this detection
    frame_id: str  # Source frame identifier
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for logging."""
        pass
```

### Configuration
```yaml
# person_detection.yaml
person_detection:
  model:
    name: "yolov8n"  # Nano variant for speed
    confidence_threshold: 0.7
    iou_threshold: 0.5
    device: "cpu"  # Pi5 doesn't have CUDA
    
  torso_extraction:
    vertical_range: [0.0, 0.6]  # Top 60% of person bbox
    horizontal_center: true  # Center horizontally
    min_width: 50  # Minimum valid torso width (pixels)
    min_height: 80  # Minimum valid torso height (pixels)
    
  preprocessing:
    resize_size: [224, 224]
    normalization: "standard"  # "standard" (0-1) or "imagenet" (-1 to 1)
    interpolation: "bilinear"
    
  performance:
    max_detections: 10  # Max people per frame
    batch_processing: false  # Process frames individually
```

### API Design

```python
class PersonDetector:
    """Detect people and extract torso ROIs."""
    
    def __init__(self, config_path: str = "src/config/person_detection.yaml"):
        """Initialize detector with YOLOv8n model."""
        self.config = self._load_config(config_path)
        self.model = self._load_yolo_model()
        self.detection_count = 0
        
    def detect_people(
        self, 
        frame: np.ndarray, 
        frame_id: str
    ) -> List[TorsoROI]:
        """
        Detect people in frame and extract torso ROIs.
        
        Args:
            frame: Input RGB image (H, W, 3)
            frame_id: Unique frame identifier
            
        Returns:
            List of TorsoROI objects, one per detected person
            
        Raises:
            ValueError: If frame is None or empty
        """
        pass
        
    def _extract_torso_roi(
        self, 
        frame: np.ndarray, 
        person_bbox: Tuple[int, int, int, int],
        confidence: float,
        person_id: str,
        frame_id: str
    ) -> Optional[TorsoROI]:
        """Extract and preprocess torso region from person bbox."""
        pass
        
    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """Resize and normalize ROI."""
        pass
        
    def get_statistics(self) -> dict:
        """Return detection statistics."""
        return {
            'total_detections': self.detection_count,
            'model_name': self.config['model']['name'],
            'avg_confidence': self.avg_confidence
        }
        
    def reset_statistics(self):
        """Reset detection counters."""
        pass


# Convenience function
def detect_people_quick(
    frame: np.ndarray, 
    frame_id: str = "frame_0"
) -> List[TorsoROI]:
    """Quick person detection with default config."""
    detector = PersonDetector()
    return detector.detect_people(frame, frame_id)
```

---

## Implementation Notes

### YOLOv8n Model Details
- **Size:** ~3.2MB (nano variant)
- **Speed:** ~30-50 FPS on Pi5 (640x640 input)
- **Accuracy:** mAP@50 ~37% on COCO (sufficient for person detection)
- **Installation:** `pip install ultralytics>=8.0.0`

### Torso ROI Heuristic
```python
def calculate_torso_bbox(person_bbox):
    """
    Extract torso from person bbox.
    
    Heuristic: Take top 60% of person height, centered horizontally.
    This captures chest/vest area while excluding head and legs.
    """
    x, y, w, h = person_bbox
    
    # Torso is top 60% of person
    torso_height = int(h * 0.6)
    torso_y = y
    
    # Keep same horizontal center
    torso_x = x
    torso_width = w
    
    return (torso_x, torso_y, torso_width, torso_height)
```

### Performance Optimization
- Use YOLOv8n (smallest variant) for speed
- Run inference at 640x640 (not 1280x1280)
- Process single frame at a time (no batching overhead)
- Cache model in memory (don't reload per frame)

---

## Testing Strategy

### Unit Tests (`tests/test_story_2_1_person_detection.py`)

```python
class TestPersonDetector:
    - test_load_config()
    - test_missing_config_raises_error()
    - test_yolo_model_loads()
    
class TestTorsoExtraction:
    - test_extract_torso_from_person_bbox()
    - test_torso_centered_horizontally()
    - test_torso_top_60_percent()
    - test_invalid_bbox_returns_none()
    - test_bbox_at_frame_edge()
    
class TestPreprocessing:
    - test_resize_to_224x224()
    - test_normalize_0_to_1()
    - test_normalize_imagenet()
    
class TestConfidenceFiltering:
    - test_only_high_confidence_detections()
    - test_configurable_threshold()
    
class TestMultiplePeople:
    - test_multiple_detections_returned()
    - test_unique_person_ids()
    - test_max_detections_limit()
```

### Integration Tests (`tests/test_story_2_1_integration.py`)

```python
class TestEndToEndDetection:
    - test_detect_people_real_frame()
    - test_detect_people_synthetic_frame()
    - test_no_people_returns_empty_list()
    - test_performance_under_200ms()
    
class TestCameraIntegration:
    - test_detect_from_epic1_capture()  # Integration with Story 1.1
```

---

## Definition of Done

- [ ] PersonDetector class implemented
- [ ] TorsoROI dataclass implemented
- [ ] Configuration YAML created
- [ ] YOLOv8n integrated and tested
- [ ] 15+ unit tests passing
- [ ] 5+ integration tests passing
- [ ] Performance target met (<200ms per frame)
- [ ] Code reviewed for privacy compliance (no face extraction)
- [ ] Documentation updated (API docs, usage examples)

---

## Dependencies

### Python Packages
- `ultralytics>=8.0.0` (YOLOv8)
- `opencv-python` (already installed from Epic 1)
- `numpy` (already installed)
- `pyyaml` (already installed)

### Hardware
- Pi5 with camera (available from Epic 1)

### Prior Work
- Epic 1: Camera capture system provides input frames

---

## Estimated Effort

**5 Story Points** = ~1-2 days

- YOLOv8 integration: 0.5 days
- Torso extraction logic: 0.5 days
- Preprocessing pipeline: 0.25 days
- Unit tests: 0.5 days
- Integration tests: 0.25 days

---

**Story Created:** 2025-11-15  
**Ready for Development:** Yes  
**Assigned Agent:** dev
