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
from src.behaviors.behavior_module import BehaviorManager, greeting_wave, look_at_person, idle_breath, thinking_look

# LLM clients
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    openai_client = None
    print("⚠️  OpenAI package not installed. Install with: pip install openai")

# Ollama client (local LLM)
try:
    import requests
    ollama_available = True
except ImportError:
    ollama_available = False
    print("⚠️  requests package not installed for Ollama support")


# Shared event loop for async operations
_event_loop = None
_loop_thread = None

def get_shared_loop():
    """Get or create shared event loop running in background thread."""
    global _event_loop, _loop_thread
    
    if _event_loop is None:
        def run_loop():
            global _event_loop
            _event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_event_loop)
            _event_loop.run_forever()
        
        _loop_thread = threading.Thread(target=run_loop, daemon=True)
        _loop_thread.start()
        
        # Wait for loop to be ready
        while _event_loop is None:
            time.sleep(0.01)
    
    return _event_loop


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
                
                if self.recognizer.AcceptWaveform(data):  # type: ignore
                    # Full phrase recognized
                    result = json.loads(self.recognizer.Result())  # type: ignore
                    text = result.get('text', '').strip()
                    if text:
                        return text
            except queue.Empty:
                break
            except Exception as e:
                print(f"⚠️  Speech recognition error: {e}")
        
        return None


