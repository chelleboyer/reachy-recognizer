# Quick Start: Conversation Demo on Pi

## On Raspberry Pi 5

```bash
# 1. Pull latest code from GitHub
cd ~/reachy-mini-dev
git pull origin main

# 2. Make setup script executable
chmod +x setup_conversation_demo_pi.sh

# 3. Download Vosk model (~40MB)
mkdir -p models
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
cd ..

# 4. Run setup script (installs dependencies)
./setup_conversation_demo_pi.sh

# 5. Start Reachy daemon (in separate terminal or background)
reachy-mini-daemon
# OR: nohup reachy-mini-daemon > daemon.log 2>&1 &

# 6. Run conversation demo
python3 conversation_demo.py --reachy --headless
```

## What the conversation demo does:
- ✅ Detects when someone approaches (face detection)
- ✅ Greets them proactively
- ✅ Listens to speech (Vosk offline recognition)
- ✅ Responds intelligently (OpenAI GPT-4)
- ✅ Speaks responses (OpenAI TTS)
- ✅ Integrates with gestures (thumbs up, palm stop, wave)

## Press Ctrl+C to stop

## Troubleshooting:
- If Vosk model fails: Model must be in `models/vosk-model-small-en-us-0.15/`
- If mic not working: Check `arecord -l` for microphone
- If camera fails: Check Reachy daemon is running
- If no OpenAI responses: Check `.env` has OPENAI_API_KEY

See CONVERSATION_DEMO_README.md for full documentation.
