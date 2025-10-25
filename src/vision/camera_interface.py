"""
Camera Interface Module - Story 1.3

Simple wrapper around OpenCV VideoCapture for consistent camera access.
Provides frame capture with error handling and resource management.
"""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CameraInterface:
    """
    Simple camera interface using OpenCV.
    
    Wraps cv2.VideoCapture with error handling and consistent API.
    
    Attributes:
        camera_id: Camera device index
        width: Frame width in pixels
        height: Frame height in pixels
        fps: Target frames per second
        camera: OpenCV VideoCapture instance
    """
    
    def __init__(
        self,
        camera_id: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30
    ):
        """
        Initialize camera interface.
        
        Args:
            camera_id: Camera device index (0 for default webcam)
            width: Desired frame width
            height: Desired frame height
            fps: Target frames per second
            
        Raises:
            RuntimeError: If camera cannot be opened
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        
        # Open camera
        self.camera = cv2.VideoCapture(camera_id)
        
        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera {camera_id}")
        
        # Configure camera
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.camera.set(cv2.CAP_PROP_FPS, fps)
        
        # Verify actual settings
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
        
        logger.info(f"Camera {camera_id} opened: {actual_width}x{actual_height} @ {actual_fps} FPS")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera.
        
        Returns:
            Tuple of (success, frame)
            success is True if frame was read successfully
            frame is BGR numpy array or None if read failed
        """
        ret, frame = self.camera.read()
        return ret, frame
    
    def release(self):
        """Release camera resources."""
        if self.camera is not None:
            self.camera.release()
            logger.info(f"Camera {self.camera_id} released")
    
    def __del__(self):
        """Cleanup on deletion."""
        self.release()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


def main():
    """Test camera interface."""
    print("Testing Camera Interface...")
    
    try:
        with CameraInterface() as camera:
            print("✓ Camera opened successfully")
            print(f"  Resolution: {camera.width}x{camera.height}")
            print(f"  FPS: {camera.fps}")
            print("\nPress 'q' to quit...")
            
            while True:
                ret, frame = camera.read_frame()
                
                if not ret:
                    print("✗ Failed to read frame")
                    break
                
                # Display frame
                cv2.imshow("Camera Test", frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            cv2.destroyAllWindows()
            print("\n✓ Camera test complete!")
    
    except RuntimeError as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
