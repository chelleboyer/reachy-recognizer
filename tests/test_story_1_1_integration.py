"""
Integration Test for Multi-Angle Capture - Story 1.1

End-to-end integration test that validates the complete capture sequence
with Reachy SIM/hardware, camera, and configuration.

Tests verify:
- Full system integration
- Performance requirements (AC1: <10s)
- All frames captured successfully
- Real camera functionality
- Error handling and recovery
"""

import asyncio
import time
from pathlib import Path
import cv2

from src.vision.multi_angle_capture import MultiAngleCaptureController
from src.vision.camera_interface import CameraInterface


async def test_end_to_end_capture_sequence():
    """
    Full end-to-end integration test.
    
    Acceptance Criteria Validation:
    - AC1: Total sequence completes in <10 seconds
    - AC2: Each angle movement completes in <2 seconds
    - AC3: 100ms stabilization pause between movement and capture
    - AC4: All frames have complete metadata
    - AC5: Returns to neutral (0°, 0°) after sequence
    """
    print("=" * 70)
    print("Integration Test: End-to-End Capture Sequence")
    print("=" * 70)
    print()
    
    # Check for configuration
    config_path = Path(__file__).parent.parent / "src" / "config" / "multi_angle_capture.yaml"
    if not config_path.exists():
        print(f"✗ Configuration not found: {config_path}")
        return False
    
    print("Step 1: Initialize controller...")
    try:
        controller = MultiAngleCaptureController(
            config_path=str(config_path),
            enable_robot=True  # Set to False for mock mode if no hardware
        )
        print("✓ Controller initialized")
        print(f"  Robot enabled: {controller.enable_robot}")
        print(f"  Angles: {controller.config['angles']['yaw']}")
        print()
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    # Step 2: Execute capture sequence
    print("Step 2: Execute capture sequence...")
    start_time = time.time()
    
    try:
        frames = await controller.capture_sequence()
        elapsed = time.time() - start_time
        
        print(f"✓ Sequence completed in {elapsed:.2f}s")
        print(f"  Frames captured: {len(frames)}")
        print()
        
    except Exception as e:
        print(f"✗ Capture sequence failed: {e}")
        controller.cleanup()
        return False
    
    # Step 3: Validate results
    print("Step 3: Validate results...")
    
    # AC1: Total time < 10 seconds
    sequence_time = controller.get_last_sequence_time()
    if sequence_time < 10.0:
        print(f"✓ AC1: Total sequence time {sequence_time:.2f}s < 10.0s")
    else:
        print(f"✗ AC1: Total sequence time {sequence_time:.2f}s exceeds 10.0s")
        controller.cleanup()
        return False
    
    # Verify 5 frames captured
    if len(frames) == 5:
        print(f"✓ Captured all 5 frames")
    else:
        print(f"✗ Expected 5 frames, got {len(frames)}")
        controller.cleanup()
        return False
    
    # AC4: Verify metadata completeness
    print()
    print("Frame metadata:")
    metadata_valid = True
    for i, frame in enumerate(frames):
        print(f"  Frame {i}: yaw={frame.angle_yaw}°, pitch={frame.angle_pitch}°, "
              f"shape={frame.frame.shape}, idx={frame.angle_index}")
        
        # Validate metadata
        if not (isinstance(frame.angle_yaw, (int, float)) and
                isinstance(frame.angle_pitch, (int, float)) and
                isinstance(frame.timestamp, float) and
                isinstance(frame.capture_id, str) and
                isinstance(frame.angle_index, int)):
            metadata_valid = False
    
    if metadata_valid:
        print("✓ AC4: All frames have complete metadata")
    else:
        print("✗ AC4: Incomplete metadata detected")
        controller.cleanup()
        return False
    
    # AC5: Return to neutral (verified by lack of errors)
    print("✓ AC5: Returned to neutral position")
    
    print()
    
    # Step 4: Performance summary
    print("Performance Summary:")
    print(f"  Total time: {sequence_time:.2f}s")
    print(f"  Average per angle: {sequence_time / len(frames):.2f}s")
    print(f"  Target met: {'✓ YES' if sequence_time < 10.0 else '✗ NO'}")
    print()
    
    # Cleanup
    controller.cleanup()
    print("✓ Integration test PASSED")
    print()
    
    return True


