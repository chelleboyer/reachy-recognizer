# Conversation Demo - Quick Start

## Overview

The conversation demo turns Reachy into an interactive desk assistant that:
- **Detects** when someone approaches
- **Greets** them proactively with contextual messages
- **Listens** to speech using Vosk (offline speech recognition)
- **Responds** intelligently using OpenAI GPT-4
- **Speaks** responses using OpenAI TTS
- **Integrates** with gesture control (optional)

## Architecture

```
conversation_demo.py
├─ PersonDetector (MediaPipe face detection)
├─ SpeechRecognizer (Vosk - 40MB model, offline)
├─ ConversationManager (GPT-4 + conversation history)
├─ AdaptiveTTSManager (OpenAI TTS / pyttsx3 fallback)
└─ GestureCoordinator (optional - from existing system)
```

## Prerequisites

### Required
- Python 3.11+
- OpenAI API key (in `.env` file)
- Vosk model (~40MB) in `models/vosk-model-small-en-us-0.15/`
- Microphone access
- Camera access

### Optional
- Reachy Mini robot
- Gesture recognition system

## Installation

### Windows (Development)

```powershell
# Install dependencies
pip install vosk pyaudio openai mediapipe

# Download Vosk model
New-Item -ItemType Directory -Force -Path models
Invoke-WebRequest -Uri "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip" -OutFile "models\vosk-model.zip"
Expand-Archive -Path models\vosk-model.zip -DestinationPath models -Force
```

### Raspberry Pi 5 (Production)

```bash
# Deploy from Windows using PowerShell script
.\deploy_conversation_demo.ps1 <pi-ip-address>

# OR manually:
scp -r conversation_demo.py src/ models/ .env pi@<pi-ip>:/home/pi/reachy-mini-dev/
ssh pi@<pi-ip>
cd reachy-mini-dev
pip install vosk pyaudio openai mediapipe
```

## Usage

### Basic Usage (Webcam)

```bash
python conversation_demo.py
```

### With Reachy Robot

```bash
python conversation_demo.py --reachy
```

### Headless Mode (SSH/Remote)

```bash
python conversation_demo.py --reachy --headless
```

### Custom Vosk Model Path

```bash
python conversation_demo.py --vosk-model path/to/vosk-model
```

## Command Line Options

```
--reachy              Use Reachy robot and camera
--webcam              Force use of webcam
--camera-index INT    Webcam index (default: 0)
--vosk-model PATH     Path to Vosk model directory
--headless            Run without display window
```

## How It Works

### State Machine

```
IDLE
  └─ Person detected for 2+ seconds
     └─ GREETING
        └─ Reachy speaks contextual greeting
           └─ CONVERSING
              ├─ Listen for speech (Vosk)
              ├─ Send to GPT-4
              ├─ Speak response (OpenAI TTS)
              └─ Timeout after 30s of silence
                 └─ Say goodbye → IDLE
```

### Conversation Flow

1. **Presence Detection** - MediaPipe detects face in frame for 2+ seconds
2. **Proactive Greeting** - "Good morning! I'm Reachy. What brings you by?"
3. **Speech Recognition** - Vosk converts speech to text (offline, ~200ms latency)
4. **AI Response** - GPT-4o-mini generates intelligent reply
5. **Voice Output** - OpenAI TTS speaks response naturally
6. **Context Awareness** - Maintains last 10 exchanges in memory
7. **Graceful Exit** - 30s timeout or person leaves → goodbye message

### Integration with Gestures

The conversation demo integrates with your existing gesture system:
- 👍 **Thumbs up** - "I agree" / acknowledge
- ✋ **Palm stop** - Interrupt / pause Reachy
- 👋 **Wave** - End conversation gracefully

## Configuration

### OpenAI API Key

Add to `.env` file:
```
OPENAI_API_KEY=sk-...
```

### Reachy Personality

Edit in `conversation_demo.py` → `ConversationManager.system_prompt`:
```python
self.system_prompt = """You are Reachy, a friendly desk assistant robot...
- Warm and approachable
- Concise (under 30 words)
- Helpful and curious
```

### Detection Thresholds

```python
person_present_threshold = 2.0    # seconds before greeting
no_person_timeout = 5.0           # seconds before considering person left
conversation_timeout = 30.0       # seconds of silence before goodbye
```

## Performance

### Latency Breakdown
- **Person detection**: 10-20ms (MediaPipe face)
- **Speech recognition**: 100-300ms (Vosk, depends on utterance length)
- **GPT-4 response**: 500-2000ms (depends on complexity)
- **TTS generation**: 200-500ms (OpenAI TTS)

**Total end-to-end**: ~1-3 seconds from user finishing speech to Reachy starting response

### Storage Requirements
- Vosk model: 40MB
- Python packages: ~200MB
- Total: ~250MB

### Pi5 Performance
- CPU usage: 30-50% (with face detection + speech recognition)
- Memory: ~500MB
- Temperature: Monitor for cooling needs

## Troubleshooting

### Audio Input Error (Windows)

**Symptom**: `OSError: [Errno -9999] Unanticipated host error`

**Solution**: PyAudio issues on Windows are common. Install Microsoft Visual C++ Redistributable:
```powershell
# Or use alternative: pip install sounddevice
```

**Alternative**: Test on Raspberry Pi where PyAudio works reliably.

### Vosk Model Not Found

**Symptom**: `FileNotFoundError: Vosk model not found`

**Solution**: 
1. Download from https://alphacephei.com/vosk/models
2. Extract to `models/vosk-model-small-en-us-0.15/`
3. Verify path with: `Test-Path models\vosk-model-small-en-us-0.15`

### No Person Detected

**Symptom**: Stays in IDLE state

**Solution**:
- Ensure good lighting for face detection
- Position face 2-6 feet from camera
- Check camera is working: `python -c "import cv2; print(cv2.VideoCapture(0).read())"`

### GPT-4 Not Responding

**Symptom**: "Sorry, I'm having trouble..."

**Solution**:
- Check OpenAI API key is valid in `.env`
- Verify internet connection
- Check OpenAI API status: https://status.openai.com
- Review API usage limits

### Speech Not Recognized

**Symptom**: No response to speech

**Solution**:
- Check microphone permissions
- Verify mic is default input device
- Speak clearly and wait for processing
- Check Vosk model loaded: look for "✓ Vosk model loaded" in startup

## Next Steps

### Production Deployment
1. ✅ Test on Pi5 with Reachy
2. Create systemd service for auto-start
3. Add conversation logging
4. Implement conversation analytics

### Feature Enhancements
1. Multi-language support (Vosk has models for 20+ languages)
2. Voice activity detection (reduce false triggers)
3. Emotion detection from speech tone
4. Integration with calendar/tasks
5. Privacy mode (local LLM instead of GPT-4)

### Epic 4: Full Integration
- See `docs/epic-4-conversation-integration.md` (coming soon)
- Combine with face recognition
- Add memory of previous interactions
- Multi-person conversation handling

## Resources

- **Vosk Models**: https://alphacephei.com/vosk/models
- **OpenAI API**: https://platform.openai.com/docs
- **MediaPipe Docs**: https://developers.google.com/mediapipe
- **Reachy SDK**: https://docs.pollen-robotics.com/reachy-mini/

## Support

For issues or questions:
1. Check existing issues in GitHub repo
2. Review troubleshooting section above
3. Test individual components (camera, mic, TTS)
4. Create detailed issue with logs

Happy conversing with Reachy! 🤖💬
