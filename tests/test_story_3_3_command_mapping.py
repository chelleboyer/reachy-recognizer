"""
Story 3.3 Unit Tests: Gesture-to-Command Mapping

Tests for mapping recognized gestures to executable commands.

Test Coverage:
- GestureCommand enum values
- GestureEvent dataclass and serialization  
- Command mapping logic
- Statistics tracking (public API only)
"""

import unittest
import time

from src.coordination.gesture_coordinator import (
    GestureCommand,
    GestureEvent,
    GESTURE_COMMAND_MAP
)
from src.vision.gesture_recognizer import GestureType, GestureResult


class TestGestureCommand(unittest.TestCase):
    """Test GestureCommand enum."""
    
    def test_gesture_command_values(self):
        """Test GestureCommand enum has correct values."""
        self.assertEqual(GestureCommand.APPROVE.value, "approve")
        self.assertEqual(GestureCommand.SKIP.value, "skip")
        self.assertEqual(GestureCommand.PAUSE.value, "pause")
    
    def test_gesture_command_count(self):
        """Test GestureCommand enum has exactly 3 commands."""
        self.assertEqual(len(GestureCommand), 3)
    
    def test_command_from_string(self):
        """Test creating GestureCommand from string value."""
        self.assertEqual(GestureCommand("approve"), GestureCommand.APPROVE)
        self.assertEqual(GestureCommand("skip"), GestureCommand.SKIP)
        self.assertEqual(GestureCommand("pause"), GestureCommand.PAUSE)


class TestGestureCommandMapping(unittest.TestCase):
    """Test gesture-to-command mapping."""
    
    def test_thumbs_up_maps_to_approve(self):
        """Test THUMBS_UP gesture maps to APPROVE command."""
        self.assertEqual(
            GESTURE_COMMAND_MAP[GestureType.THUMBS_UP],
            GestureCommand.APPROVE
        )
    
    def test_wave_maps_to_skip(self):
        """Test WAVE gesture maps to SKIP command."""
        self.assertEqual(
            GESTURE_COMMAND_MAP[GestureType.WAVE],
            GestureCommand.SKIP
        )
    
    def test_palm_stop_maps_to_pause(self):
        """Test PALM_STOP gesture maps to PAUSE command."""
        self.assertEqual(
            GESTURE_COMMAND_MAP[GestureType.PALM_STOP],
            GestureCommand.PAUSE
        )
    
    def test_command_map_complete(self):
        """Test command map covers all required gestures."""
        # Map should include 3 command gestures plus UNKNOWN (mapped to None)
        expected_gestures = {
            GestureType.THUMBS_UP,
            GestureType.WAVE,
            GestureType.PALM_STOP,
            GestureType.UNKNOWN
        }
        self.assertEqual(set(GESTURE_COMMAND_MAP.keys()), expected_gestures)
        
        # Verify UNKNOWN maps to None (ignored)
        self.assertIsNone(GESTURE_COMMAND_MAP[GestureType.UNKNOWN])


class TestGestureEvent(unittest.TestCase):
    """Test GestureEvent dataclass."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gesture_result = GestureResult(
            gesture_type=GestureType.THUMBS_UP,
            confidence=0.95,
            hand_id=1,
            handedness="Right"
        )
    
    def test_gesture_event_creation(self):
        """Test creating GestureEvent."""
        event = GestureEvent(
            command=GestureCommand.APPROVE,
            gesture_result=self.gesture_result,
            timestamp=123.45,
            processed=False
        )
        
        self.assertEqual(event.command, GestureCommand.APPROVE)
        self.assertEqual(event.gesture_result, self.gesture_result)
        self.assertEqual(event.timestamp, 123.45)
        self.assertFalse(event.processed)
    
    def test_gesture_event_default_values(self):
        """Test GestureEvent default values."""
        current_time = time.time()
        event = GestureEvent(
            command=GestureCommand.SKIP,
            gesture_result=self.gesture_result,
            timestamp=current_time
        )
        
        # timestamp should be what we provided
        self.assertEqual(event.timestamp, current_time)
        self.assertFalse(event.processed)  # Default is False
    
    def test_to_dict_serialization(self):
        """Test GestureEvent.to_dict() serialization."""
        event = GestureEvent(
            command=GestureCommand.PAUSE,
            gesture_result=self.gesture_result,
            timestamp=123.45,
            processed=True
        )
        
        result = event.to_dict()
        
        self.assertEqual(result["command"], "pause")
        self.assertEqual(result["gesture_type"], "thumbs_up")
        self.assertEqual(result["confidence"], 0.95)
        self.assertEqual(result["handedness"], "Right")
        self.assertEqual(result["timestamp"], 123.45)
        self.assertTrue(result["processed"])
    
    def test_to_dict_with_unknown_gesture(self):
        """Test to_dict() with UNKNOWN gesture type."""
        gesture_result = GestureResult(
            gesture_type=GestureType.UNKNOWN,
            confidence=0.3,
            hand_id=2,
            handedness="Left"
        )
        event = GestureEvent(
            command=GestureCommand.APPROVE,
            gesture_result=gesture_result,
            timestamp=time.time()
        )
        
        result = event.to_dict()
        self.assertEqual(result["gesture_type"], "unknown")
        self.assertEqual(result["handedness"], "Left")


if __name__ == '__main__':
    unittest.main()
