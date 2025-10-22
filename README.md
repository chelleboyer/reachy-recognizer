# Reachy Recognizer

**Human-Aware AI Companion** - A face recognition system that enables Reachy Mini robot to recognize and interact with people through personalized greetings and responsive behaviors.

## Overview

Reachy Recognizer transforms the Reachy Mini robot into an aware, interactive companion that can:
- Detect and recognize faces from webcam input in real-time
- Greet known individuals by name with coordinated gestures and speech
- Respond appropriately to unknown visitors
- Maintain natural idle behaviors when alone

## Features

- **Real-Time Face Recognition**: Fast, accurate face detection and recognition using OpenCV and face_recognition library
- **Personalized Interactions**: Greets recognized individuals by name with TTS
- **Behavioral Responses**: Context-aware gestures and head movements
- **Web-Based Control**: FastAPI server with browser-based UI for testing and control
- **MuJoCo Simulation**: Test and develop without physical hardware

## Quick Start

### Prerequisites

- Python 3.12+
- Reachy Mini SDK with MuJoCo simulator
- Webcam (for face detection)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pollen-robotics/reachy_mini.git
   cd reachy_mini
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

### Running the System

#### Option 1: Web Interface (Manual Control)

1. **Start the Reachy daemon in simulation mode:**
   ```bash
   uvx reachy-mini --daemon start
   ```

2. **Launch the web interface:**
   ```bash
   python test-webui.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:8001`

#### Option 2: Integration Test (Camera + Face Detection)

**End-to-end test combining camera capture, face detection, and Reachy control:**

1. **Start the Reachy daemon:**
   ```bash
   uvx reachy-mini --daemon start
   ```

2. **Start the FastAPI server:**
   ```bash
   python test-webui.py
   ```

3. **Run the integration test (in a new terminal):**
   ```bash
   python e2e_integration_test.py
   ```

This will:
- Open a camera window with live feed
- Detect faces using OpenCV Haar cascade
- Command Reachy to look at the camera when a face is detected
- Return Reachy to neutral position when no face is detected
- Run for 2 minutes (or press 'q'/'ESC' to stop early)
- Display real-time statistics and event logs

**Short test (30 seconds):**
```bash
python e2e_integration_test.py --duration 30
```

**Use different camera:**
```bash
python e2e_integration_test.py --camera 1
```

## Project Structure

```
reachy-mini-dev/
├── docs/                     # Documentation and project management
│   ├── prd.md               # Product Requirements Document
│   ├── epics.md             # Epic breakdown with 16 stories
│   └── stories/             # Individual story implementation files
├── tests/                    # Test suite
├── reachy_mini/             # Reachy Mini SDK source
├── reachy_mini_toolbox/     # Vision and utility modules
├── examples/                # Example scripts and demos
├── test-webui.py           # FastAPI server for web control
├── index.html              # Web-based control interface
└── pyproject.toml          # Dependency configuration
```

## Development

See [SETUP.md](SETUP.md) for detailed development environment setup instructions.

### Key Dependencies

- **reachy-mini**: Robot SDK with MuJoCo simulation support (>=1.0.0rc5)
- **opencv-python**: Computer vision and camera input (>=4.8.0)
- **face-recognition**: Face detection and recognition (>=1.3.0)
- **fastapi**: Web API framework (>=0.100.0)
- **pyttsx3**: Text-to-speech synthesis (>=2.90)
- **openai**: AI-powered move generation (>=2.4.0)

### Running Tests

```bash
pytest tests/
```

## Documentation

- **[Product Requirements](docs/prd.md)**: Complete PRD with 5 milestones and 8 functional requirements
- **[Epic Breakdown](docs/epics.md)**: 16 stories across 4 epics
- **[Setup Guide](SETUP.md)**: Detailed development environment setup
- **[TTS Setup](TTS_SETUP_GUIDE.md)**: Text-to-speech configuration

## Architecture

The system consists of 5 main subsystems:
1. **Camera Input Pipeline**: Webcam capture with OpenCV
2. **Vision Engine**: Face detection and recognition
3. **Behavior Engine**: Response coordination (gestures + speech)
4. **Configuration System**: YAML-based settings management
5. **Monitoring & Analytics**: Performance logging and metrics

## Contributing

This project follows the BMAD (Business Method Agile Development) workflow for structured development:

1. Stories are created from epic breakdown
2. Each story includes acceptance criteria and tasks
3. Implementation follows strict test-driven development
4. All changes are tracked and documented

## License

See LICENSE files in respective subdirectories.

## Contact

- **Project**: Reachy Mini Robot Platform
- **Organization**: Pollen Robotics
- **Repository**: https://github.com/pollen-robotics/reachy_mini

---

**Status**: Active Development - Epic 1 Foundation (4 stories) ✓