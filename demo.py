"""
Reachy Recognizer - Reachy Mini Robot Integration

Runs face recognition system on Reachy Mini hardware with:
- Reachy Mini camera feed
- Robot head movements and gestures
- Speech through robot's audio system or PC speakers
- Coordinated behaviors and greetings

Usage:
    python demo.py [--duration SECONDS] [--no-display] [--robot-audio]
    
Examples:
    python demo.py --duration 300                # 5 min demo with PC audio
    python demo.py --robot-audio                 # Use robot's speakers
    python demo.py --no-display --duration 60    # Headless mode
"""

import sys
import time
import signal
import argparse
from pathlib import Path
from typing import Optional
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
# Add reachy_mini_conversation_app to path
sys.path.insert(0, str(Path(__file__).parent / "reachy_mini_conversation_app" / "src"))

from src.config import load_config
from src.logging import setup_logging
from src.vision import RecognitionPipeline
from src.events import EventManager, EventType
from src.voice import AdaptiveTTSManager, GreetingSelector
from src.coordination import GreetingCoordinator

# Reachy imports
from reachy_mini import ReachyMini
from reachy_mini_conversation_app.moves import MovementManager
from reachy_mini_conversation_app.camera_worker import CameraWorker
from reachy_mini_conversation_app.dance_emotion_moves import GotoQueueMove, EmotionQueueMove


class ReachyAudioPlayer:
    """Audio player that uses Reachy's media system."""
    
    def __init__(self, reachy: ReachyMini):
        self.reachy = reachy
        self.logger = logging.getLogger(__name__)
        self.temp_audio_dir = Path("cache/temp_audio")
        self.temp_audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def play_audio_file(self, audio_path: str):
        """Play audio file through robot's media player."""
        try:
            # Use reachy's media player to play audio
            # Note: This requires the audio file to be accessible to the robot
            self.logger.info(f"Playing audio through robot: {audio_path}")
            # TODO: Implement robot media player integration
            # self.reachy.media.play(audio_path)
            self.logger.warning("Robot audio playback not yet implemented - would play through robot speakers")
        except Exception as e:
            self.logger.error(f"Failed to play audio on robot: {e}")


class ReachyBehaviorManager:
    """Behavior manager adapted for Reachy Mini robot."""
    
    def __init__(self, reachy: ReachyMini, movement_manager: MovementManager):
        self.reachy = reachy
        self.movement_manager = movement_manager
        self.logger = logging.getLogger(__name__)
    
    def execute_behavior(self, behavior):
        """Execute a behavior - called by GreetingCoordinator."""
        # For now, just perform greeting gesture
        # The 'behavior' parameter is ignored as we use our own gestures
        self.perform_greeting_gesture()
        return True
    
    def perform_greeting_gesture(self, person_name: Optional[str] = None):
        """Perform greeting gesture using Reachy."""
        try:
            if person_name:
                # Known person - enthusiastic wave
                self.logger.info(f"Performing greeting gesture for {person_name}")
                # Queue a happy emotion
                emotion_move = EmotionQueueMove("happy", self.reachy)
                self.movement_manager.queue_move(emotion_move)
            else:
                # Unknown person - subtle nod
                self.logger.info("Performing subtle greeting for unknown person")
                # Small head nod using goto
                current_pose = self.reachy.get_current_head_pose()
                from reachy_mini.utils import create_head_pose
                nod_pose = create_head_pose(0, 0, 0, 0, 10, 0, degrees=True)  # Small nod
                
                goto_move = GotoQueueMove(
                    target_head_pose=nod_pose,
                    start_head_pose=current_pose,
                    duration=0.5
                )
                self.movement_manager.queue_move(goto_move)
        except Exception as e:
            self.logger.error(f"Greeting gesture failed: {e}")
    
    def perform_idle_behavior(self):
        """Perform idle behavior - breathing is handled by MovementManager."""
        # Movement manager already handles breathing automatically
        pass


class ReachyIdleManager:
    """Simplified idle manager - movement manager handles breathing."""
    
    def __init__(self):
        self.active = True
    
    def start(self):
        self.active = True
    
    def stop(self):
        self.active = False
    
    def update(self, faces_present: bool):
        """Update called but breathing handled by MovementManager."""
        pass


