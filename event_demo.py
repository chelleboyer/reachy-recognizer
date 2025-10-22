"""
Event System Demo - Story 2.5

Demonstrates the recognition event system with callbacks.
Shows how events are generated and callbacks are triggered.
"""

from event_system import EventManager, EventType, RecognitionEvent
from recognition_pipeline import RecognitionPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("=" * 60)
    print("Recognition Event System Demo")
    print("=" * 60)
    
    # Create pipeline with event system enabled
    pipeline = RecognitionPipeline(enable_events=True, event_debounce_frames=3)
    
    # Load face database
    if not pipeline.load_database("face_database.json"):
        logger.error("Failed to load face database")
        return
    
    print(f"\nLoaded {pipeline.database.size()} faces")
    print("Event system enabled with 3-frame debouncing\n")
    
    # Register event callbacks
    print("Registering event callbacks...")
    
    def on_person_recognized(event: RecognitionEvent):
        """Called when a known person is recognized."""
        print(f"🎉 [Frame {event.frame_number}] Hello {event.person_name}! (confidence: {event.confidence:.2f})")
    
    def on_person_unknown(event: RecognitionEvent):
        """Called when an unknown person appears."""
        print(f"👋 [Frame {event.frame_number}] Hi stranger! (confidence: {event.confidence:.2f})")
    
    def on_person_departed(event: RecognitionEvent):
        """Called when a person leaves."""
        print(f"💨 [Frame {event.frame_number}] Goodbye {event.person_name}!")
    
    def on_no_faces(event: RecognitionEvent):
        """Called when no faces are detected."""
        print(f"👀 [Frame {event.frame_number}] No faces detected")
    
    # Register callbacks
    cb1 = pipeline.add_event_callback(EventType.PERSON_RECOGNIZED, on_person_recognized)
    cb2 = pipeline.add_event_callback(EventType.PERSON_UNKNOWN, on_person_unknown)
    cb3 = pipeline.add_event_callback(EventType.PERSON_DEPARTED, on_person_departed)
    cb4 = pipeline.add_event_callback(EventType.NO_FACES, on_no_faces)
    
    print(f"✓ Registered {4} callbacks\n")
    
    # Run live recognition
    print("Starting live recognition...")
    print("\nControls:")
    print("  'q' - Quit")
    print("  's' - Save snapshot")
    print("  'd' - Toggle debug overlay")
    print("  ' ' - Pause/resume")
    print("  'e' - Show event statistics\n")
    
    print("=" * 60)
    print("EVENTS WILL APPEAR BELOW")
    print("=" * 60)
    print()
    
    try:
        # Note: Modified run_live to support 'e' key for event stats
        pipeline.run_live()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    
    # Show final statistics
    print("\n" + "=" * 60)
    print("Event Statistics")
    print("=" * 60)
    
    stats = pipeline.get_event_stats()
    if stats:
        print(f"\nFrames processed: {stats['frame_count']}")
        print(f"Event history size: {stats['event_history_size']}")
        print(f"Currently tracked: {stats['currently_tracked']}")
        print(f"Tracked people: {stats['tracked_people']}")
        
        print("\nEvent counts:")
        for event_name, count in stats['event_counts'].items():
            print(f"  {event_name}: {count}")
        
        print("\nRecent events:")
        for event in pipeline.get_recent_events(limit=10):
            print(f"  {event}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
