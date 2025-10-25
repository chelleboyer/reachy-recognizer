"""
Adaptive TTS Manager - Story 3.4 (Voice Enhancement)

Multi-backend TTS system with automatic failover and intelligent caching
for natural, reliable voice synthesis.

Backends (in priority order):
1. OpenAI TTS (primary) - Best quality, fast, natural
2. Azure Neural TTS (secondary) - High quality, SSML support
3. pyttsx3 (fallback) - Local, always available

Features:
- Automatic backend selection and failover
- Intelligent caching for common greetings
- Async speech generation
- Backend health tracking
- Cost management and tracking
"""

import asyncio
import os
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, List
from collections import deque
import hashlib

# Try importing optional backends
try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available - install with: pip install openai")

try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Azure Speech SDK not available - install with: pip install azure-cognitiveservices-speech")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("Warning: pyttsx3 not available")

# Audio playback (optional)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Note: pygame not available for MP3 playback - install with: pip install pygame")

from .greeting_selector import GreetingTemplate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import config (optional - falls back to defaults)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default TTS settings")


def play_audio_data(audio_data: bytes, format: str = "mp3"):
    """
    Play audio data using pygame.
    
    Args:
        audio_data: Audio bytes
        format: Audio format ('mp3', 'wav', etc.)
    """
    if not PYGAME_AVAILABLE:
        logger.warning("pygame not available - cannot play audio")
        return
    
    try:
        # Initialize pygame mixer if not already initialized
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        
        # Create temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name
        
        try:
            # Play the audio
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        finally:
            # Clean up temp file
            import time
            time.sleep(0.1)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass  # Ignore cleanup errors
        
    except Exception as e:
        logger.error(f"Audio playback error: {e}")


class VoiceBackend(Enum):
    """Available voice backends in priority order."""
    OPENAI_TTS = "openai"
    AZURE_NEURAL = "azure"
    PYTTSX3 = "pyttsx3"


@dataclass
class AudioData:
    """Container for audio data with metadata."""
    data: bytes
    format: str  # 'mp3', 'wav', etc.
    latency: float  # Generation time in seconds
    backend: VoiceBackend
    cached: bool = False


@dataclass
class SpeechResult:
    """Result of speech synthesis attempt."""
    success: bool
    audio_data: Optional[AudioData] = None
    error: Optional[str] = None
    backend_used: Optional[VoiceBackend] = None
    latency: float = 0.0


@dataclass
class BackendStats:
    """Statistics for a voice backend."""
    successes: int = 0
    failures: int = 0
    total_latency: float = 0.0
    last_failure_time: Optional[float] = None
    last_failure_reason: Optional[str] = None
    
    @property
    def avg_latency(self) -> float:
        """Calculate average latency."""
        if self.successes == 0:
            return 0.0
        return self.total_latency / self.successes
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        total = self.successes + self.failures
        if total == 0:
            return 0.0
        return (self.successes / total) * 100


@dataclass
class CachedGreeting:
    """Cached greeting with metadata."""
    text: str
    audio_data: AudioData
    created_at: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)


