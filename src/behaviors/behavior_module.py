"""
Behavior Module - Story 3.1

Defines greeting behaviors for different recognition scenarios, mapping events
to Reachy's physical actions (head movements, gestures).

This module provides non-blocking behavior execution that integrates with the
event system to create natural, responsive robot interactions.
"""

import threading
import time
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum

import numpy as np
from scipy.spatial.transform import Rotation as R

# Import Reachy SDK utilities
try:
    from reachy_mini import ReachyMini
    from reachy_mini.utils import create_head_pose
    REACHY_AVAILABLE = True
except ImportError:
    REACHY_AVAILABLE = False
    print("Warning: reachy_mini not available - using mock mode")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import config (optional - falls back to defaults)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default behavior settings")


@dataclass
class BehaviorAction:
    """
    Single action in a behavior sequence.
    
    Attributes:
        roll: Head roll angle in degrees (-30 to 30)
        pitch: Head pitch angle in degrees (-40 to 40)
        yaw: Head yaw angle in degrees (-180 to 180)
        x: Head x position in meters (forward/back)
        y: Head y position in meters (left/right)
        z: Head z position in meters (up/down)
        duration: Time to hold this pose (seconds)
        blocking: If True, wait for duration before next action
    """
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    duration: float = 0.5
    blocking: bool = True
    
    def to_pose_matrix(self) -> np.ndarray:
        """Convert action to 4x4 pose matrix for Reachy."""
        if REACHY_AVAILABLE:
            return create_head_pose(
                x=self.x,
                y=self.y,
                z=self.z,
                roll=self.roll,
                pitch=self.pitch,
                yaw=self.yaw,
                degrees=True,
                mm=False
            )
        else:
            # Mock implementation
            return np.eye(4)


@dataclass
class Behavior:
    """
    Sequence of actions defining a complete behavior.
    
    Attributes:
        name: Behavior identifier
        actions: List of BehaviorAction to execute sequentially
        interruptible: If True, can be stopped by higher priority behavior
        priority: Higher priority behaviors can interrupt lower (1-10)
    """
    name: str
    actions: List[BehaviorAction]
    interruptible: bool = True
    priority: int = 5


