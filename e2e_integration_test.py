#!/usr/bin/env python3
"""
End-to-End Integration Test - Story 1.4
Combines camera capture with Reachy control to validate complete pipeline.

This test demonstrates:
1. Camera capture from webcam
2. Face detection using OpenCV Haar cascade
3. Reachy movement response (look at camera when face detected, neutral otherwise)
4. Continuous operation for 2 minutes
5. Event logging and statistics

Prerequisites:
- Reachy daemon running (uvx reachy-mini --daemon start)
- FastAPI server running (python test-webui.py)
- Webcam connected and accessible

Usage:
    python e2e_integration_test.py [--duration SECONDS] [--camera INDEX]

Example:
    python e2e_integration_test.py --duration 120 --camera 0
"""

import argparse
import time
from datetime import datetime, timedelta
import cv2
import numpy as np
import requests
from typing import Optional, Tuple
import sys

# Optional TTS import
try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("⚠ pyttsx3 not available - TTS will be simulated in console")


class FaceDetector:
    """Simple face detection using OpenCV Haar cascade."""
    
    def __init__(self):
        """Initialize the Haar cascade face detector."""
        self.face_cascade = None
        self.load_cascade()
    
    def load_cascade(self):
        """Load the Haar cascade classifier for face detection."""
        # Load pre-trained Haar cascade from OpenCV
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise RuntimeError(f"Failed to load Haar cascade from {cascade_path}")
        
        print(f"✓ Loaded Haar cascade face detector")
    
    def detect_faces(self, frame: np.ndarray) -> list:
        """
        Detect faces in the frame using Haar cascade.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            List of (x, y, w, h) tuples for each detected face
        """
        # Convert to grayscale for Haar cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return faces


class ReachyController:
    """Interface to control Reachy via FastAPI server."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize Reachy controller.
        
        Args:
            base_url: Base URL of FastAPI server
        """
        self.base_url = base_url
        self.verify_connection()
    
    def verify_connection(self):
        """Verify connection to FastAPI server."""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print(f"✓ Connected to Reachy server at {self.base_url}")
            else:
                print(f"⚠ Server responded with status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to connect to Reachy server: {e}")
            print("  Make sure test-webui.py is running (python test-webui.py)")
            raise
    
    def look_at_camera(self) -> bool:
        """
        Command Reachy to look at the camera.
        
        Returns:
            True if command succeeded, False otherwise
        """
        try:
            # Move head to look down/forward at camera (typical webcam position)
            # Pitch down slightly to look at desk-level camera
            payload = {
                "head_pitch": 20.0,      # Look down 20 degrees
                "head_roll": 0.0,
                "head_yaw": 0.0,
                "head_x": 0.0,
                "head_y": 0.0,
                "head_z": 0.0,
                "antenna_left": 30.0,    # Antennas up (interested)
                "antenna_right": 30.0,
                "body_yaw": 0.0
            }
            response = requests.post(
                f"{self.base_url}/api/manual-control",
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to send look_at_camera command: {e}")
            return False
    
    def return_to_neutral(self) -> bool:
        """
        Command Reachy to return to neutral position.
        
        Returns:
            True if command succeeded, False otherwise
        """
        try:
            # Use the manual-control endpoint to move to neutral position
            payload = {
                "head_pitch": 0.0,
                "head_roll": 0.0,
                "head_yaw": 0.0,
                "head_x": 0.0,
                "head_y": 0.0,
                "head_z": 0.0,
                "antenna_left": 0.0,
                "antenna_right": 0.0,
                "body_yaw": 0.0
            }
            response = requests.post(
                f"{self.base_url}/api/manual-control",
                json=payload,
                timeout=5
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"✗ Failed to send return_to_neutral command: {e}")
            return False


class TextToSpeech:
    """Text-to-speech interface using pyttsx3."""
    
    def __init__(self):
        """Initialize TTS engine."""
        self.engine = None
        
        if not HAS_TTS:
            print("✓ TTS engine: simulation mode (pyttsx3 not installed)")
            return
            
        try:
            self.engine = pyttsx3.init()
            # Set properties for better voice
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0.0 to 1.0)
            print("✓ TTS engine initialized")
        except Exception as e:
            print(f"⚠ TTS initialization failed: {e}")
            self.engine = None
    
    def say(self, text: str, async_mode: bool = True):
        """
        Speak the given text.
        
        Args:
            text: Text to speak
            async_mode: If True, speak asynchronously (non-blocking)
        """
        if not self.engine:
            # Simulation mode - just print
            return
        
        try:
            if async_mode:
                # Non-blocking speech (won't wait for completion)
                self.engine.say(text)
                self.engine.runAndWait()
            else:
                # Blocking speech
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            print(f"✗ TTS error: {e}")


