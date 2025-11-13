# Story 3.4: Unknown & Idle Behaviors with Natural Speech

**Epic**: 3 - Engagement & Response  
**Priority**: High  
**Estimated Effort**: 4-6 hours (includes natural speech integration from X.2)  
**Status**: Not Started

## Overview

Implement unknown person response and idle behaviors (NO_FACES state), integrating natural speech variations and personality-driven responses from Story X.2 to create more engaging, less robotic interactions.

## User Story

**As a** person interacting with Reachy  
**I want** Reachy to respond naturally when it doesn't recognize me and show subtle life-like behaviors when idle  
**So that** interactions feel more engaging, varied, and human-like regardless of recognition status

## Business Value

- **Complete State Coverage**: All event types now have responses
- **Natural Interactions**: Varied, personality-driven speech (from X.2)
- **Life-Like Presence**: Idle behaviors make Reachy feel alive
- **Better UX**: Reduced repetition through greeting variation system
- **Demo Quality**: Impressive natural responses in all scenarios

## Acceptance Criteria

### Unknown Person Response
1. ✅ PERSON_APPEARED(unknown) triggers greeting response
2. ✅ Uses "unknown" behavior set (different from recognized greeting)
3. ✅ 5+ greeting variations for unknown persons (X.2 integration)
4. ✅ Speech uses natural TTS with prosody (X.2 integration)
5. ✅ Logs unknown person event for analytics
6. ✅ Latency < 400ms from detection to initial response

### Idle Behaviors
7. ✅ NO_FACES state triggers idle behavior after threshold
8. ✅ Subtle head movements (drift, look around)
9. ✅ Periodic activation (not constant)
10. ✅ Stops when person detected
11. ✅ Logs idle behavior events

### Natural Speech Integration (Story X.2)
12. ✅ Greeting variation system implemented (5+ templates per type)
13. ✅ Non-repetition tracking (avoids recent greetings)
14. ✅ Context awareness (time of day, session duration)
15. ✅ Personality configuration (friendly, professional, playful)
16. ✅ Azure/OpenAI TTS integration (more natural voice)
17. ✅ SSML prosody control (pauses, emphasis, rate)

## Prerequisites

- Story 3.3.5: Reachy SDK Integration ✅
- Story X.2: Natural Speech Enhancement (integrate here)

## Technical Design

### Part 1: Unknown Person Response

**Event Flow:**
```
PERSON_APPEARED(unknown) 
  → EventManager.handle_event()
  → GreetingCoordinator.greet_person()
  → GreetingSelector.select_greeting(unknown) [NEW from X.2]
  → TTSManager.speak_greeting(varied_message)
  → BehaviorManager.execute_behavior(curious_tilt)
```

**Integration Point:**
```python
# greeting_coordinator.py
def greet_person(self, event: PersonEvent):
    """Enhanced with natural speech variation from X.2"""
    
    greeting_type = (
        GreetingType.RECOGNIZED if event.person_id in self.known_people 
        else GreetingType.UNKNOWN
    )
    
    # NEW: Use GreetingSelector for variation (X.2)
    message = self.greeting_selector.select_greeting(
        person_name=event.person_id if greeting_type == GreetingType.RECOGNIZED else None,
        greeting_type=greeting_type,
        context={
            'time_of_day': self._get_time_of_day(),
            'session_duration': time.time() - self.session_start,
            'first_greeting': not self.greeting_history
        }
    )
    
    # Coordinate speech + behavior
    self._coordinate_greeting(message, greeting_type)
```

**Unknown Greeting Behaviors:**
```python
# behavior_definitions.py (NEW)

unknown_greeting = Behavior(
    name="unknown_greeting",
    description="Friendly inquisitive greeting for unknown person",
    actions=[
        BehaviorAction(roll=0, pitch=5, yaw=-10, duration=0.6, blocking=False),
        BehaviorAction(roll=0, pitch=0, yaw=10, duration=0.5, blocking=False),
        BehaviorAction(roll=0, pitch=-5, yaw=0, duration=0.4, blocking=False),
        BehaviorAction(roll=0, pitch=0, yaw=0, duration=0.3, blocking=True),
    ]
)

unknown_curious = Behavior(
    name="unknown_curious",
    description="Curious head tilt for unfamiliar face",
    actions=[
        BehaviorAction(roll=-10, pitch=5, yaw=0, duration=0.8, blocking=False),
        BehaviorAction(roll=10, pitch=5, yaw=0, duration=0.8, blocking=False),
        BehaviorAction(roll=0, pitch=0, yaw=0, duration=0.4, blocking=True),
    ]
)
```

### Part 2: Idle Behaviors

