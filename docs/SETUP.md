# Reachy Recognizer - Development Environment Setup

**Project:** Reachy Recognizer - Human-Aware AI Companion  
**Last Updated:** 2025-10-22  
**Status:** Stories 1.1 and 1.2 Complete

---

## 📋 Overview

This document covers the complete setup and operation of the Reachy Recognizer development environment, including the Reachy Mini simulator, daemon, and web-based control interface.

---

## ✅ Story 1.1: Project Setup & Dependencies (COMPLETE)

### Python Environment

**Virtual Environment Location:** `.venv/`  
**Python Version:** 3.12+  
**Activation Command:**

```powershell
& C:/code/reachy-mini-dev/.venv/Scripts/Activate.ps1
```

### Installed Dependencies

All dependencies are managed in `pyproject.toml`:

**Core Dependencies:**
- `reachy-mini[mujoco]>=1.0.0rc5` - Reachy Mini SDK with MuJoCo simulation
- `reachy-mini-toolbox[vision]` - Vision utilities (from GitHub)
- `reachy-mini-dances-library` - Choreography library (from GitHub)

**AI/ML Libraries:**
- `openai[voice-helpers]>=2.4.0` - OpenAI API for AI-generated moves
- `librosa>=0.11.0` - Audio processing
- `pydub>=0.25.1` - Audio manipulation

**Web & API:**
- `fastapi` (installed via FastAPI)
- `uvicorn` (for running FastAPI server)
- `python-dotenv>=1.1.1` - Environment variable management

**Utilities:**
- `numpy` (dependency of CV libraries)
- `pynput>=1.8.1` - Keyboard/mouse input
- `rich>=14.2.0` - Terminal formatting

### Project Structure

```
c:\code\reachy-mini-dev\
├── .venv/                      # Virtual environment
├── docs/                       # Documentation
│   ├── prd.md                  # Product Requirements Document
│   ├── epics.md                # Epic & Story breakdown
│   ├── bmm-workflow-status.md  # Project tracking
│   └── SETUP.md                # This file
├── test-webui.py               # FastAPI web controller
├── index.html                  # Web UI for Reachy control
├── pyproject.toml              # Dependencies & project config
├── .env                        # Environment variables (create if needed)
└── README.md                   # Project readme

```

### Installation Commands

```powershell
# Activate virtual environment
& C:/code/reachy-mini-dev/.venv/Scripts/Activate.ps1

# Install dependencies (already complete)
uv sync

# Or with pip
pip install -e .
```

---

## ✅ Story 1.2: Reachy SIM Connection (COMPLETE)

### Architecture Overview

**Component Stack:**
1. **Reachy Daemon** (Simulation Mode) - Manages robot state and motor control
2. **FastAPI Backend** (`test-webui.py`) - HTTP API wrapper around Reachy SDK
3. **Web UI** (`index.html`) - Interactive browser-based controller

**Data Flow:**
```
Browser UI → FastAPI (port 8001) → Reachy SDK → Daemon → MuJoCo Simulator
```

### Starting the System

#### Step 1: Activate Virtual Environment

```powershell
& C:/code/reachy-mini-dev/.venv/Scripts/Activate.ps1
```

#### Step 2: Start Reachy Daemon (Simulation Mode)

**Command:**
```powershell
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim
```

**What it does:**
- Launches MuJoCo physics simulator
- Creates simulated Reachy Mini robot
- Starts daemon server (default: `localhost:50055` via gRPC, `localhost:8000` via HTTP)
- Opens 3D visualization window

**Options:**
```powershell
# With scene objects
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim --scene minimal

# Accept network connections (not just localhost)
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim --no-localhost-only

# Show help
uvx --from reachy-mini[mujoco] reachy-mini-daemon --help
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Troubleshooting:**
- If MuJoCo window doesn't appear: Check display settings
- If port 8000 is busy: Stop other services or use `-p` flag to change port
- On macOS: May need to use `mjpython` instead of uvx

#### Step 3: Start FastAPI Web Controller

**Command:**
```powershell
python C:\code\reachy-mini-dev\test-webui.py
```

**Alternative (with auto-reload for development):**
```powershell
uvicorn test-webui:app --host 0.0.0.0 --port 8001 --reload
```

**What it does:**
- Connects to Reachy daemon
- Initializes Reachy SDK (`ReachyMini()`)
- Starts FastAPI server on port 8001
- Optionally initializes OpenAI client (if `.env` configured)

**Expected Output:**
```
🤖 Initializing Reachy Mini...
✅ Reachy Mini initialized
✅ OpenAI API initialized (direct)
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Demo Mode (without robot):**
If daemon isn't running, the server runs in "demo mode":
```
⚠️ Could not connect to Reachy Mini: [error]
📝 Running in demo mode without robot connection
```

**Environment Variables (.env file):**
```env
OPENAI_API_KEY=your-api-key-here
LLM_BASE_URL=https://llm.your.url/v1  # Optional custom endpoint
LLM_MODEL=gpt-4o-mini                  # Optional model override
```

#### Step 4: Open Web UI

**Command:**
```powershell
# Open in default browser
start C:\code\reachy-mini-dev\index.html

# Or navigate to:
# http://localhost:8001/
```

**Web UI Features:**

1. **Pre-recorded Moves Panel**
   - Grid of available choreographed moves from `reachy-mini-dances-library`
   - Click "Play" to execute moves
   - Shows duration and description

