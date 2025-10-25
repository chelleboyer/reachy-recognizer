"""
Quick test to verify OpenAI TTS voice is working correctly.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from src.voice.adaptive_tts_manager import OpenAITTSBackend, AudioData
from src.voice.greeting_selector import GreetingTemplate

async def test_shimmer():
    """Test Shimmer voice directly."""
    print("Testing Shimmer voice...")
    print("=" * 60)
    
    backend = OpenAITTSBackend()
    
    # Create a simple greeting
    template = GreetingTemplate(
        text="Hi Michelle! I'm using the Shimmer voice. Can you hear the difference?",
        emotion="excited"
    )
    
    print(f"Text: {template.text}")
    print(f"Emotion: {template.emotion}")
    print(f"Default voice: {backend.default_voice}")
    print(f"Voice mapping: excited -> {backend._select_voice(template)}")
    print()
    
    print("Generating speech...")
    audio = await backend.synthesize(template)
    
    print(f"✓ Generated {len(audio.data)} bytes in {audio.latency:.2f}s")
    print(f"  Backend: {audio.backend}")
    print(f"  Format: {audio.format}")
    print()
    
    # Play it
    print("Playing audio...")
    from src.voice.adaptive_tts_manager import play_audio_data
    play_audio_data(audio.data, audio.format)
    print("✓ Done!")

if __name__ == "__main__":
    asyncio.run(test_shimmer())
