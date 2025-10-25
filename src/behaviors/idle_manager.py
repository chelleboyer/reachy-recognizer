"""
Idle Manager - Story 3.4

Manages idle behaviors when no faces are detected (NO_FACES state).
Coordinates subtle, natural movements to keep Reachy looking alive and attentive.

The idle manager activates after a configurable threshold (default 5s) and
deactivates immediately when a face is detected.
"""

import threading
import time
import logging
from typing import Optional, Callable
from datetime import datetime, timedelta

from .behavior_module import BehaviorManager, create_idle_drift
from ..events.event_system import EventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import config (optional - falls back to defaults)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default idle settings")


class IdleManager:
    """
    Manages idle behaviors during NO_FACES state.
    
    Activates subtle idle movements (drift, look-around) after a threshold
    period with no face detection. Deactivates immediately when faces appear.
    
    Features:
    - Thread-based monitoring for non-blocking operation
    - Configurable activation threshold
    - Smooth behavior transitions
    - Automatic deactivation on face detection
    """
    
    def __init__(
        self,
        behavior_manager: BehaviorManager,
        activation_threshold: Optional[float] = None,
        idle_interval: Optional[float] = None
    ):
        """
        Initialize IdleManager.
        
        Args:
            behavior_manager: BehaviorManager for executing idle behaviors
            activation_threshold: Seconds of NO_FACES before activating idle (default from config or 5.0)
            idle_interval: Seconds between idle behavior executions (default from config or 3.0)
        """
        # Load from config if available
        if _CONFIG_AVAILABLE and (activation_threshold is None or idle_interval is None):
            try:
                config = get_config()
                if activation_threshold is None:
                    activation_threshold = config.behaviors.idle.activation_threshold
                if idle_interval is None:
                    idle_interval = config.behaviors.idle.movement_interval
                logger.info("Loaded idle settings from config")
            except Exception as e:
                logger.warning(f"Failed to load idle config: {e}")
        
        # Use defaults if still None
        if activation_threshold is None:
            activation_threshold = 5.0
        if idle_interval is None:
            idle_interval = 3.0
        
        self.behavior_manager = behavior_manager
        self.activation_threshold = activation_threshold
        self.idle_interval = idle_interval
        
        # State tracking
        self.active = False
        self.last_face_time: Optional[datetime] = None
        self.idle_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Thread control
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        logger.info(
            f"IdleManager initialized: threshold={activation_threshold}s, "
            f"interval={idle_interval}s"
        )
    
    def start(self):
        """Start the idle manager monitoring thread."""
        if self.running:
            logger.warning("IdleManager already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start monitoring thread
        self.idle_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="IdleManager"
        )
        self.idle_thread.start()
        
        logger.info("IdleManager started")
    
    def stop(self):
        """Stop the idle manager and deactivate any idle behaviors."""
        if not self.running:
            return
        
        self.running = False
        self._stop_event.set()
        
        # Deactivate idle state
        self._deactivate_idle()
        
        # Wait for thread to finish
        if self.idle_thread and self.idle_thread.is_alive():
            self.idle_thread.join(timeout=2.0)
        
        logger.info("IdleManager stopped")
    
    def notify_face_detected(self):
        """
        Notify manager that a face was detected.
        
        This immediately deactivates idle behaviors and resets the timer.
        Should be called on RECOGNIZED, UNKNOWN, or any face detection event.
        """
        with self._lock:
            self.last_face_time = datetime.now()
            
            if self.active:
                self._deactivate_idle()
    
    def notify_no_faces(self):
        """
        Notify manager that no faces are detected.
        
        Starts the activation timer if not already tracking.
        Should be called on NO_FACES or DEPARTED events.
        """
        with self._lock:
            if self.last_face_time is None:
                # First NO_FACES - start timer
                self.last_face_time = datetime.now()
                logger.debug("NO_FACES: Starting idle activation timer")
    
    def _monitor_loop(self):
        """
        Main monitoring loop (runs in separate thread).
        
        Checks periodically if idle should be activated based on
        time since last face detection.
        """
        logger.debug("Idle monitoring loop started")
        
        while self.running and not self._stop_event.is_set():
            try:
                # Check if we should activate idle
                if not self.active:
                    self._check_activation()
                else:
                    # Already active - execute idle behaviors periodically
                    self._execute_idle_behavior()
                
                # Sleep for interval
                self._stop_event.wait(timeout=self.idle_interval)
                
            except Exception as e:
                logger.error(f"Error in idle monitor loop: {e}", exc_info=True)
        
        logger.debug("Idle monitoring loop stopped")
    
    def _check_activation(self):
        """Check if idle should be activated based on threshold."""
        with self._lock:
            if self.last_face_time is None:
                return
            
            time_since_face = (datetime.now() - self.last_face_time).total_seconds()
            
            if time_since_face >= self.activation_threshold and not self.active:
                self._activate_idle()
    
    def _activate_idle(self):
        """Activate idle behaviors."""
        self.active = True
        logger.info("🌙 Idle behaviors activated (no faces detected)")
        
        # Execute first idle behavior immediately
        self._execute_idle_behavior()
    
    def _deactivate_idle(self):
        """Deactivate idle behaviors."""
        if not self.active:
            return
        
        self.active = False
        self.last_face_time = None
        logger.info("☀️ Idle behaviors deactivated (face detected)")
        
        # Note: Don't interrupt current behavior - let it finish naturally
        # Higher priority behaviors (greetings) will interrupt if needed
    
    def _execute_idle_behavior(self):
        """Execute a randomized idle behavior."""
        if not self.active:
            return
        
        try:
            # Create random idle drift behavior
            idle_behavior = create_idle_drift()
            
            # Execute non-blocking (will be interrupted by higher priority behaviors)
            logger.debug("Executing idle drift")
            self.behavior_manager.execute_behavior(idle_behavior)
            
        except Exception as e:
            logger.error(f"Error executing idle behavior: {e}")
    
    def get_status(self) -> dict:
        """
        Get current idle manager status.
        
        Returns:
            Dictionary with status information
        """
        with self._lock:
            time_since_face = None
            if self.last_face_time:
                time_since_face = (datetime.now() - self.last_face_time).total_seconds()
            
            return {
                "running": self.running,
                "active": self.active,
                "time_since_face": time_since_face,
                "activation_threshold": self.activation_threshold,
                "will_activate_in": (
                    max(0, self.activation_threshold - time_since_face)
                    if time_since_face is not None and not self.active
                    else None
                )
            }


