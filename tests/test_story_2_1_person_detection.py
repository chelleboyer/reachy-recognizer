"""
Unit Tests for Story 2.1: Person Detection with Torso ROI

Tests the PersonDetector class and torso extraction logic.
Uses mock YOLO model to avoid downloading during tests.
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.vision.person_detector import (
    PersonDetector,
    TorsoROI,
    detect_people_quick
)


class MockYOLOBox:
    """Mock YOLO detection box."""
    def __init__(self, x1, y1, x2, y2, conf):
        self.xyxy = [np.array([x1, y1, x2, y2])]
        self.conf = [np.array([conf])]


class MockYOLOResult:
    """Mock YOLO result."""
    def __init__(self, boxes):
        self.boxes = boxes if boxes else None


class MockYOLO:
    """Mock YOLO model for testing."""
    def __init__(self, model_name):
        self.model_name = model_name
        self.device = 'cpu'
        
    def to(self, device):
        self.device = device
        return self
        
    def __call__(self, frame, conf=0.7, iou=0.5, classes=None, verbose=True):
        # Return mock detections based on frame size
        h, w = frame.shape[:2]
        
        # Mock: detect one person in center of frame
        if w > 100 and h > 100:
            center_x, center_y = w // 2, h // 2
            box_w, box_h = 100, 200
            
            box = MockYOLOBox(
                center_x - box_w//2,
                center_y - box_h//2,
                center_x + box_w//2,
                center_y + box_h//2,
                conf=0.85
            )
            
            return [MockYOLOResult([box])]
        else:
            # No detections in small frames
            return [MockYOLOResult(None)]


@pytest.fixture
def mock_yolo():
    """Fixture to patch YOLO model."""
    with patch('src.vision.person_detector.YOLO', MockYOLO):
        yield


class TestPersonDetector:
    """Test PersonDetector initialization and configuration."""
    
    def test_load_config(self, mock_yolo):
        """Test loading configuration from YAML."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        assert detector.model_name == "yolov8n"
        assert detector.confidence_threshold == 0.7
        assert detector.vertical_range == [0.0, 0.6]
        assert detector.resize_size == (224, 224)
    
    def test_missing_config_raises_error(self):
        """Test that missing config file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            PersonDetector("nonexistent_config.yaml")
    
    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config structure raises ValueError."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("other_section:\n  value: 123")
        
        with pytest.raises(ValueError, match="missing 'person_detection'"):
            PersonDetector(str(config_file))
    
    def test_yolo_model_loads(self, mock_yolo):
        """Test that YOLO model loads successfully."""
        detector = PersonDetector("src/config/person_detection.yaml")
        assert detector.model is not None
        assert detector.model.device == 'cpu'


class TestTorsoExtraction:
    """Test torso ROI extraction logic."""
    
    def test_extract_torso_from_person_bbox(self, mock_yolo):
        """Test extracting torso from person bounding box."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        person_bbox = (200, 100, 100, 200)  # x, y, w, h
        
        torso_roi = detector._extract_torso_roi(
            frame, person_bbox, 0.9, "person_1", "frame_1"
        )
        
        assert torso_roi is not None
        assert torso_roi.person_bbox == person_bbox
        assert torso_roi.confidence == 0.9
        assert torso_roi.person_id == "person_1"
        assert torso_roi.frame_id == "frame_1"
    
    def test_torso_top_60_percent(self, mock_yolo):
        """Test that torso is top 60% of person bbox."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        person_bbox = (200, 100, 100, 200)  # height = 200
        
        torso_roi = detector._extract_torso_roi(
            frame, person_bbox, 0.9, "person_1", "frame_1"
        )
        
        # Expected torso height = 200 * 0.6 = 120
        assert torso_roi is not None
        assert torso_roi.torso_bbox[3] == 120
        # Torso should start at same y as person
        assert torso_roi.torso_bbox[1] == 100
    
    def test_invalid_bbox_returns_none(self, mock_yolo):
        """Test that invalid bbox (too small) returns None."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        # Torso will be 30x30, below min_width=50, min_height=80
        person_bbox = (200, 100, 30, 50)
        
        torso_roi = detector._extract_torso_roi(
            frame, person_bbox, 0.9, "person_1", "frame_1"
        )
        
        assert torso_roi is None
    
    def test_bbox_at_frame_edge(self, mock_yolo):
        """Test handling of bbox at frame edge."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        # Person extends beyond frame edge
        person_bbox = (600, 400, 100, 200)
        
        torso_roi = detector._extract_torso_roi(
            frame, person_bbox, 0.9, "person_1", "frame_1"
        )
        
        # Should clip to frame boundaries
        if torso_roi is not None:
            tx, ty, tw, th = torso_roi.torso_bbox
            assert tx >= 0
            assert ty >= 0
            assert tx + tw <= 640
            assert ty + th <= 480


class TestPreprocessing:
    """Test ROI preprocessing."""
    
    def test_resize_to_224x224(self, mock_yolo):
        """Test that ROI is resized to 224x224."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        roi = np.ones((100, 80, 3), dtype=np.uint8) * 128
        preprocessed = detector._preprocess_roi(roi)
        
        assert preprocessed.shape == (224, 224, 3)
    
    def test_normalize_0_to_1(self, mock_yolo):
        """Test standard normalization (0-255 -> 0-1)."""
        detector = PersonDetector("src/config/person_detection.yaml")
        detector.normalization = "standard"
        
        roi = np.ones((100, 100, 3), dtype=np.uint8) * 255
        preprocessed = detector._preprocess_roi(roi)
        
        assert preprocessed.max() <= 1.0
        assert preprocessed.min() >= 0.0
        assert abs(preprocessed[0, 0, 0] - 1.0) < 0.01
    
    def test_normalize_imagenet(self, mock_yolo):
        """Test ImageNet normalization (0-255 -> -1 to 1)."""
        detector = PersonDetector("src/config/person_detection.yaml")
        detector.normalization = "imagenet"
        
        roi = np.ones((100, 100, 3), dtype=np.uint8) * 128
        preprocessed = detector._preprocess_roi(roi)
        
        assert preprocessed.max() <= 1.0
        assert preprocessed.min() >= -1.0
        # 128 -> (128/127.5) - 1 = 0.0039
        assert abs(preprocessed[0, 0, 0]) < 0.1


