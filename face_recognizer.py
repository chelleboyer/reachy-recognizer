"""
Face Recognition Engine - Story 2.3

Identifies people by comparing face encodings with database using cosine similarity.
Returns person name and confidence score for recognized faces.
"""

import numpy as np
from typing import Optional, List, Tuple
import logging
import time

from face_database import FaceDatabase
from face_detector import FaceDetector
from face_encoder import FaceEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceRecognizer:
    """
    Recognize faces by comparing encodings with database.
    
    Uses cosine similarity to match unknown face encodings against
    known faces in the database. Returns person name and confidence score.
    
    Attributes:
        database: FaceDatabase instance with known face encodings
        threshold: Minimum similarity score for positive match (default 0.6)
        detector: FaceDetector instance for face detection
        encoder: FaceEncoder instance for encoding generation
    """
    
    DEFAULT_THRESHOLD = 0.6
    
    def __init__(
        self,
        database: FaceDatabase,
        threshold: float = DEFAULT_THRESHOLD,
        detector: Optional[FaceDetector] = None,
        encoder: Optional[FaceEncoder] = None
    ):
        """
        Initialize face recognizer.
        
        Args:
            database: FaceDatabase with known face encodings
            threshold: Similarity threshold for recognition (0.0-1.0)
            detector: FaceDetector instance (creates new if None)
            encoder: FaceEncoder instance (creates new if None)
            
        Raises:
            ValueError: If threshold not in valid range
        """
        self.database = database
        self.set_threshold(threshold)
        self.detector = detector if detector is not None else FaceDetector()
        self.encoder = encoder if encoder is not None else FaceEncoder()
        
        logger.info(f"FaceRecognizer initialized (threshold={self.threshold:.2f}, database={database.size()} faces)")
    
    def set_threshold(self, threshold: float):
        """
        Set recognition threshold.
        
        Args:
            threshold: Similarity threshold (0.0-1.0)
            
        Raises:
            ValueError: If threshold not in valid range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be between 0.0 and 1.0, got {threshold}")
        self.threshold = threshold
    
    def get_threshold(self) -> float:
        """Get current recognition threshold."""
        return self.threshold
    
    def recognize_face(self, encoding: np.ndarray) -> Tuple[str, float]:
        """
        Recognize a single face encoding.
        
        Args:
            encoding: Face encoding to recognize (128-d numpy array)
            
        Returns:
            Tuple of (name, confidence):
                - name: Person's name or "unknown"
                - confidence: Similarity score (0.0-1.0)
                
        Example:
            >>> recognizer = FaceRecognizer(database)
            >>> name, confidence = recognizer.recognize_face(unknown_encoding)
            >>> if name != "unknown":
            >>>     print(f"Recognized {name} with {confidence:.2f} confidence")
        """
        # Handle empty database
        if self.database.is_empty():
            return ("unknown", 0.0)
        
        # Get all known encodings
        all_encodings = self.database.get_all_encodings()
        
        best_match_name = "unknown"
        best_match_score = 0.0
        
        # Compare with each known face
        for name, known_encoding in all_encodings:
            # Calculate cosine similarity
            # Since encodings are L2-normalized, cosine similarity = dot product
            similarity = np.dot(encoding, known_encoding)
            
            # Track best match
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_name = name
        
        # Check if best match exceeds threshold
        if best_match_score >= self.threshold:
            return (best_match_name, float(best_match_score))
        else:
            return ("unknown", float(best_match_score))
    
    def recognize_faces(self, encodings: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Recognize multiple face encodings.
        
        Args:
            encodings: List of face encodings to recognize
            
        Returns:
            List of (name, confidence) tuples, same order as input
            
        Example:
            >>> recognizer = FaceRecognizer(database)
            >>> results = recognizer.recognize_faces([enc1, enc2, enc3])
            >>> for name, conf in results:
            >>>     print(f"{name}: {conf:.2f}")
        """
        results = []
        for encoding in encodings:
            result = self.recognize_face(encoding)
            results.append(result)
        
        return results
    
    def recognize_faces_vectorized(self, encodings: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Recognize multiple faces using vectorized operations (faster).
        
        Args:
            encodings: List of face encodings to recognize
            
        Returns:
            List of (name, confidence) tuples, same order as input
        """
        if len(encodings) == 0:
            return []
        
        if self.database.is_empty():
            return [("unknown", 0.0) for _ in encodings]
        
        # Stack encodings into matrix
        unknown_matrix = np.array(encodings)  # Shape: (n_unknown, 128)
        
        # Get all known encodings
        all_encodings = self.database.get_all_encodings()
        names = [name for name, _ in all_encodings]
        known_encodings = [enc for _, enc in all_encodings]
        known_matrix = np.array(known_encodings)  # Shape: (n_known, 128)
        
        # Compute all similarities at once: (n_unknown, n_known)
        similarities = np.dot(unknown_matrix, known_matrix.T)
        
        # Find best match for each unknown face
        results = []
        for i in range(len(encodings)):
            best_idx = np.argmax(similarities[i])
            best_score = similarities[i, best_idx]
            
            if best_score >= self.threshold:
                results.append((names[best_idx], float(best_score)))
            else:
                results.append(("unknown", float(best_score)))
        
        return results
    
    def recognize_from_frame(
        self, 
        frame: np.ndarray,
        use_vectorized: bool = True
    ) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
        """
        Full pipeline: detect → encode → recognize faces in a frame.
        
        Args:
            frame: Camera frame (BGR format)
            use_vectorized: Use vectorized recognition for better performance
            
        Returns:
            List of (name, confidence, bbox) tuples:
                - name: Person's name or "unknown"
                - confidence: Similarity score (0.0-1.0)
                - bbox: Face bounding box as (top, right, bottom, left)
                
        Example:
            >>> recognizer = FaceRecognizer(database)
            >>> frame = cv2.VideoCapture(0).read()[1]
            >>> results = recognizer.recognize_from_frame(frame)
            >>> for name, conf, (top, right, bottom, left) in results:
            >>>     print(f"{name} at ({left}, {top}): {conf:.2f}")
        """
        # Detect faces
        face_locations = self.detector.detect_faces(frame)
        
        if len(face_locations) == 0:
            return []
        
        # Encode all detected faces
        encodings = []
        for location in face_locations:
            encoding = self.encoder.encode_face_from_frame(frame, location)
            if encoding is not None:
                encodings.append(encoding)
            else:
                # If encoding fails, use zero vector (will be recognized as unknown)
                encodings.append(np.zeros(128))
        
        # Recognize faces
        if use_vectorized and len(encodings) > 1:
            recognitions = self.recognize_faces_vectorized(encodings)
        else:
            recognitions = self.recognize_faces(encodings)
        
        # Combine results with bounding boxes
        results = []
        for (name, confidence), bbox in zip(recognitions, face_locations):
            results.append((name, confidence, bbox))
        
        return results
    
    def benchmark_recognition(self, num_faces: int = 100) -> dict:
        """
        Benchmark recognition performance.
        
        Args:
            num_faces: Number of random faces to test
            
        Returns:
            Dictionary with performance metrics
        """
        logger.info(f"Benchmarking recognition with {num_faces} random faces...")
        
        # Generate random encodings
        random_encodings = [
            np.random.randn(128).astype(np.float32) 
            for _ in range(num_faces)
        ]
        
        # Normalize encodings
        for i in range(len(random_encodings)):
            random_encodings[i] = random_encodings[i] / np.linalg.norm(random_encodings[i])
        
        # Benchmark individual recognition
        start = time.time()
        for encoding in random_encodings:
            self.recognize_face(encoding)
        individual_time = (time.time() - start) * 1000  # Convert to ms
        
        # Benchmark vectorized recognition
        start = time.time()
        self.recognize_faces_vectorized(random_encodings)
        vectorized_time = (time.time() - start) * 1000  # Convert to ms
        
        results = {
            "num_faces": num_faces,
            "database_size": self.database.size(),
            "individual_total_ms": individual_time,
            "individual_avg_ms": individual_time / num_faces,
            "vectorized_total_ms": vectorized_time,
            "vectorized_avg_ms": vectorized_time / num_faces,
            "speedup": individual_time / vectorized_time if vectorized_time > 0.001 else float('inf')
        }
        
        logger.info(f"Individual: {results['individual_avg_ms']:.2f}ms per face")
        logger.info(f"Vectorized: {results['vectorized_avg_ms']:.2f}ms per face")
        logger.info(f"Speedup: {results['speedup']:.2f}x")
        
        return results
    
    def get_stats(self) -> dict:
        """Get recognizer statistics."""
        return {
            "threshold": self.threshold,
            "database_size": self.database.size(),
            "known_people": self.database.get_all_names()
        }


def main():
    """Demo script showing FaceRecognizer usage."""
    import cv2
    import sys
    
    print("=" * 60)
    print("FaceRecognizer Demo")
    print("=" * 60)
    
    # Initialize database
    db = FaceDatabase()
    print(f"\n✓ FaceDatabase initialized ({db.size()} faces)")
    
    # Try to load existing database
    if db.load_database("faces.json"):
        print(f"✓ Loaded database: {db.size()} faces")
        print(f"  Known people: {', '.join(db.get_all_names())}")
    else:
        print("⚠ No existing database found. Add faces first using face_database.py demo")
        print("  Or press 'a' during demo to add faces")
    
    # Initialize recognizer
    recognizer = FaceRecognizer(db, threshold=0.6)
    print(f"✓ FaceRecognizer initialized (threshold={recognizer.get_threshold():.2f})")
    
    # Benchmark if database not empty
    if not db.is_empty():
        print("\n[Benchmark]")
        recognizer.benchmark_recognition(num_faces=50)
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        sys.exit(1)
    
    print("\n✓ Camera opened")
    print("\nInstructions:")
    print("  - Press SPACE to recognize faces in current frame")
    print("  - Press 't' to adjust threshold (+0.1)")
    print("  - Press 'r' to adjust threshold (-0.1)")
    print("  - Press 'a' to add current face to database")
    print("  - Press ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces for visualization
        faces = recognizer.detector.detect_faces(frame)
        
        # Draw bounding boxes
        display_frame = frame.copy()
        for (top, right, bottom, left) in faces:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(
                display_frame,
                "Press SPACE to recognize",
                (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        # Add UI info
        cv2.putText(
            display_frame,
            f"Database: {db.size()} faces | Threshold: {recognizer.get_threshold():.2f}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )
        
        cv2.putText(
            display_frame,
            "SPACE: Recognize | t/r: Threshold | a: Add face | ESC: Exit",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        cv2.imshow("FaceRecognizer Demo", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE - Recognize
            results = recognizer.recognize_from_frame(frame)
            if results:
                print(f"\n[Recognition Results]")
                for name, confidence, (top, right, bottom, left) in results:
                    status = "✓" if name != "unknown" else "?"
                    print(f"  {status} {name}: {confidence:.4f} at ({left}, {top})")
            else:
                print("\n⚠ No faces detected")
        
        elif key == ord('t'):  # Increase threshold
            new_threshold = min(1.0, recognizer.get_threshold() + 0.1)
            recognizer.set_threshold(new_threshold)
            print(f"\n→ Threshold: {recognizer.get_threshold():.2f}")
        
        elif key == ord('r'):  # Decrease threshold
            new_threshold = max(0.0, recognizer.get_threshold() - 0.1)
            recognizer.set_threshold(new_threshold)
            print(f"\n→ Threshold: {recognizer.get_threshold():.2f}")
        
        elif key == ord('a'):  # Add face
            if len(faces) > 0:
                print("\nEnter person's name: ", end='', flush=True)
                name = input().strip()
                if name:
                    success = db.add_face(name, frame, auto_detect=True)
                    if success:
                        db.save_database("faces.json")
                        print(f"✓ Added '{name}' to database and saved")
                    else:
                        print(f"❌ Failed to add '{name}'")
            else:
                print("\n⚠ No face detected")
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    print(f"✅ Demo complete! Database has {db.size()} faces")
    print("=" * 60)


if __name__ == "__main__":
    main()
