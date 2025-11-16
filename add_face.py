"""
Quick script to add a face to the database for testing.
Captures a photo from webcam or Reachy camera and adds it with a name.
"""

import os
import sys
import time
from pathlib import Path

# Fix OpenCV Qt platform plugin error on Windows
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
os.environ["QT_QPA_PLATFORM"] = "windows"  # Force Windows platform
# Disable Qt plugins to use native Windows display
os.environ["OPENCV_VIDEOIO_DEBUG"] = "1"

import cv2

# Force OpenCV to use HighGUI without Qt
cv2.setNumThreads(1)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.face_database import FaceDatabase
from src.vision.face_detector import FaceDetector
from src.vision.face_encoder import FaceEncoder

# Import Reachy components (optional)
try:
    from reachy_mini import ReachyMini
    from reachy_mini_conversation_app.camera_worker import CameraWorker  # type: ignore
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("⚠️  Reachy SDK not available - will use webcam")

def capture_and_add_face(name: str, use_reachy: bool = False):
    """Capture face from webcam or Reachy camera and add to database."""
    
    print(f"\n📸 Capturing face for: {name}")
    print("=" * 60)
    
    # Initialize components
    print("Initializing camera and face detection...")
    detector = FaceDetector()
    encoder = FaceEncoder()
    database = FaceDatabase()
    
    # Initialize camera
    reachy = None
    camera_worker = None
    camera = None
    reachy_camera_ready = False
    
    if use_reachy and REACHY_AVAILABLE:
        try:
            print("Connecting to Reachy...")
            reachy = ReachyMini()
            camera_worker = CameraWorker(reachy, head_tracker=None)
            camera_worker.start()
            
            # Wait for first frame
            print("Waiting for Reachy camera...")
            for _ in range(50):  # Wait up to 5 seconds
                frame = camera_worker.get_latest_frame()
                if frame is not None:
                    break
                time.sleep(0.1)
            
            if frame is None:
                print("❌ Error: Reachy camera not producing frames")
                if camera_worker:
                    camera_worker.stop()
                if reachy:
                    reachy.client.disconnect()
                print("   Falling back to webcam...")
            else:
                print("✓ Reachy camera ready!")
                reachy_camera_ready = True
        except Exception as e:
            print(f"❌ Error connecting to Reachy: {e}")
            print("   Falling back to webcam...")
            if camera_worker:
                camera_worker.stop()
            if reachy:
                reachy.client.disconnect()
            camera_worker = None
            reachy = None
    
    # Open webcam if not using Reachy camera
    if not reachy_camera_ready:
        camera_capture = cv2.VideoCapture(0)
        if not camera_capture.isOpened():
            print("❌ Error: Could not open webcam")
            return False
        camera = camera_capture
        print("✓ Webcam ready!")
    
    print("\nInstructions:")
    print("  - Look at the camera")
    print("  - Press SPACE when your face is clearly visible")
    print("  - Press ESC to cancel")
    print("\nWaiting for face...")
    
    # Create window and ensure it's visible
    window_name = 'Add Face to Database'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    captured = False
    
    while not captured:
        # Get frame from appropriate source
        if reachy_camera_ready and camera_worker:
            frame = camera_worker.get_latest_frame()
            if frame is None:
                time.sleep(0.033)  # ~30 FPS
                continue
            # Convert RGB back to BGR for OpenCV display
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        else:
            if camera is not None:
                ret, frame = camera.read()
                if not ret:
                    continue
            else:
                continue
        
        # Detect faces
        faces = detector.detect_faces(frame)
        
        # Draw bounding boxes
        display_frame = frame.copy()
        for (top, right, bottom, left) in faces:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(display_frame, f"Press SPACE to capture as '{name}'", 
                       (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Show status
        if len(faces) == 0:
            cv2.putText(display_frame, "No face detected - move closer", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif len(faces) > 1:
            cv2.putText(display_frame, "Multiple faces - only show one face", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        else:
            cv2.putText(display_frame, "Face detected! Press SPACE to capture", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Display the frame
        cv2.imshow(window_name, display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("\n❌ Cancelled by user")
            if camera is not None:
                camera.release()
            if camera_worker is not None:
                camera_worker.stop()
            if reachy is not None:
                reachy.client.disconnect()
            cv2.destroyAllWindows()
            return False
        
        elif key == 32:  # SPACE
            if len(faces) == 1:
                print(f"\n📷 Capturing face for {name}...")
                
                # Frame is already in BGR format (either from webcam or converted from Reachy RGB)
                # Database expects BGR, so use frame as-is
                success = database.add_face(name, frame, auto_detect=True)
                
                if success:
                    # Save the database
                    database.save_database("data/faces.json")
                    all_names = database.get_all_names()
                    print(f"✅ Added {name} to database!")
                    print(f"   Database now contains {len(all_names)} face(s): {all_names}")
                    print(f"   Saved to: data/faces.json")
                    captured = True
                else:
                    print("❌ Failed to add face, try again")
            elif len(faces) == 0:
                print("⚠️  No face detected, position yourself in front of camera")
            else:
                print("⚠️  Multiple faces detected, only show one face")
    
    # Cleanup
    if camera is not None:
        camera.release()  # type: ignore
    if camera_worker is not None:
        camera_worker.stop()
    if reachy is not None:
        reachy.client.disconnect()
    cv2.destroyAllWindows()
    
    print(f"\n✓ Face database updated!")
    print("\nYou can now run the demo and it will recognize you!")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add a face to the recognition database')
    parser.add_argument('name', nargs='?', default=None, help='Name for the person')
    parser.add_argument('--reachy', action='store_true', 
                       help='Use Reachy camera instead of webcam')
    
    args = parser.parse_args()
    
    name = args.name
    if not name:
        print("Enter the name for this person:")
        name = input("> ").strip()
        if not name:
            print("❌ Name cannot be empty")
            sys.exit(1)
    
    success = capture_and_add_face(name, use_reachy=args.reachy)
    sys.exit(0 if success else 1)
