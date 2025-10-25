"""
Standalone camera test script for Story 1.3: Camera Input Pipeline
Tests OpenCV camera capture with FPS measurement and error handling.
"""
import cv2
import time
import numpy as np
from typing import Optional


class CameraCapture:
    """Manages webcam capture with OpenCV."""
    
    def __init__(self, device_index: int = 0, target_fps: int = 30):
        """
        Initialize camera capture.
        
        Args:
            device_index: Camera device index (default 0 for primary webcam)
            target_fps: Target frames per second (default 30)
        """
        self.device_index = device_index
        self.target_fps = target_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # FPS tracking
        self.frame_count = 0
        self.start_time = None
        self.current_fps = 0.0
        
        # Frame info
        self.width = 0
        self.height = 0
    
    def initialize(self) -> bool:
        """
        Initialize camera capture.
        
        Returns:
            True if successful, False otherwise
        """
        print(f"🎥 Initializing camera (device {self.device_index})...")
        
        try:
            self.cap = cv2.VideoCapture(self.device_index)
            
            if not self.cap.isOpened():
                print(f"❌ Cannot open camera device {self.device_index}")
                print("   Possible issues:")
                print("   - Camera not connected")
                print("   - Camera in use by another application")
                print("   - Permission denied (check OS camera permissions)")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            
            # Read actual properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"✅ Camera initialized")
            print(f"   Resolution: {self.width}x{self.height}")
            print(f"   Target FPS: {self.target_fps}")
            print(f"   Camera FPS setting: {actual_fps}")
            
            # Validate minimum resolution
            if self.width < 640 or self.height < 480:
                print(f"⚠️  Warning: Resolution below recommended 640x480")
            
            self.is_running = True
            self.start_time = time.time()
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            return False
    
    def read_frame(self) -> Optional[tuple]:
        """
        Read a frame from the camera.
        
        Returns:
            Tuple of (bgr_frame, rgb_frame) or None if failed
        """
        if not self.cap or not self.is_running:
            return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                print("⚠️  Failed to read frame from camera")
                return None
            
            # Convert BGR (OpenCV default) to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Update FPS counter
            self.frame_count += 1
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                self.current_fps = self.frame_count / elapsed
            
            return (frame, rgb_frame)
            
        except Exception as e:
            print(f"❌ Error reading frame: {e}")
            return None
    
    def add_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Add FPS and status overlay to frame.
        
        Args:
            frame: BGR frame from camera
            
        Returns:
            Frame with overlay
        """
        # Add FPS counter
        fps_text = f"FPS: {self.current_fps:.1f}"
        cv2.putText(frame, fps_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add resolution info
        res_text = f"{self.width}x{self.height}"
        cv2.putText(frame, res_text, (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add frame count
        count_text = f"Frames: {self.frame_count}"
        cv2.putText(frame, count_text, (10, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add instructions
        cv2.putText(frame, "Press 'q' or ESC to quit", (10, self.height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def run_display_loop(self):
        """
        Run continuous capture and display loop.
        Press 'q' or ESC to exit.
        """
        if not self.is_running:
            print("❌ Camera not initialized. Call initialize() first.")
            return
        
        print("\n🎬 Starting camera feed...")
        print("   Press 'q' or ESC to quit")
        print()
        
        window_name = "Camera Test - Story 1.3"
        cv2.namedWindow(window_name)
        
        frame_time = 1.0 / self.target_fps if self.target_fps > 0 else 0.033
        
        try:
            while self.is_running:
                loop_start = time.time()
                
                # Read frame
                result = self.read_frame()
                if result is None:
                    print("⚠️  Camera disconnected or frame read failed")
                    break
                
                bgr_frame, rgb_frame = result
                
                # Add overlay to BGR frame for display
                display_frame = self.add_overlay(bgr_frame.copy())
                
                # Display frame
                cv2.imshow(window_name, display_frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\n⏹️  Stopping camera feed...")
                    break
                
                # Frame rate control
                elapsed = time.time() - loop_start
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
        
        except KeyboardInterrupt:
            print("\n⏹️  Interrupted by user...")
        
        except Exception as e:
            print(f"\n❌ Error in display loop: {e}")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Release camera resources and close windows."""
        print("\n🛑 Shutting down camera...")
        
        self.is_running = False
        
        if self.cap:
            self.cap.release()
            print("   ✓ Camera released")
        
        cv2.destroyAllWindows()
        print("   ✓ Windows closed")
        
        # Print final statistics
        if self.start_time and self.frame_count > 0:
            total_time = time.time() - self.start_time
            avg_fps = self.frame_count / total_time if total_time > 0 else 0
            print(f"\n📊 Session Statistics:")
            print(f"   Total frames: {self.frame_count}")
            print(f"   Duration: {total_time:.1f}s")
            print(f"   Average FPS: {avg_fps:.1f}")


def main():
    """Main function to test camera capture."""
    print("=" * 60)
    print("Story 1.3: Camera Input Pipeline - Test")
    print("=" * 60)
    print()
    
    camera = CameraCapture(device_index=0, target_fps=30)
    
    if camera.initialize():
        camera.run_display_loop()
    else:
        print("\n❌ Camera initialization failed")
        print("\nTroubleshooting:")
        print("1. Check camera is connected")
        print("2. Close other apps using the camera (Zoom, Teams, etc.)")
        print("3. Check camera permissions in OS settings")
        print("4. Try a different device index (e.g., 1 instead of 0)")
        return 1
    
    print("\n✅ Camera test complete!")
    return 0


if __name__ == "__main__":
    exit(main())