**Idle Drift Behavior:**
```python
# behavior_definitions.py

idle_drift = Behavior(
    name="idle_drift",
    description="Subtle random head movement when idle",
    actions=[
        BehaviorAction(
            roll=random.uniform(-5, 5),
            pitch=random.uniform(-3, 8),
            yaw=random.uniform(-15, 15),
            duration=random.uniform(2.0, 4.0),
            blocking=True
        ),
    ]
)

idle_look_around = Behavior(
    name="idle_look_around",
    description="Periodic scanning behavior when no faces present",
    actions=[
        BehaviorAction(roll=0, pitch=0, yaw=-20, duration=1.5, blocking=False),
        BehaviorAction(roll=0, pitch=5, yaw=0, duration=1.5, blocking=False),
        BehaviorAction(roll=0, pitch=0, yaw=20, duration=1.5, blocking=False),
        BehaviorAction(roll=0, pitch=0, yaw=0, duration=1.0, blocking=True),
    ]
)
```

**Idle Manager:**
```python
# idle_manager.py (NEW)

class IdleManager:
    """Manages idle behaviors during NO_FACES state."""
    
    def __init__(self, behavior_manager: BehaviorManager, 
                 idle_threshold: float = 5.0,
                 idle_interval: float = 10.0):
        self.behavior_manager = behavior_manager
        self.idle_threshold = idle_threshold  # Seconds before idle activates
        self.idle_interval = idle_interval    # Seconds between idle behaviors
        
        self.last_face_time = time.time()
        self.last_idle_time = 0
        self.idle_active = False
        self.idle_thread = None
        
    def update_face_status(self, has_faces: bool):
        """Update idle state based on face presence."""
        if has_faces:
            self.last_face_time = time.time()
            self.idle_active = False
        else:
            time_since_face = time.time() - self.last_face_time
            if time_since_face > self.idle_threshold:
                self._activate_idle()
    
    def _activate_idle(self):
        """Start idle behavior loop."""
        if self.idle_active:
            return
        
        self.idle_active = True
        self.idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self.idle_thread.start()
    
    def _idle_loop(self):
        """Execute periodic idle behaviors."""
        while self.idle_active:
            time_since_last = time.time() - self.last_idle_time
            
            if time_since_last >= self.idle_interval:
                # Random idle behavior
                behavior = random.choice([
                    idle_drift,
                    idle_look_around,
                    # Could add more variations
                ])
                
                logger.info(f"Executing idle behavior: {behavior.name}")
                self.behavior_manager.execute_behavior(behavior)
                self.last_idle_time = time.time()
            
            time.sleep(1.0)  # Check every second
```

### Part 3: Natural Speech Integration (Story X.2)

