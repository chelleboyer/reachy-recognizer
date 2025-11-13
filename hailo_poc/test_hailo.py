#!/usr/bin/env python3
"""
Test Hailo AI Hat is properly installed and working.
Run this FIRST to verify hardware setup.
"""

import sys

def test_hailo_import():
    """Test if Hailo Python API is available."""
    print("Testing Hailo import...")
    try:
        from hailo_platform import (
            HEF, 
            Device, 
            VDevice, 
            HailoSchedulingAlgorithm,
            ConfigureParams,
            InferVStreams,
            InputVStreamParams,
            OutputVStreamParams
        )
        print("✅ Hailo Python API imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Hailo API: {e}")
        print("\nInstall Hailo software:")
        print("  https://github.com/hailo-ai/hailo-rpi5-examples")
        return False


def test_hailo_device():
    """Test if Hailo device is detected."""
    print("\nTesting Hailo device detection...")
    try:
        from hailo_platform import Device, HailoSchedulingAlgorithm
        
        # Scan for devices
        devices = Device.scan()
        
        if not devices:
            print("❌ No Hailo devices found")
            print("\nTroubleshooting:")
            print("  1. Is the Hailo AI Hat properly connected?")
            print("  2. Run: lspci | grep Hailo")
            print("  3. Check dmesg for Hailo driver messages")
            return False
        
        print(f"✅ Found {len(devices)} Hailo device(s)")
        
        # Try to create device instance
        with Device() as device:
            # Try to get device info (API varies by version)
            try:
                device_info = device.get_device_architecture()
                print(f"   Architecture: {device_info}")
            except AttributeError:
                print(f"   Device ID: {devices[0].device_id if hasattr(devices[0], 'device_id') else 'Unknown'}")
            
            # Try to get temperature
            try:
                temp = device.get_chip_temperature()
                print(f"   Temperature: {temp}°C")
            except (AttributeError, Exception) as e:
                print(f"   Temperature: (not available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Device test failed: {e}")
        return False


def test_system_info():
    """Display system information."""
    print("\nSystem Information:")
    print("-" * 50)
    
    # Python version
    print(f"Python: {sys.version}")
    
    # OS info
    try:
        import platform
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Architecture: {platform.machine()}")
    except:
        pass
    
    # Check for PCIe devices (Hailo uses PCIe)
    print("\nPCIe Devices:")
    try:
        import subprocess
        result = subprocess.run(['lspci'], capture_output=True, text=True)
        hailo_devices = [line for line in result.stdout.split('\n') if 'Hailo' in line]
        if hailo_devices:
            for device in hailo_devices:
                print(f"  ✅ {device}")
        else:
            print("  ❌ No Hailo devices found in lspci")
    except:
        print("  ⚠️  Could not run lspci")


def main():
    """Run all Hailo tests."""
    print("=" * 60)
    print("🔍 Hailo AI Hat Diagnostic Test")
    print("=" * 60)
    
    test_system_info()
    print("\n" + "=" * 60)
    
    # Test 1: Import
    import_ok = test_hailo_import()
    if not import_ok:
        print("\n❌ Cannot proceed without Hailo API")
        return 1
    
    print("=" * 60)
    
    # Test 2: Device detection
    device_ok = test_hailo_device()
    if not device_ok:
        print("\n❌ Cannot proceed without Hailo device")
        return 1
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Hailo is ready to use.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