class BehaviorManager:
    """
    Manages behavior execution with non-blocking threading.
    
    Handles behavior queuing, interruption, and thread-safe execution
    of robot movements in response to recognition events.
    """
    
    def __init__(self, reachy: Optional[object] = None, enable_robot: Optional[bool] = None):
        """
        Initialize behavior manager.
        
        Args:
            reachy: ReachyMini instance (None = auto-connect or mock)
            enable_robot: If False, runs in simulation mode (default from config or True)
        """
        # Load from config if available
        if _CONFIG_AVAILABLE and enable_robot is None:
            try:
                config = get_config()
                enable_robot = config.behaviors.enable_robot
                logger.info(f"Loaded enable_robot={enable_robot} from config")
            except Exception as e:
                logger.warning(f"Failed to load behavior config: {e}")
        
        # Use default if still None
        if enable_robot is None:
            enable_robot = True
        
        self.reachy = reachy
        self.enable_robot = enable_robot
        self.auto_connected = False
        
        # Try to auto-connect if reachy not provided and robot enabled
        if self.enable_robot and self.reachy is None and REACHY_AVAILABLE:
            try:
                logger.info("Attempting to connect to Reachy...")
                self.reachy = ReachyMini(media_backend="no_media")
                self.auto_connected = True
                logger.info("✓ Connected to Reachy successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Reachy: {e}")
                logger.info("Falling back to SIMULATION mode")
                self.enable_robot = False
        
        # Finalize robot status
        if not REACHY_AVAILABLE:
            self.enable_robot = False
        elif self.reachy is None:
            self.enable_robot = False
        
        # Behavior state
        self.current_behavior: Optional[Behavior] = None
        self.behavior_thread: Optional[threading.Thread] = None
        self.stop_flag = threading.Event()
        self.lock = threading.Lock()
        
        # Statistics
        self.behaviors_executed = 0
        self.behaviors_interrupted = 0
        
        if not self.enable_robot:
            logger.info("BehaviorManager initialized in SIMULATION mode")
        else:
            logger.info("BehaviorManager initialized with REAL ROBOT")
    
    def execute_behavior(self, behavior: Behavior) -> bool:
        """
        Execute a behavior in a separate thread.
        
        Args:
            behavior: Behavior to execute
            
        Returns:
            True if behavior started, False if blocked by higher priority
        """
        with self.lock:
            # Check if current behavior can be interrupted
            if self.current_behavior is not None:
                if not self.current_behavior.interruptible:
                    logger.debug(f"Behavior '{self.current_behavior.name}' is not interruptible")
                    return False
                
                if behavior.priority <= self.current_behavior.priority:
                    logger.debug(f"Behavior '{behavior.name}' has lower/equal priority")
                    return False
            
            # Stop current behavior if any
            if self.current_behavior is not None:
                logger.info(f"Interrupting behavior '{self.current_behavior.name}' for '{behavior.name}'")
                self.stop_current()
                self.behaviors_interrupted += 1
            
            # Start new behavior
            self.current_behavior = behavior
            self.stop_flag.clear()
            
            self.behavior_thread = threading.Thread(
                target=self._run_behavior,
                args=(behavior,),
                daemon=True
            )
            self.behavior_thread.start()
            
            logger.info(f"Started behavior '{behavior.name}' (priority {behavior.priority})")
            return True
    
    def _run_behavior(self, behavior: Behavior):
        """Execute behavior actions sequentially (runs in separate thread)."""
        try:
            start_time = time.time()
            
            for i, action in enumerate(behavior.actions):
                # Check if behavior should stop
                if self.stop_flag.is_set():
                    logger.debug(f"Behavior '{behavior.name}' stopped at action {i}")
                    break
                
                # Execute action
                if self.enable_robot:
                    try:
                        pose = action.to_pose_matrix()
                        self.reachy.set_target(head=pose)
                        logger.debug(f"Action {i}: roll={action.roll:.1f}, pitch={action.pitch:.1f}, yaw={action.yaw:.1f}")
                    except Exception as e:
                        logger.error(f"Failed to execute action {i}: {e}")
                        break
                else:
                    # Simulation mode - just log
                    logger.debug(f"[SIM] Action {i}: roll={action.roll:.1f}, pitch={action.pitch:.1f}, yaw={action.yaw:.1f}")
                
                # Wait for duration if blocking
                if action.blocking:
                    time.sleep(action.duration)
            
            # Behavior complete
            elapsed = time.time() - start_time
            logger.info(f"Behavior '{behavior.name}' completed in {elapsed:.2f}s")
            
        except Exception as e:
            logger.error(f"Error executing behavior '{behavior.name}': {e}")
        
        finally:
            with self.lock:
                if self.current_behavior == behavior:
                    self.current_behavior = None
                    self.behaviors_executed += 1
    
    def stop_current(self):
        """Stop currently executing behavior."""
        if self.behavior_thread is not None and self.behavior_thread.is_alive():
            self.stop_flag.set()
            self.behavior_thread.join(timeout=2.0)
            
            if self.behavior_thread.is_alive():
                logger.warning("Behavior thread did not stop within timeout")
    
    def is_executing(self) -> bool:
        """Check if a behavior is currently executing."""
        return self.current_behavior is not None
    
    def get_current_behavior(self) -> Optional[str]:
        """Get name of currently executing behavior."""
        if self.current_behavior is not None:
            return self.current_behavior.name
        return None
    
    def get_stats(self) -> Dict[str, int]:
        """Get behavior execution statistics."""
        return {
            "behaviors_executed": self.behaviors_executed,
            "behaviors_interrupted": self.behaviors_interrupted,
            "currently_executing": self.current_behavior is not None
        }
    
    def close(self):
        """Cleanup resources (close robot connection if auto-connected)."""
        if self.auto_connected and self.reachy is not None:
            try:
                logger.info("Closing Reachy connection...")
                # ReachyMini uses __exit__ for cleanup, not close()
                if hasattr(self.reachy, '__exit__'):
                    self.reachy.__exit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing Reachy connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# =============================================================================
# Predefined Behaviors
# =============================================================================

# Greeting wave for recognized person (AC: 2)
greeting_wave = Behavior(
    name="greeting_wave",
    actions=[
        # Look at camera
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.3,
            blocking=True
        ),
        # Tilt right (wave gesture)
        BehaviorAction(
            roll=15.0, pitch=-5.0, yaw=0.0,
            duration=0.3,
            blocking=True
        ),
        # Tilt left
        BehaviorAction(
            roll=-15.0, pitch=-5.0, yaw=0.0,
            duration=0.3,
            blocking=True
        ),
        # Return to center
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.3,
            blocking=True
        )
    ],
    interruptible=False,
    priority=8
)

# Curious tilt for unknown person (AC: 3)
curious_tilt = Behavior(
    name="curious_tilt",
    actions=[
        # Tilt head left with slight up
        BehaviorAction(
            roll=-12.0, pitch=8.0, yaw=0.0,
            duration=0.6,
            blocking=True
        ),
        # Pause in tilted position
        BehaviorAction(
            roll=-12.0, pitch=8.0, yaw=0.0,
            duration=0.4,
            blocking=True
        ),
        # Return to center
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.5,
            blocking=True
        )
    ],
    interruptible=True,
    priority=6
)

