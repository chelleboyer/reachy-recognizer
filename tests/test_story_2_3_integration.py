"""
Integration tests for Story 2.3: Staff vs Customer Classification

Tests end-to-end pipeline and integration with Stories 2.1 and 2.2:
- Complete pipeline: frame → detection → features → classification
- Performance testing (<500ms latency)
- Privacy validation (no image storage)
- Multi-story integration
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import time
import tempfile
import os

from src.vision.person_detector import PersonDetector, TorsoROI
from src.vision.feature_extractor import FeatureExtractor, UniformFeatures
from src.vision.uniform_classifier import UniformClassifier, ClassificationResult


# Test Helpers

def create_synthetic_person_image(
    uniform_color: tuple = (50, 100, 200),  # BGR
    size: tuple = (640, 480),
    person_bbox: tuple = (150, 100, 350, 450)  # x1, y1, x2, y2
) -> np.ndarray:
    """
    Create a synthetic image with a person wearing a uniform.
    
    Args:
        uniform_color: BGR color for uniform
        size: Image size (width, height)
        person_bbox: Bounding box (x1, y1, x2, y2)
        
    Returns:
        BGR image array
    """
    width, height = size
    image = np.ones((height, width, 3), dtype=np.uint8) * 200  # Gray background
    
    # Draw person rectangle (uniform)
    x1, y1, x2, y2 = person_bbox
    cv2.rectangle(image, (x1, y1), (x2, y2), uniform_color, -1)
    
    # Add some texture/noise to make it more realistic
    noise = np.random.randint(-20, 20, image.shape, dtype=np.int16)
    image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return image


def create_mock_torso_roi_from_image(
    image: np.ndarray,
    person_bbox: tuple
) -> TorsoROI:
    """Create a TorsoROI from a synthetic image."""
    x1, y1, x2, y2 = person_bbox
    
    # Extract torso (upper 60%)
    person_height = y2 - y1
    person_width = x2 - x1
    torso_height = int(person_height * 0.6)
    torso_bbox = (x1, y1, person_width, torso_height)  # x, y, w, h format
    
    # Extract torso region from image
    torso_image = image[y1:y1+torso_height, x1:x2]
    
    # Resize to 224x224 for feature extraction
    torso_image_resized = cv2.resize(torso_image, (224, 224))
    
    return TorsoROI(
        person_bbox=(x1, y1, person_width, person_height),  # x, y, w, h format
        torso_bbox=torso_bbox,
        torso_image=torso_image_resized,
        confidence=0.95,
        person_id=f"person_{int(time.time() * 1000)}",
        frame_id="test_frame"
    )


class TestEndToEndPipeline:
    """Test complete pipeline from frame to classification."""
    
    def test_frame_to_classification_staff(self):
        """Test full pipeline: frame → detection → features → classification (staff)."""
        # Create synthetic staff uniform image (dark blue uniform)
        image = create_synthetic_person_image(
            uniform_color=(100, 50, 30),  # Dark uniform
            person_bbox=(150, 100, 350, 450)
        )
        
        # Step 1: Detect person and extract torso (mock)
        torso_roi = create_mock_torso_roi_from_image(
            image, 
            person_bbox=(150, 100, 350, 450)
        )
        
        # Step 2: Extract features
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        assert features is not None
        assert features.feature_vector is not None
        
        # Step 3: Classify
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False  # Single frame for this test
        
        result = classifier.classify(features, person_id=torso_roi.person_id)
        
        # Verify result
        assert result is not None
        assert result.label in ["staff", "customer"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.is_certain in [True, False]
        assert result.person_id == torso_roi.person_id
        
    def test_frame_to_classification_customer(self):
        """Test full pipeline with customer clothing (varied colors)."""
        # Create synthetic customer image (colorful clothing)
        image = create_synthetic_person_image(
            uniform_color=(180, 120, 80),  # Lighter, less uniform
            person_bbox=(150, 100, 350, 450)
        )
        
        # Full pipeline
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        result = classifier.classify(features)
        
        assert result is not None
        assert result.label in ["staff", "customer"]
        
    def test_multiple_people_classification(self):
        """Test classification of multiple people in sequence."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        extractor = FeatureExtractor()
        
        results = []
        
        # Create 3 different people
        for i, color in enumerate([(50, 30, 20), (150, 100, 80), (200, 180, 160)]):
            image = create_synthetic_person_image(uniform_color=color)
            torso_roi = create_mock_torso_roi_from_image(
                image, 
                person_bbox=(150, 100, 350, 450)
            )
            
            features = extractor.extract_features(torso_roi)
            result = classifier.classify(features, person_id=f"person_{i}")
            
            results.append(result)
            
        # Verify all classified
        assert len(results) == 3
        assert all(r is not None for r in results)
        assert all(r.label in ["staff", "customer"] for r in results)
        
        # Person IDs should be unique
        person_ids = [r.person_id for r in results]
        assert len(set(person_ids)) == 3
        
    def test_multi_frame_sequence(self):
        """Test multi-frame classification with frame sequence."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = True
        classifier.min_frames = 3
        classifier.num_frames = 3
        
        extractor = FeatureExtractor()
        
        # Create 3 frames of same person
        person_id = "multi_frame_person"
        results = []
        
        for i in range(3):
            # Same uniform color across frames
            image = create_synthetic_person_image(uniform_color=(60, 40, 30))
            torso_roi = create_mock_torso_roi_from_image(
                image,
                person_bbox=(150, 100, 350, 450)
            )
            
            features = extractor.extract_features(torso_roi)
            result = classifier.classify(features, person_id=person_id)
            
            results.append(result)
            
        # First 2 frames: None (buffering)
        assert results[0] is None
        assert results[1] is None
        
        # Third frame: classification
        assert results[2] is not None
        assert results[2].frame_count == 3
        assert results[2].person_id == person_id
        
    def test_uncertain_classification_logged(self):
        """Test that uncertain classifications are properly flagged."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        classifier.confidence_threshold = 0.95  # Very high threshold
        
        extractor = FeatureExtractor()
        
        # Create ambiguous image (medium color intensity)
        image = create_synthetic_person_image(uniform_color=(120, 100, 90))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        features = extractor.extract_features(torso_roi)
        result = classifier.classify(features)
        
        # With high threshold, might be uncertain
        assert result is not None
        if result.confidence < 0.95:
            assert result.is_certain == False  # Use == for numpy bool comparison


