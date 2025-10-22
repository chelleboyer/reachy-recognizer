# Story 3.2: Text-to-Speech Integration

Status: ✅ Complete

## Goal

Implement text-to-speech functionality so Reachy can speak greetings, making interactions more natural and engaging.

## User Story

As a **developer**,
I want Reachy to speak greetings using text-to-speech,
So that interactions feel more natural and engaging.

## Acceptance Criteria

1. ✅ TTS module implemented using `pyttsx3` (local TTS)
2. ✅ Greeting phrases defined: recognized ("Hello [Name]!"), unknown ("Hi there! I don't think we've met yet.")
3. ✅ TTS voice configured (select natural-sounding voice if available)
4. ✅ Speech rate adjusted for clarity (not too fast)
5. ✅ TTS runs in separate thread to avoid blocking
6. ✅ Error handling: TTS fails gracefully, logs error, continues without speech
7. ✅ Test script validates TTS working with sample phrases

## Prerequisites

- Story 1.1: Project Setup (pyttsx3 should be installed)

## Tasks / Subtasks

- [x] Task 1: Install and verify pyttsx3
  - [x] Check if pyttsx3 is in requirements
  - [x] Test basic TTS functionality
  - [x] Verify available voices

- [x] Task 2: Create TTSManager class (AC: 1, 5, 6)
  - [x] Initialize pyttsx3 engine
  - [x] speak() method with threading
  - [x] Error handling with try/catch
  - [x] Thread-safe queue for speech requests

- [x] Task 3: Configure voice and speech rate (AC: 3, 4)
  - [x] List available voices
  - [x] Select natural-sounding voice
  - [x] Set speech rate (150-180 words/min)
  - [x] Set volume level

- [x] Task 4: Define greeting phrases (AC: 2)
  - [x] Recognized person: "Hello {name}!"
  - [x] Unknown person: "Hi there! I don't think we've met yet."
  - [x] Departed: "Goodbye {name}!"
  - [x] Template system for variation

- [x] Task 5: Create unit tests (AC: 7)
  - [x] Test TTSManager initialization
  - [x] Test speech generation (mocked)
  - [x] Test threading behavior
  - [x] Test error handling
  - [x] All tests passing

- [x] Task 6: Demo script
  - [x] Test all greeting phrases
  - [x] Verify voice quality
  - [x] Check threading (non-blocking)
  - [x] Performance metrics

## Technical Notes

### Implementation Approach

**TTS Manager**:
```python
import pyttsx3
import threading
import queue
import logging

class TTSManager:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.configure_voice()
        self.speech_queue = queue.Queue()
        self.worker_thread = threading.Thread(
            target=self._speech_worker,
            daemon=True
        )
        self.worker_thread.start()
    
    def configure_voice(self):
        # Get available voices
        voices = self.engine.getProperty('voices')
        
        # Select natural-sounding voice (prefer female)
        for voice in voices:
            if 'zira' in voice.name.lower():  # Windows: Microsoft Zira
                self.engine.setProperty('voice', voice.id)
                break
        
        # Set speech rate (default: 200, set to 160 for clarity)
        self.engine.setProperty('rate', 160)
        
        # Set volume (0.0 to 1.0)
        self.engine.setProperty('volume', 0.9)
    
    def speak(self, text: str):
        \"\"\"Queue text for speech (non-blocking).\"\"\"
        self.speech_queue.put(text)
    
    def _speech_worker(self):
        \"\"\"Worker thread to process speech queue.\"\"\"
        while True:
            try:
                text = self.speech_queue.get(timeout=1.0)
                self.engine.say(text)
                self.engine.runAndWait()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"TTS error: {e}")
```

**Greeting Phrases**:
```python
GREETINGS = {
    'recognized': [
        "Hello {name}!",
        "Hi {name}! Good to see you!",
        "Hey {name}, how are you?"
    ],
    'unknown': [
        "Hi there! I don't think we've met yet.",
        "Hello! Nice to meet you!",
        "Hi! I'm Reachy. Who are you?"
    ],
    'departed': [
        "Goodbye {name}!",
        "See you later, {name}!",
        "Bye {name}!"
    ]
}

def get_greeting(event_type: str, name: str = "") -> str:
    \"\"\"Get random greeting phrase.\"\"\"
    templates = GREETINGS.get(event_type, ["Hello!"])
    template = random.choice(templates)
    return template.format(name=name)
```