class ConversationManager:
    """Manages conversation state and LLM interaction."""
    
    def __init__(self, tts_manager: Optional[AdaptiveTTSManager], backend: str = "openai", ollama_model: str = "phi3:mini"):
        """
        Initialize conversation manager.
        
        Args:
            tts_manager: TTS manager for speaking responses (can be None)
            backend: LLM backend - "openai", "ollama", or "auto" (try ollama first)
            ollama_model: Ollama model to use if backend is ollama
        """
        self.tts = tts_manager
        self.backend = backend
        self.ollama_model = ollama_model
        self.ollama_url = "http://localhost:11434/api/chat"
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 10  # Keep last 10 exchanges
        
        # Test backends
        self._test_backends()
        
        # System prompt for Reachy's personality
        self.system_prompt = """You are Reachy, a friendly desk assistant robot. You are:
- Warm and approachable, but professional
- Concise (responses under 30 words usually)
- Helpful and curious about visitors
- Aware you're a physical robot with a camera and can see gestures
- Quick to engage but respectful of people's time

Keep responses conversational and natural. Don't be overly formal."""
    
    def _test_backends(self):
        """Test which backends are available and configure accordingly."""
        self.ollama_works = False
        self.openai_works = openai_client is not None
        
        # Test Ollama if needed
        if self.backend in ["ollama", "auto"] and ollama_available:
            try:
                print("   Testing Ollama connection...")
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_names = [m['name'] for m in models]
                    print(f"   Ollama models available: {model_names}")
                    
                    if self.ollama_model not in model_names and model_names:
                        print(f"⚠️  Model {self.ollama_model} not found. Available: {model_names}")
                        if model_names:
                            self.ollama_model = model_names[0]
                            print(f"   Using {self.ollama_model} instead")
                    
                    # Do a quick test generation (also pre-loads model)
                    print(f"   Testing {self.ollama_model} generation (pre-loading model)...")
                    test_payload = {
                        "model": self.ollama_model,
                        "messages": [{"role": "user", "content": "Hi"}],
                        "stream": False,
                        "options": {
                            "temperature": 0.8,
                            "num_predict": 50  # Generate more to fully load model
                        }
                    }
                    import time
                    test_start = time.time()
                    test_response = requests.post(self.ollama_url, json=test_payload, timeout=60)
                    test_time = time.time() - test_start
                    
                    if test_response.status_code == 200:
                        self.ollama_works = True
                        print(f"   ✓ Ollama test successful! ({test_time:.1f}s)")
                        if test_time > 10:
                            print(f"   ⚠️  Model loaded slowly ({test_time:.1f}s). Next responses will be faster (~1-2s)")
                        else:
                            print(f"   ✓ Model already loaded, responses will be fast!")
                    else:
                        print(f"   ✗ Ollama test failed: HTTP {test_response.status_code}")
                else:
                    print(f"   ✗ Ollama not responding (HTTP {response.status_code})")
            except requests.exceptions.ConnectionError:
                print("   ✗ Ollama not running. Start with: ollama serve")
            except requests.exceptions.Timeout:
                print("   ✗ Ollama timeout - model may be loading (try again)")
            except Exception as e:
                print(f"   ✗ Ollama test failed: {e}")
        
        # Determine active backend
        if self.backend == "auto":
            if self.ollama_works:
                self.active_backend = "ollama"
                print(f"✓ Using Ollama ({self.ollama_model}) - LOCAL & FAST")
            elif self.openai_works:
                self.active_backend = "openai"
                print("✓ Using OpenAI GPT-4 - CLOUD (slower)")
            else:
                self.active_backend = None
                print("⚠️  No LLM backends available!")
        elif self.backend == "ollama":
            self.active_backend = "ollama" if self.ollama_works else None
            if self.ollama_works:
                print(f"✓ Using Ollama ({self.ollama_model}) - LOCAL & FAST")
            else:
                print("⚠️  Ollama not available. Start with: ollama serve")
        else:  # openai
            self.active_backend = "openai" if self.openai_works else None
            if self.openai_works:
                print("✓ Using OpenAI GPT-4 - CLOUD")
            else:
                print("⚠️  OpenAI not configured")
    
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
        Get LLM response to user input.
        
        Args:
            user_input: User's speech text
            
        Returns:
            Reachy's response text
        """
        if not self.active_backend:
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
            if self.active_backend == "ollama":
                assistant_reply = await self._get_ollama_response()
            else:  # openai
                assistant_reply = await self._get_openai_response()
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_reply
            })
            
            return assistant_reply
        
        except Exception as e:
            print(f"⚠️  LLM error ({self.active_backend}): {e}")
            import traceback
            traceback.print_exc()
            
            # Try fallback if auto mode
            if self.backend == "auto" and self.active_backend == "ollama" and self.openai_works:
                print("   Falling back to OpenAI...")
                try:
                    self.active_backend = "openai"
                    assistant_reply = await self._get_openai_response()
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_reply
                    })
                    return assistant_reply
                except Exception as fallback_error:
                    print(f"   Fallback also failed: {fallback_error}")
                    traceback.print_exc()
            return "Sorry, I got a bit distracted. Could you repeat that?"
    
    async def _get_openai_response(self) -> str:
        """Get response from OpenAI API."""
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        response = openai_client.chat.completions.create(  # type: ignore
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=100,
            temperature=0.8
        )
        
        return response.choices[0].message.content.strip()
    
    async def _get_ollama_response(self) -> str:
        """Get response from Ollama local LLM."""
        import asyncio
        import time
        from concurrent.futures import ThreadPoolExecutor
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history
        
        payload = {
            "model": self.ollama_model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",  # Keep model loaded for 10 minutes
            "options": {
                "temperature": 0.8,
                "num_predict": 100
            }
        }
        
        print(f"   [DEBUG] Calling Ollama with {len(messages)} messages...")
        print(f"   [DEBUG] Model: {self.ollama_model}, URL: {self.ollama_url}")
        
        # Note: Model should already be loaded from pre-load test
        if len(self.conversation_history) <= 1:
            print(f"   [INFO] First conversation request (model pre-loaded)...")
        
        # Run blocking request in thread pool to avoid blocking async loop
        loop = asyncio.get_event_loop()
        start_time = time.time()
        
        try:
            with ThreadPoolExecutor() as executor:
                response = await asyncio.wait_for(
                    loop.run_in_executor(
                        executor,
                        lambda: requests.post(self.ollama_url, json=payload, timeout=90)
                    ),
                    timeout=90  # Overall timeout
                )
            
            elapsed = time.time() - start_time
            print(f"   [DEBUG] Ollama responded in {elapsed:.1f}s, HTTP status: {response.status_code}")
        except asyncio.TimeoutError:
            print(f"   [ERROR] Ollama timeout after {time.time() - start_time:.1f}s")
            raise Exception("Ollama timeout - model may be stuck loading")
        
        if response.status_code != 200:
            print(f"   [ERROR] Ollama returned status {response.status_code}")
            print(f"   [ERROR] Response: {response.text}")
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        
        if 'message' not in result or 'content' not in result['message']:
            print(f"   [ERROR] Unexpected Ollama response format: {result}")
            raise Exception(f"Invalid Ollama response: {result}")
        
        content = result['message']['content'].strip()
        print(f"   [DEBUG] Ollama response: '{content[:50]}...' ({len(content)} chars)")
        
        return content
    
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
    parser.add_argument('--llm', type=str, default='auto',
                       choices=['auto', 'ollama', 'openai'],
                       help='LLM backend: auto (try local first), ollama (local), or openai (cloud)')
    parser.add_argument('--ollama-model', type=str, default='phi3:mini',
                       help='Ollama model to use (default: phi3:mini)')
    parser.add_argument('--no-cloud', action='store_true',
                       help='Disable all cloud services (OpenAI API) - 100%% local only')
    parser.add_argument('--headless', action='store_true', help='No display window')
    args = parser.parse_args()
    
    # Configure Qt platform based on headless flag
    import os
    import sys
    if args.headless and sys.platform.startswith("linux"):
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    
    # Disable OpenAI if --no-cloud flag set
    if args.no_cloud:
        global openai_client
        openai_client = None
        # Clear API key from environment
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        print("🔒 Cloud services disabled - running 100%% LOCAL ONLY")
    
    print("=" * 70)
    print("🤖 Reachy Conversational AI Demo (POC)")
    if args.no_cloud:
        print("🔒 MODE: 100%% LOCAL (No cloud services)")
    print("=" * 70)
    
    # Setup camera and Reachy
    camera = None
    reachy = None
    behavior_manager = None
    use_reachy_camera = False
    
    if args.reachy:
        print("🔍 Connecting to Reachy...")
        try:
            from reachy_mini import ReachyMini
            reachy = ReachyMini()
            print("✓ Reachy connected")
            
            # Initialize behavior manager immediately for responsive movements
            try:
                behavior_manager = BehaviorManager(reachy=reachy, enable_robot=True)
                print("✓ Behavior manager ready")
            except Exception as e:
                print(f"⚠️  Behavior manager failed: {e}")
                import traceback
                traceback.print_exc()
            
            # Test camera
            frame_data = reachy.media.get_frame()
            if frame_data is not None:
                frame = np.asarray(frame_data)
                if frame.size > 0:
                    use_reachy_camera = True
                    print("✓ Reachy camera ready")
                else:
                    print("⚠️  Reachy camera returned empty frame, using webcam fallback")
            else:
                print("⚠️  Reachy camera returned None, using webcam fallback")
        except Exception as e:
            print(f"⚠️  Failed to connect to Reachy: {e}")
            print("   Using webcam fallback...")
    
    if not use_reachy_camera:
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
    conversation_manager = ConversationManager(tts, backend=args.llm, ollama_model=args.ollama_model)
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
    person_present_threshold = 1.0  # seconds (reduced for faster response)
    no_person_timeout = 5.0  # seconds
    last_person_time = time.time()
    last_speech_time = None
    conversation_timeout = 30.0  # seconds
    last_idle_behavior = time.time()
    idle_behavior_interval = 8.0  # seconds between idle movements
    
    # Display window
    if not args.headless:
        cv2.namedWindow("Reachy Desk Assistant", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Reachy Desk Assistant", 640, 480)
    
    try:
        while True:
            # Get frame
            if use_reachy_camera and reachy:
                frame_data = reachy.media.get_frame()
                if frame_data is None:
                    print("Failed to read frame from Reachy")
                    break
                frame = np.asarray(frame_data)
            elif camera is not None:
                ret, frame = camera.read()
                if not ret:
                    print("Failed to read frame from webcam")
                    break
            else:
                print("No camera available")
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
                        
                        # IMMEDIATE RESPONSE: Quick head nod acknowledgment
                        if behavior_manager and behavior_manager.reachy:
                            print("   🤖 Quick acknowledgment nod")
                            def quick_acknowledge():
                                try:
                                    result = behavior_manager.execute_behavior(look_at_person)
                                    if not result:
                                        print("   ⚠️  Acknowledgment behavior blocked")
                                except Exception as e:
                                    print(f"   ⚠️  Acknowledgment failed: {e}")
                            threading.Thread(target=quick_acknowledge, daemon=True).start()
                        else:
                            print(f"   ⚠️  Behavior manager not ready (mgr={behavior_manager is not None}, reachy={behavior_manager.reachy if behavior_manager else None})")
                    
                    elif current_time - person_detected_time >= person_present_threshold:
                        # Person has been present long enough - greet them!
                        print("\n✨ Initiating conversation...")
                        state = "GREETING"
                        person_detected_time = None
                        
                        # Wave gesture IMMEDIATELY (before speech)
                        if behavior_manager and behavior_manager.reachy:
                            print("   👋 Greeting wave")
                            def wave_now():
                                try:
                                    behavior_manager.execute_behavior(greeting_wave)
                                except Exception as e:
                                    print(f"   ⚠️  Wave failed: {e}")
                            threading.Thread(target=wave_now, daemon=True).start()
                        
                        # Generate and speak greeting
                        greeting = conversation_manager.generate_greeting()
                        print(f"🤖 Reachy: {greeting}")
                        
                        def speak_greeting():
                            loop = get_shared_loop()
                            future = asyncio.run_coroutine_threadsafe(
                                conversation_manager.speak(
                                    greeting, 
                                    emotion="friendly",
                                    energy=4
                                ),
                                loop
                            )
                            future.result()  # Wait for completion
                        
                        threading.Thread(target=speak_greeting, daemon=True).start()
                        
                        # Start listening for response
                        speech_recognizer.start_listening()
                        last_speech_time = current_time
                        state = "CONVERSING"
                        print("State: CONVERSING - Listening...")
                
                else:
                    person_detected_time = None
                    
                    # Idle breathing behavior when no one is around
                    if behavior_manager and behavior_manager.reachy:
                        if current_time - last_idle_behavior >= idle_behavior_interval:
                            def idle_movement():
                                try:
                                    behavior_manager.execute_behavior(idle_breath)
                                except:
                                    pass
                            threading.Thread(target=idle_movement, daemon=True).start()
                            last_idle_behavior = current_time
            
            elif state == "CONVERSING":
                if person_present:
                    last_person_time = current_time
                    
                    # Check for speech
                    speech_text = speech_recognizer.get_speech()
                    if speech_text:
                        last_speech_time = current_time
                        print(f"👤 User: {speech_text}")
                        
                        # IMMEDIATE RESPONSE: Head tilt/nod to show listening
                        if behavior_manager and behavior_manager.reachy:
                            print("   🤔 Thinking look")
                            def show_listening():
                                try:
                                    behavior_manager.execute_behavior(thinking_look)
                                except Exception as e:
                                    print(f"   ⚠️  Thinking look failed: {e}")
                            threading.Thread(target=show_listening, daemon=True).start()
                        
                        # Get LLM response with thinking animation
                        def handle_response():
                            try:
                                # Type check: speech_text is str here (checked by if statement)
                                user_text: str = speech_text  # type: ignore
                                loop = get_shared_loop()
                                
                                # Get response
                                future = asyncio.run_coroutine_threadsafe(
                                    conversation_manager.get_response(user_text),
                                    loop
                                )
                                response = future.result()  # Wait for completion
                                print(f"🤖 Reachy: {response}")
                                
                                # Speak response
                                future = asyncio.run_coroutine_threadsafe(
                                    conversation_manager.speak(response),
                                    loop
                                )
                                future.result()  # Wait for completion
                            except RuntimeError as e:
                                if "cannot schedule new futures after shutdown" in str(e):
                                    print("   (Response arrived after shutdown - ignoring)")
                                else:
                                    raise
                        
                        threading.Thread(target=handle_response, daemon=True).start()
                    
                    # Check for timeout
                    if last_speech_time and current_time - last_speech_time > conversation_timeout:
                        print("\n⏱️  Conversation timeout - saying goodbye...")
                        
                        def say_goodbye():
                            loop = get_shared_loop()
                            future = asyncio.run_coroutine_threadsafe(
                                conversation_manager.speak(
                                    "Nice chatting with you! Let me know if you need anything.",
                                    emotion="friendly",
                                    energy=3
                                ),
                                loop
                            )
                            future.result()  # Wait for completion
                        
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
        if camera is not None:
            camera.release()
        if not args.headless:
            cv2.destroyAllWindows()
        print("✓ Done")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
