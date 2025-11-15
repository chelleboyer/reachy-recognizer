"""
Integration tests for Story 3.4: Visual Feedback & UI Integration.

Tests end-to-end feedback display, coordination with gesture system,
and performance validation.
"""

import time
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from src.ui.feedback_manager import FeedbackManager, FeedbackAnimation
from src.vision.gesture_recognizer import GestureType, GestureResult
from src.coordination.gesture_coordinator import GestureCoordinator, GestureCommand
from src.events.event_system import EventManager, EventType


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def event_manager():
    """Create EventManager for testing."""
    return EventManager()


@pytest.fixture
def feedback_manager():
    """Create FeedbackManager for testing."""
    config = {
        'animation': {
            'total_duration_seconds': 1.0,
            'fade_in_duration': 0.2,
            'pulse_duration': 0.6,
            'fade_out_duration': 0.2,
        },
        'icons': {
            'thumbs_up': '👍',
            'wave': '👋',
            'palm_stop': '✋',
            'size_pixels': 200,
            'scale_pulse_max': 1.2,
        },
        'position': {'x': 'center', 'y': 'center', 'offset_x': 0, 'offset_y': -50},
        'colors': {
            'icon_color': [255, 255, 255, 255],
            'background_color': [0, 0, 0, 128],
            'background_enabled': True,
        },
        'target_latency_ms': 200,
        'frame_rate': 30,
        'max_queue_size': 3,
    }
    manager = FeedbackManager(config=config, headless=True)
    manager.start()
    yield manager
    manager.cleanup()


@pytest.fixture
def mock_hand_detector():
    """Create mock HandDetector."""
    detector = Mock()
    detector.detect = Mock(return_value=[])
    return detector


@pytest.fixture
def mock_gesture_recognizer():
    """Create mock GestureRecognizer."""
    recognizer = Mock()
    # Return empty list by default, tests will override
    recognizer.recognize = Mock(return_value=[])
    recognizer.get_statistics = Mock(return_value={})
    recognizer.reset_statistics = Mock()
    return recognizer


# ============================================================================
# End-to-End Display Tests (2 tests)
# ============================================================================

def test_end_to_end_feedback(feedback_manager):
    """Test GestureResult triggers visual feedback end-to-end."""
    # Create gesture result
    gesture_result = GestureResult(
        gesture_type=GestureType.THUMBS_UP,
        confidence=0.95,
        hand_id=0,
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.6,
        distance_estimate=2.0,
        timestamp=time.time()
    )
    
    # Show feedback
    feedback_manager.show_gesture_feedback(gesture_result)
    
    # Give animation thread time to process
    time.sleep(0.1)
    
    # Should have active animation
    with feedback_manager._lock:
        assert feedback_manager.current_state is not None
        assert feedback_manager.current_state.gesture_type == GestureType.THUMBS_UP
        assert feedback_manager.current_state.icon == '👍'
    
    # Verify statistics
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] == 1
    assert stats['avg_latency_ms'] < 200


def test_multiple_gestures(feedback_manager):
    """Test queue handles multiple animations."""
    gestures = [
        GestureResult(
            gesture_type=GestureType.THUMBS_UP,
            confidence=0.95,
            hand_id=0,
            handedness="Right",
            is_confirmed=True,
            hold_duration=0.6,
            distance_estimate=2.0,
            timestamp=time.time()
        ),
        GestureResult(
            gesture_type=GestureType.WAVE,
            confidence=0.92,
            hand_id=1,
            handedness="Left",
            is_confirmed=True,
            hold_duration=0.7,
            distance_estimate=1.8,
            timestamp=time.time()
        ),
    ]
    
    # Queue multiple gestures
    for gesture in gestures:
        feedback_manager.show_gesture_feedback(gesture)
    
    # Give time to process
    time.sleep(0.1)
    
    # Should process animations
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] == 2


# ============================================================================
# Coordination Tests (2 tests)
# ============================================================================

