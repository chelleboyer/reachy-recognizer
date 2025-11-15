"""
Unit Tests for Story 1.3: Best Frame Selection & OCR

Tests the BestFrameSelector class, OCREngine, and frame selection strategies.
"""

import pytest
import numpy as np
import cv2
from pathlib import Path

from src.vision.best_frame_selector import (
    BestFrameSelector,
    SelectionResult,
    NoGoodFramesError,
    select_best_frame_quick
)
from src.vision.ocr_engine import (
    OCREngine,
    OCRResult,
    Box,
    extract_text_quick
)
from src.vision.frame_quality import QualityMetrics


# Mock CapturedFrame for testing
class MockCapturedFrame:
    def __init__(self, frame: np.ndarray, capture_id: str):
        self.frame = frame
        self.capture_id = capture_id


class TestBestFrameSelector:
    """Test frame selection logic."""
    
    def test_load_config(self):
        """Test loading configuration from YAML."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        assert selector.excellent_quality == 80
        assert selector.acceptable_quality == 60
        assert selector.minimum_quality == 60
        assert selector.max_frames_to_fuse == 3
    
    def test_missing_config_raises_error(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            BestFrameSelector("nonexistent_config.yaml")
    
    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config structure raises ValueError."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("other_section:\n  value: 123")
        
        with pytest.raises(ValueError, match="missing 'frame_selector'"):
            BestFrameSelector(str(config_file))


class TestSingleBestFrameSelection:
    """Test single best frame selection strategy."""
    
    def test_select_single_best_high_quality(self):
        """Test with one frame >80 quality, verify selected."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        # Create frames with quality scores: 85, 70, 65
        frames = [
            MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * 100, f"frame_{i}")
            for i in range(3)
        ]
        
        metrics = [
            QualityMetrics(85.0, 20.0, 90.0, False, False, 1.0, "frame_0", 5.0),
            QualityMetrics(70.0, 30.0, 80.0, False, False, 1.0, "frame_1", 5.0),
            QualityMetrics(65.0, 35.0, 75.0, False, False, 1.0, "frame_2", 5.0)
        ]
        
        result = selector.select_best_frames(frames, metrics)
        
        assert result.strategy == "single_best"
        assert result.selected_frames == [0]
        assert result.best_score == 85.0
        assert result.fused_frame is None
    
    def test_select_highest_when_multiple_excellent(self):
        """Test that highest score is selected when multiple frames >80."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [
            MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * i, f"frame_{i}")
            for i in range(3)
        ]
        
        metrics = [
            QualityMetrics(82.0, 15.0, 92.0, False, False, 1.0, "frame_0", 5.0),
            QualityMetrics(88.0, 10.0, 95.0, False, False, 1.0, "frame_1", 5.0),
            QualityMetrics(85.0, 12.0, 93.0, False, False, 1.0, "frame_2", 5.0)
        ]
        
        result = selector.select_best_frames(frames, metrics)
        
        assert result.strategy == "single_best"
        assert result.selected_frames == [1]  # Highest score
        assert result.best_score == 88.0


class TestMultiFrameFusion:
    """Test multi-frame fusion strategy."""
    
    def test_fuse_multiple_medium_quality(self):
        """Test with multiple frames 60-80, verify fusion."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        # Create frames with quality scores: 75, 70, 65 (all in fusion range)
        frames = [
            MockCapturedFrame(
                np.ones((480, 640, 3), dtype=np.uint8) * (100 + i*20), 
                f"frame_{i}"
            )
            for i in range(3)
        ]
        
        metrics = [
            QualityMetrics(75.0, 25.0, 80.0, False, False, 1.0, "frame_0", 5.0),
            QualityMetrics(70.0, 30.0, 75.0, False, False, 1.0, "frame_1", 5.0),
            QualityMetrics(65.0, 35.0, 70.0, False, False, 1.0, "frame_2", 5.0)
        ]
        
        result = selector.select_best_frames(frames, metrics)
        
        assert result.strategy == "multi_frame_fusion"
        assert len(result.selected_frames) == 3
        assert result.fused_frame is not None
        assert result.fused_frame.shape == (480, 640, 3)
        assert result.best_score == 75.0
    
    def test_fusion_weights_correct(self):
        """Verify fusion weights computed correctly."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        scores = [75.0, 70.0, 65.0]
        weights = selector._compute_fusion_weights(scores)
        
        # Weights should sum to 1.0
        assert abs(sum(weights) - 1.0) < 0.001
        
        # Higher score should have higher weight
        assert weights[0] > weights[1] > weights[2]
    
    def test_fusion_pixel_values(self):
        """Test that fused frame has weighted average pixel values."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        # Create frames with distinct pixel values
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 100
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 150
        frame3 = np.ones((100, 100, 3), dtype=np.uint8) * 200
        
        frames = [frame1, frame2, frame3]
        weights = [0.5, 0.3, 0.2]
        
        fused = selector._weighted_average_fusion(frames, weights)
        
        # Expected value: 100*0.5 + 150*0.3 + 200*0.2 = 135
        assert fused.shape == (100, 100, 3)
        assert abs(fused[0, 0, 0] - 135) < 2  # Allow small rounding error


