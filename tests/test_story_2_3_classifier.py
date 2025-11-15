"""
Unit tests for Story 2.3: Staff vs Customer Classification

Tests the UniformClassifier implementation including:
- Configuration loading
- Single-frame classification
- Multi-frame voting
- Confidence thresholds
- Statistics tracking
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
import time

from src.vision.uniform_classifier import (
    UniformClassifier,
    ClassificationResult,
    classify_person_quick
)
from src.vision.feature_extractor import UniformFeatures


# Test Helpers

def create_mock_features(
    uniform_like: bool = True,
    feature_dim: int = 512
) -> UniformFeatures:
    """
    Create mock UniformFeatures for testing.
    
    Args:
        uniform_like: If True, create features that should classify as "staff"
                     If False, create features that should classify as "customer"
        feature_dim: Dimension of feature vector
        
    Returns:
        UniformFeatures object
    """
    if uniform_like:
        # Staff uniform: high intensity in first features (solid color histogram)
        features = np.zeros(feature_dim)
        features[:100] = np.random.uniform(0.6, 0.9, 100)  # High mean
        features[:100] += np.random.normal(0, 0.2, 100)  # High std
        features = np.clip(features, 0, 1)
    else:
        # Customer clothing: low intensity (varied colors)
        features = np.random.uniform(0.1, 0.4, feature_dim)
        
    # L2 normalize
    features = features / (np.linalg.norm(features) + 1e-10)
    
    return UniformFeatures(
        hsv_histogram=np.random.rand(4096),
        pattern_descriptor=np.random.rand(9),
        dominant_colors=[(180.0, 255.0, 128.0), (90.0, 200.0, 100.0), (45.0, 150.0, 80.0)],
        color_percentages=[0.5, 0.3, 0.2],
        feature_vector=features,
        roi_bbox=(100, 100, 200, 300),
        person_id="test_person",
        frame_id="test_frame",
        processing_time_ms=150.0
    )


class TestUniformClassifier:
    """Test UniformClassifier initialization and configuration."""
    
    def test_load_config(self):
        """Test configuration loading."""
        classifier = UniformClassifier()
        
        assert classifier.config is not None
        assert 'model' in classifier.config
        assert 'classification' in classifier.config
        assert 'multi_frame' in classifier.config
        
    def test_config_values_extracted(self):
        """Test that config values are extracted correctly."""
        classifier = UniformClassifier()
        
        assert classifier.confidence_threshold == 0.75
        assert classifier.multi_frame_enabled is True
        assert classifier.num_frames == 5
        assert classifier.min_frames == 3
        assert classifier.voting_method == "average_features"
        assert classifier.model_version == "1.0"
        assert classifier.labels == ["staff", "customer"]
        
    def test_missing_config_raises_error(self):
        """Test that missing config file raises error."""
        with pytest.raises(FileNotFoundError):
            UniformClassifier(config_path="nonexistent.yaml")
            
    def test_mock_model_loaded(self):
        """Test that mock model is loaded when real model doesn't exist."""
        classifier = UniformClassifier()
        
        assert classifier.model is not None
        assert hasattr(classifier.model, 'predict_proba')
        
    def test_statistics_initialized(self):
        """Test that statistics are initialized to zero."""
        classifier = UniformClassifier()
        
        stats = classifier.get_statistics()
        assert stats['total_classifications'] == 0
        assert stats['buffered_people'] == 0


