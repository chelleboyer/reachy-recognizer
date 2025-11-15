"""
Gesture Coordinator - Story 3.3

Maps recognized gestures to robot commands and integrates with event system.
Handles command dispatch, duplicate prevention, and feedback triggering.

Key Features:
- Maps gestures to commands (thumbs up → approve, wave → skip, palm stop → pause)
- Prevents duplicate commands within 3-second window
- Emits GESTURE_DETECTED events via EventManager
- Triggers visual/audio feedback
- Tracks command statistics
"""

import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from collections import defaultdict, deque

import yaml
import numpy as np

from ..vision.hand_detector import HandDetector
from ..vision.gesture_recognizer import GestureRecognizer, GestureType, GestureResult
from ..events.event_system import EventManager, EventType

# Configure logging
logger = logging.getLogger(__name__)


class GestureCommand(Enum):
    """Robot commands mapped from gestures."""
    APPROVE = "approve"
    SKIP = "skip"
    PAUSE = "pause"


# Gesture to command mapping
GESTURE_COMMAND_MAP = {
    GestureType.THUMBS_UP: GestureCommand.APPROVE,
    GestureType.WAVE: GestureCommand.SKIP,
    GestureType.PALM_STOP: GestureCommand.PAUSE,
    GestureType.UNKNOWN: None  # Ignored
}


