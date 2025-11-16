"""
Hand Detection Demo - Test MediaPipe hand detection with Reachy camera

This demo shows hand detection running on the real robot, displaying:
- Detected hands with landmarks
- Left/right hand differentiation
- Real-time FPS and statistics
- Visual overlay of hand skeleton

Usage:
    On Raspberry Pi with Reachy:
        python hand_detection_demo.py
    
    On Windows with webcam (for testing):
        python hand_detection_demo.py --webcam
"""

import sys
import cv2
import time
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.vision.hand_detector import HandDetector, MEDIAPIPE_AVAILABLE

# Try to import Reachy
try:
    from reachy_mini import ReachyMini
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False

# MediaPipe drawing utilities
try:
    import mediapipe as mp
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_hands = mp.solutions.hands
    DRAWING_AVAILABLE = True
except ImportError:
    DRAWING_AVAILABLE = False


def draw_hand_landmarks(frame, hands_detected):
    """
    Draw hand landmarks and info on frame.
    
    Args:
        frame: Image to draw on
        hands_detected: List of HandLandmarks from detector
    
    Returns:
        Annotated frame
    """
    if not DRAWING_AVAILABLE:
        # Simple text-only display
        for i, hand in enumerate(hands_detected):
            y_pos = 30 + (i * 60)
            cv2.putText(frame, f"Hand {i+1}: {hand.handedness}", 
                       (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Confidence: {hand.confidence:.2%}", 
                       (10, y_pos + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return frame
    
    # Draw detailed landmarks with MediaPipe
    for hand in hands_detected:
        # Convert normalized landmarks to pixel coordinates
        h, w, _ = frame.shape
        landmarks_px = []
        for lm in hand.landmarks:
            x_px = int(lm[0] * w)
            y_px = int(lm[1] * h)
            landmarks_px.append((x_px, y_px))
        
        # Draw hand skeleton
        # Connections between landmarks (MediaPipe hand connections)
        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (5, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (9, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
            (0, 17)  # Palm
        ]
        
        # Choose color based on handedness
        color = (0, 255, 0) if hand.handedness == "Right" else (255, 0, 0)
        
        # Draw connections
        for conn in connections:
            if conn[0] < len(landmarks_px) and conn[1] < len(landmarks_px):
                pt1 = landmarks_px[conn[0]]
                pt2 = landmarks_px[conn[1]]
                cv2.line(frame, pt1, pt2, color, 2)
        
        # Draw landmarks
        for i, (x, y) in enumerate(landmarks_px):
            # Larger circle for wrist and fingertips
            radius = 8 if i in [0, 4, 8, 12, 16, 20] else 4
            cv2.circle(frame, (x, y), radius, color, -1)
            cv2.circle(frame, (x, y), radius + 2, (255, 255, 255), 1)
        
        # Draw label
        wrist_x, wrist_y = landmarks_px[0]
        label = f"{hand.handedness} ({hand.confidence:.0%})"
        cv2.putText(frame, label, (wrist_x - 50, wrist_y - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    return frame


def main():
    """Main demo loop."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hand Detection Demo')
    parser.add_argument('--webcam', action='store_true',
                       help='Use webcam instead of Reachy camera')
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("🤚 Hand Detection Demo - Story 3.1")
    print("="*70)
    
    # Check MediaPipe availability
    if not MEDIAPIPE_AVAILABLE:
        print("\n❌ MediaPipe not installed!")
        print("   Install with: pip install mediapipe")
        return 1
    
    # Initialize camera
    reachy = None
    camera = None
    use_reachy = False
    
    if not args.webcam:
        # Try to detect Raspberry Pi
        try:
            with open('/proc/device-tree/model', 'r') as f:
                if 'Raspberry Pi' in f.read():
                    print("\n🔍 Detected Raspberry Pi - using Reachy camera")
                    use_reachy = True
        except:
            pass
    
    if use_reachy and REACHY_AVAILABLE:
        try:
            print("\nConnecting to Reachy...")
            reachy = ReachyMini()
            test_frame = reachy.media.get_frame()
            
            if test_frame is not None:
                print("✓ Reachy camera ready!")
            else:
                print("❌ Reachy camera not working, falling back to webcam")
                reachy.client.disconnect()
                reachy = None
                use_reachy = False
        except Exception as e:
            print(f"❌ Reachy error: {e}")
            print("   Falling back to webcam")
            if reachy:
                reachy.client.disconnect()
            reachy = None
            use_reachy = False
    
    # Fallback to webcam
    if not use_reachy:
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            print("❌ Could not open webcam")
            return 1
        print("✓ Webcam ready!")
    
    # Initialize hand detector
    try:
        print("\nInitializing hand detector...")
        detector = HandDetector("src/config/hand_detection.yaml")
        print("✓ Hand detector initialized")
        print(f"   Max hands: {detector.max_num_hands}")
        print(f"   Min confidence: {detector.min_detection_confidence}")
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        return 1
    
    print("\n" + "="*70)
    print("📹 Starting hand detection...")
    print("="*70)
    print("\n👋 Show your hands to the camera!")
    print("   Press 'q' to quit")
    print("   Press 's' to show statistics\n")
    
    # Main loop
    try:
        while True:
            # Get frame
            if use_reachy and reachy:
                frame = reachy.media.get_frame()
                if frame is None:
                    time.sleep(0.033)
                    continue
                frame = np.asarray(frame, dtype=np.uint8)
            else:
                ret, frame = camera.read()
                if not ret:
                    continue
            
            # Detect hands
            hands = detector.detect(frame)
            
            # Draw results
            frame = draw_hand_landmarks(frame, hands)
            
            # Draw stats overlay
            stats = detector.get_statistics()
            cv2.rectangle(frame, (10, frame.shape[0] - 100), 
                         (300, frame.shape[0] - 10), (0, 0, 0), -1)
            cv2.rectangle(frame, (10, frame.shape[0] - 100), 
                         (300, frame.shape[0] - 10), (255, 255, 255), 2)
            
            cv2.putText(frame, f"FPS: {stats['fps']:.1f}", 
                       (20, frame.shape[0] - 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Hands: {len(hands)}", 
                       (20, frame.shape[0] - 50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Latency: {stats['avg_latency_ms']:.1f}ms", 
                       (20, frame.shape[0] - 25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Display
            cv2.imshow('Hand Detection Demo', frame)
            
            # Handle keys
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                print("\n" + "="*70)
                print("Statistics:")
                print("="*70)
                for k, v in stats.items():
                    print(f"  {k}: {v}")
                print("="*70 + "\n")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        # Cleanup
        if camera:
            camera.release()
        if reachy:
            reachy.client.disconnect()
        cv2.destroyAllWindows()
        detector.close()
        print("\n✓ Demo complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
