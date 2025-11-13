#!/bin/bash
# Hailo Installation Diagnostic Script
# Run this on Raspberry Pi to diagnose installation issues

echo "=========================================="
echo "Hailo Installation Diagnostic"
echo "=========================================="
echo ""

# Check 1: System Info
echo "1. System Information"
echo "----------------------------------------"
echo -n "OS: "
cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2
echo -n "Architecture: "
uname -m
echo -n "Kernel: "
uname -r
echo -n "Hardware: "
cat /proc/device-tree/model 2>/dev/null || echo "Unknown"
echo ""

# Check 2: PCIe Device
echo "2. PCIe Device Detection"
echo "----------------------------------------"
if lspci | grep -i hailo; then
    echo "✅ Hailo device found on PCIe bus"
else
    echo "❌ No Hailo device found"
    echo "   This could mean:"
    echo "   - AI Hat not properly seated"
    echo "   - PCIe not enabled"
    echo "   - Hardware issue"
fi
echo ""

# Check 3: Kernel Module
echo "3. Kernel Module"
echo "----------------------------------------"
if lsmod | grep hailo; then
    echo "✅ Hailo kernel module loaded"
else
    echo "❌ Hailo kernel module not loaded"
    echo "   Driver may not be installed"
fi
echo ""

# Check 4: HailoRT Package
echo "4. HailoRT Package"
echo "----------------------------------------"
if dpkg -l | grep -i hailort; then
    echo "✅ HailoRT package installed:"
    dpkg -l | grep -i hailort
else
    echo "❌ HailoRT package not found"
fi
echo ""

# Check 5: Python Package Locations
echo "5. Python Package Search"
echo "----------------------------------------"
echo "Searching for hailo_platform..."

# Check pip3 list
if pip3 list 2>/dev/null | grep -i hailo; then
    echo "✅ Found in pip3:"
    pip3 list | grep -i hailo
else
    echo "❌ Not found in pip3 list"
fi

# Check common install locations
HAILO_PATHS=(
    "/opt/hailo"
    "/usr/lib/python3/dist-packages/hailo_platform"
    "/usr/local/lib/python3*/dist-packages/hailo_platform"
    "$HOME/.local/lib/python3*/site-packages/hailo_platform"
)

echo ""
echo "Checking common installation paths:"
for path in "${HAILO_PATHS[@]}"; do
    if ls $path 2>/dev/null | head -n 1; then
        echo "✅ Found: $path"
    fi
done
echo ""

# Check 6: Python Import Test
echo "6. Python Import Test"
echo "----------------------------------------"
echo "Testing: python3 -c 'import hailo_platform'"
if python3 -c "import hailo_platform" 2>/dev/null; then
    echo "✅ Import successful!"
    python3 -c "from hailo_platform import Device; print('Device class accessible')"
else
    echo "❌ Import failed"
    echo ""
    echo "Full error:"
    python3 -c "import hailo_platform" 2>&1 || true
fi
echo ""

# Check 7: PYTHONPATH
echo "7. Python Path"
echo "----------------------------------------"
echo "PYTHONPATH: ${PYTHONPATH:-not set}"
echo ""
echo "Python sys.path:"
python3 -c "import sys; print('\n'.join(sys.path))"
echo ""

# Check 8: hailo-rpi5-examples
echo "8. Installation Repo"
echo "----------------------------------------"
if [ -d "$HOME/hailo-rpi5-examples" ]; then
    echo "✅ hailo-rpi5-examples found"
    if [ -f "$HOME/hailo-rpi5-examples/install.sh" ]; then
        echo "✅ install.sh present"
    else
        echo "⚠️  install.sh missing"
    fi
else
    echo "❌ hailo-rpi5-examples not found"
fi
echo ""

# Check 9: Device Node
echo "9. Device Node"
echo "----------------------------------------"
if ls /dev/hailo* 2>/dev/null; then
    echo "✅ Hailo device nodes found:"
    ls -l /dev/hailo*
else
    echo "❌ No /dev/hailo* devices"
fi
echo ""

# Summary
echo "=========================================="
echo "SUMMARY & RECOMMENDATIONS"
echo "=========================================="
echo ""

if ! lspci | grep -qi hailo; then
    echo "🔴 CRITICAL: No Hailo device on PCIe bus"
    echo "   → Check physical connection"
    echo "   → Reseat the AI Hat"
    echo "   → Run: sudo poweroff, then reconnect hat"
    echo ""
fi

if ! dpkg -l | grep -qi hailort; then
    echo "🔴 CRITICAL: HailoRT not installed"
    echo "   → Run: cd ~/hailo-rpi5-examples && sudo ./install.sh"
    echo ""
fi

if ! python3 -c "import hailo_platform" 2>/dev/null; then
    echo "🔴 CRITICAL: Python module not accessible"
    echo "   → Try manual installation (see below)"
    echo ""
fi

echo "=========================================="
echo "MANUAL FIX COMMANDS"
echo "=========================================="
echo ""
echo "If HailoRT is installed but Python import fails:"
echo ""
echo "# Find the wheel file"
echo "find /opt/hailo -name '*.whl' 2>/dev/null"
echo ""
echo "# Install it"
echo "sudo pip3 install /opt/hailo/hailo_platform-*.whl"
echo ""
echo "# Or add to PYTHONPATH"
echo "export PYTHONPATH=/opt/hailo:\$PYTHONPATH"
echo "python3 -c 'import hailo_platform'"
echo ""
echo "=========================================="
echo ""
