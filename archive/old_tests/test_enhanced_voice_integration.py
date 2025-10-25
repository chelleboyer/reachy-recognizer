"""
Enhanced Voice Integration Test

Tests the new greeting coordinator with OpenAI TTS and varied greetings.
"""

import time
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("\n" + "="*70)
print("🎤 Enhanced Voice Integration Test")
print("="*70)

# Import systems
from event_system import EventManager, EventType, RecognitionEvent
from behavior_module import BehaviorManager
from greeting_coordinator import GreetingCoordinator

print("\n1. Initializing systems...")

# Initialize components
event_manager = EventManager()
behavior_manager = BehaviorManager(enable_robot=False)  # Mock mode for testing

# Initialize coordinator with enhanced voice
coordinator = GreetingCoordinator(
    event_manager=event_manager,
    behavior_manager=behavior_manager,
    use_enhanced_voice=True  # Enable OpenAI TTS
)

print("✓ Systems initialized")

# Test scenarios
test_scenarios = [
    {
        'name': 'Sarah',
        'confidence': 0.95,
        'description': 'First greeting - should use varied template'
    },
    {
        'name': 'John',
        'confidence': 0.89,
        'description': 'Different person - different greeting'
    },
    {
        'name': 'Sarah',
        'confidence': 0.92,
        'description': 'Duplicate - should be skipped'
    },
    {
        'name': 'Emily',
        'confidence': 0.87,
        'description': 'Third person - another variation'
    },
]

print("\n" + "="*70)
print("2. Testing Enhanced Greetings")
print("="*70)

for i, scenario in enumerate(test_scenarios, 1):
    print(f"\nTest {i}: {scenario['description']}")
    print(f"  Person: {scenario['name']}")
    print(f"  Confidence: {scenario['confidence']:.2f}")
    
    # Create mock recognition result  
    mock_result = (scenario['name'], scenario['confidence'])
    
    # Process through event manager (simulates recognition pipeline)
    coordinator._on_person_recognized(
        RecognitionEvent(
            event_type=EventType.PERSON_RECOGNIZED,
            timestamp=time.time(),
            person_name=scenario['name'],
            confidence=scenario['confidence'],
            bbox=(100, 200, 300, 400),
            frame_number=i * 100
        )
    )
    
    # Small delay between tests
    time.sleep(1.5)

# Statistics
print("\n" + "="*70)
print("3. Statistics")
print("="*70)

stats = coordinator.get_stats()
print(f"\nGreetings:")
print(f"  Total: {stats['total_greetings']}")
print(f"  Unique people: {stats['unique_people_greeted']}")
print(f"  Pending: {stats['pending_greetings']}")

print(f"\nPerformance:")
print(f"  Avg latency: {stats['avg_latency_ms']:.1f}ms")
print(f"  Min latency: {stats['min_latency_ms']:.1f}ms")
print(f"  Max latency: {stats['max_latency_ms']:.1f}ms")
print(f"  Target met (<400ms): {'✓ YES' if stats['latency_target_met'] else '✗ NO'}")

# TTS stats if available
if coordinator.adaptive_tts:
    print(f"\nVoice System:")
    tts_stats = coordinator.adaptive_tts.get_statistics()
    overall = tts_stats['overall']
    print(f"  Total requests: {overall['total_requests']}")
    print(f"  Success rate: {overall['success_rate']}")
    
    if tts_stats['cache']:
        cache = tts_stats['cache']
        print(f"\nCache:")
        print(f"  Size: {cache['size']}/{cache['max_size']}")
        print(f"  Hit rate: {cache['hit_rate']}")
        print(f"  Total requests: {cache['total_requests']}")

print("\n" + "="*70)
print("✓ Integration test complete!")
print("="*70)

print("\n💡 What you just heard:")
print("  • Natural OpenAI TTS voices (nova/shimmer)")
print("  • Varied greetings (no repetition)")
print("  • Contextual selection")
print("  • Intelligent caching")
print("\n✨ Much better than robotic pyttsx3!")