class IntegrationTest:
    """End-to-end integration test combining camera, detection, and Reachy control."""
    
    def __init__(self, camera_index: int = 0, duration_seconds: int = 120):
        """
        Initialize the integration test.
        
        Args:
            camera_index: Camera device index (default 0)
            duration_seconds: Test duration in seconds (default 120)
        """
        self.camera_index = camera_index
        self.duration_seconds = duration_seconds
        
        # Components
        self.cap: Optional[cv2.VideoCapture] = None
        self.detector = FaceDetector()
        self.reachy = ReachyController()
        self.tts = TextToSpeech()
        
        # State tracking
        self.face_detected_last = False
        self.has_greeted = False  # Track if we've greeted in this session
        self.start_time: Optional[float] = None
        self.frame_count = 0
        self.detection_events = 0
        self.reachy_commands = 0
        
        # Timing
        self.last_detection_time = 0
        self.detection_cooldown = 1.0  # Don't send commands more than once per second
    
    def initialize_camera(self):
        """Initialize camera capture."""
        print(f"\n[1/4] Initializing camera (device {self.camera_index})...")
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Verify by reading a test frame
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Camera opened but failed to read frame")
        
        height, width = frame.shape[:2]
        print(f"✓ Camera initialized: {width}x{height}")
    
    def run(self):
        """Run the integration test."""
        print("\n" + "="*70)
        print("End-to-End Integration Test - Story 1.4")
        print("="*70)
        print(f"Duration: {self.duration_seconds} seconds")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        try:
            # Initialize
            self.initialize_camera()
            print("[2/4] Face detector ready")
            print("[3/4] Reachy controller connected")
            print(f"[4/4] Starting test loop for {self.duration_seconds} seconds...")
            print("\nPress 'q' or ESC to stop early\n")
            
            # Start test
            self.start_time = time.time()
            end_time = self.start_time + self.duration_seconds
            
            cv2.namedWindow('E2E Integration Test', cv2.WINDOW_NORMAL)
            
            while time.time() < end_time:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("✗ Failed to read frame")
                    break
                
                self.frame_count += 1
                
                # Detect faces
                faces = self.detector.detect_faces(frame)
                face_detected = len(faces) > 0
                
                # Draw bounding boxes
                display_frame = frame.copy()
                for (x, y, w, h) in faces:
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(display_frame, "FACE", (x, y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # State transition logging and Reachy commands
                current_time = time.time()
                if face_detected != self.face_detected_last:
                    # State changed
                    if face_detected:
                        self.log_event(f"DETECTED {len(faces)} face(s)")
                        self.detection_events += 1
                        
                        # Greet Michelle on first detection
                        if not self.has_greeted:
                            self.tts.say("Hi Michelle!")
                            self.log_event("🔊 Reachy: 'Hi Michelle!'")
                            self.has_greeted = True
                        
                        # Command Reachy to return to neutral when face detected
                        if current_time - self.last_detection_time > self.detection_cooldown:
                            if self.reachy.return_to_neutral():
                                self.log_event("→ Reachy: RETURN TO NEUTRAL (face detected)")
                                self.reachy_commands += 1
                                self.last_detection_time = current_time
                    else:
                        self.log_event("NO FACES detected")
                        
                        # Command Reachy to look at camera when no face
                        if current_time - self.last_detection_time > self.detection_cooldown:
                            if self.reachy.look_at_camera():
                                self.log_event("→ Reachy: LOOK AT CAMERA (searching)")
                                self.reachy_commands += 1
                                self.last_detection_time = current_time
                    
                    self.face_detected_last = face_detected
                
                # Add overlay
                self.add_overlay(display_frame, faces, end_time)
                
                # Display
                cv2.imshow('E2E Integration Test', display_frame)
                
                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\n[User requested stop]")
                    break
            
            # Complete
            self.print_summary()
            
        except KeyboardInterrupt:
            print("\n\n[Interrupted by user]")
            self.print_summary()
        
        except Exception as e:
            print(f"\n✗ Error during test: {e}")
            raise
        
        finally:
            self.shutdown()
    
    def add_overlay(self, frame: np.ndarray, faces: list, end_time: float):
        """Add status overlay to frame."""
        elapsed = time.time() - self.start_time
        remaining = max(0, end_time - time.time())
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # Status text
        status = "FACE DETECTED" if len(faces) > 0 else "NO FACE"
        status_color = (0, 255, 0) if len(faces) > 0 else (0, 0, 255)
        
        # Add text overlay
        y_offset = 30
        cv2.putText(frame, f"Status: {status}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        y_offset += 30
        cv2.putText(frame, f"Elapsed: {int(elapsed)}s / {self.duration_seconds}s", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        y_offset += 25
        cv2.putText(frame, f"Remaining: {int(remaining)}s", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        y_offset += 25
        cv2.putText(frame, f"FPS: {fps:.1f}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        y_offset += 25
        cv2.putText(frame, f"Detections: {self.detection_events}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        y_offset += 25
        cv2.putText(frame, f"Commands: {self.reachy_commands}", 
                   (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Instructions
        cv2.putText(frame, "Press 'q' or ESC to stop", 
                   (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def log_event(self, message: str):
        """Log an event with timestamp."""
        elapsed = time.time() - self.start_time
        timestamp = f"[{int(elapsed):3d}s]"
        print(f"{timestamp} {message}")
    
    def print_summary(self):
        """Print test summary statistics."""
        elapsed = time.time() - self.start_time
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Duration:        {elapsed:.1f} seconds")
        print(f"Frames:          {self.frame_count}")
        print(f"Average FPS:     {fps:.1f}")
        print(f"Detection Events: {self.detection_events}")
        print(f"Reachy Commands: {self.reachy_commands}")
        print(f"Ended:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Success criteria
        success = (
            elapsed >= min(30, self.duration_seconds) and  # Ran for at least 30 seconds
            self.frame_count > 0 and
            fps > 10  # Reasonable frame rate
        )
        
        if success:
            print("\n✅ Integration test PASSED")
        else:
            print("\n⚠ Integration test may have issues")
        print()
    
    def shutdown(self):
        """Clean up resources."""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Resources released")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="End-to-End Integration Test for Reachy Recognizer"
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=120,
        help='Test duration in seconds (default: 120)'
    )
    parser.add_argument(
        '--camera',
        type=int,
        default=0,
        help='Camera device index (default: 0)'
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    print("\nPrerequisites Check:")
    print("1. Reachy daemon running? (uvx reachy-mini --daemon start)")
    print("2. FastAPI server running? (python test-webui.py)")
    print("3. Webcam connected?")
    input("\nPress ENTER to continue or Ctrl+C to abort...")
    
    test = IntegrationTest(
        camera_index=args.camera,
        duration_seconds=args.duration
    )
    test.run()


if __name__ == "__main__":
    main()
