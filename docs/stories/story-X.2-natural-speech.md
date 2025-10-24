# Story X.2: Natural, Responsive Speech Enhancement

**Epic**: Quality of Life / Interaction Enhancement  
**Priority**: High (User Experience)  
**Estimated Effort**: 6-8 hours  
**Status**: Not Started

## Overview

Enhance the text-to-speech system to make Reachy's speech more natural, human-like, and contextually responsive. Move beyond simple template-based greetings to dynamic, varied, and personality-driven responses.

## User Story

**As a** person interacting with Reachy  
**I want** Reachy's speech to sound natural and varied  
**So that** interactions feel more engaging and less robotic

## Business Value

- **Better UX**: More engaging, less repetitive interactions
- **Personality**: Reachy feels more alive and relatable
- **Context Awareness**: Responses adapt to situation
- **Reduced Fatigue**: Variety prevents greeting fatigue
- **Demo Quality**: More impressive in demonstrations

## Current State (Baseline)

**Existing TTS Implementation:**
```python
# From tts_module.py
def speak_greeting(self, greeting_type: GreetingType, person_name: str = None):
    if greeting_type == GreetingType.RECOGNIZED:
        message = f"Welcome back {person_name}" if person_name else "Welcome back"
    elif greeting_type == GreetingType.UNKNOWN:
        message = "Hello there"
    # ...
```

**Issues:**
- ✗ Same greeting every time (repetitive)
- ✗ No variation in phrasing
- ✗ Fixed sentence structure
- ✗ No personality or emotion
- ✗ Robotic TTS voice (pyttsx3)
- ✗ No context awareness (time of day, frequency, etc.)
- ✗ No prosody control (emphasis, pausing)

## Acceptance Criteria

1. ✅ **Greeting Variation**: 5+ different greeting templates per person
2. ✅ **Context Awareness**: Greetings adapt to time of day, session duration
3. ✅ **Natural Voice**: Replace pyttsx3 with more natural TTS (Azure/OpenAI)
4. ✅ **Prosody Control**: Add pauses, emphasis, speech rate variation
5. ✅ **Personality Traits**: Configurable personality (friendly, professional, playful)
6. ✅ **Non-Repetition**: Track recent phrases, avoid immediate repeats
7. ✅ **Response Latency**: Maintain < 400ms for initial response

## Technical Design

### Enhancement 1: Greeting Variation System

**Template-Based Variation:**
```python
RECOGNIZED_GREETINGS = [
    "Welcome back, {name}!",
    "Good to see you again, {name}.",
    "Hey {name}, glad you're here!",
    "{name}! How have you been?",
    "Oh hi {name}, welcome back!",
    "There you are, {name}!",
    "Hello {name}, nice to see you.",
]

UNKNOWN_GREETINGS = [
    "Hello there! Nice to meet you.",
    "Hi! I don't think we've met yet.",
    "Welcome! I'm Reachy, what's your name?",
    "Oh hello! Are you new here?",
    "Hey there, I'm Reachy. Nice to meet you!",
]
```

**Selection Strategy:**
```python
class GreetingSelector:
    def __init__(self):
        self.recent_greetings = deque(maxlen=5)  # Track recent
        self.greeting_history = {}  # Per-person history
    
    def select_greeting(self, person_name: str, greeting_type: GreetingType) -> str:
        """Select non-repeating, contextually appropriate greeting."""
        templates = self._get_templates(greeting_type)
        
        # Filter out recently used
        available = [t for t in templates if t not in self.recent_greetings]
        if not available:
            available = templates  # Reset if all used
        
        # Select based on context
        selected = self._select_by_context(available, person_name)
        
        self.recent_greetings.append(selected)
        return selected.format(name=person_name)
```

### Enhancement 2: Context-Aware Greetings

**Time-of-Day Awareness:**
```python
def get_time_context() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"

MORNING_GREETINGS = [
    "Good morning, {name}!",
    "Morning {name}, hope you slept well!",
    "{name}! Ready to start the day?",
]

AFTERNOON_GREETINGS = [
    "Good afternoon, {name}!",
    "Hey {name}, how's your day going?",
    "Afternoon {name}!",
]
```

**Session Context:**
```python
class SessionContext:
    def __init__(self):
        self.session_start = time.time()
        self.greeting_count = defaultdict(int)
    
    def get_greeting_modifier(self, person_name: str) -> str:
        """Modify greeting based on session history."""
        count = self.greeting_count[person_name]
        
        if count == 0:
            return "first"  # "Welcome back"
        elif count == 1:
            return "second"  # "Back again?"
        elif count >= 3:
            return "frequent"  # "You're here a lot today!"
        else:
            return "repeat"  # Normal greeting
```

### Enhancement 3: Natural TTS Replacement

