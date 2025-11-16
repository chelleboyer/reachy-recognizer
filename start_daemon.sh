#!/bin/bash
# Start Reachy Mini Daemon
# Usage: ./start_daemon.sh

echo "🤖 Starting Reachy Mini Daemon"
echo "============================================================"
echo ""

# Check if reachy-mini is installed
echo "Checking for reachy-mini SDK..."
if python3 -c "import reachy_mini" 2>/dev/null; then
    echo "✓ reachy-mini SDK found"
else
    echo "❌ reachy-mini SDK not found"
    echo "   Install with: pip install reachy-mini"
    exit 1
fi

# Check for serial ports
echo ""
echo "Checking for Reachy Mini on serial ports..."
python3 -c "
import serial.tools.list_ports
ports = list(serial.tools.list_ports.comports())
if ports:
    print('Available serial ports:')
    for p in ports:
        print(f'  {p.device}: {p.description}')
else:
    print('⚠️  No serial ports found')
    print('   Make sure Reachy Mini is connected via USB')
"

# Start daemon
echo ""
echo "Starting daemon..."
echo "Press Ctrl+C to stop"
echo ""

# Run the daemon (it will auto-detect the port)
uvx --from reachy-mini reachy-mini-daemon
