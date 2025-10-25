"""Voice subsystem - TTS and greeting generation."""

from .tts_module import TTSManager
from .adaptive_tts_manager import AdaptiveTTSManager
from .greeting_selector import GreetingSelector, GreetingTemplate

__all__ = [
    "TTSManager",
    "AdaptiveTTSManager",
    "GreetingSelector",
    "GreetingTemplate"
]