**Option 1: Azure Cognitive Services TTS**
- **Pros**: Very natural voices, SSML support, low latency
- **Cons**: Requires Azure subscription, internet connection
- **Cost**: ~$1 per 1M characters (very cheap)

```python
import azure.cognitiveservices.speech as speechsdk

class AzureTTSManager:
    def __init__(self, subscription_key: str, region: str):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key,
            region=region
        )
        # Use natural voice
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        
    def speak(self, text: str, ssml: bool = False):
        """Speak with Azure TTS."""
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
        
        if ssml:
            result = synthesizer.speak_ssml_async(text).get()
        else:
            result = synthesizer.speak_text_async(text).get()
```

**Option 2: OpenAI TTS**
- **Pros**: Very natural, multiple voices, simple API
- **Cons**: Requires OpenAI API key, moderate latency
- **Cost**: ~$15 per 1M characters

```python
from openai import OpenAI

class OpenAITTSManager:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def speak(self, text: str, voice: str = "nova"):
        """Speak with OpenAI TTS."""
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,  # alloy, echo, fable, onyx, nova, shimmer
            input=text
        )
        
        # Stream or save audio
        response.stream_to_file("output.mp3")
        # Then play with pygame or similar
```

**Option 3: Hybrid Approach**
- Use pyttsx3 for low-latency initial response
- Stream higher-quality TTS in background
- Switch after first greeting

### Enhancement 4: SSML for Prosody Control

**Speech Synthesis Markup Language (SSML):**
```python
def create_expressive_greeting(name: str, emotion: str = "friendly") -> str:
    """Generate SSML with prosody control."""
    if emotion == "friendly":
        return f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <prosody rate="105%" pitch="+5%">
                Welcome back, <emphasis level="moderate">{name}</emphasis>!
            </prosody>
            <break time="200ms"/>
            <prosody rate="95%">
                Good to see you again.
            </prosody>
        </speak>
        """
    elif emotion == "excited":
        return f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <prosody rate="115%" pitch="+10%" volume="+5dB">
                Oh, <emphasis level="strong">{name}</emphasis>!
            </prosody>
            <break time="150ms"/>
            <prosody rate="110%">
                So great to see you!
            </prosody>
        </speak>
        """
```

**Prosody Controls:**
- `rate`: Speech speed (80%-120%)
- `pitch`: Voice pitch (+/- 20%)
- `volume`: Loudness (+/- 10dB)
- `emphasis`: Word stress (strong, moderate, reduced)
- `break`: Pauses (50ms - 5000ms)

### Enhancement 5: Personality System

**Configurable Personality Traits:**
```python
@dataclass
class PersonalityConfig:
    """Define Reachy's personality."""
    formality: float = 0.5  # 0=casual, 1=formal
    enthusiasm: float = 0.7  # 0=subdued, 1=excited
    verbosity: float = 0.5  # 0=brief, 1=chatty
    humor: float = 0.3  # 0=serious, 1=playful

class PersonalityBasedGreeter:
    def __init__(self, personality: PersonalityConfig):
        self.personality = personality
    
    def select_greeting(self, name: str) -> str:
        """Select greeting matching personality."""
        if self.personality.formality > 0.7:
            templates = FORMAL_GREETINGS  # "Good day, {name}"
        elif self.personality.formality < 0.3:
            templates = CASUAL_GREETINGS  # "Hey {name}!"
        else:
            templates = NEUTRAL_GREETINGS  # "Hello {name}"
        
        # Adjust based on enthusiasm
        if self.personality.enthusiasm > 0.7:
            templates = [t + "!" for t in templates]  # Add excitement
        
        return random.choice(templates).format(name=name)
```

### Enhancement 6: Non-Repetition Tracking

**Recent Phrase Tracker:**
```python
class PhraseTracker:
    def __init__(self, window_size: int = 10):
        self.recent_phrases = deque(maxlen=window_size)
        self.phrase_counts = defaultdict(int)
    
    def is_too_recent(self, phrase: str, min_gap: int = 3) -> bool:
        """Check if phrase was used too recently."""
        if phrase not in self.recent_phrases:
            return False
        
        last_index = len(self.recent_phrases) - 1 - self.recent_phrases[::-1].index(phrase)
        gap = len(self.recent_phrases) - last_index
        return gap < min_gap
    
    def record_phrase(self, phrase: str):
        """Track phrase usage."""
        self.recent_phrases.append(phrase)
        self.phrase_counts[phrase] += 1
    
    def get_least_used(self, candidates: List[str]) -> str:
        """Select least frequently used phrase."""
        return min(candidates, key=lambda p: self.phrase_counts[p])
```

## Implementation Tasks

### Phase 1: Greeting Variation (2-3 hours)
- [ ] Create greeting template database
- [ ] Implement GreetingSelector class
- [ ] Add non-repetition tracking
- [ ] Test with multiple greetings
- [ ] Integrate with existing TTSManager

