# 🗣️ How to Make Reachy Actually Say "Hi Mom" with YOUR API Key

## 🔧 **Step-by-Step Setup:**

### **1. Set Your API Key (Choose ONE method):**

**Method A - PowerShell (Recommended):**
```powershell
# Set your real API key
$env:OPENAI_API_KEY='your-actual-api-key-here'

# Then run the TTS test
uv run python test_tts_simple.py
```

**Method B - Command Line with uv:**
```bash
# Run with your API key directly
uv run --env OPENAI_API_KEY=your-actual-api-key-here python test_tts_simple.py
```

**Method C - Persistent Environment Variable:**
```powershell
# Set permanently (until you close PowerShell)
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-actual-api-key-here", "Process")
uv run python test_tts_simple.py
```

---

### **2. What Will Happen:**
1. ✅ **TTS Generation:** Creates `reachy_says_hi_mom.mp3` 
2. ✅ **Reachy Connection:** Connects to robot
3. ✅ **Speech Simulation:** Plays built-in sound while showing the message
4. ✅ **Loving Gestures:** Sweet nods and loving movements
5. ✅ **Audio File:** You get the MP3 file of Reachy's voice!

---

### **3. Expected Output:**
```
💝 Reachy Says Hi Mom - TTS Test 💝
✓ API key found (length: 51)
🗣️ Generating 'Hi Mom' speech...
✅ Speech generated!
📁 File: reachy_says_hi_mom.mp3
📊 Size: ~45000 bytes
💬 Generated message: 'Hi Mom! I love you so much! You're the best mom ever!'
🤖 Testing with Reachy...
✓ Connected to Reachy!
🗣️ Reachy 'speaks': 'Hi Mom! I love you so much!'
💕 Loving gestures...
💖 'I love you Mom!'
✅ Complete!
```

---

### **4. Quick Test Commands:**

**Test TTS Generation:**
```bash
# Replace 'your-key' with your actual API key
$env:OPENAI_API_KEY='your-actual-key'; uv run python test_tts_simple.py
```

**Make Reachy Say Hi Mom (with gestures):**
```bash
$env:OPENAI_API_KEY='your-actual-key'; uv run python reachy_hi_mom.py
```

---

### **5. Files You Can Use:**

- **`test_tts_simple.py`** - Test TTS generation + basic Reachy demo
- **`reachy_hi_mom.py`** - Full loving performance with real speech
- **`hi_mom.py`** - Quick version (works without API key too)

---

### **6. Troubleshooting:**

**If you get "API key not found":**
- Make sure you're setting it in the same PowerShell window
- Check your key is valid at: https://platform.openai.com/

**If you get "401 Unauthorized":**
- Double-check your API key is correct
- Make sure your OpenAI account has credits

**If you get "audio format error":**
- The MP3 is generated correctly
- Reachy needs WAV format for direct playback
- The demo uses built-in sounds as simulation

---

## 🎯 **Quick Start (RIGHT NOW):**

```powershell
# 1. Set your API key (replace with your real key)
$env:OPENAI_API_KEY='sk-your-actual-key-here'

# 2. Test TTS generation
uv run python test_tts_simple.py

# 3. Full Hi Mom performance 
uv run python reachy_hi_mom.py
```

**Result:** Reachy will generate real speech saying "Hi Mom! I love you so much!" and perform loving gestures! 💝🤖