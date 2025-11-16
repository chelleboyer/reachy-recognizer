"""Gesture Recognition with Voice Response Demo

Demonstrates Reachy responding to thumbs up gesture with voice.
When thumbs up is detected, Reachy says "You got it boss!"

Usage:
    python gesture_voice_demo.py

    # On Raspberry Pi with Reachy:
    python gesture_voice_demo.py --reachy
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

# Auto-detect platform and configure Qt
if sys.platform.startswith("linux"):
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                os.environ['QT_QPA_PLATFORM'] = 'xcb'
    except:
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
elif sys.platform == "darwin":
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'
elif sys.platform.startswith("win"):
    os.environ['QT_QPA_PLATFORM'] = 'windows'

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.vision.hand_detector import HandDetector
from src.vision.gesture_recognizer import GestureRecognizer, GestureType
from src.coordination.gesture_coordinator import GestureCoordinator, GestureCommand, GestureEvent
from src.events.event_system import EventManager, EventType
from src.voice.adaptive_tts_manager import AdaptiveTTSManager
from src.behaviors.behavior_module import BehaviorManager


def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi."""
    try:
        with open('/proc/device-tree/model', 'r') as f:
            return 'Raspberry Pi' in f.read()
    except:
        return False


def setup_reachy_camera():
    """Initialize Reachy Mini and get camera access."""
    try:
        from reachy_mini import ReachyMini
        
        print("Connecting to Reachy...")
        reachy = ReachyMini()
        
        # Test camera access
        frame_data = reachy.media.get_frame()
        if frame_data is None:
            raise RuntimeError("Reachy camera returned None")
        frame = np.asarray(frame_data)
        if frame.size == 0:
            raise RuntimeError("Reachy camera returned empty frame")
        
        print("✓ Reachy camera ready!")
        return reachy
    except Exception as e:
        print(f"✗ Failed to initialize Reachy: {e}")
        return None


