# Story 2.3: Staff vs Customer Classification

**Epic:** Epic 2 - Uniform Recognition System  
**Story Points:** 13  
**Priority:** P0 (Must Have)  
**Status:** Ready for Development

---

## Story Description

**As a** Reachy Mini robot  
**I want to** classify people as staff or customers based on uniform features  
**So that** I can interact appropriately with store employees and avoid confusing customers

---

## Acceptance Criteria

### AC1: Classifier Training
- [ ] Classifier trained on uniform dataset (≥50 staff, ≥50 customer samples)
- [ ] Training pipeline documented and reproducible
- [ ] Model hyperparameters tuned via validation set
- [ ] Training logs and metrics saved

### AC2: Accuracy Target
- [ ] Model achieves ≥85% accuracy on validation set
- [ ] False positive rate (customer→staff) <10%
- [ ] Confusion matrix and classification report generated

### AC3: Confidence Score Output
- [ ] Classifier outputs probability score (0-1)
- [ ] Confidence calibrated (predicted probs match true frequencies)
- [ ] Configurable confidence threshold (default 0.75)

### AC4: Multi-Frame Voting
- [ ] Classifier averages features across 3-5 frames
- [ ] Majority vote classification when multiple predictions available
- [ ] Individual frame predictions logged for debugging

### AC5: Confidence Threshold
- [ ] Predictions below threshold marked as "uncertain"
- [ ] Threshold configurable via YAML
- [ ] Uncertainty cases logged for manual review

### AC6: Model Serialization
- [ ] Model saved in portable format (ONNX or joblib)
- [ ] Model loading tested on fresh Python environment
- [ ] Model versioning tracked (version number in filename)

### AC7: Integration with Stories 2.1 & 2.2
- [ ] End-to-end pipeline: frame → detection → features → classification
- [ ] Seamless data flow between components
- [ ] Error handling for each pipeline stage

### AC8: End-to-End Pipeline Test
- [ ] Test with real camera frames
- [ ] Test with synthetic uniform samples
- [ ] Test with multiple people in frame

### AC9: Performance Requirement
- [ ] Total latency <500ms (detection + features + classification)
- [ ] Profiled and optimized bottlenecks
- [ ] Performance metrics logged

### AC10: Privacy Validation
- [ ] No face data extracted or stored
- [ ] No photos written to disk
- [ ] Only feature vectors and labels logged
- [ ] Privacy compliance automated test

---

## Technical Specification

### Input
```python
# From Story 2.2
uniform_features: UniformFeatures  # Single frame features
# OR
feature_sequence: List[UniformFeatures]  # Multi-frame features
```

### Output
```python
@dataclass
class ClassificationResult:
    """Result of staff vs customer classification."""
    label: str  # "staff" or "customer"
    confidence: float  # 0.0 to 1.0 probability
    is_certain: bool  # True if confidence >= threshold
    frame_count: int  # Number of frames used
    feature_vector: np.ndarray  # (512,) average features
    individual_votes: List[Tuple[str, float]]  # Per-frame (label, confidence)
    processing_time_ms: float
    person_id: str  # Links to TorsoROI
    timestamp: float  # Unix timestamp
    model_version: str  # Classifier version used
    
    def to_dict(self) -> dict:
        """Serialize to dictionary (exclude large arrays)."""
        return {
            'label': self.label,
            'confidence': self.confidence,
            'is_certain': self.is_certain,
            'frame_count': self.frame_count,
            'person_id': self.person_id,
            'timestamp': self.timestamp,
            'model_version': self.model_version,
            'individual_votes': [
                {'label': v[0], 'confidence': v[1]} 
                for v in self.individual_votes
            ]
        }
```

### Configuration
```yaml
# uniform_classifier.yaml
uniform_classifier:
  model:
    type: "svm"  # "svm" or "mlp"
    model_path: "models/uniform_classifier_v1.pkl"
    version: "1.0"
    input_dim: 512  # Match PCA output from Story 2.2
    
  svm:
    kernel: "rbf"
    C: 1.0
    gamma: "scale"
    probability: true  # Enable probability estimates
    
  mlp:
    hidden_layers: [256, 128]
    activation: "relu"
    dropout: 0.2
    epochs: 50
    batch_size: 32
    
  classification:
    confidence_threshold: 0.75  # Min confidence for certain classification
    labels:
      - "staff"
      - "customer"
      
  multi_frame:
    enabled: true
    num_frames: 5  # Collect 5 frames per person
    voting_method: "average_features"  # "average_features" or "majority_vote"
    min_frames: 3  # Minimum frames required
    
  performance:
    max_latency_ms: 500  # Total pipeline latency target
    enable_profiling: true
    
  privacy:
    log_features: false  # Don't log raw feature vectors
    log_predictions: true  # Log labels and confidence only
    never_store_images: true  # Enforce no image storage
```