**Greeting Variation System:**
```python
# greeting_selector.py (NEW from X.2)

from collections import deque
from dataclasses import dataclass
from typing import Dict, List
import random
from datetime import datetime

@dataclass
class GreetingTemplate:
    text: str
    personality: str  # 'friendly', 'professional', 'playful'
    time_of_day: List[str]  # ['morning', 'afternoon', 'evening', 'any']
    prosody: Dict[str, str]  # SSML prosody hints

class GreetingSelector:
    """Selects varied, contextually appropriate greetings."""
    
    RECOGNIZED_TEMPLATES = [
        GreetingTemplate(
            text="Welcome back, {name}!",
            personality="friendly",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "+5%"}
        ),
        GreetingTemplate(
            text="Good to see you again, {name}.",
            personality="professional",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "medium"}
        ),
        GreetingTemplate(
            text="Hey {name}, glad you're here!",
            personality="playful",
            time_of_day=["any"],
            prosody={"rate": "fast", "pitch": "+10%"}
        ),
        GreetingTemplate(
            text="Good morning, {name}!",
            personality="friendly",
            time_of_day=["morning"],
            prosody={"rate": "medium", "pitch": "+3%"}
        ),
        GreetingTemplate(
            text="{name}! <break time='200ms'/> How have you been?",
            personality="friendly",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "+5%"}
        ),
        GreetingTemplate(
            text="Oh hi {name}, welcome back!",
            personality="playful",
            time_of_day=["any"],
            prosody={"rate": "fast", "pitch": "+8%"}
        ),
        GreetingTemplate(
            text="Hello {name}, nice to see you.",
            personality="professional",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "medium"}
        ),
    ]
    
    UNKNOWN_TEMPLATES = [
        GreetingTemplate(
            text="Hello there! <break time='300ms'/> Nice to meet you.",
            personality="friendly",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "+5%"}
        ),
        GreetingTemplate(
            text="Hi! I don't think we've met yet.",
            personality="friendly",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "+3%"}
        ),
        GreetingTemplate(
            text="Welcome! I'm Reachy. <break time='200ms'/> What's your name?",
            personality="playful",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "+8%"}
        ),
        GreetingTemplate(
            text="Oh hello! Are you new here?",
            personality="friendly",
            time_of_day=["any"],
            prosody={"rate": "fast", "pitch": "+10%"}
        ),
        GreetingTemplate(
            text="Hey there, I'm Reachy. Nice to meet you!",
            personality="playful",
            time_of_day=["any"],
            prosody={"rate": "fast", "pitch": "+8%"}
        ),
        GreetingTemplate(
            text="Good morning! I'm Reachy.",
            personality="friendly",
            time_of_day=["morning"],
            prosody={"rate": "medium", "pitch": "+5%"}
        ),
        GreetingTemplate(
            text="Hello, welcome.",
            personality="professional",
            time_of_day=["any"],
            prosody={"rate": "medium", "pitch": "medium"}
        ),
    ]
    
    def __init__(self, personality: str = "friendly"):
        self.personality = personality
        self.recent_greetings = deque(maxlen=3)  # Avoid last 3
        self.greeting_history: Dict[str, List[str]] = {}
    
    def select_greeting(self, person_name: str = None, 
                       greeting_type: GreetingType = GreetingType.UNKNOWN,
                       context: dict = None) -> GreetingTemplate:
        """Select contextually appropriate greeting with variation."""
        context = context or {}
        
        # Get templates for greeting type
        templates = (
            self.RECOGNIZED_TEMPLATES if greeting_type == GreetingType.RECOGNIZED
            else self.UNKNOWN_TEMPLATES
        )
        
        # Filter by personality
        filtered = [t for t in templates if t.personality == self.personality]
        if not filtered:
            filtered = templates  # Fallback to all
        
        # Filter by time of day
        time_of_day = context.get('time_of_day', self._get_time_of_day())
        time_filtered = [
            t for t in filtered 
            if time_of_day in t.time_of_day or 'any' in t.time_of_day
        ]
        if not time_filtered:
            time_filtered = filtered
        
        # Remove recently used
        available = [
            t for t in time_filtered 
            if t.text not in self.recent_greetings
        ]
        if not available:
            available = time_filtered  # Reset if exhausted
        
        # Select randomly from available
        selected = random.choice(available)
        self.recent_greetings.append(selected.text)
        
        # Format with name if recognized
        if person_name:
            selected.text = selected.text.format(name=person_name)
        
        return selected
    
    def _get_time_of_day(self) -> str:
        """Determine current time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"
```

**Enhanced TTS with Azure/OpenAI:**
```python
# tts_module.py (ENHANCED from X.2)

class EnhancedTTSManager:
    """TTS with Azure Neural Voices and SSML prosody."""
    
    def __init__(self, voice_backend: str = "azure"):
        self.voice_backend = voice_backend
        
        if voice_backend == "azure":
            self._init_azure()
        elif voice_backend == "openai":
            self._init_openai()
        else:
            self._init_pyttsx3()  # Fallback
    
    def _init_azure(self):
        """Initialize Azure Neural TTS."""
        import azure.cognitiveservices.speech as speechsdk
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION")
        )
        
        # Use neural voice
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
    
    def speak_greeting(self, greeting_template: GreetingTemplate):
        """Speak with SSML prosody control."""
        ssml = self._build_ssml(greeting_template)
        
        if self.voice_backend == "azure":
            result = self.synthesizer.speak_ssml_async(ssml).get()
            # Check result.reason for success/failure
        else:
            # Fallback: strip SSML tags and use pyttsx3
            text = self._strip_ssml(greeting_template.text)
            self.engine.say(text)
            self.engine.runAndWait()
    
    def _build_ssml(self, template: GreetingTemplate) -> str:
        """Build SSML with prosody control."""
        rate = template.prosody.get("rate", "medium")
        pitch = template.prosody.get("pitch", "medium")
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-JennyNeural">
                <prosody rate="{rate}" pitch="{pitch}">
                    {template.text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml
```

## Implementation Tasks

### Phase 1: Unknown Person Response (1-2 hours)
- [ ] Add unknown_greeting and unknown_curious to behavior_definitions.py
- [ ] Update GreetingCoordinator to handle UNKNOWN greeting type
- [ ] Map PERSON_APPEARED(unknown) events to greeting flow
- [ ] Test unknown greeting with behavior + speech
- [ ] Verify latency < 400ms

### Phase 2: Idle Behaviors (1-2 hours)
- [ ] Create idle_manager.py module
- [ ] Implement IdleManager class with threading
- [ ] Add idle_drift and idle_look_around behaviors
- [ ] Integrate with EventManager for NO_FACES events
- [ ] Test idle activation/deactivation
- [ ] Verify smooth transitions

