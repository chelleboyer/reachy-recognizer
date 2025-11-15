"""
Integration Tests for Story 2.2: Feature Extraction

Tests end-to-end feature extraction with realistic uniform images and
integration with Story 2.1 person detection.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch
import tempfile
import yaml

from src.vision.feature_extractor import FeatureExtractor, UniformFeatures
from src.vision.person_detector import TorsoROI


@pytest.fixture
def integration_config():
    """Create config file for integration testing."""
    config = {
        'feature_extraction': {
            'color_histogram': {
                'color_space': 'HSV',
                'bins_per_channel': 16,
                'normalize': 'L1'
            },
            'pattern_descriptor': {
                'grid_size': [3, 3],
                'edge_detector': 'canny',
                'canny_threshold': [50, 150],
                'edge_density_method': 'mean'
            },
            'dominant_colors': {
                'num_colors': 3,
                'min_percentage': 5.0,
                'clustering_method': 'kmeans'
            },
            'dimensionality_reduction': {
                'method': 'none',
                'target_dimensions': 512,
                'pca_model_path': ''
            },
            'normalization': {
                'final_norm': 'L2'
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        yield f.name


def create_synthetic_uniform(color='blue', pattern='solid', size=(224, 224)):
    """
    Create synthetic uniform image for testing.
    
    Args:
        color: 'blue', 'red', 'green', 'white'
        pattern: 'solid', 'striped', 'checkered'
        size: Image dimensions
        
    Returns:
        RGB image as numpy array (values in [0, 1])
    """
    image = np.zeros((size[0], size[1], 3), dtype=np.float32)
    
    # Base color
    if color == 'blue':
        base = np.array([0.0, 0.0, 1.0])  # Blue
    elif color == 'red':
        base = np.array([1.0, 0.0, 0.0])  # Red
    elif color == 'green':
        base = np.array([0.0, 1.0, 0.0])  # Green
    elif color == 'white':
        base = np.array([1.0, 1.0, 1.0])  # White
    else:
        base = np.array([0.5, 0.5, 0.5])  # Gray
    
    # Apply pattern
    if pattern == 'solid':
        image[:, :] = base
    elif pattern == 'striped':
        # Vertical stripes
        for i in range(0, size[1], 30):
            image[:, i:i+15] = base
            image[:, i+15:i+30] = base * 0.5
    elif pattern == 'checkered':
        # Checkerboard
        square_size = size[0] // 8
        for i in range(0, size[0], square_size * 2):
            for j in range(0, size[1], square_size * 2):
                image[i:i+square_size, j:j+square_size] = base
                image[i+square_size:i+square_size*2, j+square_size:j+square_size*2] = base
    
    return image


class TestEndToEndExtraction:
    """Test end-to-end feature extraction with synthetic uniforms."""
    
    def test_extract_features_solid_blue_vest(self, integration_config):
        """Test feature extraction from solid blue uniform."""
        extractor = FeatureExtractor(integration_config)
        
        # Create solid blue uniform
        image = create_synthetic_uniform('blue', 'solid')
        
        # Create TorsoROI
        torso_roi = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image,
            confidence=0.95,
            person_id="staff_001",
            frame_id="frame_001"
        )
        
        # Extract features
        features = extractor.extract_features(torso_roi)
        
        # Validate output
        assert isinstance(features, UniformFeatures)
        assert features.hsv_histogram.shape == (4096,)
        assert features.pattern_descriptor.shape == (9,)
        assert len(features.dominant_colors) == 3
        assert len(features.color_percentages) == 3
        assert features.feature_vector.shape == (4105,)
        assert features.person_id == "staff_001"
        assert features.frame_id == "frame_001"
        
        # Solid uniform should have low edge density
        assert np.mean(features.pattern_descriptor) < 0.2
        
        # First dominant color should be blue-ish (H~120 for blue in OpenCV)
        assert features.color_percentages[0] > 90.0  # Dominant color
    
    def test_extract_features_striped_uniform(self, integration_config):
        """Test feature extraction from striped uniform."""
        extractor = FeatureExtractor(integration_config)
        
        # Create striped uniform
        image = create_synthetic_uniform('red', 'striped')
        
        torso_roi = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image,
            confidence=0.92,
            person_id="staff_002",
            frame_id="frame_002"
        )
        
        features = extractor.extract_features(torso_roi)
        
        # Striped pattern should have higher edge density
        assert np.mean(features.pattern_descriptor) > 0.05
        
        # Should detect multiple dominant colors
        non_zero_colors = sum(1 for p in features.color_percentages if p > 5.0)
        assert non_zero_colors >= 2
    
    def test_extract_features_checkered_uniform(self, integration_config):
        """Test feature extraction from checkered pattern."""
        extractor = FeatureExtractor(integration_config)
        
        # Create checkered pattern
        image = create_synthetic_uniform('green', 'checkered')
        
        torso_roi = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image,
            confidence=0.88,
            person_id="staff_003",
            frame_id="frame_003"
        )
        
        features = extractor.extract_features(torso_roi)
        
        # Checkered should have moderate to high edge density
        assert np.mean(features.pattern_descriptor) > 0.03
        
        # Pattern descriptor should vary across grid cells
        assert np.std(features.pattern_descriptor) > 0.005
    
    def test_extract_features_customer_clothing(self, integration_config):
        """Test feature extraction from random customer clothing."""
        extractor = FeatureExtractor(integration_config)
        
        # Create random colorful image (typical customer clothing)
        image = np.random.rand(224, 224, 3).astype(np.float32)
        
        torso_roi = TorsoROI(
            person_bbox=(150, 100, 180, 350),
            torso_bbox=(150, 100, 180, 210),
            torso_image=image,
            confidence=0.85,
            person_id="customer_001",
            frame_id="frame_004"
        )
        
        features = extractor.extract_features(torso_roi)
        
        # Random pattern should have varied edge density
        assert features.pattern_descriptor.std() > 0.001
        
        # Multiple colors should be present
        assert sum(features.color_percentages) > 80.0
    
    def test_processing_time_reasonable(self, integration_config):
        """Test that feature extraction completes in reasonable time."""
        extractor = FeatureExtractor(integration_config)
        
        image = create_synthetic_uniform('blue', 'solid')
        torso_roi = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image,
            confidence=0.95,
            person_id="perf_test",
            frame_id="frame_perf"
        )
        
        features = extractor.extract_features(torso_roi)
        
        # Should complete in under 200ms (reasonable for Pi5)
        assert features.processing_time_ms < 200


class TestWithStory21Integration:
    """Test integration with Story 2.1 person detection."""
    
    def test_torso_roi_to_features_pipeline(self, integration_config):
        """Test complete pipeline from TorsoROI to UniformFeatures."""
        extractor = FeatureExtractor(integration_config)
        
        # Simulate TorsoROI from Story 2.1
        image = create_synthetic_uniform('blue', 'solid')
        
        torso_roi = TorsoROI(
            person_bbox=(200, 100, 150, 300),
            torso_bbox=(200, 100, 150, 180),  # Upper 60% of person
            torso_image=image,
            confidence=0.92,
            person_id="pipeline_test_001",
            frame_id="pipeline_frame_001"
        )
        
        # Extract features
        features = extractor.extract_features(torso_roi)
        
        # Verify metadata carries through
        assert features.person_id == torso_roi.person_id
        assert features.frame_id == torso_roi.frame_id
        assert features.roi_bbox == torso_roi.torso_bbox
    
    def test_multiple_people_feature_extraction(self, integration_config):
        """Test extracting features from multiple people."""
        extractor = FeatureExtractor(integration_config)
        
        # Create multiple TorsoROIs (simulating multiple people detected)
        torso_rois = [
            TorsoROI(
                person_bbox=(100, 50, 150, 300),
                torso_bbox=(100, 50, 150, 180),
                torso_image=create_synthetic_uniform('blue', 'solid'),
                confidence=0.95,
                person_id=f"person_{i}",
                frame_id="multi_frame_001"
            )
            for i in range(3)
        ]
        
        # Extract features for all people
        all_features = [extractor.extract_features(roi) for roi in torso_rois]
        
        assert len(all_features) == 3
        assert extractor.get_statistics()['total_extractions'] == 3
        
        # Each should have unique person_id
        person_ids = [f.person_id for f in all_features]
        assert len(set(person_ids)) == 3
    
    def test_serialization_for_downstream_classifier(self, integration_config):
        """Test that features can be serialized for Story 2.3."""
        extractor = FeatureExtractor(integration_config)
        
        image = create_synthetic_uniform('red', 'striped')
        torso_roi = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image,
            confidence=0.90,
            person_id="serialize_test",
            frame_id="serialize_frame"
        )
        
        features = extractor.extract_features(torso_roi)
        
        # Test serialization
        feature_dict = features.to_dict()
        
        assert isinstance(feature_dict, dict)
        assert 'person_id' in feature_dict
        assert 'feature_dim' in feature_dict
        assert feature_dict['feature_dim'] == 4105
        
        # Feature vector should be accessible for classifier
        assert features.feature_vector is not None
        assert features.feature_vector.shape == (4105,)


class TestFeatureQuality:
    """Test quality and consistency of extracted features."""
    
    def test_same_uniform_produces_similar_features(self, integration_config):
        """Test that same uniform produces similar feature vectors."""
        extractor = FeatureExtractor(integration_config)
        
        # Create two identical uniforms
        image1 = create_synthetic_uniform('blue', 'solid')
        image2 = create_synthetic_uniform('blue', 'solid')
        
        torso_roi1 = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image1,
            confidence=0.95,
            person_id="same_1",
            frame_id="same_frame_1"
        )
        
        torso_roi2 = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image2,
            confidence=0.95,
            person_id="same_2",
            frame_id="same_frame_2"
        )
        
        features1 = extractor.extract_features(torso_roi1)
        features2 = extractor.extract_features(torso_roi2)
        
        # Feature vectors should be very similar (cosine similarity ~1)
        dot_product = np.dot(features1.feature_vector, features2.feature_vector)
        cosine_sim = dot_product  # Already L2 normalized
        
        assert cosine_sim > 0.99  # Very high similarity
    
    def test_different_uniforms_produce_different_features(self, integration_config):
        """Test that different uniforms produce distinguishable features."""
        extractor = FeatureExtractor(integration_config)
        
        # Create different uniforms
        image1 = create_synthetic_uniform('blue', 'solid')
        image2 = create_synthetic_uniform('red', 'striped')
        
        torso_roi1 = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image1,
            confidence=0.95,
            person_id="diff_1",
            frame_id="diff_frame_1"
        )
        
        torso_roi2 = TorsoROI(
            person_bbox=(100, 50, 200, 400),
            torso_bbox=(100, 50, 200, 240),
            torso_image=image2,
            confidence=0.95,
            person_id="diff_2",
            frame_id="diff_frame_2"
        )
        
        features1 = extractor.extract_features(torso_roi1)
        features2 = extractor.extract_features(torso_roi2)
        
        # Feature vectors should be different (cosine similarity < 0.9)
        dot_product = np.dot(features1.feature_vector, features2.feature_vector)
        cosine_sim = dot_product
        
        assert cosine_sim < 0.9  # Clearly different


class TestConfigurationProfiles:
    """Test alternative configuration profiles."""
    
    def test_fast_profile_smaller_features(self):
        """Test that fast profile produces smaller feature dimensions."""
        config = {
            'feature_extraction': {
                'color_histogram': {
                    'color_space': 'HSV',
                    'bins_per_channel': 8,  # Reduced from 16
                    'normalize': 'L1'
                },
                'pattern_descriptor': {
                    'grid_size': [2, 2],  # Reduced from 3x3
                    'edge_detector': 'canny',
                    'canny_threshold': [100, 200],
                    'edge_density_method': 'mean'
                },
                'dominant_colors': {
                    'num_colors': 3,
                    'min_percentage': 5.0,
                    'clustering_method': 'kmeans'
                },
                'dimensionality_reduction': {
                    'method': 'none',
                    'target_dimensions': 256,
                    'pca_model_path': ''
                },
                'normalization': {
                    'final_norm': 'L2'
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            config_path = f.name
        
        try:
            extractor = FeatureExtractor(config_path)
            
            image = create_synthetic_uniform('blue', 'solid')
            torso_roi = TorsoROI(
                person_bbox=(100, 50, 200, 400),
                torso_bbox=(100, 50, 200, 240),
                torso_image=image,
                confidence=0.95,
                person_id="fast_test",
                frame_id="fast_frame"
            )
            
            features = extractor.extract_features(torso_roi)
            
            # 8^3 + 2^2 = 512 + 4 = 516
            assert features.feature_vector.shape == (516,)
            assert features.pattern_descriptor.shape == (4,)
        finally:
            import os
            os.unlink(config_path)


class TestErrorHandling:
    """Test error handling in integration scenarios."""
    
    def test_batch_extraction_handles_invalid_roi(self, integration_config):
        """Test that batch processing continues after invalid ROI."""
        extractor = FeatureExtractor(integration_config)
        
        # Mix of valid and invalid ROIs
        rois = [
            TorsoROI(
                person_bbox=(100, 50, 200, 400),
                torso_bbox=(100, 50, 200, 240),
                torso_image=create_synthetic_uniform('blue', 'solid'),
                confidence=0.95,
                person_id="valid_1",
                frame_id="batch_frame"
            ),
            TorsoROI(
                person_bbox=(100, 50, 200, 400),
                torso_bbox=(100, 50, 200, 240),
                torso_image=None,  # type: ignore  # Invalid for testing error handling
                confidence=0.95,
                person_id="invalid",
                frame_id="batch_frame"
            ),
            TorsoROI(
                person_bbox=(100, 50, 200, 400),
                torso_bbox=(100, 50, 200, 240),
                torso_image=create_synthetic_uniform('red', 'solid'),
                confidence=0.95,
                person_id="valid_2",
                frame_id="batch_frame"
            )
        ]
        
        # Extract with error handling
        features_list = []
        for roi in rois:
            try:
                features = extractor.extract_features(roi)
                features_list.append(features)
            except ValueError:
                pass  # Skip invalid ROI
        
        # Should have extracted 2 valid features
        assert len(features_list) == 2
