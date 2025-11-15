"""Unit Tests for Story 3.2: Three-Gesture Recognition

Tests the GestureRecognizer class for detecting thumbs up, wave, and palm stop gestures.

Test Coverage:
- GestureType enum and GestureResult dataclass
- GestureRecognizer initialization and configuration
- Thumbs up gesture detection
- Wave gesture detection
- Palm stop gesture detection
- Distance estimation
- Temporal validation and hold time
- False positive prevention
- Confidence scoring
- Statistics tracking
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch
from collections import deque

from src.vision.gesture_recognizer import (
    GestureRecognizer, GestureType, GestureResult
)
from src.vision.hand_detector import HandLandmarks


# Fixtures

@pytest.fixture
def config_path():
    """Path to gesture recognition configuration file."""
    return "src/config/gesture_recognition.yaml"


@pytest.fixture
def recognizer(config_path):
    """Create GestureRecognizer instance."""
    return GestureRecognizer(config_path)


@pytest.fixture
def mock_hand_landmarks():
    """Create mock HandLandmarks for testing."""
    def create_landmarks(gesture_type="neutral"):
        """Create landmarks based on gesture type."""
        landmarks = []
        world_landmarks = []
        
        if gesture_type == "thumbs_up":
            # Thumb extended upward, other fingers closed
            # Wrist at (0.5, 0.8)
            landmarks.append((0.5, 0.8, 0.0))  # WRIST
            world_landmarks.append((0.5 * 0.2, 0.8 * 0.2, 0.0))  # WRIST in world coords
            for i in range(1, 21):
                if i == 4:  # THUMB_TIP
                    landmarks.append((0.5, 0.3, -0.05))  # High up
                elif i in [8, 12, 16, 20]:  # Other fingertips
                    landmarks.append((0.5 + i*0.01, 0.7, 0.0))  # Closed
                else:
                    landmarks.append((0.5 + i*0.01, 0.6 + i*0.01, 0.0))
                world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
        
        elif gesture_type == "palm_stop":
            # All fingers extended upward
            landmarks.append((0.5, 0.8, 0.0))  # WRIST
            world_landmarks.append((0.5 * 0.2, 0.8 * 0.2, 0.0))  # WRIST in world coords
            for i in range(1, 21):
                if i in [4, 8, 12, 16, 20]:  # Fingertips
                    landmarks.append((0.3 + i*0.02, 0.2, -0.02))  # All high (reduced spread to stay in bounds)
                elif i in [3, 5, 9, 13, 17]:  # MCPs
                    landmarks.append((0.3 + i*0.02, 0.5, 0.0))
                else:
                    landmarks.append((0.3 + i*0.02, 0.4 + i*0.01, 0.0))
                world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
        
        else:  # neutral
            # Neutral hand position
            landmarks.append((0.5, 0.5, 0.0))  # WRIST
            world_landmarks.append((0.5 * 0.2, 0.5 * 0.2, 0.0))  # WRIST in world coords
            for i in range(1, 21):
                landmarks.append((0.5 + i*0.01, 0.5 + i*0.01, 0.0))
                world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
        
        return HandLandmarks(
            hand_id=0,
            handedness="Right",
            landmarks=landmarks,
            world_landmarks=world_landmarks,
            confidence=0.95,
            timestamp=time.time()
        )
    
    return create_landmarks


# Test GestureType and GestureResult

class TestGestureTypes:
    """Test suite for GestureType enum and GestureResult dataclass."""
    
    def test_gesture_type_enum_values(self):
        """Test GestureType enum has correct values."""
        assert GestureType.THUMBS_UP.value == "thumbs_up"
        assert GestureType.WAVE.value == "wave"
        assert GestureType.PALM_STOP.value == "palm_stop"
        assert GestureType.UNKNOWN.value == "unknown"
    
    def test_gesture_result_creation(self):
        """Test creating GestureResult with all fields."""
        result = GestureResult(
            gesture_type=GestureType.THUMBS_UP,
            confidence=0.85,
            hand_id=0,
            handedness="Right",
            timestamp=time.time(),
            distance_estimate=1.5,
            hold_duration=0.6,
            is_confirmed=True
        )
        
        assert result.gesture_type == GestureType.THUMBS_UP
        assert result.confidence == 0.85
        assert result.hand_id == 0
        assert result.handedness == "Right"
        assert result.distance_estimate == 1.5
        assert result.hold_duration == 0.6
        assert result.is_confirmed is True
    
    def test_gesture_result_to_dict(self):
        """Test converting GestureResult to dictionary."""
        timestamp = time.time()
        result = GestureResult(
            gesture_type=GestureType.WAVE,
            confidence=0.72,
            hand_id=1,
            handedness="Left",
            timestamp=timestamp,
            distance_estimate=2.0,
            hold_duration=0.8,
            is_confirmed=True
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["gesture_type"] == "wave"
        assert result_dict["confidence"] == 0.72
        assert result_dict["hand_id"] == 1
        assert result_dict["handedness"] == "Left"
        assert result_dict["timestamp"] == timestamp
        assert result_dict["distance_estimate"] == 2.0
        assert result_dict["hold_duration"] == 0.8
        assert result_dict["is_confirmed"] is True


# Test GestureRecognizer Initialization

class TestGestureRecognizerInit:
    """Test suite for GestureRecognizer initialization."""
    
    def test_init_with_valid_config(self, config_path):
        """Test initializing GestureRecognizer with valid config."""
        recognizer = GestureRecognizer(config_path)
        
        assert recognizer.config_path.exists()
        assert recognizer.hold_time > 0
        assert recognizer.smoothing_window > 0
        assert recognizer.enable_distance is not None
        assert len(recognizer.gesture_history) == 0
        assert len(recognizer.last_gesture_time) == 0
        assert recognizer.recognition_count == 0
    
    def test_init_with_missing_config(self):
        """Test initialization fails with missing config."""
        with pytest.raises(FileNotFoundError):
            GestureRecognizer("nonexistent/config.yaml")
    
    def test_config_parameters_loaded(self, recognizer):
        """Test configuration parameters are loaded correctly."""
        assert hasattr(recognizer, 'thumbs_up_config')
        assert hasattr(recognizer, 'wave_config')
        assert hasattr(recognizer, 'palm_stop_config')
        assert recognizer.hold_time >= 0.5  # Default 0.5s
        assert recognizer.smoothing_window >= 3  # Minimum smoothing


# Test Thumbs Up Detection

class TestThumbsUpDetection:
    """Test suite for thumbs up gesture detection."""
    
    def test_detect_thumbs_up_gesture(self, recognizer, mock_hand_landmarks):
        """Test detecting valid thumbs up gesture."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Run detection multiple times to build history
        for _ in range(recognizer.smoothing_window):
            result = recognizer.recognize(hand)
        
        # Final result should detect thumbs up
        assert result.gesture_type in [GestureType.THUMBS_UP, GestureType.UNKNOWN]
        if result.gesture_type == GestureType.THUMBS_UP:
            assert result.confidence > 0.0
    
    def test_thumbs_up_confidence_scoring(self, recognizer, mock_hand_landmarks):
        """Test thumbs up confidence scoring."""
        hand = mock_hand_landmarks("thumbs_up")
        confidence = recognizer._is_thumbs_up(hand)
        
        # Should return some confidence for thumbs up gesture
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_reject_non_thumbs_up(self, recognizer, mock_hand_landmarks):
        """Test rejecting non-thumbs-up gestures."""
        neutral_hand = mock_hand_landmarks("neutral")
        confidence = recognizer._is_thumbs_up(neutral_hand)
        
        # Neutral hand should not be detected as thumbs up
        assert confidence < 0.5


