"""
Quick script to add a face to the database for testing.
Captures a photo from webcam and adds it with a name.
"""

import cv2
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.face_database import FaceDatabase
from src.vision.face_detector import FaceDetector
from src.vision.face_encoder import FaceEncoder

def capture_and_add_face(name: str):
    """Capture face from webcam and add to database."""
    
    print(f"\n📸 Capturing face for: {name}")
    print("=" * 60)
    
    # Initialize components
    print("Initializing camera and face detection...")
    detector = FaceDetector()
    encoder = FaceEncoder()
    database = FaceDatabase()
    
    # Open camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ Error: Could not open camera")
        return False
    
    print("\n✓ Camera ready!")
    print("\nInstructions:")
    print("  - Look at the camera")
    print("  - Press SPACE when your face is clearly visible")
    print("  - Press ESC to cancel")
    print("\nWaiting for face...")
    
    captured = False
    
    while not captured:
        ret, frame = camera.read()
        if not ret:
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
        
        cv2.imshow('Add Face to Database', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("\n❌ Cancelled by user")
            camera.release()
            cv2.destroyAllWindows()
            return False
        
        elif key == 32:  # SPACE
            if len(faces) == 1:
                print(f"\n📷 Capturing face for {name}...")
                
                # Add to database (it will auto-detect and encode)
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
    
    camera.release()
    cv2.destroyAllWindows()
    
    print(f"\n✓ Face database updated!")
    print("\nYou can now run the demo and it will recognize you!")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Add a face to the recognition database')
    parser.add_argument('name', nargs='?', default=None, help='Name for the person')
    
    args = parser.parse_args()
    
    name = args.name
    if not name:
        print("Enter the name for this person:")
        name = input("> ").strip()
        if not name:
            print("❌ Name cannot be empty")
            sys.exit(1)
    
    success = capture_and_add_face(name)
    sys.exit(0 if success else 1)
