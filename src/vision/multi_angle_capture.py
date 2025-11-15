"""
Multi-Angle Capture Module - Story 1.1

Orchestrates head movement and frame capture across multiple angles to eliminate
glare and occlusion issues on reflective surfaces (e.g., cigarette packaging).

This module coordinates:
- Sequential head movement to predefined angles
- Camera stabilization between movements
- Frame capture with metadata tracking
- Return to neutral position

Key Features:
- Configurable angle sequences via YAML
- <10 second total capture time (AC1)
- <2 seconds per angle movement (AC2)
- 100ms stabilization pause (AC3)
- Full metadata per frame (AC4)
"""

import time
import logging
import asyncio
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path

import numpy as np
import yaml

# Import Reachy SDK
try:
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("Warning: reachy_mini not available - using mock mode")

from .camera_interface import CameraInterface

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CapturedFrame:
    """
    Frame captured at specific angle with metadata.
    
    Attributes:
        frame: Image data (BGR numpy array)
        angle_yaw: Yaw angle in degrees
        angle_pitch: Pitch angle in degrees
        timestamp: Unix timestamp of capture
        capture_id: Unique sequence identifier
        angle_index: Position in sequence (0-based)
    """
    frame: np.ndarray
    angle_yaw: float
    angle_pitch: float
    timestamp: float
    capture_id: str
    angle_index: int
    
    def __repr__(self):
        return (f"CapturedFrame(angle={self.angle_yaw}°, "
                f"shape={self.frame.shape}, idx={self.angle_index})")


class CaptureSequenceError(Exception):
    """Raised when capture sequence fails."""
    pass