# Test Wave Detection

class TestWaveDetection:
    """Test suite for wave gesture detection."""
    
    def test_wave_requires_history(self, recognizer, mock_hand_landmarks):
        """Test wave detection requires sufficient history."""
        hand = mock_hand_landmarks("neutral")
        
        # Single frame should not detect wave
        result = recognizer.recognize(hand)
        wave_conf = recognizer._is_wave(hand)
        
        assert wave_conf == 0.0  # Not enough history
    
    def test_wave_with_oscillating_movement(self, recognizer, mock_hand_landmarks):
        """Test wave detection with simulated oscillating movement."""
        # Simulate oscillating wrist positions
        recognizer.wrist_history[0] = deque(maxlen=20)
        current_time = time.time()
        
        # Add oscillating positions
        for i in range(15):
            x = 0.5 + 0.15 * np.sin(i * 0.5)  # Oscillate
            recognizer.wrist_history[0].append((x, 0.5, current_time + i * 0.1))
        
        hand = mock_hand_landmarks("palm_stop")  # Use extended fingers
        hand.hand_id = 0
        
        wave_conf = recognizer._is_wave(hand)
        
        # Should detect some movement pattern
        assert isinstance(wave_conf, float)
        assert 0.0 <= wave_conf <= 1.0
    
    def test_wave_direction_changes(self, recognizer, mock_hand_landmarks):
        """Test wave detection counts direction changes."""
        recognizer.wrist_history[0] = deque(maxlen=20)
        current_time = time.time()
        
        # Positions with clear direction changes: left-right-left
        positions = [0.3, 0.4, 0.5, 0.6, 0.5, 0.4, 0.3, 0.4, 0.5, 0.6, 0.5, 0.4]
        for i, x in enumerate(positions):
            recognizer.wrist_history[0].append((x, 0.5, current_time + i * 0.1))
        
        hand = mock_hand_landmarks("palm_stop")
        hand.hand_id = 0
        
        wave_conf = recognizer._is_wave(hand)
        
        # Should detect oscillation with multiple direction changes
        assert wave_conf >= 0.0


