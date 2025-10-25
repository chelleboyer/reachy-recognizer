"""
Text-to-Speech Module - Story 3.2

Implements text-to-speech functionality for Reachy using pyttsx3,
enabling natural spoken greetings and responses.

This module provides non-blocking TTS with thread-safe queuing and
graceful error handling.
"""

import pyttsx3
import threading
import queue
import logging
import random
import time
from typing import Optional, List, Dict
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GreetingType(Enum):
    """Types of greetings."""
    RECOGNIZED = "recognized"
    UNKNOWN = "unknown"
    DEPARTED = "departed"
    GENERAL = "general"


# Greeting phrase templates (AC: 2)
GREETINGS: Dict[str, List[str]] = {
    'recognized': [
        "Hello {name}!",
        "Hi {name}! Good to see you!",
        "Hey {name}, how are you?",
        "Welcome back, {name}!"
    ],
    'unknown': [
        "Hi there! I don't think we've met yet.",
        "Hello! Nice to meet you!",
        "Hi! I'm Reachy. Who are you?",
        "Hello there! I don't believe we've been introduced."
    ],
    'departed': [
        "Goodbye {name}!",
        "See you later, {name}!",
        "Bye {name}!",
        "Take care, {name}!"
    ],
    'general': [
        "Hello!",
        "Hi there!",
        "Greetings!"
    ]
}


