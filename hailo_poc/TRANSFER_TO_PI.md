# Transfer hailo_poc to Raspberry Pi - Quick Guide

## Option 1: Manual Copy via OneDrive (Simplest)

### On Windows:
```powershell
# Copy hailo_poc to OneDrive
Copy-Item -Path "C:\code\reachy-mini-dev\hailo_poc" -Destination "$env:USERPROFILE\OneDrive\reachy-mini-dev\" -Recurse -Force

# Verify files copied
dir "$env:USERPROFILE\OneDrive\reachy-mini-dev\hailo_poc"
```

### On Raspberry Pi:
```bash
# Mount OneDrive or copy from shared location
# If you have OneDrive desktop app or shared folder

# Or manually download from OneDrive web to Pi
# Then:
mkdir -p ~/reachy-mini-dev
# Extract/copy hailo_poc folder to ~/reachy-mini-dev/
```

---

## Option 2: Direct SCP Transfer (Fastest if SSH works)

### On Windows PowerShell:
```powershell
# Get Pi IP address first (check on Pi: hostname -I)
$PI_IP = "192.168.1.XXX"  # Replace with your Pi's IP

# Transfer entire folder
scp -r "C:\code\reachy-mini-dev\hailo_poc" pi@${PI_IP}:~/reachy-mini-dev/

# Enter password when prompted
```

---

## Option 3: Create Archive for Easy Transfer

### On Windows:
```powershell
# Create ZIP archive
Compress-Archive -Path "C:\code\reachy-mini-dev\hailo_poc" -DestinationPath "$env:USERPROFILE\Desktop\hailo_poc.zip"

# Now copy hailo_poc.zip to Pi via:
# - OneDrive
# - USB drive
# - Email
# - Your preferred method
```

### On Raspberry Pi:
```bash
# Extract the ZIP
cd ~
unzip hailo_poc.zip -d reachy-mini-dev/

# Or if you copied to a different location:
unzip ~/Downloads/hailo_poc.zip -d ~/reachy-mini-dev/
```

---

## Verify Transfer

### On Raspberry Pi:
```bash
# Check files are there
ls -la ~/reachy-mini-dev/hailo_poc/

# Should see:
# test_hailo.py
# test_yolo_hailo.py
# download_models.sh
# requirements.txt
# *.md files
```

---

## Quick Start After Transfer

```bash
# 1. Install Hailo software (if not already done)
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
sudo reboot

# 2. After reboot, setup Python environment
cd ~/reachy-mini-dev/hailo_poc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Get models
chmod +x download_models.sh
./download_models.sh

# 4. Test Hailo
python3 test_hailo.py

# 5. Test YOLO (once model is available)
python3 test_yolo_hailo.py
```

---

## What's Your Pi's IP Address?

Tell me and I'll give you exact SCP commands! 🚀

Or just use OneDrive - whatever's easiest for you.