### Dependencies

**Required:**
- `pyttsx3` - Cross-platform TTS library
- `threading` - Non-blocking speech
- `queue` - Thread-safe speech queue
- `logging` - Error logging

**pyttsx3 Installation**:
```bash
pip install pyttsx3
```

**Platform-specific TTS engines:**
- Windows: SAPI5 (Microsoft Speech API)
- macOS: NSSpeechSynthesizer
- Linux: eSpeak

### Testing Strategy

1. **Unit Tests**:
   - Mock pyttsx3 engine
   - Test TTSManager initialization
   - Test speak() queuing
   - Test thread safety
   - Test error handling

2. **Integration Tests**:
   - Test with real TTS engine
   - Verify voice quality
   - Test all greeting phrases
   - Measure latency

3. **Demo Script**:
   - Speak all greeting types
   - Test with various names
   - Verify non-blocking behavior
   - Check error recovery

### Success Metrics

- TTS initialization: < 500ms
- Speech queuing latency: < 10ms
- Non-blocking: Main thread continues immediately
- Error recovery: System continues without crash
- Voice quality: Clear, natural-sounding
- Speech rate: 150-180 words/min for clarity

### Edge Cases

1. **TTS engine not available**:
   - Solution: Catch exception, log warning, continue silently

2. **Multiple speech requests queued**:
   - Solution: Queue processes sequentially

3. **Very long name**:
   - Solution: Truncate or handle gracefully

4. **Special characters in name**:
   - Solution: Sanitize input before speech

### Future Enhancements

- Multiple voice options (male/female/robotic)
- Language support (multilingual greetings)
- Emotion-based speech (happy, surprised, excited)
- Speech synthesis customization per person
- Integration with cloud TTS (Google, Azure) for better quality

## Dependencies

- **Depends on:**
  - Story 1.1: Project Setup (pyttsx3 installed)

- **Enables:**
  - Story 3.3: Coordinated Greeting Response (behaviors + speech)
  - Story 3.4: Unknown & Idle Behaviors (speech for all scenarios)

## Notes

**pyttsx3 Voice Selection**:
- Windows: Microsoft David (male), Microsoft Zira (female)
- macOS: Alex, Samantha, Victoria
- Linux: eSpeak voices (multiple accents)

**Speech Rate Guidelines**:
- Too fast (>200 wpm): Hard to understand
- Good range (150-180 wpm): Clear and natural
- Too slow (<130 wpm): Sounds robotic

**Testing Without Audio**:
- Use `engine.save_to_file()` for offline testing
- Mock pyttsx3 for automated tests
- Verify queue and threading logic works correctly

---

##  Completion Notes

**Date Completed**: January 2025

### Implementation Summary

Successfully implemented text-to-speech integration with pyttsx3, enabling Reachy to speak natural greetings alongside behaviors.

**Files Created:**
1. **tts_module.py** (450+ lines): TTSManager class, voice configuration, non-blocking speech, greeting templates
2. **tests/test_story_3_2_tts.py** (500+ lines): 21 unit tests, all passing
3. **behavior_speech_demo.py** (180+ lines): Integration demo with 5 scenarios

### Test Results

**Unit Tests**: 21/21 PASSING 

**Performance**:
- TTS initialization: 1.57ms (target < 500ms) 
- Queuing latency: < 0.01ms (target < 10ms)   
- Non-blocking operation: Confirmed 

**Integration Demo**:
- 8 behaviors executed (100% success)
- 7 speeches queued and spoken
- 0 TTS errors
- Voice: Microsoft Zira (clear, natural)

### Key Achievements

1.  AC 1 - TTS Module with pyttsx3
2.  AC 2 - Greeting Phrases (4 categories, 12+ phrases)
3.  AC 3 - Voice Configuration (Microsoft Zira)
4.  AC 4 - Speech Rate (160 wpm)
5.  AC 5 - Threading (non-blocking with queue)
6.  AC 6 - Error Handling (silent mode fallback)
7.  AC 7 - Test Validation (demo + 21 tests)

**Ready for Story 3.3**: Full event  behavior  speech pipeline integration