def main():
    """Main demo loop."""
    parser = argparse.ArgumentParser(description="Gesture Voice Response Demo")
    parser.add_argument(
        '--reachy', action='store_true',
        help='Force use of Reachy camera'
    )
    parser.add_argument(
        '--webcam', action='store_true',
        help='Force use of webcam instead of Reachy camera'
    )
    parser.add_argument(
        '--camera-index', type=int, default=0,
        help='Webcam index (default: 0)'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("👍 Gesture Voice Response Demo")
    print("=" * 70)
    
    # Detect platform and setup camera
    use_reachy = False
    reachy = None
    camera = None
    behavior_manager = None
    
    if (args.reachy or (not args.webcam and is_raspberry_pi())):
        print("🔍 Using Reachy camera")
        reachy = setup_reachy_camera()
        if reachy:
            use_reachy = True
            # Initialize behavior manager with Reachy
            try:
                behavior_manager = BehaviorManager(enable_robot=True)
                print("✓ Behavior manager initialized")
            except Exception as e:
                print(f"⚠️  Behavior manager failed: {e}")
        else:
            print("⚠️  Falling back to webcam")
    
    if not use_reachy:
        print(f"📷 Using webcam (index {args.camera_index})")
        camera = cv2.VideoCapture(args.camera_index)
        if not camera.isOpened():
            print("✗ Failed to open camera")
            return 1
        print("✓ Camera opened")
    
    # Initialize hand detector
    print("\nInitializing hand detector...")
    try:
        detector = HandDetector("src/config/hand_detection.yaml")
        print("✓ Hand detector initialized")
    except Exception as e:
        print(f"✗ Failed to initialize hand detector: {e}")
        return 1
    
    # Initialize gesture recognizer
    print("Initializing gesture recognizer...")
    try:
        recognizer = GestureRecognizer("src/config/gesture_recognition.yaml")
        print("✓ Gesture recognizer initialized")
    except Exception as e:
        print(f"✗ Failed to initialize gesture recognizer: {e}")
        return 1
    
    # Initialize event manager
    print("Initializing event manager...")
    event_manager = EventManager(debounce_seconds=1.0)
    print("✓ Event manager initialized")
    
    # Initialize gesture coordinator
    print("Initializing gesture coordinator...")
    try:
        coordinator = GestureCoordinator(
            hand_detector=detector,
            gesture_recognizer=recognizer,
            event_manager=event_manager
        )
        print("✓ Gesture coordinator initialized")
    except Exception as e:
        print(f"✗ Failed to initialize gesture coordinator: {e}")
        return 1
    
    # Initialize TTS manager
    print("Initializing voice system...")
    try:
        tts = AdaptiveTTSManager(enable_caching=True)
        print("✓ Voice system initialized (OpenAI TTS)")
    except Exception as e:
        print(f"⚠️  Voice system failed: {e}, continuing without voice")
        tts = None
    
    # Register callback for gesture events
    thumbs_up_count = 0
    
    def on_gesture_detected(gesture_event: GestureEvent):
        """Handle gesture detection event."""
        nonlocal thumbs_up_count
        
        print(f"\n🎯 Gesture detected: {gesture_event.command.value}")
        print(f"   Type: {gesture_event.gesture_result.gesture_type.value}")
        print(f"   Confidence: {gesture_event.gesture_result.confidence:.2f}")
        print(f"   Hand: {gesture_event.gesture_result.handedness}")
        
        # Respond to thumbs up
        if gesture_event.command == GestureCommand.APPROVE:
            thumbs_up_count += 1
            print(f"👍 Thumbs up #{thumbs_up_count} detected!")
            
            # Make Reachy wave if available
            if behavior_manager and behavior_manager.reachy:
                try:
                    print("   🤖 Reachy waving...")
                    behavior_manager.execute_behavior("greeting_wave")
                except Exception as e:
                    print(f"   ⚠️  Wave failed: {e}")
            
            # Speak response
            if tts:
                try:
                    print("   🗣️  Speaking: 'You got it boss!'")
                    tts.speak_async(
                        "You got it boss!",
                        voice="nova",  # Male voice
                        speed=1.0
                    )
                except Exception as e:
                    print(f"   ⚠️  Speech failed: {e}")
        
        elif gesture_event.command == GestureCommand.SKIP:
            print("👋 Wave detected!")
            if tts:
                try:
                    tts.speak_async("Hello there!", voice="nova")
                except:
                    pass
        
        elif gesture_event.command == GestureCommand.PAUSE:
            print("✋ Palm stop detected!")
            if tts:
                try:
                    tts.speak_async("Okay, I'll wait", voice="nova")
                except:
                    pass
    
    event_manager.add_callback(EventType.GESTURE_DETECTED, on_gesture_detected)
    print("✓ Gesture callback registered")
    
    print("=" * 70)
    print("📹 Starting gesture recognition...")
    print("=" * 70)
    print("👍 Show gestures to the camera:")
    print("   - Thumbs Up → 'You got it boss!' + wave")
    print("   - Wave → 'Hello there!'")
    print("   - Palm Stop → 'Okay, I'll wait'")
    print("\nPress 'q' to quit\n")
    
    # Create display window
    window_name = "Gesture Voice Demo"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    frame_count = 0
    fps = 0.0
    last_fps_time = time.time()
    
    try:
        while True:
            # Get frame
            if use_reachy and reachy:
                frame_data = reachy.media.get_frame()
                if frame_data is None:
                    print("Failed to get frame from Reachy")
                    break
                frame = np.asarray(frame_data)
            elif camera is not None:
                ret, frame = camera.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
            else:
                break
            
            # Process frame through coordinator
            # This will detect hands, recognize gestures, and emit events
            gesture_events = coordinator.process_frame(frame)
            
            # Draw simple overlay
            h, w = frame.shape[:2]
            cv2.putText(
                frame, f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
            cv2.putText(
                frame, f"Thumbs up count: {thumbs_up_count}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
            cv2.putText(
                frame, "Press 'q' to quit",
                (10, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
            
            # Display frame
            cv2.imshow(window_name, frame)
            
            # Update FPS
            frame_count += 1
            if frame_count % 10 == 0:
                current_time = time.time()
                elapsed = current_time - last_fps_time
                if elapsed > 0:
                    fps = 10 / elapsed
                    last_fps_time = current_time
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("\nQuitting...")
                break
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print("\nCleaning up...")
        
        cv2.destroyAllWindows()
        
        if camera:
            camera.release()
        
        detector.close()
        
        print(f"\n✓ Demo complete - detected {thumbs_up_count} thumbs up gestures")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
