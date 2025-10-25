#!/usr/bin/env python3
"""
Face Detection Module - Story 2.1

Implements face detection using OpenCV DNN face detector as an alternative
to face_recognition library (which requires complex Windows build setup).

OpenCV DNN detector provides:
- High accuracy (DNN-based, better than Haar cascade)
- Fast performance (< 100ms per frame on CPU)
- No build dependencies (works with standard opencv-python)
- Compatible bounding box format for future face_recognition integration

Future: Can be upgraded to face_recognition library when build environment permits.
"""

import cv2
import numpy as np
from typing import List, Tuple
import time


class FaceDetector:
    """
    Face detection using OpenCV DNN face detector.
    
    Uses a pre-trained Caffe model for robust face detection.
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        """
        Initialize the DNN face detector.
        
        Args:
            confidence_threshold: Minimum confidence for valid detection (0.0 to 1.0)
        """
        self.confidence_threshold = confidence_threshold
        self.net = None
        self.model_loaded = False
        self.load_model()
    
    def load_model(self):
        """Load the pre-trained DNN face detection model."""
        try:
            # OpenCV provides pre-trained face detection models
            # Using Caffe-based SSD (Single Shot Detector) model
            modelFile = cv2.data.haarcascades.replace("haarcascades", "")
            
            # Try to load from opencv-python package data
            # Note: For production, download models explicitly:
            # https://github.com/opencv/opencv/tree/master/samples/dnn/face_detector
            
            # For now, we'll use a simpler approach with the available Haar cascade
            # and document the upgrade path to DNN in the future
            
            # Alternative: Use pre-trained DNN model if available
            prototxt = "models/deploy.prototxt"
            caffemodel = "models/res10_300x300_ssd_iter_140000.caffemodel"
            
            try:
                self.net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
                self.model_loaded = True
                print(f"✓ Loaded DNN face detector (Caffe SSD model)")
            except:
                # Fallback: Use Haar cascade if DNN models not available
                print("⚠ DNN models not found, using Haar cascade fallback")
                self.cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                )
                self.model_loaded = False
                print(f"✓ Loaded Haar cascade face detector (fallback)")
                
        except Exception as e:
            raise RuntimeError(f"Failed to load face detection model: {e}")
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in the frame.
        
        Args:
            frame: BGR image from camera (numpy array)
            
        Returns:
            List of face bounding boxes as (top, right, bottom, left) tuples
            matching face_recognition library format for future compatibility
        """
        if frame is None or frame.size == 0:
            return []
        
        h, w = frame.shape[:2]
        
        if self.model_loaded and self.net is not None:
            # DNN-based detection
            return self._detect_dnn(frame, w, h)
        else:
            # Haar cascade fallback
            return self._detect_haar(frame, w, h)
    
    def _detect_dnn(self, frame: np.ndarray, w: int, h: int) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using DNN model.
        
        Args:
            frame: Input frame
            w: Frame width
            h: Frame height
            
        Returns:
            List of (top, right, bottom, left) tuples
        """
        # Prepare blob from frame
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        # Run detection
        self.net.setInput(blob)
        detections = self.net.forward()
        
        faces = []
        
        # Process detections
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                # Get bounding box coordinates
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                
                # Convert to (top, right, bottom, left) format
                # to match face_recognition library
                faces.append((startY, endX, endY, startX))
        
        return faces
    
    def _detect_haar(self, frame: np.ndarray, w: int, h: int) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces using Haar cascade (fallback).
        
        Args:
            frame: Input frame
            w: Frame width
            h: Frame height
            
        Returns:
            List of (top, right, bottom, left) tuples
        """
        # Convert to grayscale for Haar cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        detected = self.cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        faces = []
        
        # Convert from (x, y, w, h) to (top, right, bottom, left)
        for (x, y, w, h) in detected:
            top = y
            right = x + w
            bottom = y + h
            left = x
            faces.append((top, right, bottom, left))
        
        return faces
    
    def draw_faces(self, frame: np.ndarray, faces: List[Tuple[int, int, int, int]], 
                   color: Tuple[int, int, int] = (0, 255, 0), 
                   thickness: int = 2,
                   label: str = "FACE") -> np.ndarray:
        """
        Draw bounding boxes on detected faces.
        
        Args:
            frame: Image to draw on
            faces: List of (top, right, bottom, left) tuples
            color: BGR color for bounding box
            thickness: Line thickness
            label: Text label to display
            
        Returns:
            Frame with drawn boxes
        """
        output = frame.copy()
        
        for (top, right, bottom, left) in faces:
            # Draw rectangle
            cv2.rectangle(output, (left, top), (right, bottom), color, thickness)
            
            # Draw label
            cv2.putText(
                output, 
                label, 
                (left, top - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                thickness
            )
        
        return output
    
    def benchmark(self, frame: np.ndarray, iterations: int = 100) -> dict:
        """
        Benchmark detection performance.
        
        Args:
            frame: Test frame
            iterations: Number of iterations to run
            
        Returns:
            Dictionary with performance metrics
        """
        times = []
        
        for _ in range(iterations):
            start = time.time()
            faces = self.detect_faces(frame)
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)
        
        return {
            'avg_ms': np.mean(times),
            'min_ms': np.min(times),
            'max_ms': np.max(times),
            'std_ms': np.std(times),
            'meets_target': np.mean(times) < 100.0
        }


def main():
    """Test the face detector with webcam."""
    print("\n" + "="*70)
    print("Face Detector Test - Story 2.1")
    print("="*70)
    
    # Initialize detector
    detector = FaceDetector(confidence_threshold=0.5)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Failed to open camera")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print("✓ Camera opened")
    print("\nPress 'q' or ESC to quit\n")
    
    frame_count = 0
    total_time = 0
    
    cv2.namedWindow('Face Detection Test', cv2.WINDOW_NORMAL)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces
            start = time.time()
            faces = detector.detect_faces(frame)
            detection_time = (time.time() - start) * 1000  # ms
            
            # Draw faces
            output = detector.draw_faces(frame, faces)
            
            # Add performance overlay
            fps = frame_count / total_time if total_time > 0 else 0
            cv2.putText(
                output,
                f"Faces: {len(faces)}  |  Detection: {detection_time:.1f}ms  |  FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )
            
            # Display
            cv2.imshow('Face Detection Test', output)
            
            # Update stats
            frame_count += 1
            total_time += time.time() - start
            
            # Check for quit
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Print summary
        avg_detection_time = (total_time / frame_count * 1000) if frame_count > 0 else 0
        print(f"\nProcessed {frame_count} frames")
        print(f"Average detection time: {avg_detection_time:.1f}ms")
        print(f"Target met (< 100ms): {'✓' if avg_detection_time < 100 else '✗'}")


if __name__ == "__main__":
    main()
