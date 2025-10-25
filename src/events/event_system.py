"""
Recognition Event System - Story 2.5

Generates discrete recognition events with debouncing logic to prevent
duplicate events and provides callback mechanism for behavior systems.

This module tracks people across frames and emits events for:
- Person recognized (known person detected after debouncing)
- Person unknown (unknown person detected after debouncing)  
- Person departed (person left frame)
- No faces (no faces detected)
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Callable, Any
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import config (optional - falls back to defaults if not available)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default values")


class EventType(Enum):
    """Recognition event types."""
    PERSON_RECOGNIZED = "person_recognized"  # Known person detected
    PERSON_UNKNOWN = "person_unknown"        # Unknown person detected
    PERSON_DEPARTED = "person_departed"      # Person left frame
    NO_FACES = "no_faces"                    # No faces in frame


@dataclass
class RecognitionEvent:
    """
    Recognition event with all relevant information.
    
    Attributes:
        event_type: Type of event
        timestamp: Unix timestamp when event occurred
        person_name: Name of person ("unknown" for PERSON_UNKNOWN)
        confidence: Recognition confidence (0.0 for NO_FACES, PERSON_DEPARTED)
        bbox: Bounding box (top, right, bottom, left) or None
        frame_number: Frame number when event occurred
    """
    event_type: EventType
    timestamp: float
    person_name: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]]
    frame_number: int
    
    def __str__(self) -> str:
        """String representation for logging."""
        if self.event_type == EventType.NO_FACES:
            return f"[Frame {self.frame_number}] NO_FACES"
        elif self.event_type == EventType.PERSON_DEPARTED:
            return f"[Frame {self.frame_number}] DEPARTED: {self.person_name}"
        else:
            return f"[Frame {self.frame_number}] {self.event_type.value.upper()}: {self.person_name} ({self.confidence:.2f})"


@dataclass
class PersonState:
    """
    Tracks a person's state across frames.
    
    Attributes:
        name: Person's name
        consecutive_frames: Number of consecutive frames person has been seen
        departed_frames: Number of consecutive frames person has been absent
        last_confidence: Most recent confidence score
        last_bbox: Most recent bounding box
        event_triggered: Whether PERSON_RECOGNIZED/UNKNOWN event has been triggered
    """
    name: str
    consecutive_frames: int = 0
    departed_frames: int = 0
    last_confidence: float = 0.0
    last_bbox: Optional[Tuple[int, int, int, int]] = None
    event_triggered: bool = False


class EventManager:
    """
    Manages recognition events with debouncing and callbacks.
    
    Tracks people across frames, generates events for state changes,
    and notifies registered callbacks.
    
    Attributes:
        debounce_frames: Number of consecutive frames required before triggering event
        departed_frames: Number of absent frames before triggering PERSON_DEPARTED
        max_history: Maximum number of events to keep in history
        event_history: Deque of recent events
        callbacks: Dict mapping event types to callback functions
        current_state: Dict mapping person names to PersonState
        frame_count: Total frames processed
    """
    
    def __init__(
        self,
        debounce_seconds: Optional[float] = None,
        departed_threshold_seconds: Optional[float] = None,
        debounce_frames: Optional[int] = None,
        departed_frames: Optional[int] = None,
        max_history: Optional[int] = None,
        fps: float = 30.0
    ):
        """
        Initialize event manager.
        
        Args:
            debounce_seconds: Seconds required before triggering event (loaded from config if None)
            departed_threshold_seconds: Seconds absent before departed event (loaded from config if None)
            debounce_frames: DEPRECATED - use debounce_seconds
            departed_frames: DEPRECATED - use departed_frames
            max_history: Maximum events to keep in history (loaded from config if None)
            fps: Frame rate for converting seconds to frames (default: 30.0)
        """
        # Load from config if available
        if _CONFIG_AVAILABLE and (debounce_seconds is None or departed_threshold_seconds is None or max_history is None):
            try:
                config = get_config()
                if debounce_seconds is None:
                    debounce_seconds = config.events.debounce_seconds
                if departed_threshold_seconds is None:
                    departed_threshold_seconds = config.events.departed_threshold_seconds
                if max_history is None:
                    max_history = config.events.max_event_history
                logger.info("✓ Loaded event configuration from config")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        # Set defaults if still None
        if debounce_seconds is None:
            debounce_seconds = 3.0
        if departed_threshold_seconds is None:
            departed_threshold_seconds = 3.0
        if max_history is None:
            max_history = 100
        
        # Convert seconds to frames (backwards compatibility)
        if debounce_frames is None:
            debounce_frames = max(1, int(debounce_seconds * fps))
        if departed_frames is None:
            departed_frames = max(1, int(departed_threshold_seconds * fps))
        
        self.debounce_frames = debounce_frames
        self.departed_frames = departed_frames
        self.max_history = max_history
        
        self.event_history: deque = deque(maxlen=max_history)
        self.callbacks: Dict[EventType, List[Tuple[int, Callable]]] = {
            event_type: [] for event_type in EventType
        }
        self.current_state: Dict[str, PersonState] = {}
        self.frame_count = 0
        self.next_callback_id = 0
        
        # Accuracy tracking (Story 4.2)
        self.accuracy_metrics = {
            'true_positives': 0,   # Correctly recognized known person
            'false_positives': 0,  # Incorrectly recognized as known (would need ground truth)
            'true_negatives': 0,   # Correctly identified as unknown
            'false_negatives': 0,  # Failed to recognize known person (would need ground truth)
            'unknown_count': 0,    # Total unknown person detections
            'recognized_count': 0,  # Total recognized person detections
            'total_events': 0,     # Total events generated
        }
        
        logger.info(f"EventManager initialized (debounce={debounce_frames}, departed={departed_frames})")
    
    def process_recognition_results(
        self,
        results: List[Tuple[str, float, Tuple[int, int, int, int]]],
        frame_number: Optional[int] = None
    ) -> List[RecognitionEvent]:
        """
        Process recognition results and generate events.
        
        Args:
            results: List of (name, confidence, bbox) tuples from recognizer
            frame_number: Optional frame number (uses internal counter if None)
            
        Returns:
            List of events generated this frame
            
        Example:
            >>> results = [("Alice", 0.85, (100, 200, 300, 100))]
            >>> events = manager.process_recognition_results(results)
            >>> for event in events:
            >>>     print(event)
        """
        if frame_number is None:
            self.frame_count += 1
            frame_number = self.frame_count
        
        events = []
        current_names = set()
        
        # Process detected people
        for name, confidence, bbox in results:
            current_names.add(name)
            
            if name in self.current_state:
                # Person already being tracked
                state = self.current_state[name]
                state.consecutive_frames += 1
                state.departed_frames = 0  # Reset departed counter
                state.last_confidence = confidence
                state.last_bbox = bbox
                
                # Trigger event after debounce period
                if state.consecutive_frames == self.debounce_frames and not state.event_triggered:
                    if name == "unknown":
                        event_type = EventType.PERSON_UNKNOWN
                    else:
                        event_type = EventType.PERSON_RECOGNIZED
                    
                    event = RecognitionEvent(
                        event_type=event_type,
                        timestamp=time.time(),
                        person_name=name,
                        confidence=confidence,
                        bbox=bbox,
                        frame_number=frame_number
                    )
                    events.append(event)
                    state.event_triggered = True
                    self._add_to_history(event)
                    self._trigger_callbacks(event)
                    
                    # Track accuracy metrics (Story 4.2)
                    self._update_accuracy_metrics(event_type, name, confidence)
                    
                    logger.info(f"✓ Event: {event}")
            
            else:
                # New person detected
                self.current_state[name] = PersonState(
                    name=name,
                    consecutive_frames=1,
                    last_confidence=confidence,
                    last_bbox=bbox
                )
                logger.debug(f"Started tracking: {name}")
        
        # Check for departed people
        departed_names = []
        for name, state in self.current_state.items():
            if name not in current_names:
                # Person not detected in this frame
                state.departed_frames += 1
                state.consecutive_frames = 0  # Reset consecutive counter
                
                # Trigger PERSON_DEPARTED after departed threshold
                if state.departed_frames == self.departed_frames and state.event_triggered:
                    event = RecognitionEvent(
                        event_type=EventType.PERSON_DEPARTED,
                        timestamp=time.time(),
                        person_name=name,
                        confidence=0.0,
                        bbox=None,
                        frame_number=frame_number
                    )
                    events.append(event)
                    self._add_to_history(event)
                    self._trigger_callbacks(event)
                    departed_names.append(name)
                    
                    logger.info(f"✓ Event: {event}")
        
        # Remove departed people from tracking
        for name in departed_names:
            del self.current_state[name]
            logger.debug(f"Stopped tracking: {name}")
        
        # Check for NO_FACES event
        if len(results) == 0 and len(self.current_state) == 0:
            # Only trigger NO_FACES once per "session"
            # (not every frame when no faces present)
            if self.frame_count == 1 or self._last_event_was_not_no_faces():
                event = RecognitionEvent(
                    event_type=EventType.NO_FACES,
                    timestamp=time.time(),
                    person_name="",
                    confidence=0.0,
                    bbox=None,
                    frame_number=frame_number
                )
                events.append(event)
                self._add_to_history(event)
                self._trigger_callbacks(event)
                
                logger.debug(f"Event: {event}")
        
        return events
    
    def _last_event_was_not_no_faces(self) -> bool:
        """Check if last event was something other than NO_FACES."""
        if len(self.event_history) == 0:
            return True
        return self.event_history[-1].event_type != EventType.NO_FACES
    
    def _add_to_history(self, event: RecognitionEvent):
        """Add event to history (FIFO with max size)."""
        self.event_history.append(event)
    
    def _trigger_callbacks(self, event: RecognitionEvent):
        """Trigger all callbacks registered for this event type."""
        for callback_id, callback_fn in self.callbacks[event.event_type]:
            try:
                callback_fn(event)
            except Exception as e:
                logger.error(f"Callback {callback_id} failed: {e}")
    
    def add_callback(
        self,
        event_type: EventType,
        callback_fn: Callable[[RecognitionEvent], None]
    ) -> int:
        """
        Register a callback for specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback_fn: Function to call when event occurs
            
        Returns:
            Callback ID (use to remove callback later)
            
        Example:
            >>> def on_person_recognized(event):
            >>>     print(f"Hello {event.person_name}!")
            >>> callback_id = manager.add_callback(
            >>>     EventType.PERSON_RECOGNIZED,
            >>>     on_person_recognized
            >>> )
        """
        callback_id = self.next_callback_id
        self.next_callback_id += 1
        
        self.callbacks[event_type].append((callback_id, callback_fn))
        logger.debug(f"Added callback {callback_id} for {event_type.value}")
        
        return callback_id
    
    def remove_callback(self, callback_id: int) -> bool:
        """
        Remove a callback by ID.
        
        Args:
            callback_id: ID returned by add_callback()
            
        Returns:
            True if callback was found and removed
        """
        for event_type, callbacks in self.callbacks.items():
            for i, (cid, _) in enumerate(callbacks):
                if cid == callback_id:
                    callbacks.pop(i)
                    logger.debug(f"Removed callback {callback_id}")
                    return True
        return False
    
    def get_recent_events(self, count: Optional[int] = None) -> List[RecognitionEvent]:
        """
        Get recent events from history.
        
        Args:
            count: Number of events to retrieve (None = all)
            
        Returns:
            List of recent events (newest first)
        """
        events = list(self.event_history)
        events.reverse()  # Newest first
        
        if count is not None:
            events = events[:count]
        
        return events
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event manager statistics."""
        event_counts = {event_type.value: 0 for event_type in EventType}
        for event in self.event_history:
            event_counts[event.event_type.value] += 1
        
        return {
            "frame_count": self.frame_count,
            "event_history_size": len(self.event_history),
            "currently_tracked": len(self.current_state),
            "tracked_people": list(self.current_state.keys()),
            "event_counts": event_counts,
            "callback_counts": {
                event_type.value: len(callbacks)
                for event_type, callbacks in self.callbacks.items()
            }
        }
    
    def _update_accuracy_metrics(self, event_type: EventType, person_name: str, confidence: float):
        """
        Update accuracy tracking metrics (Story 4.2).
        
        Args:
            event_type: Type of event triggered
            person_name: Person's name
            confidence: Recognition confidence score
        """
        self.accuracy_metrics['total_events'] += 1
        
        if event_type == EventType.PERSON_RECOGNIZED:
            # Assume true positive (correctly recognized known person)
            # Note: False positive detection would require ground truth data
            self.accuracy_metrics['recognized_count'] += 1
            self.accuracy_metrics['true_positives'] += 1
            
        elif event_type == EventType.PERSON_UNKNOWN:
            # Assume true negative (correctly identified as unknown)
            # Note: False negative detection would require ground truth data
            self.accuracy_metrics['unknown_count'] += 1
            self.accuracy_metrics['true_negatives'] += 1
        
        # Log accuracy event
        logger.info(
            f"Recognition accuracy tracked",
            extra={
                'event': 'accuracy_update',
                'data': {
                    'event_type': event_type.value,
                    'person_name': person_name,
                    'confidence': confidence
                },
                'metrics': self.accuracy_metrics.copy()
            }
        )
    
    def get_accuracy_report(self) -> Dict[str, Any]:
        """
        Generate recognition accuracy report (Story 4.2).
        
        Returns:
            Dictionary with accuracy statistics
            
        Note: True accuracy calculation requires ground truth data.
        Current implementation assumes all recognitions are correct.
        """
        total = self.accuracy_metrics['total_events']
        if total == 0:
            return {
                'accuracy': 0.0,
                'total_events': 0,
                'recognized_count': 0,
                'unknown_count': 0
            }
        
        # Calculate accuracy (with caveat about ground truth)
        correct = (
            self.accuracy_metrics['true_positives'] + 
            self.accuracy_metrics['true_negatives']
        )
        accuracy = (correct / total * 100) if total > 0 else 0.0
        
        return {
            'accuracy': round(accuracy, 2),
            'total_events': total,
            'recognized_count': self.accuracy_metrics['recognized_count'],
            'unknown_count': self.accuracy_metrics['unknown_count'],
            'true_positives': self.accuracy_metrics['true_positives'],
            'false_positives': self.accuracy_metrics['false_positives'],
            'true_negatives': self.accuracy_metrics['true_negatives'],
            'false_negatives': self.accuracy_metrics['false_negatives'],
            'note': 'Accuracy assumes all recognitions are correct (no ground truth validation)'
        }
    
    def reset(self):
        """Reset event manager state (clear history and tracking)."""
        self.event_history.clear()
        self.current_state.clear()
        self.frame_count = 0
        self.accuracy_metrics = {
            'true_positives': 0,
            'false_positives': 0,
            'true_negatives': 0,
            'false_negatives': 0,
            'unknown_count': 0,
            'recognized_count': 0,
            'total_events': 0,
        }
        logger.info("EventManager reset")


