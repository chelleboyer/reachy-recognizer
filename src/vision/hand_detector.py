"""MediaPipe Hand Detection Module

Story 3.1: MediaPipe Hand Detection Setup

This module provides hand detection and landmark extraction using MediaPipe Hands.
Supports detection of up to 2 hands with 21 landmarks each, achieving 10+ FPS
for responsive gesture recognition.

Key Features:
- MediaPipe Hands integration with configurable parameters
- 21 landmark points per hand (fingers, palm, wrist)
- Left/right hand differentiation
- Performance tracking (FPS, detection counts)
- World coordinate support for distance estimation

Classes:
    HandLandmarks: Dataclass representing detected hand landmarks
    HandDetector: Main detector class for hand landmark extraction

Example:
    >>> detector = HandDetector("src/config/hand_detection.yaml")
    >>> hands = detector.detect(frame)
    >>> for hand in hands:
    ...     print(f"Detected {hand.handedness} hand with {len(hand.landmarks)} landmarks")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
import logging

import cv2
import numpy as np
import yaml

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    mp = None

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class HandLandmarks:
    """Represents detected hand landmarks from MediaPipe.
    
    Contains all landmark information for a single detected hand including
    position coordinates, hand type (left/right), confidence scores, and
    world coordinates for distance estimation.
    
    Attributes:
        hand_id: Unique identifier for this hand in the current frame
        handedness: "Left" or "Right" indicating which hand
        landmarks: List of 21 (x, y, z) tuples in normalized coordinates [0,1]
                  z represents depth relative to wrist (negative = toward camera)
        world_landmarks: List of 21 (x, y, z) tuples in world coordinates (meters)
                        Relative to hand geometric center
        confidence: Detection confidence score (0.0-1.0)
        timestamp: Unix timestamp when landmarks were detected
    """
    hand_id: int
    handedness: str  # "Left" or "Right"
    landmarks: List[Tuple[float, float, float]]
    world_landmarks: List[Tuple[float, float, float]]
    confidence: float
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert landmarks to dictionary format.
        
        Returns:
            Dictionary with all landmark data and metadata
        """
        return {
            "hand_id": self.hand_id,
            "handedness": self.handedness,
            "landmarks": [{"x": x, "y": y, "z": z} for x, y, z in self.landmarks],
            "world_landmarks": [{"x": x, "y": y, "z": z} for x, y, z in self.world_landmarks],
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }
    
    def get_landmark(self, index: int) -> Tuple[float, float, float]:
        """Get specific landmark by index.
        
        Args:
            index: Landmark index (0-20)
                  0 = WRIST, 4 = THUMB_TIP, 8 = INDEX_TIP, etc.
        
        Returns:
            (x, y, z) tuple for the specified landmark
        
        Raises:
            IndexError: If index is out of range
        """
        if index < 0 or index >= len(self.landmarks):
            raise IndexError(f"Landmark index {index} out of range (0-{len(self.landmarks)-1})")
        return self.landmarks[index]


