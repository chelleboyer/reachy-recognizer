"""Reachy Conversational AI Demo - Proof of Concept

Demonstrates Reachy as a desk assistant that:
1. Detects when someone approaches
2. Initiates conversation proactively
3. Listens and responds using OpenAI GPT-4
4. Responds to gestures during conversation

Requirements:
    pip install vosk pyaudio openai

Usage:
    python conversation_demo.py
    python conversation_demo.py --reachy  # On Raspberry Pi with Reachy
"""

import argparse
import asyncio
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Optional, List, Dict

import cv2
import numpy as np
import pyaudio
from vosk import Model, KaldiRecognizer

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.vision.hand_detector import HandDetector
from src.vision.gesture_recognizer import GestureType
from src.coordination.gesture_coordinator import GestureCoordinator, GestureCommand
from src.events.event_system import EventManager, EventType
from src.voice.adaptive_tts_manager import AdaptiveTTSManager
from src.voice.greeting_selector import GreetingTemplate
from src.behaviors.behavior_module import BehaviorManager, greeting_wave

# OpenAI client
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    openai_client = None
    print("⚠️  OpenAI package not installed. Install with: pip install openai")


class PersonDetector:
    """Simple person detection using MediaPipe Pose or face detection."""
    
    def __init__(self):
        """Initialize person detector."""
        # Try MediaPipe face detection (lightweight)
        try:
            import mediapipe as mp
            self.mp_face = mp.solutions.face_detection
            self.face_detector = self.mp_face.FaceDetection(
                model_selection=0,  # Short-range model
                min_detection_confidence=0.5
            )
            self.detection_method = "face"
            print("✓ Using MediaPipe face detection for presence")
        except Exception as e:
            print(f"⚠️  MediaPipe face detection failed: {e}")
            print("   Falling back to simple motion detection")
            self.detection_method = "motion"
            self.prev_frame = None
    
    def detect(self, frame: np.ndarray) -> bool:
        """
        Detect if a person is present in the frame.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            True if person detected, False otherwise
        """
        if self.detection_method == "face":
            # Convert to RGB for MediaPipe
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(frame_rgb)
            return results.detections is not None and len(results.detections) > 0
        
        else:
            # Simple motion detection fallback
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            
            if self.prev_frame is None:
                self.prev_frame = gray
                return False
            
            # Compute difference
            frame_delta = cv2.absdiff(self.prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            motion_pixels = np.sum(thresh == 255)
            
            self.prev_frame = gray
            
            # Detect significant motion (person present)
            return motion_pixels > 5000  # Threshold for person-sized motion
    
    def close(self):
        """Cleanup resources."""
        if hasattr(self, 'face_detector'):
            self.face_detector.close()


class SpeechRecognizer:
    """Real-time speech recognition using Vosk."""
    
    def __init__(self, model_path: str = "models/vosk-model-small-en-us-0.15"):
        """
        Initialize Vosk speech recognizer.
        
        Args:
            model_path: Path to Vosk model directory
        """
        self.model_path = Path(model_path)
        self.model = None
        self.recognizer = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.audio_thread = None
        
        # Audio parameters
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 4000
        
        # Check if model exists
        if not self.model_path.exists():
            print(f"⚠️  Vosk model not found at {self.model_path}")
            print("   Download from: https://alphacephei.com/vosk/models")
            print("   Recommended: vosk-model-small-en-us-0.15 (~40MB)")
            raise FileNotFoundError(f"Vosk model not found: {self.model_path}")
        
        # Load model
        print(f"Loading Vosk model from {self.model_path}...")
        self.model = Model(str(self.model_path))
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(True)
        print("✓ Vosk model loaded")
    
    def start_listening(self):
        """Start listening for speech in background thread."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.audio_thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.audio_thread.start()
        print("🎤 Speech recognition active")
    
    def stop_listening(self):
        """Stop listening for speech."""
        self.is_listening = False
        if self.audio_thread:
            self.audio_thread.join(timeout=1.0)
        print("🎤 Speech recognition paused")
    
    def _audio_loop(self):
        """Background thread for capturing audio."""
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            while self.is_listening:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_queue.put(data)
                except Exception as e:
                    print(f"⚠️  Audio capture error: {e}")
                    break
        
        finally:
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
            p.terminate()
    
    def get_speech(self) -> Optional[str]:
        """
        Get recognized speech text (non-blocking).
        
        Returns:
            Recognized text or None if no speech detected
        """
        if not self.is_listening:
            return None
        
        # Process available audio chunks
        while not self.audio_queue.empty():
            try:
                data = self.audio_queue.get_nowait()
                
                if self.recognizer.AcceptWaveform(data):
                    # Full phrase recognized
                    result = json.loads(self.recognizer.Result())
                    text = result.get('text', '').strip()
                    if text:
                        return text
            except queue.Empty:
                break
            except Exception as e:
                print(f"⚠️  Speech recognition error: {e}")
        
        return None


class ConversationManager:
    """Manages conversation state and GPT-4 interaction."""
    
    def __init__(self, tts_manager: AdaptiveTTSManager):
        """
        Initialize conversation manager.
        
        Args:
            tts_manager: TTS manager for speaking responses
        """
        self.tts = tts_manager
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # System prompt for Reachy's personality
        self.system_prompt = """You are Reachy, a friendly desk assistant robot. You are:
- Warm and approachable, but professional
- Concise (responses under 30 words usually)
- Helpful and curious about visitors
- Aware you're a physical robot with a camera and can see gestures
- Quick to engage but respectful of people's time

Keep responses conversational and natural. Don't be overly formal."""
    
    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []
        print("🔄 Conversation history reset")
    
    def generate_greeting(self) -> str:
        """Generate contextual greeting based on time of day."""
        hour = time.localtime().tm_hour
        
        if 5 <= hour < 12:
            greetings = [
                "Good morning! I'm Reachy. What brings you by?",
                "Morning! How can I help you today?",
                "Hey there! Early start today?"
            ]
        elif 12 <= hour < 17:
            greetings = [
                "Hi there! I'm Reachy. What can I do for you?",
                "Hey! Good to see you. What's up?",
                "Hello! How's your day going?"
            ]
        else:
            greetings = [
                "Evening! I'm Reachy. What brings you by?",
                "Hey there! Working late?",
                "Hi! How can I help you?"
            ]
        
        import random
        return random.choice(greetings)
    
    async def get_response(self, user_input: str) -> str:
        """
        Get GPT-4 response to user input.
        
        Args:
            user_input: User's speech text
            
        Returns:
            Reachy's response text
        """
        if not openai_client:
            return "Sorry, I'm having trouble connecting to my language center."
        
        # Add user input to history
        self.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Trim history if too long
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
        
        try:
            # Build messages for GPT-4
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history
            
            # Call GPT-4
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Faster and cheaper for desk assistant
                messages=messages,
                max_tokens=100,
                temperature=0.8
            )
            
            assistant_reply = response.choices[0].message.content.strip()
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_reply
            })
            
            return assistant_reply
        
        except Exception as e:
            print(f"⚠️  GPT-4 error: {e}")
            return "Sorry, I got a bit distracted. Could you repeat that?"
    
    async def speak(self, text: str, emotion: str = "neutral", energy: int = 3):
        """
        Speak text using TTS.
        
        Args:
            text: Text to speak
            emotion: Emotion for delivery
            energy: Energy level (1-5)
        """
        if not self.tts:
            print(f"[Reachy would say: {text}]")
            return
        
        template = GreetingTemplate(
            text=text,
            emotion=emotion,
            energy_level=energy
        )
        
        try:
            await self.tts.speak_greeting(template)
        except Exception as e:
            print(f"⚠️  TTS error: {e}")


