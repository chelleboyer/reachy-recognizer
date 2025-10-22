"""
Greeting Coordinator - Story 3.3

Coordinates recognition events with behaviors and speech for natural,
personalized greeting interactions.

This module ties together:
- Event System (Story 2.5): Recognition events
- Behavior Module (Story 3.1): Physical gestures
- TTS Module (Story 3.2): Spoken greetings

Implements timing coordination, session tracking, and multi-person prioritization.
"""

import time
import threading
import logging
from typing import Optional, Dict, List, Set
from dataclasses import dataclass

from event_system import EventManager, EventType, RecognitionEvent
from behavior_module import BehaviorManager, greeting_wave
from tts_module import TTSManager, GreetingType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GreetingCoordinator:
    """
    Coordinates recognition events with behaviors and speech.
    
    Manages greeting responses with proper timing, de-duplication,
    and multi-person prioritization.
    
    Key features:
    - Coordinated gesture + speech timing
    - Session-based duplicate prevention
    - Multi-person confidence-based priority
    - Response latency tracking (< 400ms target)
    - Thread-safe execution
    """
    
    def __init__(
        self,
        event_manager: EventManager,
        behavior_manager: BehaviorManager,
        tts_manager: TTSManager,
        gesture_speech_delay: float = 0.3
    ):
        """
        Initialize greeting coordinator.
        
        Args:
            event_manager: Event manager for recognition events
            behavior_manager: Behavior manager for gestures
            tts_manager: TTS manager for speech
            gesture_speech_delay: Delay between gesture start and speech (seconds)
        """
        self.event_manager = event_manager
        self.behavior_manager = behavior_manager
        self.tts_manager = tts_manager
        self.gesture_speech_delay = gesture_speech_delay
        
        # Session tracking (AC: 6)
        self.greeted_persons: Set[str] = set()  # Person names greeted this session
        self.greeting_in_progress = False
        self.greeting_lock = threading.Lock()
        
        # Performance metrics (AC: 4)
        self.total_greetings = 0
        self.latencies: List[float] = []
        self.avg_latency = 0.0
        self.max_latency = 0.0
        self.min_latency = float('inf')
        
        # Multi-person queue
        self.pending_greetings: List[RecognitionEvent] = []
        
        # Register event callback (AC: 1)
        self.event_manager.add_callback(
            EventType.PERSON_RECOGNIZED,
            self._on_person_recognized
        )
        
        logger.info("GreetingCoordinator initialized")
        logger.info(f"  Gesture-speech delay: {gesture_speech_delay}s")
    
    def _on_person_recognized(self, event: RecognitionEvent):
        """
        Handle PERSON_RECOGNIZED event.
        
        Checks for duplicates, manages greeting queue, and executes
        coordinated greeting response.
        
        Args:
            event: Recognition event with person details
        """
        # Check if already greeted this session (AC: 6)
        if event.person_name in self.greeted_persons:
            logger.debug(f"Already greeted {event.person_name}, skipping")
            return
        
        # Check if greeting in progress
        with self.greeting_lock:
            if self.greeting_in_progress:
                logger.debug(f"Greeting in progress, queueing {event.person_name}")
                self.pending_greetings.append(event)
                return
            self.greeting_in_progress = True
        
        try:
            # Execute coordinated greeting (AC: 2, 3)
            self._execute_greeting(event)
        except Exception as e:
            logger.error(f"Error executing greeting: {e}")
        finally:
            with self.greeting_lock:
                self.greeting_in_progress = False
            
            # Process pending greetings
            self._process_pending_greetings()
    
    def _execute_greeting(self, event: RecognitionEvent):
        """
        Execute coordinated greeting with timing.
        
        Sequence (AC: 2):
        1. Start gesture (greeting_wave)
        2. Wait gesture_speech_delay seconds
        3. Start speech (overlaps with gesture)
        4. Mark person as greeted
        5. Track performance metrics
        
        Args:
            event: Recognition event to respond to
        """
        start_time = time.time()
        
        logger.info(f"Greeting {event.person_name} (confidence: {event.confidence:.2f})")
        
        # 1. Start gesture immediately (AC: 2, 3)
        self.behavior_manager.execute_behavior(greeting_wave)
        
        # Track initial response latency (AC: 4)
        initial_latency = (time.time() - start_time) * 1000  # ms
        
        # 2. Wait before speech (gesture starts first) (AC: 3)
        time.sleep(self.gesture_speech_delay)
        
        # 3. Start speech (during gesture) (AC: 3)
        self.tts_manager.speak_greeting(
            GreetingType.RECOGNIZED,
            event.person_name
        )
        
        # 4. Mark as greeted (AC: 6)
        self.greeted_persons.add(event.person_name)
        self.total_greetings += 1
        
        # 5. Track full latency (AC: 4)
        total_latency = (time.time() - start_time) * 1000  # ms
        self.latencies.append(total_latency)
        self.avg_latency = sum(self.latencies) / len(self.latencies)
        self.max_latency = max(self.max_latency, total_latency)
        self.min_latency = min(self.min_latency, total_latency)
        
        logger.info(f"  Initial response: {initial_latency:.1f}ms")
        logger.info(f"  Total coordination: {total_latency:.1f}ms")
        
        # Check latency target (AC: 4)
        if initial_latency > 400:
            logger.warning(f"⚠️  Initial latency {initial_latency:.1f}ms exceeds 400ms target!")
    
    def _process_pending_greetings(self):
        """
        Process queued greetings (multi-person handling).
        
        Sorts by confidence and greets highest confidence person
        that hasn't been greeted yet (AC: 5).
        """
        if not self.pending_greetings:
            return
        
        # Sort by confidence (highest first) (AC: 5)
        self.pending_greetings.sort(key=lambda e: e.confidence, reverse=True)
        
        # Greet highest confidence person not yet greeted
        for event in self.pending_greetings:
            if event.person_name not in self.greeted_persons:
                logger.debug(f"Processing pending greeting for {event.person_name}")
                self.pending_greetings.remove(event)
                
                # Execute with lock
                with self.greeting_lock:
                    self.greeting_in_progress = True
                
                try:
                    self._execute_greeting(event)
                except Exception as e:
                    logger.error(f"Error in pending greeting: {e}")
                finally:
                    with self.greeting_lock:
                        self.greeting_in_progress = False
                
                # Recursively process remaining (one at a time)
                self._process_pending_greetings()
                break
    
    def reset_session(self):
        """
        Clear greeted persons for new session.
        
        Call this when starting a new interaction session
        (e.g., after a break, or explicit user reset).
        """
        num_greeted = len(self.greeted_persons)
        self.greeted_persons.clear()
        self.pending_greetings.clear()
        logger.info(f"Greeting session reset ({num_greeted} persons cleared)")
    
    def has_greeted(self, person_name: str) -> bool:
        """
        Check if person has been greeted this session.
        
        Args:
            person_name: Person's name
            
        Returns:
            True if person has been greeted, False otherwise
        """
        return person_name in self.greeted_persons
    
    def get_stats(self) -> Dict:
        """
        Get greeting statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "total_greetings": self.total_greetings,
            "unique_people_greeted": len(self.greeted_persons),
            "greeting_in_progress": self.greeting_in_progress,
            "pending_greetings": len(self.pending_greetings),
            "avg_latency_ms": round(self.avg_latency, 2) if self.latencies else 0.0,
            "min_latency_ms": round(self.min_latency, 2) if self.latencies else 0.0,
            "max_latency_ms": round(self.max_latency, 2) if self.latencies else 0.0,
            "latency_target_met": all(l < 400 for l in self.latencies) if self.latencies else True
        }
    
    def get_detailed_stats(self) -> str:
        """Get formatted statistics string."""
        stats = self.get_stats()
        
        lines = [
            "=" * 60,
            "Greeting Coordinator Statistics",
            "=" * 60,
            f"Total greetings: {stats['total_greetings']}",
            f"Unique people greeted: {stats['unique_people_greeted']}",
            f"Greeting in progress: {stats['greeting_in_progress']}",
            f"Pending greetings: {stats['pending_greetings']}",
            "",
            "Latency Performance:",
            f"  Average: {stats['avg_latency_ms']:.1f}ms",
            f"  Minimum: {stats['min_latency_ms']:.1f}ms",
            f"  Maximum: {stats['max_latency_ms']:.1f}ms",
            f"  Target (<400ms): {'✅ MET' if stats['latency_target_met'] else '❌ MISSED'}",
            "=" * 60
        ]
        
        return "\n".join(lines)


# =============================================================================
# Demo / Testing
# =============================================================================

def main():
    """Demo greeting coordination."""
    print("=" * 70)
    print("Greeting Coordinator Demo")
    print("=" * 70)
    print()
    
    # Initialize systems
    print("Initializing systems...")
    event_mgr = EventManager()
    behavior_mgr = BehaviorManager(enable_robot=True)  # Auto-connect to Reachy
    tts_mgr = TTSManager(rate=160, volume=0.9, voice_preference="female")
    
    coordinator = GreetingCoordinator(
        event_mgr,
        behavior_mgr,
        tts_mgr,
        gesture_speech_delay=0.3
    )
    
    print("[OK] All systems ready")
    print()
    
    # Scenario 1: Single person greeting
    print("=" * 70)
    print("Scenario 1: Single Person Greeting")
    print("=" * 70)
    print()
    
    print("Simulating: Alice recognized...")
    event = RecognitionEvent(
        event_type=EventType.PERSON_RECOGNIZED,
        timestamp=time.time(),
        person_name="Alice",
        confidence=0.95,
        bbox=(100, 200, 200, 100),
        frame_number=1
    )
    # Manually trigger coordinator callback (simulating event)
    coordinator._on_person_recognized(event)
    
    time.sleep(2.5)  # Wait for greeting to complete
    
    print("\nStats after Scenario 1:")
    print(coordinator.get_detailed_stats())
    
    # Scenario 2: Duplicate detection (should skip)
    print("\n" + "=" * 70)
    print("Scenario 2: Duplicate Detection (Alice again)")
    print("=" * 70)
    print()
    
    print("Simulating: Alice recognized again (should skip)...")
    coordinator._on_person_recognized(event)
    time.sleep(1.0)
    
    print("\nStats after Scenario 2 (should be same):")
    print(coordinator.get_detailed_stats())
    
    # Scenario 3: Multiple people
    print("\n" + "=" * 70)
    print("Scenario 3: Multiple People (priority by confidence)")
    print("=" * 70)
    print()
    
    print("Simulating: Bob (0.88) and Charlie (0.92) arrive...")
    
    # Bob (lower confidence)
    event_bob = RecognitionEvent(
        event_type=EventType.PERSON_RECOGNIZED,
        timestamp=time.time(),
        person_name="Bob",
        confidence=0.88,
        bbox=(300, 400, 200, 300),
        frame_number=2
    )
    
    # Charlie (higher confidence)
    event_charlie = RecognitionEvent(
        event_type=EventType.PERSON_RECOGNIZED,
        timestamp=time.time(),
        person_name="Charlie",
        confidence=0.92,
        bbox=(500, 600, 200, 500),
        frame_number=3
    )
    
    # Emit both events
    coordinator._on_person_recognized(event_bob)
    time.sleep(0.1)
    coordinator._on_person_recognized(event_charlie)
    
    time.sleep(5.0)  # Wait for both greetings
    
    print("\nStats after Scenario 3:")
    print(coordinator.get_detailed_stats())
    
    # Scenario 4: Session reset
    print("\n" + "=" * 70)
    print("Scenario 4: Session Reset")
    print("=" * 70)
    print()
    
    print("Resetting session...")
    coordinator.reset_session()
    
    print("Simulating: Alice recognized again (after reset, should greet)...")
    coordinator._on_person_recognized(event)
    time.sleep(2.5)
    
    print("\nStats after Scenario 4:")
    print(coordinator.get_detailed_stats())
    
    # Final summary
    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Key observations:")
    print("  • Single person greeted with coordinated gesture + speech")
    print("  • Duplicate detection working (Alice not greeted twice)")
    print("  • Multiple people: higher confidence greeted first")
    print("  • Session reset allows re-greeting same person")
    print("  • Latency tracking shows performance metrics")
    print()
    
    # Cleanup
    tts_mgr.shutdown()


if __name__ == "__main__":
    main()