### API Design

```python
class UniformClassifier:
    """Classify people as staff or customer based on uniform features."""
    
    def __init__(self, config_path: str = "src/config/uniform_classifier.yaml"):
        """Initialize classifier."""
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.classification_count = 0
        self.frame_buffer = {}  # person_id -> List[UniformFeatures]
        
    def classify(
        self, 
        features: UniformFeatures,
        person_id: str = None
    ) -> ClassificationResult:
        """
        Classify a person as staff or customer.
        
        If multi-frame enabled, buffers features until enough frames collected,
        then returns classification. Otherwise classifies immediately.
        
        Args:
            features: UniformFeatures from Story 2.2
            person_id: Optional person ID for multi-frame tracking
            
        Returns:
            ClassificationResult (or None if waiting for more frames)
            
        Raises:
            ValueError: If features are invalid
        """
        pass
        
    def classify_multi_frame(
        self, 
        feature_sequence: List[UniformFeatures]
    ) -> ClassificationResult:
        """
        Classify using multiple frames (batch mode).
        
        Args:
            feature_sequence: List of features from different frames
            
        Returns:
            ClassificationResult with averaged features
        """
        pass
        
    def _predict(self, feature_vector: np.ndarray) -> Tuple[str, float]:
        """Run model inference."""
        pass
        
    def _average_features(
        self, 
        feature_sequence: List[UniformFeatures]
    ) -> np.ndarray:
        """Average feature vectors across frames."""
        pass
        
    def _majority_vote(
        self, 
        predictions: List[Tuple[str, float]]
    ) -> Tuple[str, float]:
        """Compute majority vote from individual predictions."""
        pass
        
    def get_statistics(self) -> dict:
        """Return classification statistics."""
        return {
            'total_classifications': self.classification_count,
            'model_version': self.config['model']['version'],
            'confidence_threshold': self.config['classification']['confidence_threshold']
        }
        
    def reset_statistics(self):
        """Reset classification counters."""
        pass


# Convenience function
def classify_person_quick(features: UniformFeatures) -> ClassificationResult:
    """Quick classification with default config."""
    classifier = UniformClassifier()
    return classifier.classify(features)
```

---

## Training Pipeline

### Dataset Preparation

```python
# tools/prepare_dataset.py
"""
Prepare uniform dataset for training.

Expected structure:
data/uniforms/
  staff/
    sample_001.jpg
    sample_002.jpg
    ...
  customer/
    sample_001.jpg
    sample_002.jpg
    ...
"""

def prepare_dataset(data_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract features from all images.
    
    Returns:
        X: (N, 512) feature matrix
        y: (N,) label array (0=customer, 1=staff)
    """
    detector = PersonDetector()
    extractor = FeatureExtractor()
    
    X, y = [], []
    
    for label_dir in ['staff', 'customer']:
        label = 1 if label_dir == 'staff' else 0
        image_dir = data_dir / label_dir
        
        for image_path in image_dir.glob('*.jpg'):
            # Load image
            image = cv2.imread(str(image_path))
            
            # Detect person and extract torso
            torso_rois = detector.detect_people(image, str(image_path))
            if len(torso_rois) == 0:
                continue
                
            # Extract features
            features = extractor.extract_features(torso_rois[0])
            
            X.append(features.feature_vector)
            y.append(label)
    
    return np.array(X), np.array(y)
```

### Model Training

```python
# tools/train_classifier.py
"""
Train staff vs customer classifier.

Usage: python tools/train_classifier.py --data data/uniforms/ --output models/uniform_classifier_v1.pkl
"""

from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import joblib

def train_svm_classifier(X, y):
    """Train SVM classifier with hyperparameter tuning."""
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Hyperparameter search
    param_grid = {
        'C': [0.1, 1.0, 10.0],
        'gamma': ['scale', 'auto'],
        'kernel': ['rbf', 'linear']
    }
    
    grid_search = GridSearchCV(
        SVC(probability=True, random_state=42),
        param_grid,
        cv=5,
        scoring='accuracy',
        n_jobs=-1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"Best params: {grid_search.best_params_}")
    print(f"Best CV score: {grid_search.best_score_:.3f}")
    
    # Evaluate on validation set
    y_pred = grid_search.predict(X_val)
    print(classification_report(y_val, y_pred, target_names=['customer', 'staff']))
    print(confusion_matrix(y_val, y_pred))
    
    return grid_search.best_estimator_


def save_model(model, output_path: Path):
    """Save trained model with metadata."""
    model_data = {
        'model': model,
        'version': '1.0',
        'training_date': datetime.now().isoformat(),
        'input_dim': 512,
        'labels': ['customer', 'staff']
    }
    joblib.dump(model_data, output_path)
    print(f"Model saved to {output_path}")
```

