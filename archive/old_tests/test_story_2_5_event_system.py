"""
Unit Tests for Recognition Event System - Story 2.5

Tests event generation, debouncing logic, callbacks, and state tracking.
"""

import unittest
import time
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from event_system import EventManager, EventType, RecognitionEvent, PersonState


class TestEventSystem(unittest.TestCase):
    """Test suite for EventManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = EventManager(debounce_frames=3, departed_frames=3)
        self.callback_events = []
    
    def tearDown(self):
        """Clean up after tests."""
        self.callback_events.clear()


def test_event_types():
    """Test event type definitions (AC: 3)."""
    print("\n[TEST] Event type definitions...")
    
    assert EventType.PERSON_RECOGNIZED.value == "person_recognized"
    assert EventType.PERSON_UNKNOWN.value == "person_unknown"
    assert EventType.PERSON_DEPARTED.value == "person_departed"
    assert EventType.NO_FACES.value == "no_faces"
    
    print(f"✓ All 4 event types defined correctly")
    return True


def test_recognition_event_structure():
    """Test RecognitionEvent dataclass (AC: 4)."""
    print("\n[TEST] RecognitionEvent structure...")
    
    event = RecognitionEvent(
        event_type=EventType.PERSON_RECOGNIZED,
        timestamp=time.time(),
        person_name="Alice",
        confidence=0.85,
        bbox=(100, 200, 300, 100),
        frame_number=5
    )
    
    assert event.event_type == EventType.PERSON_RECOGNIZED
    assert event.person_name == "Alice"
    assert event.confidence == 0.85
    assert event.bbox == (100, 200, 300, 100)
    assert event.frame_number == 5
    assert event.timestamp > 0
    
    print(f"✓ RecognitionEvent structure validated")
    print(f"  Event: {event}")
    return True


def test_debouncing_person_recognized():
    """Test debouncing for PERSON_RECOGNIZED (AC: 2)."""
    print("\n[TEST] Debouncing - PERSON_RECOGNIZED...")
    
    manager = EventManager(debounce_frames=3)
    
    # Frame 1: Alice appears (no event yet)
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    events = manager.process_recognition_results(results, frame_number=1)
    assert len(events) == 0, "Should not trigger event on frame 1"
    
    # Frame 2: Alice still present (no event yet)
    events = manager.process_recognition_results(results, frame_number=2)
    assert len(events) == 0, "Should not trigger event on frame 2"
    
    # Frame 3: Alice still present (event triggers!)
    events = manager.process_recognition_results(results, frame_number=3)
    assert len(events) == 1, "Should trigger event on frame 3"
    assert events[0].event_type == EventType.PERSON_RECOGNIZED
    assert events[0].person_name == "Alice"
    
    # Frame 4: Alice still present (no duplicate event)
    events = manager.process_recognition_results(results, frame_number=4)
    assert len(events) == 0, "Should not trigger duplicate event"
    
    print(f"✓ Debouncing working correctly (3 frames required)")
    print(f"  Event triggered on frame 3")
    print(f"  No duplicate on frame 4")
    return True


def test_debouncing_person_unknown():
    """Test debouncing for PERSON_UNKNOWN (AC: 2, 3)."""
    print("\n[TEST] Debouncing - PERSON_UNKNOWN...")
    
    manager = EventManager(debounce_frames=3)
    
    # Frames 1-2: Unknown person (no event)
    results = [("unknown", 0.42, (150, 350, 400, 200))]
    for i in range(1, 3):
        events = manager.process_recognition_results(results, frame_number=i)
        assert len(events) == 0
    
    # Frame 3: Event triggers
    events = manager.process_recognition_results(results, frame_number=3)
    assert len(events) == 1
    assert events[0].event_type == EventType.PERSON_UNKNOWN
    assert events[0].person_name == "unknown"
    
    print(f"✓ PERSON_UNKNOWN debouncing works")
    return True


def test_person_departed_event():
    """Test PERSON_DEPARTED event generation (AC: 1, 3)."""
    print("\n[TEST] PERSON_DEPARTED event...")
    
    manager = EventManager(debounce_frames=3, departed_frames=3)
    
    # Frames 1-3: Alice appears and gets recognized
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    # Frames 4-5: Alice disappears (no event yet - only 2 absent frames)
    for i in range(4, 6):
        events = manager.process_recognition_results([], frame_number=i)
        assert all(e.event_type != EventType.PERSON_DEPARTED for e in events), f"Should not depart on frame {i}"
    
    # Frame 6: Alice departed event triggers (3rd absent frame)
    events = manager.process_recognition_results([], frame_number=6)
    departed_events = [e for e in events if e.event_type == EventType.PERSON_DEPARTED]
    assert len(departed_events) == 1, f"Should have 1 departed event, got {len(departed_events)}"
    assert departed_events[0].person_name == "Alice"
    assert departed_events[0].confidence == 0.0
    assert departed_events[0].bbox is None
    
    print(f"✓ PERSON_DEPARTED event triggered after 3 absent frames")
    return True


def test_no_faces_event():
    """Test NO_FACES event generation (AC: 1, 3)."""
    print("\n[TEST] NO_FACES event...")
    
    manager = EventManager()
    
    # Process frame with no faces
    events = manager.process_recognition_results([], frame_number=1)
    
    # Should get NO_FACES event
    no_faces_events = [e for e in events if e.event_type == EventType.NO_FACES]
    assert len(no_faces_events) == 1
    assert no_faces_events[0].person_name == ""
    assert no_faces_events[0].confidence == 0.0
    
    # Subsequent frames with no faces shouldn't trigger more NO_FACES events
    events = manager.process_recognition_results([], frame_number=2)
    no_faces_events = [e for e in events if e.event_type == EventType.NO_FACES]
    assert len(no_faces_events) == 0, "Should not trigger duplicate NO_FACES"
    
    print(f"✓ NO_FACES event triggered once")
    print(f"  No duplicate events on subsequent empty frames")
    return True


def test_multiple_people_debouncing():
    """Test independent debouncing for multiple people (AC: 2, 5)."""
    print("\n[TEST] Multiple people debouncing...")
    
    manager = EventManager(debounce_frames=3)
    
    # Frame 1: Alice appears
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    manager.process_recognition_results(results, frame_number=1)
    
    # Frame 2: Alice + Bob appear
    results = [
        ("Alice", 0.85, (100, 200, 300, 100)),
        ("Bob", 0.78, (150, 500, 350, 400))
    ]
    manager.process_recognition_results(results, frame_number=2)
    
    # Frame 3: Both still present
    events = manager.process_recognition_results(results, frame_number=3)
    
    # Alice should trigger (3 frames), Bob not yet (only 2 frames)
    assert len(events) == 1
    assert events[0].person_name == "Alice"
    
    # Frame 4: Bob should now trigger
    events = manager.process_recognition_results(results, frame_number=4)
    assert len(events) == 1
    assert events[0].person_name == "Bob"
    
    print(f"✓ Multiple people debounce independently")
    print(f"  Alice triggered frame 3, Bob frame 4")
    return True


def test_callback_system():
    """Test callback registration and triggering (AC: 5)."""
    print("\n[TEST] Callback system...")
    
    manager = EventManager(debounce_frames=3)
    callback_events = []
    
    # Register callback
    def on_recognized(event):
        callback_events.append(event)
    
    callback_id = manager.add_callback(EventType.PERSON_RECOGNIZED, on_recognized)
    
    # Trigger event
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    # Callback should have been called
    assert len(callback_events) == 1
    assert callback_events[0].person_name == "Alice"
    
    # Test callback removal
    manager.remove_callback(callback_id)
    
    # Trigger another event
    results = [("Bob", 0.78, (150, 500, 350, 400))]
    for i in range(4, 7):
        manager.process_recognition_results(results, frame_number=i)
    
    # Callback should NOT have been called (removed)
    assert len(callback_events) == 1, "Removed callback should not be triggered"
    
    print(f"✓ Callback system working")
    print(f"  Callback triggered: 1 time")
    print(f"  Callback removed successfully")
    return True


def test_multiple_callbacks():
    """Test multiple callbacks for same event type (AC: 5)."""
    print("\n[TEST] Multiple callbacks...")
    
    manager = EventManager(debounce_frames=3)
    callback_counts = {"callback1": 0, "callback2": 0}
    
    def callback1(event):
        callback_counts["callback1"] += 1
    
    def callback2(event):
        callback_counts["callback2"] += 1
    
    manager.add_callback(EventType.PERSON_RECOGNIZED, callback1)
    manager.add_callback(EventType.PERSON_RECOGNIZED, callback2)
    
    # Trigger event
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    # Both callbacks should have been called
    assert callback_counts["callback1"] == 1
    assert callback_counts["callback2"] == 1
    
    print(f"✓ Multiple callbacks work correctly")
    print(f"  Both callbacks triggered")
    return True


def test_event_history():
    """Test event history management (AC: 6)."""
    print("\n[TEST] Event history...")
    
    manager = EventManager(debounce_frames=3, max_history=10, departed_frames=999)  # High departed to prevent DEPARTED events
    
    # Generate multiple recognition events only
    for person_num in range(5):
        person_name = f"Person{person_num}"
        results = [(person_name, 0.80, (100, 200, 300, 100))]
        
        for frame in range(1, 4):
            manager.process_recognition_results(results, frame_number=person_num*3 + frame)
    
    # Check history
    history = manager.get_recent_events()
    assert len(history) == 5, f"Should have 5 events, got {len(history)}"
    assert history[0].person_name == "Person4", "Most recent should be Person4"
    assert history[-1].person_name == "Person0", "Oldest should be Person0"
    
    # Test history limit
    manager_limited = EventManager(debounce_frames=1, max_history=3)
    for i in range(5):
        results = [(f"Person{i}", 0.80, (100, 200, 300, 100))]
        manager_limited.process_recognition_results(results, frame_number=i+1)
    
    history = manager_limited.get_recent_events()
    assert len(history) <= 3, "Should respect max_history limit"
    
    print(f"✓ Event history working correctly")
    print(f"  History size: {len(history)}")
    print(f"  Max history enforced: 3 events")
    return True


def test_person_re_entering():
    """Test person leaving and re-entering (AC: 1, 2)."""
    print("\n[TEST] Person re-entering...")
    
    manager = EventManager(debounce_frames=3, departed_frames=3)
    
    # Alice appears and gets recognized (frames 1-3)
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    # Alice departs (frames 4-6)
    for i in range(4, 7):
        manager.process_recognition_results([], frame_number=i)
    
    # Alice returns (frames 7-9)
    for i in range(7, 10):
        events = manager.process_recognition_results(results, frame_number=i)
        
        if i == 9:
            # Should trigger new PERSON_RECOGNIZED event
            assert len(events) == 1
            assert events[0].event_type == EventType.PERSON_RECOGNIZED
            assert events[0].person_name == "Alice"
    
    print(f"✓ Person re-entering handled correctly")
    print(f"  New recognition event triggered on return")
    return True


def test_get_stats():
    """Test statistics retrieval."""
    print("\n[TEST] Statistics retrieval...")
    
    manager = EventManager(debounce_frames=3)
    
    # Generate some events
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    stats = manager.get_stats()
    
    assert "event_history_size" in stats
    assert "currently_tracked" in stats
    assert "tracked_people" in stats
    assert "event_counts" in stats
    assert "callback_counts" in stats
    
    assert stats["event_history_size"] == 1
    assert stats["currently_tracked"] == 1
    assert "Alice" in stats["tracked_people"]
    
    print(f"✓ Statistics retrieved correctly")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return True


def test_reset():
    """Test event manager reset."""
    print("\n[TEST] EventManager reset...")
    
    manager = EventManager(debounce_frames=3)
    
    # Generate events
    results = [("Alice", 0.85, (100, 200, 300, 100))]
    for i in range(1, 4):
        manager.process_recognition_results(results, frame_number=i)
    
    # Reset
    manager.reset()
    
    # Check state is cleared
    stats = manager.get_stats()
    assert stats["event_history_size"] == 0
    assert stats["currently_tracked"] == 0
    assert stats["frame_count"] == 0
    
    print(f"✓ Reset working correctly")
    print(f"  History cleared, state reset")
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Story 2.5: Recognition Event System - Unit Tests")
    print("=" * 60)
    
    tests = [
        test_event_types,
        test_recognition_event_structure,
        test_debouncing_person_recognized,
        test_debouncing_person_unknown,
        test_person_departed_event,
        test_no_faces_event,
        test_multiple_people_debouncing,
        test_callback_system,
        test_multiple_callbacks,
        test_event_history,
        test_person_re_entering,
        test_get_stats,
        test_reset
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
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("✅ All acceptance criteria validated!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
