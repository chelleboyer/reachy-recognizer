# Voice Response System Design - Story 3.4 Enhancement

**Version**: 1.0  
**Date**: October 24, 2025  
**Status**: Design Phase

## Executive Summary

This document outlines a comprehensive, production-quality voice response system for Reachy that balances:
- **Naturalness**: Human-like speech quality and variation
- **Reliability**: Graceful fallbacks and offline capability
- **Performance**: Sub-400ms latency targets
- **Cost-effectiveness**: Smart API usage with local fallback
- **Maintainability**: Modular architecture with easy voice switching

## Design Goals

### Primary Objectives
1. **Natural Speech Quality**: Move beyond robotic TTS to expressive, engaging voice
2. **Variation System**: No repeated greetings, contextually appropriate responses
3. **Low Latency**: Real-time response (<400ms from detection to speech start)
4. **High Availability**: Works offline, degrades gracefully
5. **Scalability**: Easy to add new greeting types and voice options

### Success Metrics
- Voice quality subjective rating: 8+/10 (vs current pyttsx3 baseline ~5/10)
- Greeting variation: 0% repetition in 10 consecutive greetings
- Latency: 95th percentile <400ms end-to-end
- Uptime: 99.9% (with local fallback)
- User engagement: Positive sentiment in 80%+ interactions

## Architecture Overview

### Three-Tier Voice System

```
┌─────────────────────────────────────────────────────────┐
│                  GREETING COORDINATOR                    │
│              (Handles timing & coordination)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  GREETING SELECTOR                       │
│        (Selects varied, contextual greetings)           │
│  • Non-repetition tracking                              │
│  • Time-of-day awareness                                │
│  • Personality modes                                    │
│  • SSML/prosody hints                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              ADAPTIVE TTS MANAGER                        │
│         (Multi-backend voice synthesis)                  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PRIMARY     │  │  SECONDARY   │  │   FALLBACK   │ │
│  │  OpenAI TTS  │→│  Azure Neural│→│   pyttsx3    │ │
│  │  (Best)      │  │  (Good)      │  │  (Reliable)  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Component Design

### 1. Greeting Selector (Core Intelligence)

**File**: `greeting_selector.py`

#### Key Features

**1.1 Template System**
```python
@dataclass
class GreetingTemplate:
    """Rich greeting template with metadata."""
    text: str                          # Greeting text (may include {name})
    personality: str                   # 'warm', 'professional', 'playful', 'neutral'
    time_of_day: List[str]            # ['morning', 'afternoon', 'evening', 'any']
    context_tags: List[str]            # ['first_meeting', 'repeat_visitor', 'long_absence']
    emotion: str                       # 'happy', 'curious', 'calm', 'excited'
    prosody: Dict[str, str]           # Voice modulation hints
    duration_estimate: float           # Expected speech duration (seconds)
    energy_level: int                  # 1-5 scale for enthusiasm
```

**1.2 Non-Repetition System**
- **Short-term memory**: Last 5 greetings (deque)
- **Per-person history**: Track greetings used per individual
- **Session-based reset**: Clear history on new session
- **Exhaustion handling**: Graceful fallback when templates exhausted

**1.3 Contextual Selection**
```python
def select_greeting(
    person_name: Optional[str],
    greeting_type: GreetingType,
    context: GreetingContext
) -> GreetingTemplate:
    """
    Smart greeting selection with multiple filters:
    1. Filter by greeting_type (recognized/unknown/departed)
    2. Filter by personality preference
    3. Filter by time_of_day
    4. Filter by context_tags (first meeting, etc.)
    5. Remove recently used (non-repetition)
    6. Weight by appropriateness score
    7. Random selection from top candidates
    """
```

**1.4 Context Object**
```python
@dataclass
class GreetingContext:
    """Context for greeting selection."""
    time_of_day: str                   # morning/afternoon/evening
    session_duration: float            # Seconds since session start
    is_first_greeting: bool            # First of session
    person_history: Optional[PersonHistory]  # Previous interactions
    current_emotion: str               # Robot's current "mood"
    room_occupancy: int                # Number of people present
    interaction_count: int             # Total greetings this session