---

## Testing Strategy

### Unit Tests (`tests/test_story_2_3_classifier.py`)

```python
class TestUniformClassifier:
    - test_load_config()
    - test_load_model()
    - test_missing_model_raises_error()
    
class TestSingleFrameClassification:
    - test_classify_staff_uniform()
    - test_classify_customer_clothing()
    - test_confidence_above_threshold()
    - test_low_confidence_marked_uncertain()
    
class TestMultiFrameVoting:
    - test_average_features_across_frames()
    - test_majority_vote_classification()
    - test_min_frames_requirement()
    - test_conflicting_votes_handled()
    
class TestConfidenceThreshold:
    - test_configurable_threshold()
    - test_is_certain_flag()
    - test_threshold_affects_classification()
    
class TestStatistics:
    - test_statistics_tracking()
    - test_reset_statistics()
```

### Integration Tests (`tests/test_story_2_3_integration.py`)

```python
class TestEndToEndPipeline:
    - test_frame_to_classification()  # Full pipeline
    - test_multiple_people_classification()
    - test_multi_frame_sequence()
    - test_uncertain_classification_logged()
    
class TestPerformance:
    - test_latency_under_500ms()
    - test_batch_processing_performance()
    
class TestPrivacy:
    - test_no_images_written_to_disk()
    - test_no_face_data_in_logs()
    - test_only_features_and_labels_stored()
    
class TestWithPriorStories:
    - test_integration_with_story_21_22()  # Full Epic 2 pipeline
```

### Acceptance Tests

```python
class TestAcceptanceCriteria:
    - test_accuracy_above_85_percent()
    - test_false_positive_rate_below_10_percent()
    - test_model_serialization_loading()
    - test_confidence_calibration()
```

---

## Definition of Done

- [ ] UniformClassifier class implemented
- [ ] ClassificationResult dataclass implemented
- [ ] Configuration YAML created
- [ ] Training pipeline implemented and documented
- [ ] Model trained and achieves ≥85% accuracy
- [ ] Multi-frame voting logic working
- [ ] End-to-end integration with Stories 2.1 & 2.2
- [ ] 25+ unit tests passing
- [ ] 10+ integration tests passing
- [ ] Performance target met (<500ms latency)
- [ ] Privacy validation passing (no image storage)
- [ ] Documentation complete (training guide, API docs, usage examples)

---

## Dependencies

### Python Packages
- `scikit-learn>=1.3.0` (SVM, metrics)
- `joblib` (model serialization, included with sklearn)
- `numpy` (already installed)
- `pyyaml` (already installed)

### Optional (for MLP alternative)
- `torch` or `tensorflow` (if using neural network instead of SVM)

### Prior Work
- **Story 2.1:** Person detection and torso ROI extraction
- **Story 2.2:** Feature extraction from torso regions

### Data
- **Training Dataset:** 50+ staff uniform samples, 50+ customer samples
  - Can use synthetic data initially (color augmentation)
  - Real samples collected in Week 2-3

---

## Estimated Effort

**13 Story Points** = ~3-4 days

- Dataset preparation: 0.5 days
- Model training pipeline: 1.0 days
- Classifier integration: 1.0 days
- Multi-frame voting: 0.5 days
- Unit tests: 0.5 days
- Integration tests: 0.5 days
- Performance optimization: 0.5 days
- Documentation: 0.25 days

---

## Risk Mitigation

### Risk: Low Accuracy (<85%)
**Mitigation:**
- Collect more diverse training samples
- Try different classifiers (SVM → MLP)
- Use data augmentation (color jitter, rotation)
- Increase feature dimensions (512 → 1024)

### Risk: High Latency (>500ms)
**Mitigation:**
- Profile pipeline and optimize bottlenecks
- Use SVM instead of MLP (faster inference)
- Reduce PCA dimensions if needed
- Cache model in memory

### Risk: Insufficient Training Data
**Mitigation:**
- Generate synthetic uniform samples (solid colors)
- Use data augmentation aggressively
- Start with 50 samples, expand to 100+ if needed

---

**Story Created:** 2025-11-15  
**Ready for Development:** Yes  
**Assigned Agent:** dev