def main():
    """Main demo loop."""
    parser = argparse.ArgumentParser(description="Reachy Conversational AI Demo")
    parser.add_argument('--reachy', action='store_true', help='Use Reachy camera and robot')
    parser.add_argument('--webcam', action='store_true', help='Force webcam')
    parser.add_argument('--camera-index', type=int, default=0, help='Webcam index')
    parser.add_argument('--vosk-model', type=str, 
                       default='models/vosk-model-small-en-us-0.15',
                       help='Path to Vosk model')
    parser.add_argument('--headless', action='store_true', help='No display window')
    args = parser.parse_args()
    
    print("=" * 70)
    print("🤖 Reachy Conversational AI Demo (POC)")
    print("=" * 70)
    
    # Setup camera
    camera = None
    reachy = None
    behavior_manager = None
    
    if args.reachy:
        print("🔍 Reachy mode (not implemented in POC)")
        print("   Using webcam for now...")
    
    print(f"📷 Opening webcam (index {args.camera_index})...")
    if sys.platform.startswith("win"):
        camera = cv2.VideoCapture(args.camera_index, cv2.CAP_DSHOW)
    else:
        camera = cv2.VideoCapture(args.camera_index)
    
    if not camera.isOpened():
        print("✗ Failed to open camera")
        return 1
    print("✓ Camera opened")
    
    # Initialize components
    print("\n🔧 Initializing components...")
    
    # Person detector
    try:
        person_detector = PersonDetector()
        print("✓ Person detector ready")
    except Exception as e:
        print(f"✗ Person detector failed: {e}")
        return 1
    
    # Speech recognizer
    try:
        speech_recognizer = SpeechRecognizer(args.vosk_model)
        print("✓ Speech recognizer ready")
    except Exception as e:
        print(f"✗ Speech recognizer failed: {e}")
        print("\n📥 To use speech recognition, download a Vosk model:")
        print("   1. Visit: https://alphacephei.com/vosk/models")
        print("   2. Download: vosk-model-small-en-us-0.15 (~40MB)")
        print("   3. Extract to: models/vosk-model-small-en-us-0.15/")
        return 1
    
    # TTS
    try:
        tts = AdaptiveTTSManager(enable_caching=True)
        print("✓ TTS ready")
    except Exception as e:
        print(f"⚠️  TTS failed: {e}, continuing without voice")
        tts = None
    
    # Conversation manager
    conversation_manager = ConversationManager(tts)
    print("✓ Conversation manager ready")
    
    # Gesture system (optional)
    event_manager = EventManager(debounce_seconds=1.0)
    gesture_coordinator = None
    try:
        detector = HandDetector("src/config/hand_detection.yaml")
        from src.vision.gesture_recognizer import GestureRecognizer
        recognizer = GestureRecognizer("src/config/gesture_recognition.yaml")
        gesture_coordinator = GestureCoordinator(detector, recognizer, event_manager)
        print("✓ Gesture system ready")
    except Exception as e:
        print(f"⚠️  Gesture system disabled: {e}")
    
    print("\n" + "=" * 70)
    print("🎬 Starting desk assistant mode...")
    print("=" * 70)
    print("State: IDLE - Waiting for someone to approach...")
    print()
    
    # State machine
    state = "IDLE"  # IDLE, GREETING, CONVERSING
    person_detected_time = None
    person_present_threshold = 2.0  # seconds
    no_person_timeout = 5.0  # seconds
    last_person_time = time.time()
    last_speech_time = None
    conversation_timeout = 30.0  # seconds
    
    # Display window
    if not args.headless:
        cv2.namedWindow("Reachy Desk Assistant", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Reachy Desk Assistant", 640, 480)
    
    try:
        while True:
            # Get frame
            ret, frame = camera.read()
            if not ret:
                print("Failed to read frame")
                break
            
            # Detect person
            person_present = person_detector.detect(frame)
            current_time = time.time()
            
            # Process gestures if available
            if gesture_coordinator:
                gesture_coordinator.process_frame(frame)
            
            # State machine logic
            if state == "IDLE":
                if person_present:
                    if person_detected_time is None:
                        person_detected_time = current_time
                        print("👀 Person detected...")
                    
                    elif current_time - person_detected_time >= person_present_threshold:
                        # Person has been present long enough - greet them!
                        print("\n✨ Initiating conversation...")
                        state = "GREETING"
                        person_detected_time = None
                        
                        # Generate and speak greeting
                        greeting = conversation_manager.generate_greeting()
                        print(f"🤖 Reachy: {greeting}")
                        
                        def speak_greeting():
                            asyncio.run(conversation_manager.speak(
                                greeting, 
                                emotion="friendly",
                                energy=4
                            ))
                        
                        threading.Thread(target=speak_greeting, daemon=True).start()
                        
                        # Start listening for response
                        speech_recognizer.start_listening()
                        last_speech_time = current_time
                        state = "CONVERSING"
                        print("State: CONVERSING - Listening...")
                
                else:
                    person_detected_time = None
            
            elif state == "CONVERSING":
                if person_present:
                    last_person_time = current_time
                    
                    # Check for speech
                    speech_text = speech_recognizer.get_speech()
                    if speech_text:
                        last_speech_time = current_time
                        print(f"👤 User: {speech_text}")
                        
                        # Get GPT-4 response
                        def handle_response():
                            response = asyncio.run(conversation_manager.get_response(speech_text))
                            print(f"🤖 Reachy: {response}")
                            asyncio.run(conversation_manager.speak(response))
                        
                        threading.Thread(target=handle_response, daemon=True).start()
                    
                    # Check for timeout
                    if last_speech_time and current_time - last_speech_time > conversation_timeout:
                        print("\n⏱️  Conversation timeout - saying goodbye...")
                        
                        def say_goodbye():
                            asyncio.run(conversation_manager.speak(
                                "Nice chatting with you! Let me know if you need anything.",
                                emotion="friendly",
                                energy=3
                            ))
                        
                        threading.Thread(target=say_goodbye, daemon=True).start()
                        
                        speech_recognizer.stop_listening()
                        conversation_manager.reset_conversation()
                        state = "IDLE"
                        print("State: IDLE - Waiting for next person...")
                
                else:
                    # Person left
                    if current_time - last_person_time > no_person_timeout:
                        print("\n👋 Person left - ending conversation...")
                        speech_recognizer.stop_listening()
                        conversation_manager.reset_conversation()
                        state = "IDLE"
                        print("State: IDLE - Waiting for next person...")
            
            # Display
            if not args.headless:
                # Draw status
                status_color = (0, 255, 0) if person_present else (100, 100, 100)
                cv2.putText(frame, f"State: {state}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f"Person: {'YES' if person_present else 'NO'}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                
                if state == "CONVERSING":
                    cv2.putText(frame, "🎤 LISTENING", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                cv2.imshow("Reachy Desk Assistant", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\nQuitting...")
                    break
                elif key == ord('r'):
                    print("\n🔄 Manual reset...")
                    speech_recognizer.stop_listening()
                    conversation_manager.reset_conversation()
                    state = "IDLE"
                    print("State: IDLE")
            else:
                time.sleep(0.01)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    
    finally:
        print("\nCleaning up...")
        speech_recognizer.stop_listening()
        person_detector.close()
        camera.release()
        if not args.headless:
            cv2.destroyAllWindows()
        print("✓ Done")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