def main():
    """Demo script showing EventManager usage."""
    print("=" * 60)
    print("Recognition Event System - Story 2.5")
    print("=" * 60)
    
    # Create event manager
    manager = EventManager(debounce_frames=3, departed_frames=3)
    
    # Register callbacks
    def on_person_recognized(event: RecognitionEvent):
        print(f"🎉 Callback: Hello {event.person_name}! (confidence: {event.confidence:.2f})")
    
    def on_person_unknown(event: RecognitionEvent):
        print(f"👋 Callback: Hi stranger! (confidence: {event.confidence:.2f})")
    
    def on_person_departed(event: RecognitionEvent):
        print(f"👋 Callback: Goodbye {event.person_name}!")
    
    manager.add_callback(EventType.PERSON_RECOGNIZED, on_person_recognized)
    manager.add_callback(EventType.PERSON_UNKNOWN, on_person_unknown)
    manager.add_callback(EventType.PERSON_DEPARTED, on_person_departed)
    
    print(f"\n✓ EventManager initialized")
    print(f"  Debounce frames: {manager.debounce_frames}")
    print(f"  Departed frames: {manager.departed_frames}")
    print(f"  Callbacks registered: 3")
    
    # Simulate recognition results over multiple frames
    print(f"\n" + "=" * 60)
    print("Simulating Recognition Results")
    print("=" * 60)
    
    # Frame 1-3: Alice appears (debouncing)
    print("\n[Frames 1-3] Alice appears...")
    for i in range(1, 4):
        results = [("Alice", 0.85, (100, 200, 300, 100))]
        events = manager.process_recognition_results(results, frame_number=i)
        print(f"  Frame {i}: {len(events)} event(s)")
    
    # Frame 4-6: Alice + Bob appear
    print("\n[Frames 4-6] Bob joins...")
    for i in range(4, 7):
        results = [
            ("Alice", 0.85, (100, 200, 300, 100)),
            ("Bob", 0.78, (150, 500, 350, 400))
        ]
        events = manager.process_recognition_results(results, frame_number=i)
        print(f"  Frame {i}: {len(events)} event(s)")
    
    # Frame 7-9: Only Bob (Alice departs)
    print("\n[Frames 7-9] Alice leaves...")
    for i in range(7, 10):
        results = [("Bob", 0.78, (150, 500, 350, 400))]
        events = manager.process_recognition_results(results, frame_number=i)
        print(f"  Frame {i}: {len(events)} event(s)")
    
    # Frame 10-12: Unknown person
    print("\n[Frames 10-12] Unknown person appears...")
    for i in range(10, 13):
        results = [
            ("Bob", 0.78, (150, 500, 350, 400)),
            ("unknown", 0.42, (200, 350, 400, 250))
        ]
        events = manager.process_recognition_results(results, frame_number=i)
        print(f"  Frame {i}: {len(events)} event(s)")
    
    # Print statistics
    print(f"\n" + "=" * 60)
    print("Session Statistics")
    print("=" * 60)
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Print event history
    print(f"\n" + "=" * 60)
    print("Event History (most recent first)")
    print("=" * 60)
    recent_events = manager.get_recent_events(10)
    for event in recent_events:
        print(f"  {event}")
    
    print(f"\n✓ Event system demo complete!")


if __name__ == "__main__":
    main()