class TestPerformance:
    """Test performance requirements."""
    
    def test_latency_under_500ms(self):
        """Test that total pipeline latency is under 500ms."""
        # Create test image
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        # Time the full pipeline (features + classification)
        start_time = time.time()
        
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        result = classifier.classify(features)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Should be well under 500ms
        assert latency_ms < 500, f"Latency {latency_ms:.1f}ms exceeds 500ms target"
        
        # Log for visibility
        print(f"\nPipeline latency: {latency_ms:.1f}ms")
        
    def test_batch_processing_performance(self):
        """Test performance with batch processing (multiple people)."""
        extractor = FeatureExtractor()
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        # Process 10 people
        start_time = time.time()
        
        for i in range(10):
            image = create_synthetic_person_image(uniform_color=(50 + i*10, 30, 20))
            torso_roi = create_mock_torso_roi_from_image(
                image,
                person_bbox=(150, 100, 350, 450)
            )
            
            features = extractor.extract_features(torso_roi)
            result = classifier.classify(features, person_id=f"batch_person_{i}")
            
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_person = total_time_ms / 10
        
        # Average should be well under 500ms
        assert avg_time_per_person < 500
        
        print(f"\nBatch processing: {avg_time_per_person:.1f}ms per person")


class TestPrivacy:
    """Test privacy compliance."""
    
    def test_no_images_written_to_disk(self):
        """Test that no images are written to disk during classification."""
        # Get initial file count in temp directory
        temp_dir = tempfile.gettempdir()
        initial_files = set(os.listdir(temp_dir))
        
        # Run classification pipeline
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        result = classifier.classify(features)
        
        # Check that no new image files were created
        final_files = set(os.listdir(temp_dir))
        new_files = final_files - initial_files
        
        # Filter for image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
        new_image_files = [
            f for f in new_files 
            if Path(f).suffix.lower() in image_extensions
        ]
        
        assert len(new_image_files) == 0, f"Image files created: {new_image_files}"
        
    def test_result_dict_excludes_images(self):
        """Test that serialized result doesn't contain image data."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        extractor = FeatureExtractor()
        
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        features = extractor.extract_features(torso_roi)
        result = classifier.classify(features)
        
        assert result is not None
        result_dict = result.to_dict()
        
        # Should not contain large arrays or image data
        assert 'feature_vector' not in result_dict
        assert 'torso_image' not in result_dict
        assert 'image' not in result_dict
        
        # Should contain only metadata
        assert 'label' in result_dict
        assert 'confidence' in result_dict
        assert 'person_id' in result_dict
        
    def test_privacy_config_enforced(self):
        """Test that privacy config is loaded and enforced."""
        classifier = UniformClassifier()
        
        privacy_config = classifier.config.get('privacy', {})
        
        # Check privacy settings
        assert privacy_config.get('never_store_images') is True
        assert privacy_config.get('log_predictions') is True
        assert privacy_config.get('log_features') is False


class TestWithPriorStories:
    """Test integration with Stories 2.1 and 2.2."""
    
    def test_integration_with_story_21_22(self):
        """Test full Epic 2 pipeline: detection → features → classification."""
        # This is a comprehensive integration test
        
        # Create test image
        image = create_synthetic_person_image(
            uniform_color=(50, 30, 20),  # Dark uniform
            person_bbox=(150, 100, 350, 450)
        )
        
        # Story 2.1: Person detection and torso extraction
        torso_roi = create_mock_torso_roi_from_image(
            image,
            person_bbox=(150, 100, 350, 450)
        )
        
        # Verify Story 2.1 output
        assert torso_roi is not None
        assert torso_roi.torso_image is not None
        assert torso_roi.torso_image.shape == (224, 224, 3)
        
        # Story 2.2: Feature extraction
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        # Verify Story 2.2 output
        assert features is not None
        assert features.feature_vector is not None
        # Feature vector could be 512 (with PCA) or 4105 (without PCA)
        assert len(features.feature_vector) in [512, 4105]
        
        # Story 2.3: Classification
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        result = classifier.classify(features, person_id=torso_roi.person_id)
        
        # Verify Story 2.3 output
        assert result is not None
        assert result.label in ["staff", "customer"]
        assert result.person_id == torso_roi.person_id
        
        # Verify data flow (feature vector shape depends on PCA)
        assert result.feature_vector.shape in [(512,), (4105,)]
        
    def test_pipeline_with_multiple_frames(self):
        """Test multi-frame pipeline with frame buffer."""
        extractor = FeatureExtractor()
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = True
        classifier.min_frames = 3
        classifier.num_frames = 3
        
        person_id = "pipeline_test"
        
        # Process 3 frames
        for i in range(3):
            # Create frame
            image = create_synthetic_person_image(
                uniform_color=(50, 30 + i*5, 20),  # Slight color variation
                person_bbox=(150, 100, 350, 450)
            )
            
            # Story 2.1
            torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
            
            # Story 2.2
            features = extractor.extract_features(torso_roi)
            
            # Story 2.3
            result = classifier.classify(features, person_id=person_id)
            
            if i < 2:
                assert result is None  # Buffering
            else:
                assert result is not None  # Final classification
                assert result.frame_count == 3
                
    def test_data_format_compatibility(self):
        """Test that data formats are compatible across stories."""
        # Story 2.1 output → Story 2.2 input
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        # Verify TorsoROI format
        assert hasattr(torso_roi, 'torso_image')
        assert hasattr(torso_roi, 'person_id')
        
        # Story 2.2 output → Story 2.3 input
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        # Verify UniformFeatures format
        assert hasattr(features, 'feature_vector')
        assert features.feature_vector is not None
        assert len(features.feature_vector) > 0
        
        # Story 2.3 accepts UniformFeatures
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        result = classifier.classify(features)
        
        # Verify ClassificationResult format
        assert hasattr(result, 'label')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'is_certain')


class TestAcceptanceCriteria:
    """Test story acceptance criteria."""
    
    def test_confidence_output_valid(self):
        """AC3: Classifier outputs probability score (0-1)."""
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        
        extractor = FeatureExtractor()
        
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        features = extractor.extract_features(torso_roi)
        result = classifier.classify(features)
        
        # Confidence should be in [0, 1]
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
        
    def test_configurable_confidence_threshold(self):
        """AC5: Threshold configurable via config."""
        classifier = UniformClassifier()
        
        # Default threshold from config
        assert classifier.confidence_threshold == 0.75
        
        # Can be changed
        classifier.confidence_threshold = 0.6
        assert classifier.confidence_threshold == 0.6
        
    def test_model_versioning(self):
        """AC6: Model versioning tracked."""
        classifier = UniformClassifier()
        
        assert hasattr(classifier, 'model_version')
        assert classifier.model_version == "1.0"
        
        # Result includes version
        classifier.multi_frame_enabled = False
        extractor = FeatureExtractor()
        
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        features = extractor.extract_features(torso_roi)
        result = classifier.classify(features)
        
        assert result is not None
        assert result.model_version == "1.0"
        
    def test_performance_requirement_met(self):
        """AC9: Total latency <500ms."""
        # Full pipeline timing
        start_time = time.time()
        
        image = create_synthetic_person_image(uniform_color=(50, 30, 20))
        torso_roi = create_mock_torso_roi_from_image(image, (150, 100, 350, 450))
        
        extractor = FeatureExtractor()
        features = extractor.extract_features(torso_roi)
        
        classifier = UniformClassifier()
        classifier.multi_frame_enabled = False
        result = classifier.classify(features)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # AC9: <500ms requirement
        assert latency_ms < 500
        
    def test_privacy_validation(self):
        """AC10: Privacy compliance validated."""
        classifier = UniformClassifier()
        
        # No image storage
        assert classifier.config['privacy']['never_store_images'] is True
        
        # Only metadata logged
        assert classifier.config['privacy']['log_features'] is False
        assert classifier.config['privacy']['log_predictions'] is True
