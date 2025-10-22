"""
Unit Tests for Story 3.1: Greeting Behavior Module

Tests behavior definitions, BehaviorManager execution, non-blocking operation,
interruption logic, and thread safety.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import threading
from behavior_module import (
    BehaviorAction,
    Behavior,
    BehaviorManager,
    greeting_wave,
    curious_tilt,
    create_idle_drift,
    neutral_pose
)


def test_behavior_action_structure():
    """Test BehaviorAction dataclass structure (AC: 5)."""
    print("\n[TEST] BehaviorAction structure...")
    
    action = BehaviorAction(
        roll=10.0,
        pitch=5.0,
        yaw=-15.0,
        x=0.01,
        y=0.02,
        z=0.03,
        duration=0.5,
        blocking=True
    )
    
    assert action.roll == 10.0
    assert action.pitch == 5.0
    assert action.yaw == -15.0
    assert action.x == 0.01
    assert action.y == 0.02
    assert action.z == 0.03
    assert action.duration == 0.5
    assert action.blocking == True
    
    # Test pose matrix generation
    pose = action.to_pose_matrix()
    assert pose.shape == (4, 4)
    
    print("✓ BehaviorAction structure validated")
    return True


def test_behavior_structure():
    """Test Behavior dataclass structure (AC: 5)."""
    print("\n[TEST] Behavior structure...")
    
    behavior = Behavior(
        name="test_behavior",
        actions=[
            BehaviorAction(roll=10.0, duration=0.5),
            BehaviorAction(roll=-10.0, duration=0.5)
        ],
        interruptible=True,
        priority=5
    )
    
    assert behavior.name == "test_behavior"
    assert len(behavior.actions) == 2
    assert behavior.interruptible == True
    assert behavior.priority == 5
    
    print("✓ Behavior structure validated")
    return True


def test_predefined_behaviors():
    """Test predefined behaviors exist and are valid (AC: 2, 3, 4)."""
    print("\n[TEST] Predefined behaviors...")
    
    # Test greeting_wave (AC: 2)
    assert greeting_wave.name == "greeting_wave"
    assert len(greeting_wave.actions) > 0
    assert greeting_wave.interruptible == False
    assert greeting_wave.priority == 8
    print(f"  ✓ greeting_wave: {len(greeting_wave.actions)} actions")
    
    # Test curious_tilt (AC: 3)
    assert curious_tilt.name == "curious_tilt"
    assert len(curious_tilt.actions) > 0
    assert curious_tilt.interruptible == True
    assert curious_tilt.priority == 6
    print(f"  ✓ curious_tilt: {len(curious_tilt.actions)} actions")
    
    # Test idle_drift (AC: 4)
    idle = create_idle_drift()
    assert idle.name == "idle_drift"
    assert len(idle.actions) > 0
    assert idle.interruptible == True
    assert idle.priority == 1
    print(f"  ✓ idle_drift: {len(idle.actions)} actions")
    
    # Test neutral_pose
    assert neutral_pose.name == "neutral"
    assert len(neutral_pose.actions) > 0
    print(f"  ✓ neutral_pose: {len(neutral_pose.actions)} actions")
    
    print("✓ All predefined behaviors validated")
    return True


def test_behavior_manager_initialization():
    """Test BehaviorManager initialization (AC: 1, 6)."""
    print("\n[TEST] BehaviorManager initialization...")
    
    # Test with no robot (simulation)
    manager = BehaviorManager(reachy=None, enable_robot=False)
    assert manager.reachy is None
    assert manager.enable_robot == False
    assert manager.current_behavior is None
    assert manager.behaviors_executed == 0
    print("  ✓ Simulation mode initialization")
    
    # Test with mock robot
    class MockRobot:
        def set_target(self, head=None):
            pass
    
    manager = BehaviorManager(reachy=MockRobot(), enable_robot=True)
    assert manager.reachy is not None
    assert manager.enable_robot == True
    print("  ✓ Robot mode initialization")
    
    print("✓ BehaviorManager initialization validated")
    return True


def test_behavior_execution_non_blocking():
    """Test non-blocking behavior execution (AC: 6)."""
    print("\n[TEST] Non-blocking execution...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Create a behavior with longer duration
    long_behavior = Behavior(
        name="long_test",
        actions=[
            BehaviorAction(roll=10.0, duration=1.0, blocking=True)
        ],
        interruptible=True,
        priority=5
    )
    
    # Execute behavior
    start = time.time()
    success = manager.execute_behavior(long_behavior)
    elapsed = time.time() - start
    
    # Should return immediately (non-blocking)
    assert success == True
    assert elapsed < 0.1, f"Should be non-blocking, took {elapsed}s"
    assert manager.is_executing() == True
    
    # Wait for completion
    time.sleep(1.2)
    assert manager.is_executing() == False
    
    print("✓ Non-blocking execution validated")
    return True


def test_behavior_interruption():
    """Test behavior interruption logic (AC: 6)."""
    print("\n[TEST] Behavior interruption...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Start a longer behavior (low priority, interruptible)
    long_behavior = Behavior(
        name="long_low_priority",
        actions=[
            BehaviorAction(roll=5.0, duration=2.0, blocking=True)
        ],
        interruptible=True,
        priority=2
    )
    manager.execute_behavior(long_behavior)
    time.sleep(0.2)
    assert manager.is_executing() == True
    print(f"  Started: {manager.get_current_behavior()}")
    
    # Interrupt with greeting (high priority)
    success = manager.execute_behavior(greeting_wave)
    time.sleep(0.2)
    assert success == True
    assert manager.get_current_behavior() == "greeting_wave"
    print(f"  Interrupted with: {manager.get_current_behavior()}")
    
    time.sleep(1.5)  # Let greeting complete
    
    print("✓ Behavior interruption validated")
    return True


def test_non_interruptible_behavior():
    """Test non-interruptible behavior protection (AC: 6)."""
    print("\n[TEST] Non-interruptible protection...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Start non-interruptible greeting
    manager.execute_behavior(greeting_wave)
    time.sleep(0.1)
    assert manager.get_current_behavior() == "greeting_wave"
    print(f"  Started non-interruptible: {manager.get_current_behavior()}")
    
    # Try to interrupt with idle (should fail)
    idle = create_idle_drift()
    success = manager.execute_behavior(idle)
    assert success == False, "Should not interrupt non-interruptible behavior"
    assert manager.get_current_behavior() == "greeting_wave", "Should still be greeting"
    print(f"  ✓ Protected from interruption")
    
    time.sleep(1.5)  # Let greeting complete
    
    print("✓ Non-interruptible protection validated")
    return True


def test_priority_system():
    """Test priority-based behavior selection (AC: 1, 6)."""
    print("\n[TEST] Priority system...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Start high-priority behavior
    manager.execute_behavior(greeting_wave)  # priority 8
    time.sleep(0.1)
    print(f"  Started high-priority (8): {manager.get_current_behavior()}")
    
    # Try lower priority (should fail)
    success = manager.execute_behavior(curious_tilt)  # priority 6
    assert success == False, "Lower priority should not interrupt"
    assert manager.get_current_behavior() == "greeting_wave"
    print(f"  ✓ Lower priority blocked")
    
    # Try equal priority (should fail)
    success = manager.execute_behavior(greeting_wave)  # priority 8
    assert success == False, "Equal priority should not interrupt"
    print(f"  ✓ Equal priority blocked")
    
    time.sleep(1.5)  # Let greeting complete
    
    print("✓ Priority system validated")
    return True


def test_thread_safety():
    """Test thread-safe behavior execution (AC: 6)."""
    print("\n[TEST] Thread safety...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Execute multiple behaviors from different threads
    def execute_random_behavior(i):
        if i % 2 == 0:
            manager.execute_behavior(greeting_wave)
        else:
            manager.execute_behavior(curious_tilt)
        time.sleep(0.1)
    
    threads = []
    for i in range(5):
        t = threading.Thread(target=execute_random_behavior, args=(i,))
        threads.append(t)
        t.start()
    
    # Wait for all threads
    for t in threads:
        t.join()
    
    # Should have handled concurrent requests safely
    time.sleep(2.0)  # Let final behavior complete
    
    stats = manager.get_stats()
    assert stats['behaviors_executed'] > 0
    print(f"  ✓ Handled {len(threads)} concurrent requests")
    print(f"  ✓ Executed: {stats['behaviors_executed']} behaviors")
    
    print("✓ Thread safety validated")
    return True


def test_behavior_statistics():
    """Test behavior execution statistics."""
    print("\n[TEST] Statistics tracking...")
    
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    # Execute several behaviors
    manager.execute_behavior(greeting_wave)
    time.sleep(1.5)
    
    manager.execute_behavior(curious_tilt)
    time.sleep(1.8)
    
    # Get stats
    stats = manager.get_stats()
    assert stats['behaviors_executed'] >= 2
    assert 'behaviors_interrupted' in stats
    assert 'currently_executing' in stats
    
    print(f"  Executed: {stats['behaviors_executed']}")
    print(f"  Interrupted: {stats['behaviors_interrupted']}")
    print(f"  Currently executing: {stats['currently_executing']}")
    
    print("✓ Statistics tracking validated")
    return True


def test_idle_drift_randomization():
    """Test idle drift creates varied movements (AC: 4)."""
    print("\n[TEST] Idle drift randomization...")
    
    # Create multiple idle behaviors
    idles = [create_idle_drift() for _ in range(5)]
    
    # Check for variation in actions
    rolls = [idle.actions[0].roll for idle in idles]
    pitches = [idle.actions[0].pitch for idle in idles]
    yaws = [idle.actions[0].yaw for idle in idles]
    
    # Should have some variation (not all identical)
    assert len(set(rolls)) > 1, "Roll should vary"
    assert len(set(pitches)) > 1, "Pitch should vary"
    assert len(set(yaws)) > 1, "Yaw should vary"
    
    print(f"  ✓ Roll variation: {len(set(rolls))} unique values")
    print(f"  ✓ Pitch variation: {len(set(pitches))} unique values")
    print(f"  ✓ Yaw variation: {len(set(yaws))} unique values")
    
    print("✓ Idle drift randomization validated")
    return True


def run_all_tests():
    """Run all behavior module tests."""
    print("=" * 70)
    print("Story 3.1: Greeting Behavior Module - Unit Tests")
    print("=" * 70)
    
    tests = [
        test_behavior_action_structure,
        test_behavior_structure,
        test_predefined_behaviors,
        test_behavior_manager_initialization,
        test_behavior_execution_non_blocking,
        test_behavior_interruption,
        test_non_interruptible_behavior,
        test_priority_system,
        test_thread_safety,
        test_behavior_statistics,
        test_idle_drift_randomization
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"❌ {test.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} error: {e}")
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed == 0:
        print("✅ All acceptance criteria validated!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
