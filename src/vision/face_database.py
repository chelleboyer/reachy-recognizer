"""
Face Database Module - Story 2.2

Manages storage and retrieval of face encodings with person names/IDs.
Supports JSON serialization for persistence across sessions.

Compatible with face_recognition library format for future upgrades.
"""

import json
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any, Union
from datetime import datetime
import logging
import shutil

from .face_encoder import FaceEncoder
from .face_detector import FaceDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceDatabase:
    """
    Manage database of known face encodings.
    
    Stores face encodings with associated person names and metadata.
    Supports loading/saving to JSON files for persistence.
    
    Attributes:
        database: Dictionary mapping person names to face data
        encoder: FaceEncoder instance for generating encodings
        detector: FaceDetector instance for face detection
        encoding_dim: Dimension of face encodings (128)
        version: Database schema version
    """
    
    VERSION = "1.0"
    
    def __init__(self, encoder: Optional[FaceEncoder] = None, detector: Optional[FaceDetector] = None):
        """
        Initialize an empty face database.
        
        Args:
            encoder: FaceEncoder instance (creates new one if None)
            detector: FaceDetector instance (creates new one if None)
        """
        self.database: Dict[str, Dict[str, Any]] = {}
        self.encoder = encoder if encoder is not None else FaceEncoder()
        self.detector = detector if detector is not None else FaceDetector()
        self.encoding_dim = 128
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        
        logger.info(f"FaceDatabase initialized (version {self.VERSION})")
    
    def add_face(
        self, 
        name: str, 
        image: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
        auto_detect: bool = True
    ) -> bool:
        """
        Add a face to the database.
        
        Args:
            name: Person's name/ID
            image: Face image (BGR format) or full frame if auto_detect=True
            metadata: Optional metadata to store with face
            auto_detect: If True, auto-detect face in image; if False, treat image as cropped face
            
        Returns:
            True if face added successfully, False otherwise
            
        Example:
            >>> db = FaceDatabase()
            >>> frame = cv2.imread("michelle.jpg")
            >>> success = db.add_face("Michelle", frame)
            >>> print(f"Added: {success}")
        """
        try:
            # Auto-detect face if requested
            if auto_detect:
                faces = self.detector.detect_faces(image)
                if len(faces) == 0:
                    logger.warning(f"No face detected in image for '{name}'")
                    return False
                elif len(faces) > 1:
                    logger.warning(f"Multiple faces detected for '{name}', using first face")
                
                # Extract first face
                top, right, bottom, left = faces[0]
                face_image = image[top:bottom, left:right]
            else:
                face_image = image
            
            # Generate encoding
            encoding = self.encoder.encode_face(face_image, normalize=True)
            if encoding is None:
                logger.error(f"Failed to generate encoding for '{name}'")
                return False
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata["added_at"] = datetime.now().isoformat()
            metadata["detection_method"] = "auto" if auto_detect else "manual"
            
            # Store in database
            self.database[name] = {
                "encoding": encoding.tolist(),  # Convert to list for JSON serialization
                "metadata": metadata
            }
            
            self.updated_at = datetime.now().isoformat()
            
            logger.info(f"✓ Added face for '{name}' to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add face for '{name}': {e}")
            return False
    
    def remove_face(self, name: str) -> bool:
        """
        Remove a face from the database.
        
        Args:
            name: Person's name/ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self.database:
            del self.database[name]
            self.updated_at = datetime.now().isoformat()
            logger.info(f"✓ Removed '{name}' from database")
            return True
        else:
            logger.warning(f"'{name}' not found in database")
            return False
    
    def get_encoding(self, name: str) -> Optional[np.ndarray]:
        """
        Get face encoding for a specific person.
        
        Args:
            name: Person's name/ID
            
        Returns:
            Face encoding as numpy array, or None if not found
        """
        if name in self.database:
            encoding_list = self.database[name]["encoding"]
            return np.array(encoding_list)
        else:
            return None
    
    def get_all_encodings(self) -> List[Tuple[str, np.ndarray]]:
        """
        Get all face encodings in the database.
        
        Returns:
            List of (name, encoding) tuples
            
        Example:
            >>> db = FaceDatabase()
            >>> db.load_database("faces.json")
            >>> for name, encoding in db.get_all_encodings():
            >>>     print(f"{name}: {encoding.shape}")
        """
        encodings = []
        for name, data in self.database.items():
            encoding = np.array(data["encoding"])
            encodings.append((name, encoding))
        
        return encodings
    
    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific person.
        
        Args:
            name: Person's name/ID
            
        Returns:
            Metadata dictionary, or None if not found
        """
        if name in self.database:
            return self.database[name]["metadata"]
        else:
            return None
    
    def get_all_names(self) -> List[str]:
        """Get list of all person names in database."""
        return list(self.database.keys())
    
    def size(self) -> int:
        """Get number of faces in database."""
        return len(self.database)
    
    def is_empty(self) -> bool:
        """Check if database is empty."""
        return len(self.database) == 0
    
    def save_database(self, filepath: Union[str, Path], create_backup: bool = True) -> bool:
        """
        Save database to JSON file.
        
        Args:
            filepath: Path to save JSON file
            create_backup: If True, backup existing file before overwriting
            
        Returns:
            True if saved successfully, False otherwise
            
        Example:
            >>> db = FaceDatabase()
            >>> db.add_face("Michelle", image)
            >>> db.save_database("faces.json")
        """
        try:
            filepath = Path(filepath)
            
            # Create backup if file exists
            if create_backup and filepath.exists():
                backup_path = filepath.with_suffix(filepath.suffix + ".bak")
                shutil.copy2(filepath, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            # Prepare database export
            export_data = {
                "version": self.VERSION,
                "created_at": self.created_at,
                "updated_at": datetime.now().isoformat(),
                "encoding_dim": self.encoding_dim,
                "model": "SFace_128d",
                "num_faces": len(self.database),
                "faces": self.database
            }
            
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"✓ Saved database to {filepath} ({len(self.database)} faces)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            return False
    
    def load_database(self, filepath: Union[str, Path], merge: bool = False) -> bool:
        """
        Load database from JSON file.
        
        Args:
            filepath: Path to JSON file
            merge: If True, merge with existing database; if False, replace
            
        Returns:
            True if loaded successfully, False otherwise
            
        Example:
            >>> db = FaceDatabase()
            >>> db.load_database("faces.json")
            >>> print(f"Loaded {db.size()} faces")
        """
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                logger.error(f"Database file not found: {filepath}")
                return False
            
            # Load JSON file
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate schema version
            if data.get("version") != self.VERSION:
                logger.warning(f"Database version mismatch: {data.get('version')} vs {self.VERSION}")
            
            # Validate encoding dimension
            if data.get("encoding_dim") != self.encoding_dim:
                logger.error(f"Encoding dimension mismatch: {data.get('encoding_dim')} vs {self.encoding_dim}")
                return False
            
            # Load faces
            loaded_faces = data.get("faces", {})
            
            if merge:
                # Merge with existing database
                self.database.update(loaded_faces)
                logger.info(f"✓ Merged {len(loaded_faces)} faces from {filepath}")
            else:
                # Replace existing database
                self.database = loaded_faces
                self.created_at = data.get("created_at", datetime.now().isoformat())
                logger.info(f"✓ Loaded {len(loaded_faces)} faces from {filepath}")
            
            self.updated_at = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            return False
    
    def clear(self):
        """Clear all faces from database."""
        self.database = {}
        self.updated_at = datetime.now().isoformat()
        logger.info("Database cleared")
    
    def get_info(self) -> Dict[str, Any]:
        """Get database information."""
        return {
            "version": self.VERSION,
            "num_faces": len(self.database),
            "names": list(self.database.keys()),
            "encoding_dim": self.encoding_dim,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


def main():
    """Demo script showing FaceDatabase usage."""
    import cv2
    import sys
    
    print("=" * 60)
    print("FaceDatabase Demo")
    print("=" * 60)
    
    # Initialize database
    db = FaceDatabase()
    print(f"\n✓ FaceDatabase initialized")
    print(f"  Info: {db.get_info()}")
    
    # Open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        sys.exit(1)
    
    print("\n✓ Camera opened")
    print("\nInstructions:")
    print("  - Position your face in front of camera")
    print("  - Press SPACE to add your face (will prompt for name)")
    print("  - Press 's' to save database to faces.json")
    print("  - Press 'l' to load database from faces.json")
    print("  - Press 'i' to show database info")
    print("  - Press ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        faces = db.detector.detect_faces(frame)
        
        # Draw bounding boxes
        display_frame = frame.copy()
        for (top, right, bottom, left) in faces:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)
        
        # Add database info
        cv2.putText(
            display_frame,
            f"Database: {db.size()} faces | {', '.join(db.get_all_names()) if not db.is_empty() else 'Empty'}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2
        )
        
        cv2.putText(
            display_frame,
            "SPACE: Add face | s: Save | l: Load | i: Info | ESC: Exit",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        cv2.imshow("FaceDatabase Demo", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE - Add face
            if len(faces) > 0:
                # Prompt for name
                print("\nEnter person's name: ", end='', flush=True)
                name = input().strip()
                
                if name:
                    success = db.add_face(name, frame, auto_detect=True)
                    if success:
                        print(f"✓ Added '{name}' to database")
                    else:
                        print(f"❌ Failed to add '{name}'")
                else:
                    print("❌ Name cannot be empty")
            else:
                print("\n⚠ No face detected. Move closer to camera.")
        
        elif key == ord('s'):  # Save database
            success = db.save_database("faces.json")
            if success:
                print("\n✓ Database saved to faces.json")
            else:
                print("\n❌ Failed to save database")
        
        elif key == ord('l'):  # Load database
            success = db.load_database("faces.json")
            if success:
                print(f"\n✓ Database loaded from faces.json ({db.size()} faces)")
            else:
                print("\n❌ Failed to load database")
        
        elif key == ord('i'):  # Show info
            print("\n" + "=" * 40)
            print("Database Info:")
            info = db.get_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
            print("=" * 40)
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "=" * 60)
    print(f"✅ Demo complete! Database has {db.size()} faces")
    print("=" * 60)


if __name__ == "__main__":
    main()
