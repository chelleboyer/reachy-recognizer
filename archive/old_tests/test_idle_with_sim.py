"""
Test idle manager with actual Reachy SIM connection.
This will make the robot move in the simulator!
"""

import time
from reachy_mini import ReachyMini
from behavior_module import BehaviorManager
from idle_manager import IdleManager


def main():
    print("\n" + "="*70)
    print("🤖 Idle Manager + Reachy SIM Test")
    print("="*70)
    
    print("\n📡 Connecting to Reachy SIM...")
    print("   (Make sure: uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim is running)")
    
    # Create managers with real robot connection
    print("\n📋 Creating managers...")
    
    with BehaviorManager(enable_robot=True) as behavior_manager:
        print(f"✓ BehaviorManager created")
        print(f"   Robot enabled: {behavior_manager.enable_robot}")
        print(f"   Reachy connected: {behavior_manager.reachy is not None}")
        
        if not behavior_manager.enable_robot:
            print("\n⚠️  Running in SIMULATION mode (no robot)")
            print("   Start simulator: uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim")
            return
        
        idle_manager = IdleManager(
            behavior_manager=behavior_manager,
            activation_threshold=3.0,  # 3 seconds
            idle_interval=2.5  # Check every 2.5s
        )
        print("✓ IdleManager created")
        
        # Start idle manager
        print("\n▶️  Starting idle manager...")
        idle_manager.start()
        
        # Test 1: Let idle behaviors activate
        print("\n" + "="*70)
        print("TEST 1: Watch robot enter idle state (3s)")
        print("="*70)
        print("\n⏱️  Starting NO_FACES countdown...")
        print("   👀 Watch the simulator - robot will start drifting!")
        
        idle_manager.notify_no_faces()
        
        for i in range(10):
            time.sleep(1)
            status = idle_manager.get_status()
            
            if status['active']:
                print(f"   {i+1}s: 🌙 IDLE - Robot doing gentle movements")
            else:
                remaining = status.get('will_activate_in', 0)
                print(f"   {i+1}s: ⏳ Idle activates in {remaining:.1f}s")
        
        # Test 2: Interrupt with face detection
        print("\n" + "="*70)
        print("TEST 2: Face detected - idle stops")
        print("="*70)
        print("\n👤 Simulating face detection...")
        idle_manager.notify_face_detected()
        status = idle_manager.get_status()
        print(f"   ✓ Idle deactivated: {not status['active']}")
        
        time.sleep(2)
        
        # Test 3: Return to idle
        print("\n" + "="*70)
        print("TEST 3: Person leaves - idle resumes")
        print("="*70)
        print("\n👋 Person departed...")
        print("   👀 Robot will resume idle movements")
        
        idle_manager.notify_no_faces()
        
        for i in range(8):
            time.sleep(1)
            status = idle_manager.get_status()
            
            if status['active']:
                print(f"   {i+1}s: 🌙 Idle active - gentle drift")
            else:
                remaining = status.get('will_activate_in', 0)
                print(f"   {i+1}s: ⏳ {remaining:.1f}s until idle")
        
        # Cleanup
        print("\n" + "="*70)
        print("🛑 Stopping...")
        idle_manager.stop()
        
        print("\n" + "="*70)
        print("✅ Test Complete!")
        print("="*70)
        print("\nDid you see the robot head moving in the simulator?")
        print("The idle behaviors create subtle, natural movements.")
        print("="*70 + "\n")


if __name__ == "__main__":
    main()
