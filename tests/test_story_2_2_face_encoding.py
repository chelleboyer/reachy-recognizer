"""
Unit Tests for Story 2.2: Face Encoding Database

Tests for FaceEncoder and FaceDatabase classes.
Validates all acceptance criteria for Story 2.2.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
import json
import tempfile
import shutil

# Import modules to test
from face_encoder import FaceEncoder
from face_database import FaceDatabase


def test_face_encoder_initialization():
    """Test FaceEncoder initialization (AC: 1)."""
    print("\n[TEST] FaceEncoder initialization...")
    
    encoder = FaceEncoder()
    
    assert encoder is not None, "FaceEncoder should initialize"
    assert encoder.encoding_dim == 128, "Should use 128-d encodings"
    assert encoder.input_size == (112, 112), "Input size should be 112x112"
    assert encoder.net is not None, "Model should be loaded"
    
    print("✓ FaceEncoder initialized correctly")
    return True


def test_face_encoding_generation():
    """Test encoding generation from synthetic face (AC: 1)."""
    print("\n[TEST] Face encoding generation...")
    
    encoder = FaceEncoder()
    
    # Create synthetic face image (112x112x3 BGR)
    test_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    # Generate encoding
    encoding = encoder.encode_face(test_face, normalize=True)
    
    assert encoding is not None, "Encoding should be generated"
    assert encoding.shape == (128,), f"Encoding should be 128-d, got {encoding.shape}"
    assert np.isclose(np.linalg.norm(encoding), 1.0, atol=1e-6), "Encoding should be L2-normalized"
    
    print(f"✓ Generated {encoding.shape[0]}-d encoding")
    print(f"  Sample values: {encoding[:5]}")
    print(f"  L2 norm: {np.linalg.norm(encoding):.6f}")
    
    return True


def test_face_encoding_consistency():
    """Test that same face produces similar encodings (AC: 1)."""
    print("\n[TEST] Encoding consistency...")
    
    encoder = FaceEncoder()
    
    # Create test face
    test_face = np.random.randint(100, 150, (112, 112, 3), dtype=np.uint8)
    
    # Generate two encodings from same face
    encoding1 = encoder.encode_face(test_face, normalize=True)
    encoding2 = encoder.encode_face(test_face, normalize=True)
    
    # Calculate similarity (cosine similarity via dot product of normalized vectors)
    similarity = np.dot(encoding1, encoding2)
    
    assert similarity > 0.99, f"Same face should produce similar encodings (similarity: {similarity:.4f})"
    
    print(f"✓ Encoding consistency verified (similarity: {similarity:.6f})")
    
    return True


def test_face_database_initialization():
    """Test FaceDatabase initialization (AC: 2)."""
    print("\n[TEST] FaceDatabase initialization...")
    
    db = FaceDatabase()
    
    assert db is not None, "FaceDatabase should initialize"
    assert db.is_empty(), "New database should be empty"
    assert db.size() == 0, "Size should be 0"
    assert db.encoding_dim == 128, "Should use 128-d encodings"
    
    info = db.get_info()
    assert info["num_faces"] == 0, "Should have 0 faces"
    assert info["version"] == "1.0", "Version should be 1.0"
    
    print("✓ FaceDatabase initialized correctly")
    print(f"  Info: {info}")
    
    return True


def test_add_face_manual():
    """Test adding face with manual mode (AC: 4)."""
    print("\n[TEST] Adding face (manual mode)...")
    
    db = FaceDatabase()
    
    # Create synthetic face image
    face_image = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    # Add face without auto-detection
    success = db.add_face("TestPerson", face_image, auto_detect=False)
    
    assert success, "add_face should succeed"
    assert db.size() == 1, "Database should have 1 face"
    assert "TestPerson" in db.get_all_names(), "Person should be in database"
    
    # Verify encoding
    encoding = db.get_encoding("TestPerson")
    assert encoding is not None, "Should retrieve encoding"
    assert encoding.shape == (128,), "Encoding should be 128-d"
    
    print("✓ Face added successfully (manual mode)")
    print(f"  Database size: {db.size()}")
    
    return True


def test_add_face_auto_detect():
    """Test adding face with auto-detection (AC: 4)."""
    print("\n[TEST] Adding face (auto-detect mode)...")
    
    db = FaceDatabase()
    
    # Open camera and capture one frame
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠ Skipping test (camera not available)")
        return True
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("⚠ Skipping test (could not read frame)")
        return True
    
    # Try to add face with auto-detection
    success = db.add_face("CameraTest", frame, auto_detect=True)
    
    if success:
        assert db.size() == 1, "Database should have 1 face"
        assert "CameraTest" in db.get_all_names(), "Person should be in database"
        print("✓ Face added successfully (auto-detect mode)")
    else:
        print("⚠ No face detected in frame (expected if no one in front of camera)")
    
    return True


def test_database_save_and_load():
    """Test saving and loading database (AC: 3, 5, 6)."""
    print("\n[TEST] Database save/load...")
    
    # Create temporary database file
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_faces.json"
        
        # Create database with test faces
        db1 = FaceDatabase()
        
        face1 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        face2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        
        db1.add_face("Person1", face1, auto_detect=False, metadata={"source": "test1"})
        db1.add_face("Person2", face2, auto_detect=False, metadata={"source": "test2"})
        
        assert db1.size() == 2, "Should have 2 faces before save"
        
        # Save database
        success = db1.save_database(db_path, create_backup=False)
        assert success, "save_database should succeed"
        assert db_path.exists(), "Database file should exist"
        
        print(f"✓ Database saved to {db_path}")
        
        # Verify JSON format
        with open(db_path, 'r') as f:
            data = json.load(f)
        
        assert data["version"] == "1.0", "Version should be 1.0"
        assert data["num_faces"] == 2, "Should have 2 faces"
        assert "Person1" in data["faces"], "Person1 should be in JSON"
        assert "Person2" in data["faces"], "Person2 should be in JSON"
        
        print(f"✓ JSON format validated ({data['num_faces']} faces)")
        
        # Load database into new instance
        db2 = FaceDatabase()
        success = db2.load_database(db_path)
        
        assert success, "load_database should succeed"
        assert db2.size() == 2, "Should have 2 faces after load"
        assert "Person1" in db2.get_all_names(), "Person1 should be loaded"
        assert "Person2" in db2.get_all_names(), "Person2 should be loaded"
        
        # Verify encodings match
        enc1_original = db1.get_encoding("Person1")
        enc1_loaded = db2.get_encoding("Person1")
        
        assert np.allclose(enc1_original, enc1_loaded), "Encodings should match after load"
        
        print("✓ Database loaded successfully")
        print(f"  Encodings match: {np.allclose(enc1_original, enc1_loaded)}")
    
    return True


def test_get_all_encodings():
    """Test retrieving all encodings (AC: 7)."""
    print("\n[TEST] Get all encodings...")
    
    db = FaceDatabase()
    
    # Empty database
    all_encodings = db.get_all_encodings()
    assert len(all_encodings) == 0, "Empty database should return empty list"
    
    # Add some faces
    face1 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    face2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    face3 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    db.add_face("Alice", face1, auto_detect=False)
    db.add_face("Bob", face2, auto_detect=False)
    db.add_face("Charlie", face3, auto_detect=False)
    
    # Get all encodings
    all_encodings = db.get_all_encodings()
    
    assert len(all_encodings) == 3, "Should have 3 encodings"
    
    names = [name for name, _ in all_encodings]
    assert "Alice" in names, "Alice should be in results"
    assert "Bob" in names, "Bob should be in results"
    assert "Charlie" in names, "Charlie should be in results"
    
    # Verify encoding format
    for name, encoding in all_encodings:
        assert isinstance(name, str), "Name should be string"
        assert isinstance(encoding, np.ndarray), "Encoding should be numpy array"
        assert encoding.shape == (128,), f"Encoding should be 128-d, got {encoding.shape}"
    
    print(f"✓ Retrieved {len(all_encodings)} encodings")
    print(f"  Names: {names}")
    
    return True


def test_database_operations():
    """Test various database operations (AC: 2, 4, 7)."""
    print("\n[TEST] Database operations...")
    
    db = FaceDatabase()
    
    # Add faces
    face1 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    face2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    db.add_face("Person1", face1, auto_detect=False)
    db.add_face("Person2", face2, auto_detect=False)
    
    # Test size
    assert db.size() == 2, "Size should be 2"
    
    # Test get_all_names
    names = db.get_all_names()
    assert len(names) == 2, "Should have 2 names"
    assert "Person1" in names and "Person2" in names, "Both names should be present"
    
    # Test get_encoding
    enc1 = db.get_encoding("Person1")
    assert enc1 is not None, "Should get encoding for Person1"
    assert enc1.shape == (128,), "Encoding should be 128-d"
    
    # Test get_encoding for non-existent person
    enc_none = db.get_encoding("NonExistent")
    assert enc_none is None, "Should return None for non-existent person"
    
    # Test get_metadata
    metadata1 = db.get_metadata("Person1")
    assert metadata1 is not None, "Should get metadata"
    assert "added_at" in metadata1, "Metadata should have added_at"
    
    # Test remove_face
    success = db.remove_face("Person1")
    assert success, "remove_face should succeed"
    assert db.size() == 1, "Size should be 1 after removal"
    assert "Person1" not in db.get_all_names(), "Person1 should be removed"
    
    # Test clear
    db.clear()
    assert db.is_empty(), "Database should be empty after clear"
    assert db.size() == 0, "Size should be 0 after clear"
    
    print("✓ All database operations working correctly")
    
    return True


def test_backup_creation():
    """Test database backup creation (AC: 6)."""
    print("\n[TEST] Database backup...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_faces.json"
        backup_path = db_path.with_suffix(db_path.suffix + ".bak")
        
        # Create and save initial database
        db1 = FaceDatabase()
        face1 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        db1.add_face("Person1", face1, auto_detect=False)
        db1.save_database(db_path, create_backup=False)
        
        assert db_path.exists(), "Database file should exist"
        assert not backup_path.exists(), "Backup should not exist yet"
        
        # Save again with backup enabled
        db2 = FaceDatabase()
        face2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        db2.add_face("Person2", face2, auto_detect=False)
        db2.save_database(db_path, create_backup=True)
        
        assert backup_path.exists(), "Backup should be created"
        
        # Verify backup contains original data
        db_backup = FaceDatabase()
        db_backup.load_database(backup_path)
        
        assert db_backup.size() == 1, "Backup should have 1 face (original)"
        assert "Person1" in db_backup.get_all_names(), "Backup should have Person1"
        
        print("✓ Backup created successfully")
        print(f"  Backup file: {backup_path}")
    
    return True


def test_edge_cases():
    """Test edge cases and error handling (AC: 1-7)."""
    print("\n[TEST] Edge cases...")
    
    db = FaceDatabase()
    encoder = FaceEncoder()
    
    # Test encoding with None image
    encoding = encoder.encode_face(None, normalize=True)
    assert encoding is None, "Should handle None image gracefully"
    
    # Test encoding with empty image
    empty_img = np.array([])
    encoding = encoder.encode_face(empty_img, normalize=True)
    assert encoding is None, "Should handle empty image gracefully"
    
    # Test add_face with empty name
    face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    success = db.add_face("", face, auto_detect=False)
    # Empty names are allowed, just testing it doesn't crash
    
    # Test load_database with non-existent file
    success = db.load_database("nonexistent_file.json")
    assert not success, "Should fail gracefully on missing file"
    
    # Test get_encoding for non-existent person
    encoding = db.get_encoding("NonExistent")
    assert encoding is None, "Should return None for non-existent person"
    
    # Test remove non-existent face
    success = db.remove_face("NonExistent")
    assert not success, "Should return False when removing non-existent face"
    
    print("✓ Edge cases handled correctly")
    
    return True


def run_all_tests():
    """Run all Story 2.2 tests."""
    tests = [
        test_face_encoder_initialization,
        test_face_encoding_generation,
        test_face_encoding_consistency,
        test_face_database_initialization,
        test_add_face_manual,
        test_add_face_auto_detect,
        test_database_save_and_load,
        test_get_all_encodings,
        test_database_operations,
        test_backup_creation,
        test_edge_cases,
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("Story 2.2: Face Encoding Database - Unit Tests")
    print("=" * 60)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                print(f"❌ {test.__name__} returned False")
        except AssertionError as e:
            failed += 1
            print(f"❌ {test.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All acceptance criteria validated!")
        return True
    else:
        print(f"❌ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