class GreetingCache:
    """
    LRU cache for pre-generated greetings.
    
    Stores common greetings in memory for instant playback,
    reducing API calls and latency.
    """
    
    def __init__(
        self,
        max_size: int = 50,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize greeting cache.
        
        Args:
            max_size: Maximum number of cached greetings
            cache_dir: Optional directory for persistent cache
        """
        self.max_size = max_size
        self.cache_dir = cache_dir
        
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache: Dict[str, CachedGreeting] = {}
        self.access_order: deque = deque()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        logger.info(f"GreetingCache initialized: max_size={max_size}")
    
    def get(self, text: str) -> Optional[AudioData]:
        """
        Get cached greeting if available.
        
        Args:
            text: Greeting text to look up
            
        Returns:
            Cached audio data or None
        """
        cache_key = self._get_cache_key(text)
        
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            cached.access_count += 1
            cached.last_access = time.time()
            
            # Update access order
            if cache_key in self.access_order:
                self.access_order.remove(cache_key)
            self.access_order.append(cache_key)
            
            self.hits += 1
            logger.debug(f"Cache HIT: '{text[:50]}...'")
            
            # Mark as cached
            audio = cached.audio_data
            audio.cached = True
            return audio
        
        self.misses += 1
        logger.debug(f"Cache MISS: '{text[:50]}...'")
        return None
    
    def store(self, text: str, audio_data: AudioData):
        """
        Store greeting in cache.
        
        Args:
            text: Greeting text
            audio_data: Generated audio data
        """
        cache_key = self._get_cache_key(text)
        
        # Evict if cache full
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            self._evict_lru()
        
        # Store in cache
        self.cache[cache_key] = CachedGreeting(
            text=text,
            audio_data=audio_data,
            created_at=time.time()
        )
        
        # Update access order
        if cache_key in self.access_order:
            self.access_order.remove(cache_key)
        self.access_order.append(cache_key)
        
        logger.debug(f"Cached: '{text[:50]}...'")
    
    def _evict_lru(self):
        """Remove least recently used item."""
        if not self.access_order:
            return
        
        lru_key = self.access_order.popleft()
        if lru_key in self.cache:
            del self.cache[lru_key]
            logger.debug("Evicted LRU cache entry")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.md5(text.encode()).hexdigest()
    
    def get_statistics(self) -> Dict:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }
    
    def clear(self):
        """Clear all cached greetings."""
        self.cache.clear()
        self.access_order.clear()
        logger.info("Cache cleared")


class OpenAITTSBackend:
    """
    OpenAI TTS backend - Primary voice provider.
    
    Uses OpenAI's TTS-1 model with 'nova' voice for natural,
    engaging speech synthesis.
    """
    
    def __init__(self):
        """Initialize OpenAI TTS backend."""
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "tts-1"  # Fast model optimized for real-time
        self.default_voice = "shimmer"  # Bright, energetic female voice
        
        # Voice mapping for prosody
        self.voice_map = {
            'energetic': 'shimmer',  # Bright, energetic
            'calm': 'alloy',         # Neutral, balanced
            'professional': 'alloy',  # Clear, professional
            'warm': 'shimmer',       # Warm, engaging
            'playful': 'shimmer'     # Bright, playful
        }
        
        logger.info("OpenAI TTS backend initialized")
    
    async def synthesize(
        self,
        template: GreetingTemplate,
        stream_playback: bool = True
    ) -> AudioData:
        """
        Generate speech with OpenAI TTS, optionally with streaming playback.
        
        Args:
            template: Greeting template with text and prosody hints
            stream_playback: If True, start playback as soon as first chunk arrives
            
        Returns:
            Generated audio data
        """
        start_time = time.time()
        
        # Clean text (remove SSML tags OpenAI doesn't support)
        clean_text = self._strip_ssml(template.text)
        
        # Select voice based on prosody/emotion
        voice = self._select_voice(template)
        logger.info(f"🎤 Using OpenAI voice: '{voice}' (emotion: {template.emotion})")
        
        try:
            # Generate speech - OpenAI returns the full audio
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=clean_text,
                response_format="mp3"
            )
            
            # Get audio data
            audio_bytes = response.content
            
            latency = time.time() - start_time
            
            logger.debug(
                f"OpenAI TTS generated {len(audio_bytes)} bytes "
                f"in {latency:.3f}s (voice={voice})"
            )
            
            return AudioData(
                data=audio_bytes,
                format="mp3",
                latency=latency,
                backend=VoiceBackend.OPENAI_TTS
            )
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise
    
    def _strip_ssml(self, text: str) -> str:
        """Remove SSML tags (OpenAI doesn't support them)."""
        import re
        # Remove <break> tags
        text = re.sub(r'<break\s+time=[\'"][^\'"]*[\'"]\s*/>', ' ', text)
        # Remove other tags
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()
    
    def _select_voice(self, template: GreetingTemplate) -> str:
        """
        Select appropriate voice based on template metadata.
        
        Available voices:
        - alloy: neutral, balanced
        - echo: male, clear
        - fable: British male, expressive
        - onyx: deep male, authoritative
        - nova: warm female, engaging
        - shimmer: bright female, energetic (DEFAULT - use for all greetings)
        """
        # Map ALL emotions to shimmer for consistent bright, energetic voice
        emotion_map = {
            'excited': 'shimmer',
            'playful': 'shimmer',
            'happy': 'shimmer',      # Changed from 'nova' to 'shimmer'
            'curious': 'shimmer',    # Changed from 'nova' to 'shimmer'
            'calm': 'shimmer',       # Changed from 'alloy' to 'shimmer'
            'professional': 'shimmer' # Changed from 'alloy' to 'shimmer'
        }
        
        return emotion_map.get(template.emotion, self.default_voice)


class Pyttsx3Backend:
    """
    pyttsx3 TTS backend - Local fallback.
    
    Provides offline text-to-speech capability with no API calls.
    Lower quality but always available.
    """
    
    def __init__(
        self,
        rate: int = 160,
        volume: float = 0.9
    ):
        """Initialize pyttsx3 backend."""
        if not PYTTSX3_AVAILABLE:
            raise ImportError("pyttsx3 not available")
        
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', rate)
        self.engine.setProperty('volume', volume)
        
        # Try to set female voice
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        logger.info("pyttsx3 backend initialized (fallback)")
    
    async def synthesize(
        self,
        template: GreetingTemplate
    ) -> AudioData:
        """
        Generate speech with pyttsx3.
        
        Note: This is synchronous under the hood, we wrap it in async.
        """
        start_time = time.time()
        
        # Clean text
        clean_text = self._strip_ssml(template.text)
        
        # pyttsx3 doesn't generate audio data directly in memory easily
        # For now, we'll use it for playback only (not caching)
        # This is a simplified implementation
        
        # Speak directly (synchronous)
        await asyncio.to_thread(self._speak_sync, clean_text)
        
        latency = time.time() - start_time
        
        # Return dummy audio data (pyttsx3 speaks directly)
        return AudioData(
            data=b'',  # No data (spoke directly)
            format='none',
            latency=latency,
            backend=VoiceBackend.PYTTSX3
        )
    
    def _speak_sync(self, text: str):
        """Synchronous speech (called in thread)."""
        self.engine.say(text)
        self.engine.runAndWait()
    
    def _strip_ssml(self, text: str) -> str:
        """Remove SSML tags."""
        import re
        text = re.sub(r'<break\s+time=[\'"][^\'"]*[\'"]\s*/>', ' ', text)
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()


class AdaptiveTTSManager:
    """
    Adaptive TTS manager with multi-backend support and failover.
    
    Automatically selects best available backend and falls back
    to alternatives if primary fails.
    """
    
    def __init__(
        self,
        enable_caching: Optional[bool] = None,
        cache_size: Optional[int] = None,
        cache_dir: Optional[Path] = None
    ):
        """
        Initialize adaptive TTS manager.
        
        Args:
            enable_caching: Enable greeting cache (default from config or True)
            cache_size: Maximum cached greetings (default from config or 50)
            cache_dir: Optional persistent cache directory (default from config or None)
        """
        # Load from config if available
        if _CONFIG_AVAILABLE:
            try:
                config = get_config()
                if enable_caching is None:
                    enable_caching = config.tts.cache.enabled
                if cache_size is None:
                    cache_size = config.tts.cache.max_size
                # Note: cache_dir can be passed explicitly, config doesn't have directory setting
                logger.info("Loaded TTS settings from config")
            except Exception as e:
                logger.warning(f"Failed to load TTS config: {e}")
        
        # Use defaults if still None
        if enable_caching is None:
            enable_caching = True
        if cache_size is None:
            cache_size = 50
        
        # Initialize cache
        self.cache = GreetingCache(cache_size, cache_dir) if enable_caching else None
        
        # Initialize backends (in priority order)
        self.backends: Dict[VoiceBackend, object] = {}
        self._initialize_backends()
        
        # Backend statistics
        self.stats: Dict[VoiceBackend, BackendStats] = {
            backend: BackendStats() for backend in VoiceBackend
        }
        
        # Overall statistics
        self.total_requests = 0
        self.total_successes = 0
        self.total_failures = 0
        
        logger.info(
            f"AdaptiveTTSManager initialized: "
            f"backends={list(self.backends.keys())}, "
            f"caching={'enabled' if self.cache else 'disabled'}"
        )
    
    def _initialize_backends(self):
        """Initialize available TTS backends."""
        # Try OpenAI (primary)
        if OPENAI_AVAILABLE:
            try:
                self.backends[VoiceBackend.OPENAI_TTS] = OpenAITTSBackend()
                logger.info("✓ OpenAI TTS backend available")
            except Exception as e:
                logger.warning(f"OpenAI TTS initialization failed: {e}")
        
        # Try pyttsx3 (fallback)
        if PYTTSX3_AVAILABLE:
            try:
                self.backends[VoiceBackend.PYTTSX3] = Pyttsx3Backend()
                logger.info("✓ pyttsx3 backend available (fallback)")
            except Exception as e:
                logger.warning(f"pyttsx3 initialization failed: {e}")
        
        if not self.backends:
            logger.error("No TTS backends available!")
    
    async def speak_greeting(
        self,
        template: GreetingTemplate
    ) -> SpeechResult:
        """
        Synthesize and return greeting audio with automatic failover.
        
        Flow:
        1. Check cache for pre-generated audio
        2. Try primary backend (OpenAI)
        3. If fails, try fallback (pyttsx3)
        4. Update statistics
        5. Cache result if successful
        
        Args:
            template: Greeting template to synthesize
            
        Returns:
            SpeechResult with audio data or error
        """
        self.total_requests += 1
        
        # Check cache first
        if self.cache:
            cached_audio = self.cache.get(template.text)
            if cached_audio:
                logger.info(f"Cache hit: '{template.text[:50]}...'")
                
                # Play the cached audio
                if cached_audio.data:
                    play_audio_data(cached_audio.data, cached_audio.format)
                
                return SpeechResult(
                    success=True,
                    audio_data=cached_audio,
                    backend_used=cached_audio.backend,
                    latency=0.0  # Instant from cache
                )
        
        # Try backends in priority order
        for backend_type in self._get_backend_priority():
            if backend_type not in self.backends:
                continue
            
            backend = self.backends[backend_type]
            
            try:
                logger.debug(f"Trying {backend_type.value} backend...")
                audio_data = await backend.synthesize(template)
                
                # Record success
                self._record_success(backend_type, audio_data.latency)
                self.total_successes += 1
                
                # Cache for future use
                if self.cache and audio_data.data:  # Don't cache pyttsx3 (no data)
                    self.cache.store(template.text, audio_data)
                
                logger.info(
                    f"✓ {backend_type.value}: '{template.text[:50]}...' "
                    f"({audio_data.latency:.3f}s)"
                )
                
                # Play the audio if we have data
                if audio_data.data:
                    play_audio_data(audio_data.data, audio_data.format)
                
                return SpeechResult(
                    success=True,
                    audio_data=audio_data,
                    backend_used=backend_type,
                    latency=audio_data.latency
                )
                
            except Exception as e:
                # Record failure
                self._record_failure(backend_type, str(e))
                logger.warning(f"{backend_type.value} failed: {e}")
                continue
        
        # All backends failed
        self.total_failures += 1
        logger.error("All TTS backends failed!")
        
        return SpeechResult(
            success=False,
            error="All TTS backends failed",
            latency=0.0
        )
    
    def _get_backend_priority(self) -> List[VoiceBackend]:
        """Get backends in priority order."""
        # Priority: OpenAI -> pyttsx3
        priority = [
            VoiceBackend.OPENAI_TTS,
            VoiceBackend.PYTTSX3
        ]
        
        # Only return available backends
        return [b for b in priority if b in self.backends]
    
    def _record_success(self, backend: VoiceBackend, latency: float):
        """Record successful backend usage."""
        stats = self.stats[backend]
        stats.successes += 1
        stats.total_latency += latency
    
    def _record_failure(self, backend: VoiceBackend, reason: str):
        """Record backend failure."""
        stats = self.stats[backend]
        stats.failures += 1
        stats.last_failure_time = time.time()
        stats.last_failure_reason = reason
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics."""
        overall_stats = {
            'total_requests': self.total_requests,
            'total_successes': self.total_successes,
            'total_failures': self.total_failures,
            'success_rate': f"{(self.total_successes / max(self.total_requests, 1) * 100):.1f}%"
        }
        
        backend_stats = {}
        for backend, stats in self.stats.items():
            if backend in self.backends:
                backend_stats[backend.value] = {
                    'successes': stats.successes,
                    'failures': stats.failures,
                    'avg_latency': f"{stats.avg_latency:.3f}s",
                    'success_rate': f"{stats.success_rate:.1f}%"
                }
        
        cache_stats = self.cache.get_statistics() if self.cache else None
        
        return {
            'overall': overall_stats,
            'backends': backend_stats,
            'cache': cache_stats
        }


async def main():
    """Test adaptive TTS manager."""
    print("\n" + "="*60)
    print("Adaptive TTS Manager Test")
    print("="*60)
    
        # Import demo dependencies
    from .greeting_selector import GreetingSelector, GreetingType, GreetingContext
    
    # Initialize systems
    tts = AdaptiveTTSManager(enable_caching=True)
    selector = GreetingSelector(personality="warm")
    
    # Test greetings
    print("\n--- Testing TTS with Various Greetings ---\n")
    
    test_cases = [
        ("Sarah", GreetingType.RECOGNIZED),
        (None, GreetingType.UNKNOWN),
        ("Sarah", GreetingType.RECOGNIZED),  # Should hit cache
        ("John", GreetingType.RECOGNIZED),
        ("Sarah", GreetingType.DEPARTED),
    ]
    
    for person_name, greeting_type in test_cases:
        context = GreetingContext(
            time_of_day=selector.get_time_of_day()
        )
        
        # Select greeting
        template = selector.select_greeting(
            person_name=person_name,
            greeting_type=greeting_type,
            context=context
        )
        
        print(f"Greeting: '{template.text}'")
        print(f"  Emotion: {template.emotion}, Energy: {template.energy_level}")
        
        # Synthesize
        result = await tts.speak_greeting(template)
        
        if result.success:
            cached = result.audio_data.cached if result.audio_data else False
            print(f"  ✓ {result.backend_used.value}: {result.latency:.3f}s "
                  f"({'cached' if cached else 'generated'})")
        else:
            print(f"  ✗ Failed: {result.error}")
        
        print()
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Statistics
    print("\n--- Statistics ---")
    stats = tts.get_statistics()
    
    print("\nOverall:")
    for key, value in stats['overall'].items():
        print(f"  {key}: {value}")
    
    print("\nBackends:")
    for backend, backend_stats in stats['backends'].items():
        print(f"  {backend}:")
        for key, value in backend_stats.items():
            print(f"    {key}: {value}")
    
    if stats['cache']:
        print("\nCache:")
        for key, value in stats['cache'].items():
            print(f"  {key}: {value}")
    
    print("\n✓ Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