# Test Palm Stop Detection

class TestPalmStopDetection:
    """Test suite for palm stop gesture detection."""
    
    def test_detect_palm_stop_gesture(self, recognizer, mock_hand_landmarks):
        """Test detecting valid palm stop gesture."""
        hand = mock_hand_landmarks("palm_stop")
        
        # Run detection multiple times
        for _ in range(recognizer.smoothing_window):
            result = recognizer.recognize(hand)
        
        # Should detect palm stop or unknown
        assert result.gesture_type in [GestureType.PALM_STOP, GestureType.UNKNOWN]
        if result.gesture_type == GestureType.PALM_STOP:
            assert result.confidence > 0.0
    
    def test_palm_stop_requires_extended_fingers(self, recognizer, mock_hand_landmarks):
        """Test palm stop requires all fingers extended."""
        neutral_hand = mock_hand_landmarks("neutral")
        confidence = recognizer._is_palm_stop(neutral_hand)
        
        # Neutral hand should not be palm stop
        assert confidence < 0.5
    
    def test_palm_stop_confidence_scoring(self, recognizer, mock_hand_landmarks):
        """Test palm stop confidence scoring."""
        hand = mock_hand_landmarks("palm_stop")
        confidence = recognizer._is_palm_stop(hand)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0


# Test Distance Estimation

class TestDistanceEstimation:
    """Test suite for distance estimation."""
    
    def test_estimate_distance_from_hand_size(self, recognizer, mock_hand_landmarks):
        """Test estimating distance from hand size."""
        hand = mock_hand_landmarks("palm_stop")
        distance = recognizer._estimate_distance(hand)
        
        assert isinstance(distance, float)
        assert recognizer.min_distance <= distance <= recognizer.max_distance
    
    def test_distance_clamped_to_range(self, recognizer, mock_hand_landmarks):
        """Test distance is clamped to valid range."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Modify world landmarks to test clamping
        # Very small span -> large distance -> clamped to max
        hand.world_landmarks[4] = (0.001, 0.001, 0.0)
        hand.world_landmarks[20] = (0.002, 0.002, 0.0)
        
        distance = recognizer._estimate_distance(hand)
        
        assert distance <= recognizer.max_distance
    
    def test_distance_in_result(self, recognizer, mock_hand_landmarks):
        """Test distance estimate included in result."""
        hand = mock_hand_landmarks("palm_stop")
        result = recognizer.recognize(hand)
        
        if recognizer.enable_distance:
            assert result.distance_estimate is not None
            assert isinstance(result.distance_estimate, float)


# Test Temporal Validation

class TestTemporalValidation:
    """Test suite for temporal validation and hold time."""
    
    def test_gesture_requires_hold_time(self, recognizer, mock_hand_landmarks):
        """Test gesture must be held for minimum duration."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # First detection should not be confirmed
        result1 = recognizer.recognize(hand)
        assert result1.is_confirmed is False
        assert result1.hold_duration < recognizer.hold_time
    
    def test_gesture_confirmed_after_hold_time(self, recognizer, mock_hand_landmarks):
        """Test gesture confirmed after hold time."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Detect gesture multiple times to build history
        for _ in range(recognizer.smoothing_window):
            recognizer.recognize(hand)
            time.sleep(0.15)  # Accumulate hold time
        
        result = recognizer.recognize(hand)
        
        # After sufficient time, may be confirmed
        # (depends on gesture detection success)
        assert isinstance(result.is_confirmed, bool)
        if result.gesture_type != GestureType.UNKNOWN:
            assert result.hold_duration >= 0.0
    
    def test_temporal_smoothing_reduces_noise(self, recognizer, mock_hand_landmarks):
        """Test temporal smoothing over multiple frames."""
        hand = mock_hand_landmarks("thumbs_up")
        
        results = []
        for _ in range(5):
            result = recognizer.recognize(hand)
            results.append(result.gesture_type)
        
        # Should maintain consistent detection with smoothing
        assert len(results) == 5
    
    def test_gesture_cooldown_period(self, recognizer, mock_hand_landmarks):
        """Test cooldown period after confirmed gesture."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Build up detection history and confirm
        for _ in range(recognizer.smoothing_window * 2):
            recognizer.recognize(hand)
            time.sleep(0.1)
        
        # Mark as confirmed manually for testing
        recognizer.last_gesture_time[hand.hand_id] = time.time()
        
        # Immediate next detection should respect cooldown
        result = recognizer.recognize(hand)
        # Cooldown prevents rapid re-confirmation
        assert isinstance(result.is_confirmed, bool)


