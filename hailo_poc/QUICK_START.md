# Quick Start - Windows to Pi Setup

## Step 1: Copy Files to OneDrive (Windows)

```powershell
# From your Windows laptop
# Copy entire hailo_poc folder to OneDrive
Copy-Item -Path "C:\code\reachy-mini-dev\hailo_poc" -Destination "C:\Users\<YourName>\OneDrive\reachy-mini-dev\" -Recurse

# Verify files synced
dir "C:\Users\<YourName>\OneDrive\reachy-mini-dev\hailo_poc"
```

## Step 2: Access on Raspberry Pi

### Option A: OneDrive via rclone
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure OneDrive
rclone config
# Name: onedrive
# Type: onedrive (Microsoft OneDrive)
# Follow browser authentication

# Mount OneDrive
mkdir -p ~/onedrive
rclone mount onedrive: ~/onedrive --daemon --vfs-cache-mode writes

# Access files
cd ~/onedrive/reachy-mini-dev/hailo_poc
ls -la
```

### Option B: Manual Copy via SSH (from Windows)
```powershell
# From Windows PowerShell
# Install pscp (part of PuTTY) or use WinSCP GUI

# Using SCP (if available)
scp -r "C:\Users\<YourName>\OneDrive\reachy-mini-dev\hailo_poc" pi@<pi-ip>:~/

# Or use WinSCP GUI:
# 1. Download WinSCP: https://winscp.net/
# 2. Connect to Pi
# 3. Drag & drop hailo_poc folder
```

### Option C: VS Code Remote SSH (BEST!)
```powershell
# 1. Install VS Code extension: "Remote - SSH"
# 2. Open VS Code
# 3. Press F1 > "Remote-SSH: Connect to Host"
# 4. Enter: pi@<raspberry-pi-ip>
# 5. Open folder: /home/pi/reachy-mini-dev
# 6. Edit code directly on Pi!
```

## Step 3: Run Tests on Pi

```bash
# SSH into Pi
ssh pi@<raspberry-pi-ip>

# Navigate to project
cd ~/reachy-mini-dev/hailo_poc
# OR if using OneDrive mount
cd ~/onedrive/reachy-mini-dev/hailo_poc

# Install Hailo software (first time only)
cd ~
git clone https://github.com/hailo-ai/hailo-rpi5-examples.git
cd hailo-rpi5-examples
./install.sh
sudo reboot

# After reboot, test Hailo
cd ~/reachy-mini-dev/hailo_poc
python3 test_hailo.py
```

## Step 4: Share Results Back to Windows

### Automatic (if using OneDrive mount)
```bash
# Results written to ~/onedrive/ auto-sync to Windows
echo "Test completed!" > ~/onedrive/reachy-mini-dev/shared/status.txt
```

### Manual (copy log files)
```bash
# On Pi: copy logs to OneDrive folder
cp test_results.log ~/onedrive/reachy-mini-dev/logs/

# On Windows: View in OneDrive folder
type C:\Users\<YourName>\OneDrive\reachy-mini-dev\logs\test_results.log
```

## Recommended Setup: VS Code Remote SSH

**Why this is best:**
- Edit code directly on Pi from Windows VS Code
- Run Python directly in integrated terminal
- No file sync delays
- Full debugging support
- Git works seamlessly

**Setup:**
1. Install "Remote - SSH" extension in VS Code
2. Connect to Pi
3. Open `/home/pi/reachy-mini-dev`
4. Work as if local!

**Screenshot of workflow:**
```
┌─────────────────────────────────┐
│   VS Code on Windows            │
│   ↓ SSH Connection              │
│   ↓ Editing files on Pi         │
│   ↓ Running Python on Pi        │
│   ↓ Viewing logs instantly      │
└─────────────────────────────────┘
```

## What's your Pi's IP address?

Once you tell me, I can give you the exact commands to connect!

```bash
# On the Pi, find IP address:
hostname -I
```
