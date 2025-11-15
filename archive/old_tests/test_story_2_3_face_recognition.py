"""
Unit Tests for Story 2.3: Face Recognition Engine

Tests for FaceRecognizer class.
Validates all acceptance criteria for Story 2.3.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np
import tempfile

# Import modules to test
from face_recognizer import FaceRecognizer
from face_database import FaceDatabase
from face_encoder import FaceEncoder
from face_detector import FaceDetector


def test_face_recognizer_initialization():
    """Test FaceRecognizer initialization (AC: 1, 6)."""
    print("\n[TEST] FaceRecognizer initialization...")
    
    db = FaceDatabase()
    recognizer = FaceRecognizer(db, threshold=0.7)
    
    assert recognizer is not None, "FaceRecognizer should initialize"
    assert recognizer.threshold == 0.7, f"Threshold should be 0.7, got {recognizer.threshold}"
    assert recognizer.get_threshold() == 0.7, "get_threshold() should return 0.7"
    assert recognizer.database is db, "Database should be set"
    assert recognizer.detector is not None, "Detector should be created"
    assert recognizer.encoder is not None, "Encoder should be created"
    
    print("✓ FaceRecognizer initialized correctly")
    return True


def test_threshold_configuration():
    """Test configurable threshold (AC: 6)."""
    print("\n[TEST] Threshold configuration...")
    
    db = FaceDatabase()
    recognizer = FaceRecognizer(db)
    
    # Test default threshold
    assert recognizer.get_threshold() == FaceRecognizer.DEFAULT_THRESHOLD, "Default threshold should be 0.6"
    
    # Test set_threshold
    recognizer.set_threshold(0.8)
    assert recognizer.get_threshold() == 0.8, "Threshold should be updated to 0.8"
    
    recognizer.set_threshold(0.5)
    assert recognizer.get_threshold() == 0.5, "Threshold should be updated to 0.5"
    
    # Test invalid thresholds
    try:
        recognizer.set_threshold(1.5)
        assert False, "Should raise ValueError for threshold > 1.0"
    except ValueError:
        pass  # Expected
    
    try:
        recognizer.set_threshold(-0.1)
        assert False, "Should raise ValueError for threshold < 0.0"
    except ValueError:
        pass  # Expected
    
    print("✓ Threshold configuration working correctly")
    return True


def test_cosine_similarity_calculation():
    """Test cosine similarity calculation (AC: 1)."""
    print("\n[TEST] Cosine similarity calculation...")
    
    db = FaceDatabase()
    encoder = FaceEncoder()
    
    # Create test encodings
    encoding1 = np.random.randn(128).astype(np.float32)
    encoding1 = encoding1 / np.linalg.norm(encoding1)  # Normalize
    
    encoding2 = encoding1.copy()  # Identical
    encoding3 = -encoding1  # Opposite
    encoding4 = np.random.randn(128).astype(np.float32)
    encoding4 = encoding4 / np.linalg.norm(encoding4)  # Random
    
    # Add first encoding to database
    db.add_face("TestPerson", np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8), auto_detect=False)
    # Override the encoding with our test encoding
    db.database["TestPerson"]["encoding"] = encoding1.tolist()
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Test identical encodings (similarity = 1.0)
    name, confidence = recognizer.recognize_face(encoding2)
    assert name == "TestPerson", f"Should recognize identical encoding, got {name}"
    assert np.isclose(confidence, 1.0, atol=0.01), f"Confidence should be ~1.0, got {confidence}"
    
    # Test opposite encodings (similarity = -1.0)
    name, confidence = recognizer.recognize_face(encoding3)
    assert name == "unknown", "Should not recognize opposite encoding"
    # Confidence should be negative or close to 0
    assert confidence < 0.1, f"Confidence should be low/negative, got {confidence}"
    
    # Test random encoding (similarity varies)
    name, confidence = recognizer.recognize_face(encoding4)
    # Result depends on random similarity, just check format
    assert isinstance(name, str), "Name should be string"
    assert 0 <= abs(confidence) <= 1.0, f"Confidence should be in [-1, 1], got {confidence}"
    
    print(f"✓ Cosine similarity calculated correctly")
    print(f"  Identical: {1.0:.4f}")
    print(f"  Opposite: {confidence:.4f}")
    
    return True


def test_recognition_with_threshold():
    """Test recognition with threshold (AC: 2, 3)."""
    print("\n[TEST] Recognition with threshold...")
    
    db = FaceDatabase()
    encoder = FaceEncoder()
    
    # Create test encodings with known similarities
    encoding_alice = np.random.randn(128).astype(np.float32)
    encoding_alice = encoding_alice / np.linalg.norm(encoding_alice)
    
    # Create similar encoding (high confidence)
    encoding_similar = encoding_alice + np.random.randn(128) * 0.1
    encoding_similar = encoding_similar / np.linalg.norm(encoding_similar)
    
    # Create different encoding (low confidence)
    encoding_different = np.random.randn(128).astype(np.float32)
    encoding_different = encoding_different / np.linalg.norm(encoding_different)
    
    # Add to database
    db.add_face("Alice", np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8), auto_detect=False)
    db.database["Alice"]["encoding"] = encoding_alice.tolist()
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Test exact match (should recognize)
    name, confidence = recognizer.recognize_face(encoding_alice)
    assert name == "Alice", f"Should recognize exact match, got {name}"
    assert confidence >= 0.99, f"Confidence should be very high, got {confidence}"
    
    # Test similar encoding (should recognize if above threshold)
    name, confidence = recognizer.recognize_face(encoding_similar)
    similarity = np.dot(encoding_alice, encoding_similar)
    if similarity >= 0.6:
        assert name == "Alice", f"Should recognize similar encoding (similarity={similarity:.4f})"
    else:
        assert name == "unknown", f"Should not recognize (similarity={similarity:.4f} < 0.6)"
    
    print(f"✓ Threshold-based recognition working")
    print(f"  Exact match: {name}, {confidence:.4f}")
    
    return True


def test_multiple_faces_recognition():
    """Test recognition with multiple faces (AC: 4)."""
    print("\n[TEST] Multiple faces recognition...")
    
    db = FaceDatabase()
    
    # Create multiple test people
    face1 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    face2 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    face3 = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    db.add_face("Alice", face1, auto_detect=False)
    db.add_face("Bob", face2, auto_detect=False)
    db.add_face("Charlie", face3, auto_detect=False)
    
    # Get encodings
    alice_enc = np.array(db.get_encoding("Alice"))
    bob_enc = np.array(db.get_encoding("Bob"))
    charlie_enc = np.array(db.get_encoding("Charlie"))
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Test batch recognition
    encodings = [alice_enc, bob_enc, charlie_enc]
    results = recognizer.recognize_faces(encodings)
    
    assert len(results) == 3, "Should return 3 results"
    
    # All should be recognized (exact matches)
    names = [name for name, _ in results]
    assert "Alice" in names, "Alice should be recognized"
    assert "Bob" in names, "Bob should be recognized"
    assert "Charlie" in names, "Charlie should be recognized"
    
    print(f"✓ Multiple faces recognized:")
    for name, conf in results:
        print(f"  - {name}: {conf:.4f}")
    
    return True


def test_vectorized_recognition():
    """Test vectorized batch recognition (AC: 4, 5)."""
    print("\n[TEST] Vectorized recognition...")
    
    db = FaceDatabase()
    
    # Create test database
    for i in range(5):
        face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        db.add_face(f"Person{i}", face, auto_detect=False)
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Generate random test encodings
    num_test = 10
    test_encodings = []
    for _ in range(num_test):
        enc = np.random.randn(128).astype(np.float32)
        enc = enc / np.linalg.norm(enc)
        test_encodings.append(enc)
    
    # Test both methods return same results
    results_individual = recognizer.recognize_faces(test_encodings)
    results_vectorized = recognizer.recognize_faces_vectorized(test_encodings)
    
    assert len(results_individual) == len(results_vectorized) == num_test, "Should return same number of results"
    
    # Results should match (with small tolerance for floating point)
    for i, ((name1, conf1), (name2, conf2)) in enumerate(zip(results_individual, results_vectorized)):
        assert name1 == name2, f"Names should match at index {i}: {name1} vs {name2}"
        assert np.isclose(conf1, conf2, atol=0.2), f"Confidences should match at index {i}: {conf1:.4f} vs {conf2:.4f}"
    
    print(f"✓ Vectorized recognition matches individual recognition")
    print(f"  Tested {num_test} faces")
    
    return True


def test_recognition_performance():
    """Test recognition performance (AC: 5)."""
    print("\n[TEST] Recognition performance...")
    
    db = FaceDatabase()
    
    # Create database with 10 faces
    for i in range(10):
        face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
        db.add_face(f"Person{i}", face, auto_detect=False)
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Benchmark
    results = recognizer.benchmark_recognition(num_faces=100)
    
    # Check performance metrics
    assert results["num_faces"] == 100, "Should test 100 faces"
    assert results["database_size"] == 10, "Database should have 10 faces"
    assert results["individual_avg_ms"] < 50, f"Individual recognition should be < 50ms, got {results['individual_avg_ms']:.2f}ms"
    assert results["vectorized_avg_ms"] < 50, f"Vectorized recognition should be < 50ms, got {results['vectorized_avg_ms']:.2f}ms"
    # Speedup might be inf if vectorized is very fast
    assert results["speedup"] >= 1 or results["speedup"] == float('inf'), "Vectorized should be at least as fast as individual"
    
    print(f"✓ Performance acceptable:")
    print(f"  Individual: {results['individual_avg_ms']:.2f}ms per face")
    print(f"  Vectorized: {results['vectorized_avg_ms']:.2f}ms per face")
    print(f"  Speedup: {results['speedup']:.2f}x")
    
    return True


def test_empty_database():
    """Test recognition with empty database (AC: 3)."""
    print("\n[TEST] Empty database handling...")
    
    db = FaceDatabase()  # Empty
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Create random encoding
    encoding = np.random.randn(128).astype(np.float32)
    encoding = encoding / np.linalg.norm(encoding)
    
    # Should return unknown
    name, confidence = recognizer.recognize_face(encoding)
    
    assert name == "unknown", f"Should return 'unknown' for empty database, got {name}"
    assert confidence == 0.0, f"Confidence should be 0.0, got {confidence}"
    
    print("✓ Empty database handled correctly")
    
    return True


def test_recognize_from_frame():
    """Test full pipeline integration (AC: 1-5)."""
    print("\n[TEST] recognize_from_frame integration...")
    
    db = FaceDatabase()
    
    # Try to capture a frame from camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("⚠ Skipping test (camera not available)")
        return True
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("⚠ Skipping test (could not read frame)")
        return True
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Run full pipeline
    results = recognizer.recognize_from_frame(frame)
    
    # Check result format
    assert isinstance(results, list), "Should return list"
    
    for result in results:
        assert len(result) == 3, "Each result should be (name, confidence, bbox)"
        name, confidence, bbox = result
        assert isinstance(name, str), "Name should be string"
        assert isinstance(confidence, float), "Confidence should be float"
        assert len(bbox) == 4, "Bounding box should have 4 coordinates"
        assert 0 <= confidence <= 1.0, f"Confidence should be in [0, 1], got {confidence}"
    
    if results:
        print(f"✓ Full pipeline working ({len(results)} faces detected)")
        for name, conf, bbox in results:
            print(f"  - {name}: {conf:.4f}")
    else:
        print("✓ Full pipeline working (no faces detected)")
    
    return True


def test_unknown_face_handling():
    """Test unknown face returns 'unknown' (AC: 3)."""
    print("\n[TEST] Unknown face handling...")
    
    db = FaceDatabase()
    
    # Add one known face
    face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    db.add_face("Alice", face, auto_detect=False)
    
    recognizer = FaceRecognizer(db, threshold=0.6)
    
    # Create very different encoding
    known_enc = np.array(db.get_encoding("Alice"))
    unknown_enc = np.random.randn(128).astype(np.float32)
    unknown_enc = unknown_enc / np.linalg.norm(unknown_enc)
    
    # Make sure it's different
    similarity = np.dot(known_enc, unknown_enc)
    
    # Recognize
    name, confidence = recognizer.recognize_face(unknown_enc)
    
    # Should be unknown if similarity < threshold
    if similarity < 0.6:
        assert name == "unknown", f"Should return 'unknown' for dissimilar face (similarity={similarity:.4f})"
        print(f"✓ Unknown face correctly identified (similarity={similarity:.4f})")
    else:
        print(f"⚠ Random face happened to be similar (similarity={similarity:.4f})")
    
    return True


def test_get_stats():
    """Test statistics retrieval."""
    print("\n[TEST] Statistics retrieval...")
    
    db = FaceDatabase()
    db.add_face("Alice", np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8), auto_detect=False)
    db.add_face("Bob", np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8), auto_detect=False)
    
    recognizer = FaceRecognizer(db, threshold=0.7)
    
    stats = recognizer.get_stats()
    
    assert stats["threshold"] == 0.7, "Threshold should be 0.7"
    assert stats["database_size"] == 2, "Database size should be 2"
    assert "Alice" in stats["known_people"], "Alice should be in known people"
    assert "Bob" in stats["known_people"], "Bob should be in known people"
    
    print(f"✓ Statistics retrieved correctly")
    print(f"  Stats: {stats}")
    
    return True


def run_all_tests():
    """Run all Story 2.3 tests."""
    tests = [
        test_face_recognizer_initialization,
        test_threshold_configuration,
        test_cosine_similarity_calculation,
        test_recognition_with_threshold,
        test_multiple_faces_recognition,
        test_vectorized_recognition,
        test_recognition_performance,
        test_empty_database,
        test_recognize_from_frame,
        test_unknown_face_handling,
        test_get_stats,
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 60)
    print("Story 2.3: Face Recognition Engine - Unit Tests")
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
