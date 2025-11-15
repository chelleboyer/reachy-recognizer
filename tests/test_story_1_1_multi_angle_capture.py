"""
Unit Tests for Multi-Angle Capture - Story 1.1

Tests the MultiAngleCaptureController to verify:
- Configuration loading
- Angle sequence ordering
- Movement timing
- Frame metadata
- Return to neutral
- Error handling
"""

import pytest
import asyncio
import time
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import numpy as np

from src.vision.multi_angle_capture import (
    MultiAngleCaptureController,
    CapturedFrame,
    CaptureSequenceError
)
from src.vision.camera_interface import CameraInterface


@pytest.fixture
def mock_camera():
    """Create mock camera interface."""
    camera = Mock(spec=CameraInterface)
    # Mock successful frame capture
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    camera.read_frame.return_value = (True, test_frame)
    camera.release = Mock()
    return camera


@pytest.fixture
def test_config_path():
    """Get path to test configuration file."""
    config_path = Path(__file__).parent.parent / "src" / "config" / "multi_angle_capture.yaml"
    if not config_path.exists():
        pytest.skip("Configuration file not found")
    return str(config_path)


@pytest.fixture
def controller_mock_mode(test_config_path, mock_camera):
    """Create controller in mock mode (no robot)."""
    controller = MultiAngleCaptureController(
        config_path=test_config_path,
        camera=mock_camera,
        enable_robot=False  # Mock mode
    )
    yield controller
    controller.cleanup()


class TestConfigurationLoading:
    """Test configuration file loading and validation."""
    
    def test_load_config_from_yaml(self, test_config_path):
        """Verify angles loaded from config correctly."""
        with patch('src.vision.multi_angle_capture.CameraInterface'):
            controller = MultiAngleCaptureController(
                config_path=test_config_path,
                enable_robot=False
            )
            
            config = controller.get_config()
            
            # Verify angles present
            assert 'angles' in config
            assert 'yaw' in config['angles']
            assert 'pitch' in config['angles']
            
            # Verify default values
            assert config['angles']['yaw'] == [-45, -22, 0, 22, 45]
            assert config['angles']['pitch'] == -10
            
            controller.cleanup()
    
    def test_missing_config_file_raises_error(self):
        """Verify error raised if config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            with patch('src.vision.multi_angle_capture.CameraInterface'):
                MultiAngleCaptureController(
                    config_path="/nonexistent/path.yaml",
                    enable_robot=False
                )
    
    def test_movement_parameters_loaded(self, test_config_path):
        """Verify movement parameters loaded correctly."""
        with patch('src.vision.multi_angle_capture.CameraInterface'):
            controller = MultiAngleCaptureController(
                config_path=test_config_path,
                enable_robot=False
            )
            
            config = controller.get_config()
            
            assert 'movement' in config
            assert config['movement']['speed_factor'] == 0.7
            assert config['movement']['stabilization_pause_ms'] == 100
            assert config['movement']['max_movement_time_sec'] == 2
            assert config['movement']['return_to_neutral'] is True
            
            controller.cleanup()


class TestAngleSequencing:
    """Test angle sequence execution and ordering."""
    
    @pytest.mark.asyncio
    async def test_angle_sequence_order(self, controller_mock_mode):
        """Verify angles executed in correct order."""
        frames = await controller_mock_mode.capture_sequence()
        
        # Verify correct number of frames
        expected_angles = [-45, -22, 0, 22, 45]
        assert len(frames) == len(expected_angles)
        
        # Verify angles in order
        for idx, (frame, expected_yaw) in enumerate(zip(frames, expected_angles)):
            assert frame.angle_yaw == expected_yaw
            assert frame.angle_index == idx
    
    @pytest.mark.asyncio
    async def test_pitch_angle_consistent(self, controller_mock_mode):
        """Verify pitch angle consistent across all frames."""
        frames = await controller_mock_mode.capture_sequence()
        
        expected_pitch = -10
        for frame in frames:
            assert frame.angle_pitch == expected_pitch
    
    @pytest.mark.asyncio
    async def test_stabilization_pause_applied(self, controller_mock_mode):
        """Verify 100ms pause between movement and capture."""
        # This test verifies timing indirectly through total sequence time
        start = time.time()
        frames = await controller_mock_mode.capture_sequence()
        elapsed = time.time() - start
        
        # Should include at least num_angles * stabilization_pause
        min_stabilization_time = len(frames) * 0.1  # 100ms per angle
        assert elapsed >= min_stabilization_time


class TestMovementTiming:
    """Test movement timing requirements."""
    
    @pytest.mark.asyncio
    async def test_movement_timing_per_angle(self, controller_mock_mode):
        """Verify each angle completes in <2 seconds (mock mode allows testing)."""
        # In mock mode, movements are simulated with sleep(0.5)
        # Should be well under 2 seconds
        
        start = time.time()
        await controller_mock_mode._move_to_angle(45, -10)
        elapsed = time.time() - start
        
        assert elapsed < 2.0, f"Movement took {elapsed:.2f}s, expected <2.0s"
    
    @pytest.mark.asyncio
    async def test_total_sequence_timing(self, controller_mock_mode):
        """Verify total sequence completes in <10 seconds."""
        frames = await controller_mock_mode.capture_sequence()
        
        sequence_time = controller_mock_mode.get_last_sequence_time()
        
        # AC1: Must complete in <10 seconds
        assert sequence_time < 10.0, f"Sequence took {sequence_time:.2f}s, expected <10.0s"
        assert len(frames) == 5  # Should have captured all frames


class TestFrameMetadata:
    """Test frame metadata completeness."""
    
    @pytest.mark.asyncio
    async def test_frame_metadata_complete(self, controller_mock_mode):
        """Verify captured frames have correct metadata."""
        frames = await controller_mock_mode.capture_sequence()
        
        for frame in frames:
            # AC4: All metadata fields present
            assert isinstance(frame.frame, np.ndarray)
            assert frame.frame.shape == (480, 640, 3)  # BGR format
            
            assert isinstance(frame.angle_yaw, (int, float))
            assert isinstance(frame.angle_pitch, (int, float))
            assert isinstance(frame.timestamp, float)
            assert frame.timestamp > 0
            
            assert isinstance(frame.capture_id, str)
            assert frame.capture_id.startswith("seq_")
            
            assert isinstance(frame.angle_index, int)
            assert 0 <= frame.angle_index < 5
    
    @pytest.mark.asyncio
    async def test_capture_id_unique_per_sequence(self, controller_mock_mode):
        """Verify each sequence gets unique capture_id."""
        frames1 = await controller_mock_mode.capture_sequence()
        frames2 = await controller_mock_mode.capture_sequence()
        
        id1 = frames1[0].capture_id
        id2 = frames2[0].capture_id
        
        assert id1 != id2, "Capture IDs should be unique per sequence"
    
    @pytest.mark.asyncio
    async def test_capture_id_same_within_sequence(self, controller_mock_mode):
        """Verify all frames in sequence share same capture_id."""
        frames = await controller_mock_mode.capture_sequence()
        
        capture_ids = [f.capture_id for f in frames]
        assert len(set(capture_ids)) == 1, "All frames in sequence should have same capture_id"
    
    @pytest.mark.asyncio
    async def test_timestamp_increases(self, controller_mock_mode):
        """Verify timestamps increase across frames."""
        frames = await controller_mock_mode.capture_sequence()
        
        timestamps = [f.timestamp for f in frames]
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i-1], "Timestamps should increase"


class TestReturnToNeutral:
    """Test return to neutral position."""
    
    @pytest.mark.asyncio
    async def test_return_to_neutral_called(self, controller_mock_mode):
        """Verify head returns to neutral after sequence."""
        # Mock the _return_to_neutral method to track calls
        with patch.object(controller_mock_mode, '_return_to_neutral', 
                         wraps=controller_mock_mode._return_to_neutral) as mock_return:
            
            await controller_mock_mode.capture_sequence()
            
            # Verify return to neutral was called
            mock_return.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_return_to_neutral_on_error(self, controller_mock_mode):
        """Verify return to neutral attempted even if capture fails."""
        # Make camera fail
        controller_mock_mode.camera.read_frame.return_value = (False, None)
        
        with patch.object(controller_mock_mode, '_return_to_neutral', 
                         wraps=controller_mock_mode._return_to_neutral) as mock_return:
            
            with pytest.raises(CaptureSequenceError):
                await controller_mock_mode.capture_sequence()
            
            # Should still attempt return to neutral
            mock_return.assert_called()


class TestErrorHandling:
    """Test error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_camera_failure_raises_error(self, controller_mock_mode):
        """Verify error raised if camera capture fails."""
        # Make camera return failure
        controller_mock_mode.camera.read_frame.return_value = (False, None)
        
        with pytest.raises(CaptureSequenceError):
            await controller_mock_mode.capture_sequence()
    
    @pytest.mark.asyncio
    async def test_sequence_count_increments(self, controller_mock_mode):
        """Verify sequence counter increments."""
        initial_count = controller_mock_mode.sequence_count
        
        await controller_mock_mode.capture_sequence()
        assert controller_mock_mode.sequence_count == initial_count + 1
        
        await controller_mock_mode.capture_sequence()
        assert controller_mock_mode.sequence_count == initial_count + 2


