# Story 1.3: Best Frame Selection & OCR

**Story ID:** STORY-1.3  
**Epic:** [Epic 1 - Multi-Angle Capture System](./epic-1-multi-angle-capture.md)  
**Status:** BLOCKED (Requires Story 1.2)  
**Priority:** P0 (Must Have)  
**Story Points:** 8  
**Assigned To:** dev agent  
**Sprint:** Week 1, Day 5

---

## User Story

**As a** store manager  
**I want** the system to automatically use the clearest frame for product detection  
**So that** I get accurate inventory counts without manual intervention

## Business Context

The multi-angle capture system produces multiple frames, but only the highest-quality frame(s) should be used for OCR/detection. Intelligent selection maximizes accuracy while minimizing processing time.

**User Benefit:** "The system automatically picks the best angle - I don't have to manually review frames"

**Value Delivered:** OCR success rate improves by 40%+ vs single-angle capture, with zero manual frame selection

## Acceptance Criteria

### AC1: Single Best Frame Selection
- [ ] If any frame has quality score >80, select highest-scoring frame
- [ ] Selected frame passed to OCR/detection pipeline
- [ ] Selection decision logged with quality score

### AC2: Multi-Frame Fusion
- [ ] If multiple frames have scores 60-80 (no single great frame), fuse top 2-3
- [ ] Fusion strategy: weighted average based on quality scores
- [ ] Fused frame passed to OCR/detection pipeline

### AC3: Failure Mode
- [ ] If all frames have quality score <60, flag sequence as failed
- [ ] Failed sequence logged with all quality scores
- [ ] Optional: Alert/notification sent for manual review
- [ ] System does NOT attempt OCR on low-quality frames (prevents false positives)

### AC4: OCR Integration
- [ ] Selected frame(s) passed to OCR engine (EasyOCR or Tesseract)
- [ ] OCR extracts text from cigarette pack labels
- [ ] OCR results include: detected text, confidence scores, bounding boxes
- [ ] OCR processing completes in <3 seconds

### AC5: End-to-End Performance
- [ ] Total time (capture → quality assessment → selection → OCR) <15 seconds
- [ ] OCR success rate: 90%+ on pilot tobacco wall dataset (20+ products)
- [ ] System handles edge cases: partial occlusion, angled text, varied lighting

## Technical Implementation

### Module: `src/vision/frame_selector.py`

#### Class: `BestFrameSelector`

**Purpose:** Select optimal frame(s) from quality-assessed sequence for OCR/detection

**Key Methods:**

```python
class BestFrameSelector:
    def __init__(self, config_path: str):
        """
        Initialize selector with thresholds from config
        
        Args:
            config_path: Path to YAML config
        """
        
    def select_best_frames(
        self, 
        frames: List[CapturedFrame], 
        quality_metrics: List[QualityMetrics]
    ) -> SelectionResult:
        """
        Select best frame(s) for OCR based on quality scores
        
        Args:
            frames: Captured frames from Story 1.1
            quality_metrics: Quality assessments from Story 1.2
            
        Returns:
            SelectionResult with selected frame(s) and strategy used
            
        Raises:
            NoGoodFramesError: If all frames below quality threshold
        """
        
    def _select_single_best(
        self, 
        frames: List[CapturedFrame], 
        metrics: List[QualityMetrics]
    ) -> CapturedFrame:
        """Select single highest-quality frame (when score >80 exists)"""
        
    def _fuse_multiple_frames(
        self, 
        frames: List[CapturedFrame], 
        metrics: List[QualityMetrics]
    ) -> np.ndarray:
        """
        Fuse top 2-3 frames with weighted average (when scores 60-80)
        
        Algorithm:
        1. Sort frames by quality score
        2. Take top N frames (N=2 or 3)
        3. Normalize quality scores to weights
        4. Compute weighted average: fused = Σ(frame_i * weight_i)
        """
        
    def _handle_failure(self, metrics: List[QualityMetrics]) -> SelectionResult:
        """Handle case where all frames have low quality (<60)"""
```

#### Class: `OCREngine`

**Purpose:** Extract text from selected frame using OCR

**Key Methods:**

```python
class OCREngine:
    def __init__(self, engine: str = "easyocr", config_path: str = None):
        """
        Initialize OCR engine
        
        Args:
            engine: "easyocr" or "tesseract"
            config_path: Path to OCR config
        """
        
    def extract_text(self, frame: np.ndarray, roi: Optional[Box] = None) -> OCRResult:
        """
        Extract text from frame
        
        Args:
            frame: Input image (BGR format)
            roi: Optional region of interest (crop before OCR)
            
        Returns:
            OCRResult with detected text and confidence
        """
        
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for better OCR:
        1. Convert to grayscale
        2. Increase contrast (CLAHE)
        3. Denoise (bilateral filter)
        4. Sharpen (unsharp mask)
        """
```