class HandDetector:
    """MediaPipe-based hand detector for landmark extraction.
    
    Detects hands in video frames and extracts 21 landmark points per hand.
    Supports up to 2 hands simultaneously with left/right differentiation.
    Achieves 10+ FPS performance target for responsive gesture recognition.
    
    Attributes:
        config_path: Path to hand_detection.yaml configuration file
        config: Loaded configuration dictionary
        hands: MediaPipe Hands solution instance
        detection_count: Number of successful detections
        frame_count: Total frames processed
        last_fps_update: Timestamp of last FPS calculation
        fps: Current frames per second
    """
    
    def __init__(self, config_path: str):
        """Initialize HandDetector with configuration.
        
        Args:
            config_path: Path to hand_detection.yaml configuration file
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If MediaPipe is not installed
            yaml.YAMLError: If config file is invalid
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        if not MEDIAPIPE_AVAILABLE:
            raise ValueError(
                "MediaPipe is not installed. Install with: pip install mediapipe>=0.10.8"
            )
        
        # Load configuration
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Extract MediaPipe parameters
        mp_config = self.config.get('mediapipe', {})
        self.model_complexity = mp_config.get('model_complexity', 1)
        self.min_detection_confidence = mp_config.get('min_detection_confidence', 0.5)
        self.min_tracking_confidence = mp_config.get('min_tracking_confidence', 0.5)
        self.max_num_hands = mp_config.get('max_num_hands', 2)
        self.static_image_mode = mp_config.get('static_image_mode', False)
        
        # Extract performance parameters
        perf_config = self.config.get('performance', {})
        self.target_fps = perf_config.get('target_fps', 15)
        self.max_latency_ms = perf_config.get('max_latency_ms', 66)
        self.enable_logging = perf_config.get('enable_logging', True)
        self.stats_update_interval = perf_config.get('stats_update_interval', 30)
        
        # Extract output parameters
        output_config = self.config.get('output', {})
        self.include_world_landmarks = output_config.get('include_world_landmarks', True)
        self.normalize_coordinates = output_config.get('normalize_coordinates', True)
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.static_image_mode,
            max_num_hands=self.max_num_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        
        # Initialize statistics tracking
        self.detection_count = 0
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.fps = 0.0
        self.total_latency_ms = 0.0
        self.start_time = time.time()
        
        logger.info(f"HandDetector initialized with config from {config_path}")
        logger.info(f"Target FPS: {self.target_fps}, Max latency: {self.max_latency_ms}ms")
    
    def detect(self, frame: np.ndarray) -> List[HandLandmarks]:
        """Detect hands and extract landmarks from a video frame.
        
        Processes the input frame using MediaPipe Hands to detect up to
        max_num_hands hands and extract 21 landmarks per hand.
        
        Args:
            frame: Input BGR image from camera (numpy array)
        
        Returns:
            List of HandLandmarks objects, one per detected hand.
            Empty list if no hands detected.
        
        Raises:
            ValueError: If frame is invalid or empty
        """
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame: frame is None or empty")
        
        start_time = time.time()
        
        # Convert BGR to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame with MediaPipe
        results = self.hands.process(frame_rgb)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        self.total_latency_ms += latency_ms
        
        # Update frame count
        self.frame_count += 1
        
        # Update FPS statistics periodically
        if self.frame_count % self.stats_update_interval == 0:
            self._update_fps()
        
        # Extract hand landmarks if detected
        detected_hands: List[HandLandmarks] = []
        
        if results.multi_hand_landmarks:
            self.detection_count += len(results.multi_hand_landmarks)
            
            for hand_id, (hand_landmarks, handedness) in enumerate(
                zip(results.multi_hand_landmarks, results.multi_handedness)
            ):
                # Extract handedness (Left/Right)
                hand_label = handedness.classification[0].label
                hand_confidence = handedness.classification[0].score
                
                # Extract normalized landmarks
                landmarks = [
                    (lm.x, lm.y, lm.z)
                    for lm in hand_landmarks.landmark
                ]
                
                # Extract world landmarks if available
                world_landmarks = []
                if results.multi_hand_world_landmarks and self.include_world_landmarks:
                    world_lm = results.multi_hand_world_landmarks[hand_id]
                    world_landmarks = [
                        (lm.x, lm.y, lm.z)
                        for lm in world_lm.landmark
                    ]
                else:
                    # Use normalized landmarks if world landmarks not available
                    world_landmarks = landmarks
                
                # Create HandLandmarks object
                hand_data = HandLandmarks(
                    hand_id=hand_id,
                    handedness=hand_label,
                    landmarks=landmarks,
                    world_landmarks=world_landmarks,
                    confidence=hand_confidence,
                    timestamp=time.time()
                )
                
                detected_hands.append(hand_data)
            
            if self.enable_logging and len(detected_hands) > 0:
                logger.debug(
                    f"Detected {len(detected_hands)} hand(s) in {latency_ms:.1f}ms "
                    f"(FPS: {self.fps:.1f})"
                )
        
        return detected_hands
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current detection statistics.
        
        Returns:
            Dictionary containing:
                - fps: Current frames per second
                - frame_count: Total frames processed
                - detection_count: Total hands detected
                - detection_rate: Percentage of frames with hands detected
                - avg_latency_ms: Average detection latency in milliseconds
                - uptime_seconds: Seconds since initialization
        """
        uptime = time.time() - self.start_time
        detection_rate = (self.detection_count / max(self.frame_count, 1)) * 100
        avg_latency = self.total_latency_ms / max(self.frame_count, 1)
        
        return {
            "fps": self.fps,
            "frame_count": self.frame_count,
            "detection_count": self.detection_count,
            "detection_rate": detection_rate,
            "avg_latency_ms": avg_latency,
            "uptime_seconds": uptime,
            "target_fps": self.target_fps,
            "max_latency_ms": self.max_latency_ms
        }
    
    def reset_statistics(self) -> None:
        """Reset all detection statistics to initial state."""
        self.detection_count = 0
        self.frame_count = 0
        self.last_fps_update = time.time()
        self.fps = 0.0
        self.total_latency_ms = 0.0
        self.start_time = time.time()
        
        logger.info("Detection statistics reset")
    
    def _update_fps(self) -> None:
        """Update FPS calculation based on recent frames."""
        current_time = time.time()
        elapsed = current_time - self.last_fps_update
        
        if elapsed > 0:
            # Calculate FPS based on stats_update_interval frames
            self.fps = self.stats_update_interval / elapsed
            self.last_fps_update = current_time
            
            if self.enable_logging:
                logger.debug(f"FPS updated: {self.fps:.1f}")
    
    def close(self) -> None:
        """Release MediaPipe resources."""
        if hasattr(self, 'hands'):
            self.hands.close()
            logger.info("HandDetector closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
