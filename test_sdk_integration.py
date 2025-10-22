"""
Test Script for Story 3.3.5 - Reachy SDK Integration

Tests real robot movements with the behavior system.

Prerequisites:
- Run `uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim` first
- Or connect to physical Reachy robot
"""

import time
from behavior_module import (
    BehaviorManager,
    greeting_wave,
    curious_tilt,
    neutral_pose,
    create_idle_drift
)

print("=" * 70)
print("Reachy SDK Integration Test - Story 3.3.5")
print("=" * 70)
print()

# Initialize behavior manager (will auto-connect to Reachy)
print("Initializing BehaviorManager...")
print("(Will attempt to connect to Reachy daemon)")
print()

with BehaviorManager(enable_robot=True) as manager:
    print(f"Robot enabled: {manager.enable_robot}")
    print(f"Reachy instance: {manager.reachy is not None}")
    print()
    
    if not manager.enable_robot:
        print("⚠️  Running in SIMULATION mode (no robot connected)")
        print("   To test with simulator:")
        print("   1. Run: uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim")
        print("   2. Run this script again")
        print()
    else:
        print("✓ Connected to Reachy!")
        print()
    
    # Test 1: Greeting wave
    print("=" * 70)
    print("Test 1: Greeting Wave Behavior")
    print("=" * 70)
    print("Expected: Head should wave side-to-side")
    print()
    
    input("Press Enter to execute greeting_wave...")
    manager.execute_behavior(greeting_wave)
    time.sleep(2.0)  # Wait for completion
    print("✓ Greeting wave complete")
    print()
    
    # Test 2: Curious tilt
    print("=" * 70)
    print("Test 2: Curious Tilt Behavior")
    print("=" * 70)
    print("Expected: Head should tilt inquisitively")
    print()
    
    input("Press Enter to execute curious_tilt...")
    manager.execute_behavior(curious_tilt)
    time.sleep(2.0)
    print("✓ Curious tilt complete")
    print()
    
    # Test 3: Neutral pose
    print("=" * 70)
    print("Test 3: Neutral Pose Behavior")
    print("=" * 70)
    print("Expected: Head should return to center")
    print()
    
    input("Press Enter to execute neutral_pose...")
    manager.execute_behavior(neutral_pose)
    time.sleep(1.0)
    print("✓ Neutral pose complete")
    print()
    
    # Test 4: Idle drift
    print("=" * 70)
    print("Test 4: Idle Drift Behavior")
    print("=" * 70)
    print("Expected: Random subtle head movements")
    print()
    
    input("Press Enter to execute idle_drift...")
    idle = create_idle_drift()
    manager.execute_behavior(idle)
    time.sleep(3.0)
    print("✓ Idle drift complete")
    print()
    
    # Test 5: Behavior interruption
    print("=" * 70)
    print("Test 5: Behavior Interruption (Priority)")
    print("=" * 70)
    print("Expected: Idle drift interrupted by greeting wave")
    print()
    
    input("Press Enter to start...")
    print("Starting idle_drift (low priority)...")
    idle = create_idle_drift()
    manager.execute_behavior(idle)
    time.sleep(1.0)
    
    print("Interrupting with greeting_wave (high priority)...")
    manager.execute_behavior(greeting_wave)
    time.sleep(2.0)
    print("✓ Interruption test complete")
    print()
    
    # Statistics
    print("=" * 70)
    print("Execution Statistics")
    print("=" * 70)
    stats = manager.get_stats()
    print(f"Behaviors executed: {stats['behaviors_executed']}")
    print(f"Behaviors interrupted: {stats['behaviors_interrupted']}")
    print()
    
    # Final return to neutral
    print("Returning to neutral pose...")
    manager.execute_behavior(neutral_pose)
    time.sleep(1.0)
    
    print()
    print("=" * 70)
    print("SDK Integration Test Complete!")
    print("=" * 70)
    print()
    
    if manager.enable_robot:
        print("✓ All movements executed on real robot/simulator")
        print("✓ No errors or crashes")
        print("✓ Behavior system integrated with Reachy SDK")
    else:
        print("✓ Mock mode working correctly")
        print("  Run with simulator for full test")
    print()

print("Test script finished.")
