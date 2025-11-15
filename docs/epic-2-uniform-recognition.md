# Epic 2: Uniform Recognition System

**Epic Owner:** Michelle  
**Duration:** Weeks 2-3 (Parallel with Epic 3)  
**Story Points:** 23  
**Priority:** P0 (Must Have)  
**Status:** Ready for Development

---

## Epic Overview

### Vision

Enable privacy-first staff identification using clothing patterns and colors instead of face recognition. The system detects people, extracts torso region features, and classifies them as staff or customer based on uniform characteristics. No photos stored, only color embeddings.

### Business Value

- **Privacy Compliance:** No PII collection, no face database
- **Staff Recognition:** 85%+ accuracy identifying store employees
- **Contextual Interaction:** Robot knows who to approach for tasks
- **Customer Safety:** Robot doesn't confuse customers with staff

### Success Metrics

- **Classification Accuracy:** ≥85% on staff vs customer test set
- **Processing Time:** <500ms per person detection + classification
- **False Positive Rate:** <10% (customer incorrectly identified as staff)
- **Privacy:** Zero face data or photos stored to disk

---

## Technical Architecture

### System Components

```
Camera Frame Input
    ↓
[Person Detection - YOLO]
    ↓
[Torso ROI Extraction]
    ↓
[Color-Pattern Feature Extraction]
    ↓ (HSV histogram + pattern descriptor)
[Staff/Customer Classifier]
    ↓
[Confidence Score + Label]
```

### Key Design Decisions

1. **Person Detection:** Use YOLOv8n (nano) for speed on Pi5
2. **Torso Focus:** Extract upper body region (chest/vest area)
3. **Feature Extraction:** HSV color histogram + simple pattern encoding
4. **Classifier:** Lightweight MLP or SVM (not full CNN)
5. **Multi-Frame:** Average embeddings across 3-5 frames for robustness

### Privacy Architecture

- ❌ **No face detection or recognition**
- ❌ **No photo storage**
- ✅ **Only store color embeddings (512-dim vectors)**
- ✅ **Face regions excluded from processing**
- ✅ **Data deleted after classification**

---

## Stories

### Story 2.1: Person Detection with Torso ROI (5 points)

**Goal:** Detect people in camera frames and extract torso bounding boxes for uniform analysis

**Acceptance Criteria:**
- AC1: YOLOv8n person detector integrated and running on Pi5
- AC2: Torso ROI extraction from person bbox (upper 50-70% of body)
- AC3: ROI preprocessing (resize to 224x224, normalize)
- AC4: Detection confidence threshold configurable (default 0.7)
- AC5: Multiple people handled (process all detections)
- AC6: Unit tests for ROI extraction logic
- AC7: Integration test with real/synthetic camera frames

**Technical Details:**
- YOLOv8n model (3.2MB, optimized for edge devices)
- Torso heuristic: Top 60% of person bbox, centered horizontally
- Output: List of TorsoROI objects with bbox coordinates
- Performance: Target <200ms per frame on Pi5

---

### Story 2.2: Color-Pattern Feature Extraction (5 points)

**Goal:** Extract color histogram and pattern descriptors from torso regions

**Acceptance Criteria:**
- AC1: HSV color histogram extraction (16 bins per channel = 4096-dim)
- AC2: Pattern encoding (solid/striped/logo detection using edge density)
- AC3: Dominant color extraction (top 3 colors with percentages)
- AC4: Feature vector normalization (L2 norm)
- AC5: Configurable feature extraction parameters (bins, pattern threshold)
- AC6: Unit tests for histogram computation
- AC7: Integration test with sample uniform images

**Technical Details:**
- HSV histogram: 16x16x16 bins (4096 dimensions)
- Pattern descriptor: Edge density in 3x3 grid (9 values)
- Combined feature: 4105-dim vector (4096 + 9)
- Reduce to 512-dim via PCA for efficiency (trained on uniform dataset)

**Output Data Structure:**
```python
@dataclass
class UniformFeatures:
    hsv_histogram: np.ndarray  # (4096,) histogram
    pattern_descriptor: np.ndarray  # (9,) edge density grid
    dominant_colors: List[Tuple[float, float, float]]  # Top 3 HSV colors
    color_percentages: List[float]  # Percentages for top 3
    feature_vector: np.ndarray  # (512,) PCA-reduced features
    roi_bbox: Tuple[int, int, int, int]  # x, y, w, h
```

---

### Story 2.3: Staff vs Customer Classification (13 points)

**Goal:** Train and deploy classifier to distinguish staff from customers based on uniform features

**Acceptance Criteria:**
- AC1: Classifier trained on uniform dataset (50+ staff, 50+ customer samples)
- AC2: Model achieves ≥85% accuracy on validation set
- AC3: Confidence score output (0-1 probability)
- AC4: Multi-frame voting (classify across 3-5 frames, majority vote)
- AC5: Configurable confidence threshold (default 0.75)
- AC6: Model serialization and loading (ONNX or joblib)
- AC7: Integration with Stories 2.1 & 2.2
- AC8: End-to-end pipeline test (frame → person → features → classification)
- AC9: Performance meets <500ms total latency requirement
- AC10: Privacy validation (no face data, no photo storage)