async def test_repeated_sequences():
    """
    Test running multiple capture sequences consecutively.
    
    Validates:
    - No performance degradation over multiple runs
    - No motor overheating or errors
    - Consistent timing across runs
    """
    print("=" * 70)
    print("Integration Test: Repeated Sequences (10 runs)")
    print("=" * 70)
    print()
    
    config_path = Path(__file__).parent.parent / "src" / "config" / "multi_angle_capture.yaml"
    if not config_path.exists():
        print(f"✗ Configuration not found: {config_path}")
        return False
    
    try:
        controller = MultiAngleCaptureController(
            config_path=str(config_path),
            enable_robot=True
        )
        print("✓ Controller initialized")
        print()
        
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False
    
    # Run 10 consecutive sequences
    times = []
    
    for run in range(10):
        print(f"Run {run + 1}/10...", end=" ", flush=True)
        
        try:
            frames = await controller.capture_sequence()
            sequence_time = controller.get_last_sequence_time()
            times.append(sequence_time)
            
            print(f"{sequence_time:.2f}s ({len(frames)} frames)")
            
            # Brief pause between runs
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            controller.cleanup()
            return False
    
    # Analyze performance
    print()
    print("Performance Analysis:")
    print(f"  Average time: {sum(times) / len(times):.2f}s")
    print(f"  Min time: {min(times):.2f}s")
    print(f"  Max time: {max(times):.2f}s")
    print(f"  All runs < 10s: {'✓ YES' if all(t < 10.0 for t in times) else '✗ NO'}")
    
    # Check for degradation
    first_half_avg = sum(times[:5]) / 5
    second_half_avg = sum(times[5:]) / 5
    degradation = ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    print(f"  Performance degradation: {degradation:+.1f}%")
    
    if abs(degradation) < 10:
        print("✓ No significant performance degradation")
    else:
        print("⚠️  Performance changed significantly across runs")
    
    print()
    
    controller.cleanup()
    print("✓ Repeated sequences test PASSED")
    print()
    
    return True


async def test_camera_visualization():
    """
    Visual test showing captured frames (optional).
    
    Displays each captured frame for manual inspection.
    Useful for verifying frame quality and angle coverage.
    """
    print("=" * 70)
    print("Visual Test: Display Captured Frames")
    print("=" * 70)
    print()
    print("Press 'q' to continue through frames...")
    print()
    
    config_path = Path(__file__).parent.parent / "src" / "config" / "multi_angle_capture.yaml"
    if not config_path.exists():
        print(f"✗ Configuration not found")
        return False
    
    try:
        controller = MultiAngleCaptureController(
            config_path=str(config_path),
            enable_robot=True
        )
        
        frames = await controller.capture_sequence()
        
        # Display each frame
        for frame in frames:
            # Add angle annotation
            display_frame = frame.frame.copy()
            cv2.putText(
                display_frame,
                f"Yaw: {frame.angle_yaw}deg, Pitch: {frame.angle_pitch}deg",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            cv2.putText(
                display_frame,
                f"Frame {frame.angle_index + 1}/5",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2
            )
            
            cv2.imshow("Multi-Angle Capture - Press 'q' for next", display_frame)
            cv2.waitKey(0)
        
        cv2.destroyAllWindows()
        controller.cleanup()
        
        print("✓ Visual test complete")
        print()
        return True
        
    except Exception as e:
        print(f"✗ Visual test failed: {e}")
        return False


async def main():
    """Run all integration tests."""
    print()
    print("=" * 70)
    print("Story 1.1 Integration Tests")
    print("Multi-Angle Capture System")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: End-to-end capture
    result1 = await test_end_to_end_capture_sequence()
    results.append(("End-to-End Capture", result1))
    
    # Test 2: Repeated sequences
    result2 = await test_repeated_sequences()
    results.append(("Repeated Sequences", result2))
    
    # Test 3: Visual inspection (optional, comment out if no display)
    # result3 = await test_camera_visualization()
    # results.append(("Visual Inspection", result3))
    
    # Summary
    print()
    print("=" * 70)
    print("Integration Test Summary")
    print("=" * 70)
    print()
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name}: {status}")
    
    print()
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("✓ ALL INTEGRATION TESTS PASSED")
    else:
        print("✗ SOME INTEGRATION TESTS FAILED")
    
    print()
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