#### Data Models:

```python
@dataclass
class SelectionResult:
    strategy: str              # "single_best" | "multi_frame_fusion" | "failure"
    selected_frames: List[CapturedFrame]  # 1 or more frames
    fused_frame: Optional[np.ndarray]     # If fusion used
    quality_scores: List[float]           # Quality scores of selected frames
    reason: str                           # Human-readable explanation
    timestamp: float

@dataclass
class OCRResult:
    detected_text: List[str]   # All text strings found
    confidence_scores: List[float]  # Per-text confidence
    bounding_boxes: List[Box]  # Per-text location
    processing_time_ms: float
    frame_id: str              # Reference to source frame
```

### Configuration: `src/config/frame_selector.yaml`

```yaml
frame_selector:
  thresholds:
    excellent_quality: 80      # Use single best frame if score > 80
    acceptable_quality: 60     # Fuse frames if scores 60-80
    minimum_quality: 60        # Fail if all scores < 60
  
  fusion:
    max_frames_to_fuse: 3      # Fuse top 2-3 frames
    weight_by_quality: true    # Use quality scores as weights
    normalization: "softmax"   # Normalize weights via softmax
  
  failure_handling:
    log_all_scores: true       # Log quality metrics on failure
    send_alert: false          # Alert on failure (for future)
    fallback_to_best: false    # Don't use low-quality frames

ocr:
  engine: "easyocr"            # "easyocr" or "tesseract"
  languages: ["en"]            # Languages to detect
  gpu: false                   # Use GPU if available (Pi5: false)
  
  preprocessing:
    grayscale: true
    contrast_enhancement: true # CLAHE
    denoise: true              # Bilateral filter
    sharpen: false             # Unsharp mask (optional)
  
  performance:
    max_processing_time_sec: 3  # OCR timeout
```

### Integration Points

**Upstream Dependencies:**
- Story 1.1 - Multi-Angle Capture (provides `CapturedFrame` objects)
- Story 1.2 - Frame Quality Assessment (provides `QualityMetrics`)

**Downstream Consumers:**
- End-to-end demo (Epic 4, Story 4.3)
- Future: Inventory tracking system

## Testing Plan

### Unit Tests

**File:** `tests/test_story_1_3_frame_selector.py`

```python
class TestBestFrameSelector:
    def test_select_single_best_high_quality(self):
        """Test with one frame >80 quality, verify selected"""
        
    def test_fuse_multiple_medium_quality(self):
        """Test with multiple frames 60-80, verify fusion"""
        
    def test_failure_all_low_quality(self):
        """Test with all frames <60, verify failure mode"""
        
    def test_fusion_weights_correct(self):
        """Verify fusion weights computed correctly"""
        
    def test_selection_logging(self):
        """Verify selection decision logged with reason"""

class TestOCREngine:
    def test_extract_text_from_clear_image(self):
        """Test OCR on synthetic clear text image"""
        
    def test_extract_text_from_tobacco_label(self):
        """Test OCR on real cigarette pack image"""
        
    def test_preprocessing_improves_quality(self):
        """Verify preprocessing increases OCR confidence"""
        
    def test_performance_timing(self):
        """Verify OCR completes in <3 seconds"""
```

### Integration Tests

```python
async def test_end_to_end_best_frame_pipeline():
    """
    Full pipeline test:
    1. Capture multi-angle sequence (Story 1.1)
    2. Assess quality (Story 1.2)
    3. Select best frame (Story 1.3)
    4. Run OCR
    5. Verify text extracted correctly
    6. Total time <15 seconds
    """
    
async def test_tobacco_wall_dataset():
    """
    Test on 20+ real tobacco products:
    - Verify 90%+ OCR success rate
    - Measure average processing time
    - Identify failure cases
    """
```

### Validation Dataset

**Tobacco Wall Test Set:**
- 20+ unique cigarette pack products
- Varied positions: top/middle/bottom shelf
- Varied lighting: morning/afternoon/evening
- Include edge cases: partial occlusion, angled placement

**Success Criteria:**
- 90%+ products correctly identified (text extracted)
- <15 seconds per product (capture → OCR)
- <5% false positives (incorrect text)

### Manual Testing Checklist

