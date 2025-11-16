"""Gesture Recognition Demo - Story 3.2

Live demonstration of gesture recognition on Reachy Mini robot.
Detects and displays thumbs up, wave, and palm stop gestures in real-time.

Usage:
    # On Raspberry Pi with Reachy robot:
    python gesture_recognition_demo.py

    # On Windows with webcam (fallback):
    python gesture_recognition_demo.py --webcam

Controls:
    - Press 'q' to quit
    - Press 's' to show/hide statistics
    - Press 'r' to reset statistics
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import cv2
import numpy as np

# Auto-detect platform and configure Qt
if sys.platform.startswith("linux"):
    # Try to detect if we're on a Pi (headless)
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            if 'Raspberry Pi' in model:
                # Use xcb for Pi
                os.environ['QT_QPA_PLATFORM'] = 'xcb'
    except:
        # Assume regular Linux with display
        os.environ['QT_QPA_PLATFORM'] = 'xcb'
elif sys.platform == "darwin":
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'
elif sys.platform.startswith("win"):
    os.environ['QT_QPA_PLATFORM'] = 'windows'

from src.vision.hand_detector import HandDetector, HandLandmarks
from src.vision.gesture_recognizer import (
    GestureRecognizer, GestureType, GestureResult
)


# MediaPipe drawing utilities
try:
    import mediapipe as mp  # type: ignore
    mp_hands = mp.solutions.hands  # type: ignore
    mp_drawing = mp.solutions.drawing_utils  # type: ignore
    mp_drawing_styles = mp.solutions.drawing_styles  # type: ignore
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp_hands = None
    mp_drawing = None
    mp_drawing_styles = None


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
        frame = reachy.media.get_frame()
        if frame is None or frame.size == 0:
            raise RuntimeError("Reachy camera returned empty frame")
        
        print("✓ Reachy camera ready!")
        return reachy
    except Exception as e:
        print(f"✗ Failed to initialize Reachy: {e}")
        return None


def draw_hand_landmarks(
    frame: np.ndarray,
    hand: HandLandmarks,
    color: Tuple[int, int, int] = (0, 255, 0)
) -> None:
    """Draw hand landmarks on frame.
    
    Args:
        frame: BGR image to draw on
        hand: HandLandmarks with landmark positions
        color: BGR color for landmarks
    """
    h, w = frame.shape[:2]
    
    # Draw landmarks as circles
    for x, y, _ in hand.landmarks:
        px, py = int(x * w), int(y * h)
        cv2.circle(frame, (px, py), 4, color, -1)
        cv2.circle(frame, (px, py), 6, (255, 255, 255), 1)
    
    # Draw connections
    if MEDIAPIPE_AVAILABLE and mp_hands:
        connections = mp_hands.HAND_CONNECTIONS
        for connection in connections:
            start_idx, end_idx = connection
            start = hand.landmarks[start_idx]
            end = hand.landmarks[end_idx]
            
            start_px = (int(start[0] * w), int(start[1] * h))
            end_px = (int(end[0] * w), int(end[1] * h))
            
            cv2.line(frame, start_px, end_px, color, 2)


def draw_gesture_overlay(
    frame: np.ndarray,
    gesture: GestureResult,
    hand: HandLandmarks
) -> None:
    """Draw gesture recognition overlay on frame.
    
    Args:
        frame: BGR image to draw on
        gesture: GestureResult with detection info
        hand: HandLandmarks for positioning
    """
    h, w = frame.shape[:2]
    
    # Get wrist position for text placement
    wrist = hand.landmarks[0]
    text_x = int(wrist[0] * w)
    text_y = int(wrist[1] * h) - 40
    
    # Choose color based on gesture type
    if gesture.gesture_type == GestureType.THUMBS_UP:
        color = (0, 255, 0)  # Green
        emoji = "👍"
        gesture_text = "THUMBS UP"
    elif gesture.gesture_type == GestureType.WAVE:
        color = (255, 165, 0)  # Orange
        emoji = "👋"
        gesture_text = "WAVE"
    elif gesture.gesture_type == GestureType.PALM_STOP:
        color = (0, 0, 255)  # Red
        emoji = "✋"
        gesture_text = "PALM STOP"
    else:
        color = (128, 128, 128)  # Gray
        emoji = "?"
        gesture_text = "UNKNOWN"
    
    # Draw gesture indicator
    if gesture.is_confirmed:
        # Confirmed - bright color with larger box
        box_color = color
        text_prefix = f"{emoji} "
        thickness = 3
    else:
        # Not confirmed - dimmer color
        box_color = tuple(c // 2 for c in color)
        text_prefix = f"{emoji} "
        thickness = 2
    
    # Draw background box for text
    text = f"{text_prefix}{gesture_text}"
    (text_w, text_h), baseline = cv2.getTextSize(
        text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, thickness
    )
    
    box_x1 = text_x - 10
    box_y1 = text_y - text_h - 10
    box_x2 = text_x + text_w + 10
    box_y2 = text_y + baseline + 10
    
    # Draw semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), box_color, -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Draw text
    cv2.putText(
        frame, text, (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), thickness
    )
    
    # Draw confidence and hold time if not unknown
    if gesture.gesture_type != GestureType.UNKNOWN:
        info_y = text_y + 30
        
        # Confidence bar
        conf_text = f"Conf: {gesture.confidence:.2f}"
        cv2.putText(
            frame, conf_text, (text_x, info_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        
        # Hold duration (if being held)
        if gesture.hold_duration > 0:
            hold_text = f"Hold: {gesture.hold_duration:.1f}s"
            cv2.putText(
                frame, hold_text, (text_x, info_y + 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
        
        # Distance estimate
        if gesture.distance_estimate is not None:
            dist_text = f"Dist: {gesture.distance_estimate:.1f}m"
            cv2.putText(
                frame, dist_text, (text_x, info_y + 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )


def draw_statistics(
    frame: np.ndarray,
    detector_stats: Dict[str, Any],
    recognizer_stats: Dict[str, Any],
    fps: float
) -> None:
    """Draw performance statistics overlay.
    
    Args:
        frame: BGR image to draw on
        detector_stats: HandDetector statistics
        recognizer_stats: GestureRecognizer statistics
        fps: Current FPS
    """
    h, w = frame.shape[:2]
    
    # Stats background
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (300, 250), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
    
    # Draw statistics text
    y = 35
    line_height = 25
    
    stats_lines = [
        f"FPS: {fps:.1f}",
        f"Detection Rate: {detector_stats.get('detection_rate', 0):.1f}%",
        f"Avg Latency: {detector_stats.get('avg_latency_ms', 0):.1f}ms",
        f"Recognitions: {recognizer_stats.get('recognition_count', 0)}",
        f"Active Hands: {recognizer_stats.get('active_hands', 0)}",
        "",
        "Gesture Counts:",
    ]
    
    for line in stats_lines:
        cv2.putText(
            frame, line, (20, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        y += line_height
    
    # Draw gesture counts
    gesture_counts = recognizer_stats.get('gesture_counts', {})
    for gesture_name, count in gesture_counts.items():
        if gesture_name != 'unknown':
            text = f"  {gesture_name}: {count}"
            cv2.putText(
                frame, text, (20, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
            )
            y += line_height


def main():
    """Main demo loop."""
    parser = argparse.ArgumentParser(description="Gesture Recognition Demo")
    parser.add_argument(
        '--webcam', action='store_true',
        help='Use webcam instead of Reachy camera'
    )
    parser.add_argument(
        '--camera-index', type=int, default=0,
        help='Webcam index (default: 0)'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("👍 Gesture Recognition Demo - Story 3.2")
    print("=" * 70)
    
    # Detect platform and setup camera
    use_reachy = False
    reachy = None
    camera = None
    
    if not args.webcam and is_raspberry_pi():
        print("🔍 Detected Raspberry Pi - using Reachy camera")
        reachy = setup_reachy_camera()
        if reachy:
            use_reachy = True
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
        
        # Show configuration
        stats = recognizer.get_statistics()
        config = stats.get('config', {})
        print(f"Hold time: {config.get('hold_time', 0.5)}s")
        print(f"Smoothing window: {config.get('smoothing_window', 5)} frames")
        print(f"Min confidence: {config.get('min_confidence', 0.6)}")
    except Exception as e:
        print(f"✗ Failed to initialize gesture recognizer: {e}")
        return 1
    
    print("=" * 70)
    print("📹 Starting gesture recognition...")
    print("=" * 70)
    print("👍 Show gestures to the camera:")
    print("   - Thumbs Up: Thumb extended, fingers closed")
    print("   - Wave: Horizontal hand movement")
    print("   - Palm Stop: Hand up, palm facing camera")
    print("\nPress 'q' to quit")
    print("Press 's' to show/hide statistics")
    print("Press 'r' to reset statistics")
    print()
    
    # Create display window
    window_name = "Gesture Recognition Demo"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)
    
    # Performance tracking
    frame_count = 0
    fps = 0.0
    last_fps_time = time.time()
    show_stats = False
    
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
            
            # Detect hands
            start_time = time.time()
            hands = detector.detect(frame)
            
            # Recognize gestures for each hand
            gestures: List[Tuple[HandLandmarks, GestureResult]] = []
            for hand in hands:
                gesture = recognizer.recognize(hand)
                gestures.append((hand, gesture))
            
            detection_time = (time.time() - start_time) * 1000
            
            # Draw results
            display_frame = frame.copy()
            
            for hand, gesture in gestures:
                # Choose color based on handedness
                if hand.handedness == "Right":
                    hand_color = (0, 255, 0)  # Green
                else:
                    hand_color = (0, 0, 255)  # Red
                
                # Draw hand landmarks
                draw_hand_landmarks(display_frame, hand, hand_color)
                
                # Draw gesture overlay
                draw_gesture_overlay(display_frame, gesture, hand)
                
                # Log confirmed gestures
                if gesture.is_confirmed:
                    print(
                        f"✓ {gesture.gesture_type.value.upper()} detected! "
                        f"({gesture.handedness} hand, "
                        f"conf={gesture.confidence:.2f}, "
                        f"dist={gesture.distance_estimate:.1f}m)"
                    )
            
            # Draw hand count
            cv2.putText(
                display_frame, f"Hands: {len(hands)}",
                (10, display_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
            
            # Draw FPS and latency
            cv2.putText(
                display_frame, f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
            cv2.putText(
                display_frame, f"Latency: {detection_time:.1f}ms",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
            
            # Draw statistics if enabled
            if show_stats:
                detector_stats = detector.get_statistics()
                recognizer_stats = recognizer.get_statistics()
                draw_statistics(display_frame, detector_stats, recognizer_stats, fps)
            
            # Display frame
            cv2.imshow(window_name, display_frame)
            
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
            elif key == ord('s'):
                show_stats = not show_stats
                print(f"Statistics: {'ON' if show_stats else 'OFF'}")
            elif key == ord('r'):
                detector.reset_statistics()
                recognizer.reset_statistics()
                print("Statistics reset")
    
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
        
        # Show final statistics
        print("\n" + "=" * 70)
        print("Final Statistics:")
        print("=" * 70)
        
        detector_stats = detector.get_statistics()
        print(f"Detection FPS: {detector_stats.get('fps', 0):.1f}")
        print(f"Frames processed: {detector_stats.get('frame_count', 0)}")
        print(f"Hands detected: {detector_stats.get('detection_count', 0)}")
        print(f"Detection rate: {detector_stats.get('detection_rate', 0):.1f}%")
        print(f"Avg latency: {detector_stats.get('avg_latency_ms', 0):.1f}ms")
        
        recognizer_stats = recognizer.get_statistics()
        print(f"\nRecognitions: {recognizer_stats.get('recognition_count', 0)}")
        print("Gesture counts:")
        for gesture_name, count in recognizer_stats.get('gesture_counts', {}).items():
            print(f"  {gesture_name}: {count}")
        
        print("\n✓ Demo complete")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
