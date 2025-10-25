"""
Voice Conversation Demo

Full voice-based conversation with Reachy using:
- Speech-to-Text (Whisper)
- LLM Conversation (GPT-4o-mini)
- Text-to-Speech (OpenAI TTS with Shimmer voice)
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.conversation.stt_module import SpeechToText, AudioRecorder
from src.conversation.conversation_manager import ConversationManager
from src.voice.adaptive_tts_manager import play_audio_data, PYGAME_AVAILABLE
from src.voice.greeting_selector import GreetingTemplate
from src.behaviors.behavior_module import BehaviorManager, curious_tilt, unknown_curious
from src.behaviors.idle_manager import IdleManager
from openai import AsyncOpenAI
import os
import logging
import random

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VoiceConversation:
    """Full voice conversation system."""
    
    def __init__(self, person_name: str = "Friend", enable_robot: bool = True):
        """Initialize voice conversation system."""
        self.person_name = person_name
        self.stt = SpeechToText()
        self.conversation = ConversationManager(personality="friendly")
        self.tts_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.recorder = AudioRecorder(
            silence_threshold=50,  # Much lower for quiet microphones
            silence_duration=1.0   # Reduced from 2.0s - faster detection of end of speech
        )
        
        # Initialize behavior manager for robot movements
        self.behavior_manager = BehaviorManager(enable_robot=enable_robot)
        self.enable_movements = enable_robot
        
        # Initialize idle manager for continuous antenna movements
        # Use very short intervals for active, engaging movements
        if enable_robot:
            self.idle_manager = IdleManager(
                behavior_manager=self.behavior_manager,
                activation_threshold=0.1,  # Almost instant activation
                idle_interval=0.8  # Move every 0.8 seconds - VERY active!
            )
            self.idle_manager.start()
            logger.info("✓ Idle manager started for CONTINUOUS antenna movement")
        else:
            self.idle_manager = None
        
        logger.info(f"VoiceConversation initialized for {person_name}")
        logger.info(f"Robot movements: {'enabled' if enable_robot else 'disabled'}")
    
    async def speak(self, text: str):
        """Convert text to speech and play it."""
        try:
            # ALWAYS add an expressive gesture while speaking
            if self.enable_movements:
                gesture = random.choice([curious_tilt, unknown_curious])
                self.behavior_manager.execute_behavior(gesture)
            
            # Generate speech with OpenAI TTS - use faster tts-1-hd model
            response = await self.tts_client.audio.speech.create(
                model="tts-1",  # Already using fastest model
                voice="shimmer",
                input=text,
                response_format="mp3",
                speed=1.15  # Speak 15% faster for punchier responses
            )
            
            audio_bytes = response.content
            
            # Play audio
            if PYGAME_AVAILABLE:
                play_audio_data(audio_bytes, format="mp3")
            else:
                logger.warning("Audio playback not available")
        
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    async def listen(self) -> str:
        """Listen for user speech and transcribe."""
        try:
            # Pause idle movements during listening to avoid audio conflicts
            if self.idle_manager:
                self.idle_manager.stop()
            
            # ALWAYS add a "listening" curious tilt gesture
            if self.enable_movements:
                self.behavior_manager.execute_behavior(curious_tilt)
            
            result = self.stt.transcribe_from_microphone(self.recorder, cleanup=False)
            
            # Resume idle movements after listening
            if self.idle_manager:
                self.idle_manager.start()
            
            return result.text
        except Exception as e:
            logger.error(f"STT error: {e}")
            # Make sure to restart idle manager even on error
            if self.idle_manager:
                self.idle_manager.start()
            return ""
    
    async def conversation_loop(self):
        """Run continuous conversation loop."""
        print("\n" + "=" * 70)
        print("🎤 Voice Conversation with Reachy")
        print("=" * 70)
        print()
        print(f"Speaking with: {self.person_name}")
        print("Say something to start the conversation")
        print("Press Ctrl+C to exit")
        print()
        
        # Initial greeting
        greeting = f"Hello {self.person_name}! I'm ready to chat with you."
        print(f"Reachy: {greeting}")
        await self.speak(greeting)
        
        try:
            while True:
                # Listen for user input
                print("\n🎤 Listening...")
                user_text = await self.listen()
                
                if not user_text:
                    print("⚠️ Didn't catch that. Could you repeat?")
                    continue
                
                print(f"\n{self.person_name}: {user_text}")
                
                # Check for exit commands
                if any(word in user_text.lower() for word in ['goodbye', 'bye', 'exit', 'quit', 'stop']):
                    farewell = f"Goodbye {self.person_name}! It was nice talking with you."
                    print(f"Reachy: {farewell}")
                    await self.speak(farewell)
                    break
                
                # Get conversational response
                response = await self.conversation.get_response(
                    user_text,
                    person_name=self.person_name
                )
                
                print(f"Reachy: {response}")
                
                # Speak response
                await self.speak(response)
        
        except KeyboardInterrupt:
            print("\n\n⏹️ Conversation ended")
        finally:
            self.recorder.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        if self.idle_manager:
            self.idle_manager.stop()
        self.recorder.cleanup()


async def main():
    """Run voice conversation demo."""
    import sys
    
    # Get person's name
    if len(sys.argv) > 1:
        person_name = sys.argv[1]
    else:
        person_name = input("What's your name? ")
    
    # Create conversation system
    vc = VoiceConversation(person_name=person_name)
    
    try:
        await vc.conversation_loop()
    finally:
        vc.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
