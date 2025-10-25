#!/usr/bin/env python3
"""
Face Detection Integration Test - Story 2.1

Tests the FaceDetector class with live camera feed, demonstrating:
- Real-time face detection
- Multiple face handling
- Performance measurement
- Edge case handling
- Bounding box visualization
"""

import cv2
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from face_detector import FaceDetector


class FaceDetectionPipeline:
    """Integration pipeline combining camera capture and face detection."""
    
    def __init__(self, camera_index: int = 0, confidence: float = 0.5):
        """
        Initialize the detection pipeline.
        
        Args:
            camera_index: Camera device index
            confidence: Detection confidence threshold
        """
        self.camera_index = camera_index
        self.detector = FaceDetector(confidence_threshold=confidence)
        self.cap = None
        
        # Statistics
        self.frame_count = 0
        self.total_faces_detected = 0
        self.detection_times = []
        self.start_time = None
    
    def initialize_camera(self):
        """Initialize camera capture."""
        print(f"Initializing camera (device {self.camera_index})...")
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open camera {self.camera_index}")
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Verify
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Camera opened but failed to read frame")
        
        height, width = frame.shape[:2]
        print(f"✓ Camera initialized: {width}x{height}")
    
    def run(self, duration_seconds: int = 60):
        """
        Run the detection pipeline.
        
        Args:
            duration_seconds: How long to run (0 = infinite)
        """
        print("\n" + "="*70)
        print("Face Detection Pipeline Test - Story 2.1")
        print("="*70)
        print(f"Duration: {duration_seconds}s" if duration_seconds > 0 else "Duration: Infinite")
        print("Press 'q' or ESC to quit")
        print("Press 'b' to run performance benchmark")
        print("="*70 + "\n")
        
        try:
            self.initialize_camera()
            
            self.start_time = time.time()
            end_time = self.start_time + duration_seconds if duration_seconds > 0 else float('inf')
            
            cv2.namedWindow('Face Detection Test', cv2.WINDOW_NORMAL)
            
            while time.time() < end_time:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("✗ Failed to read frame")
                    break
                
                # Detect faces
                detect_start = time.time()
                faces = self.detector.detect_faces(frame)
                detection_time = (time.time() - detect_start) * 1000  # ms
                
                # Update statistics
                self.frame_count += 1
                self.total_faces_detected += len(faces)
                self.detection_times.append(detection_time)
                
                # Draw faces
                output = self.detector.draw_faces(
                    frame, 
                    faces, 
                    color=(0, 255, 0), 
                    thickness=2,
                    label=f"FACE"
                )
                
                # Add overlay with statistics
                self.add_overlay(output, faces, detection_time)
                
                # Display
                cv2.imshow('Face Detection Test', output)
                
                # Log significant events
                if len(faces) > 0 and self.frame_count % 30 == 0:  # Log every 30 frames with faces
                    elapsed = time.time() - self.start_time
                    avg_time = sum(self.detection_times[-30:]) / min(30, len(self.detection_times))
                    print(f"[{int(elapsed):3d}s] Detected {len(faces)} face(s) | "
                          f"Avg detection: {avg_time:.1f}ms")
                
                # Handle keypresses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    print("\nUser requested quit")
                    break
                elif key == ord('b'):  # 'b' for benchmark
                    self.run_benchmark(frame)
            
            # Print summary
            self.print_summary()
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.print_summary()
        
        except Exception as e:
            print(f"\n✗ Error: {e}")
            raise
        
        finally:
            self.shutdown()
    
    def add_overlay(self, frame, faces, detection_time):
        """Add informational overlay to frame."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        avg_detection = sum(self.detection_times[-100:]) / min(100, len(self.detection_times)) if self.detection_times else 0
        
        # Status box background
        cv2.rectangle(frame, (5, 5), (635, 130), (0, 0, 0), -1)
        cv2.rectangle(frame, (5, 5), (635, 130), (0, 255, 0), 2)
        
        y_offset = 25
        line_height = 20
        
        # Current detection
        status_color = (0, 255, 0) if len(faces) > 0 else (0, 165, 255)
        cv2.putText(frame, f"Faces Detected: {len(faces)}", (15, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        y_offset += line_height
        cv2.putText(frame, f"Current Detection: {detection_time:.1f}ms", (15, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y_offset += line_height
        cv2.putText(frame, f"Avg Detection (100f): {avg_detection:.1f}ms", (15, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Performance
        perf_color = (0, 255, 0) if avg_detection < 100 else (0, 165, 255)
        y_offset += line_height
        cv2.putText(frame, f"Target (<100ms): {'PASS' if avg_detection < 100 else 'CHECK'}", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, perf_color, 1)
        
        # General stats
        y_offset += line_height
        cv2.putText(frame, f"FPS: {fps:.1f} | Frames: {self.frame_count} | Elapsed: {int(elapsed)}s", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Instructions
        y_offset += line_height + 5
        cv2.putText(frame, "Press 'q'/ESC: Quit | 'b': Benchmark", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    def run_benchmark(self, test_frame):
        """Run performance benchmark."""
        print("\n" + "="*70)
        print("Running Performance Benchmark...")
        print("="*70)
        
        results = self.detector.benchmark(test_frame, iterations=100)
        
        print(f"\nBenchmark Results (100 iterations):")
        print(f"  Average: {results['avg_ms']:.2f}ms")
        print(f"  Min:     {results['min_ms']:.2f}ms")
        print(f"  Max:     {results['max_ms']:.2f}ms")
        print(f"  Std Dev: {results['std_ms']:.2f}ms")
        print(f"  Target (<100ms): {'✓ PASS' if results['meets_target'] else '✗ FAIL'}")
        print("="*70 + "\n")
    
    def print_summary(self):
        """Print session summary."""
        if self.start_time is None or self.frame_count == 0:
            return
        
        elapsed = time.time() - self.start_time
        avg_fps = self.frame_count / elapsed
        avg_detection = sum(self.detection_times) / len(self.detection_times) if self.detection_times else 0
        avg_faces = self.total_faces_detected / self.frame_count
        
        print("\n" + "="*70)
        print("SESSION SUMMARY")
        print("="*70)
        print(f"Duration:           {elapsed:.1f}s")
        print(f"Frames Processed:   {self.frame_count}")
        print(f"Average FPS:        {avg_fps:.1f}")
        print(f"Total Faces:        {self.total_faces_detected}")
        print(f"Avg Faces/Frame:    {avg_faces:.2f}")
        print(f"Avg Detection Time: {avg_detection:.2f}ms")
        print(f"Performance Target: {'✓ PASS (<100ms)' if avg_detection < 100 else '✗ FAIL (>=100ms)'}")
        print("="*70 + "\n")
    
    def shutdown(self):
        """Clean up resources."""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Resources released")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Face Detection Pipeline Test")
    parser.add_argument('--duration', type=int, default=60, 
                       help='Test duration in seconds (0=infinite, default=60)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device index (default=0)')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Detection confidence threshold 0-1 (default=0.5)')
    
    args = parser.parse_args()
    
    pipeline = FaceDetectionPipeline(
        camera_index=args.camera,
        confidence=args.confidence
    )
    
    pipeline.run(duration_seconds=args.duration)


if __name__ == "__main__":
    main()
