"""
Face Encoder Module - Story 2.2

Generates face encodings (embeddings) from face images using OpenCV DNN.
Uses SFace model from OpenCV Zoo for 128-dimensional face embeddings.

Compatible with face_recognition library format for future upgrades.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceEncoder:
    """
    Generate face encodings using OpenCV DNN with SFace model.
    
    The SFace model produces 128-dimensional face embeddings compatible
    with the face_recognition library format.
    
    Attributes:
        model_path: Path to the ONNX model file
        net: OpenCV DNN network
        encoding_dim: Dimension of output embeddings (128)
        input_size: Required input image size (112x112)
    """
    
    def __init__(self, model_path: str = "models/face_recognition_sface_2021dec.onnx"):
        """
        Initialize the face encoder with SFace model.
        
        Args:
            model_path: Path to the SFace ONNX model file
            
        Raises:
            FileNotFoundError: If model file doesn't exist
            Exception: If model fails to load
        """
        self.model_path = Path(model_path)
        self.encoding_dim = 128
        self.input_size = (112, 112)
        
        # Load model
        self._load_model()
        
        logger.info(f"FaceEncoder initialized with SFace model ({self.encoding_dim}-d)")
    
    def _load_model(self):
        """Load the SFace ONNX model."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {self.model_path}\n"
                f"Please download from: https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface"
            )
        
        try:
            self.net = cv2.dnn.readNetFromONNX(str(self.model_path))
            logger.info(f"✓ Loaded SFace model from {self.model_path}")
        except Exception as e:
            raise Exception(f"Failed to load SFace model: {e}")
    
    def encode_face(self, face_image: np.ndarray, normalize: bool = True) -> Optional[np.ndarray]:
        """
        Generate face encoding from a face image.
        
        Args:
            face_image: Face image (BGR format from OpenCV)
            normalize: Whether to L2-normalize the encoding (recommended for cosine similarity)
            
        Returns:
            Face encoding as 128-d numpy array, or None if encoding fails
            
        Example:
            >>> encoder = FaceEncoder()
            >>> face_img = cv2.imread("face.jpg")
            >>> encoding = encoder.encode_face(face_img)
            >>> print(encoding.shape)  # (128,)
        """
        if face_image is None or face_image.size == 0:
            logger.warning("Cannot encode empty or None image")
            return None
        
        try:
            # Preprocess: resize to 112x112
            face_resized = cv2.resize(face_image, self.input_size)
            
            # Convert to blob (normalize to [0, 1], BGR to RGB)
            blob = cv2.dnn.blobFromImage(
                face_resized,
                scalefactor=1.0 / 255.0,
                size=self.input_size,
                mean=(0, 0, 0),
                swapRB=True,  # BGR to RGB
                crop=False
            )
            
            # Run inference
            self.net.setInput(blob)
            encoding = self.net.forward()
            
            # Flatten to 1D array
            encoding = encoding.flatten()
            
            # L2 normalization for cosine similarity
            if normalize:
                norm = np.linalg.norm(encoding)
                if norm > 0:
                    encoding = encoding / norm
            
            return encoding
            
        except Exception as e:
            logger.error(f"Failed to encode face: {e}")
            return None
    
    def encode_face_from_frame(
        self, 
        frame: np.ndarray, 
        face_location: Tuple[int, int, int, int],
        normalize: bool = True
    ) -> Optional[np.ndarray]:
        """
        Generate face encoding from a specific face location in a frame.
        
        Args:
            frame: Full camera frame (BGR format)
            face_location: Face bounding box as (top, right, bottom, left)
            normalize: Whether to L2-normalize the encoding
            
        Returns:
            Face encoding as 128-d numpy array, or None if encoding fails
            
        Example:
            >>> encoder = FaceEncoder()
            >>> from face_detector import FaceDetector
            >>> detector = FaceDetector()
            >>> frame = cv2.VideoCapture(0).read()[1]
            >>> faces = detector.detect_faces(frame)
            >>> if faces:
            >>>     encoding = encoder.encode_face_from_frame(frame, faces[0])
        """
        if frame is None or frame.size == 0:
            logger.warning("Cannot encode from empty or None frame")
            return None
        
        try:
            # Extract face region
            top, right, bottom, left = face_location
            
            # Validate bounds
            height, width = frame.shape[:2]
            top = max(0, top)
            left = max(0, left)
            bottom = min(height, bottom)
            right = min(width, right)
            
            if bottom <= top or right <= left:
                logger.warning(f"Invalid face location: {face_location}")
                return None
            
            # Crop face
            face_image = frame[top:bottom, left:right]
            
            # Encode the cropped face
            return self.encode_face(face_image, normalize=normalize)
            
        except Exception as e:
            logger.error(f"Failed to encode face from frame: {e}")
            return None
    
    def batch_encode_faces(
        self, 
        face_images: list[np.ndarray],
        normalize: bool = True
    ) -> list[Optional[np.ndarray]]:
        """
        Encode multiple face images in batch.
        
        Args:
            face_images: List of face images
            normalize: Whether to L2-normalize encodings
            
        Returns:
            List of face encodings (None for failed encodings)
        """
        encodings = []
        for face_image in face_images:
            encoding = self.encode_face(face_image, normalize=normalize)
            encodings.append(encoding)
        
        return encodings
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_path": str(self.model_path),
            "model_name": "SFace",
            "encoding_dimension": self.encoding_dim,
            "input_size": self.input_size,
            "model_size_mb": self.model_path.stat().st_size / 1024 / 1024 if self.model_path.exists() else 0
        }