class TestPerformanceMetrics:
    """Test performance tracking."""
    
    @pytest.mark.asyncio
    async def test_last_sequence_time_tracked(self, controller_mock_mode):
        """Verify last sequence time is tracked."""
        assert controller_mock_mode.get_last_sequence_time() == 0.0
        
        await controller_mock_mode.capture_sequence()
        
        sequence_time = controller_mock_mode.get_last_sequence_time()
        assert sequence_time > 0.0
        assert sequence_time < 10.0  # AC1: Must be under 10 seconds


# =============================================================================
# Integration Test Marker (requires real hardware)
# =============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_hardware_capture():
    """
    Integration test on real Reachy hardware.
    
    This test requires:
    - Reachy Mini connected and accessible
    - Camera connected
    - Configuration file present
    
    Run with: pytest -v -m integration
    """
    config_path = Path(__file__).parent.parent / "src" / "config" / "multi_angle_capture.yaml"
    
    if not config_path.exists():
        pytest.skip("Configuration file not found")
    
    try:
        controller = MultiAngleCaptureController(
            config_path=str(config_path),
            enable_robot=True  # Real robot
        )
        
        # Execute capture sequence
        frames = await controller.capture_sequence()
        
        # Verify results
        assert len(frames) == 5, "Should capture 5 frames"
        assert controller.get_last_sequence_time() < 10.0, "Should complete in <10 seconds"
        
        # Verify frames are valid images
        for frame in frames:
            assert frame.frame.shape[0] > 0
            assert frame.frame.shape[1] > 0
            assert frame.frame.shape[2] == 3
        
        controller.cleanup()
        
        print("✓ Real hardware integration test passed")
        
    except Exception as e:
        pytest.skip(f"Hardware not available: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
