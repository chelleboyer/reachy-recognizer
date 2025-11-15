"""
Unit Tests for Story 2.2: Feature Extraction

Tests HSV histogram, pattern descriptor, dominant colors, and feature vector creation.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import yaml

from src.vision.feature_extractor import (
    FeatureExtractor,
    UniformFeatures,
    extract_features_quick
)


# Mock TorsoROI for testing
class MockTorsoROI:
    def __init__(self, image, bbox=(0, 0, 224, 224), person_id="test_person", frame_id="test_frame"):
        self.torso_image = image
        self.torso_bbox = bbox
        self.person_id = person_id
        self.frame_id = frame_id


@pytest.fixture
def mock_config_file():
    """Create temporary config file for testing."""
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
                'method': 'none',  # Disable PCA for unit tests
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
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


class TestFeatureExtractor:
    """Test FeatureExtractor initialization and configuration."""
    
    def test_load_config(self, mock_config_file):
        """Test that config loads correctly."""
        extractor = FeatureExtractor(mock_config_file)
        
        assert extractor.bins_per_channel == 16
        assert extractor.grid_size == (3, 3)
        assert extractor.num_colors == 3
        assert extractor.extraction_count == 0
    
    def test_missing_config_raises_error(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            FeatureExtractor("nonexistent_config.yaml")
    
    def test_invalid_config_raises_error(self):
        """Test that invalid YAML raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: {")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid YAML"):
                FeatureExtractor(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_statistics_tracking(self, mock_config_file):
        """Test that extraction count increments."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Create mock torso ROI
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        extractor.extract_features(torso_roi)
        extractor.extract_features(torso_roi)
        
        stats = extractor.get_statistics()
        assert stats['total_extractions'] == 2
    
    def test_reset_statistics(self, mock_config_file):
        """Test that statistics can be reset."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        extractor.extract_features(torso_roi)
        assert extractor.get_statistics()['total_extractions'] == 1
        
        extractor.reset_statistics()
        assert extractor.get_statistics()['total_extractions'] == 0


class TestHSVHistogram:
    """Test HSV histogram computation."""
    
    def test_compute_histogram_16_bins(self, mock_config_file):
        """Test that histogram has correct dimensions (16^3 = 4096)."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Create test image
        image = np.random.rand(224, 224, 3).astype(np.float32)
        hist = extractor._compute_hsv_histogram(image)
        
        assert hist.shape == (4096,)
    
    def test_histogram_normalized_L1(self, mock_config_file):
        """Test that histogram is L1 normalized (sums to 1)."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        hist = extractor._compute_hsv_histogram(image)
        
        assert np.isclose(hist.sum(), 1.0, atol=1e-5)
    
    def test_solid_color_histogram(self, mock_config_file):
        """Test histogram for solid color image."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Create solid blue image
        image = np.zeros((224, 224, 3), dtype=np.float32)
        image[:, :, 2] = 1.0  # Blue channel
        
        hist = extractor._compute_hsv_histogram(image)
        
        # Histogram should have most weight in a few bins
        assert hist.max() > 0.5  # At least one bin dominant
        assert hist.sum() > 0.99  # Properly normalized
    
    def test_histogram_uint8_input(self, mock_config_file):
        """Test histogram with uint8 input (0-255)."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.randint(0, 256, (224, 224, 3), dtype=np.uint8)
        hist = extractor._compute_hsv_histogram(image)
        
        assert hist.shape == (4096,)
        assert np.isclose(hist.sum(), 1.0, atol=1e-5)


class TestPatternDescriptor:
    """Test pattern descriptor (edge density) computation."""
    
    def test_edge_density_3x3_grid(self, mock_config_file):
        """Test that pattern descriptor has 9 values for 3x3 grid."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        descriptor = extractor._compute_pattern_descriptor(image)
        
        assert descriptor.shape == (9,)
    
    def test_solid_image_low_edge_density(self, mock_config_file):
        """Test that solid color image has low edge density."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Solid color image (no edges)
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        descriptor = extractor._compute_pattern_descriptor(image)
        
        # All values should be close to 0 (no edges)
        assert np.all(descriptor < 0.1)
    
    def test_striped_image_high_edge_density(self, mock_config_file):
        """Test that striped image has higher edge density."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Create striped image (vertical stripes)
        image = np.zeros((224, 224, 3), dtype=np.float32)
        for i in range(0, 224, 20):
            image[:, i:i+10, :] = 1.0
        
        descriptor = extractor._compute_pattern_descriptor(image)
        
        # Should detect edges in stripe boundaries
        assert np.any(descriptor > 0.1)
    
    def test_pattern_values_in_range(self, mock_config_file):
        """Test that edge density values are in [0, 1]."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        descriptor = extractor._compute_pattern_descriptor(image)
        
        assert np.all(descriptor >= 0.0)
        assert np.all(descriptor <= 1.0)
    
    def test_grayscale_image_handled(self, mock_config_file):
        """Test that grayscale image is handled correctly."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Grayscale image (2D)
        image = np.random.rand(224, 224).astype(np.float32)
        descriptor = extractor._compute_pattern_descriptor(image)
        
        assert descriptor.shape == (9,)


class TestDominantColors:
    """Test dominant color extraction."""
    
    def test_extract_top_3_colors(self, mock_config_file):
        """Test that exactly 3 dominant colors are extracted."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        colors, percentages = extractor._extract_dominant_colors(image)
        
        assert len(colors) == 3
        assert len(percentages) == 3
    
    def test_percentages_sum_less_equal_100(self, mock_config_file):
        """Test that percentages sum to ≤100%."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        colors, percentages = extractor._extract_dominant_colors(image)
        
        assert sum(percentages) <= 100.1  # Allow small floating point error
    
    def test_colors_in_hsv_space(self, mock_config_file):
        """Test that colors are in HSV space."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        colors, percentages = extractor._extract_dominant_colors(image)
        
        for color in colors:
            assert len(color) == 3  # H, S, V
            # HSV ranges in OpenCV: H[0,180], S[0,256], V[0,256]
            if color != (0.0, 0.0, 0.0):  # Skip padding zeros
                assert 0 <= color[0] <= 180
                assert 0 <= color[1] <= 256
                assert 0 <= color[2] <= 256
    
    def test_single_color_image(self, mock_config_file):
        """Test dominant color extraction on solid color image."""
        extractor = FeatureExtractor(mock_config_file)
        
        # Solid red image
        image = np.zeros((224, 224, 3), dtype=np.float32)
        image[:, :, 0] = 1.0  # Red channel
        
        colors, percentages = extractor._extract_dominant_colors(image)
        
        # First color should dominate
        assert percentages[0] > 90.0
    
    def test_percentages_descending_order(self, mock_config_file):
        """Test that percentages are in descending order."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        colors, percentages = extractor._extract_dominant_colors(image)
        
        # Check descending order (ignoring zeros)
        non_zero_pct = [p for p in percentages if p > 0]
        assert non_zero_pct == sorted(non_zero_pct, reverse=True)


class TestFeatureVector:
    """Test feature vector creation and normalization."""
    
    def test_feature_vector_4105_dim(self, mock_config_file):
        """Test that combined feature vector is 4105-dim (no PCA)."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        features = extractor.extract_features(torso_roi)
        
        # 4096 (histogram) + 9 (pattern) = 4105
        assert features.feature_vector.shape == (4105,)
    
    def test_feature_vector_L2_normalized(self, mock_config_file):
        """Test that feature vector is L2 normalized."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        torso_roi = MockTorsoROI(image)
        
        features = extractor.extract_features(torso_roi)
        
        # L2 norm should be 1
        norm = np.linalg.norm(features.feature_vector)
        assert np.isclose(norm, 1.0, atol=1e-5)
    
    def test_feature_vector_512_dim_with_pca(self, mock_config_file):
        """Test that PCA reduces to 512-dim."""
        # Create mock PCA model
        class MockPCA:
            def transform(self, X):
                return np.random.rand(1, 512)
        
        extractor = FeatureExtractor(mock_config_file)
        extractor.pca_model = MockPCA()
        
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        features = extractor.extract_features(torso_roi)
        
        assert features.feature_vector.shape == (512,)
    
    def test_histogram_and_pattern_combined(self, mock_config_file):
        """Test that histogram and pattern are combined correctly."""
        extractor = FeatureExtractor(mock_config_file)
        
        hist = np.random.rand(4096)
        pattern = np.random.rand(9)
        
        combined = extractor._create_feature_vector(hist, pattern)
        
        assert combined.shape == (4105,)
        # Combined should be L2 normalized
        assert np.isclose(np.linalg.norm(combined), 1.0, atol=1e-5)


class TestEdgeCases:
    """Test error handling and edge cases."""
    
    def test_none_torso_roi_raises_error(self, mock_config_file):
        """Test that None torso_roi raises ValueError."""
        extractor = FeatureExtractor(mock_config_file)
        
        with pytest.raises(ValueError, match="torso_roi cannot be None"):
            extractor.extract_features(None)
    
    def test_none_image_raises_error(self, mock_config_file):
        """Test that None torso_image raises ValueError."""
        extractor = FeatureExtractor(mock_config_file)
        
        torso_roi = MockTorsoROI(None)
        
        with pytest.raises(ValueError, match="torso_image cannot be None"):
            extractor.extract_features(torso_roi)
    
    def test_empty_image_raises_error(self, mock_config_file):
        """Test that empty image raises ValueError."""
        extractor = FeatureExtractor(mock_config_file)
        
        empty_image = np.array([])
        torso_roi = MockTorsoROI(empty_image)
        
        with pytest.raises(ValueError, match="torso_image cannot be empty"):
            extractor.extract_features(torso_roi)
    
    def test_invalid_image_type_raises_error(self, mock_config_file):
        """Test that non-numpy image raises ValueError."""
        extractor = FeatureExtractor(mock_config_file)
        
        torso_roi = MockTorsoROI([1, 2, 3])  # List instead of array
        
        with pytest.raises(ValueError, match="must be numpy array"):
            extractor.extract_features(torso_roi)


class TestUniformFeaturesDataclass:
    """Test UniformFeatures dataclass."""
    
    def test_to_dict_excludes_large_arrays(self, mock_config_file):
        """Test that to_dict excludes histogram and feature_vector."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        features = extractor.extract_features(torso_roi)
        feature_dict = features.to_dict()
        
        # Should not include large arrays
        assert 'hsv_histogram' not in feature_dict
        assert 'pattern_descriptor' not in feature_dict
        assert 'feature_vector' not in feature_dict
        
        # Should include metadata
        assert 'person_id' in feature_dict
        assert 'frame_id' in feature_dict
        assert 'dominant_colors' in feature_dict
        assert 'color_percentages' in feature_dict
        assert 'feature_dim' in feature_dict
        assert 'processing_time_ms' in feature_dict
    
    def test_processing_time_recorded(self, mock_config_file):
        """Test that processing time is recorded."""
        extractor = FeatureExtractor(mock_config_file)
        
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        features = extractor.extract_features(torso_roi)
        
        assert features.processing_time_ms > 0


class TestConvenienceFunction:
    """Test extract_features_quick convenience function."""
    
    def test_extract_features_quick(self):
        """Test quick extraction with default config."""
        image = np.ones((224, 224, 3), dtype=np.float32) * 0.5
        torso_roi = MockTorsoROI(image)
        
        features = extract_features_quick(torso_roi)
        
        assert isinstance(features, UniformFeatures)
        assert features.feature_vector is not None