class TestFailureHandling:
    """Test failure mode when all frames have low quality."""
    
    def test_failure_all_low_quality(self):
        """Test with all frames <60, verify failure mode."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [
            MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * i, f"frame_{i}")
            for i in range(3)
        ]
        
        metrics = [
            QualityMetrics(45.0, 50.0, 40.0, False, True, 1.0, "frame_0", 5.0),
            QualityMetrics(50.0, 45.0, 45.0, False, True, 1.0, "frame_1", 5.0),
            QualityMetrics(48.0, 48.0, 42.0, False, True, 1.0, "frame_2", 5.0)
        ]
        
        with pytest.raises(NoGoodFramesError):
            selector.select_best_frames(frames, metrics)
    
    def test_failure_logs_all_scores(self):
        """Test that failure mode logs all quality scores."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        assert selector.log_all_scores == True


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_frame_list_raises_error(self):
        """Test that empty frame list raises ValueError."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        with pytest.raises(ValueError, match="empty frame list"):
            selector.select_best_frames([], [])
    
    def test_mismatched_lengths_raises_error(self):
        """Test that mismatched frame/metrics lists raise ValueError."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8), "f1")]
        metrics = []
        
        with pytest.raises(ValueError, match="doesn't match"):
            selector.select_best_frames(frames, metrics)
    
    def test_single_frame_selection(self):
        """Test selection with only one frame."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * 100, "frame_0")]
        metrics = [QualityMetrics(85.0, 20.0, 90.0, False, False, 1.0, "frame_0", 5.0)]
        
        result = selector.select_best_frames(frames, metrics)
        
        assert result.strategy == "single_best"
        assert result.selected_frames == [0]


class TestStatistics:
    """Test selection statistics tracking."""
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [
            MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * 100, f"frame_{i}")
            for i in range(3)
        ]
        
        # Run some selections
        metrics_high = [
            QualityMetrics(85.0, 20.0, 90.0, False, False, 1.0, f"frame_{i}", 5.0)
            for i in range(3)
        ]
        selector.select_best_frames(frames, metrics_high)
        
        metrics_med = [
            QualityMetrics(70.0, 30.0, 75.0, False, False, 1.0, f"frame_{i}", 5.0)
            for i in range(3)
        ]
        selector.select_best_frames(frames, metrics_med)
        
        stats = selector.get_statistics()
        
        assert stats['total_selections'] == 2
        assert stats['strategy_counts']['single_best'] == 1
        assert stats['strategy_counts']['multi_frame_fusion'] == 1
    
    def test_reset_statistics(self):
        """Test that statistics can be reset."""
        selector = BestFrameSelector("src/config/frame_selection.yaml")
        
        frames = [MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * 100, "f")]
        metrics = [QualityMetrics(85.0, 20.0, 90.0, False, False, 1.0, "f", 5.0)]
        
        selector.select_best_frames(frames, metrics)
        selector.reset_statistics()
        
        stats = selector.get_statistics()
        assert stats['total_selections'] == 0


class TestOCREngine:
    """Test OCR engine functionality."""
    
    def test_mock_ocr_initialization(self):
        """Test initializing mock OCR engine."""
        engine = OCREngine(engine="mock")
        assert engine.engine_name == "mock"
    
    def test_invalid_engine_raises_error(self):
        """Test that invalid engine name raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported OCR engine"):
            OCREngine(engine="invalid_engine")
    
    def test_mock_ocr_extraction(self):
        """Test mock OCR text extraction."""
        engine = OCREngine(engine="mock")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        result = engine.extract_text(frame, frame_id="test_001")
        
        assert isinstance(result, OCRResult)
        assert len(result.detected_text) > 0
        assert len(result.confidence_scores) == len(result.detected_text)
        assert len(result.bounding_boxes) == len(result.detected_text)
        assert result.frame_id == "test_001"
        assert result.engine == "mock"
    
    def test_ocr_with_roi(self):
        """Test OCR with region of interest."""
        engine = OCREngine(engine="mock")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        roi = Box(x=100, y=100, width=200, height=150)
        
        result = engine.extract_text(frame, frame_id="roi_test", roi=roi)
        
        assert isinstance(result, OCRResult)
    
    def test_ocr_invalid_frame_raises_error(self):
        """Test that invalid frame raises ValueError."""
        engine = OCREngine(engine="mock")
        
        with pytest.raises(ValueError, match="None or empty"):
            engine.extract_text(None, frame_id="test")  # type: ignore[arg-type]
    
    def test_ocr_preprocessing(self):
        """Test that preprocessing is applied."""
        engine = OCREngine(engine="mock", config_path="src/config/frame_selection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        preprocessed = engine._preprocess_frame(frame)
        
        assert preprocessed is not None
        # Should be grayscale if configured
        if engine.do_grayscale:
            assert len(preprocessed.shape) == 2


class TestOCRResult:
    """Test OCRResult dataclass."""
    
    def test_ocr_result_to_dict(self):
        """Test converting OCRResult to dictionary."""
        result = OCRResult(
            detected_text=["MARLBORO", "RED"],
            confidence_scores=[0.95, 0.88],
            bounding_boxes=[Box(100, 50, 200, 40), Box(100, 100, 80, 30)],
            processing_time_ms=150.5,
            frame_id="test_frame",
            engine="mock"
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert result_dict['detected_text'] == ["MARLBORO", "RED"]
        assert len(result_dict['confidence_scores']) == 2
        assert len(result_dict['bounding_boxes']) == 2
        assert result_dict['frame_id'] == "test_frame"
        assert result_dict['text_count'] == 2


class TestOCRStatistics:
    """Test OCR statistics tracking."""
    
    def test_ocr_statistics_tracking(self):
        """Test that OCR statistics are tracked."""
        engine = OCREngine(engine="mock")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        for i in range(5):
            engine.extract_text(frame, frame_id=f"frame_{i}")
        
        stats = engine.get_statistics()
        
        assert stats['total_extractions'] == 5
        assert stats['avg_processing_time_ms'] > 0
        assert stats['engine'] == "mock"
    
    def test_ocr_reset_statistics(self):
        """Test that OCR statistics can be reset."""
        engine = OCREngine(engine="mock")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        engine.extract_text(frame)
        
        engine.reset_statistics()
        
        stats = engine.get_statistics()
        assert stats['total_extractions'] == 0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_select_best_frame_quick(self):
        """Test quick frame selection function."""
        frames = [MockCapturedFrame(np.ones((480, 640, 3), dtype=np.uint8) * 100, "f")]
        metrics = [QualityMetrics(85.0, 20.0, 90.0, False, False, 1.0, "f", 5.0)]
        
        result = select_best_frame_quick(frames, metrics)
        
        assert isinstance(result, SelectionResult)
        assert result.strategy == "single_best"
    
    def test_extract_text_quick(self):
        """Test quick OCR extraction function."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        result = extract_text_quick(frame, frame_id="quick_test", engine="mock")
        
        assert isinstance(result, OCRResult)
        assert result.frame_id == "quick_test"