def main():
    """Demo script showing FaceEncoder usage."""
    import sys
    from face_detector import FaceDetector
    
    print("=" * 60)
    print("FaceEncoder Demo")
    print("=" * 60)
    
    # Initialize encoder
    try:
        encoder = FaceEncoder()
        print("\n✓ FaceEncoder initialized")
        print(f"  Model info: {encoder.get_model_info()}")
    except Exception as e:
        print(f"\n❌ Failed to initialize FaceEncoder: {e}")
        sys.exit(1)
    
    # Initialize detector
    detector = FaceDetector()
    print("✓ FaceDetector initialized")
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        sys.exit(1)
    
    print("\n✓ Camera opened")
    print("\nInstructions:")
    print("  - Position your face in front of camera")
    print("  - Press SPACE to encode your face")
    print("  - Press ESC to exit")
    
    encodings_captured = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        faces = detector.detect_faces(frame)
        
        # Draw bounding boxes
        display_frame = frame.copy()
        for i, (top, right, bottom, left) in enumerate(faces):
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(
                display_frame, 
                f"Face {i+1}", 
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                (0, 255, 0), 
                2
            )
        
        # Add instructions
        cv2.putText(
            display_frame, 
            f"Encodings captured: {len(encodings_captured)} | SPACE: Encode | ESC: Exit", 
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (255, 255, 255), 
            2
        )
        
        cv2.imshow("FaceEncoder Demo", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            if len(faces) > 0:
                # Encode first detected face
                encoding = encoder.encode_face_from_frame(frame, faces[0])
                if encoding is not None:
                    encodings_captured.append(encoding)
                    print(f"\n✓ Encoded face #{len(encodings_captured)}:")
                    print(f"  - Encoding shape: {encoding.shape}")
                    print(f"  - Sample values: {encoding[:5]}")
                    print(f"  - L2 norm: {np.linalg.norm(encoding):.4f}")
                    
                    # Compare with previous encodings
                    if len(encodings_captured) > 1:
                        similarity = np.dot(encodings_captured[-1], encodings_captured[-2])
                        print(f"  - Similarity to previous: {similarity:.4f}")
                else:
                    print("\n❌ Failed to encode face")
            else:
                print("\n⚠ No face detected. Move closer to camera.")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    print(f"✅ Demo complete! Captured {len(encodings_captured)} face encodings")
    print("=" * 60)


if __name__ == "__main__":
    main()