### Phase 3: Natural Speech Integration (Story X.2) (2-3 hours)
- [ ] Create greeting_selector.py with GreetingTemplate system
- [ ] Implement GreetingSelector with variation logic
- [ ] Add 5+ templates for RECOGNIZED and UNKNOWN
- [ ] Implement non-repetition tracking (deque)
- [ ] Add context awareness (time of day, session duration)
- [ ] Integrate personality configuration
- [ ] Update TTSManager with Azure/OpenAI TTS (optional)
- [ ] Add SSML prosody support
- [ ] Test greeting variation in GreetingCoordinator

### Phase 4: Integration & Testing (1 hour)
- [ ] Wire all components together in event_manager.py
- [ ] Create comprehensive test script
- [ ] Test all greeting variations (recognized + unknown)
- [ ] Test idle behaviors with NO_FACES
- [ ] Verify no performance degradation
- [ ] Update documentation

## Testing Strategy

### Test 1: Unknown Person Greeting
```python
# Test unknown person greeting with variation
event = PersonEvent(
    event_type=EventType.PERSON_APPEARED,
    person_id="unknown_abc123",
    timestamp=time.time(),
    metadata={}
)

# First greeting
coordinator.greet_person(event)
# Should: Play varied greeting + curious behavior

# Second greeting (same person, later)
time.sleep(2)
coordinator.greet_person(event)
# Should: Use different greeting template
```

### Test 2: Idle Behaviors
```python
# Test idle activation
idle_manager.update_face_status(has_faces=False)
time.sleep(6)  # Wait past threshold
# Should: Start idle drift behaviors

# Test idle deactivation
idle_manager.update_face_status(has_faces=True)
# Should: Stop idle behaviors immediately
```

### Test 3: Greeting Variation
```python
# Test non-repetition
greetings = []
for i in range(10):
    template = selector.select_greeting(
        person_name="Test",
        greeting_type=GreetingType.RECOGNIZED
    )
    greetings.append(template.text)

# Verify: No consecutive duplicates
for i in range(len(greetings) - 1):
    assert greetings[i] != greetings[i+1]
```

## Success Metrics

**Unknown Person Response:**
- ✅ PERSON_APPEARED(unknown) triggers greeting
- ✅ Unknown behaviors execute correctly
- ✅ Speech + behavior coordination < 400ms
- ✅ 5+ greeting variations available

**Idle Behaviors:**
- ✅ Idle activates after 5s of NO_FACES
- ✅ Behaviors execute every 10s
- ✅ Stops immediately when face detected
- ✅ No crashes or threading issues

**Natural Speech (X.2):**
- ✅ Greeting variation system working
- ✅ No repeated greetings in last 3
- ✅ Context awareness (time of day)
- ✅ Personality configuration functional
- ✅ Azure/OpenAI TTS integrated (optional)
- ✅ SSML prosody control working

## Dependencies

**Required:**
- Story 3.3.5: Reachy SDK Integration ✅
- Story X.2: Natural Speech Enhancement (integrate here)

**Enables:**
- Complete Epic 3 (Engagement & Response) ✅
- Full state coverage for all event types
- Natural, human-like interaction system

## Notes

**Story X.2 Integration:**
This story incorporates all enhancements from Story X.2 (Natural Speech) into the main development track. Rather than implementing X.2 separately, we're integrating its features directly into Story 3.4 to:
- Avoid duplicate work
- Ensure cohesive implementation
- Complete Epic 3 with full natural speech support
- Provide immediate UX benefit

**Voice Backend Options:**
- **pyttsx3**: Local, free, basic quality (current)
- **Azure Neural**: Cloud, paid, high quality, SSML support
- **OpenAI TTS**: Cloud, paid, very natural, limited prosody
- **Recommendation**: Start with pyttsx3, add Azure as enhancement

**Idle Behavior Philosophy:**
- Subtle, not distracting
- Random variation to feel organic
- Periodic, not constant
- Energy-efficient (infrequent)

**Performance Considerations:**
- Idle behaviors run in separate thread
- No impact on greeting latency
- Graceful shutdown with daemon threads
- Minimal CPU when idle

## Completion Criteria

✅ All 17 acceptance criteria met  
✅ Tests passing for unknown greeting  
✅ Tests passing for idle behaviors  
✅ Tests passing for greeting variation  
✅ Latency < 400ms maintained  
✅ Documentation updated  
✅ Code committed and reviewed  

**Status**: Epic 3 (Engagement & Response) - COMPLETE! 🎉

---

**Related Stories:**
- Story 3.1: Greeting Behavior Module ✅
- Story 3.2: Text-to-Speech Integration ✅
- Story 3.3: Coordinated Greeting Response ✅
- Story 3.3.5: Reachy SDK Integration ✅
- Story X.2: Natural Speech Enhancement (integrated here)