class ReachySystemDemo:
    """System demonstration running on Reachy Mini robot."""
    
    def __init__(self, display: bool = True, use_robot_audio: bool = False):
        """
        Initialize demo system.
        
        Args:
            display: Show camera feed window
            use_robot_audio: Use robot's speakers (True) or PC speakers (False)
        """
        self.display = display
        self.use_robot_audio = use_robot_audio
        self.running = False
        self.start_time = None
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'faces_recognized': 0,
            'unknown_faces': 0,
            'greetings_given': 0
        }
        
        print("\n" + "="*80)
        print("🤖 Reachy Recognizer - Running on Reachy Mini")
        print("="*80)
        
        # Setup logging
        print("\n📝 Setting up logging...")
        self.logger = setup_logging()
        
        # Load configuration
        print("📋 Loading configuration...")
        self.config = load_config()
        
        # Initialize Reachy robot
        print("\n🤖 Connecting to Reachy Mini...")
        try:
            self.reachy = ReachyMini()
            print(f"   ✓ Connected to Reachy Mini")
        except Exception as e:
            print(f"   ✗ Failed to connect: {e}")
            raise
        
        # Initialize subsystems
        print("\n🔧 Initializing subsystems...")
        self._initialize_subsystems()
        
        print("\n✅ System initialization complete!")
        print("="*80)
    
    def _print_config_summary(self):
        """Print key configuration settings."""
        print(f"\n   Key Settings:")
        print(f"   • Camera: Device {self.config.camera.device_id}, {self.config.camera.width}x{self.config.camera.height} @ {self.config.camera.fps} FPS")
        print(f"   • Recognition threshold: {self.config.face_recognition.threshold}")
        print(f"   • Event debounce: {self.config.events.debounce_seconds}s")
        print(f"   • Enhanced voice: {self.config.tts.use_enhanced_voice}")
    
    def _initialize_subsystems(self):
        """Initialize all system components."""
        
        # Movement manager for robot control
        print("   • Movement Manager...", end="")
        self.movement_manager = MovementManager(
            current_robot=self.reachy,
            camera_worker=None  # Will set up separately
        )
        self.movement_manager.start()
        print(" ✓")
        
        # Camera worker for Reachy's camera
        print("   • Camera Worker...", end="")
        self.camera_worker = CameraWorker(
            reachy_mini=self.reachy,
            head_tracker=None  # Face recognition handles tracking
        )
        self.camera_worker.start()
        print(" ✓")
        
        # Wait for camera to warm up and start producing frames
        print("   • Waiting for camera frames...", end="", flush=True)
        max_wait = 10  # seconds
        start_wait = time.time()
        test_frame = None
        
        while test_frame is None and (time.time() - start_wait) < max_wait:
            time.sleep(0.5)
            test_frame = self.camera_worker.get_latest_frame()
            print(".", end="", flush=True)
        
        print()  # New line
        
        if test_frame is not None:
            print(f"   ✓ Camera ready: Frame received ({test_frame.shape})")
        else:
            print(f"   ✗ Camera timeout: No frames after {max_wait}s")
            print(f"   ⚠️  Check if robot's camera/media system is active")
            raise RuntimeError("Camera failed to produce frames")
        
        # Behavior manager adapted for Reachy
        print("   • Behavior Manager...", end="")
        self.behavior_manager = ReachyBehaviorManager(
            self.reachy,
            self.movement_manager
        )
        print(" ✓")
        
        # Event system
        print("   • Event Manager...", end="")
        self.event_manager = EventManager(
            debounce_seconds=self.config.events.debounce_seconds,
            departed_threshold_seconds=self.config.events.departed_threshold_seconds
        )
        self.event_manager.add_callback(EventType.PERSON_RECOGNIZED, self._on_person_recognized)
        self.event_manager.add_callback(EventType.PERSON_UNKNOWN, self._on_person_unknown)
        print(" ✓")
        
        # Voice system
        if self.config.tts.use_enhanced_voice:
            print("   • Enhanced Voice System...", end="")
            self.greeting_selector = GreetingSelector(
                personality=self.config.greetings.personality,
                non_repetition_window=self.config.greetings.repetition_window
            )
            
            if self.use_robot_audio:
                # Use robot's audio system
                self.robot_audio_player = ReachyAudioPlayer(self.reachy)
                self.adaptive_tts = AdaptiveTTSManager(
                    enable_caching=self.config.tts.cache.enabled
                )
                print(" ✓")
                print("   🔊 Audio: Reachy's speakers (via media player)")
                print("   ⚠️  Robot audio integration is experimental")
            else:
                # Use PC speakers
                self.robot_audio_player = None
                self.adaptive_tts = AdaptiveTTSManager(
                    enable_caching=self.config.tts.cache.enabled
                )
                print(" ✓")
                print("   🔊 Audio: PC speakers (development mode)")
        else:
            self.greeting_selector = None
            self.adaptive_tts = None
            self.robot_audio_player = None
        
        # Greeting coordinator
        print("   • Greeting Coordinator...", end="")
        self.coordinator = GreetingCoordinator(
            event_manager=self.event_manager,
            behavior_manager=self.behavior_manager,
            gesture_speech_delay=self.config.behaviors.gesture_speech_delay,
            adaptive_tts=self.adaptive_tts,
            greeting_selector=self.greeting_selector,
            use_enhanced_voice=self.config.tts.use_enhanced_voice
        )
        print(" ✓")
        
        # Idle manager (simplified - breathing handled by MovementManager)
        print("   • Idle Manager...", end="")
        self.idle_manager = ReachyIdleManager()
        self.idle_manager.start()
        print(" ✓")
        
        # Recognition pipeline - using Reachy's camera
        print("   • Recognition Pipeline...", end="")
        
        self.pipeline = RecognitionPipeline(
            process_every_n_frames=self.config.performance.process_every_n_frames
        )
        
        # Create custom camera adapter for Reachy
        class ReachyCamera:
            """Adapter for Reachy's camera to match CameraInterface API."""
            def __init__(self, camera_worker):
                self.camera_worker = camera_worker
                self.width = 640
                self.height = 480
            
            def read_frame(self):
                frame = self.camera_worker.get_latest_frame()
                if frame is not None:
                    return True, frame
                return False, None
            
            def release(self):
                pass
        
        # Replace camera with Reachy camera
        self.pipeline.camera = ReachyCamera(self.camera_worker)
        
        # Load face database
        if Path("data/faces.json").exists():
            self.pipeline.load_database("data/faces.json")
        print(" ✓")
    
    def _on_person_recognized(self, event):
        """Track recognized person events."""
        self.stats['faces_recognized'] += 1
        self.stats['greetings_given'] += 1
        print(f"\n👤 Recognized: {event.person_name} (confidence: {event.confidence:.2f})")
        print(f"   🔊 Greeting should be playing now...")
        self.logger.info(f"Person recognized: {event.person_name}, TTS enabled: {self.config.tts.use_enhanced_voice}")
    
    def _on_person_unknown(self, event):
        """Track unknown person events."""
        self.stats['unknown_faces'] += 1
        print(f"\n❓ Unknown person detected")
    
    def run(self, duration: Optional[int] = None):
        """Run the demonstration on Reachy."""
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration if duration else None
        
        print("\n▶️  Starting demonstration on Reachy Mini...")
        if duration:
            print(f"   Running for {duration} seconds")
        else:
            print("   Running until Ctrl+C")
        
        print("\n📸 Reachy's camera active")
        print("   • Point Reachy at faces to recognize")
        print("   • Reachy will greet known and unknown people")
        print("\n   Press Ctrl+C to stop\n")
        
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        
        frame_count = 0
        last_status_time = time.time()
        
        try:
            while self.running:
                if end_time and time.time() >= end_time:
                    break
                
                # Get frame from Reachy's camera
                ret, frame = self.pipeline.camera.read_frame()
                if not ret or frame is None:
                    if frame_count % 100 == 0:  # Print every 100 failed attempts
                        print(f"⚠️  No frame from camera (attempt {frame_count})")
                    time.sleep(0.1)
                    frame_count += 1
                    continue
                
                self.stats['frames_processed'] += 1
                
                # Print status every 5 seconds
                if time.time() - last_status_time > 5.0:
                    print(f"📊 Status: {self.stats['frames_processed']} frames, "
                          f"{self.stats['faces_detected']} faces detected, "
                          f"{self.stats['faces_recognized']} recognized")
                    last_status_time = time.time()
                
                # Process frame
                results = self.pipeline.process_frame(frame)
                
                if results:
                    self.stats['faces_detected'] += len(results)
                    
                    # Process through event manager
                    self.event_manager.process_recognition_results(
                        results,
                        frame_number=self.stats['frames_processed']
                    )
                
                # Update idle manager
                faces_present = len(results) > 0 if results else False
                self.idle_manager.update(faces_present)
                
                time.sleep(0.01)
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            self.logger.error(f"Demo error: {e}", exc_info=True)
        
        finally:
            self.stop()
    
    def stop(self):
        """Stop the demonstration."""
        if not self.running:
            return
        
        print("\n\n🛑 Stopping demonstration...")
        self.running = False
        
        # Stop subsystems
        if hasattr(self, 'movement_manager'):
            self.movement_manager.stop()
        
        if hasattr(self, 'camera_worker'):
            self.camera_worker.stop()
        
        if hasattr(self, 'reachy'):
            self.reachy.client.disconnect()
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate final report."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*80)
        print("📊 DEMO SUMMARY")
        print("="*80)
        print(f"\n⏱️  Duration: {elapsed:.1f}s")
        print(f"📸 Frames: {self.stats['frames_processed']}")
        print(f"👥 Faces detected: {self.stats['faces_detected']}")
        print(f"🎯 Recognized: {self.stats['faces_recognized']}")
        print(f"❓ Unknown: {self.stats['unknown_faces']}")
        print(f"💬 Greetings: {self.stats['greetings_given']}")
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Reachy Recognizer on Reachy Mini')
    parser.add_argument('--duration', type=int, help='Demo duration in seconds')
    parser.add_argument('--no-display', action='store_true', help='Headless mode')
    parser.add_argument('--robot-audio', action='store_true', 
                        help='Use robot speakers (default: PC speakers for development)')
    
    args = parser.parse_args()
    
    try:
        demo = ReachySystemDemo(
            display=not args.no_display,
            use_robot_audio=args.robot_audio
        )
        demo.run(duration=args.duration)
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