**Technical Details:**
- **Classifier:** SVM with RBF kernel or simple MLP (2 layers, 256 hidden units)
- **Training Data:** Synthetic + real uniform samples
  - Staff uniforms: Consistent colors (e.g., blue vest, red shirt)
  - Customer clothing: Random colors, diverse patterns
- **Multi-Frame Logic:** Extract features from 3-5 frames, average vectors, classify
- **Output:** Binary label ("staff" / "customer") + confidence score

**Output Data Structure:**
```python
@dataclass
class ClassificationResult:
    label: str  # "staff" or "customer"
    confidence: float  # 0.0 to 1.0
    frame_count: int  # Number of frames used
    feature_vector: np.ndarray  # (512,) average features
    individual_votes: List[Tuple[str, float]]  # Per-frame predictions
    processing_time_ms: float
    person_id: str  # Unique ID for tracking
```

**Privacy Compliance:**
- Only store `feature_vector` (512-dim, not reversible to image)
- Delete intermediate frames after classification
- Log only label + confidence, not images

---

## Dependencies

### External Dependencies
- **ultralytics** (YOLOv8): `pip install ultralytics>=8.0.0`
- **opencv-python**: Already installed (Epic 1)
- **numpy**: Already installed
- **scikit-learn**: For SVM/PCA: `pip install scikit-learn>=1.3.0`

### Internal Dependencies
- **Epic 1:** Camera capture system for frame input
- **Hardware:** Pi5 + camera (already available)

### Data Dependencies
- **Uniform Dataset:** 50+ staff uniform samples (to be collected)
- **Customer Dataset:** 50+ customer clothing samples (synthetic + real)

---

## Implementation Plan

### Week 2 (Stories 2.1 & 2.2)

**Story 2.1 - Days 1-2:**
- Integrate YOLOv8n person detector
- Implement torso ROI extraction
- Unit tests for ROI logic
- Integration test with camera frames

**Story 2.2 - Days 3-4:**
- HSV histogram extraction
- Pattern descriptor encoding
- Feature vector normalization
- Unit tests for feature extraction

### Week 3 (Story 2.3)

**Story 2.3 - Days 5-9:**
- Collect/generate uniform dataset (50+ samples each)
- Train SVM/MLP classifier
- Implement multi-frame voting logic
- End-to-end integration testing
- Performance optimization (<500ms target)
- Privacy validation (no photo storage)

---

## Testing Strategy

### Unit Tests
- Torso ROI extraction with various person sizes
- HSV histogram computation correctness
- Pattern descriptor edge cases
- Feature normalization (L2 norm)
- PCA dimensionality reduction
- Classifier prediction logic

### Integration Tests
- End-to-end pipeline: frame → detection → features → classification
- Multi-frame voting with simulated sequences
- Performance benchmarks (latency, throughput)
- Privacy compliance (no disk writes of images)

### Acceptance Tests
- Real-world uniform samples (staff photos)
- Customer clothing samples (diverse colors/patterns)
- Accuracy on validation set (≥85%)
- False positive rate (<10%)

---

## Risks & Mitigations

### Risk 1: Low Classification Accuracy
**Likelihood:** Medium  
**Impact:** High  
**Mitigation:**
- Start with simple uniform colors (blue vest, red shirt)
- Collect diverse customer samples for training
- Use multi-frame voting to reduce noise

### Risk 2: YOLOv8 Too Slow on Pi5
**Likelihood:** Low  
**Impact:** Medium  
**Mitigation:**
- Use YOLOv8n (nano) variant (optimized for edge)
- Profile and optimize inference pipeline
- Reduce input resolution if needed (640x480 → 416x416)

### Risk 3: Insufficient Training Data
**Likelihood:** Medium  
**Impact:** High  
**Mitigation:**
- Generate synthetic uniform samples (color variations)
- Use data augmentation (rotation, brightness, contrast)
- Start with 50 samples, expand to 100+ if accuracy low

### Risk 4: Privacy Violation (Accidental Face Storage)
**Likelihood:** Low  
**Impact:** Critical  
**Mitigation:**
- Automated tests to detect any disk writes of images
- Code review for privacy compliance
- Exclude face region from torso ROI extraction

---

## Success Criteria

✅ **Epic Complete When:**
1. Person detection integrated and tested
2. Feature extraction working on uniform samples
3. Classifier achieves ≥85% accuracy
4. End-to-end pipeline processes frames in <500ms
5. Privacy validated (no photos stored)
6. All unit and integration tests passing
7. Documentation complete (API docs, model training guide)

---

## Future Enhancements (Post-MVP)

- **Story 2.4:** Badge/logo detection for fine-grained staff ID
- **Story 2.5:** Person re-identification across frames
- **Story 2.6:** Adaptive classifier (online learning from corrections)
- **Story 2.7:** Depth sensor integration (Intel D405) for 3D uniform analysis

---

**Epic Created:** 2025-11-15  
**Ready for Development:** Yes  
**Assigned Agent:** dev  
**Estimated Completion:** End of Week 3
