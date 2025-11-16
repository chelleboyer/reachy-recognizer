# Conversation Demo - Performance & Responsiveness Guide

## Key Optimizations Applied

### 1. **Immediate Physical Reactions** ⚡
The demo now provides instant visual feedback through Reachy's movements:

- **Person Detection** (0.0s): Quick head nod acknowledgment when someone approaches
- **Greeting** (1.0s): Wave gesture starts BEFORE speech begins
- **User Speaks**: Head tilt/thinking animation triggers immediately on speech detection
- **Response Thinking**: Subtle head movements while GPT-4 processes

### 2. **Faster Detection Threshold**
- **Before**: 2 seconds person present → greeting
- **After**: 1 second person present → greeting
- **Result**: 50% faster initial response time

### 3. **Parallel Processing**
All behaviors run in background threads to prevent blocking:
- Speech synthesis runs in parallel with next speech recognition
- Physical movements execute independently of voice output
- GPT-4 API calls don't freeze the main loop

### 4. **Idle Behavior**
When no one is around, Reachy performs subtle breathing movements every 8 seconds:
- Makes the robot feel "alive" even when idle
- Low priority (easily interrupted)
- Minimal power consumption

## Response Timeline

```
Event                    | Latency | Visual Feedback
-------------------------|---------|---------------------------
Person enters frame      | 0ms     | Head nod immediately
1 second present         | 1000ms  | Wave starts + greeting speech begins
User starts speaking     | 100ms   | Head tilt (listening pose)
Speech recognized        | 200ms   | Thinking look animation
GPT-4 response ready     | 1-2s    | Speaking + return to neutral
```

**Total End-to-End Latency**: ~2-3 seconds (feels responsive due to continuous movement)

## Behavior Priority System

Behaviors have priorities to ensure natural interactions:

| Priority | Behavior          | Interruptible | Use Case                    |
|----------|-------------------|---------------|-----------------------------|
| 9        | look_at_person    | No            | Immediate acknowledgment    |
| 8        | greeting_wave     | No            | Initial greeting            |
| 7        | thinking_look     | Yes           | Listening/processing        |
| 6        | curious_tilt      | Yes           | Examining unknown person    |
| 3        | neutral_pose      | Yes           | Return to default           |
| 2        | idle_breath       | Yes           | Subtle idle movement        |
| 1        | idle_drift        | Yes           | Random idle variation       |

Higher priority behaviors can interrupt lower priority ones.

## Performance Tips

### On Raspberry Pi 5:
1. **Camera FPS**: ~15-20 FPS is sufficient (person detection is lightweight)
2. **Speech Recognition**: Vosk runs offline, ~200ms latency
3. **GPT-4 API**: 1-2s for response (network dependent)
4. **TTS**: OpenAI TTS ~500ms, pyttsx3 fallback ~100ms

### Memory Usage:
- Vosk model: ~40MB RAM
- MediaPipe: ~50MB RAM
- Total system: ~200-300MB RAM
- **Pi5 8GB**: No issues, plenty of headroom

### CPU Usage:
- Idle (no person): ~5-10% CPU
- Active conversation: ~25-40% CPU
- Speech synthesis: ~15-20% CPU spike

## Making It Even Faster

### Option 1: Pre-cache Common Responses
```python
# Cache common greetings in TTS
common_phrases = [
    "Good morning! I'm Reachy. What brings you by?",
    "Hi there! I'm Reachy. What can I do for you?",
    "Hey! Good to see you. What's up?"
]
for phrase in common_phrases:
    tts.cache_phrase(phrase)  # Pre-generate audio
```

### Option 2: Use GPT-4o-mini Streaming
```python
# Stream GPT-4 response word-by-word
response_stream = openai_client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    stream=True  # Start speaking as words arrive
)
```

### Option 3: Local Voice Detection (VAD)
Replace speech recognition trigger with Voice Activity Detection:
- Faster detection of "someone is speaking" (50ms)
- Start thinking animation immediately
- Then process actual words with Vosk

## Testing Commands

### Basic Test (Pi with display):
```bash
python3 conversation_demo.py --reachy
```

### Performance Benchmarking:
```bash
# Monitor CPU/RAM during conversation
python3 conversation_demo.py --reachy &
htop  # Watch process usage
```

### Latency Testing:
Add timing logs to measure each stage:
- Person detection → greeting: Target <1.5s
- Speech start → thinking animation: Target <200ms
- User speech end → response start: Target <2.5s

## Troubleshooting Slow Performance

### Issue: Slow person detection
**Solution**: Check camera FPS and MediaPipe performance
```python
# In conversation_demo.py, add FPS counter
fps_start = time.time()
if frame_count % 30 == 0:
    fps = 30 / (time.time() - fps_start)
    print(f"FPS: {fps:.1f}")
    fps_start = time.time()
```

### Issue: Delayed speech recognition
**Solution**: Verify Vosk model loaded and PyAudio working
```bash
# Test microphone input
python3 -c "import pyaudio; p=pyaudio.PyAudio(); print(p.get_device_count())"
```

### Issue: Slow GPT-4 responses
**Solution**: Check network latency
```bash
# Test API latency
time curl -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"Hi"}]}'
```

### Issue: Jerky robot movements
**Solution**: Reduce behavior duration or simplify movements
```python
# In behavior_module.py, adjust durations
BehaviorAction(
    roll=8.0, pitch=-5.0, yaw=0.0,
    duration=0.2,  # Reduce from 0.3 for snappier movements
    blocking=True
)
```

## Next Steps for Production

1. **Add gesture interrupt**: Let user wave to stop Reachy mid-speech
2. **Context memory**: Remember previous conversations
3. **Multi-person handling**: Detect multiple people, prioritize focus
4. **Voice commands**: "Hey Reachy" wake word before conversation
5. **Emotion detection**: Adjust behavior based on user's facial expression

---

**Performance Philosophy**: Always provide immediate physical feedback while async operations complete. Humans perceive responsiveness through motion, not just speed.