```

#### Template Library Design

**For Recognized Persons** (15+ variations)
```python
RECOGNIZED_TEMPLATES = [
    # Warm & Friendly
    GreetingTemplate(
        text="Welcome back, {name}!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["repeat_visitor"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+8%", "emphasis": "strong"},
        duration_estimate=1.5,
        energy_level=4
    ),
    
    # First meeting today
    GreetingTemplate(
        text="Good morning, {name}! Great to see you.",
        personality="warm",
        time_of_day=["morning"],
        context_tags=["repeat_visitor", "first_today"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+5%"},
        duration_estimate=2.0,
        energy_level=3
    ),
    
    # Enthusiastic
    GreetingTemplate(
        text="Hey {name}! <break time='200ms'/> So glad you're here!",
        personality="playful",
        time_of_day=["any"],
        context_tags=["repeat_visitor"],
        emotion="excited",
        prosody={"rate": "fast", "pitch": "+12%", "emphasis": "strong"},
        duration_estimate=2.5,
        energy_level=5
    ),
    
    # Professional
    GreetingTemplate(
        text="Hello {name}, good to see you again.",
        personality="professional",
        time_of_day=["any"],
        context_tags=["repeat_visitor"],
        emotion="calm",
        prosody={"rate": "medium", "pitch": "medium"},
        duration_estimate=1.8,
        energy_level=2
    ),
    
    # Long absence
    GreetingTemplate(
        text="Oh wow, {name}! <break time='300ms'/> It's been a while! Welcome back!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["long_absence"],
        emotion="excited",
        prosody={"rate": "medium", "pitch": "+10%", "emphasis": "strong"},
        duration_estimate=3.0,
        energy_level=5
    ),
    
    # Casual
    GreetingTemplate(
        text="Oh hi {name}, how's it going?",
        personality="playful",
        time_of_day=["afternoon", "evening"],
        context_tags=["repeat_visitor"],
        emotion="curious",
        prosody={"rate": "fast", "pitch": "+6%"},
        duration_estimate=2.0,
        energy_level=3
    ),
    
    # Gentle/quiet
    GreetingTemplate(
        text="Hello {name}. Nice to see you.",
        personality="neutral",
        time_of_day=["any"],
        context_tags=["repeat_visitor"],
        emotion="calm",
        prosody={"rate": "slow", "pitch": "+2%"},
        duration_estimate=1.5,
        energy_level=2
    ),
    
    # Question-based
    GreetingTemplate(
        text="Hi {name}! <break time='250ms'/> How have you been?",
        personality="warm",
        time_of_day=["any"],
        context_tags=["repeat_visitor"],
        emotion="curious",
        prosody={"rate": "medium", "pitch": "+7%"},
        duration_estimate=2.2,
        energy_level=3
    ),
    
    # Evening-specific
    GreetingTemplate(
        text="Good evening, {name}. Welcome back.",
        personality="professional",
        time_of_day=["evening"],
        context_tags=["repeat_visitor"],
        emotion="calm",
        prosody={"rate": "medium", "pitch": "+3%"},
        duration_estimate=2.0,
        energy_level=2
    ),
    
    # Surprised/delighted
    GreetingTemplate(
        text="Oh, {name}! <break time='400ms'/> What a nice surprise!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["unexpected_visitor"],
        emotion="excited",
        prosody={"rate": "fast", "pitch": "+15%", "emphasis": "strong"},
        duration_estimate=2.5,
        energy_level=5
    ),
    
    # More variations for rich diversity...
]
```

**For Unknown Persons** (12+ variations)
```python
UNKNOWN_TEMPLATES = [
    # Friendly introduction
    GreetingTemplate(
        text="Hello there! <break time='300ms'/> I'm Reachy. Nice to meet you!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+8%"},
        duration_estimate=3.0,
        energy_level=4
    ),
    
    # Curious
    GreetingTemplate(
        text="Oh hello! <break time='200ms'/> I don't think we've met. What's your name?",
        personality="playful",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="curious",
        prosody={"rate": "fast", "pitch": "+10%"},
        duration_estimate=3.5,
        energy_level=4
    ),
    
    # Professional welcome
    GreetingTemplate(
        text="Good morning. Welcome. I'm Reachy.",
        personality="professional",
        time_of_day=["morning"],
        context_tags=["first_meeting"],
        emotion="calm",
        prosody={"rate": "medium", "pitch": "+2%"},
        duration_estimate=2.0,
        energy_level=2
    ),
    
    # Warm invitation
    GreetingTemplate(
        text="Hi there! <break time='250ms'/> I haven't seen you before. Welcome!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+7%"},
        duration_estimate=3.0,
        energy_level=3
    ),
    
    # Excited to meet
    GreetingTemplate(
        text="Hey! <break time='200ms'/> Are you new here? I'm Reachy, nice to meet you!",
        personality="playful",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="excited",
        prosody={"rate": "fast", "pitch": "+12%"},
        duration_estimate=3.5,
        energy_level=5
    ),
    
    # Simple and gentle
    GreetingTemplate(
        text="Hello. I'm Reachy. <break time='300ms'/> Nice to meet you.",
        personality="neutral",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="calm",
        prosody={"rate": "slow", "pitch": "+3%"},
        duration_estimate=2.5,
        energy_level=2
    ),
    
    # Afternoon specific
    GreetingTemplate(
        text="Good afternoon! I don't think we've been introduced. I'm Reachy.",
        personality="professional",
        time_of_day=["afternoon"],
        context_tags=["first_meeting"],
        emotion="calm",
        prosody={"rate": "medium", "pitch": "+4%"},
        duration_estimate=3.0,
        energy_level=3
    ),
    
    # Friendly question
    GreetingTemplate(
        text="Oh hi! <break time='250ms'/> You're new here, right? Welcome!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["first_meeting"],
        emotion="curious",
        prosody={"rate": "medium", "pitch": "+6%"},
        duration_estimate=2.8,
        energy_level=3
    ),
    
    # More variations for diversity...
]
```

**For Departures** (8+ variations)
```python
DEPARTED_TEMPLATES = [
    # Warm goodbye
    GreetingTemplate(
        text="Goodbye, {name}! See you soon!",
        personality="warm",
        time_of_day=["any"],
        context_tags=["known_person"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+5%"},
        duration_estimate=2.0,
        energy_level=3
    ),
    
    # Evening goodbye
    GreetingTemplate(
        text="Have a great evening, {name}!",
        personality="warm",
        time_of_day=["evening"],
        context_tags=["known_person"],
        emotion="happy",
        prosody={"rate": "medium", "pitch": "+4%"},
        duration_estimate=1.8,
        energy_level=2
    ),
    
    # Playful
    GreetingTemplate(
        text="Bye {name}! <break time='200ms'/> Come back soon!",
        personality="playful",
        time_of_day=["any"],
        context_tags=["known_person"],
        emotion="happy",
        prosody={"rate": "fast", "pitch": "+8%"},
        duration_estimate=2.2,
        energy_level=4
    ),
    
    # Professional
    GreetingTemplate(
        text="Take care, {name}.",
        personality="professional",
        time_of_day=["any"],
        context_tags=["known_person"],
        emotion="calm",
        prosody={"rate": "medium", "pitch": "medium"},
        duration_estimate=1.2,
        energy_level=2
    ),
    
    # More variations...
]
```

### 2. Adaptive TTS Manager (Multi-Backend)

**File**: `adaptive_tts_manager.py`

#### Backend Priority System

```python
class VoiceBackend(Enum):
    """Available voice backends in priority order."""
    OPENAI_TTS = "openai"           # Primary: Best quality, natural
    AZURE_NEURAL = "azure"          # Secondary: High quality, SSML
    PYTTSX3 = "pyttsx3"            # Fallback: Local, always works
    ELEVENLABS = "elevenlabs"       # Optional: Premium quality
    GOOGLE_TTS = "google"           # Optional: Good quality
```

#### Smart Backend Selection

```python
class AdaptiveTTSManager:
    """
    TTS manager with automatic backend selection and failover.
    """
    
    def __init__(
        self,
        primary_backend: VoiceBackend = VoiceBackend.OPENAI_TTS,
        enable_caching: bool = True,
        cache_duration: int = 3600,  # 1 hour
        max_retries: int = 2,
        timeout: float = 3.0  # seconds
    ):
        self.backends = self._initialize_backends()
        self.cache = GreetingCache() if enable_caching else None
        
        # Performance tracking
        self.backend_stats = {
            backend: {
                'successes': 0,
                'failures': 0,
                'avg_latency': 0.0,
                'last_failure': None
            }
            for backend in VoiceBackend
        }
    
    async def speak_greeting(
        self,
        template: GreetingTemplate,
        priority: Priority = Priority.NORMAL
    ) -> SpeechResult:
        """
        Synthesize and play greeting with automatic failover.
        
        Flow:
        1. Check cache for pre-generated audio
        2. Try primary backend (OpenAI)
        3. If fails, try secondary (Azure)
        4. If fails, use fallback (pyttsx3)
        5. Update backend statistics
        6. Cache result if successful
        """
        
        # Check cache first (instant playback)
        if self.cache:
            cached = self.cache.get(template.text)
            if cached:
                return self._play_cached(cached)
        
        # Try backends in order
        for backend in self._get_backend_order():
            try:
                result = await self._synthesize(backend, template)
                self._record_success(backend, result.latency)
                
                # Cache for future use
                if self.cache:
                    self.cache.store(template.text, result.audio_data)
                
                return result
                
            except Exception as e:
                logger.warning(f"{backend.value} failed: {e}")
                self._record_failure(backend)
                continue
        
        # All backends failed - emergency fallback
        logger.error("All TTS backends failed - using silent mode")
        return SpeechResult(success=False, backend=None)
```

#### OpenAI TTS Integration (Primary)

```python
class OpenAITTSBackend:
    """
    OpenAI TTS-1 backend - Best quality/latency balance.
    
    Voice: 'nova' (warm, engaging female voice)
    Model: tts-1 (fast, optimized for real-time)
    Format: mp3 (then convert to wav for playback)
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.voice = "nova"  # Options: alloy, echo, fable, onyx, nova, shimmer
        self.model = "tts-1"  # vs tts-1-hd (slower but higher quality)
    
    async def synthesize(
        self,
        text: str,
        prosody: Dict[str, str]
    ) -> AudioData:
        """
        Generate speech with OpenAI TTS.
        
        Note: OpenAI TTS doesn't support SSML, but has good natural prosody.
        We strip SSML tags and rely on natural voice variation.
        """
        
        # Strip SSML tags (OpenAI doesn't support them)
        clean_text = self._strip_ssml(text)
        
        # Map prosody hints to voice selection
        voice = self._select_voice_for_prosody(prosody)
        
        start_time = time.time()
        
        response = await asyncio.to_thread(
            self.client.audio.speech.create,
            model=self.model,
            voice=voice,
            input=clean_text,
            response_format="mp3"
        )
        
        # Get audio data
        audio_data = response.content
        
        latency = time.time() - start_time
        
        return AudioData(
            data=audio_data,
            format="mp3",
            latency=latency,
            backend=VoiceBackend.OPENAI_TTS
        )
    
    def _select_voice_for_prosody(self, prosody: Dict[str, str]) -> str:
        """
        Map prosody hints to best OpenAI voice.
        
        Voices:
        - alloy: neutral, balanced
        - echo: male, clear
        - fable: British male, expressive
        - onyx: deep male, authoritative
        - nova: warm female, engaging (DEFAULT)
        - shimmer: bright female, energetic
        """
        
        pitch = prosody.get("pitch", "medium")
        rate = prosody.get("rate", "medium")
        emphasis = prosody.get("emphasis", "moderate")
        
        # Energetic/playful -> shimmer
        if rate == "fast" and pitch in ["+8%", "+10%", "+12%", "+15%"]:
            return "shimmer"
        
        # Calm/professional -> alloy
        if rate == "slow" or pitch == "medium":
            return "alloy"
        
        # Default warm/engaging -> nova
        return "nova"
```

#### Azure Neural TTS Integration (Secondary)

```python
class AzureNeuralTTSBackend:
    """
    Azure Neural TTS - High quality with SSML support.
    
    Voice: en-US-JennyNeural (warm, natural female)
    Supports: Full SSML with prosody control
    """
    
    def __init__(self):
        import azure.cognitiveservices.speech as speechsdk
        
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_SPEECH_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION", "eastus")
        )
        
        self.speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        # Other options: AriaNeural, GuyNeural, JaneNeural
        
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
    
    async def synthesize(
        self,
        text: str,
        prosody: Dict[str, str]
    ) -> AudioData:
        """
        Generate speech with Azure Neural TTS.
        
        Advantage: Full SSML support with prosody control.
        """
        
        ssml = self._build_ssml(text, prosody)
        
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=None  # No audio output, we'll get the data
        )
        
        start_time = time.time()
        
        result = await asyncio.to_thread(
            synthesizer.speak_ssml_async(ssml).get
        )
        
        latency = time.time() - start_time
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return AudioData(
                data=result.audio_data,
                format="mp3",
                latency=latency,
                backend=VoiceBackend.AZURE_NEURAL
            )
        else:
            raise Exception(f"Azure TTS failed: {result.reason}")
    
    def _build_ssml(self, text: str, prosody: Dict[str, str]) -> str:
        """
        Build SSML with full prosody control.
        
        SSML Example:
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-JennyNeural">
                <prosody rate="fast" pitch="+10%" volume="loud">
                    Hello there!
                </prosody>
            </voice>
        </speak>
        """
        
        rate = prosody.get("rate", "medium")
        pitch = prosody.get("pitch", "medium")
        volume = prosody.get("volume", "medium")
        
        # Convert rate to percentage
        rate_map = {"slow": "-20%", "medium": "+0%", "fast": "+20%"}
        rate_value = rate_map.get(rate, rate)
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
            <voice name="en-US-JennyNeural">
                <prosody rate="{rate_value}" pitch="{pitch}" volume="{volume}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        
        return ssml.strip()
```

#### Intelligent Caching System

```python
class GreetingCache:
    """
    Cache pre-generated greetings for instant playback.
    
    Strategy:
    - Pre-generate common greetings at startup
    - Cache on-demand generations
    - LRU eviction when cache full
    - Invalidate on voice backend change
    """
    
    def __init__(
        self,
        max_size: int = 100,  # Max cached greetings
        cache_dir: Path = Path("cache/greetings")
    ):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache: Dict[str, CachedGreeting] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
    
    async def pre_generate_common_greetings(
        self,
        templates: List[GreetingTemplate],
        backend: VoiceBackend
    ):
        """
        Pre-generate most common greetings at startup.
        
        Generates top 20 most likely greetings in background
        for instant playback when needed.
        """
        
        # Sort by expected frequency
        common = sorted(
            templates,
            key=lambda t: self._estimate_frequency(t),
            reverse=True
        )[:20]
        
        logger.info(f"Pre-generating {len(common)} common greetings...")
        
        tasks = [
            self._generate_and_cache(template, backend)
            for template in common
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"Pre-generation complete. Cache size: {len(self.cache)}")
    
    def get(self, text: str) -> Optional[AudioData]:
        """Get cached greeting if available."""
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.cache:
            self.access_times[cache_key] = time.time()
            cached = self.cache[cache_key]
            
            logger.debug(f"Cache HIT: {text[:50]}...")
            return cached.audio_data
        
        logger.debug(f"Cache MISS: {text[:50]}...")
        return None
    
    def store(self, text: str, audio_data: AudioData):
        """Store greeting in cache."""
        cache_key = self._get_cache_key(text)
        
        # Evict if cache full
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[cache_key] = CachedGreeting(
            text=text,
            audio_data=audio_data,
            created_at=time.time()
        )
        self.access_times[cache_key] = time.time()
    
    def _evict_lru(self):
        """Remove least recently used item."""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times, key=self.access_times.get)
        del self.cache[lru_key]
        del self.access_times[lru_key]
        logger.debug(f"Evicted LRU cache entry")
```

### 3. Performance Optimization

#### Latency Breakdown & Targets

```
Total End-to-End Latency Target: <400ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Component                    Target      Current     Strategy
────────────────────────────────────────────────────────────
Face Detection              50ms        ✓ 45ms      Optimized
Event Processing            10ms        ✓ 8ms       Fast path
Greeting Selection          20ms        NEW         In-memory
TTS Generation (OpenAI)     150ms       NEW         Async
Audio Playback Start        50ms        NEW         Stream
Behavior Coordination       100ms       ✓ 85ms      Parallel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL                       380ms       
```

#### Optimization Strategies

**1. Pre-generation**
- Generate common greetings at startup
- Cache in memory + disk
- Instant playback for cached greetings

**2. Streaming Playback**
- Start playing audio before full generation
- OpenAI supports streaming responses
- Reduces perceived latency by ~100ms

**3. Parallel Execution**
```python
async def greet_person_optimized(event: RecognitionEvent):
    """Parallel greeting execution for minimal latency."""
    
    # Start behavior immediately (non-blocking)
    behavior_task = asyncio.create_task(
        behavior_manager.execute_behavior_async(greeting_wave)
    )
    
    # Select greeting (fast, in-memory)
    template = greeting_selector.select_greeting(
        person_name=event.person_name,
        greeting_type=event.type,
        context=self._build_context()
    )
    
    # Generate speech (async)
    speech_task = asyncio.create_task(
        tts_manager.speak_greeting_async(template)
    )
    
    # Wait for both (they run in parallel)
    await asyncio.gather(behavior_task, speech_task)
```

**4. Predictive Generation**
```python
class PredictiveGenerator:
    """
    Predicts likely next greetings and pre-generates them.
    
    Example: When person approaches door, start generating
    their likely greeting before face is fully recognized.
    """
    
    def on_person_approaching(self, person_id: str):
        """Pre-generate greeting as person approaches."""
        likely_templates = self._predict_templates(person_id)
        asyncio.create_task(self._pre_generate(likely_templates))
```

### 4. Cost Management

#### API Usage Optimization

```python
class CostManager:
    """
    Manages API costs across voice backends.
    
    Strategies:
    - Use cached greetings when possible (free)
    - Batch pre-generation during low-usage times
    - Track costs per greeting
    - Alert on budget thresholds
    - Automatic fallback to pyttsx3 if budget exceeded
    """
    
    COSTS_PER_CHAR = {
        VoiceBackend.OPENAI_TTS: 0.000015,      # $15/1M chars
        VoiceBackend.AZURE_NEURAL: 0.000016,    # $16/1M chars
        VoiceBackend.ELEVENLABS: 0.0003,        # $300/1M chars (premium)
        VoiceBackend.PYTTSX3: 0.0,              # Free
    }
    
    def __init__(self, daily_budget: float = 5.0):
        self.daily_budget = daily_budget
        self.daily_usage = 0.0
        self.last_reset = datetime.now().date()
    
    def check_budget(self, text_length: int, backend: VoiceBackend) -> bool:
        """Check if generation fits within budget."""
        cost = text_length * self.COSTS_PER_CHAR[backend]
        
        if self.daily_usage + cost > self.daily_budget:
            logger.warning(
                f"Daily budget exceeded ({self.daily_usage:.2f}/{self.daily_budget})"
            )
            return False
        
        return True
    
    def record_usage(self, text_length: int, backend: VoiceBackend):
        """Record API usage."""
        cost = text_length * self.COSTS_PER_CHAR[backend]
        self.daily_usage += cost
        
        logger.info(
            f"TTS cost: ${cost:.4f} | Daily total: ${self.daily_usage:.2f}"
        )
```

#### Expected Monthly Costs

```
Scenario: Office robot, 50 greetings/day
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Backend         Greetings/Day   Cost/Day   Cost/Month
────────────────────────────────────────────────────
OpenAI TTS      50              $0.12      $3.60
Azure Neural    50              $0.13      $3.90
pyttsx3         ∞               $0.00      $0.00

With 80% Cache Hit Rate:
────────────────────────────────────────────────────
OpenAI TTS      10 (new)        $0.02      $0.72
Azure Neural    10 (new)        $0.03      $0.78

Recommendation: Use OpenAI with caching = ~$1/month
```

## Implementation Roadmap

### Phase 1: Foundation (Hours 1-2)
- [x] Design architecture
- [ ] Create `greeting_selector.py` with template system
- [ ] Create `adaptive_tts_manager.py` with backend abstraction
- [ ] Implement basic GreetingTemplate and selection logic
- [ ] Add 5+ templates for each greeting type

### Phase 2: Primary Backend (Hours 2-3)
- [ ] Implement OpenAI TTS backend
- [ ] Add async speech generation
- [ ] Implement caching system
- [ ] Test latency and quality

### Phase 3: Failover & Reliability (Hours 3-4)
- [ ] Implement Azure Neural backend (secondary)
- [ ] Add automatic failover logic
- [ ] Keep pyttsx3 as ultimate fallback
- [ ] Test backend switching

### Phase 4: Optimization (Hours 4-5)
- [ ] Add pre-generation at startup
- [ ] Implement parallel execution
- [ ] Add streaming playback
- [ ] Optimize cache hit rate

### Phase 5: Integration (Hours 5-6)
- [ ] Integrate with GreetingCoordinator
- [ ] Update behavior timing for voice
- [ ] Add cost tracking
- [ ] Comprehensive testing

### Phase 6: Polish & Testing (Hour 6)
- [ ] Test all greeting variations
- [ ] Verify <400ms latency
- [ ] Test failover scenarios
- [ ] Document configuration

## Configuration

### Environment Variables
```bash
# OpenAI TTS (Primary - Recommended)
OPENAI_API_KEY=sk-...

# Azure Neural TTS (Secondary - Optional)
AZURE_SPEECH_KEY=...
AZURE_SPEECH_REGION=eastus

# ElevenLabs (Premium - Optional)
ELEVENLABS_API_KEY=...
```

### YAML Configuration
```yaml
# config/voice_response.yaml

voice:
  # Backend priority order
  backends:
    primary: openai
    secondary: azure
    fallback: pyttsx3
  
  # OpenAI TTS settings
  openai:
    model: tts-1  # or tts-1-hd for higher quality
    voice: nova   # alloy, echo, fable, onyx, nova, shimmer
    
  # Azure Neural TTS settings
  azure:
    voice: en-US-JennyNeural
    
  # pyttsx3 settings (local fallback)
  pyttsx3:
    rate: 160
    volume: 0.9
    voice_preference: female

greeting_selector:
  personality: warm  # warm, professional, playful, neutral
  non_repetition_window: 5  # Avoid last N greetings
  enable_time_context: true
  enable_person_history: true

caching:
  enabled: true
  max_cache_size: 100
  pre_generate_common: true
  cache_dir: cache/greetings

performance:
  latency_target_ms: 400
  enable_parallel_execution: true
  enable_predictive_generation: false  # Experimental

cost_management:
  enabled: true
  daily_budget_usd: 5.0
  alert_threshold: 0.8  # Alert at 80% of budget
  auto_fallback_on_budget: true
```

## Testing Strategy

### Test 1: Voice Quality Assessment
```python
async def test_voice_quality():
    """Subjective quality test across backends."""
    
    test_phrases = [
        "Welcome back, Sarah!",
        "Hello there! Nice to meet you!",
        "Good morning! Great to see you."
    ]
    
    for backend in [VoiceBackend.OPENAI_TTS, VoiceBackend.AZURE_NEURAL]:
        for phrase in test_phrases:
            audio = await tts.synthesize(phrase, backend)
            # Manual listening assessment
            # Rate: 1-10 for naturalness, clarity, emotion
```

### Test 2: Latency Benchmark
```python
async def test_latency():
    """Measure end-to-end latency."""
    
    results = []
    
    for i in range(100):
        start = time.time()
        
        # Full greeting flow
        template = selector.select_greeting(...)
        await tts.speak_greeting(template)
        
        latency = time.time() - start
        results.append(latency)
    
    print(f"Mean: {np.mean(results)*1000:.0f}ms")
    print(f"P95: {np.percentile(results, 95)*1000:.0f}ms")
    print(f"P99: {np.percentile(results, 99)*1000:.0f}ms")
    
    # Target: P95 < 400ms
    assert np.percentile(results, 95) < 0.4
```

### Test 3: Variation Testing
```python
def test_greeting_variation():
    """Verify no repetition in greetings."""
    
    greetings = []
    for i in range(20):
        template = selector.select_greeting(
            person_name="Test",
            greeting_type=GreetingType.RECOGNIZED,
            context=build_context()
        )
        greetings.append(template.text)
    
    # Check no consecutive duplicates
    for i in range(len(greetings) - 1):
        assert greetings[i] != greetings[i+1], \
            f"Consecutive duplicate at position {i}"
    
    # Check diversity (at least 10 unique in 20 greetings)
    unique = len(set(greetings))
    assert unique >= 10, f"Only {unique} unique greetings in 20 attempts"
```

### Test 4: Failover Resilience
```python
async def test_backend_failover():
    """Test automatic failover when backend fails."""
    
    # Simulate primary backend failure
    tts.backends[VoiceBackend.OPENAI_TTS].force_failure = True
    
    # Should automatically use secondary
    result = await tts.speak_greeting(template)
    
    assert result.success
    assert result.backend == VoiceBackend.AZURE_NEURAL
    
    # Simulate all API backends failing
    for backend in [VoiceBackend.OPENAI_TTS, VoiceBackend.AZURE_NEURAL]:
        tts.backends[backend].force_failure = True
    
    # Should fall back to pyttsx3
    result = await tts.speak_greeting(template)
    
    assert result.success
    assert result.backend == VoiceBackend.PYTTSX3
```

## Success Metrics

### Quantitative Targets
- **Voice Quality**: Subjective rating 8+/10 (vs 5/10 baseline)
- **Latency P95**: <400ms end-to-end
- **Greeting Diversity**: 0% consecutive repetition, 80%+ unique in 10
- **Cache Hit Rate**: 60%+ for common greetings
- **Uptime**: 99.9%+ with failover
- **Cost**: <$5/month for typical office usage
- **API Success Rate**: 95%+ for primary backend

### Qualitative Goals
- Natural, engaging voice that doesn't sound robotic
- Varied greetings that don't feel repetitive
- Contextually appropriate responses
- Smooth coordination with physical behaviors
- Reliable performance in all network conditions

## Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API rate limits | High | Medium | Implement caching, use multiple backends |
| High API costs | Medium | Low | Cost tracking, budget limits, cache aggressively |
| Network failures | High | Medium | Local fallback (pyttsx3), offline mode |
| Increased latency | High | Medium | Parallel execution, pre-generation, streaming |
| Voice quality varies | Medium | Low | Careful voice selection, SSML tuning |
| Template exhaustion | Low | Low | 15+ templates per type, graceful fallback |

## Future Enhancements

### Post-MVP (Story 4.x+)
1. **Dynamic Voice Cloning**: Clone specific voices for personalization
2. **Emotion Detection**: Adjust greeting tone based on detected emotion
3. **Multi-Language Support**: Detect language preference, respond accordingly
4. **Conversation Memory**: Reference previous interactions in greetings
5. **A/B Testing**: Experiment with different greeting styles
6. **Voice Analytics**: Track which greetings get best reception
7. **Custom Vocabulary**: Add domain-specific terms with pronunciation guides
8. **Real-time Voice Modulation**: Adjust prosody based on real-time feedback

## Conclusion

This design provides a production-quality voice response system that:

✅ **Sounds Natural**: OpenAI TTS voices are engaging and human-like  
✅ **Never Repeats**: 15+ templates per type with smart selection  
✅ **Stays Fast**: <400ms latency with caching and parallel execution  
✅ **Always Works**: Automatic failover to local TTS if APIs unavailable  
✅ **Costs Little**: ~$1-5/month with intelligent caching  
✅ **Scales Easily**: Add new backends, templates, or features modularly  

The system is designed to delight users with varied, natural interactions while maintaining the reliability and performance required for production deployment.

---

**Next Steps**: Review this design, then proceed with implementation in Story 3.4 Phase 3.
