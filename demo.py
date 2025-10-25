"""
Reachy Recognizer - Comprehensive System Demonstration

End-to-end demo showcasing all system capabilities:
- Face recognition with live camera feed
- Event system with debouncing
- Behavior coordination (greetings, idle)
- Text-to-speech with adaptive voice
- Performance logging and metrics
- Configuration system

Usage:
    python demo.py [--duration SECONDS] [--no-display] [--benchmark]
    
Examples:
    python demo.py --duration 300            # 5 minute demo
    python demo.py --benchmark               # Run performance benchmarks
    python demo.py --no-display --duration 60  # Headless mode
"""

import sys
import time
import signal
import argparse
import cv2
from pathlib import Path
from typing import Optional
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.logging import setup_logging
from src.vision import RecognitionPipeline
from src.events import EventManager, EventType
from src.behaviors import BehaviorManager, IdleManager
from src.voice import AdaptiveTTSManager, GreetingSelector
from src.coordination import GreetingCoordinator


class SystemDemo:
    """Comprehensive system demonstration."""
    
    def __init__(self, display: bool = True, benchmark: bool = False):
        """
        Initialize demo system.
        
        Args:
            display: Show camera feed window
            benchmark: Enable detailed performance tracking
        """
        self.display = display
        self.benchmark = benchmark
        self.running = False
        self.start_time = None
        
        # Statistics
        self.stats = {
            'frames_processed': 0,
            'faces_detected': 0,
            'faces_recognized': 0,
            'unknown_faces': 0,
            'greetings_given': 0,
            'idle_behaviors': 0
        }
        
        print("\n" + "="*80)
        print("🤖 Reachy Recognizer - System Demonstration")
        print("="*80)
        
        # Setup logging
        print("\n📝 Setting up logging...")
        self.logger = setup_logging()
        self.logger.info("Demo started")
        
        # Load configuration
        print("📋 Loading configuration...")
        try:
            self.config = load_config()
            print(f"   ✓ Configuration loaded successfully")
            self._print_config_summary()
        except Exception as e:
            print(f"   ✗ Failed to load config: {e}")
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
        
        # Event system
        print("   • Event Manager...", end="")
        self.event_manager = EventManager(
            debounce_seconds=self.config.events.debounce_seconds,
            departed_threshold_seconds=self.config.events.departed_threshold_seconds
        )
        # Register callbacks to track events
        self.event_manager.add_callback(EventType.PERSON_RECOGNIZED, self._on_person_recognized)
        self.event_manager.add_callback(EventType.PERSON_UNKNOWN, self._on_person_unknown)
        print(" ✓")
        
        # Behavior system
        print("   • Behavior Manager...", end="")
        self.behavior_manager = BehaviorManager(
            enable_robot=self.config.behaviors.enable_robot
        )
        print(" ✓")
        
        # Voice system
        if self.config.tts.use_enhanced_voice:
            print("   • Enhanced Voice System...", end="")
            self.greeting_selector = GreetingSelector(
                personality=self.config.greetings.personality,
                non_repetition_window=self.config.greetings.repetition_window
            )
            self.adaptive_tts = AdaptiveTTSManager(
                enable_caching=self.config.tts.cache.enabled
            )
            print(" ✓")
        else:
            print("   • Legacy TTS...", end="")
            self.greeting_selector = None
            self.adaptive_tts = None
            print(" ✓")
        
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
        
        # Idle manager
        print("   • Idle Manager...", end="")
        self.idle_manager = IdleManager(
            behavior_manager=self.behavior_manager,
            activation_threshold=self.config.behaviors.idle.activation_threshold,
            idle_interval=self.config.behaviors.idle.movement_interval
        )
        # Always start idle manager
        self.idle_manager.start()
        print(" ✓")
        
        # Recognition pipeline
        print("   • Recognition Pipeline...", end="")
        self.pipeline = RecognitionPipeline(
            process_every_n_frames=self.config.performance.process_every_n_frames
        )
        # Load face database if it exists
        if Path("data/faces.json").exists():
            self.pipeline.load_database("data/faces.json")
        print(" ✓")
    
    def _on_person_recognized(self, event):
        """Track recognized person events."""
        self.stats['faces_recognized'] += 1
        self.stats['greetings_given'] += 1
        print(f"\n👤 Recognized: {event.person_name} (confidence: {event.confidence:.2f})")
    
    def _on_person_unknown(self, event):
        """Track unknown person events."""
        self.stats['unknown_faces'] += 1
        print(f"\n❓ Unknown person detected (confidence: {event.confidence:.2f})")
    
    def run(self, duration: Optional[int] = None):
        """
        Run the demonstration.
        
        Args:
            duration: Demo duration in seconds (None = run until Ctrl+C)
        """
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration if duration else None
        
        print("\n▶️  Starting demonstration...")
        if duration:
            print(f"   Running for {duration} seconds ({duration//60}m {duration%60}s)")
        else:
            print("   Running until Ctrl+C")
        
        print("\n📸 Camera feed active - Point camera at faces")
        print("   • Known faces will be greeted by name")
        print("   • Unknown faces will receive generic greeting")
        print("   • Idle behaviors activate when no faces present")
        print("\n   Press 'q' to quit early\n")
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: self.stop())
        
        try:
            while self.running:
                # Check duration
                if end_time and time.time() >= end_time:
                    print("\n⏱️  Demo duration reached")
                    break
                
                # Get frame
                ret, frame = self.pipeline.camera.read_frame()
                if not ret or frame is None:
                    print("⚠️  Failed to read frame")
                    time.sleep(0.1)
                    continue
                
                self.stats['frames_processed'] += 1
                
                # Process frame for recognition
                results = self.pipeline.process_frame(frame)
                
                if results:
                    self.stats['faces_detected'] += len(results)
                    
                    # Results are tuples: (name, confidence, bbox)
                    # Process through event manager
                    events = self.event_manager.process_recognition_results(
                        results,
                        frame_number=self.stats['frames_processed']
                    )
                    
                    # Draw on frame for display
                    if self.display:
                        for name, confidence, location in results:
                            result_dict = {
                                'name': name,
                                'confidence': confidence,
                                'location': location
                            }
                            self._draw_detection(frame, result_dict)
                
                # Display frame
                if self.display:
                    self._draw_stats_overlay(frame)
                    cv2.imshow('Reachy Recognizer Demo', frame)
                    
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n🛑 User requested quit")
                        break
                
                # Small delay to control frame rate
                time.sleep(0.01)
        
        except Exception as e:
            print(f"\n❌ Error during demo: {e}")
            self.logger.error(f"Demo error: {e}", exc_info=True)
        
        finally:
            self.stop()
    
    def _draw_detection(self, frame, result):
        """Draw bounding box and label on frame."""
        top, right, bottom, left = result['location']
        name = result['name']
        confidence = result['confidence']
        
        # Color: green for known, yellow for unknown
        color = (0, 255, 0) if name != 'Unknown' else (0, 255, 255)
        
        # Draw rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        
        # Draw label background
        label = f"{name} ({confidence:.0%})"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (left, bottom), (left + label_size[0], bottom + 25), color, -1)
        
        # Draw label text
        cv2.putText(frame, label, (left + 5, bottom + 18),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    def _draw_stats_overlay(self, frame):
        """Draw statistics overlay on frame."""
        elapsed = time.time() - self.start_time
        fps = self.stats['frames_processed'] / elapsed if elapsed > 0 else 0
        
        # Stats text
        stats_lines = [
            f"FPS: {fps:.1f}",
            f"Frames: {self.stats['frames_processed']}",
            f"Faces: {self.stats['faces_detected']}",
            f"Recognized: {self.stats['faces_recognized']}",
            f"Unknown: {self.stats['unknown_faces']}",
            f"Greetings: {self.stats['greetings_given']}",
            f"Time: {int(elapsed)}s"
        ]
        
        # Draw background
        overlay_height = len(stats_lines) * 25 + 10
        cv2.rectangle(frame, (5, 5), (200, overlay_height), (0, 0, 0), -1)
        
        # Draw text
        y = 25
        for line in stats_lines:
            cv2.putText(frame, line, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                       0.5, (255, 255, 255), 1)
            y += 25
    
    def stop(self):
        """Stop the demonstration."""
        if not self.running:
            return
        
        print("\n\n🛑 Stopping demonstration...")
        self.running = False
        
        # Stop subsystems
        if hasattr(self, 'idle_manager'):
            self.idle_manager.stop()
        
        if hasattr(self, 'pipeline') and hasattr(self.pipeline, 'camera'):
            self.pipeline.camera.release()
        
        if self.display:
            cv2.destroyAllWindows()
        
        # Generate final report
        self._generate_report()
    
    def _generate_report(self):
        """Generate and display final demo report."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "="*80)
        print("📊 DEMO SUMMARY REPORT")
        print("="*80)
        
        print(f"\n⏱️  Duration: {elapsed:.1f}s ({int(elapsed//60)}m {int(elapsed%60)}s)")
        
        print(f"\n📸 Camera Performance:")
        print(f"   • Frames processed: {self.stats['frames_processed']}")
        print(f"   • Average FPS: {self.stats['frames_processed']/elapsed:.1f}")
        
        print(f"\n👥 Face Detection:")
        print(f"   • Total faces detected: {self.stats['faces_detected']}")
        print(f"   • Detection rate: {self.stats['faces_detected']/self.stats['frames_processed']*100:.1f}% of frames")
        
        print(f"\n🎯 Recognition:")
        print(f"   • Recognized (known): {self.stats['faces_recognized']}")
        print(f"   • Unknown: {self.stats['unknown_faces']}")
        if self.stats['faces_detected'] > 0:
            recognition_rate = self.stats['faces_recognized'] / self.stats['faces_detected'] * 100
            print(f"   • Recognition rate: {recognition_rate:.1f}%")
        
        print(f"\n💬 Interactions:")
        print(f"   • Greetings given: {self.stats['greetings_given']}")
        print(f"   • Idle behaviors: {self.stats['idle_behaviors']}")
        
        # Get accuracy report from event manager
        if hasattr(self, 'event_manager'):
            accuracy = self.event_manager.get_accuracy_report()
            print(f"\n📈 Accuracy Metrics:")
            for key, value in accuracy.items():
                print(f"   • {key}: {value}")
        
        # Log file info
        log_file = Path("logs/reachy_recognizer.log")
        if log_file.exists():
            size_kb = log_file.stat().st_size / 1024
            print(f"\n📝 Logging:")
            print(f"   • Log file: {log_file}")
            print(f"   • Size: {size_kb:.2f} KB")
            print(f"\n   Analyze with:")
            print(f"     python tools/analyze_logs.py {log_file}")
        
        print("\n" + "="*80)
        print("✅ Demo complete!")
        print("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Reachy Recognizer System Demonstration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo.py                           # Run demo with display
  python demo.py --duration 300            # 5 minute demo
  python demo.py --no-display              # Headless mode
  python demo.py --benchmark --duration 60 # 1 minute benchmark
        """
    )
    
    parser.add_argument(
        '--duration',
        type=int,
        default=None,
        help='Demo duration in seconds (default: run until Ctrl+C)'
    )
    
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Disable camera feed window (headless mode)'
    )
    
    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Enable detailed performance benchmarking'
    )
    
    args = parser.parse_args()
    
    try:
        demo = SystemDemo(
            display=not args.no_display,
            benchmark=args.benchmark
        )
        demo.run(duration=args.duration)
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
