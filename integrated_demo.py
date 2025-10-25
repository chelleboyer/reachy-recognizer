"""
Integrated Demo with Conversation

Combines face recognition, greetings, and voice conversation.
When Reachy recognizes you, it greets you and starts a conversation.
"""

import sys
import time
import signal
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.vision.recognition_pipeline import RecognitionPipeline
from src.events.event_system import EventManager, EventType
from src.behaviors.behavior_module import BehaviorManager
from src.behaviors.idle_manager import IdleManager
from src.coordination.greeting_coordinator import GreetingCoordinator
from src.conversation.stt_module import SpeechToText, AudioRecorder
from src.conversation.conversation_manager import ConversationManager
from src.voice.adaptive_tts_manager import AdaptiveTTSManager, play_audio_data, PYGAME_AVAILABLE
from src.config.config_loader import load_config
from openai import AsyncOpenAI
import os
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedDemo:
    """Full demo with recognition, greetings, and conversation."""
    
    def __init__(self):
        """Initialize all subsystems."""
        self.config = load_config()
        self.should_stop = False
        self.in_conversation = False
        self.current_person = None
        
        # Initialize subsystems
        print("\n🔧 Initializing subsystems...")
        
        # Event system
        self.event_manager = EventManager(
            debounce_seconds=self.config.events.debounce_seconds,
            departed_threshold_seconds=self.config.events.departed_threshold_seconds
        )
        print("   ✓ Event Manager")
        
        # Behavior system
        self.behavior_manager = BehaviorManager(enable_robot=True)
        print("   ✓ Behavior Manager")
        
        # Voice system
        self.greeting_selector = None
        self.adaptive_tts = AdaptiveTTSManager(enable_caching=True)
        print("   ✓ Voice System")
        
        # Greeting coordinator
        self.coordinator = GreetingCoordinator(
            event_manager=self.event_manager,
            behavior_manager=self.behavior_manager,
            gesture_speech_delay=self.config.behaviors.gesture_speech_delay,
            adaptive_tts=self.adaptive_tts,
            greeting_selector=self.greeting_selector,
            use_enhanced_voice=True
        )
        print("   ✓ Greeting Coordinator")
        
        # Idle manager
        self.idle_manager = IdleManager(
            behavior_manager=self.behavior_manager,
            activation_threshold=5.0,
            idle_interval=3.0
        )
        self.idle_manager.start()
        print("   ✓ Idle Manager")
        
        # Recognition pipeline
        self.pipeline = RecognitionPipeline(
            camera_device=self.config.camera.device_id,
            recognition_threshold=self.config.face_recognition.threshold,
            event_manager=self.event_manager
        )
        
        # Load face database
        self.pipeline.load_database("data/faces.json")
        print("   ✓ Recognition Pipeline")
        
        # Conversation system
        self.stt = SpeechToText()
        self.conversation = ConversationManager(personality="friendly")
        self.tts_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.recorder = AudioRecorder(
            silence_threshold=50,
            silence_duration=2.0
        )
        print("   ✓ Conversation System")
        
        # Register event handlers
        self.event_manager.add_callback(
            EventType.PERSON_RECOGNIZED,
            self.on_person_recognized
        )
        
        print("\n✅ System initialized!\n")
    
    def on_person_recognized(self, event_data):
        """Handle person recognition - offer conversation."""
        if not self.in_conversation:
            name = event_data.get('name', 'Friend')
            self.current_person = name
            
            # Greeting will happen automatically via coordinator
            # After 3 seconds, offer conversation
            threading.Timer(3.0, lambda: asyncio.run(self.offer_conversation(name))).start()
    
    async def offer_conversation(self, name):
        """Offer to have a conversation."""
        if self.in_conversation:
            return
        
        offer = f"{name}, would you like to chat?"
        print(f"\n💬 Reachy: {offer}")
        
        try:
            # Speak offer
            response = await self.tts_client.audio.speech.create(
                model="tts-1",
                voice="shimmer",
                input=offer,
                response_format="mp3"
            )
            
            audio_bytes = response.content
            if PYGAME_AVAILABLE:
                play_audio_data(audio_bytes, format="mp3")
            
            # Wait for response
            print("🎤 Listening for your response...")
            result = self.stt.transcribe_from_microphone(self.recorder, cleanup=False)
            
            if result.text:
                print(f"You: {result.text}")
                
                # Check if they want to chat
                if any(word in result.text.lower() for word in ['yes', 'yeah', 'sure', 'okay', 'ok', 'chat', 'talk']):
                    await self.start_conversation(name)
        
        except Exception as e:
            logger.error(f"Offer conversation error: {e}")
    
    async def start_conversation(self, name):
        """Start voice conversation."""
        self.in_conversation = True
        
        print(f"\n{'='*70}")
        print(f"💬 Starting conversation with {name}")
        print(f"{'='*70}")
        print("Say 'goodbye' or 'bye' to end the conversation\n")
        
        try:
            while self.in_conversation and not self.should_stop:
                # Listen
                print("🎤 Listening...")
                result = self.stt.transcribe_from_microphone(self.recorder, cleanup=False)
                
                if not result.text:
                    continue
                
                print(f"\n{name}: {result.text}")
                
                # Check for exit
                if any(word in result.text.lower() for word in ['goodbye', 'bye', 'stop', 'quit', 'end']):
                    farewell = f"Goodbye {name}! It was great talking with you!"
                    print(f"Reachy: {farewell}")
                    
                    # Speak farewell
                    response = await self.tts_client.audio.speech.create(
                        model="tts-1",
                        voice="shimmer",
                        input=farewell,
                        response_format="mp3"
                    )
                    
                    if PYGAME_AVAILABLE:
                        play_audio_data(response.content, format="mp3")
                    
                    self.in_conversation = False
                    break
                
                # Get response
                response_text = await self.conversation.get_response(
                    result.text,
                    person_name=name
                )
                
                print(f"Reachy: {response_text}")
                
                # Speak response
                response = await self.tts_client.audio.speech.create(
                    model="tts-1",
                    voice="shimmer",
                    input=response_text,
                    response_format="mp3"
                )
                
                if PYGAME_AVAILABLE:
                    play_audio_data(response.content, format="mp3")
        
        except Exception as e:
            logger.error(f"Conversation error: {e}")
        finally:
            self.in_conversation = False
            print("\n💬 Conversation ended\n")
    
    def run(self):
        """Run the integrated demo."""
        print(f"\n{'='*70}")
        print("🤖 Reachy Integrated Demo - Recognition + Conversation")
        print(f"{'='*70}")
        print("\n👀 Looking for faces...")
        print("   When recognized, Reachy will greet you and offer to chat")
        print("   Press Ctrl+C to stop\n")
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            print("\n\n🛑 Stopping demo...")
            self.should_stop = True
            self.pipeline.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Run pipeline in display mode
            import threading
            import cv2
            
            # Start pipeline
            while not self.should_stop:
                results = self.pipeline.process_frame()
                
                # Get frame for display
                frame = self.pipeline.camera.read_frame()
                if frame is not None:
                    # Draw results
                    for face_box, name, confidence in results:
                        x, y, w, h = face_box
                        color = (0, 255, 0) if name != "Unknown" else (0, 165, 255)
                        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                        
                        label = f"{name}"
                        if confidence:
                            label += f" ({confidence:.0%})"
                        
                        cv2.putText(frame, label, (x, y-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    # Show frame
                    cv2.imshow('Reachy Vision', frame)
                    
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
        
        except KeyboardInterrupt:
            print("\n\n🛑 Interrupted by user")
        finally:
            # Cleanup
            self.pipeline.stop()
            self.idle_manager.stop()
            self.recorder.cleanup()
            cv2.destroyAllWindows()
            print("✅ Demo complete!")


def main():
    """Run integrated demo."""
    demo = IntegratedDemo()
    demo.run()


if __name__ == "__main__":
    import threading
    main()
