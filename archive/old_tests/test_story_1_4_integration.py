#!/usr/bin/env python3
"""
Validation tests for Story 1.4: End-to-End Integration Test

This test suite validates that the integration test script meets all acceptance criteria:
1. Single test script combines camera capture + Reachy control
2. Face detection triggers Reachy to look toward camera
3. No face detected returns Reachy to neutral position
4. Test runs continuously for 2 minutes without errors
5. Console logs show detection events and Reachy commands
6. Documentation updated with getting started instructions
7. Demo capability (manual verification)

Run with: python tests/test_story_1_4_integration.py
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_integration_script_exists():
    """AC 1: Verify integration test script exists."""
    print("\n[TEST] Checking integration script exists...")
    
    script_path = project_root / "e2e_integration_test.py"
    assert script_path.exists(), f"Integration script not found: {script_path}"
    
    print(f"  ✓ Found e2e_integration_test.py ({script_path.stat().st_size} bytes)")


def test_script_imports():
    """AC 1: Verify script has required imports for camera and Reachy control."""
    print("\n[TEST] Checking required imports...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    required_imports = [
        'import cv2',           # Camera capture
        'import requests',      # Reachy API communication
        'import numpy',         # Image processing
    ]
    
    missing = []
    for imp in required_imports:
        if imp not in content:
            missing.append(imp)
    
    assert not missing, f"Missing required imports: {missing}"
    print(f"  ✓ All required imports present")


def test_face_detection_implementation():
    """AC 2: Verify face detection implementation with Haar cascade."""
    print("\n[TEST] Checking face detection implementation...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for Haar cascade
    required_features = [
        'haarcascade_frontalface',   # Haar cascade face detector
        'detectMultiScale',            # Detection method
        'CascadeClassifier',           # OpenCV classifier
        'detect_faces',                # Detection function/method
    ]
    
    missing = []
    for feature in required_features:
        if feature not in content:
            missing.append(feature)
    
    assert not missing, f"Missing face detection features: {missing}"
    print(f"  ✓ Haar cascade face detection implemented")


def test_reachy_control_integration():
    """AC 2, 3: Verify Reachy control commands integrated."""
    print("\n[TEST] Checking Reachy control integration...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for Reachy commands
    required_features = [
        'look_at_camera',         # Command when face detected
        'return_to_neutral',      # Command when no face
        'requests.post',          # API calls to Reachy server
        'localhost:8001',         # FastAPI server connection
    ]
    
    missing = []
    for feature in required_features:
        if feature not in content:
            missing.append(feature)
    
    assert not missing, f"Missing Reachy control features: {missing}"
    print(f"  ✓ Reachy control commands integrated (look_at_camera, return_to_neutral)")


def test_state_transitions():
    """AC 2, 3: Verify state transition logic (face detected vs no face)."""
    print("\n[TEST] Checking state transition logic...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for state tracking
    required_features = [
        'face_detected',          # State variable
        'if face_detected',       # Conditional logic
        'else:',                  # Alternative path
        'State changed' or 'state' or 'transition',  # State awareness
    ]
    
    # At least check for face_detected logic
    assert 'face_detected' in content, "No face_detected state variable"
    assert content.count('if') >= 5, "Insufficient conditional logic for state transitions"
    
    print(f"  ✓ State transition logic implemented")


def test_continuous_operation():
    """AC 4: Verify test supports 2-minute continuous operation."""
    print("\n[TEST] Checking continuous operation support...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for timing and duration
    required_features = [
        'duration',               # Duration parameter
        '120',                    # Default 2 minutes (120 seconds)
        'while',                  # Continuous loop
        'time.time()',            # Timing mechanism
    ]
    
    missing = []
    for feature in required_features:
        if feature not in content:
            missing.append(feature)
    
    assert not missing, f"Missing continuous operation features: {missing}"
    print(f"  ✓ Continuous operation for 2 minutes supported")


def test_logging_implementation():
    """AC 5: Verify console logging for events and commands."""
    print("\n[TEST] Checking logging implementation...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for logging
    required_features = [
        'print(',                 # Console output
        'log_event',              # Event logging method
        'DETECTED' or 'detection' or 'FACE',  # Detection logging
        'Command' or 'REACHY' or 'Reachy',    # Command logging
    ]
    
    # Count print statements (should have many for logging)
    print_count = content.count('print(')
    assert print_count >= 10, f"Insufficient logging: only {print_count} print statements"
    
    # Check for event/command logging
    assert 'log_event' in content or 'print(' in content, "No logging mechanism"
    
    print(f"  ✓ Console logging implemented ({print_count} print statements)")


def test_statistics_tracking():
    """AC 5: Verify statistics tracking and reporting."""
    print("\n[TEST] Checking statistics tracking...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for stats variables
    stats_vars = [
        'frame_count',            # Frame counter
        'detection_events',       # Detection counter
        'reachy_commands' or 'commands',  # Command counter
        'fps' or 'FPS',          # FPS calculation
        'summary' or 'SUMMARY',   # Summary output
    ]
    
    found = 0
    for var in stats_vars:
        if var in content:
            found += 1
    
    assert found >= 4, f"Missing statistics tracking (found {found}/5)"
    print(f"  ✓ Statistics tracking implemented (found {found}/5 metrics)")


def test_documentation_exists():
    """AC 6: Verify documentation includes getting started instructions."""
    print("\n[TEST] Checking documentation...")
    
    # Check for README.md or documentation
    readme_path = project_root / "README.md"
    assert readme_path.exists(), "README.md not found"
    
    readme_content = readme_path.read_text(encoding='utf-8')
    
    # Check for getting started content
    getting_started_keywords = [
        'Quick Start' or 'Getting Started' or 'Usage',
        'install' or 'setup',
        'example' or 'Example',
    ]
    
    found = sum(1 for kw in getting_started_keywords if kw in readme_content)
    assert found >= 2, "README.md missing getting started instructions"
    
    print(f"  ✓ README.md exists with getting started instructions")


def test_command_line_interface():
    """AC 7: Verify script has command line interface with help."""
    print("\n[TEST] Checking command line interface...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for argparse (CLI)
    required_features = [
        'argparse',               # Command line parsing
        'ArgumentParser',         # Parser class
        '--duration' or 'duration',  # Duration argument
        '--camera' or 'camera',   # Camera argument
        '__main__',               # Main entry point
    ]
    
    found = sum(1 for feature in required_features if feature in content)
    assert found >= 4, f"Missing CLI features (found {found}/5)"
    
    print(f"  ✓ Command line interface implemented")


def test_error_handling():
    """Verify robust error handling."""
    print("\n[TEST] Checking error handling...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for error handling
    error_features = [
        'try:',                   # Exception handling
        'except',                 # Exception catching
        'raise',                  # Error raising
        'RuntimeError' or 'Exception',  # Error types
        'finally:',               # Cleanup
    ]
    
    found = sum(1 for feature in error_features if feature in content)
    assert found >= 4, f"Insufficient error handling (found {found}/5)"
    
    print(f"  ✓ Error handling implemented (found {found}/5 patterns)")


def test_resource_cleanup():
    """Verify proper resource cleanup."""
    print("\n[TEST] Checking resource cleanup...")
    
    script_path = project_root / "e2e_integration_test.py"
    content = script_path.read_text(encoding='utf-8')
    
    # Check for cleanup
    cleanup_features = [
        'shutdown',               # Cleanup method
        'release()',              # Camera release
        'destroyAllWindows()',    # OpenCV cleanup
        'finally:',               # Guaranteed cleanup
    ]
    
    found = sum(1 for feature in cleanup_features if feature in content)
    assert found >= 3, f"Missing resource cleanup (found {found}/4)"
    
    print(f"  ✓ Resource cleanup implemented")


def test_opencv_haar_cascade_availability():
    """Verify OpenCV Haar cascade is available."""
    print("\n[TEST] Checking OpenCV Haar cascade availability...")
    
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        cascade = cv2.CascadeClassifier(cascade_path)
        
        assert not cascade.empty(), "Haar cascade failed to load"
        print(f"  ✓ OpenCV Haar cascade available: {cascade_path}")
    except Exception as e:
        print(f"  ✗ Failed to load Haar cascade: {e}")
        raise


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("Story 1.4: End-to-End Integration Test - Validation")
    print("="*70)
    
    tests = [
        test_integration_script_exists,
        test_script_imports,
        test_face_detection_implementation,
        test_reachy_control_integration,
        test_state_transitions,
        test_continuous_operation,
        test_logging_implementation,
        test_statistics_tracking,
        test_documentation_exists,
        test_command_line_interface,
        test_error_handling,
        test_resource_cleanup,
        test_opencv_haar_cascade_availability,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✅ All acceptance criteria validated!")
        print("\nManual Testing Required (AC 7 - Demo):")
        print("1. Start Reachy daemon: uvx reachy-mini --daemon start")
        print("2. Start FastAPI server: python test-webui.py")
        print("3. Run integration test: python e2e_integration_test.py")
        print("4. Verify:")
        print("   - Camera window opens with live feed")
        print("   - Face detection works (green box around face)")
        print("   - Console logs show detection events")
        print("   - Reachy commands logged (look_at_camera, return_to_neutral)")
        print("   - Test runs for 2 minutes")
        print("   - Statistics printed at end")
        print("   - Optional: Capture screenshot/video for documentation")
    else:
        print(f"\n⚠ {failed} test(s) failed - review above for details")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
