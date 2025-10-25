"""
Visual test for idle manager with detailed behavior logging.
Shows what the robot WOULD do if hardware was connected.
"""

import time
from behavior_module import BehaviorManager
from idle_manager import IdleManager


def main():
    print("\n" + "="*70)
    print("🤖 Idle Manager Visual Test")
    print("="*70)
    print("\nNOTE: Running in SIMULATION mode (no robot hardware)")
    print("This shows what behaviors WOULD execute on real hardware.")
    print("="*70)
    
    # Create managers
    print("\n📋 Setup:")
    behavior_manager = BehaviorManager(enable_robot=False)
    idle_manager = IdleManager(
        behavior_manager=behavior_manager,
        activation_threshold=3.0,  # 3 seconds
        idle_interval=2.0  # Check every 2s
    )
    
    print("✓ BehaviorManager created (simulation mode)")
    print("✓ IdleManager created (3s threshold, 2s interval)")
    
    # Start idle manager
    print("\n▶️  Starting idle manager...")
    idle_manager.start()
    
    # Scenario 1: No faces detected
    print("\n" + "="*70)
    print("SCENARIO 1: No faces detected for extended period")
    print("="*70)
    
    print("\n⏱️  Time 0s: NO_FACES state begins")
    idle_manager.notify_no_faces()
    status = idle_manager.get_status()
    print(f"   Status: active={status['active']}, time_since_face={status['time_since_face']:.1f}s")
    
    for i in range(1, 9):
        time.sleep(1)
        status = idle_manager.get_status()
        
        if status['active']:
            print(f"\n⏱️  Time {i}s: 🌙 IDLE ACTIVE - Robot doing subtle drift movements")
            print(f"   (Head gently moving: random roll/pitch/yaw within ±10°)")
        else:
            remaining = status['will_activate_in']
            print(f"\n⏱️  Time {i}s: ⏳ Waiting for idle (activates in {remaining:.1f}s)")
        
        if i == 5:
            print("   💭 Robot thinking: 'Is anyone there?'")
    
    # Scenario 2: Face detected - immediate deactivation
    print("\n" + "="*70)
    print("SCENARIO 2: Face detected - idle stops immediately")
    print("="*70)
    
    print("\n👤 Face detected! (RECOGNIZED event)")
    idle_manager.notify_face_detected()
    status = idle_manager.get_status()
    print(f"   Status: active={status['active']} (idle deactivated)")
    print("   🎯 Robot now ready for greeting behavior (higher priority)")
    
    time.sleep(2)
    
    # Scenario 3: Face departs, idle resumes
    print("\n" + "="*70)
    print("SCENARIO 3: Person leaves, idle gradually resumes")
    print("="*70)
    
    print("\n👋 Person departed (NO_FACES again)")
    idle_manager.notify_no_faces()
    
    for i in range(1, 6):
        time.sleep(1)
        status = idle_manager.get_status()
        
        if status['active']:
            print(f"\n⏱️  +{i}s: 🌙 IDLE RESUMED - Back to gentle movements")
        else:
            remaining = status.get('will_activate_in', 0)
            print(f"\n⏱️  +{i}s: ⏳ Idle activates in {remaining:.1f}s")
    
    # Stop
    print("\n" + "="*70)
    print("🛑 Stopping idle manager...")
    idle_manager.stop()
    
    print("\n" + "="*70)
    print("✅ Test Complete!")
    print("="*70)
    print("\n📊 Summary:")
    print("  • Idle activates after 3s of no faces")
    print("  • Executes gentle drift movements every 2s")
    print("  • Deactivates immediately when face detected")
    print("  • Higher priority behaviors (greetings) interrupt idle")
    print("\n🔌 To see actual robot movement:")
    print("  1. Connect to Reachy hardware")
    print("  2. Use BehaviorManager(enable_robot=True)")
    print("  3. Run main.py with full integration")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
