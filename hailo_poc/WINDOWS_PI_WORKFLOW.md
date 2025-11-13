# Development Workflow - Windows Laptop + Raspberry Pi 5

## Setup Overview

```
┌─────────────────────────────────┐
│   Windows Laptop (Your Dev)    │
│   - VS Code                     │
│   - Git repo                    │
│   - OneDrive sync               │
└────────────┬────────────────────┘
             │ OneDrive
             │ File Sharing
┌────────────▼────────────────────┐
│   Raspberry Pi 5                │
│   - Hailo AI Hat                │
│   - Reachy Mini (USB/network)   │
│   - Python runtime              │
│   - OneDrive access             │
└─────────────────────────────────┘
```

## Development Flow

### 1. Windows Laptop (Code Development)
- Edit code in VS Code
- Test logic (without hardware)
- Commit to Git
- Files auto-sync to OneDrive

### 2. Raspberry Pi 5 (Hardware Testing)
- Access code from OneDrive
- Run with real Reachy hardware
- Test Hailo inference
- Share logs back via OneDrive

## File Sync Strategy

### Option A: OneDrive Direct Mount (Recommended)
```bash
# On Raspberry Pi, install rclone for OneDrive access
curl https://rclone.org/install.sh | sudo bash

# Configure OneDrive
rclone config
# Follow prompts to connect your OneDrive account

# Create mount point
mkdir -p ~/onedrive

# Mount OneDrive
rclone mount onedrive: ~/onedrive --daemon

# Access files
cd ~/onedrive/reachy-mini-dev/hailo_poc
```

### Option B: Manual Sync
```bash
# Copy from OneDrive to local
cp -r ~/onedrive/reachy-mini-dev ~/reachy-mini-dev

# Work locally
cd ~/reachy-mini-dev

# Copy results back to OneDrive
cp logs/*.log ~/onedrive/reachy-mini-dev/logs/
```

## Testing Workflow

### On Windows (Development)
```powershell
# Edit code
code hailo_poc/test_yolo_hailo.py

# Commit changes
git add .
git commit -m "Update YOLO test script"

# Files auto-sync to OneDrive
```

### On Raspberry Pi (Testing)
```bash
# Update code from OneDrive
cd ~/onedrive/reachy-mini-dev/hailo_poc
# OR
rsync -av ~/onedrive/reachy-mini-dev/ ~/reachy-mini-dev/

# Run tests
python3 test_hailo.py
python3 test_yolo_hailo.py

# Results automatically sync back to OneDrive
```

## Recommended Directory Structure

```
OneDrive/
└── reachy-mini-dev/          # Synced folder
    ├── hailo_poc/            # Hailo PoC code
    ├── src/                  # Main source code
    ├── models/               # .hef model files (might be large!)
    ├── logs/                 # Test logs (sync back to Windows)
    ├── data/                 # Face embeddings database
    └── shared/               # Share files both ways
        ├── test_results.md
        └── performance.json
```

## Tips

### Large Files Warning
- **Model files** (.hef) can be large (50-200 MB)
- Consider storing models only on Pi
- Share model metadata/config via OneDrive instead

### Real-time Collaboration
1. **Windows**: Edit code, commit to Git
2. **OneDrive**: Auto-sync to cloud
3. **Pi**: Pull changes, test with hardware
4. **Pi**: Write results to `shared/` folder
5. **Windows**: View results, iterate

## Remote Access Options

### SSH into Pi from Windows
```powershell
# Install SSH client (built into Windows 10+)
ssh pi@<raspberry-pi-ip>

# Or use VS Code Remote SSH extension
# File > New Window > Remote-SSH > Connect to Host
```

### VS Code Remote Development
1. Install "Remote - SSH" extension
2. Connect to Pi via SSH
3. Edit code directly on Pi in VS Code
4. No need for OneDrive sync!

## Next Steps

1. ✅ Setup OneDrive access on Pi (or use VS Code Remote SSH)
2. ⏳ Copy hailo_poc folder to Pi
3. ⏳ Run hardware tests
4. ⏳ Share results back to Windows via OneDrive

## Which approach do you prefer?

- **A) OneDrive rclone mount** - Automatic sync
- **B) Manual copy/paste** - Full control
- **C) VS Code Remote SSH** - Best developer experience (my recommendation!)
