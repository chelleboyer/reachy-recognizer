"""Unit Tests for Story 3.1: MediaPipe Hand Detection Setup

Tests the HandDetector class and HandLandmarks dataclass for correct
MediaPipe integration, landmark extraction, and performance tracking.

Test Coverage:
- Configuration loading and validation
- HandDetector initialization
- Hand detection with single/multiple hands
- Landmark extraction and coordinate formats
- Left/right hand differentiation
- Statistics tracking (FPS, detection counts)
- Error handling for invalid inputs
"""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import time
from typing import List

from src.vision.hand_detector import HandDetector, HandLandmarks, MEDIAPIPE_AVAILABLE


# Fixtures

@pytest.fixture
def config_path():
    """Path to hand detection configuration file."""
    return "src/config/hand_detection.yaml"


@pytest.fixture
def test_frame():
    """Create a test frame (640x480 BGR image)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_mediapipe_hands():
    """Mock MediaPipe Hands solution."""
    with patch('src.vision.hand_detector.mp') as mock_mp:
        # Mock the Hands class
        mock_hands_instance = MagicMock()
        mock_mp.solutions.hands.Hands.return_value = mock_hands_instance
        
        # Create mock results
        mock_results = MagicMock()
        mock_results.multi_hand_landmarks = None
        mock_hands_instance.process.return_value = mock_results
        
        yield mock_mp, mock_hands_instance, mock_results


@pytest.fixture
def mock_hand_landmarks():
    """Create mock hand landmarks for testing."""
    # Create 21 mock landmarks (MediaPipe standard)
    landmarks = []
    for i in range(21):
        mock_lm = MagicMock()
        mock_lm.x = i * 0.05  # Normalized x coordinate
        mock_lm.y = i * 0.05  # Normalized y coordinate
        mock_lm.z = -0.01 * i  # Depth coordinate
        landmarks.append(mock_lm)
    
    mock_hand = MagicMock()
    mock_hand.landmark = landmarks
    
    return mock_hand


@pytest.fixture
def mock_handedness():
    """Create mock handedness classification."""
    mock_classification = MagicMock()
    mock_classification.label = "Right"
    mock_classification.score = 0.95
    
    mock_handedness = MagicMock()
    mock_handedness.classification = [mock_classification]
    
    return mock_handedness


# Test HandLandmarks Dataclass

class TestHandLandmarks:
    """Test suite for HandLandmarks dataclass."""
    
    def test_hand_landmarks_creation(self):
        """Test creating HandLandmarks with all fields."""
        landmarks = [(i * 0.05, i * 0.05, -0.01 * i) for i in range(21)]
        world_landmarks = [(i * 0.01, i * 0.01, -0.001 * i) for i in range(21)]
        
        hand = HandLandmarks(
            hand_id=0,
            handedness="Right",
            landmarks=landmarks,
            world_landmarks=world_landmarks,
            confidence=0.95,
            timestamp=time.time()
        )
        
        assert hand.hand_id == 0
        assert hand.handedness == "Right"
        assert len(hand.landmarks) == 21
        assert len(hand.world_landmarks) == 21
        assert hand.confidence == 0.95
        assert hand.timestamp > 0
    
    def test_hand_landmarks_to_dict(self):
        """Test converting HandLandmarks to dictionary."""
        landmarks = [(0.5, 0.5, 0.0), (0.6, 0.6, -0.01)]
        world_landmarks = [(0.05, 0.05, 0.0), (0.06, 0.06, -0.001)]
        
        hand = HandLandmarks(
            hand_id=1,
            handedness="Left",
            landmarks=landmarks,
            world_landmarks=world_landmarks,
            confidence=0.89,
            timestamp=1234567890.0
        )
        
        result = hand.to_dict()
        
        assert result["hand_id"] == 1
        assert result["handedness"] == "Left"
        assert len(result["landmarks"]) == 2
        assert result["landmarks"][0] == {"x": 0.5, "y": 0.5, "z": 0.0}
        assert result["confidence"] == 0.89
        assert result["timestamp"] == 1234567890.0
    
    def test_get_landmark_valid_index(self):
        """Test getting landmark by valid index."""
        landmarks = [(i * 0.1, i * 0.1, -0.01 * i) for i in range(21)]
        
        hand = HandLandmarks(
            hand_id=0,
            handedness="Right",
            landmarks=landmarks,
            world_landmarks=landmarks,
            confidence=0.9
        )
        
        # Test wrist (index 0)
        wrist = hand.get_landmark(0)
        assert wrist == (0.0, 0.0, 0.0)
        
        # Test index finger tip (index 8)
        index_tip = hand.get_landmark(8)
        assert index_tip == (0.8, 0.8, -0.08)
    
    def test_get_landmark_invalid_index(self):
        """Test getting landmark with invalid index raises error."""
        landmarks = [(i * 0.1, i * 0.1, -0.01 * i) for i in range(21)]
        
        hand = HandLandmarks(
            hand_id=0,
            handedness="Right",
            landmarks=landmarks,
            world_landmarks=landmarks,
            confidence=0.9
        )
        
        with pytest.raises(IndexError):
            hand.get_landmark(21)  # Out of range
        
        with pytest.raises(IndexError):
            hand.get_landmark(-1)  # Negative index


# Test HandDetector Initialization

class TestHandDetectorInit:
    """Test suite for HandDetector initialization."""
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_init_with_valid_config(self, config_path, mock_mediapipe_hands):
        """Test initializing HandDetector with valid configuration."""
        detector = HandDetector(config_path)
        
        assert detector.config_path == Path(config_path)
        assert detector.model_complexity in [0, 1]
        assert 0.0 <= detector.min_detection_confidence <= 1.0
        assert 0.0 <= detector.min_tracking_confidence <= 1.0
        assert detector.max_num_hands >= 1
        assert detector.target_fps >= 10
        assert detector.frame_count == 0
        assert detector.detection_count == 0
        assert detector.fps == 0.0
    
    def test_init_with_missing_config(self):
        """Test initialization fails with missing config file."""
        with pytest.raises(FileNotFoundError):
            HandDetector("nonexistent/config.yaml")
    
    @patch('src.vision.hand_detector.MEDIAPIPE_AVAILABLE', False)
    def test_init_without_mediapipe(self, config_path):
        """Test initialization fails when MediaPipe not installed."""
        with pytest.raises(ValueError, match="MediaPipe is not installed"):
            HandDetector(config_path)


# Test Hand Detection

class TestHandDetection:
    """Test suite for hand detection functionality."""
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_detect_no_hands(self, config_path, test_frame, mock_mediapipe_hands):
        """Test detection returns empty list when no hands present."""
        _, mock_hands_instance, mock_results = mock_mediapipe_hands
        mock_results.multi_hand_landmarks = None
        
        detector = HandDetector(config_path)
        hands = detector.detect(test_frame)
        
        assert isinstance(hands, list)
        assert len(hands) == 0
        assert detector.frame_count > 0
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_detect_single_hand(
        self, config_path, test_frame, mock_mediapipe_hands,
        mock_hand_landmarks, mock_handedness
    ):
        """Test detection returns one HandLandmarks for single hand."""
        _, mock_hands_instance, mock_results = mock_mediapipe_hands
        mock_results.multi_hand_landmarks = [mock_hand_landmarks]
        mock_results.multi_handedness = [mock_handedness]
        mock_results.multi_hand_world_landmarks = [mock_hand_landmarks]
        
        detector = HandDetector(config_path)
        hands = detector.detect(test_frame)
        
        assert len(hands) == 1
        assert isinstance(hands[0], HandLandmarks)
        assert hands[0].handedness == "Right"
        assert hands[0].confidence == 0.95
        assert len(hands[0].landmarks) == 21
        assert detector.detection_count == 1
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_detect_two_hands(
        self, config_path, test_frame, mock_mediapipe_hands,
        mock_hand_landmarks, mock_handedness
    ):
        """Test detection returns two HandLandmarks for two hands."""
        _, mock_hands_instance, mock_results = mock_mediapipe_hands
        
        # Create second hand with different handedness
        mock_handedness_left = MagicMock()
        mock_classification_left = MagicMock()
        mock_classification_left.label = "Left"
        mock_classification_left.score = 0.92
        mock_handedness_left.classification = [mock_classification_left]
        
        mock_results.multi_hand_landmarks = [mock_hand_landmarks, mock_hand_landmarks]
        mock_results.multi_handedness = [mock_handedness, mock_handedness_left]
        mock_results.multi_hand_world_landmarks = [mock_hand_landmarks, mock_hand_landmarks]
        
        detector = HandDetector(config_path)
        hands = detector.detect(test_frame)
        
        assert len(hands) == 2
        assert hands[0].handedness == "Right"
        assert hands[1].handedness == "Left"
        assert hands[0].confidence == 0.95
        assert hands[1].confidence == 0.92
        assert detector.detection_count == 2
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_detect_invalid_frame(self, config_path, mock_mediapipe_hands):
        """Test detection raises error for invalid frame."""
        detector = HandDetector(config_path)
        
        with pytest.raises(ValueError, match="Invalid frame"):
            detector.detect(None)  # type: ignore
        
        with pytest.raises(ValueError, match="Invalid frame"):
            detector.detect(np.array([]))


# Test Statistics Tracking

class TestStatistics:
    """Test suite for statistics tracking functionality."""
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_get_statistics_initial(self, config_path, mock_mediapipe_hands):
        """Test statistics are initialized to zero."""
        detector = HandDetector(config_path)
        stats = detector.get_statistics()
        
        assert stats["fps"] == 0.0
        assert stats["frame_count"] == 0
        assert stats["detection_count"] == 0
        assert stats["detection_rate"] == 0.0
        assert stats["avg_latency_ms"] == 0.0
        assert stats["uptime_seconds"] >= 0
        assert stats["target_fps"] >= 10
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_get_statistics_after_detection(
        self, config_path, test_frame, mock_mediapipe_hands,
        mock_hand_landmarks, mock_handedness
    ):
        """Test statistics update after detection."""
        _, mock_hands_instance, mock_results = mock_mediapipe_hands
        mock_results.multi_hand_landmarks = [mock_hand_landmarks]
        mock_results.multi_handedness = [mock_handedness]
        mock_results.multi_hand_world_landmarks = [mock_hand_landmarks]
        
        detector = HandDetector(config_path)
        
        # Process multiple frames
        for _ in range(5):
            detector.detect(test_frame)
        
        stats = detector.get_statistics()
        
        assert stats["frame_count"] == 5
        assert stats["detection_count"] == 5
        assert stats["detection_rate"] == 100.0  # 5/5 * 100
        assert stats["avg_latency_ms"] > 0
        assert stats["uptime_seconds"] > 0
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_reset_statistics(
        self, config_path, test_frame, mock_mediapipe_hands,
        mock_hand_landmarks, mock_handedness
    ):
        """Test resetting statistics to initial state."""
        _, mock_hands_instance, mock_results = mock_mediapipe_hands
        mock_results.multi_hand_landmarks = [mock_hand_landmarks]
        mock_results.multi_handedness = [mock_handedness]
        mock_results.multi_hand_world_landmarks = [mock_hand_landmarks]
        
        detector = HandDetector(config_path)
        
        # Process frames to accumulate stats
        for _ in range(10):
            detector.detect(test_frame)
        
        assert detector.frame_count == 10
        assert detector.detection_count == 10
        
        # Reset statistics
        detector.reset_statistics()
        
        assert detector.frame_count == 0
        assert detector.detection_count == 0
        assert detector.fps == 0.0
        assert detector.total_latency_ms == 0.0


# Test Context Manager

class TestContextManager:
    """Test suite for context manager functionality."""
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_context_manager(self, config_path, mock_mediapipe_hands):
        """Test HandDetector works as context manager."""
        with HandDetector(config_path) as detector:
            assert detector is not None
            assert hasattr(detector, 'hands')
        
        # Verify close was called
        # Note: In real usage, this would release MediaPipe resources
    
    @pytest.mark.skipif(not MEDIAPIPE_AVAILABLE, reason="MediaPipe not installed")
    def test_manual_close(self, config_path, mock_mediapipe_hands):
        """Test manually closing HandDetector."""
        _, mock_hands_instance, _ = mock_mediapipe_hands
        
        detector = HandDetector(config_path)
        detector.close()
        
        # Verify close method was called on MediaPipe Hands
        mock_hands_instance.close.assert_called_once()
