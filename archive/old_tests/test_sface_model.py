"""
Test script to verify SFace model loading and understand its interface.

This script tests:
1. Model file exists and loads successfully
2. Model input/output dimensions
3. Basic encoding generation from a test face image
"""

import cv2
import numpy as np
from pathlib import Path


def test_model_loading():
    """Test if SFace model loads successfully."""
    model_path = Path("models/face_recognition_sface_2021dec.onnx")
    
    print(f"[TEST] Checking model file: {model_path}")
    if not model_path.exists():
        print(f"❌ Model file not found: {model_path}")
        return False
    
    print(f"✓ Model file exists ({model_path.stat().st_size / 1024 / 1024:.1f} MB)")
    
    try:
        # Load model using OpenCV DNN
        net = cv2.dnn.readNetFromONNX(str(model_path))
        print("✓ Model loaded successfully with OpenCV DNN")
        
        # Get layer names to understand model structure
        layer_names = net.getLayerNames()
        print(f"✓ Model has {len(layer_names)} layers")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return False


def test_model_inference():
    """Test model inference with a synthetic face image."""
    model_path = Path("models/face_recognition_sface_2021dec.onnx")
    
    print("\n[TEST] Testing model inference...")
    
    try:
        # Load model
        net = cv2.dnn.readNetFromONNX(str(model_path))
        
        # SFace model expects 112x112 RGB input (based on OpenCV Zoo docs)
        # Create synthetic face image (112x112x3)
        test_image = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        
        # Preprocess: convert to blob (normalize, resize if needed)
        blob = cv2.dnn.blobFromImage(
            test_image,
            scalefactor=1.0/255.0,  # Normalize to [0, 1]
            size=(112, 112),
            mean=(0, 0, 0),
            swapRB=True,  # BGR to RGB
            crop=False
        )
        
        print(f"✓ Input blob shape: {blob.shape}")
        
        # Run inference
        net.setInput(blob)
        encoding = net.forward()
        
        print(f"✓ Output encoding shape: {encoding.shape}")
        print(f"✓ Encoding dimension: {encoding.shape[1]}")
        print(f"✓ Encoding sample (first 5 values): {encoding[0, :5]}")
        
        # Normalize encoding (L2 normalization)
        encoding_norm = encoding / np.linalg.norm(encoding)
        print(f"✓ Normalized encoding sample: {encoding_norm[0, :5]}")
        
        return True
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_face():
    """Test encoding generation with a real face from camera."""
    from face_detector import FaceDetector
    
    print("\n[TEST] Testing with real face from camera...")
    
    try:
        # Initialize face detector
        detector = FaceDetector()
        print("✓ FaceDetector initialized")
        
        # Open camera
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Could not open camera")
            return False
        
        print("✓ Camera opened")
        print("  Press SPACE to capture face for encoding")
        print("  Press ESC to skip this test")
        
        model_path = Path("models/face_recognition_sface_2021dec.onnx")
        net = cv2.dnn.readNetFromONNX(str(model_path))
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect faces
            faces = detector.detect_faces(frame)
            
            # Draw bounding boxes
            display_frame = frame.copy()
            for (top, right, bottom, left) in faces:
                cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(display_frame, "Face detected", (left, top - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Add instructions
            cv2.putText(display_frame, "SPACE: Encode face | ESC: Skip", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow("SFace Model Test", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("  Test skipped by user")
                break
            elif key == 32:  # SPACE
                if len(faces) > 0:
                    # Get first face
                    top, right, bottom, left = faces[0]
                    face_img = frame[top:bottom, left:right]
                    
                    # Resize to 112x112 for SFace
                    face_resized = cv2.resize(face_img, (112, 112))
                    
                    # Generate encoding
                    blob = cv2.dnn.blobFromImage(
                        face_resized,
                        scalefactor=1.0/255.0,
                        size=(112, 112),
                        mean=(0, 0, 0),
                        swapRB=True,
                        crop=False
                    )
                    
                    net.setInput(blob)
                    encoding = net.forward()
                    
                    # Normalize
                    encoding_norm = encoding / np.linalg.norm(encoding)
                    
                    print(f"✓ Generated encoding from real face:")
                    print(f"  - Encoding dimension: {encoding.shape[1]}")
                    print(f"  - Sample values: {encoding_norm[0, :5]}")
                    print(f"  - L2 norm: {np.linalg.norm(encoding_norm):.4f}")
                    
                    break
                else:
                    print("  No face detected. Move closer to camera.")
        
        cap.release()
        cv2.destroyAllWindows()
        
        return True
    except Exception as e:
        print(f"❌ Real face test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("SFace Model Test Script")
    print("=" * 60)
    
    # Test 1: Model loading
    if not test_model_loading():
        print("\n❌ Model loading failed. Exiting.")
        exit(1)
    
    # Test 2: Model inference with synthetic image
    if not test_model_inference():
        print("\n❌ Model inference failed. Exiting.")
        exit(1)
    
    # Test 3: Real face encoding (optional, requires camera)
    try:
        test_with_real_face()
    except KeyboardInterrupt:
        print("\n  Test interrupted by user")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