# Unknown person greeting - welcoming head tilt (Story 3.4)
unknown_greeting = Behavior(
    name="unknown_greeting",
    actions=[
        # Look at camera/person
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.3,
            blocking=True
        ),
        # Friendly tilt right with slight nod
        BehaviorAction(
            roll=10.0, pitch=-8.0, yaw=0.0,
            duration=0.5,
            blocking=True
        ),
        # Hold position
        BehaviorAction(
            roll=10.0, pitch=-8.0, yaw=0.0,
            duration=0.3,
            blocking=True
        ),
        # Return to center with slight welcoming nod
        BehaviorAction(
            roll=0.0, pitch=-5.0, yaw=0.0,
            duration=0.4,
            blocking=True
        ),
        # Final center position
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.3,
            blocking=True
        )
    ],
    interruptible=False,
    priority=7
)

# Unknown person curious - inquisitive head movements (Story 3.4)
unknown_curious = Behavior(
    name="unknown_curious",
    actions=[
        # Tilt head left with curiosity
        BehaviorAction(
            roll=-15.0, pitch=10.0, yaw=0.0,
            duration=0.5,
            blocking=True
        ),
        # Pause to "study" the person
        BehaviorAction(
            roll=-15.0, pitch=10.0, yaw=0.0,
            duration=0.5,
            blocking=True
        ),
        # Tilt right - examining from another angle
        BehaviorAction(
            roll=15.0, pitch=10.0, yaw=0.0,
            duration=0.5,
            blocking=True
        ),
        # Hold right tilt
        BehaviorAction(
            roll=15.0, pitch=10.0, yaw=0.0,
            duration=0.4,
            blocking=True
        ),
        # Return to center with slight down nod (processing)
        BehaviorAction(
            roll=0.0, pitch=-8.0, yaw=0.0,
            duration=0.5,
            blocking=True
        ),
        # Final neutral position
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.3,
            blocking=True
        )
    ],
    interruptible=True,
    priority=6
)

# Idle drift for no person present (AC: 4)
def create_idle_drift() -> Behavior:
    """
    Create idle drift behavior with randomized movement.
    
    Returns new instance each time for variation.
    """
    # Random small movements
    roll = random.uniform(-5, 5)
    pitch = random.uniform(-5, 5)
    yaw = random.uniform(-10, 10)
    duration = random.uniform(2.0, 4.0)
    
    return Behavior(
        name="idle_drift",
        actions=[
            BehaviorAction(
                roll=roll,
                pitch=pitch,
                yaw=yaw,
                duration=duration,
                blocking=False
            ),
            # Return to near-center (subtle variation)
            BehaviorAction(
                roll=random.uniform(-2, 2),
                pitch=random.uniform(-2, 2),
                yaw=random.uniform(-5, 5),
                duration=duration,
                blocking=False
            )
        ],
        interruptible=True,
        priority=1  # Lowest priority - easily interrupted
    )

# Neutral pose (return to center)
neutral_pose = Behavior(
    name="neutral",
    actions=[
        BehaviorAction(
            roll=0.0, pitch=0.0, yaw=0.0,
            duration=0.5,
            blocking=True
        )
    ],
    interruptible=True,
    priority=3
)


# =============================================================================
# Demo / Testing
# =============================================================================

def main():
    """Demo behavior execution."""
    print("=" * 60)
    print("Behavior System Demo")
    print("=" * 60)
    print()
    
    # Create manager (simulation mode if no robot)
    manager = BehaviorManager(reachy=None, enable_robot=False)
    
    print("Testing behaviors in simulation mode...\n")
    
    # Test greeting wave
    print("1. Executing greeting_wave behavior...")
    manager.execute_behavior(greeting_wave)
    time.sleep(2.0)
    
    # Test curious tilt
    print("\n2. Executing curious_tilt behavior...")
    manager.execute_behavior(curious_tilt)
    time.sleep(2.0)
    
    # Test idle drift
    print("\n3. Executing idle_drift behavior...")
    idle = create_idle_drift()
    manager.execute_behavior(idle)
    time.sleep(3.0)
    
    # Test interruption
    print("\n4. Testing interruption (idle → greeting)...")
    idle = create_idle_drift()
    manager.execute_behavior(idle)
    time.sleep(0.5)
    manager.execute_behavior(greeting_wave)  # Should interrupt idle
    time.sleep(2.0)
    
    # Show stats
    print("\n" + "=" * 60)
    print("Statistics:")
    print("=" * 60)
    stats = manager.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    main()
