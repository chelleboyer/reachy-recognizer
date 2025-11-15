# Story 1.2: Frame Quality Assessment

**Story ID:** STORY-1.2  
**Epic:** [Epic 1 - Multi-Angle Capture System](./epic-1-multi-angle-capture.md)  
**Status:** BLOCKED (Requires Story 1.1)  
**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Assigned To:** dev agent  
**Sprint:** Week 1, Days 3-4

---

## User Story

**As a** system  
**I want** to automatically assess each frame for glare and blur  
**So that** I can select the clearest image for product detection

## Business Context

Not all angles produce clear frames - glare, blur, and occlusion vary by angle. Automated quality assessment eliminates manual review and ensures the best frame is used for OCR/detection.

**System Need:** "Don't waste OCR processing on unreadable frames"

**Value Delivered:** Intelligent frame ranking enables optimal frame selection, improving OCR success rate by 40%+

## Acceptance Criteria

### AC1: Glare Detection
- [ ] Glare detection algorithm analyzes brightness distribution
- [ ] Detects localized bright spots (>200 pixel value in BGR)
- [ ] Computes glare score: 0 (no glare) to 100 (severe glare)
- [ ] Glare threshold configurable in YAML (default: 70)

### AC2: Blur Detection
- [ ] Blur detection uses Laplacian variance method
- [ ] Computes blur score: 0 (severe blur) to 100 (sharp focus)
- [ ] Blur threshold configurable in YAML (default: 50)
- [ ] Processes 640x480 frame in <100ms

### AC3: Composite Quality Score
- [ ] Overall quality score combines glare and blur metrics
- [ ] Formula: `quality = (100 - glare_score) * 0.5 + blur_score * 0.5`
- [ ] Quality score range: 0 (worst) to 100 (best)
- [ ] Weights configurable in YAML

### AC4: Quality Metadata
- [ ] Each frame tagged with quality metrics (JSON):
  ```json
  {
    "quality_score": 75.3,
    "glare_score": 45.0,
    "blur_score": 82.0,
    "has_glare": false,
    "is_blurry": false,
    "timestamp": 1699920000.123
  }
  ```
- [ ] Low-quality frames flagged (<40 score)
- [ ] Metrics logged for analysis

### AC5: Performance
- [ ] Quality assessment completes in <100ms per frame
- [ ] Processes 5 frames (full sequence) in <500ms total
- [ ] No memory leaks during 100 consecutive assessments

## Technical Implementation

### Module: `src/vision/frame_quality.py`

#### Class: `FrameQualityAssessor`

**Purpose:** Analyze captured frames for glare, blur, and overall quality

**Key Methods:**

```python
class FrameQualityAssessor:
    def __init__(self, config_path: str):
        """
        Initialize assessor with quality thresholds from config
        
        Args:
            config_path: Path to YAML config
        """
        
    def assess_frame(self, frame: np.ndarray) -> QualityMetrics:
        """
        Analyze single frame for quality metrics
        
        Args:
            frame: Input image (BGR format)
            
        Returns:
            QualityMetrics with scores and flags
        """
        
    def _compute_glare_score(self, frame: np.ndarray) -> float:
        """
        Detect glare using brightness analysis
        
        Algorithm:
        1. Convert to grayscale
        2. Find bright regions (>200 pixel value)
        3. Calculate percentage of frame with glare
        4. Return score: 0 (no glare) to 100 (severe)
        """
        
    def _compute_blur_score(self, frame: np.ndarray) -> float:
        """
        Detect blur using Laplacian variance
        
        Algorithm:
        1. Convert to grayscale
        2. Apply Laplacian operator
        3. Calculate variance of result
        4. Normalize to 0-100 scale
        """
        
    def _compute_quality_score(self, glare: float, blur: float) -> float:
        """Combine glare and blur into composite quality score"""
        
    def assess_sequence(self, frames: List[CapturedFrame]) -> List[QualityMetrics]:
        """Batch assess all frames in capture sequence"""
```

#### Data Models:

```python
@dataclass
class QualityMetrics:
    quality_score: float       # Overall score 0-100
    glare_score: float         # Glare intensity 0-100
    blur_score: float          # Focus sharpness 0-100
    has_glare: bool            # True if glare_score > threshold
    is_blurry: bool            # True if blur_score < threshold
    timestamp: float           # When assessed
    frame_id: str              # Reference to source frame
```

### Configuration: `src/config/frame_quality.yaml`

```yaml
frame_quality:
  glare_detection:
    threshold: 70              # Flag as glare if score > 70
    bright_pixel_value: 200    # Pixel brightness threshold
    min_region_size: 0.05      # Min 5% of frame to count as glare
  
  blur_detection:
    threshold: 50              # Flag as blurry if score < 50
    laplacian_kernel_size: 3   # Kernel for edge detection
    variance_min: 100          # Min variance for sharp image
  
  quality_scoring:
    glare_weight: 0.5          # Weight for glare in composite score
    blur_weight: 0.5           # Weight for blur in composite score
    low_quality_threshold: 40  # Flag frames below this score
  
  performance:
    max_processing_time_ms: 100  # Per-frame timeout
```

### Integration Points

**Upstream Dependencies:**
- Story 1.1 - Multi-Angle Capture (provides `CapturedFrame` objects)

**Downstream Consumers:**
- Story 1.3 - Best Frame Selector (uses `QualityMetrics` for ranking)

## Testing Plan

### Unit Tests

**File:** `tests/test_story_1_2_frame_quality.py`

