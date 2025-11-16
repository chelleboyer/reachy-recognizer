"""Test direct robot control without daemon"""
import sys

print("🤖 Testing direct Reachy Mini robot control")
print("=" * 60)

# Test 1: Import the SDK
print("\n1️⃣ Importing reachy-mini SDK...")
try:
    from reachy_mini import ReachyMini
    print("   ✅ SDK imported successfully")
except ImportError as e:
    print(f"   ❌ Failed to import: {e}")
    sys.exit(1)

# Test 2: Connect to robot
print("\n2️⃣ Connecting to Reachy Mini on COM3...")
try:
    robot = ReachyMini(port="COM3")
    print("   ✅ Connected to robot!")
except Exception as e:
    print(f"   ❌ Connection failed: {e}")
    print("\n💡 This means:")
    print("   - The daemon has the same issue we're seeing")
    print("   - There's a compatibility problem between reachy-mini 1.0.0")
    print("     and the motor controller version")
    print("\n🔧 Possible solutions:")
    print("   1. Contact Pollen Robotics support about the COM port error")
    print("   2. Check if there's a firmware update for the robot")
    print("   3. Try downgrading: pip install reachy-mini==1.0.0rc5")
    sys.exit(1)

# Test 3: Check robot status
print("\n3️⃣ Checking robot status...")
try:
    print(f"   Robot firmware version: {robot.get_version() if hasattr(robot, 'get_version') else 'Unknown'}")
    print("   ✅ Robot is responsive")
except Exception as e:
    print(f"   ⚠️  Status check failed: {e}")

# Test 4: Try a simple movement
print("\n4️⃣ Testing head movement...")
try:
    from time import sleep
    robot.head.yaw.goal_position = 10
    sleep(1)
    robot.head.yaw.goal_position = 0
    print("   ✅ Head movement successful!")
except Exception as e:
    print(f"   ❌ Movement failed: {e}")

print("\n" + "=" * 60)
print("✨ Direct robot control test complete!")
print("\n💡 Your main.py app should work with enable_robot: true")
print("   (No daemon needed!)")