class MultiAngleCaptureController:
    """
    Controls multi-angle capture sequences for improved product detection.
    
    Coordinates Reachy head movements with camera capture to obtain multiple
    viewpoints of a target, eliminating glare and improving OCR success rates.
    
    Usage:
        controller = MultiAngleCaptureController(config_path="config.yaml")
        frames = await controller.capture_sequence()
        # Process frames with quality assessment (Story 1.2)
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        camera: Optional[CameraInterface] = None,
        enable_robot: bool = True
    ):
        """
        Initialize multi-angle capture controller.
        
        Args:
            config_path: Path to YAML configuration file
            camera: Camera interface (or None to create default)
            enable_robot: If True, connect to real robot. If False, mock mode.
            
        Raises:
            FileNotFoundError: If config file not found
            RuntimeError: If camera cannot be opened or robot connection fails
        """
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize camera
        if camera is None:
            cam_cfg = self.config['camera']
            self.camera = CameraInterface(
                camera_id=cam_cfg['device_id'],
                width=cam_cfg['resolution'][0],
                height=cam_cfg['resolution'][1],
                fps=cam_cfg.get('fps', 30)
            )
            self._owns_camera = True
        else:
            self.camera = camera
            self._owns_camera = False
        
        # Initialize robot connection
        self.enable_robot = enable_robot and REACHY_AVAILABLE
        self.reachy: Optional[ReachyMini] = None
        
        if self.enable_robot:
            try:
                logger.info("Connecting to Reachy Mini...")
                self.reachy = ReachyMini(media_backend="no_media", timeout=30)
                logger.info("✓ Reachy Mini connected")
            except Exception as e:
                logger.error(f"Failed to connect to Reachy: {e}")
                raise RuntimeError(f"Robot connection failed: {e}")
        else:
            logger.info("Running in mock mode (no robot control)")
        
        # Capture sequence tracking
        self.sequence_count = 0
        self.last_capture_time = 0.0
        
        logger.info("MultiAngleCaptureController initialized")
        logger.info(f"  Angles: {self.config['angles']['yaw']}")
        logger.info(f"  Pitch: {self.config['angles']['pitch']}°")
        logger.info(f"  Robot enabled: {self.enable_robot}")
    
    def _load_config(self, config_path: Optional[str]) -> dict:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to config file, or None for default
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file not found
        """
        if config_path is None:
            # Use default path
            default_path = Path(__file__).parent.parent / "config" / "multi_angle_capture.yaml"
            config_path = str(default_path)
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded config from {config_path}")
        return config.get('multi_angle_capture', config)
    
    async def capture_sequence(self, target_roi: Optional[Tuple[int, int, int, int]] = None) -> List[CapturedFrame]:
        """
        Execute multi-angle capture sequence.
        
        Moves robot head to each configured angle, stabilizes, captures frame,
        and returns to neutral position.
        
        Args:
            target_roi: Optional (x, y, width, height) region of interest to track
            
        Returns:
            List of CapturedFrame objects with metadata
            
        Raises:
            CaptureSequenceError: If movement or capture fails
            
        Acceptance Criteria:
        - AC1: Total sequence completes in <10 seconds
        - AC2: Each angle movement completes in <2 seconds
        - AC3: 100ms stabilization pause before capture
        - AC4: All frames have complete metadata
        - AC5: Returns to neutral (0°, 0°) after sequence
        """
        start_time = time.time()
        capture_id = f"seq_{self.sequence_count:04d}_{int(start_time)}"
        self.sequence_count += 1
        
        logger.info(f"Starting capture sequence {capture_id}")
        
        # Get angle configuration
        yaw_angles = self.config['angles']['yaw']
        pitch_angle = self.config['angles']['pitch']
        
        captured_frames: List[CapturedFrame] = []
        
        try:
            # Capture at each angle (AC2: <2 sec per angle)
            for idx, yaw in enumerate(yaw_angles):
                angle_start = time.time()
                
                # Move to angle (AC2)
                await self._move_to_angle(yaw, pitch_angle)
                
                move_time = time.time() - angle_start
                if move_time > 2.0:
                    logger.warning(f"⚠️  Movement to angle {yaw}° took {move_time:.2f}s (>2.0s)")
                
                # Stabilization pause (AC3: 100ms)
                stabilization_ms = self.config['movement']['stabilization_pause_ms']
                await asyncio.sleep(stabilization_ms / 1000.0)
                
                # Capture frame (AC4)
                frame = await self._capture_frame(yaw, pitch_angle, capture_id, idx)
                captured_frames.append(frame)
                
                logger.info(f"  Captured frame {idx+1}/{len(yaw_angles)} at {yaw}° "
                          f"(move: {move_time:.2f}s)")
            
            # Return to neutral (AC5)
            await self._return_to_neutral()
            
            # Check total time (AC1: <10 seconds)
            total_time = time.time() - start_time
            self.last_capture_time = total_time
            
            if total_time > 10.0:
                logger.warning(f"⚠️  Total sequence time {total_time:.2f}s exceeds 10.0s target!")
            else:
                logger.info(f"✓ Sequence complete in {total_time:.2f}s")
            
            return captured_frames
            
        except Exception as e:
            logger.error(f"Capture sequence failed: {e}")
            # Attempt to return to neutral even on failure
            try:
                await self._return_to_neutral()
            except:
                pass
            raise CaptureSequenceError(f"Capture sequence failed: {e}")
    
    async def _move_to_angle(self, yaw: float, pitch: float) -> None:
        """
        Move robot head to specified angle.
        
        Args:
            yaw: Target yaw angle in degrees
            pitch: Target pitch angle in degrees
            
        Raises:
            RuntimeError: If movement fails or times out
        """
        if not self.enable_robot or self.reachy is None:
            # Mock mode: just sleep to simulate movement
            await asyncio.sleep(0.5)
            return
        
        try:
            # Create target pose
            pose = create_head_pose(
                x=0.0,
                y=0.0,
                z=0.0,
                roll=0.0,
                pitch=pitch,
                yaw=yaw,
                degrees=True,
                mm=False
            )
            
            # Get speed factor from config
            speed_factor = self.config['movement']['speed_factor']
            movement_duration = speed_factor * 2.0
            
            # Move head using goto_target (blocking call in SDK)
            self.reachy.goto_target(head=pose, duration=movement_duration)
            
            # Note: goto_target is blocking, but add small buffer for safety
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Movement to yaw={yaw}°, pitch={pitch}° failed: {e}")
            raise RuntimeError(f"Head movement failed: {e}")
    
    async def _capture_frame(
        self,
        yaw: float,
        pitch: float,
        capture_id: str,
        angle_index: int
    ) -> CapturedFrame:
        """
        Capture frame with metadata.
        
        Args:
            yaw: Current yaw angle in degrees
            pitch: Current pitch angle in degrees
            capture_id: Unique sequence identifier
            angle_index: Position in sequence (0-based)
            
        Returns:
            CapturedFrame with complete metadata
            
        Raises:
            RuntimeError: If frame capture fails
        """
        # Clear frame buffer if configured (AC3)
        if self.config['camera'].get('frame_buffer_clear', True):
            # Read and discard a frame to clear buffer
            self.camera.read_frame()
            await asyncio.sleep(0.01)
        
        # Capture frame
        ret, frame = self.camera.read_frame()
        
        if not ret or frame is None:
            raise RuntimeError("Failed to capture frame from camera")
        
        # Create CapturedFrame with metadata (AC4)
        captured = CapturedFrame(
            frame=frame.copy(),
            angle_yaw=yaw,
            angle_pitch=pitch,
            timestamp=time.time(),
            capture_id=capture_id,
            angle_index=angle_index
        )
        
        return captured
    
    async def _return_to_neutral(self) -> None:
        """
        Return robot head to neutral position (0°, 0°).
        
        Ensures head is in standard position after capture sequence.
        """
        if not self.config['movement']['return_to_neutral']:
            logger.debug("Return to neutral disabled in config")
            return
        
        if not self.enable_robot or self.reachy is None:
            # Mock mode
            await asyncio.sleep(0.3)
            return
        
        try:
            # Create neutral pose
            neutral_pose = create_head_pose(
                x=0.0, y=0.0, z=0.0,
                roll=0.0, pitch=0.0, yaw=0.0,
                degrees=True, mm=False
            )
            
            # Move to neutral using goto_target
            self.reachy.goto_target(head=neutral_pose, duration=0.5)
            await asyncio.sleep(0.1)
            
            logger.debug("Returned to neutral position")
            
        except Exception as e:
            logger.error(f"Failed to return to neutral: {e}")
            # Don't raise - this is cleanup, we want to continue
    
    def get_last_sequence_time(self) -> float:
        """
        Get execution time of last capture sequence.
        
        Returns:
            Time in seconds, or 0.0 if no sequence completed yet
        """
        return self.last_capture_time
    
    def get_config(self) -> dict:
        """Get current configuration dictionary."""
        return self.config.copy()
    
    def cleanup(self):
        """Release resources."""
        if hasattr(self, '_owns_camera') and self._owns_camera:
            self.camera.release()
        
        if hasattr(self, 'reachy') and self.reachy is not None:
            try:
                self.reachy.client.disconnect()
                logger.info("Robot connection closed")
            except:
                pass
    
    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()


