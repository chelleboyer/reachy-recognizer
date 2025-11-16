#!/usr/bin/env python3
"""
Simple test script for face recognition with Reachy camera.
Tests the complete pipeline: detection -> encoding -> recognition.
"""

import os
import sys
import time
import platform
from pathlib import Path

# Fix OpenCV platform issues based on OS
if platform.system() == "Windows":
    os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
    os.environ["QT_QPA_PLATFORM"] = "windows"
elif platform.system() == "Linux":
    os.environ["QT_QPA_PLATFORM"] = "xcb"
elif platform.system() == "Darwin":  # macOS
    os.environ["QT_QPA_PLATFORM"] = "cocoa"

import cv2

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.face_database import FaceDatabase
from src.vision.face_detector import FaceDetector
from src.vision.face_encoder import FaceEncoder
from src.vision.face_recognizer import FaceRecognizer

# Import Reachy (optional)
try:
    from reachy_mini import ReachyMini
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("⚠️  Reachy SDK not available - will use webcam")


def test_face_recognition(use_reachy: bool = False):
    """Test face recognition in real-time."""
    
    print("\n🎯 Face Recognition Test")
    print("=" * 60)
    
    # Initialize components
    print("\nInitializing components...")
    detector = FaceDetector()
    encoder = FaceEncoder()
    database = FaceDatabase()
    recognizer = FaceRecognizer(database, detector=detector, encoder=encoder)
    
    # Load database
    if not database.load_database("data/faces.json"):
        print("❌ No face database found!")
        print("   Run: python add_face.py 'YourName' --reachy")
        return False
    
    print(f"✓ Loaded database with {len(database.get_all_names())} face(s)")
    print(f"  Names: {database.get_all_names()}")
    
    # Initialize camera
    reachy = None
    camera = None
    reachy_ready = False
    
    if use_reachy and REACHY_AVAILABLE:
        try:
            print("\nConnecting to Reachy...")
            reachy = ReachyMini()
            test_frame = reachy.media.get_frame()
            
            if test_frame is not None:
                print("✓ Reachy camera ready!")
                reachy_ready = True
            else:
                print("❌ Reachy camera not working, falling back to webcam")
                reachy.client.disconnect()
                reachy = None
        except Exception as e:
            print(f"❌ Reachy error: {e}")
            print("   Falling back to webcam")
            if reachy:
                reachy.client.disconnect()
            reachy = None
    
    # Fallback to webcam
    if not reachy_ready:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("❌ Could not open webcam")
            return False
        print("✓ Webcam ready!")
    
    print("\n" + "=" * 60)
    print("Instructions:")
    print("  - Look at the camera")
    print("  - Recognition runs automatically")
    print("  - Press ESC to exit")
    print("=" * 60 + "\n")
    
    # Create window
    window_name = 'Face Recognition Test'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Stats
    frame_count = 0
    recognition_count = 0
    start_time = time.time()
    
    try:
        while True:
            # Get frame
            if reachy_ready and reachy:
                frame = reachy.media.get_frame()
                if frame is None:
                    time.sleep(0.033)
                    continue
            else:
                ret, frame = camera.read()
                if not ret:
                    continue
            
            frame_count += 1
            
            # Detect faces
            faces = detector.detect_faces(frame)
            
            # Display frame
            display_frame = frame.copy()
            
            # Process each face
            for (top, right, bottom, left) in faces:
                # Encode and recognize
                encoding = encoder.encode_face_from_frame(frame, (top, right, bottom, left))
                
                if encoding is not None:
                    name, confidence = recognizer.recognize_face(encoding)
                    recognition_count += 1
                    
                    # Draw bounding box
                    if name != "Unknown":
                        color = (0, 255, 0)  # Green for known
                        label = f"{name} ({confidence:.2f})"
                    else:
                        color = (0, 0, 255)  # Red for unknown
                        label = "Unknown"
                    
                    cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                    cv2.putText(
                        display_frame, 
                        label,
                        (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        color,
                        2
                    )
            
            # Show stats
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            cv2.putText(
                display_frame,
                f"FPS: {fps:.1f} | Faces: {len(faces)} | Recognized: {recognition_count}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2
            )
            
            # Display
            cv2.imshow(window_name, display_frame)
            
            # Check for exit
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    
    finally:
        # Cleanup
        if camera is not None:
            camera.release()
        if reachy is not None:
            reachy.client.disconnect()
        cv2.destroyAllWindows()
        
        # Print stats
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Test Results:")
        print(f"  Total frames: {frame_count}")
        print(f"  Recognitions: {recognition_count}")
        print(f"  Duration: {elapsed:.1f}s")
        print(f"  Average FPS: {frame_count / elapsed:.1f}")
        print("=" * 60)
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test face recognition')
    parser.add_argument('--reachy', action='store_true',
                       help='Use Reachy camera instead of webcam')
    
    args = parser.parse_args()
    
    success = test_face_recognition(use_reachy=args.reachy)
    sys.exit(0 if success else 1)
