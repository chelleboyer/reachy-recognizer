# Demo Files Status

## Working Demos

### ✅ `add_face.py`
**Status:** Fully functional  
**Purpose:** Add faces to recognition database  
**Usage:**
```bash
# With webcam
python add_face.py "Name"

# With Reachy camera
python add_face.py "Name" --reachy
```

### ✅ `test_face_recognition.py`
**Status:** Fully functional  
**Purpose:** Real-time face recognition test  
**Usage:**
```bash
# With webcam
python test_face_recognition.py

# With Reachy camera
python test_face_recognition.py --reachy
```

### ✅ `main.py`
**Status:** Fully functional  
**Purpose:** Complete face recognition and greeting system  
**Requirements:** Face database must exist (`data/faces.json`)  
**Usage:**
```bash
python main.py
```
**Features:**
- Real-time face recognition
- Event system with debouncing
- Coordinated greetings (voice + gestures)
- Behavior management
- Idle movements

### ✅ `voice_demo.py`
**Status:** Fully functional  
**Purpose:** Voice conversation with continuous robot movements  
**Requirements:** OpenAI API key in `.env`  
**Usage:**
```bash
python voice_demo.py
```
**Features:**
- Speech-to-text (Whisper)
- Conversational AI (GPT-4o-mini)
- Text-to-speech (Shimmer voice)
- Continuous head movements
- Natural idle behaviors

### ✅ `integrated_demo.py`
**Status:** Fully functional  
**Purpose:** Combined face recognition + voice conversation  
**Requirements:** 
- Face database (`data/faces.json`)
- OpenAI API key in `.env`  
**Usage:**
```bash
python integrated_demo.py
```
**Features:**
- Recognizes faces and greets by name
- Initiates voice conversation after greeting
- Full integration of all systems

## Archived Demos

### 📦 `demo.py` → `archive/demo.py.bak`
**Status:** Archived (requires external package)  
**Reason:** Depends on `reachy_mini_conversation_app` package which is not included in this repository  
**Dependencies:**
- `reachy_mini_conversation_app.moves.MovementManager`
- `reachy_mini_conversation_app.camera_worker.CameraWorker`
- `reachy_mini_conversation_app.dance_emotion_moves.*`

**To use:** Install the `reachy_mini_conversation_app` package separately or copy required modules into this project.

## Test Scripts

### Working Test Scripts
- ✅ `test_face_recognition.py` - Face recognition pipeline
- ✅ `test_voice.py` - Voice/TTS system
- ✅ `test_microphone.py` - Microphone input
- ✅ `test_direct_robot.py` - Direct robot control
- ✅ `test_app.py` - App integration tests

### Test Suites
- ✅ `tests/test_story_*.py` - Story-based test suites
- All story tests should work if dependencies are installed

## Quick Start

1. **Add faces:**
   ```bash
   python add_face.py "Alice"
   python add_face.py "Bob"
   ```

2. **Test recognition:**
   ```bash
   python test_face_recognition.py
   ```

3. **Run main system:**
   ```bash
   python main.py
   ```

4. **Try voice conversation:**
   ```bash
   python voice_demo.py
   ```

## Development Workflow

**On Windows (Development):**
```powershell
.\start_dev.ps1              # Setup environment
python add_face.py "Test"    # Test with webcam
python test_face_recognition.py
git add .
git commit -m "Your changes"
git push origin main
```

**On Raspberry Pi (Production):**
```bash
cd ~/reachy-recognizer
git pull
./start_dev.sh              # Setup environment
python add_face.py "Real" --reachy  # Use Reachy camera
python test_face_recognition.py --reachy
python main.py              # Run complete system
```
