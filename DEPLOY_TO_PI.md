# Deploy to Raspberry Pi 5 with Reachy Mini

## Quick Deployment Steps

### 1. Transfer Code to Raspberry Pi

From your Windows machine:

```powershell
# Option A: Using git (recommended)
# On Pi:
git clone https://github.com/chelleboyer/reachy-recognizer.git
cd reachy-recognizer

# Option B: Using SCP
scp -r C:\code\reachy-mini-dev pi@<raspberry-pi-ip>:/home/pi/reachy-mini-dev
```

### 2. Install Dependencies on Raspberry Pi

SSH into your Pi and run:

```bash
cd reachy-mini-dev

# Install reachy-mini SDK
pip install reachy-mini

# Install your app dependencies
pip install -r requirements.txt
# OR if using pyproject.toml:
pip install -e .

# Install face recognition (optional, if you need it)
pip install face-recognition
```

### 3. Configure for Robot Control

On the Raspberry Pi, edit `src/config/config.yaml`:

```yaml
behaviors:
  enable_robot: true  # Change from false to true

camera:
  device_id: 0  # Adjust if needed for Pi camera

system:
  reachy_host: "localhost"  # Daemon runs on same machine
  debug_display: false  # No display on headless Pi
```

### 4. Start the Reachy Mini Daemon

On the Raspberry Pi:

```bash
# The daemon will auto-detect the serial port
reachy-mini-daemon

# Or specify the port if needed
reachy-mini-daemon -p /dev/ttyUSB0

# Run in background
nohup reachy-mini-daemon > daemon.log 2>&1 &
```

### 5. Run Your Application

In a new terminal on the Pi:

```bash
cd reachy-mini-dev
python main.py
```

## Testing Workflow

### Test 1: Verify Reachy Connection

```bash
# Check if the robot is detected
ls /dev/ttyUSB* /dev/ttyACM*

# Should show something like /dev/ttyUSB0
```

### Test 2: Test Daemon

```bash
# Start daemon
reachy-mini-daemon

# You should see:
# INFO: Starting Reachy Mini daemon...
# INFO: Found Reachy Mini serial port: /dev/ttyUSB0
# INFO: Started server process
```

### Test 3: Test Your App

```bash
python main.py

# You should see:
# 🤖 Reachy Recognizer - Face Recognition & Greeting System
# ✓ Configuration loaded
# ✓ Behavior system initialized (REAL ROBOT mode)
# ✓ System ready!
```

## Remote Development from Windows

You can develop on Windows and test on Pi using VS Code Remote SSH:

1. **Install VS Code Remote - SSH extension**
2. **Connect to Pi**: `ssh pi@<raspberry-pi-ip>`
3. **Edit code on Windows, runs on Pi automatically**

Or use network mode:

```python
# On Windows, connect to Pi's daemon over network
from reachy_mini import ReachyMini
robot = ReachyMini(host="<raspberry-pi-ip>")
```

## Configuration Differences

### Windows (Development)
```yaml
behaviors:
  enable_robot: false
  
system:
  debug_display: true  # Show camera window
```

### Raspberry Pi (Production)
```yaml
behaviors:
  enable_robot: true
  
system:
  debug_display: false  # Headless operation
```

## Troubleshooting

### Issue: "Could not find port"

```bash
# Check USB devices
lsusb

# Check serial ports
ls -l /dev/ttyUSB* /dev/ttyACM*

# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Issue: "Permission denied" on serial port

```bash
sudo chmod 666 /dev/ttyUSB0
# Or add permanently to dialout group (see above)
```

### Issue: Daemon won't start

```bash
# Check if port is in use
sudo lsof | grep ttyUSB

# Kill any processes using it
sudo killall reachy-mini-daemon

# Try again
reachy-mini-daemon -p /dev/ttyUSB0
```

### Issue: Camera not working

```bash
# List cameras
v4l2-ctl --list-devices

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read())"
```

## Performance Tips

1. **Run headless** - Disable X server if not needed
2. **Use systemd service** - Auto-start daemon on boot
3. **Monitor temperature** - Ensure adequate cooling
4. **Optimize frame rate** - Lower FPS if needed

## Auto-Start on Boot (Optional)

Create systemd service:

```bash
sudo nano /etc/systemd/system/reachy-daemon.service
```

```ini
[Unit]
Description=Reachy Mini Daemon
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/reachy-mini-dev
ExecStart=/home/pi/.local/bin/reachy-mini-daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable reachy-daemon
sudo systemctl start reachy-daemon
sudo systemctl status reachy-daemon
```

## Next Steps

Once deployed and tested on the Pi:
1. ✅ Verify face recognition works with Pi camera
2. ✅ Test robot movements and gestures
3. ✅ Test voice responses (ensure audio output configured)
4. ✅ Run integration tests
5. ✅ Set up auto-start if desired

Good luck with your robot testing! 🤖