class TTSManager:
    """
    Text-to-Speech manager with non-blocking speech synthesis.
    
    Uses pyttsx3 for cross-platform TTS with thread-safe queuing
    to prevent blocking the main application.
    """
    
    def __init__(
        self,
        rate: int = 160,
        volume: float = 0.9,
        voice_preference: str = "female"
    ):
        """
        Initialize TTS manager.
        
        Args:
            rate: Speech rate in words per minute (150-180 recommended)
            volume: Volume level (0.0 to 1.0)
            voice_preference: Preferred voice type ('male', 'female', or voice ID)
        """
        self.rate = rate
        self.volume = volume
        self.voice_preference = voice_preference
        
        # TTS engine
        self.engine: Optional[pyttsx3.Engine] = None
        self.engine_available = False
        
        # Speech queue and worker thread
        self.speech_queue: queue.Queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        
        # Statistics
        self.speeches_queued = 0
        self.speeches_spoken = 0
        self.errors = 0
        
        # Initialize engine (AC: 1, 6)
        try:
            self._initialize_engine()
            self.engine_available = True
            logger.info("TTSManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            logger.warning("TTS will run in silent mode (no speech output)")
            self.engine_available = False
            
            # Start worker thread even in silent mode
            self.worker_thread = threading.Thread(
                target=self._speech_worker,
                daemon=True
            )
            self.worker_thread.start()
            logger.info("TTS worker thread started (silent mode)")
    
    def _initialize_engine(self):
        """Initialize pyttsx3 engine with configuration (AC: 1, 3, 4)."""
        self.engine = pyttsx3.init()
        
        # Configure voice (AC: 3)
        voices = self.engine.getProperty('voices')
        logger.info(f"Available voices: {len(voices)}")
        
        # Try to select preferred voice
        selected = False
        for voice in voices:
            voice_name = voice.name.lower()
            logger.debug(f"  Voice: {voice.name} (ID: {voice.id})")
            
            # Prefer female voice (Zira on Windows, Samantha on Mac)
            if self.voice_preference == "female":
                if any(name in voice_name for name in ['zira', 'samantha', 'victoria']):
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Selected voice: {voice.name}")
                    selected = True
                    break
            elif self.voice_preference == "male":
                if any(name in voice_name for name in ['david', 'alex']):
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Selected voice: {voice.name}")
                    selected = True
                    break
        
        if not selected and len(voices) > 0:
            # Use first available voice
            self.engine.setProperty('voice', voices[0].id)
            logger.info(f"Using default voice: {voices[0].name}")
        
        # Set speech rate (AC: 4)
        self.engine.setProperty('rate', self.rate)
        logger.info(f"Speech rate set to {self.rate} wpm")
        
        # Set volume
        self.engine.setProperty('volume', self.volume)
        logger.info(f"Volume set to {self.volume}")
        
        # Start worker thread (AC: 5)
        self.worker_thread = threading.Thread(
            target=self._speech_worker,
            daemon=True
        )
        self.worker_thread.start()
        logger.info("TTS worker thread started")
    
    def _speech_worker(self):
        """Worker thread to process speech queue (AC: 5)."""
        while not self.stop_flag.is_set():
            try:
                # Get speech request from queue (1 second timeout)
                text = self.speech_queue.get(timeout=1.0)
                
                if text is None:  # Shutdown signal
                    break
                
                # Synthesize speech
                if self.engine_available and self.engine is not None:
                    try:
                        self.engine.say(text)
                        self.engine.runAndWait()
                        self.speeches_spoken += 1
                        logger.debug(f"Spoke: \"{text}\"")
                    except Exception as e:
                        logger.error(f"TTS synthesis error: {e}")
                        self.errors += 1
                else:
                    # Silent mode - just log
                    logger.info(f"[SILENT MODE] Would say: \"{text}\"")
                    self.speeches_spoken += 1
                
            except queue.Empty:
                # No speech requests, continue waiting
                continue
            except Exception as e:
                logger.error(f"TTS worker error: {e}")
                self.errors += 1
    
    def speak(self, text: str) -> bool:
        """
        Queue text for speech synthesis (non-blocking).
        
        Args:
            text: Text to speak
            
        Returns:
            True if queued successfully, False otherwise
            
        Example:
            >>> tts = TTSManager()
            >>> tts.speak("Hello Alice!")
            True
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to speak()")
            return False
        
        try:
            self.speech_queue.put(text)
            self.speeches_queued += 1
            logger.debug(f"Queued: \"{text}\"")
            return True
        except Exception as e:
            logger.error(f"Failed to queue speech: {e}")
            self.errors += 1
            return False
    
    def speak_greeting(
        self,
        greeting_type: GreetingType,
        name: str = "",
        random_choice: bool = True
    ) -> bool:
        """
        Speak a greeting phrase (AC: 2).
        
        Args:
            greeting_type: Type of greeting
            name: Person's name (for personalized greetings)
            random_choice: If True, randomly select from available phrases
            
        Returns:
            True if queued successfully
            
        Example:
            >>> tts.speak_greeting(GreetingType.RECOGNIZED, "Alice")
            True  # Speaks: "Hello Alice!"
        """
        phrase = get_greeting(greeting_type.value, name, random_choice)
        return self.speak(phrase)
    
    def get_stats(self) -> Dict[str, int]:
        """Get TTS statistics."""
        return {
            "speeches_queued": self.speeches_queued,
            "speeches_spoken": self.speeches_spoken,
            "queue_size": self.speech_queue.qsize(),
            "errors": self.errors,
            "engine_available": self.engine_available
        }
    
    def shutdown(self):
        """Gracefully shutdown TTS manager."""
        logger.info("Shutting down TTSManager...")
        self.stop_flag.set()
        
        # Signal worker thread to stop
        if self.worker_thread is not None and self.worker_thread.is_alive():
            self.speech_queue.put(None)  # Shutdown signal
            self.worker_thread.join(timeout=2.0)
        
        # Stop engine
        if self.engine is not None and self.engine_available:
            try:
                self.engine.stop()
            except:
                pass
        
        logger.info("TTSManager shutdown complete")


def get_greeting(
    greeting_type: str,
    name: str = "",
    random_choice: bool = True
) -> str:
    """
    Get greeting phrase for given type and name.
    
    Args:
        greeting_type: Type of greeting ('recognized', 'unknown', 'departed', 'general')
        name: Person's name (used in template)
        random_choice: If True, randomly select phrase; if False, use first
        
    Returns:
        Formatted greeting phrase
        
    Example:
        >>> get_greeting('recognized', 'Alice')
        'Hello Alice!'
        >>> get_greeting('unknown')
        "Hi there! I don't think we've met yet."
    """
    templates = GREETINGS.get(greeting_type, GREETINGS['general'])
    
    if random_choice:
        template = random.choice(templates)
    else:
        template = templates[0]
    
    # Format with name if provided
    if name:
        return template.format(name=name)
    else:
        return template


def list_available_voices():
    """List all available TTS voices on the system."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        print(f"\n{'='*60}")
        print(f"Available TTS Voices ({len(voices)})")
        print(f"{'='*60}\n")
        
        for i, voice in enumerate(voices, 1):
            print(f"{i}. Name: {voice.name}")
            print(f"   ID: {voice.id}")
            print(f"   Languages: {voice.languages}")
            print()
        
        engine.stop()
        return voices
    except Exception as e:
        print(f"Error listing voices: {e}")
        return []


# =============================================================================
# Demo / Testing
# =============================================================================

def main():
    """Demo TTS functionality."""
    print("=" * 70)
    print("Text-to-Speech Demo")
    print("=" * 70)
    print()
    
    # List available voices
    print("Available voices on this system:")
    voices = list_available_voices()
    
    # Initialize TTS manager
    print("\nInitializing TTSManager...")
    tts = TTSManager(rate=160, volume=0.9, voice_preference="female")
    
    print(f"Engine available: {tts.engine_available}")
    print()
    
    # Test recognized person greetings
    print("=" * 70)
    print("Testing RECOGNIZED person greetings")
    print("=" * 70)
    for name in ["Alice", "Bob", "Charlie"]:
        print(f"\nGreeting {name}...")
        tts.speak_greeting(GreetingType.RECOGNIZED, name)
        time.sleep(2.5)  # Wait for speech to complete
    
    # Test unknown person greetings
    print("\n" + "=" * 70)
    print("Testing UNKNOWN person greetings")
    print("=" * 70)
    print()
    for i in range(2):
        print(f"Unknown greeting {i+1}...")
        tts.speak_greeting(GreetingType.UNKNOWN)
        time.sleep(3.0)
    
    # Test departed greetings
    print("\n" + "=" * 70)
    print("Testing DEPARTED greetings")
    print("=" * 70)
    for name in ["Alice", "Bob"]:
        print(f"\nSaying goodbye to {name}...")
        tts.speak_greeting(GreetingType.DEPARTED, name)
        time.sleep(2.0)
    
    # Test direct speech
    print("\n" + "=" * 70)
    print("Testing direct speech")
    print("=" * 70)
    print()
    tts.speak("This is a test of the text to speech system.")
    time.sleep(3.0)
    
    tts.speak("I can speak any text you give me!")
    time.sleep(2.5)
    
    # Show statistics
    print("\n" + "=" * 70)
    print("Statistics")
    print("=" * 70)
    stats = tts.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print()
    print("✅ Demo complete!")
    print()
    
    # Shutdown
    tts.shutdown()


if __name__ == "__main__":
    main()
