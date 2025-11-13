# VS Code Remote SSH Setup - Windows to Raspberry Pi

## Prerequisites
- ✅ VS Code installed on Windows
- ✅ Raspberry Pi 5 connected to same network as Windows laptop
- ✅ SSH enabled on Raspberry Pi

## Step 1: Enable SSH on Raspberry Pi (if not already)

```bash
# On the Pi (via keyboard/monitor or existing SSH)
sudo raspi-config
# Select: Interface Options > SSH > Enable

# Or enable directly:
sudo systemctl enable ssh
sudo systemctl start ssh

# Find Pi's IP address
hostname -I
# Example: 192.168.1.100
```

## Step 2: Install VS Code Remote SSH Extension (Windows)

1. Open VS Code
2. Click Extensions icon (or Ctrl+Shift+X)
3. Search: "Remote - SSH"
4. Install: "Remote - SSH" by Microsoft

## Step 3: Connect to Raspberry Pi

### Method A: Quick Connect
1. Press `F1` (or Ctrl+Shift+P)
2. Type: "Remote-SSH: Connect to Host"
3. Enter: `pi@<raspberry-pi-ip>`
   - Example: `pi@192.168.1.100`
4. Enter password when prompted (default: `raspberry`)
5. VS Code will reload connected to Pi!

### Method B: Save SSH Config (Recommended)
1. Press `F1`
2. Type: "Remote-SSH: Open SSH Configuration File"
3. Select: `C:\Users\<YourName>\.ssh\config`
4. Add this:

```
Host reachy-pi
    HostName <raspberry-pi-ip>
    User pi
    ForwardAgent yes
```

5. Save file
6. Press `F1` > "Remote-SSH: Connect to Host" > Select "reachy-pi"

## Step 4: Open Project on Pi

1. After connected, click "Open Folder"
2. Navigate to: `/home/pi/reachy-mini-dev`
3. Click OK
4. VS Code now shows Pi's files!

## Step 5: Verify Setup

1. Open integrated terminal (Ctrl+`)
2. You're now in a shell ON THE PI!
3. Test:

```bash
# Check you're on the Pi
hostname
# Should show: raspberrypi (or your Pi's hostname)

# Check Python
python3 --version

# Navigate to hailo_poc
cd hailo_poc
ls -la
```

## Step 6: Develop & Test

### Edit code in VS Code (Windows UI, Pi filesystem)
- Open `test_hailo.py`
- Make changes
- Files save directly to Pi

### Run code in Terminal (executes on Pi)
```bash
python3 test_hailo.py
```

### Use VS Code features:
- ✅ IntelliSense (Python autocomplete)
- ✅ Debugging (set breakpoints!)
- ✅ Git integration
- ✅ Extensions (install Python extension on Pi)

## Troubleshooting

### "Could not establish connection"
```powershell
# Test SSH from Windows PowerShell first
ssh pi@<raspberry-pi-ip>
# If this works, VS Code should work too
```

### "Permission denied"
- Check username is `pi`
- Check password (default: `raspberry`)
- Consider setting up SSH keys (see below)

### "Host key verification failed"
```powershell
# Remove old SSH key
ssh-keygen -R <raspberry-pi-ip>
# Try connecting again
```

## Optional: SSH Key Authentication (No Password!)

### On Windows PowerShell:
```powershell
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519
# Press Enter for all prompts (accept defaults)

# Copy key to Pi
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh pi@<raspberry-pi-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

Now you can connect without password!

## Benefits of This Setup

✅ **No file sync delays** - Edit directly on Pi
✅ **Run Python on Pi hardware** - Test with real Hailo/Reachy
✅ **Full debugging** - Set breakpoints, step through code
✅ **Git integration** - Commit from VS Code
✅ **Extensions work** - Python, Pylance, etc. run on Pi
✅ **Windows UI** - Comfortable development environment

## Your Workflow

```
1. Open VS Code on Windows
2. Connect to Pi (F1 > Remote-SSH)
3. Edit code in VS Code
4. Run in integrated terminal (executes on Pi)
5. See output instantly
6. Commit with Git
7. Done! 🎉
```

No OneDrive needed - you're working directly on Pi!

---

**Ready to connect?** 

What's your Raspberry Pi's IP address? I'll give you the exact connection string!
