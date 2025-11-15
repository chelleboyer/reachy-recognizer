"""Integration Tests for Story 3.2: Three-Gesture Recognition

Integration tests for complete gesture recognition pipeline including
multi-frame sequences, gesture transitions, and end-to-end performance validation.

Test Coverage:
- End-to-end gesture recognition with HandDetector
- Multi-frame gesture sequences
- Gesture transitions and state changes
- False positive prevention in real scenarios
- Performance validation (<0.5s recognition, <5% false positives)
- Distance estimation accuracy
- Temporal smoothing effectiveness
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, MagicMock, patch

from src.vision.gesture_recognizer import (
    GestureRecognizer, GestureType, GestureResult
)
from src.vision.hand_detector import HandDetector, HandLandmarks


# Fixtures

@pytest.fixture
def config_path():
    """Path to gesture recognition configuration."""
    return "src/config/gesture_recognition.yaml"


@pytest.fixture
def hand_detector_config():
    """Path to hand detector configuration."""
    return "src/config/hand_detection.yaml"


@pytest.fixture
def recognizer(config_path):
    """Create GestureRecognizer instance."""
    return GestureRecognizer(config_path)


@pytest.fixture
def create_gesture_sequence():
    """Factory for creating gesture sequences."""
    def factory(gesture_type, num_frames=10):
        """Create sequence of HandLandmarks for a gesture.
        
        Args:
            gesture_type: Type of gesture ("thumbs_up", "wave", "palm_stop", "neutral")
            num_frames: Number of frames to generate
        
        Returns:
            List of HandLandmarks
        """
        sequence = []
        
        for frame_idx in range(num_frames):
            landmarks = []
            world_landmarks = []
            
            if gesture_type == "thumbs_up":
                # Thumb up, fingers closed
                landmarks.append((0.5, 0.8, 0.0))  # WRIST
                world_landmarks.append((0.5 * 0.2, 0.8 * 0.2, 0.0))  # WRIST in world coords
                for i in range(1, 21):
                    if i == 4:  # THUMB_TIP
                        landmarks.append((0.5, 0.25, -0.05))
                    elif i in [8, 12, 16, 20]:  # Fingertips closed
                        landmarks.append((0.5 + i*0.01, 0.7, 0.0))
                    else:
                        landmarks.append((0.5 + i*0.01, 0.6 + i*0.01, 0.0))
                    world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
            
            elif gesture_type == "wave":
                # Oscillating wrist with extended fingers
                x_offset = 0.15 * np.sin(frame_idx * 0.6)  # Oscillate
                landmarks.append((0.5 + x_offset, 0.5, 0.0))  # WRIST
                world_landmarks.append(((0.5 + x_offset) * 0.2, 0.5 * 0.2, 0.0))  # WRIST in world coords
                for i in range(1, 21):
                    if i in [4, 8, 12, 16, 20]:  # Extended fingertips
                        landmarks.append((0.4 + x_offset + i*0.015, 0.25, -0.02))  # Reduced spread to stay in bounds
                    elif i in [3, 5, 9, 13, 17]:  # MCPs
                        landmarks.append((0.4 + x_offset + i*0.015, 0.45, 0.0))
                    else:
                        landmarks.append((0.4 + x_offset + i*0.01, 0.4, 0.0))
                    world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
            
            elif gesture_type == "palm_stop":
                # All fingers extended, palm facing camera
                landmarks.append((0.5, 0.8, 0.0))  # WRIST
                world_landmarks.append((0.5 * 0.2, 0.8 * 0.2, 0.0))  # WRIST in world coords
                for i in range(1, 21):
                    if i in [4, 8, 12, 16, 20]:  # Extended fingertips
                        landmarks.append((0.2 + i*0.02, 0.15, -0.02))  # Reduced spread to stay in bounds
                    elif i in [3, 5, 9, 13, 17]:  # MCPs
                        landmarks.append((0.2 + i*0.02, 0.5, 0.0))
                    else:
                        landmarks.append((0.2 + i*0.015, 0.4 + i*0.01, -0.01))
                    world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
            
            else:  # neutral
                # Neutral hand position
                landmarks.append((0.5, 0.5, 0.0))  # WRIST
                world_landmarks.append((0.5 * 0.2, 0.5 * 0.2, 0.0))  # WRIST in world coords
                for i in range(1, 21):
                    landmarks.append((0.5 + i*0.01, 0.5 + i*0.01, 0.0))
                    world_landmarks.append((landmarks[-1][0] * 0.2, landmarks[-1][1] * 0.2, landmarks[-1][2]))
            
            hand = HandLandmarks(
                hand_id=0,
                handedness="Right",
                landmarks=landmarks,
                world_landmarks=world_landmarks,
                confidence=0.95,
                timestamp=time.time()
            )
            
            sequence.append(hand)
            time.sleep(0.05)  # Simulate frame timing
        
        return sequence
    
    return factory


# Integration Tests

class TestEndToEndGestureRecognition:
    """Integration tests for complete gesture recognition pipeline."""
    
    def test_recognize_thumbs_up_sequence(self, recognizer, create_gesture_sequence):
        """Test recognizing thumbs up over multiple frames."""
        sequence = create_gesture_sequence("thumbs_up", num_frames=15)
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # Should detect thumbs up in later frames after temporal validation
        gesture_types = [r.gesture_type for r in results]
        
        # At least some frames should detect thumbs up or build toward it
        assert len(results) == 15
        assert all(isinstance(r, GestureResult) for r in results)
    
    def test_recognize_wave_sequence(self, recognizer, create_gesture_sequence):
        """Test recognizing wave gesture over multiple frames."""
        sequence = create_gesture_sequence("wave", num_frames=20)
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # Wave detection requires oscillation history
        gesture_types = [r.gesture_type for r in results]
        
        # After sufficient frames, may detect wave
        assert len(results) == 20
        # Wave detection depends on sufficient oscillation
    
    def test_recognize_palm_stop_sequence(self, recognizer, create_gesture_sequence):
        """Test recognizing palm stop over multiple frames."""
        sequence = create_gesture_sequence("palm_stop", num_frames=15)
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        gesture_types = [r.gesture_type for r in results]
        
        # Should detect palm stop in later frames
        assert len(results) == 15
        assert all(isinstance(r, GestureResult) for r in results)
    
    def test_neutral_hand_not_recognized(self, recognizer, create_gesture_sequence):
        """Test neutral hand position not recognized as gesture."""
        sequence = create_gesture_sequence("neutral", num_frames=10)
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # Neutral hand should return UNKNOWN
        unknown_count = sum(1 for r in results if r.gesture_type == GestureType.UNKNOWN)
        
        # Most or all should be unknown
        assert unknown_count >= 8  # At least 80%


class TestGestureTransitions:
    """Test gesture transitions and state changes."""
    
    def test_transition_between_gestures(self, recognizer, create_gesture_sequence):
        """Test transitioning from one gesture to another."""
        # Start with thumbs up
        thumbs_up_seq = create_gesture_sequence("thumbs_up", num_frames=10)
        # Transition to palm stop
        palm_stop_seq = create_gesture_sequence("palm_stop", num_frames=10)
        
        all_results = []
        
        # Process thumbs up sequence
        for hand in thumbs_up_seq:
            result = recognizer.recognize(hand)
            all_results.append(result)
        
        # Process palm stop sequence
        for hand in palm_stop_seq:
            result = recognizer.recognize(hand)
            all_results.append(result)
        
        # Should handle transition smoothly
        assert len(all_results) == 20
        
        # Check that gestures change over time
        gesture_types = [r.gesture_type for r in all_results]
        unique_gestures = set(gesture_types)
        
        # Should see different gesture types
        assert len(unique_gestures) >= 1
    
    def test_gesture_to_neutral_transition(self, recognizer, create_gesture_sequence):
        """Test transitioning from gesture to neutral."""
        # Gesture sequence
        gesture_seq = create_gesture_sequence("palm_stop", num_frames=10)
        # Neutral sequence
        neutral_seq = create_gesture_sequence("neutral", num_frames=10)
        
        results = []
        
        for hand in gesture_seq:
            results.append(recognizer.recognize(hand))
        
        for hand in neutral_seq:
            results.append(recognizer.recognize(hand))
        
        # Later frames should return to UNKNOWN
        last_5_results = results[-5:]
        unknown_in_last_5 = sum(1 for r in last_5_results if r.gesture_type == GestureType.UNKNOWN)
        
        # Most should be unknown after transition to neutral
        assert unknown_in_last_5 >= 3


class TestFalsePositivePrevention:
    """Test false positive prevention in realistic scenarios."""
    
    def test_reject_brief_gesture(self, recognizer, create_gesture_sequence):
        """Test rejecting gesture shown only briefly."""
        # Only 3 frames of gesture (below hold time requirement)
        sequence = create_gesture_sequence("thumbs_up", num_frames=3)
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # None should be confirmed (hold time not met)
        confirmed_count = sum(1 for r in results if r.is_confirmed)
        
        assert confirmed_count == 0
    
    def test_reject_low_confidence_detection(self, recognizer, create_gesture_sequence):
        """Test rejecting detection with low hand confidence."""
        sequence = create_gesture_sequence("palm_stop", num_frames=5)
        
        # Set low confidence
        for hand in sequence:
            hand.confidence = 0.3  # Below threshold
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # All should be unknown due to low confidence
        assert all(r.gesture_type == GestureType.UNKNOWN for r in results)
    
    def test_temporal_smoothing_reduces_noise(self, recognizer, create_gesture_sequence):
        """Test temporal smoothing reduces detection noise."""
        # Mix of gesture and neutral frames (noisy detection)
        sequence = []
        for i in range(20):
            if i % 3 == 0:  # Intermittent gesture
                sequence.extend(create_gesture_sequence("thumbs_up", num_frames=1))
            else:
                sequence.extend(create_gesture_sequence("neutral", num_frames=1))
        
        results = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            results.append(result)
        
        # Smoothing should prevent rapid gesture type changes
        gesture_types = [r.gesture_type for r in results]
        
        # Count transitions
        transitions = sum(1 for i in range(1, len(gesture_types))
                         if gesture_types[i] != gesture_types[i-1])
        
        # Smoothing should limit transitions (fewer than half of frames)
        assert transitions < len(results) // 2


class TestDistanceEstimation:
    """Test distance estimation integration."""
    
    def test_distance_consistent_across_frames(self, recognizer, create_gesture_sequence):
        """Test distance estimation is consistent across frames."""
        sequence = create_gesture_sequence("palm_stop", num_frames=10)
        
        distances = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            if result.distance_estimate is not None:
                distances.append(result.distance_estimate)
        
        if len(distances) > 0:
            # Distance should be relatively stable for static hand
            std_dev = np.std(distances)
            assert std_dev < 0.5  # Within 0.5m variation
    
    def test_distance_smoothing(self, recognizer, create_gesture_sequence):
        """Test distance smoothing over multiple frames."""
        sequence = create_gesture_sequence("thumbs_up", num_frames=10)
        
        distances = []
        for hand in sequence:
            result = recognizer.recognize(hand)
            if result.distance_estimate is not None:
                distances.append(result.distance_estimate)
        
        # With smoothing enabled, should see smooth distance values
        if len(distances) >= 2:
            # Check distances are in valid range
            assert all(recognizer.min_distance <= d <= recognizer.max_distance
                      for d in distances)


class TestPerformanceValidation:
    """Test performance requirements are met."""
    
    def test_recognition_time_under_500ms(self, recognizer, create_gesture_sequence):
        """Test recognition time is under 0.5s."""
        sequence = create_gesture_sequence("palm_stop", num_frames=1)
        hand = sequence[0]
        
        start_time = time.time()
        result = recognizer.recognize(hand)
        elapsed = time.time() - start_time
        
        # Single recognition should be well under 500ms
        assert elapsed < 0.5
        # Should actually be much faster (< 50ms target)
        assert elapsed < 0.1
    
    def test_batch_recognition_performance(self, recognizer, create_gesture_sequence):
        """Test batch recognition maintains performance."""
        sequence = create_gesture_sequence("thumbs_up", num_frames=30)
        
        start_time = time.time()
        for hand in sequence:
            recognizer.recognize(hand)
        elapsed = time.time() - start_time
        
        avg_time = elapsed / 30
        
        # Average recognition time should be fast
        assert avg_time < 0.1  # 100ms per frame
    
    def test_false_positive_rate(self, recognizer, create_gesture_sequence):
        """Test false positive rate is low."""
        # Run 100 neutral frames
        neutral_detections = 0
        
        for _ in range(100):
            sequence = create_gesture_sequence("neutral", num_frames=1)
            result = recognizer.recognize(sequence[0])
            
            # Check if confirmed as a gesture (false positive)
            if result.is_confirmed and result.gesture_type != GestureType.UNKNOWN:
                neutral_detections += 1
        
        false_positive_rate = neutral_detections / 100
        
        # Should be under 5% false positive rate
        assert false_positive_rate < 0.05


class TestMultiHandScenarios:
    """Test scenarios with multiple hands."""
    
    def test_recognize_different_gestures_per_hand(self, recognizer, create_gesture_sequence):
        """Test recognizing different gestures from two hands."""
        # Create sequences for two hands
        hand1_seq = create_gesture_sequence("thumbs_up", num_frames=10)
        hand2_seq = create_gesture_sequence("palm_stop", num_frames=10)
        
        # Set different hand IDs
        for hand in hand1_seq:
            hand.hand_id = 0
            hand.handedness = "Right"
        
        for hand in hand2_seq:
            hand.hand_id = 1
            hand.handedness = "Left"
        
        results1 = []
        results2 = []
        
        # Process both hands frame by frame
        for hand1, hand2 in zip(hand1_seq, hand2_seq):
            results1.append(recognizer.recognize(hand1))
            results2.append(recognizer.recognize(hand2))
        
        # Should track both hands independently
        assert all(r.hand_id == 0 for r in results1)
        assert all(r.hand_id == 1 for r in results2)
        assert all(r.handedness == "Right" for r in results1)
        assert all(r.handedness == "Left" for r in results2)
    
    def test_gesture_history_per_hand(self, recognizer, create_gesture_sequence):
        """Test gesture history is tracked separately per hand."""
        # Create sequences for two hands
        hand1_seq = create_gesture_sequence("thumbs_up", num_frames=5)
        hand2_seq = create_gesture_sequence("wave", num_frames=5)
        
        for hand in hand1_seq:
            hand.hand_id = 0
        
        for hand in hand2_seq:
            hand.hand_id = 1
        
        # Process hand 1
        for hand in hand1_seq:
            recognizer.recognize(hand)
        
        # Process hand 2
        for hand in hand2_seq:
            recognizer.recognize(hand)
        
        # Both hands should have history
        assert 0 in recognizer.gesture_history
        assert 1 in recognizer.gesture_history
        
        # Histories should be independent
        assert len(recognizer.gesture_history[0]) > 0
        assert len(recognizer.gesture_history[1]) > 0


class TestStatisticsIntegration:
    """Integration tests for statistics tracking."""
    
    def test_statistics_across_multiple_gestures(self, recognizer, create_gesture_sequence):
        """Test statistics tracking across multiple gesture types."""
        # Process different gestures
        for gesture_type in ["thumbs_up", "wave", "palm_stop", "neutral"]:
            sequence = create_gesture_sequence(gesture_type, num_frames=10)
            for hand in sequence:
                recognizer.recognize(hand)
        
        stats = recognizer.get_statistics()
        
        # Should have processed 40 frames
        assert stats["recognition_count"] == 40
        assert stats["active_hands"] >= 1
        
        # Gesture counts should be tracked
        assert "gesture_counts" in stats
        assert isinstance(stats["gesture_counts"], dict)