```python
class TestFrameQualityAssessor:
    def test_glare_detection_no_glare(self):
        """Test with uniform lighting, expect low glare score"""
        
    def test_glare_detection_severe_glare(self):
        """Test with bright spot, expect high glare score"""
        
    def test_blur_detection_sharp_image(self):
        """Test with in-focus image, expect high blur score"""
        
    def test_blur_detection_blurry_image(self):
        """Test with out-of-focus image, expect low blur score"""
        
    def test_quality_score_calculation(self):
        """Verify composite score formula correct"""
        
    def test_thresholds_from_config(self):
        """Verify thresholds loaded from YAML correctly"""
        
    def test_performance_timing(self):
        """Verify assessment completes in <100ms"""
```

### Integration Tests

```python
async def test_assess_captured_sequence(captured_frames):
    """
    Test with real captured frames from Story 1.1:
    1. Load 5-frame sequence
    2. Assess quality
    3. Verify metrics present for all frames
    4. Verify scores in valid range (0-100)
    """
    
def test_synthetic_glare_dataset():
    """Test glare detection on synthetic dataset with known glare"""
    
def test_synthetic_blur_dataset():
    """Test blur detection on synthetic dataset with known blur"""
```

### Validation Dataset

Create test image set:
- **No Glare, Sharp:** 10 images (expected quality >80)
- **Glare, Sharp:** 10 images (expected quality 40-60)
- **No Glare, Blurry:** 10 images (expected quality 40-60)
- **Glare, Blurry:** 10 images (expected quality <40)

**Validation Metric:** 90%+ correct classification into quality buckets

### Manual Testing Checklist

- [ ] Run assessor on real tobacco wall captures
- [ ] Visually verify glare detection matches human judgment
- [ ] Visually verify blur detection matches human judgment
- [ ] Test edge cases: backlighting, shadows, partial occlusion
- [ ] Measure processing time on Raspberry Pi 5
- [ ] Validate memory usage stays stable over 100 runs

## Definition of Done

- [ ] Code implemented in `src/vision/frame_quality.py`
- [ ] Configuration file created at `src/config/frame_quality.yaml`
- [ ] Unit tests pass (>90% coverage on new code)
- [ ] Integration tests pass with Story 1.1 frames
- [ ] Validation dataset tests achieve 90%+ accuracy
- [ ] Performance validated: <100ms per frame on Pi5
- [ ] Manual testing on real tobacco wall complete
- [ ] Code reviewed and merged to main branch
- [ ] Documentation added to module docstrings

## Open Questions / Blockers

- **Q1:** Should we add additional quality metrics (e.g., contrast, saturation)?
  - **Decision:** No for MVP, focus on glare/blur. Can add in future iteration.
  
- **Q2:** What if all frames in a sequence have low quality scores?
  - **Decision:** Story 1.3 will handle this - flag for manual review
  
- **Q3:** Should we use GPU acceleration for Laplacian computation?
  - **Decision:** Test CPU performance first. If <100ms, GPU not needed.

- **BLOCKER:** Requires Story 1.1 complete (needs captured frames to assess)

## Dependencies

### Prerequisites (Must Complete First)
- Story 1.1 - Basic Multi-Angle Head Movement (provides captured frames)

### Blocked By
- Story 1.1 (in progress)

### Blocks
- Story 1.3 - Best Frame Selection (needs quality metrics)

## Estimated Effort

- **Implementation:** 4 hours
- **Testing:** 3 hours
- **Dataset Creation:** 1 hour
- **Documentation:** 1 hour
- **Total:** 9 hours (1.5-2 days)

## Success Metrics

### Quantitative
- Quality assessment completes in <100ms per frame (100% of runs)
- Glare detection accuracy: 90%+ vs validation dataset
- Blur detection accuracy: 90%+ vs validation dataset
- Zero memory leaks in 100 consecutive runs

### Qualitative
- Quality scores align with human visual judgment (developer assessment)
- Low-quality frames correctly flagged (manual review of 20 samples)
- High-quality frames correctly ranked higher (manual review)

## Algorithm Details

### Glare Detection Algorithm

```python
def _compute_glare_score(self, frame: np.ndarray) -> float:
    """
    1. Convert BGR to grayscale
    2. Threshold to find bright pixels (value > 200)
    3. Count bright pixels in connected regions
    4. Calculate percentage of frame covered by glare
    5. Normalize to 0-100 score
    
    Score = (glare_pixel_count / total_pixels) * 100 * severity_factor
    """
```

### Blur Detection Algorithm

```python
def _compute_blur_score(self, frame: np.ndarray) -> float:
    """
    1. Convert BGR to grayscale
    2. Apply Laplacian operator (edge detection)
    3. Calculate variance of Laplacian output
    4. Higher variance = sharper edges = less blur
    5. Normalize to 0-100 score
    
    Score = min(100, variance / variance_max * 100)
    
    Reference: "Blur detection for digital images using wavelet transform"
    """
```

## Related Resources

- [OpenCV Laplacian Documentation](https://docs.opencv.org/4.x/d5/db5/tutorial_laplace_operator.html)
- [Blur Detection Paper](https://www.sciencedirect.com/science/article/abs/pii/S0031320304001906)
- [PRD Section 4.1.2: FR-MAC-2 Frame Quality Assessment](./prd.md#fr-mac-2-frame-quality-assessment)
- [Epic 1: Multi-Angle Capture System](./epic-1-multi-angle-capture.md)

---

**Created:** 2025-11-14  
**Last Updated:** 2025-11-14  
**Version:** 1.0  
**Ready for Development:** ❌ (Blocked by Story 1.1)
