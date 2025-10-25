"""
Behavior + Speech Integration Demo - Story 3.2

Demonstrates coordinated behaviors with voice greetings.
Combines Story 3.1 (behaviors) with Story 3.2 (TTS).

This shows how Reachy responds to events with both movement and speech.
"""

import time
from behavior_module import (
    BehaviorManager,
    greeting_wave,
    curious_tilt,
    create_idle_drift,
    neutral_pose
)
from tts_module import TTSManager, GreetingType

print("=" * 70)
print("Reachy Behavior + Speech Integration Demo")
print("=" * 70)
print()

# Initialize managers
print("Initializing systems...")
behavior_mgr = BehaviorManager(reachy=None, enable_robot=False)  # Simulation mode
tts_mgr = TTSManager(rate=160, volume=0.9, voice_preference="female")

print(f"Behavior Manager: ✓ (simulation mode)")
print(f"TTS Manager: ✓ (engine available: {tts_mgr.engine_available})")
print()

# Demo scenarios
print("=" * 70)
print("Scenario 1: Recognized Person Arrives")
print("=" * 70)
print("\nEvent: Alice is recognized")
print("Response: greeting_wave behavior + personalized greeting\n")

# Execute behavior and speech together
behavior_mgr.execute_behavior(greeting_wave)
tts_mgr.speak_greeting(GreetingType.RECOGNIZED, "Alice")

time.sleep(2.0)

# Show results
print(f"\nBehavior status:")
print(f"  Behaviors executed: {behavior_mgr.behaviors_executed}")
print(f"  Current behavior: {behavior_mgr.current_behavior.name if behavior_mgr.current_behavior else 'None'}")
print(f"\nTTS status:")
print(f"  Speeches queued: {tts_mgr.speeches_queued}")
print(f"  Speeches spoken: {tts_mgr.speeches_spoken}")

# Scenario 2
print("\n" + "=" * 70)
print("Scenario 2: Unknown Person Detected")
print("=" * 70)
print("\nEvent: Unknown face detected")
print("Response: curious_tilt behavior + unknown greeting\n")

behavior_mgr.execute_behavior(curious_tilt)
tts_mgr.speak_greeting(GreetingType.UNKNOWN)

time.sleep(2.0)

print(f"\nBehavior status:")
print(f"  Behaviors executed: {behavior_mgr.behaviors_executed}")
print(f"\nTTS status:")
print(f"  Speeches queued: {tts_mgr.speeches_queued}")
print(f"  Speeches spoken: {tts_mgr.speeches_spoken}")

# Scenario 3
print("\n" + "=" * 70)
print("Scenario 3: Multiple People Arrive")
print("=" * 70)
print("\nEvent: Bob, Charlie, and Diana arrive")
print("Response: greeting_wave + personalized greeting for each\n")

for name in ["Bob", "Charlie", "Diana"]:
    print(f"Greeting {name}...")
    behavior_mgr.execute_behavior(greeting_wave)
    tts_mgr.speak_greeting(GreetingType.RECOGNIZED, name)
    time.sleep(1.5)

print(f"\nBehavior status:")
print(f"  Behaviors executed: {behavior_mgr.behaviors_executed}")
print(f"  Behaviors interrupted: {behavior_mgr.behaviors_interrupted}")
print(f"\nTTS status:")
print(f"  Speeches queued: {tts_mgr.speeches_queued}")
print(f"  Speeches spoken: {tts_mgr.speeches_spoken}")

# Scenario 4
print("\n" + "=" * 70)
print("Scenario 4: Person Departs")
print("=" * 70)
print("\nEvent: Alice leaves")
print("Response: neutral_pose behavior + goodbye\n")

behavior_mgr.execute_behavior(neutral_pose)
tts_mgr.speak_greeting(GreetingType.DEPARTED, "Alice")

time.sleep(1.5)

print(f"\nBehavior status:")
print(f"  Behaviors executed: {behavior_mgr.behaviors_executed}")
print(f"\nTTS status:")
print(f"  Speeches queued: {tts_mgr.speeches_queued}")
print(f"  Speeches spoken: {tts_mgr.speeches_spoken}")

# Scenario 5: High Priority Interruption
print("\n" + "=" * 70)
print("Scenario 5: Priority Override")
print("=" * 70)
print("\nEvent: During idle drift, VIP is recognized")
print("Response: Interrupt low-priority behavior, greet VIP\n")

# Start low-priority idle
print("Starting idle_drift (priority 1)...")
behavior_mgr.execute_behavior(create_idle_drift())
time.sleep(0.5)

# Interrupt with high-priority greeting
print("VIP recognized! Interrupting with greeting_wave (priority 8)...")
behavior_mgr.execute_behavior(greeting_wave)
tts_mgr.speak_greeting(GreetingType.RECOGNIZED, "VIP")

time.sleep(2.0)

print(f"\nBehavior status:")
print(f"  Behaviors executed: {behavior_mgr.behaviors_executed}")
print(f"  Behaviors interrupted: {behavior_mgr.behaviors_interrupted}")
print(f"\nTTS status:")
print(f"  Speeches queued: {tts_mgr.speeches_queued}")
print(f"  Speeches spoken: {tts_mgr.speeches_spoken}")

# Final Statistics
print("\n" + "=" * 70)
print("Final Statistics")
print("=" * 70)

behavior_stats = {
    "behaviors_executed": behavior_mgr.behaviors_executed,
    "behaviors_interrupted": behavior_mgr.behaviors_interrupted,
    "current_behavior": behavior_mgr.current_behavior.name if behavior_mgr.current_behavior else "None"
}

tts_stats = tts_mgr.get_stats()

print("\nBehavior System:")
for key, value in behavior_stats.items():
    print(f"  {key}: {value}")

print("\nTTS System:")
for key, value in tts_stats.items():
    print(f"  {key}: {value}")

# Performance Summary
print("\n" + "=" * 70)
print("Performance Summary")
print("=" * 70)

success_rate = (behavior_mgr.behaviors_executed / 
                (behavior_mgr.behaviors_executed + behavior_mgr.behaviors_interrupted)) * 100
speech_completion = (tts_stats['speeches_spoken'] / 
                     tts_stats['speeches_queued']) * 100 if tts_stats['speeches_queued'] > 0 else 0

print(f"\nBehavior success rate: {success_rate:.1f}%")
print(f"Speech completion rate: {speech_completion:.1f}%")
print(f"Total interactions: {behavior_mgr.behaviors_executed}")
print(f"TTS errors: {tts_stats['errors']}")

print("\n✅ Integration demo complete!")
print("\nKey observations:")
print("  • Behaviors and speech execute independently (non-blocking)")
print("  • High-priority behaviors can interrupt low-priority ones")
print("  • TTS queues speech requests for smooth delivery")
print("  • Both systems track statistics for monitoring")
print()

# Cleanup
tts_mgr.shutdown()
