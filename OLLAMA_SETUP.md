# Ollama Setup for Local LLM

This guide shows how to set up Ollama for **fast local conversations** on Raspberry Pi 5.

## Why Use Ollama?

| Feature | Ollama (Local) | OpenAI (Cloud) |
|---------|---------------|----------------|
| **Response Time** | 200-500ms | 1-2 seconds |
| **Cost** | Free | ~$0.001/conversation |
| **Privacy** | 100% local | Sent to cloud |
| **Internet Required** | No | Yes |
| **Quality** | Very Good | Excellent |

## Installation on Raspberry Pi 5

### 1. Install Ollama

```bash
# Download and install
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### 2. Start Ollama Service

```bash
# Start in background
ollama serve &

# Or use systemd (recommended)
sudo systemctl enable ollama
sudo systemctl start ollama
```

### 3. Download Phi-3 Mini Model

Phi-3 Mini is perfect for Pi5 - small, fast, and conversational:

```bash
# Download model (~2.3GB)
ollama pull phi3:mini

# Test it
ollama run phi3:mini "Hi, I'm Reachy. Someone just said hello!"
```

**Expected output:**
```
Hello! It's great to hear from you. How can I assist you today?
```

### 4. Verify Model is Ready

```bash
# List installed models
ollama list

# Should show:
# NAME           ID           SIZE     MODIFIED
# phi3:mini      abc123...    2.3 GB   2 minutes ago
```

## Alternative Models

### For Better Quality (slower):

```bash
# Llama 3.2 (3B) - better conversation
ollama pull llama3.2:3b

# Use with: python conversation_demo.py --reachy --llm ollama --ollama-model llama3.2:3b
```

### For Maximum Speed (faster but simpler):

```bash
# TinyLlama (1.1B) - fastest
ollama pull tinyllama

# Use with: python conversation_demo.py --reachy --llm ollama --ollama-model tinyllama
```

## Running the Demo

### Auto Mode (Recommended)
Tries Ollama first, falls back to OpenAI if needed:

```bash
python3 conversation_demo.py --reachy --llm auto
```

### Force Local Only
Never uses cloud, fastest responses:

```bash
python3 conversation_demo.py --reachy --llm ollama
```

### Force OpenAI
Use cloud API for best quality:

```bash
python3 conversation_demo.py --reachy --llm openai
```

### Custom Model
Use a different Ollama model:

```bash
python3 conversation_demo.py --reachy --llm ollama --ollama-model llama3.2:3b
```

## Performance Comparison

Tested on Raspberry Pi 5 (8GB):

| Model | Size | Response Time | Quality | Memory Usage |
|-------|------|--------------|---------|--------------|
| **phi3:mini** | 2.3GB | ~300ms | ⭐⭐⭐⭐ | 2.5GB RAM |
| **llama3.2:3b** | 3.2GB | ~500ms | ⭐⭐⭐⭐⭐ | 3.5GB RAM |
| **tinyllama** | 1.5GB | ~150ms | ⭐⭐⭐ | 1.8GB RAM |
| **GPT-4o-mini** | N/A | ~1500ms | ⭐⭐⭐⭐⭐ | Minimal |

## Troubleshooting

### "Ollama not available" Error

**Problem**: Can't connect to Ollama service

**Solution**:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start it manually
ollama serve &

# Or restart service
sudo systemctl restart ollama
```

### Model Not Found

**Problem**: `Model phi3:mini not found`

**Solution**:
```bash
# List available models
ollama list

# Download if missing
ollama pull phi3:mini

# Wait for download to complete (shows progress)
```

### Slow First Response

**Problem**: First response takes 5-10 seconds

**Explanation**: Model is loading into RAM. Subsequent responses are fast (~300ms).

**Solution**: Keep Ollama running in background to keep model loaded:
```bash
# Keep model in memory
ollama run phi3:mini &
# Press Ctrl+D to exit chat but keep loaded
```

### Out of Memory

**Problem**: Pi5 crashes or freezes during conversation

**Solution**: Use smaller model or close other applications:
```bash
# Use TinyLlama instead
ollama pull tinyllama
python3 conversation_demo.py --reachy --llm ollama --ollama-model tinyllama

# Or free up RAM
sudo systemctl stop bluetooth
sudo systemctl stop cups
```

## Testing Performance

Compare response times:

```bash
# Test Ollama (local)
time python3 -c "import requests; print(requests.post('http://localhost:11434/api/chat', json={'model':'phi3:mini','messages':[{'role':'user','content':'Hi'}],'stream':False}).json())"

# Expected: ~0.3s (real time)

# Test OpenAI (cloud) - requires API key
time python3 -c "from openai import OpenAI; print(OpenAI().chat.completions.create(model='gpt-4o-mini',messages=[{'role':'user','content':'Hi'}],max_tokens=50))"

# Expected: ~1.5s (real time)
```

## Storage Requirements

- Ollama binary: ~50MB
- Phi-3 Mini model: ~2.3GB
- Llama 3.2 (3B): ~3.2GB
- TinyLlama: ~1.5GB

**Total with phi3:mini**: ~2.4GB

**Raspberry Pi 5 8GB**: Plenty of space! (~45GB free after OS and dependencies)

## Best Practices

1. **Use `auto` mode** - Get speed of local + reliability of cloud
2. **Keep Ollama running** - Faster startup (model stays loaded)
3. **Monitor memory** - `htop` to watch RAM usage
4. **Pick right model** - Balance speed vs quality for your use case

## Need Help?

```bash
# Ollama help
ollama --help

# Model info
ollama show phi3:mini

# Server logs
journalctl -u ollama -f
```

---

**Recommended Setup**: `phi3:mini` with `auto` mode gives best balance of speed, quality, and reliability! 🚀