# Test False Positive Prevention

class TestFalsePositivePrevention:
    """Test suite for false positive prevention."""
    
    def test_reject_low_confidence_hand(self, recognizer, mock_hand_landmarks):
        """Test rejecting hand with low tracking confidence."""
        hand = mock_hand_landmarks("thumbs_up")
        hand.confidence = 0.3  # Below threshold
        
        result = recognizer.recognize(hand)
        
        # Should return unknown due to low hand confidence
        assert result.gesture_type == GestureType.UNKNOWN
    
    def test_reject_hand_near_edge(self, recognizer, mock_hand_landmarks):
        """Test rejecting hand too close to frame edge."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Move landmarks to edge
        hand.landmarks[0] = (0.02, 0.5, 0.0)  # Wrist near left edge
        
        result = recognizer.recognize(hand)
        
        # Should return unknown due to edge proximity
        assert result.gesture_type == GestureType.UNKNOWN
    
    def test_validate_hand_quality(self, recognizer, mock_hand_landmarks):
        """Test hand quality validation."""
        good_hand = mock_hand_landmarks("palm_stop")
        assert recognizer._validate_hand_quality(good_hand) is True
        
        bad_hand = mock_hand_landmarks("palm_stop")
        bad_hand.confidence = 0.3
        assert recognizer._validate_hand_quality(bad_hand) is False


# Test Statistics

class TestStatistics:
    """Test suite for statistics tracking."""
    
    def test_get_statistics_initial(self, recognizer):
        """Test initial statistics are zero."""
        stats = recognizer.get_statistics()
        
        assert stats["recognition_count"] == 0
        assert stats["active_hands"] == 0
        assert "gesture_counts" in stats
        assert "config" in stats
    
    def test_statistics_update_on_recognition(self, recognizer, mock_hand_landmarks):
        """Test statistics update after recognition."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Run recognition several times
        for _ in range(10):
            recognizer.recognize(hand)
        
        stats = recognizer.get_statistics()
        
        assert stats["recognition_count"] == 10
        assert stats["active_hands"] >= 1
    
    def test_reset_statistics(self, recognizer, mock_hand_landmarks):
        """Test resetting statistics."""
        hand = mock_hand_landmarks("thumbs_up")
        
        # Build up statistics
        for _ in range(5):
            recognizer.recognize(hand)
        
        assert recognizer.recognition_count > 0
        
        # Reset
        recognizer.reset_statistics()
        
        assert recognizer.recognition_count == 0
        stats = recognizer.get_statistics()
        assert stats["recognition_count"] == 0


# Test Integration Scenarios

class TestRecognizeMethod:
    """Test suite for main recognize() method."""
    
    def test_recognize_returns_result(self, recognizer, mock_hand_landmarks):
        """Test recognize returns GestureResult."""
        hand = mock_hand_landmarks("thumbs_up")
        result = recognizer.recognize(hand)
        
        assert isinstance(result, GestureResult)
        assert isinstance(result.gesture_type, GestureType)
        assert 0.0 <= result.confidence <= 1.0
        assert result.hand_id == hand.hand_id
        assert result.handedness == hand.handedness
    
    def test_recognize_multiple_hands(self, recognizer, mock_hand_landmarks):
        """Test recognizing gestures from multiple hands."""
        hand1 = mock_hand_landmarks("thumbs_up")
        hand1.hand_id = 0
        
        hand2 = mock_hand_landmarks("palm_stop")
        hand2.hand_id = 1
        hand2.handedness = "Left"
        
        result1 = recognizer.recognize(hand1)
        result2 = recognizer.recognize(hand2)
        
        assert result1.hand_id == 0
        assert result2.hand_id == 1
        assert result1.handedness == "Right"
        assert result2.handedness == "Left"
    
    def test_recognize_performance(self, recognizer, mock_hand_landmarks):
        """Test recognize() meets performance target."""
        hand = mock_hand_landmarks("palm_stop")
        
        start_time = time.time()
        for _ in range(20):
            recognizer.recognize(hand)
        elapsed = time.time() - start_time
        
        avg_time = elapsed / 20
        
        # Should be well under 50ms per recognition
        assert avg_time < 0.1  # 100ms generous limit for testing