2. **Manual Control Panel**
   - Sliders for head rotation (pitch, roll, yaw)
   - Head position control (X, Y, Z in mm)
   - Antenna control (left, right)
   - Body yaw rotation
   - Real-time control updates (50ms throttle)

3. **Generate New Move Panel**
   - AI-powered move generation using OpenAI API
   - Quick preset buttons (Curious Look, Happy Dance, Shy Peek, etc.)
   - Custom text descriptions
   - Duration control (1-16 beats)
   - Style options (smooth, antennas, body rotation, expressive)
   - Code editor with save/load functionality
   - Move analysis (complexity, line count, function name)

**Status Bar:**
- 🟢 Green indicator: Connected and ready
- 🟡 Yellow indicator: Executing move
- 🔴 Red indicator: Disconnected

### API Endpoints

**Base URL:** `http://localhost:8001`

#### GET Endpoints
- `GET /` - Serves index.html
- `GET /api/moves` - List all available pre-recorded moves

#### POST Endpoints
- `POST /api/moves/play` - Execute pre-recorded move
  ```json
  {
    "move_name": "string",
    "duration_beats": 4.0,
    "parameters": {}
  }
  ```

- `POST /api/moves/generate` - AI-generate new move code
  ```json
  {
    "description": "A curious robot looking around",
    "duration_beats": 4.0
  }
  ```

- `POST /api/moves/play-generated` - Execute generated move code
  ```json
  {
    "code": "def move_name(t_beats): ...",
    "duration_beats": 4.0
  }
  ```

- `POST /api/manual-control` - Direct position control
  ```json
  {
    "head_pitch": 0.0,
    "head_roll": 0.0,
    "head_yaw": 0.0,
    "head_x": 0.0,
    "head_y": 0.0,
    "head_z": 0.0,
    "antenna_left": 0.0,
    "antenna_right": 0.0,
    "body_yaw": 0.0
  }
  ```

- `POST /api/reset` - Reset robot to default pose

### Connection Validation

**Test Script (Direct SDK):**
```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

# Connect to simulator
with ReachyMini() as reachy:
    print("✅ Connected to Reachy!")
    
    # Test basic movement
    pose = create_head_pose(pitch=10, degrees=True)
    reachy.goto_target(head=pose, duration=1.0)
    print("✅ Movement successful!")
```

**Expected Result:** Head should tilt forward 10 degrees

### Error Handling

**Common Issues:**

1. **"Could not connect to Reachy Mini"**
   - Ensure daemon is running (`uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim`)
   - Check daemon is listening on expected port (8000)
   - Verify no firewall blocking localhost connections

2. **"Port 8001 already in use"**
   - Stop previous FastAPI instance
   - Change port: `uvicorn test-webui:app --port 8002`

3. **"OpenAI initialization failed"**
   - Not critical - server runs in demo mode for move generation
   - Add API key to `.env` file to enable AI features

4. **MuJoCo window not appearing**
   - Check graphics drivers
   - Try running without `--sim` flag to test daemon only
   - On macOS: Use `mjpython` instead of python

---

## 🎯 Testing Checklist for Stories 1.1 & 1.2

### Story 1.1: Project Setup
- [x] Virtual environment activates without errors
- [x] All dependencies installed correctly
- [x] Python 3.12+ confirmed
- [x] Project structure organized

### Story 1.2: Reachy SIM Connection
- [x] Daemon starts in simulation mode
- [x] MuJoCo window displays Reachy robot
- [x] FastAPI server connects to daemon successfully
- [x] Web UI loads and displays controls
- [x] Manual head movement works via sliders
- [x] Pre-recorded moves execute successfully
- [x] API endpoints respond correctly
- [x] Error handling works (demo mode when daemon offline)

---

## 📝 Next Steps

### Story 1.3: Camera Input Pipeline (NOT STARTED)
**Goal:** Integrate webcam capture into the FastAPI application

**Planned Implementation:**
- Add OpenCV webcam capture endpoint
- Stream frames to web UI (via WebSocket or polling)
- Validate 30 FPS capture rate
- Add camera error handling

**Required:**
- `opencv-python` (install needed)
- Camera access permissions
- WebSocket or SSE for streaming

### Story 1.4: End-to-End Integration Test
**Goal:** Validate complete pipeline (camera → detection → Reachy response)

---

## 🔧 Development Commands Reference

```powershell
# Activate environment
& C:/code/reachy-mini-dev/.venv/Scripts/Activate.ps1

# Start daemon (simulation)
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim

# Start FastAPI server
python C:\code\reachy-mini-dev\test-webui.py

# Start with auto-reload (development)
uvicorn test-webui:app --reload --port 8001

# Open web UI
start C:\code\reachy-mini-dev\index.html

# Install new dependencies
uv add <package-name>

# Run tests (when created)
pytest tests/
```

---

## 📚 Additional Resources

- **Reachy Mini SDK Docs:** `./reachy_mini/docs/python-sdk.md`
- **REST API Docs:** `./reachy_mini/docs/rest-api.md`
- **PRD:** `./docs/prd.md`
- **Epic Breakdown:** `./docs/epics.md`
- **Workflow Status:** `./docs/bmm-workflow-status.md`

---

**Document Version:** 1.0  
**Stories Covered:** 1.1 (Complete), 1.2 (Complete)  
**Next Update:** After Story 1.3 (Camera Integration)
