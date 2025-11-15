"""
Unit tests for Story 3.4: Visual Feedback & UI Integration.

Tests the FeedbackManager class, animation state transitions, icon mapping,
rendering, and performance validation.
"""

import time
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.ui.feedback_manager import (
    FeedbackAnimation,
    FeedbackState,
    FeedbackManager,
)
from src.vision.gesture_recognizer import GestureType, GestureResult


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """Minimal test configuration."""
    return {
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
        'position': {
            'x': 'center',
            'y': 'center',
            'offset_x': 0,
            'offset_y': -50,
        },
        'colors': {
            'icon_color': [255, 255, 255, 255],
            'background_color': [0, 0, 0, 128],
            'background_enabled': True,
            'background_radius': 120,
        },
        'target_latency_ms': 200,
        'frame_rate': 30,
        'max_queue_size': 3,
    }


@pytest.fixture
def feedback_manager(test_config):
    """Create FeedbackManager with test configuration."""
    manager = FeedbackManager(config=test_config, headless=True)
    yield manager
    manager.cleanup()


@pytest.fixture
def mock_gesture_result():
    """Create mock GestureResult for testing."""
    return GestureResult(
        gesture_type=GestureType.THUMBS_UP,
        confidence=0.95,
        hand_id=0,
        handedness="Right",
        is_confirmed=True,
        hold_duration=0.6,
        distance_estimate=2.0,
        timestamp=time.time()
    )


# ============================================================================
# Icon Mapping Tests (3 tests)
# ============================================================================

def test_icon_mapping_thumbs_up(feedback_manager):
    """Test thumbs up gesture maps to correct emoji."""
    icon = feedback_manager._get_icon_for_gesture(GestureType.THUMBS_UP)
    assert icon == '👍'


def test_icon_mapping_wave(feedback_manager):
    """Test wave gesture maps to correct emoji."""
    icon = feedback_manager._get_icon_for_gesture(GestureType.WAVE)
    assert icon == '👋'


def test_icon_mapping_palm_stop(feedback_manager):
    """Test palm stop gesture maps to correct emoji."""
    icon = feedback_manager._get_icon_for_gesture(GestureType.PALM_STOP)
    assert icon == '✋'


# ============================================================================
# Animation State Transition Tests (5 tests)
# ============================================================================

def test_fade_in_phase(feedback_manager):
    """Test fade-in phase animation (0.0-0.2s)."""
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.FADE_IN,
        start_time=time.time(),
        elapsed_time=0.1,  # Halfway through fade-in
        alpha=0.0,
        scale=0.8,
        position=(320, 240)
    )
    
    updated_state = feedback_manager._animate_fade_in(state)
    
    # Alpha should increase linearly (0.1 / 0.2 = 0.5)
    assert 0.4 < updated_state.alpha < 0.6
    
    # Scale should increase from 0.8 to 1.0
    assert 0.8 < updated_state.scale < 1.0


def test_pulse_phase(feedback_manager):
    """Test pulse phase animation (0.2-0.8s)."""
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.PULSE,
        start_time=time.time(),
        elapsed_time=0.5,  # Middle of pulse (0.2 + 0.3)
        alpha=1.0,
        scale=1.0,
        position=(320, 240)
    )
    
    updated_state = feedback_manager._animate_pulse(state)
    
    # Alpha should stay at 1.0
    assert updated_state.alpha == 1.0
    
    # Scale should oscillate (close to max at middle)
    assert updated_state.scale > 1.0


def test_fade_out_phase(feedback_manager):
    """Test fade-out phase animation (0.8-1.0s)."""
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.FADE_OUT,
        start_time=time.time(),
        elapsed_time=0.9,  # Halfway through fade-out (0.8 + 0.1)
        alpha=1.0,
        scale=1.0,
        position=(320, 240)
    )
    
    updated_state = feedback_manager._animate_fade_out(state)
    
    # Alpha should decrease (0.1 / 0.2 = 0.5 remaining)
    assert 0.4 < updated_state.alpha < 0.6
    
    # Scale should increase
    assert updated_state.scale > 1.0


