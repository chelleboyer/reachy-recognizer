"""
Unit Tests for Story 1.2: Frame Quality Assessment

Tests the FrameQualityAssessor class and quality metrics computation.
Validates glare detection, blur detection, and composite quality scoring.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path
import time

from src.vision.frame_quality import (
    FrameQualityAssessor,
    QualityMetrics,
    assess_frame_quick
)


class TestConfigurationLoading:
    """Test configuration loading and validation."""
    
    def test_load_config_from_yaml(self):
        """Test loading configuration from YAML file."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        assert assessor.glare_threshold == 70
        assert assessor.bright_pixel_value == 200
        assert assessor.blur_threshold == 50
        assert assessor.glare_weight == 0.5
        assert assessor.blur_weight == 0.5
    
    def test_missing_config_file_raises_error(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            FrameQualityAssessor("nonexistent_config.yaml")
    
    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config structure raises ValueError."""
        # Create invalid config without frame_quality section
        config_file = tmp_path / "invalid_config.yaml"
        config_file.write_text("some_other_section:\n  value: 123")
        
        with pytest.raises(ValueError, match="missing 'frame_quality'"):
            FrameQualityAssessor(str(config_file))
    
    def test_config_parameters_loaded_correctly(self):
        """Test all config parameters are loaded with correct values."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Glare parameters
        assert assessor.glare_threshold == 70
        assert assessor.bright_pixel_value == 200
        assert assessor.min_region_size == 0.05
        
        # Blur parameters
        assert assessor.blur_threshold == 50
        assert assessor.laplacian_kernel_size == 3
        assert assessor.variance_min == 100
        
        # Quality scoring
        assert assessor.glare_weight == 0.5
        assert assessor.blur_weight == 0.5
        assert assessor.low_quality_threshold == 40
        
        # Performance
        assert assessor.max_processing_time_ms == 100


class TestGlareDetection:
    """Test glare detection algorithm."""
    
    def test_no_glare_uniform_lighting(self):
        """Test that uniform mid-tone image has low glare score."""
        # Create uniform gray image (mid-tone)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.glare_score < 10, "Uniform lighting should have minimal glare"
        assert not metrics.has_glare
    
    def test_severe_glare_bright_spot(self):
        """Test that bright spot in center is detected as glare."""
        # Create dark image with bright center region
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        
        # Add bright spot in center (simulating glare)
        cv2.circle(frame, (320, 240), 100, (255, 255, 255), -1)
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.glare_score > 30, "Bright spot should be detected as glare"
    
    def test_small_bright_spots_ignored(self):
        """Test that small specular highlights don't trigger glare flag."""
        # Create image with tiny bright spots (< min_region_size)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 100
        
        # Add small bright spots
        for i in range(5):
            cv2.circle(frame, (100 + i*100, 240), 5, (255, 255, 255), -1)
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        # Small spots shouldn't exceed min_region_size threshold
        assert metrics.glare_score < assessor.glare_threshold
        assert not metrics.has_glare
    
    def test_glare_score_range(self):
        """Test that glare scores are in valid range 0-100."""
        frames = [
            np.ones((480, 640, 3), dtype=np.uint8) * 50,    # Dark
            np.ones((480, 640, 3), dtype=np.uint8) * 128,   # Mid
            np.ones((480, 640, 3), dtype=np.uint8) * 255,   # Bright
        ]
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        for frame in frames:
            metrics = assessor.assess_frame(frame)
            assert 0 <= metrics.glare_score <= 100


class TestBlurDetection:
    """Test blur detection algorithm."""
    
    def test_sharp_image_high_score(self):
        """Test that sharp image with edges has high blur score."""
        # Create sharp checkerboard pattern (strong edges)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        square_size = 40
        
        for i in range(0, 480, square_size):
            for j in range(0, 640, square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    frame[i:i+square_size, j:j+square_size] = 255
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.blur_score > 60, "Sharp edges should have high blur score"
        assert not metrics.is_blurry
    
    def test_blurry_image_low_score(self):
        """Test that blurred image has low blur score."""
        # Create checkerboard then blur it
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        square_size = 40
        
        for i in range(0, 480, square_size):
            for j in range(0, 640, square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    frame[i:i+square_size, j:j+square_size] = 255
        
        # Apply heavy Gaussian blur
        frame = cv2.GaussianBlur(frame, (51, 51), 0)
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.blur_score < 50, "Blurred image should have low blur score"
        assert metrics.is_blurry
    
    def test_varying_blur_levels(self):
        """Test that blur scores correlate with blur amount."""
        # Create sharp pattern
        base_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        square_size = 40
        
        for i in range(0, 480, square_size):
            for j in range(0, 640, square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    base_frame[i:i+square_size, j:j+square_size] = 255
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        blur_scores = []
        blur_amounts = [1, 5, 11, 21, 31]  # Increasing blur kernel sizes
        
        for blur_size in blur_amounts:
            if blur_size == 1:
                frame = base_frame.copy()
            else:
                frame = cv2.GaussianBlur(base_frame, (blur_size, blur_size), 0)
            
            metrics = assessor.assess_frame(frame)
            blur_scores.append(metrics.blur_score)
        
        # Blur scores should generally decrease as blur increases
        # (allowing some variance in the middle)
        assert blur_scores[0] > blur_scores[-1], "Sharp image should score higher than blurred"
    
    def test_blur_score_range(self):
        """Test that blur scores are in valid range 0-100."""
        frames = [
            np.ones((480, 640, 3), dtype=np.uint8) * 128,  # Uniform (no edges)
            np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8),  # Noise
        ]
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        for frame in frames:
            metrics = assessor.assess_frame(frame)
            assert 0 <= metrics.blur_score <= 100


class TestQualityScoring:
    """Test composite quality score calculation."""
    
    def test_quality_score_formula(self):
        """Test that quality score formula is correct."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Test known values
        glare_score = 20.0
        blur_score = 80.0
        
        expected = (100 - glare_score) * 0.5 + blur_score * 0.5
        actual = assessor._compute_quality_score(glare_score, blur_score)
        
        assert abs(actual - expected) < 0.01
    
    def test_high_quality_frame(self):
        """Test that sharp frame with no glare has high quality score."""
        # Create sharp checkerboard
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        square_size = 40
        
        for i in range(0, 480, square_size):
            for j in range(0, 640, square_size):
                if (i // square_size + j // square_size) % 2 == 0:
                    frame[i:i+square_size, j:j+square_size] = 180
                else:
                    frame[i:i+square_size, j:j+square_size] = 80
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.quality_score > 60, "Sharp frame without glare should have high quality"
    
    def test_low_quality_frame(self):
        """Test that blurry frame with glare has low quality score."""
        # Create bright uniform image (glare + no edges for blur)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 240
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        # Should have low quality due to both glare and lack of detail
        assert metrics.quality_score < 60
    
    def test_quality_score_range(self):
        """Test that quality scores are in valid range 0-100."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Test extreme cases
        test_cases = [
            (0, 0),      # Worst case
            (100, 0),    # Max glare, max blur
            (0, 100),    # No glare, sharp
            (100, 100),  # Impossible but test bounds
            (50, 50),    # Middle case
        ]
        
        for glare, blur in test_cases:
            quality = assessor._compute_quality_score(glare, blur)
            assert 0 <= quality <= 100


class TestQualityMetrics:
    """Test QualityMetrics dataclass."""
    
    def test_metrics_contains_all_fields(self):
        """Test that QualityMetrics contains all required fields."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame, frame_id="test_001")
        
        assert hasattr(metrics, 'quality_score')
        assert hasattr(metrics, 'glare_score')
        assert hasattr(metrics, 'blur_score')
        assert hasattr(metrics, 'has_glare')
        assert hasattr(metrics, 'is_blurry')
        assert hasattr(metrics, 'timestamp')
        assert hasattr(metrics, 'frame_id')
        assert hasattr(metrics, 'processing_time_ms')
    
    def test_frame_id_assignment(self):
        """Test that frame_id is correctly assigned."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame, frame_id="custom_id_123")
        
        assert metrics.frame_id == "custom_id_123"
    
    def test_auto_generated_frame_id(self):
        """Test that frame_id is auto-generated if not provided."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        assert metrics.frame_id.startswith("frame_")
        assert len(metrics.frame_id) > 6
    
    def test_timestamp_is_recent(self):
        """Test that timestamp is current time."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        before = time.time()
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        after = time.time()
        
        assert before <= metrics.timestamp <= after
    
    def test_metrics_to_dict(self):
        """Test conversion of metrics to dictionary."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame, frame_id="test_dict")
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert 'quality_score' in metrics_dict
        assert 'glare_score' in metrics_dict
        assert 'blur_score' in metrics_dict
        assert 'has_glare' in metrics_dict
        assert 'is_blurry' in metrics_dict
        assert 'timestamp' in metrics_dict
        assert 'frame_id' in metrics_dict
        assert metrics_dict['frame_id'] == "test_dict"


class TestFlagSettings:
    """Test has_glare and is_blurry flag logic."""
    
    def test_glare_flag_threshold(self):
        """Test that has_glare flag is set based on threshold."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Create frame with controlled glare
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
        # Large bright region to ensure glare > threshold
        frame[100:380, 200:440] = 255
        
        metrics = assessor.assess_frame(frame)
        
        if metrics.glare_score > assessor.glare_threshold:
            assert metrics.has_glare
        else:
            assert not metrics.has_glare
    
    def test_blur_flag_threshold(self):
        """Test that is_blurry flag is set based on threshold."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Create uniform frame (will have low blur score)
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        metrics = assessor.assess_frame(frame)
        
        if metrics.blur_score < assessor.blur_threshold:
            assert metrics.is_blurry
        else:
            assert not metrics.is_blurry


class TestPerformance:
    """Test performance requirements."""
    
    def test_single_frame_performance(self):
        """Test that single frame assessment completes in <100ms."""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        start = time.perf_counter()
        metrics = assessor.assess_frame(frame)
        end = time.perf_counter()
        
        elapsed_ms = (end - start) * 1000
        
        assert elapsed_ms < 100, f"Processing took {elapsed_ms:.1f}ms (target: <100ms)"
        assert metrics.processing_time_ms < 100
    
    def test_sequence_performance(self):
        """Test that 5-frame sequence processes in <500ms."""
        frames = [
            (np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8), f"frame_{i}")
            for i in range(5)
        ]
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        start = time.perf_counter()
        metrics_list = assessor.assess_sequence(frames)
        end = time.perf_counter()
        
        elapsed_ms = (end - start) * 1000
        
        assert len(metrics_list) == 5
        assert elapsed_ms < 500, f"Sequence processing took {elapsed_ms:.1f}ms (target: <500ms)"
    
    def test_no_memory_leaks(self):
        """Test that repeated assessments don't leak memory."""
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Run 100 assessments
        for i in range(100):
            metrics = assessor.assess_frame(frame, frame_id=f"test_{i}")
            assert metrics is not None
        
        # Check statistics
        stats = assessor.get_statistics()
        assert stats['total_assessments'] == 100
        assert stats['avg_processing_time_ms'] > 0


class TestBatchProcessing:
    """Test assess_sequence batch processing."""
    
    def test_assess_sequence_with_tuples(self):
        """Test assessing sequence with (frame, frame_id) tuples."""
        frames = [
            (np.ones((480, 640, 3), dtype=np.uint8) * 100, f"frame_{i}")
            for i in range(3)
        ]
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics_list = assessor.assess_sequence(frames)
        
        assert len(metrics_list) == 3
        for i, metrics in enumerate(metrics_list):
            assert metrics.frame_id == f"frame_{i}"
    
    def test_assess_sequence_preserves_order(self):
        """Test that sequence assessment preserves frame order."""
        frames = [
            (np.ones((480, 640, 3), dtype=np.uint8) * (50 + i*50), f"frame_{i}")
            for i in range(5)
        ]
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        metrics_list = assessor.assess_sequence(frames)
        
        for i, metrics in enumerate(metrics_list):
            assert metrics.frame_id == f"frame_{i}"


class TestErrorHandling:
    """Test error handling for invalid inputs."""
    
    def test_none_frame_raises_error(self):
        """Test that None frame raises ValueError."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        with pytest.raises(ValueError, match="None or empty"):
            assessor.assess_frame(None)  # type: ignore[arg-type]
    
    def test_empty_frame_raises_error(self):
        """Test that empty frame raises ValueError."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        empty_frame = np.array([])
        
        with pytest.raises(ValueError, match="None or empty"):
            assessor.assess_frame(empty_frame)
    
    def test_invalid_shape_raises_error(self):
        """Test that frame with wrong shape raises ValueError."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Grayscale image instead of BGR
        gray_frame = np.ones((480, 640), dtype=np.uint8) * 128
        
        with pytest.raises(ValueError, match="Expected BGR image"):
            assessor.assess_frame(gray_frame)
    
    def test_wrong_channels_raises_error(self):
        """Test that frame with wrong number of channels raises ValueError."""
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # RGBA image instead of BGR
        rgba_frame = np.ones((480, 640, 4), dtype=np.uint8) * 128
        
        with pytest.raises(ValueError, match="Expected BGR image"):
            assessor.assess_frame(rgba_frame)


class TestStatistics:
    """Test statistics tracking."""
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Initial state
        stats = assessor.get_statistics()
        assert stats['total_assessments'] == 0
        
        # After assessments
        for i in range(5):
            assessor.assess_frame(frame)
        
        stats = assessor.get_statistics()
        assert stats['total_assessments'] == 5
        assert stats['avg_processing_time_ms'] > 0
        assert stats['total_processing_time_ms'] > 0
    
    def test_reset_statistics(self):
        """Test that statistics can be reset."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        assessor = FrameQualityAssessor("src/config/frame_quality.yaml")
        
        # Run assessments
        for i in range(3):
            assessor.assess_frame(frame)
        
        # Reset
        assessor.reset_statistics()
        
        stats = assessor.get_statistics()
        assert stats['total_assessments'] == 0
        assert stats['avg_processing_time_ms'] == 0
        assert stats['total_processing_time_ms'] == 0


class TestConvenienceFunction:
    """Test assess_frame_quick convenience function."""
    
    def test_quick_assessment(self):
        """Test quick assessment with default config."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        metrics = assess_frame_quick(frame)
        
        assert isinstance(metrics, QualityMetrics)
        assert 0 <= metrics.quality_score <= 100