# =============================================================================
# Demo / Testing
# =============================================================================

async def main():
    """Demo multi-angle capture."""
    print("=" * 70)
    print("Multi-Angle Capture Demo - Story 1.1")
    print("=" * 70)
    print()
    
    # Check if config exists
    config_path = Path(__file__).parent.parent / "config" / "multi_angle_capture.yaml"
    if not config_path.exists():
        print(f"✗ Config file not found: {config_path}")
        print("  Please create configuration file first")
        return
    
    try:
        # Initialize controller
        print("Initializing controller...")
        controller = MultiAngleCaptureController(
            config_path=str(config_path),
            enable_robot=True  # Set to False for mock mode
        )
        print("✓ Controller initialized")
        print()
        
        # Run capture sequence
        print("Starting capture sequence...")
        print("-" * 70)
        
        frames = await controller.capture_sequence()
        
        print("-" * 70)
        print(f"✓ Captured {len(frames)} frames")
        print(f"  Total time: {controller.get_last_sequence_time():.2f}s")
        print()
        
        # Display frame info
        print("Captured frames:")
        for frame in frames:
            print(f"  {frame}")
        print()
        
        # Performance check
        sequence_time = controller.get_last_sequence_time()
        if sequence_time < 10.0:
            print(f"✓ Performance target met: {sequence_time:.2f}s < 10.0s")
        else:
            print(f"✗ Performance target missed: {sequence_time:.2f}s > 10.0s")
        
        # Cleanup
        controller.cleanup()
        print()
        print("✓ Demo complete!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