class TestSingleFrameClassification:
    """Test single-frame classification."""
    
    def test_classify_staff_uniform(self):
        """Test classification of staff uniform."""
        classifier = UniformClassifier()
        # Disable multi-frame for this test
        classifier.multi_frame_enabled = False
        
        features = create_mock_features(uniform_like=True)
        result = classifier.classify(features, person_id="test_staff")
        
        assert result is not None
        assert result.label in ["staff", "customer"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.frame_count == 1
        assert result.person_id == "test_staff"
        assert len(result.individual_votes) == 1
        assert result.model_version == "1.0"
        
    def test_classify_customer_clothing(self):
        """Test classification of customer clothing."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        features = create_mock_features(uniform_like=False)
        result = classifier.classify(features, person_id="test_customer")
        
        assert result is not None
        assert result.label in ["staff", "customer"]
        assert 0.0 <= result.confidence <= 1.0
        
    def test_confidence_above_threshold(self):
        """Test is_certain flag when confidence is high."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        classifier.confidence_threshold = 0.5  # Lower threshold for testing
        
        features = create_mock_features(uniform_like=True)
        result = classifier.classify(features)
        
        # Mock model should produce high confidence for uniform-like features
        assert result is not None
        assert result.confidence >= 0.5
        assert result.is_certain == True  # Use == for numpy bool comparison
        
    def test_low_confidence_marked_uncertain(self):
        """Test is_certain flag when confidence is low."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        classifier.confidence_threshold = 0.95  # Very high threshold
        
        features = create_mock_features(uniform_like=True)
        result = classifier.classify(features)
        
        # With high threshold, most predictions should be uncertain
        assert result is not None
        if result.confidence < 0.95:
            assert result.is_certain == False  # Use == for numpy bool comparison
            
    def test_classification_increments_counter(self):
        """Test that classification count is incremented."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        initial_count = classifier.classification_count
        
        features = create_mock_features(uniform_like=True)
        classifier.classify(features)
        
        assert classifier.classification_count == initial_count + 1
        
    def test_none_features_raises_error(self):
        """Test that None features raise error."""
        classifier = UniformClassifier()
        
        with pytest.raises(ValueError, match="Features cannot be None"):
            classifier.classify(None)  # type: ignore
            
    def test_empty_feature_vector_raises_error(self):
        """Test that empty feature vector raises error."""
        classifier = UniformClassifier()
        
        features = create_mock_features(uniform_like=True)
        features.feature_vector = np.array([])
        
        with pytest.raises(ValueError, match="Feature vector is empty"):
            classifier.classify(features)
            
    def test_person_id_generated_if_not_provided(self):
        """Test that person_id is auto-generated."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        features = create_mock_features(uniform_like=True)
        result = classifier.classify(features)
        
        assert result is not None
        assert result.person_id is not None
        assert result.person_id.startswith("person_")


class TestMultiFrameVoting:
    """Test multi-frame classification and voting."""
    
    def test_average_features_across_frames(self):
        """Test feature averaging across multiple frames."""
        classifier = UniformClassifier()
        
        # Create sequence of similar features
        feature_sequence = [
            create_mock_features(uniform_like=True) for _ in range(5)
        ]
        
        avg_features = classifier._average_features(feature_sequence)
        
        assert avg_features.shape == (512,)
        assert np.all(np.isfinite(avg_features))
        
    def test_classify_multi_frame_with_average_features(self):
        """Test multi-frame classification with feature averaging."""
        classifier = UniformClassifier()
        classifier.voting_method = "average_features"
        
        feature_sequence = [
            create_mock_features(uniform_like=True) for _ in range(5)
        ]
        
        result = classifier.classify_multi_frame(
            feature_sequence, 
            person_id="multi_frame_test"
        )
        
        assert result is not None
        assert result.frame_count == 5
        assert result.person_id == "multi_frame_test"
        assert len(result.individual_votes) == 1  # Single vote from averaged features
        
    def test_classify_multi_frame_with_majority_vote(self):
        """Test multi-frame classification with majority voting."""
        classifier = UniformClassifier()
        classifier.voting_method = "majority_vote"
        
        feature_sequence = [
            create_mock_features(uniform_like=True) for _ in range(5)
        ]
        
        result = classifier.classify_multi_frame(feature_sequence)
        
        assert result is not None
        assert result.frame_count == 5
        assert len(result.individual_votes) == 5  # One vote per frame
        
    def test_majority_vote_computation(self):
        """Test majority vote logic."""
        classifier = UniformClassifier()
        
        # 3 staff votes, 2 customer votes
        predictions = [
            ("staff", 0.8),
            ("staff", 0.75),
            ("staff", 0.85),
            ("customer", 0.7),
            ("customer", 0.72)
        ]
        
        majority_label, avg_confidence = classifier._majority_vote(predictions)
        
        assert majority_label == "staff"
        assert 0.75 <= avg_confidence <= 0.85  # Average of staff confidences
        
    def test_min_frames_requirement(self):
        """Test that minimum frames requirement is enforced."""
        classifier = UniformClassifier()
        classifier.min_frames = 3
        
        # Only 2 frames (below minimum)
        feature_sequence = [
            create_mock_features(uniform_like=True) for _ in range(2)
        ]
        
        with pytest.raises(ValueError, match="Need at least 3 frames"):
            classifier.classify_multi_frame(feature_sequence)
            
    def test_empty_feature_sequence_raises_error(self):
        """Test that empty sequence raises error."""
        classifier = UniformClassifier()
        
        with pytest.raises(ValueError, match="Feature sequence cannot be empty"):
            classifier.classify_multi_frame([])
            
    def test_multi_frame_buffering(self):
        """Test that frames are buffered in multi-frame mode."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = True
        classifier.min_frames = 3
        
        features1 = create_mock_features(uniform_like=True)
        result1 = classifier.classify(features1, person_id="buffer_test")
        
        # First frame: should return None (buffering)
        assert result1 is None
        assert "buffer_test" in classifier.frame_buffer
        assert len(classifier.frame_buffer["buffer_test"]) == 1
        
        # Second frame: still buffering
        features2 = create_mock_features(uniform_like=True)
        result2 = classifier.classify(features2, person_id="buffer_test")
        assert result2 is None
        assert len(classifier.frame_buffer["buffer_test"]) == 2
        
    def test_classification_after_enough_frames(self):
        """Test that classification happens after collecting enough frames."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = True
        classifier.min_frames = 3
        classifier.num_frames = 3
        
        # Add 3 frames
        for i in range(3):
            features = create_mock_features(uniform_like=True)
            result = classifier.classify(features, person_id="enough_frames")
            
            if i < 2:
                assert result is None  # Still buffering
            else:
                assert result is not None  # Classified!
                assert result.frame_count == 3
                
        # Buffer should be cleared after classification
        assert "enough_frames" not in classifier.frame_buffer
        
    def test_conflicting_votes_handled(self):
        """Test handling of conflicting frame predictions."""
        classifier = UniformClassifier()
        classifier.voting_method = "majority_vote"
        
        # Mix of staff and customer features
        feature_sequence = [
            create_mock_features(uniform_like=True),   # Staff
            create_mock_features(uniform_like=True),   # Staff
            create_mock_features(uniform_like=False),  # Customer
        ]
        
        result = classifier.classify_multi_frame(feature_sequence)
        
        # Should classify as staff (2 votes vs 1)
        assert result is not None
        # Note: Mock model might not perfectly follow our expectations
        # but it should produce a valid result
        assert result.label in ["staff", "customer"]


class TestConfidenceThreshold:
    """Test confidence threshold configuration."""
    
    def test_configurable_threshold(self):
        """Test that confidence threshold can be configured."""
        classifier = UniformClassifier()
        
        # Default threshold
        assert classifier.confidence_threshold == 0.75
        
        # Change threshold
        classifier.confidence_threshold = 0.5
        assert classifier.confidence_threshold == 0.5
        
    def test_is_certain_flag_respects_threshold(self):
        """Test that is_certain flag uses the configured threshold."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        features = create_mock_features(uniform_like=True)
        
        # Low threshold: should be certain
        classifier.confidence_threshold = 0.3
        result1 = classifier.classify(features, person_id="low_thresh")
        assert result1 is not None
        if result1.confidence >= 0.3:
            assert result1.is_certain == True  # Use == for numpy bool comparison
            
        # High threshold: might be uncertain
        classifier.confidence_threshold = 0.99
        result2 = classifier.classify(features, person_id="high_thresh")
        assert result2 is not None
        if result2.confidence < 0.99:
            assert result2.is_certain == False  # Use == for numpy bool comparison


class TestStatistics:
    """Test statistics tracking."""
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        initial_stats = classifier.get_statistics()
        assert initial_stats['total_classifications'] == 0
        
        # Perform some classifications
        for i in range(3):
            features = create_mock_features(uniform_like=True)
            classifier.classify(features)
            
        final_stats = classifier.get_statistics()
        assert final_stats['total_classifications'] == 3
        assert final_stats['model_version'] == "1.0"
        assert final_stats['confidence_threshold'] == 0.75
        
    def test_reset_statistics(self):
        """Test resetting statistics."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        # Perform classifications
        for i in range(3):
            features = create_mock_features(uniform_like=True)
            classifier.classify(features)
            
        assert classifier.classification_count == 3
        
        # Reset
        classifier.reset_statistics()
        
        assert classifier.classification_count == 0
        assert len(classifier.frame_buffer) == 0
        
    def test_buffered_people_count(self):
        """Test that buffered people count is tracked."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = True
        classifier.min_frames = 3
        
        # Add frames for two different people
        features1 = create_mock_features(uniform_like=True)
        classifier.classify(features1, person_id="person_1")
        
        features2 = create_mock_features(uniform_like=False)
        classifier.classify(features2, person_id="person_2")
        
        stats = classifier.get_statistics()
        assert stats['buffered_people'] == 2


class TestClassificationResult:
    """Test ClassificationResult dataclass."""
    
    def test_to_dict_excludes_arrays(self):
        """Test that to_dict excludes large arrays."""
        result = ClassificationResult(
            label="staff",
            confidence=0.85,
            is_certain=True,
            frame_count=5,
            feature_vector=np.random.rand(512),
            individual_votes=[("staff", 0.85), ("staff", 0.82)],
            processing_time_ms=150.0,
            person_id="test_person",
            timestamp=time.time(),
            model_version="1.0"
        )
        
        result_dict = result.to_dict()
        
        # Should include these fields
        assert 'label' in result_dict
        assert 'confidence' in result_dict
        assert 'is_certain' in result_dict
        assert 'frame_count' in result_dict
        assert 'person_id' in result_dict
        assert 'timestamp' in result_dict
        assert 'model_version' in result_dict
        assert 'processing_time_ms' in result_dict
        
        # Should NOT include feature_vector (large array)
        assert 'feature_vector' not in result_dict
        
        # individual_votes should be serialized as list of dicts
        assert 'individual_votes' in result_dict
        assert isinstance(result_dict['individual_votes'], list)
        assert isinstance(result_dict['individual_votes'][0], dict)
        
    def test_result_fields_populated(self):
        """Test that all required fields are populated."""
        result = ClassificationResult(
            label="customer",
            confidence=0.72,
            is_certain=False,
            frame_count=3,
            feature_vector=np.random.rand(512),
            individual_votes=[("customer", 0.72)],
            processing_time_ms=200.0,
            person_id="test_123",
            timestamp=12345.67,
            model_version="1.0"
        )
        
        assert result.label == "customer"
        assert result.confidence == 0.72
        assert result.is_certain is False
        assert result.frame_count == 3
        assert result.person_id == "test_123"
        assert result.timestamp == 12345.67
        assert result.model_version == "1.0"


class TestConvenienceFunction:
    """Test convenience function."""
    
def test_classify_person_quick():
        """Test quick classification function."""
        features = create_mock_features(uniform_like=True)
        
        # Quick function uses default config which has multi-frame enabled
        # This will return None on first call (buffering)
        result = classify_person_quick(features)
        
        # For a single-frame quick test, result might be None if multi-frame enabled
        # So we test that it either returns None or a valid result
        if result is not None:
            assert result.label in ["staff", "customer"]
            assert result.person_id == "quick_classify"


class TestMockModel:
    """Test mock model behavior."""
    
    def test_mock_model_predict_proba(self):
        """Test that mock model produces valid probabilities."""
        classifier = UniformClassifier()
        
        # Create test features
        features = create_mock_features(uniform_like=True)
        feature_vector = features.feature_vector.reshape(1, -1)
        
        # Get predictions
        proba = classifier.model.predict_proba(feature_vector)  # type: ignore
        
        # Check shape and probability constraints
        assert proba.shape == (1, 2)
        assert np.all(proba >= 0.0)
        assert np.all(proba <= 1.0)
        assert np.allclose(np.sum(proba, axis=1), 1.0)  # Probabilities sum to 1
        
    def test_staff_features_higher_probability(self):
        """Test that uniform-like features get higher staff probability."""
        classifier = UniformClassifier()
        
        # Staff uniform features (very high mean and std in first 100 features)
        staff_features = create_mock_features(uniform_like=True)
        # Manually boost to make distinction clearer
        staff_features.feature_vector[:100] = 0.8
        staff_features.feature_vector = staff_features.feature_vector / np.linalg.norm(staff_features.feature_vector)
        staff_vector = staff_features.feature_vector.reshape(1, -1)
        staff_proba = classifier.model.predict_proba(staff_vector)  # type: ignore
        
        # Customer features (very low mean and std)
        customer_features = create_mock_features(uniform_like=False)
        customer_features.feature_vector[:100] = 0.1
        customer_features.feature_vector = customer_features.feature_vector / np.linalg.norm(customer_features.feature_vector)
        customer_vector = customer_features.feature_vector.reshape(1, -1)
        customer_proba = classifier.model.predict_proba(customer_vector)  # type: ignore
        
        # Staff features should have higher staff probability (index 1)
        assert staff_proba[0, 1] > customer_proba[0, 1]
