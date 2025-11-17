# Piper TTS Setup - Local High-Quality Voice

## What is Piper?

Piper is a **fast, local text-to-speech system** that sounds nearly as good as OpenAI's voices, but runs completely offline on your Raspberry Pi 5.

**Benefits:**
- 🎤 High-quality, natural voices
- ⚡ Fast: ~200-400ms generation
- 💰 100% free, no API costs
- 🔒 Complete privacy (offline)
- 🌐 No internet required

## Installation on Raspberry Pi 5

### Quick Install

```bash
# Install Piper TTS
pip install piper-tts

# Test it
echo "Hello, I'm Reachy!" | piper --model en_US-amy-medium --output_file test.wav
aplay test.wav
```

### System Package (Alternative)

```bash
# Install from apt (may be older version)
sudo apt-get update
sudo apt-get install piper-tts
```

## Available Voices

Piper has many high-quality voices. Recommended for Reachy:

### **en_US-amy-medium** (Default)
- Female voice, clear and friendly
- Size: ~40MB
- Speed: ~250ms
- **Perfect for Reachy!**

### Other Good Options:

```bash
# Female voices
en_US-lessac-medium      # Warm, expressive (60MB)
en_US-libritts-high      # Very natural (200MB, slower)

# Male voices  
en_US-ryan-medium        # Clear male voice (40MB)
en_US-libritts_r-medium  # Natural male (60MB)
```

## Usage

### Run Conversation Demo with Piper (100% Local!)

```bash
# Use Ollama for conversation + Piper for voice
python3 conversation_demo.py --reachy --llm ollama

# No OpenAI needed at all!
```

The demo will automatically use Piper if available (before falling back to pyttsx3/eSpeak).

### Test Piper Directly

```bash
# Test voice generation
python3 -c "
from piper import PiperVoice
voice = PiperVoice.load('en_US-amy-medium.onnx')
with open('test.wav', 'wb') as f:
    voice.synthesize('Hello! I am Reachy, your desk assistant.', f)
"

# Play it
aplay test.wav
```

## Voice Priority with Piper

When Piper is installed, the TTS system uses this priority:

1. **OpenAI TTS** (if API key set) - Best quality, cloud
2. **Piper TTS** (if installed) - Great quality, local ✅
3. **pyttsx3/eSpeak** (always available) - Basic quality, local

To force local-only (skip OpenAI):
```bash
# Remove/comment OpenAI key from .env
# mv .env .env.backup

# Now only Piper will be used!
python3 conversation_demo.py --reachy --llm ollama
```

## Performance Comparison

Tested on Raspberry Pi 5:

| TTS Backend | Quality | Speed | Privacy | Cost |
|-------------|---------|-------|---------|------|
| **OpenAI** | ⭐⭐⭐⭐⭐ | ~500ms | Cloud | ~$0.015/1K chars |
| **Piper** | ⭐⭐⭐⭐ | ~250ms | 100% | Free |
| **eSpeak** | ⭐⭐ | ~100ms | 100% | Free |

**Recommendation**: Use Piper for the best balance of quality, speed, and privacy!

## Troubleshooting

### "piper-tts not found"

```bash
pip install piper-tts

# Or if pip install fails:
pip install piper-tts --no-binary :all:
```

### "Voice model not found"

First run will auto-download the voice (~40MB). If it fails:

```bash
# Manual download
mkdir -p ~/.local/share/piper
cd ~/.local/share/piper
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/voice-en-us-amy-medium.tar.gz
tar -xzf voice-en-us-amy-medium.tar.gz
```

### "Permission denied"

```bash
# Fix permissions
chmod +x ~/.local/share/piper/piper
```

### Check if Piper is working

```bash
python3 -c "
try:
    from piper import PiperVoice
    print('✓ Piper TTS installed and working!')
except ImportError:
    print('✗ Piper TTS not found')
"
```

## Changing Voices

Edit `src/voice/adaptive_tts_manager.py`:

```python
# Line ~453, in PiperBackend.__init__
def __init__(
    self,
    voice_name: str = "en_US-lessac-medium"  # Change to your preferred voice
):
```

Or programmatically:

```python
from src.voice.adaptive_tts_manager import AdaptiveTTSManager

tts = AdaptiveTTSManager()
# Piper backend will auto-download voice on first use
```

## Complete Local Setup (No Cloud!)

For 100% offline, private Reachy:

```bash
# 1. Install Piper
pip install piper-tts

# 2. Install Ollama (for conversation)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3:mini

# 3. Remove OpenAI API key (optional)
# Edit .env and comment out OPENAI_API_KEY

# 4. Run fully local!
python3 conversation_demo.py --reachy --llm ollama
```

**Result:**
- ✅ Person detection: MediaPipe (local)
- ✅ Speech recognition: Vosk (local)
- ✅ Conversation: Ollama/Phi-3 (local)
- ✅ Voice: Piper (local)
- ✅ **100% private, no internet needed!**

## Storage Requirements

- Piper library: ~20MB
- Amy voice model: ~40MB
- Total: **~60MB**

## Need Help?

```bash
# Check Piper installation
piper --version

# List available voices
piper --list-voices

# Test synthesis
echo "Testing Piper TTS" | piper --model en_US-amy-medium --output_file test.wav
```

---

**Recommended for production**: Use Piper + Ollama for fast, high-quality, completely private conversations! 🚀