def demo():
    """Demo idle manager functionality."""
    print("\n" + "="*70)
    print("🌙 Idle Manager Demo")
    print("="*70)
    
    # Create behavior manager (simulation mode)
    from .behavior_module import BehaviorManager
    behavior_manager = BehaviorManager(enable_robot=False)
    
    # Create idle manager with short threshold for demo
    idle_manager = IdleManager(
        behavior_manager=behavior_manager,
        activation_threshold=2.0,  # 2 seconds for demo
        idle_interval=1.5  # Check every 1.5s
    )
    
    print("\n1. Starting idle manager...")
    idle_manager.start()
    
    print("\n2. Simulating NO_FACES state...")
    idle_manager.notify_no_faces()
    
    print("   Waiting for idle activation (2s threshold)...")
    for i in range(5):
        time.sleep(1)
        status = idle_manager.get_status()
        if status['active']:
            print(f"   ✓ Idle activated after {status['time_since_face']:.1f}s")
            break
        else:
            remaining = status['will_activate_in']
            print(f"   - {i+1}s: Idle activates in {remaining:.1f}s")
    
    print("\n3. Letting idle behaviors run...")
    time.sleep(3)
    
    print("\n4. Simulating face detection...")
    idle_manager.notify_face_detected()
    status = idle_manager.get_status()
    print(f"   ✓ Idle deactivated: active={status['active']}")
    
    print("\n5. Simulating NO_FACES again...")
    idle_manager.notify_no_faces()
    time.sleep(3)
    
    print("\n6. Stopping idle manager...")
    idle_manager.stop()
    
    print("\n" + "="*70)
    print("✓ Demo complete!")
    print("="*70)


if __name__ == "__main__":
    demo()