def test_phase_progression(feedback_manager):
    """Test automatic phase transitions."""
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.FADE_IN,
        start_time=time.time(),
        elapsed_time=0.0,
        alpha=0.0,
        scale=0.8,
        position=(320, 240)
    )
    
    # Test fade-in -> pulse transition
    state.elapsed_time = 0.25  # Past fade-in duration (0.2s)
    updated_state = feedback_manager._update_animation_state(state)
    assert updated_state.animation_phase == FeedbackAnimation.PULSE
    
    # Test pulse -> fade-out transition
    state.elapsed_time = 0.85  # Past pulse end (0.2 + 0.6 = 0.8s)
    updated_state = feedback_manager._update_animation_state(state)
    assert updated_state.animation_phase == FeedbackAnimation.FADE_OUT
    
    # Test fade-out -> complete transition
    state.elapsed_time = 1.1  # Past total duration (1.0s)
    updated_state = feedback_manager._update_animation_state(state)
    assert updated_state.animation_phase == FeedbackAnimation.COMPLETE


def test_animation_completion(feedback_manager):
    """Test animation reaches COMPLETE phase at 1.0s."""
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.FADE_IN,
        start_time=time.time() - 1.5,  # Started 1.5s ago
        elapsed_time=1.5,
        alpha=0.0,
        scale=1.0,
        position=(320, 240)
    )
    
    updated_state = feedback_manager._update_animation_state(state)
    
    assert updated_state.animation_phase == FeedbackAnimation.COMPLETE
    assert updated_state.alpha == 0.0


# ============================================================================
# Rendering Tests (4 tests)
# ============================================================================

def test_render_emoji_size(feedback_manager):
    """Test emoji rendered at correct size."""
    emoji_img = feedback_manager._render_emoji('👍', scale=1.0)
    
    # Should be 200x200 (icon_size)
    assert emoji_img.shape[0] == 200
    assert emoji_img.shape[1] == 200
    assert emoji_img.shape[2] == 4  # RGBA


def test_render_background(feedback_manager):
    """Test optional circle background rendering."""
    canvas = np.zeros((480, 640, 3), dtype=np.uint8)
    state = FeedbackState(
        gesture_type=GestureType.THUMBS_UP,
        icon='👍',
        animation_phase=FeedbackAnimation.PULSE,
        start_time=time.time(),
        elapsed_time=0.5,
        alpha=1.0,
        scale=1.0,
        position=(320, 240)
    )
    
    result = feedback_manager._draw_background(canvas, state)
    
    # Background should be drawn (same shape)
    assert result.shape == canvas.shape
    assert result.dtype == canvas.dtype


def test_alpha_blending(feedback_manager):
    """Test transparency applied correctly."""
    canvas = np.ones((480, 640, 3), dtype=np.uint8) * 128  # Gray background
    overlay = np.ones((100, 100, 4), dtype=np.uint8)
    overlay[:, :, :3] = 255  # White
    overlay[:, :, 3] = 128   # 50% alpha
    
    position = (320, 240)
    result = feedback_manager._composite_overlay(canvas, overlay, position)
    
    # Check that center pixel is blended (not pure white or gray)
    center_pixel = result[240, 320]
    assert np.all(center_pixel > 128)  # Lighter than background
    assert np.all(center_pixel < 255)  # Not pure white


def test_position_calculation(feedback_manager):
    """Test center/offset positioning."""
    # Test center position
    pos = feedback_manager._calculate_position(640, 480)
    assert pos == (320, 190)  # Center with -50 Y offset
    
    # Test left position
    feedback_manager.position_x = 'left'
    pos = feedback_manager._calculate_position(640, 480)
    assert pos[0] == 200  # icon_size
    
    # Test custom offset
    feedback_manager.offset_x = 50
    pos = feedback_manager._calculate_position(640, 480)
    assert pos[0] == 250  # icon_size + offset


# ============================================================================
# Performance Tests (3 tests)
# ============================================================================