@dataclass
class GestureEvent:
    """Event emitted when gesture detected.
    
    Attributes:
        command: Mapped gesture command
        gesture_result: Full gesture recognition result
        timestamp: Event timestamp
        processed: Flag indicating if event has been processed
    """
    command: GestureCommand
    gesture_result: GestureResult
    timestamp: float
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.
        
        Returns:
            Dictionary representation of event
        """
        return {
            "command": self.command.value,
            "gesture_type": self.gesture_result.gesture_type.value,
            "confidence": self.gesture_result.confidence,
            "hand_id": self.gesture_result.hand_id,
            "handedness": self.gesture_result.handedness,
            "distance_estimate": self.gesture_result.distance_estimate,
            "hold_duration": self.gesture_result.hold_duration,
            "is_confirmed": self.gesture_result.is_confirmed,
            "timestamp": self.timestamp,
            "processed": self.processed
        }


class GestureCoordinator:
    """Coordinates gesture recognition with command execution.
    
    Integrates hand detection, gesture recognition, command mapping,
    and event emission into a unified pipeline.
    """
    
    def __init__(
        self,
        hand_detector: HandDetector,
        gesture_recognizer: GestureRecognizer,
        event_manager: EventManager,
        config_path: str = "src/config/config.yaml"
    ):
        """Initialize gesture coordinator.
        
        Args:
            hand_detector: HandDetector instance
            gesture_recognizer: GestureRecognizer instance
            event_manager: EventManager for event emission
            config_path: Path to configuration file
        """
        self.hand_detector = hand_detector
        self.gesture_recognizer = gesture_recognizer
        self.event_manager = event_manager
        
        # Load configuration
        self._load_config(config_path)
        
        # Duplicate prevention tracking (per hand)
        self.recent_gestures: Dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        
        # Statistics
        self.total_commands = 0
        self.command_counts = defaultdict(int)
        self.duplicate_blocks = 0
        self.total_processing_time = 0.0
        self.command_latencies: deque = deque(maxlen=100)
        
        # Logging
        self.enable_logging = self.config.get('debug', {}).get('enable_logging', False)
        
        logger.info("GestureCoordinator initialized")
    
    def _load_config(self, config_path: str):
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to config file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.config = config.get('gesture_control', {})
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self.config = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing config: {e}, using defaults")
            self.config = {}
        
        # Extract configuration parameters
        commands_config = self.config.get('commands', {})
        self.command_enabled = {
            GestureCommand.APPROVE: commands_config.get('approve', {}).get('enabled', True),
            GestureCommand.SKIP: commands_config.get('skip', {}).get('enabled', True),
            GestureCommand.PAUSE: commands_config.get('pause', {}).get('enabled', True),
        }
        
        self.audio_enabled = {
            GestureCommand.APPROVE: commands_config.get('approve', {}).get('audio_confirmation', False),
            GestureCommand.SKIP: commands_config.get('skip', {}).get('audio_confirmation', False),
            GestureCommand.PAUSE: commands_config.get('pause', {}).get('audio_confirmation', False),
        }
        
        self.duplicate_window = self.config.get('duplicate_window_seconds', 3.0)
        self.target_latency_ms = self.config.get('target_feedback_latency_ms', 200)
    
    def process_frame(self, frame: np.ndarray) -> List[GestureEvent]:
        """Process frame and emit gesture events.
        
        Main entry point for gesture processing pipeline:
        1. Detect hands in frame
        2. Recognize gestures from hand landmarks
        3. Map gestures to commands
        4. Check for duplicates
        5. Emit events and execute commands
        
        Args:
            frame: Camera frame (H x W x 3 RGB)
        
        Returns:
            List of GestureEvent objects emitted
        """
        start_time = time.time()
        events = []
        
        # Detect hands
        hands = self.hand_detector.detect(frame)
        
        # Process each detected hand
        for hand in hands:
            # Recognize gesture
            gesture_result = self.gesture_recognizer.recognize(hand)
            
            # Only process confirmed gestures
            if not gesture_result.is_confirmed:
                continue
            
            # Map to command
            command = self._map_gesture_to_command(gesture_result.gesture_type)
            if command is None:
                continue  # Unknown gesture or disabled command
            
            # Check for duplicates
            if self._check_duplicate(gesture_result, command):
                self.duplicate_blocks += 1
                if self.enable_logging:
                    logger.debug(
                        f"Blocked duplicate: {command.value} "
                        f"(hand {gesture_result.hand_id})"
                    )
                continue
            
            # Update recent gestures
            self._update_recent_gestures(gesture_result, command)
            
            # Create and emit event
            event = self._emit_gesture_event(gesture_result, command)
            events.append(event)
            
            # Execute command (feedback, logging)
            self._execute_command(command, gesture_result)
        
        # Update statistics
        processing_time = (time.time() - start_time) * 1000  # ms
        self.total_processing_time += processing_time
        if events:
            self.command_latencies.append(processing_time)
        
        return events
    
    def _map_gesture_to_command(self, gesture_type: GestureType) -> Optional[GestureCommand]:
        """Map gesture type to command.
        
        Args:
            gesture_type: Detected gesture type
        
        Returns:
            Mapped command or None if unknown/disabled
        """
        command = GESTURE_COMMAND_MAP.get(gesture_type)
        
        # Check if command is enabled
        if command and not self.command_enabled.get(command, True):
            return None
        
        return command
    
    def _check_duplicate(self, gesture_result: GestureResult, command: GestureCommand) -> bool:
        """Check if gesture is duplicate within window.
        
        Prevents same gesture/command from same hand within duplicate window.
        
        Args:
            gesture_result: Gesture recognition result
            command: Mapped command
        
        Returns:
            True if duplicate, False otherwise
        """
        hand_id = gesture_result.hand_id
        current_time = gesture_result.timestamp
        
        # Get recent gestures for this hand
        recent = self.recent_gestures[hand_id]
        
        # Check for duplicates within window
        for prev_command, prev_time in recent:
            if prev_command == command:
                time_delta = current_time - prev_time
                if time_delta < self.duplicate_window:
                    return True  # Duplicate found
        
        return False  # Not a duplicate
    
    def _update_recent_gestures(self, gesture_result: GestureResult, command: GestureCommand):
        """Track recent gesture for duplicate prevention.
        
        Args:
            gesture_result: Gesture recognition result
            command: Mapped command
        """
        hand_id = gesture_result.hand_id
        timestamp = gesture_result.timestamp
        
        self.recent_gestures[hand_id].append((command, timestamp))
    
    def _emit_gesture_event(self, gesture_result: GestureResult, command: GestureCommand) -> GestureEvent:
        """Emit GESTURE_DETECTED event.
        
        Creates GestureEvent and publishes via EventManager.
        
        Args:
            gesture_result: Gesture recognition result
            command: Mapped command
        
        Returns:
            Created GestureEvent
        """
        event = GestureEvent(
            command=command,
            gesture_result=gesture_result,
            timestamp=time.time(),
            processed=False
        )
        
        # Emit via EventManager
        self.event_manager.emit(EventType.GESTURE_DETECTED, event)
        
        # Update statistics
        self.total_commands += 1
        self.command_counts[command] += 1
        
        # Log if enabled
        if self.enable_logging:
            logger.info(
                f"Gesture command: {command.value} "
                f"(gesture: {gesture_result.gesture_type.value}, "
                f"confidence: {gesture_result.confidence:.2f}, "
                f"hand: {gesture_result.handedness})"
            )
        
        return event
    
    def _execute_command(self, command: GestureCommand, gesture_result: GestureResult):
        """Execute command and trigger feedback.
        
        Placeholder for command execution logic. Currently handles:
        - Visual feedback triggering (via FeedbackManager in Story 3.4)
        - Audio feedback (if enabled)
        - Command logging
        
        Args:
            command: Command to execute
            gesture_result: Gesture recognition result
        """
        # TODO: Trigger visual feedback (Story 3.4)
        # feedback_manager.show_gesture_feedback(gesture_result.gesture_type)
        
        # TODO: Trigger audio feedback if enabled
        # if self.audio_enabled.get(command, False):
        #     self._play_confirmation_beep(command)
        
        # Log command execution
        if self.enable_logging:
            logger.debug(
                f"Executed command: {command.value} "
                f"(distance: {gesture_result.distance_estimate:.2f}m, "
                f"hold: {gesture_result.hold_duration:.2f}s)"
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get command execution statistics.
        
        Returns:
            Dictionary with statistics:
            - total_commands: Total commands processed
            - command_counts: Counts per command type
            - duplicate_blocks: Number of blocked duplicates
            - avg_latency_ms: Average processing latency
            - active_hands: Number of hands being tracked
        """
        avg_latency = (
            np.mean(list(self.command_latencies)) if self.command_latencies
            else 0.0
        )
        
        return {
            "total_commands": self.total_commands,
            "command_counts": {cmd.value: count for cmd, count in self.command_counts.items()},
            "duplicate_blocks": self.duplicate_blocks,
            "avg_latency_ms": float(avg_latency),
            "active_hands": len(self.recent_gestures),
            "total_processing_time_ms": self.total_processing_time
        }
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.total_commands = 0
        self.command_counts.clear()
        self.duplicate_blocks = 0
        self.total_processing_time = 0.0
        self.command_latencies.clear()
        
        logger.info("Statistics reset")