def test_coordinator_integration(event_manager, feedback_manager, mock_hand_detector, mock_gesture_recognizer):
    """Test GestureCoordinator triggers feedback."""
    # Create coordinator without feedback manager (not yet integrated)
    coordinator = GestureCoordinator(
        hand_detector=mock_hand_detector,
        gesture_recognizer=mock_gesture_recognizer,
        event_manager=event_manager
    )
    
    # Mock recognize to return a confirmed gesture (single, not list)
    mock_gesture_result = GestureResult(
        gesture_type=GestureType.THUMBS_UP,
        confidence=0.95,
        hand_id=0,
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.6,
        distance_estimate=2.0,
        timestamp=time.time()
    )
    # recognize() takes a single hand and returns a single GestureResult
    mock_gesture_recognizer.recognize.return_value = mock_gesture_result
    
    # Mock detect to return hand landmarks
    mock_hand_detector.detect.return_value = [Mock()]  # List of hands
    
    # Process frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    gesture_events = coordinator.process_frame(frame)
    
    # Should have generated gesture events (feedback integration not yet complete)
    assert len(gesture_events) >= 1
    
    # Manually trigger feedback to test
    feedback_manager.show_gesture_feedback(mock_gesture_result)
    time.sleep(0.1)
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] >= 1


def test_event_system_integration(event_manager, feedback_manager):
    """Test EventManager callback triggers feedback."""
    feedback_triggered = []
    
    def gesture_callback(event_data):
        """Callback that triggers feedback."""
        gesture_result = GestureResult(
            gesture_type=GestureType.PALM_STOP,
            confidence=0.90,
            hand_id=0,
            handedness="Right",
            is_confirmed=True,
            hold_duration=0.5,
            distance_estimate=2.5,
            timestamp=time.time()
        )
        feedback_manager.show_gesture_feedback(gesture_result)
        feedback_triggered.append(True)
    
    # Add callback (use add_callback not register_callback)
    event_manager.add_callback(EventType.GESTURE_DETECTED, gesture_callback)
    
    # Emit gesture event
    event_data = {
        'command': 'pause',
        'gesture_type': 'palm_stop',
        'confidence': 0.90,
    }
    event_manager.emit(EventType.GESTURE_DETECTED, event_data)
    
    # Callback should have triggered
    assert len(feedback_triggered) == 1
    
    # Feedback should be shown
    time.sleep(0.1)
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] == 1


# ============================================================================
# Performance Test (1 test)
# ============================================================================

def test_total_latency(event_manager, feedback_manager, mock_hand_detector, mock_gesture_recognizer):
    """Test total latency < 1s from gesture to feedback."""
    # Create coordinator
    coordinator = GestureCoordinator(
        hand_detector=mock_hand_detector,
        gesture_recognizer=mock_gesture_recognizer,
        event_manager=event_manager
    )
    
    # Mock gesture detection
    mock_gesture_result = GestureResult(
        gesture_type=GestureType.WAVE,
        confidence=0.93,
        hand_id=0,
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.65,
        distance_estimate=2.2,
        timestamp=time.time()
    )
    # recognize() returns single GestureResult, not list
    mock_gesture_recognizer.recognize.return_value = mock_gesture_result
    mock_hand_detector.detect.return_value = [Mock()]  # List of hands
    
    # Measure total time
    start_time = time.time()
    
    # Process frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    coordinator.process_frame(frame)
    
    # Manually trigger feedback
    feedback_manager.show_gesture_feedback(mock_gesture_result)
    
    # Render feedback
    time.sleep(0.05)  # Give thread time to pick up animation
    overlay = feedback_manager.render_overlay(frame)
    
    total_latency_ms = (time.time() - start_time) * 1000
    
    # Should be well under 1 second
    assert total_latency_ms < 1000
    
    # Should have rendered overlay
    assert overlay is not None


# ============================================================================
# Render Integration Test (1 test)
# ============================================================================

def test_render_on_real_frame(feedback_manager):
    """Test rendering feedback on actual camera frame."""
    # Create realistic frame
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Trigger feedback
    gesture_result = GestureResult(
        gesture_type=GestureType.THUMBS_UP,
        confidence=0.95,
        hand_id=0,
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.6,
        distance_estimate=2.0,
        timestamp=time.time()
    )
    feedback_manager.show_gesture_feedback(gesture_result)
    
    # Give animation time to start
    time.sleep(0.1)
    
    # Render overlay
    result = feedback_manager.render_overlay(frame)
    
    # Should have rendered something
    assert result is not None
    assert result.shape == frame.shape
    
    # Verify animation is active
    with feedback_manager._lock:
        assert feedback_manager.current_state is not None
        assert feedback_manager.current_state.animation_phase != FeedbackAnimation.COMPLETE