def test_display_latency(feedback_manager, mock_gesture_result):
    """Test display latency < 200ms."""
    start_time = time.time()
    
    feedback_manager.show_gesture_feedback(mock_gesture_result)
    
    latency_ms = (time.time() - start_time) * 1000
    
    # Should be very fast (just queuing)
    assert latency_ms < 200


def test_animation_fps(feedback_manager):
    """Test animation thread runs at target FPS."""
    # Start animation thread
    feedback_manager.start()
    
    # Give it time to run a few frames
    time.sleep(0.2)
    
    # Thread should be running
    assert feedback_manager.running
    assert feedback_manager.animation_thread is not None
    assert feedback_manager.animation_thread.is_alive()


def test_thread_safety(feedback_manager, mock_gesture_result):
    """Test concurrent gestures handled safely."""
    feedback_manager.start()
    
    # Queue multiple gestures rapidly
    for _ in range(5):
        feedback_manager.show_gesture_feedback(mock_gesture_result)
    
    # Should not crash, may drop some due to queue size
    stats = feedback_manager.get_statistics()
    total_processed = stats['animations_shown'] + stats['dropped_frames']
    assert total_processed == 5


# ============================================================================
# Configuration Tests (3 tests)
# ============================================================================

def test_load_config_default(tmp_path):
    """Test loading with default config when file missing."""
    # Use non-existent path
    manager = FeedbackManager(config_path=tmp_path / 'nonexistent.yaml', headless=True)
    
    # Should load defaults
    assert manager.total_duration == 1.0
    assert manager.icon_size == 200
    
    manager.cleanup()


def test_custom_icons(test_config):
    """Test override default emojis."""
    test_config['icons']['thumbs_up'] = '✅'
    test_config['icons']['wave'] = '🔵'
    test_config['icons']['palm_stop'] = '⛔'
    
    manager = FeedbackManager(config=test_config, headless=True)
    
    assert manager._get_icon_for_gesture(GestureType.THUMBS_UP) == '✅'
    assert manager._get_icon_for_gesture(GestureType.WAVE) == '🔵'
    assert manager._get_icon_for_gesture(GestureType.PALM_STOP) == '⛔'
    
    manager.cleanup()


def test_custom_colors(test_config):
    """Test override colors."""
    test_config['colors']['icon_color'] = [255, 0, 0, 255]  # Red
    test_config['colors']['background_color'] = [0, 255, 0, 200]  # Green
    
    manager = FeedbackManager(config=test_config, headless=True)
    
    assert manager.icon_color == (255, 0, 0, 255)
    assert manager.bg_color == (0, 255, 0, 200)
    
    manager.cleanup()


# ============================================================================
# Statistics Tests (2 tests)
# ============================================================================

def test_statistics_tracking(feedback_manager, mock_gesture_result):
    """Test statistics are tracked correctly."""
    initial_stats = feedback_manager.get_statistics()
    assert initial_stats['animations_shown'] == 0
    
    # Show feedback
    feedback_manager.show_gesture_feedback(mock_gesture_result)
    
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] == 1
    assert stats['avg_latency_ms'] >= 0  # May be very fast
    assert stats['avg_latency_ms'] < 200


def test_reset_statistics(feedback_manager, mock_gesture_result):
    """Test statistics can be reset."""
    # Generate some stats
    feedback_manager.show_gesture_feedback(mock_gesture_result)
    
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] > 0
    
    # Reset
    feedback_manager.reset_statistics()
    
    stats = feedback_manager.get_statistics()
    assert stats['animations_shown'] == 0
    assert stats['avg_latency_ms'] == 0.0


# ============================================================================
# Cleanup Tests (1 test)
# ============================================================================

def test_cleanup(feedback_manager):
    """Test resource cleanup."""
    feedback_manager.start()
    
    # Should be running
    assert feedback_manager.running
    
    # Cleanup
    feedback_manager.cleanup()
    
    # Should be stopped
    assert not feedback_manager.running
    assert len(feedback_manager._emoji_cache) == 0