- [ ] Run end-to-end pipeline on tobacco wall
- [ ] Visually verify selected frame is clearest (human judgment)
- [ ] Verify OCR text matches product labels
- [ ] Test failure mode with intentionally bad lighting
- [ ] Measure total processing time (capture → result)
- [ ] Test on Raspberry Pi 5 (not just dev machine)

## Definition of Done

- [ ] Code implemented in `src/vision/frame_selector.py`
- [ ] OCR engine integrated (`src/vision/ocr_engine.py`)
- [ ] Configuration files created
- [ ] Unit tests pass (>90% coverage on new code)
- [ ] Integration tests pass end-to-end
- [ ] Tobacco wall validation dataset achieves 90%+ success
- [ ] Performance validated: <15 sec end-to-end
- [ ] Manual testing on real hardware complete
- [ ] Code reviewed and merged to main branch
- [ ] Documentation added to module docstrings
- [ ] Demo video recorded (multi-angle → OCR result)

## Open Questions / Blockers

- **Q1:** Which OCR engine to use - EasyOCR vs Tesseract?
  - **Decision:** Start with EasyOCR (better for varied fonts). Tesseract as fallback.
  
- **Q2:** Should we use multi-frame fusion or just always pick best single frame?
  - **Decision:** Implement both strategies, test which performs better on validation set.
  
- **Q3:** How to handle partial occlusion (e.g., only part of label visible)?
  - **Decision:** OCR will still run, partial text may be useful. Log confidence scores.

- **Q4:** Should we train custom OCR model on cigarette pack fonts?
  - **Decision:** Not for MVP. Use pre-trained EasyOCR, evaluate accuracy first.

- **BLOCKER:** Requires Story 1.2 complete (needs quality metrics for selection)

## Dependencies

### Prerequisites (Must Complete First)
- Story 1.1 - Basic Multi-Angle Head Movement (provides captured frames)
- Story 1.2 - Frame Quality Assessment (provides quality metrics)

### Blocked By
- Story 1.2 (in progress after Story 1.1)

### Blocks
- Epic 1 completion (this is final story in Epic 1)
- Epic 4, Story 4.3 - End-to-End Demo (needs full pipeline)

## Estimated Effort

- **Implementation (Frame Selector):** 2 hours
- **Implementation (OCR Integration):** 3 hours
- **Testing:** 3 hours
- **Dataset Collection & Validation:** 2 hours
- **Documentation:** 1 hour
- **Total:** 11 hours (1.5-2 days)

## Success Metrics

### Quantitative
- OCR success rate: 90%+ on tobacco wall validation set (20+ products)
- End-to-end processing time: <15 seconds per product (100% of runs)
- Frame selection accuracy: Selected frame is highest quality (95%+ of sequences)
- OCR confidence: Average confidence >80% on successful detections

### Qualitative
- Selected frames match human judgment of "best" frame (visual inspection)
- OCR text matches product labels (manual verification)
- System handles edge cases gracefully (partial occlusion, angled text)

## Algorithm Details

### Multi-Frame Fusion Algorithm

```python
def _fuse_multiple_frames(self, frames, metrics):
    """
    Weighted Average Fusion:
    
    1. Sort frames by quality score descending
    2. Take top N frames (N=2 or 3)
    3. Normalize quality scores to weights:
       weights = softmax([q1, q2, q3])
    4. Compute weighted average:
       fused[x,y] = Σ(frame_i[x,y] * weight_i)
    5. Clip to valid pixel range [0, 255]
    
    Example:
    Frame 1: quality=75, weight=0.5
    Frame 2: quality=70, weight=0.35
    Frame 3: quality=65, weight=0.15
    Fused = 0.5*F1 + 0.35*F2 + 0.15*F3
    """
```

### OCR Preprocessing Pipeline

```python
def _preprocess_frame(self, frame):
    """
    1. Convert BGR to grayscale
    2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
       - Increases local contrast
       - Helps with varied lighting
    3. Apply bilateral filter (denoise while preserving edges)
    4. Optional: Unsharp mask (sharpen text edges)
    
    Result: Enhanced frame optimized for OCR
    """
```

## Related Resources

- [EasyOCR Documentation](https://github.com/JaidedAI/EasyOCR)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [OpenCV Image Preprocessing](https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html)
- [PRD Section 4.1.3: FR-MAC-3 Best Frame Selection](./prd.md#fr-mac-3-best-frame-selection)
- [Epic 1: Multi-Angle Capture System](./epic-1-multi-angle-capture.md)

---

**Created:** 2025-11-14  
**Last Updated:** 2025-11-14  
**Version:** 1.0  
**Ready for Development:** ❌ (Blocked by Story 1.2)
