# Install Hailo Software on Raspberry Pi 5

## Step 1: Prerequisites Check

```bash
# Verify you're on Raspberry Pi 5
cat /proc/device-tree/model
# Should show: Raspberry Pi 5 Model B Rev ...

# Check OS version
cat /etc/os-release
# Should be Debian 12 (Bookworm) or later

# Update system
sudo apt update && sudo apt upgrade -y
```

---

## Step 2: Install Hailo Driver & Software

### Method A: Using hailo-rpi5-examples (Recommended)

```bash
# Clone the official Hailo examples repo
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples

# Run the installer (this installs everything)
sudo ./install.sh

# This will install:
# - HailoRT (runtime library)
# - Hailo Python API (hailo_platform)
# - PCIe drivers
# - Tappas (GStreamer plugins, optional)

# Installer will prompt for reboot
sudo reboot
```

**Wait for Pi to reboot** (~30 seconds)

---

## Step 3: Verify Installation

```bash
# After reboot, SSH back in

# Check Hailo PCIe device detected
lspci | grep Hailo
# Expected output:
# 0000:01:00.0 Co-processor: Hailo Technologies Ltd. Hailo-8 AI Processor (rev 01)

# Check kernel module loaded
lsmod | grep hailo
# Expected output:
# hailo_pci    ...

# Test Python API
python3 -c "from hailo_platform import Device; print('Hailo OK')"
# Expected output:
# Hailo OK
```

---

## Step 4: Test Hardware

```bash
cd ~/reachy-mini-dev/hailo_poc
python3 test_hailo.py

# Expected output:
# ✅ Hailo Python API imported successfully
# ✅ Found 1 Hailo device(s)
#    Device: HAILO8L
#    Temperature: 45-55°C
# ✅ All tests passed!
```

---

## Troubleshooting

### "lspci: command not found"
```bash
sudo apt install pciutils
```

### "No Hailo devices found"
```bash
# Check physical connection
lspci | grep -i co-processor

# Check dmesg for errors
dmesg | grep -i hailo

# Reseat the Hailo AI Hat:
sudo poweroff
# Power off, remove hat, reattach firmly, power on
```

### "hailo-rpi5-examples not found / 404 error"
```bash
# Try alternative installation
# Download HailoRT directly from Hailo website
# Visit: https://hailo.ai/developer-zone/sw-downloads/

# Or check for updated repo location
```

### "Permission denied" errors during install
```bash
# Make sure you use sudo
cd ~/hailo-rpi5-examples
sudo ./install.sh
```

### Still can't import hailo_platform after reboot
```bash
# Check if package installed
pip3 list | grep hailo

# Try installing manually (if available)
sudo pip3 install /opt/hailo/hailo_platform-*.whl

# Or check system packages
dpkg -l | grep hailo
```

---

## Alternative: Manual HailoRT Installation

If `hailo-rpi5-examples` doesn't work, try direct HailoRT install:

```bash
# Visit Hailo Developer Zone (requires free account)
# https://hailo.ai/developer-zone/

# Download:
# - HailoRT for ARM64 (Debian package)
# - Hailo PCIe driver

# Install downloaded .deb files
sudo dpkg -i hailort_*.deb
sudo dpkg -i hailo-pcie-driver_*.deb

# Reboot
sudo reboot
```

---

## Expected Timeline

- Installation: 5-10 minutes
- Reboot: 30 seconds
- Verification: 1 minute

**Total: ~15 minutes from start to working Hailo**

---

## What Gets Installed

✅ **HailoRT** - Core runtime library
✅ **hailo_platform** - Python API
✅ **PCIe drivers** - Hardware communication
✅ **hailo-all** - Meta-package for full stack
✅ **(Optional) Tappas** - GStreamer integration

---

## After Successful Install

You'll be able to:
1. ✅ Import `hailo_platform` in Python
2. ✅ Detect Hailo device with `lspci`
3. ✅ Run `test_hailo.py` successfully
4. ✅ Load and run `.hef` models

---

## Next Steps After Install

```bash
# 1. Verify hardware
python3 test_hailo.py

# 2. Download YOLO model (see MANUAL_MODEL_DOWNLOAD.md)
./download_models_manual.sh

# 3. Test YOLO inference
python3 test_yolo_hailo.py
```

---

## Need Help?

**Where are you stuck?**
- Can't clone the repo?
- Install script fails?
- No device detected after reboot?

Share the error message and I'll help debug! 🔧
