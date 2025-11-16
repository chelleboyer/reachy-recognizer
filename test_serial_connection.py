"""Test serial connection to Reachy Mini on COM3"""
import serial
import serial.tools.list_ports
import sys

print("🔍 Checking serial ports...")
print("\nAvailable ports:")
ports = list(serial.tools.list_ports.comports())
for port in ports:
    print(f"  - {port.device}: {port.description}")
    print(f"    Manufacturer: {port.manufacturer}")
    print(f"    Product: {port.product}")
    print(f"    Serial Number: {port.serial_number}")
    print(f"    VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid else "")
    print()

print("\n🔌 Attempting to connect to COM3...")
try:
    # Try to open COM3 with typical settings
    ser = serial.Serial(
        port='COM3',
        baudrate=115200,  # Common baudrate for Reachy
        timeout=1,
        write_timeout=1
    )
    print("✅ Successfully opened COM3!")
    print(f"   Baudrate: {ser.baudrate}")
    print(f"   Bytesize: {ser.bytesize}")
    print(f"   Parity: {ser.parity}")
    print(f"   Stopbits: {ser.stopbits}")
    print(f"   Timeout: {ser.timeout}")
    
    # Try to read some data
    print("\n📖 Attempting to read data (2 second timeout)...")
    ser.timeout = 2
    data = ser.read(100)
    if data:
        print(f"   Received {len(data)} bytes: {data}")
    else:
        print("   No data received (this might be normal)")
    
    ser.close()
    print("\n✅ Connection test successful!")
    print("   The port is accessible and working.")
    
except serial.SerialException as e:
    print(f"\n❌ Failed to open COM3: {e}")
    print("\nPossible causes:")
    print("  1. Port is already in use by another program")
    print("  2. Insufficient permissions (try running as Administrator)")
    print("  3. Driver issue (CH343 driver may need reinstall)")
    print("  4. Hardware issue (try unplugging and replugging USB)")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    sys.exit(1)
