"""
Simple test to verify robot connection and execute one behavior.
Run with: python tests/test_robot_connection_simple.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

print("=" * 70)
print("Simple Robot Connection Test")
print("=" * 70)
print()

# Step 1: Import ReachyMini
print("Step 1: Importing ReachyMini SDK...")
try:
    from reachy_mini import ReachyMini
    print("✓ SDK imported successfully")
except ImportError as e:
    print(f"✗ Failed to import: {e}")
    sys.exit(1)

# Step 2: Connect to robot
print("\nStep 2: Connecting to robot...")
print("Timeout: 60 seconds")
print("Waiting for Zenoh messages from daemon...")

try:
    robot = ReachyMini(media_backend="no_media", timeout=60)
    print("✓ Connected successfully!")
except Exception as e:
    print(f"✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Is the daemon running? (uvx --from reachy-mini reachy-mini-daemon)")
    print("2. Is Bluetooth awake?")
    print("3. Check port 7447: netstat -an | Select-String 7447")
    sys.exit(1)

# Step 3: Test BehaviorManager with real robot
print("\nStep 3: Testing BehaviorManager with real robot...")
try:
    from src.behaviors.behavior_module import BehaviorManager, greeting_wave
    
    manager = BehaviorManager(reachy=robot, enable_robot=True)
    print(f"✓ BehaviorManager initialized")
    print(f"  - Robot connected: {manager.reachy is not None}")
    print(f"  - Robot enabled: {manager.enable_robot}")
    
    # Step 4: Execute a behavior
    print("\nStep 4: Executing greeting_wave behavior...")
    print("Watch the robot's head!")
    
    success = manager.execute_behavior(greeting_wave)
    if success:
        print("✓ Behavior started")
        time.sleep(2.0)  # Wait for behavior to complete
        print("✓ Behavior completed")
    else:
        print("✗ Behavior failed to start")
    
    # Step 5: Check stats
    stats = manager.get_stats()
    print(f"\nStep 5: Statistics")
    print(f"  - Behaviors executed: {stats['behaviors_executed']}")
    print(f"  - Behaviors interrupted: {stats['behaviors_interrupted']}")
    
except Exception as e:
    print(f"✗ Error during test: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup
    print("\nCleaning up...")
    try:
        robot.__exit__(None, None, None)
        print("✓ Robot connection closed")
    except:
        pass

print()
print("=" * 70)
print("✅ Test Complete!")
print("=" * 70)