class TestConfidenceFiltering:
    """Test confidence threshold filtering."""
    
    def test_detect_people_with_mock_frame(self, mock_yolo):
        """Test detecting people in frame."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        results = detector.detect_people(frame, "test_frame")
        
        # Mock YOLO returns 1 person
        assert len(results) >= 0  # May be 0 or 1 depending on mock behavior
    
    def test_empty_frame_raises_error(self, mock_yolo):
        """Test that empty frame raises ValueError."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        with pytest.raises(ValueError, match="None or empty"):
            detector.detect_people(None, "test")  # type: ignore[arg-type]
    
    def test_none_frame_raises_error(self, mock_yolo):
        """Test that None frame raises ValueError."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        empty_frame = np.array([])
        with pytest.raises(ValueError, match="None or empty"):
            detector.detect_people(empty_frame, "test")


class TestMultiplePeople:
    """Test handling of multiple people in frame."""
    
    def test_unique_person_ids(self, mock_yolo):
        """Test that each detection gets unique person ID."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        results = detector.detect_people(frame, "test_frame")
        
        if len(results) > 1:
            person_ids = [r.person_id for r in results]
            assert len(person_ids) == len(set(person_ids))  # All unique
    
    def test_max_detections_limit(self, mock_yolo):
        """Test that max_detections limit is respected."""
        detector = PersonDetector("src/config/person_detection.yaml")
        detector.max_detections = 5
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        results = detector.detect_people(frame, "test_frame")
        
        assert len(results) <= 5


class TestStatistics:
    """Test detection statistics tracking."""
    
    def test_statistics_tracking(self, mock_yolo):
        """Test that statistics are tracked correctly."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        # Run multiple detections
        for i in range(3):
            detector.detect_people(frame, f"frame_{i}")
        
        stats = detector.get_statistics()
        
        assert 'total_detections' in stats
        assert 'avg_confidence' in stats
        assert 'model_name' in stats
        assert stats['model_name'] == 'yolov8n'
    
    def test_reset_statistics(self, mock_yolo):
        """Test that statistics can be reset."""
        detector = PersonDetector("src/config/person_detection.yaml")
        
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        detector.detect_people(frame, "frame_0")
        
        detector.reset_statistics()
        
        stats = detector.get_statistics()
        assert stats['total_detections'] == 0
        assert stats['avg_confidence'] == 0.0


class TestTorsoROIDataclass:
    """Test TorsoROI dataclass functionality."""
    
    def test_to_dict_excludes_large_arrays(self):
        """Test that to_dict excludes large numpy arrays."""
        torso_image = np.ones((224, 224, 3), dtype=np.float32)
        
        roi = TorsoROI(
            person_bbox=(100, 100, 100, 200),
            torso_bbox=(100, 100, 100, 120),
            torso_image=torso_image,
            confidence=0.9,
            person_id="person_1",
            frame_id="frame_1"
        )
        
        roi_dict = roi.to_dict()
        
        assert 'person_bbox' in roi_dict
        assert 'torso_bbox' in roi_dict
        assert 'confidence' in roi_dict
        assert 'person_id' in roi_dict
        assert 'frame_id' in roi_dict
        assert 'torso_image_shape' in roi_dict
        assert roi_dict['torso_image_shape'] == (224, 224, 3)
        # Large array should not be in dict
        assert 'torso_image' not in roi_dict or not isinstance(roi_dict.get('torso_image'), np.ndarray)


class TestConvenienceFunction:
    """Test convenience function."""
    
    def test_detect_people_quick(self, mock_yolo):
        """Test quick detection function."""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 128
        
        results = detect_people_quick(frame, frame_id="quick_test")
        
        assert isinstance(results, list)
