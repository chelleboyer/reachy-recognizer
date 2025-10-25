"""
Reachy Recognizer - Main Entry Point

Face recognition and greeting robot system for Reachy Mini.
Integrates vision, behaviors, voice, and coordination subsystems.
"""

import sys
import signal
import logging
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config import load_config
from src.vision import RecognitionPipeline
from src.events import EventManager, EventType
from src.behaviors import BehaviorManager, IdleManager
from src.voice import AdaptiveTTSManager, GreetingSelector
from src.coordination import GreetingCoordinator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main application entry point."""
    print("\n" + "="*70)
    print("🤖 Reachy Recognizer - Face Recognition & Greeting System")
    print("="*70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    try:
        config = load_config()
        logger.info("✓ Configuration loaded")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Initialize subsystems
    print("\n🔧 Initializing subsystems...")
    
    try:
        # Event system
        event_manager = EventManager(
            debounce_seconds=config.events.debounce_seconds,
            departed_threshold_seconds=config.events.departed_threshold_seconds
        )
        logger.info("✓ Event system initialized")
        
        # Behavior system
        behavior_manager = BehaviorManager(enable_robot=config.behaviors.enable_robot)
        logger.info("✓ Behavior system initialized")
        
        # Voice system (if enhanced voice enabled)
        if config.tts.use_enhanced_voice:
            greeting_selector = GreetingSelector(
                personality=config.greetings.personality,
                non_repetition_window=config.greetings.repetition_window
            )
            adaptive_tts = AdaptiveTTSManager(enable_caching=config.tts.cache.enabled)
            logger.info("✓ Enhanced voice system initialized")
        else:
            greeting_selector = None
            adaptive_tts = None
            logger.info("✓ Using legacy TTS")
        
        # Coordination
        coordinator = GreetingCoordinator(
            event_manager=event_manager,
            behavior_manager=behavior_manager,
            gesture_speech_delay=config.behaviors.gesture_speech_delay,
            adaptive_tts=adaptive_tts,
            greeting_selector=greeting_selector,
            use_enhanced_voice=config.tts.use_enhanced_voice
        )
        logger.info("✓ Greeting coordinator initialized")
        
        # Idle manager
        idle_manager = IdleManager(
            behavior_manager=behavior_manager,
            activation_threshold=config.behaviors.idle.activation_threshold,
            idle_interval=config.behaviors.idle.movement_interval
        )
        idle_manager.start()
        logger.info("✓ Idle manager started")
        
        # Recognition pipeline
        pipeline = RecognitionPipeline(
            recognition_threshold=config.face_recognition.threshold,
            enable_events=True
        )
        
        # Load face database
        pipeline.load_database("data/faces.json")
        logger.info("✓ Recognition pipeline initialized")
        
        # CRITICAL: Re-register coordinator with pipeline's event manager
        # The pipeline creates its own EventManager, so we need to use that one
        pipeline.event_manager.add_callback(
            EventType.PERSON_RECOGNIZED,
            coordinator._on_person_recognized
        )
        logger.info("✓ Coordinator connected to pipeline events")
        
    except Exception as e:
        logger.error(f"Failed to initialize subsystems: {e}", exc_info=True)
        return 1
    
    # Setup shutdown handler
    def shutdown_handler(signum, frame):
        print("\n\n🛑 Shutting down...")
        pipeline.camera.release()
        idle_manager.stop()
        print("✓ Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Start system
    print("\n" + "="*70)
    print("✨ System ready! Starting recognition...")
    print("="*70)
    print("\n👀 Looking for faces...")
    print("   Press Ctrl+C to stop\n")
    
    try:
        # Run recognition loop
        import cv2
        while True:
            ret, frame = pipeline.camera.read_frame()
            if not ret or frame is None:
                continue
            
            # Process frame
            results = pipeline.process_frame(frame)
            
            # Display if debug mode
            if config.system.debug_display:
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
                
                cv2.imshow('Reachy Recognizer', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"Runtime error: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        pipeline.camera.release()
        idle_manager.stop()
        if config.system.debug_display:
            cv2.destroyAllWindows()
        logger.info("System stopped")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