### Phase 2: Context Awareness (2 hours)
- [ ] Add time-of-day detection
- [ ] Implement session context tracking
- [ ] Create context-specific templates
- [ ] Test time-based greeting selection
- [ ] Add session-based modifiers

### Phase 3: Natural TTS (2-3 hours)
- [ ] Research TTS options (Azure vs OpenAI vs ElevenLabs)
- [ ] Implement Azure TTS integration (recommended)
- [ ] Add voice configuration options
- [ ] Test latency vs quality tradeoff
- [ ] Add fallback to pyttsx3 if API unavailable
- [ ] Cache common phrases for faster playback

### Phase 4: Prosody & SSML (1-2 hours)
- [ ] Create SSML template system
- [ ] Add emphasis and pausing
- [ ] Configure speech rate variation
- [ ] Test with different emotions
- [ ] Balance naturalness vs latency

### Phase 5: Personality System (1 hour)
- [ ] Define personality config schema
- [ ] Implement personality-based selection
- [ ] Create personality presets
- [ ] Test different personality configs
- [ ] Document personality tuning

## Testing Strategy

1. **Variation Testing**:
   - Greet same person 20 times
   - Verify no immediate repeats
   - Check distribution of templates

2. **Context Testing**:
   - Test at different times of day
   - Verify time-appropriate greetings
   - Test session context tracking

3. **Quality Testing**:
   - A/B test pyttsx3 vs Azure TTS
   - Measure perceived naturalness
   - Test SSML prosody effectiveness

4. **Performance Testing**:
   - Measure TTS latency
   - Test with network delays
   - Verify fallback mechanism
   - Ensure < 400ms initial response

5. **Integration Testing**:
   - Test with greeting coordinator
   - Verify behavior + speech coordination
   - Test with multiple rapid greetings

## Configuration

**tts_config.yaml:**
```yaml
tts:
  engine: "azure"  # pyttsx3, azure, openai
  
  azure:
    subscription_key: "${AZURE_SPEECH_KEY}"
    region: "eastus"
    voice: "en-US-JennyNeural"
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    voice: "nova"
  
  pyttsx3:
    rate: 160
    volume: 0.9
    voice_preference: "female"
  
  personality:
    formality: 0.4  # Casual-friendly
    enthusiasm: 0.7  # Enthusiastic
    verbosity: 0.5  # Balanced
    humor: 0.3  # Slightly playful
  
  variation:
    enable: true
    min_repetition_gap: 3  # Don't repeat within 3 greetings
    context_aware: true
    time_based: true
```

## Edge Cases

1. **API Unavailable**: Fall back to pyttsx3
2. **Network Delay**: Use cached audio for common phrases
3. **Excessive Variation**: Some users prefer consistency
4. **Name Pronunciation**: Handle difficult names gracefully
5. **Rapid Greetings**: Don't exhaust all templates too quickly

## Success Metrics

- **Variation**: 80%+ of consecutive greetings are different
- **Naturalness**: User survey rating > 4/5
- **Latency**: 95% of responses < 400ms
- **Engagement**: Users interact longer with varied speech
- **Non-Repetition**: < 10% immediate repeats

## Dependencies

**Required:**
- Current tts_module.py (Story 3.2)
- Azure Cognitive Services SDK or OpenAI SDK
- Audio playback library (pygame, pydub)

**Optional:**
- SSML parser for advanced prosody
- Voice cloning for custom voice
- Emotion detection for response tuning

## Future Enhancements

- **Conversation Continuation**: Follow-up questions after greeting
- **Emotion Recognition**: Respond to user's facial expressions
- **Voice Cloning**: Custom voice for Reachy's personality
- **Multilingual Support**: Greet in user's preferred language
- **Dynamic Personality**: Adjust based on user feedback
- **Learning System**: Learn user preferences over time
- **Interrupt Handling**: Natural interruption/resumption
- **Small Talk**: Brief conversations beyond greetings

## Cost Analysis

**Azure TTS:**
- Cost: ~$1 per 1M characters
- Typical greeting: 30 characters
- 1000 greetings = $0.03
- Very affordable for development/demo

**OpenAI TTS:**
- Cost: ~$15 per 1M characters
- 1000 greetings = $0.45
- Higher quality but more expensive

**pyttsx3:**
- Cost: Free (offline)
- Quality: Lower but acceptable
- Good for fallback

**Recommendation**: Azure TTS for best quality/cost balance

## Notes

**Priority Features:**
1. Greeting variation (biggest impact)
2. Azure TTS (quality improvement)
3. Context awareness (engagement)
4. Prosody control (naturalness)
5. Personality system (differentiation)

**Quick Wins:**
- Add 5 greeting templates (30 minutes)
- Time-of-day awareness (1 hour)
- Non-repetition tracking (1 hour)

**Long-Term Investment:**
- Azure TTS integration (best ROI)
- SSML prosody (polish)
- Personality system (differentiation)

