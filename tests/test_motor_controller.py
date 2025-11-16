"""Direct test of ReachyMiniPyControlLoop to diagnose the issue"""
import sys

print("🔍 Testing reachy_mini_motor_controller import...")
try:
    from reachy_mini_motor_controller import ReachyMiniPyControlLoop
    print("✅ Successfully imported ReachyMiniPyControlLoop")
except ImportError as e:
    print(f"❌ Failed to import: {e}")
    sys.exit(1)

print("\n🔌 Testing connection to COM3...")
print("Parameters:")
print("  - serialport: COM3")
print("  - wireless: False")
print("  - cmd_pub_period: 0.01")
print("  - state_pub_period: 0.1")
print("  - stats_pub_period: None")

try:
    control_loop = ReachyMiniPyControlLoop(
        "COM3",
        False,  # wireless
        0.01,   # cmd_pub_period
        0.1,    # state_pub_period  
        None,   # stats_pub_period
    )
    print("\n✅ Successfully created ReachyMiniPyControlLoop!")
    print("   Connection established to Reachy Mini")
    
except RuntimeError as e:
    print(f"\n❌ RuntimeError: {e}")
    print("\nDiagnostic steps:")
    print("1. Check if another program has COM3 open")
    print("2. Try unplugging and replugging the USB cable")
    print("3. Check Device Manager for driver issues (yellow exclamation)")
    print("4. Verify the robot is powered on")
    print("5. Try a different USB port")
    
    # Check if port exists
    import serial.tools.list_ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    print(f"\n📋 Available COM ports: {ports}")
    if "COM3" in ports:
        print("   ✓ COM3 is detected by the system")
    else:
        print("   ✗ COM3 not found!")
        
except Exception as e:
    print(f"\n❌ Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
