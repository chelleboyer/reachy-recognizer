"""
Recognition Pipeline Module - Story 2.4

Integrates face detection, encoding, and recognition into a real-time pipeline
that continuously processes camera frames and identifies people.

This module combines all Vision components (Stories 2.1-2.3) into a unified
pipeline that achieves ≥5 FPS real-time recognition.
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Dict, Any, Callable
from pathlib import Path
from collections import deque
import logging

from .camera_interface import CameraInterface
from .face_detector import FaceDetector
from .face_encoder import FaceEncoder
from .face_database import FaceDatabase
from .face_recognizer import FaceRecognizer
from ..events.event_system import EventManager, RecognitionEvent, EventType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import config (optional - falls back to defaults)
try:
    from ..config import get_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False
    logger.warning("Config not available, using default pipeline settings")


class RecognitionPipeline:
    """
    Real-time face recognition pipeline.
    
    Integrates camera capture, face detection, encoding, and recognition
    into a continuous processing loop with performance monitoring.
    
    Attributes:
        camera: CameraInterface for frame capture
        detector: FaceDetector for finding faces
        encoder: FaceEncoder for generating face embeddings
        database: FaceDatabase with known faces
        recognizer: FaceRecognizer for matching faces
        frame_count: Total frames processed
        fps: Current frames per second
        last_results: Most recent recognition results
    """
    
    def __init__(
        self,
        camera: Optional[CameraInterface] = None,
        detector: Optional[FaceDetector] = None,
        encoder: Optional[FaceEncoder] = None,
        database: Optional[FaceDatabase] = None,
        recognizer: Optional[FaceRecognizer] = None,
        recognition_threshold: Optional[float] = None,
        process_every_n_frames: Optional[int] = None,
        enable_events: Optional[bool] = None,
        event_debounce_frames: Optional[int] = None,
        event_departed_frames: Optional[int] = None
    ):
        """
        Initialize recognition pipeline.
        
        Args:
            camera: CameraInterface instance (creates new if None)
            detector: FaceDetector instance (creates new if None)
            encoder: FaceEncoder instance (creates new if None)
            database: FaceDatabase instance (creates new if None)
            recognizer: FaceRecognizer instance (creates new if None)
            recognition_threshold: Similarity threshold (default from config or 0.6)
            process_every_n_frames: Process every Nth frame (default from config or 1)
            enable_events: Enable event system (default from config or False)
            event_debounce_frames: Frames before event trigger (default from config or 3)
            event_departed_frames: Absent frames before DEPARTED (default from config or 3)
            
        Example:
            >>> pipeline = RecognitionPipeline(enable_events=True)
            >>> pipeline.load_database("faces.json")
            >>> results = pipeline.process_frame(frame)
            >>> events = pipeline.get_recent_events()
        """
        # Load from config if available
        if _CONFIG_AVAILABLE:
            try:
                config = get_config()
                if recognition_threshold is None:
                    recognition_threshold = config.face_recognition.threshold
                if process_every_n_frames is None:
                    process_every_n_frames = config.performance.process_every_n_frames
                if enable_events is None:
                    enable_events = False  # Default to False
                if event_debounce_frames is None:
                    event_debounce_frames = int(config.events.debounce_seconds * config.camera.fps)
                if event_departed_frames is None:
                    event_departed_frames = int(config.events.departed_threshold_seconds * config.camera.fps)
                logger.info("Loaded pipeline settings from config")
            except Exception as e:
                logger.warning(f"Failed to load pipeline config: {e}")
        
        # Use defaults if still None
        if recognition_threshold is None:
            recognition_threshold = 0.6
        if process_every_n_frames is None:
            process_every_n_frames = 1
        if enable_events is None:
            enable_events = False
        if event_debounce_frames is None:
            event_debounce_frames = 3
        if event_departed_frames is None:
            event_departed_frames = 3
        
        # Initialize components
        self.camera = camera if camera is not None else CameraInterface()
        self.detector = detector if detector is not None else FaceDetector()
        self.encoder = encoder if encoder is not None else FaceEncoder()
        self.database = database if database is not None else FaceDatabase(
            encoder=self.encoder,
            detector=self.detector
        )
        self.recognizer = recognizer if recognizer is not None else FaceRecognizer(
            database=self.database,
            threshold=recognition_threshold
        )
        
        # Event system (Story 2.5)
        self.enable_events = enable_events
        if enable_events:
            self.event_manager = EventManager(
                debounce_frames=event_debounce_frames,
                departed_frames=event_departed_frames
            )
            logger.info(f"Event system enabled (debounce={event_debounce_frames}, departed={event_departed_frames})")
        else:
            self.event_manager = None
        
        # Pipeline configuration
        self.process_every_n_frames = max(1, process_every_n_frames)
        
        # Performance tracking
        self.frame_count = 0
        self.processed_frame_count = 0
        self.fps = 0.0
        self.processing_time_ms = 0.0
        self.last_fps_update = time.time()
        self.fps_frame_count = 0
        
        # Performance metrics (Story 4.2)
        self.metrics = {
            'frames_processed': 0,
            'total_recognition_time': 0.0,
            'recognition_times': deque(maxlen=100),  # Rolling window of last 100
            'fps_samples': deque(maxlen=30),  # Last 30 FPS measurements
            'confidence_scores': deque(maxlen=100),  # Last 100 confidence scores
        }
        self.start_time = time.time()
        self.last_summary_time = time.time()
        
        # Results tracking
        self.last_results: List[Tuple[str, float, Tuple[int, int, int, int]]] = []
        
        logger.info(f"RecognitionPipeline initialized")
        logger.info(f"  Threshold: {recognition_threshold}")
        logger.info(f"  Process every {process_every_n_frames} frame(s)")
        logger.info(f"  Database: {self.database.size()} known faces")
    
    def load_database(self, filepath: str) -> bool:
        """
        Load face database from file.
        
        Args:
            filepath: Path to database JSON file
            
        Returns:
            True if loaded successfully
        """
        success = self.database.load_database(filepath)
        if success:
            logger.info(f"Loaded database: {self.database.size()} faces")
        return success
    
    def process_frame(
        self,
        frame: np.ndarray,
        force_process: bool = False
    ) -> List[Tuple[str, float, Tuple[int, int, int, int]]]:
        """
        Process a single frame through the recognition pipeline.
        
        Pipeline: detect faces → encode faces → recognize faces → return results
        
        Args:
            frame: Input frame (BGR format)
            force_process: If True, process even if frame should be skipped
            
        Returns:
            List of (name, confidence, bbox) tuples
            bbox is (top, right, bottom, left)
            Returns empty list if no faces detected
            
        Example:
            >>> results = pipeline.process_frame(frame)
            >>> for name, conf, (t, r, b, l) in results:
            >>>     print(f"{name}: {conf:.2f} at ({l},{t})-({r},{b})")
        """
        self.frame_count += 1
        
        # Frame skipping for performance
        if not force_process and self.frame_count % self.process_every_n_frames != 0:
            return self.last_results
        
        start_time = time.time()
        
        # Increment processed frame count
        self.processed_frame_count += 1
        
        # Step 1: Detect faces
        face_locations = self.detector.detect_faces(frame)
        
        if len(face_locations) == 0:
            self.last_results = []
            self._update_performance_metrics(start_time, [])
            return []
        
        # Step 2: Extract and encode faces
        encodings = []
        for top, right, bottom, left in face_locations:
            # Extract face region
            face_img = frame[top:bottom, left:right]
            
            # Encode face
            encoding = self.encoder.encode_face(face_img, normalize=True)
            if encoding is not None:
                encodings.append(encoding)
            else:
                # Encoding failed, use zero vector as placeholder
                encodings.append(np.zeros(128, dtype=np.float32))
        
        # Step 3: Recognize all faces (vectorized for performance)
        recognition_results = self.recognizer.recognize_faces_vectorized(encodings)
        
        # Step 4: Combine results
        results = []
        for (name, confidence), bbox in zip(recognition_results, face_locations):
            results.append((name, confidence, bbox))
        
        self.last_results = results
        
        # Generate events if event system enabled (Story 2.5)
        if self.event_manager is not None:
            self.event_manager.process_recognition_results(results, frame_number=self.frame_count)
        
        # Update performance metrics
        self._update_performance_metrics(start_time, results)
        
        # Print periodic performance summary (Story 4.2)
        if time.time() - self.last_summary_time >= 60:
            self._print_performance_summary()
            self.last_summary_time = time.time()
        
        # Log recognition events
        if results:
            logger.debug(
                f"Frame {self.frame_count}: {len(results)} face(s), "
                f"{self.processing_time_ms:.1f}ms, {self.fps:.1f} FPS"
            )
            for name, conf, _ in results:
                logger.debug(f"  - {name}: {conf:.3f}")
        
        return results
    
    def _update_performance_metrics(self, start_time: float, results: Optional[List] = None):
        """
        Update FPS and processing time metrics (Story 4.2).
        
        Args:
            start_time: Processing start timestamp
            results: Recognition results (for confidence tracking)
        """
        # Processing time for this frame
        self.processing_time_ms = (time.time() - start_time) * 1000
        
        # Story 4.2: Track metrics
        self.metrics['frames_processed'] += 1
        self.metrics['total_recognition_time'] += self.processing_time_ms
        self.metrics['recognition_times'].append(self.processing_time_ms)
        
        # Track confidence scores
        if results:
            for name, confidence, _ in results:
                self.metrics['confidence_scores'].append(confidence)
        
        # FPS calculation (update every second)
        self.fps_frame_count += 1
        elapsed = time.time() - self.last_fps_update
        if elapsed >= 1.0:
            self.fps = self.fps_frame_count / elapsed
            self.metrics['fps_samples'].append(self.fps)
            self.fps_frame_count = 0
            self.last_fps_update = time.time()
    
    def _print_performance_summary(self):
        """Print performance metrics summary every 60 seconds (Story 4.2)."""
        # Calculate averages
        avg_recognition_time = (
            sum(self.metrics['recognition_times']) / 
            len(self.metrics['recognition_times'])
            if self.metrics['recognition_times'] else 0
        )
        
        avg_fps = (
            sum(self.metrics['fps_samples']) / 
            len(self.metrics['fps_samples'])
            if self.metrics['fps_samples'] else 0
        )
        
        avg_confidence = (
            sum(self.metrics['confidence_scores']) / 
            len(self.metrics['confidence_scores'])
            if self.metrics['confidence_scores'] else 0
        )
        
        uptime = time.time() - self.start_time
        
        # Log structured metrics
        logger.info(
            "Performance Summary",
            extra={
                'event': 'performance_summary',
                'metrics': {
                    'avg_recognition_time_ms': round(avg_recognition_time, 2),
                    'avg_fps': round(avg_fps, 2),
                    'avg_confidence': round(avg_confidence, 3),
                    'frames_processed': self.metrics['frames_processed'],
                    'uptime_seconds': round(uptime, 1)
                }
            }
        )
        
        # Print human-readable summary
        print(f"\n{'='*70}")
        print(f"  Performance Summary (60s interval)")
        print(f"{'='*70}")
        print(f"  Avg Recognition Time: {avg_recognition_time:.2f} ms")
        print(f"  Avg FPS: {avg_fps:.2f}")
        print(f"  Avg Confidence: {avg_confidence:.3f}")
        print(f"  Frames Processed: {self.metrics['frames_processed']}")
        print(f"  Uptime: {uptime:.1f}s")
        print(f"{'='*70}\n")
    
    def draw_results(
        self,
        frame: np.ndarray,
        results: Optional[List[Tuple[str, float, Tuple[int, int, int, int]]]] = None,
        show_fps: bool = True
    ) -> np.ndarray:
        """
        Draw recognition results on frame.
        
        Args:
            frame: Input frame to draw on (will be copied)
            results: Recognition results (uses last_results if None)
            show_fps: If True, display FPS counter
            
        Returns:
            Frame with visual overlays
            
        Example:
            >>> results = pipeline.process_frame(frame)
            >>> annotated = pipeline.draw_results(frame, results)
            >>> cv2.imshow("Recognition", annotated)
        """
        # Copy frame to avoid modifying original
        output = frame.copy()
        
        # Use last results if not provided
        if results is None:
            results = self.last_results
        
        # Draw bounding boxes and labels
        for name, confidence, (top, right, bottom, left) in results:
            # Choose color based on recognition
            if name == "unknown":
                color = (0, 0, 255)  # Red for unknown
                label_color = (255, 255, 255)  # White text
            else:
                color = (0, 255, 0)  # Green for recognized
                label_color = (0, 0, 0)  # Black text
            
            # Draw bounding box
            cv2.rectangle(output, (left, top), (right, bottom), color, 2)
            
            # Draw label background
            label = f"{name}"
            conf_label = f"{confidence:.2f}"
            
            # Calculate label size
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.6
            thickness = 2
            (label_w, label_h), _ = cv2.getTextSize(label, font, font_scale, thickness)
            (conf_w, conf_h), _ = cv2.getTextSize(conf_label, font, font_scale - 0.1, thickness)
            
            # Draw label background rectangle
            label_top = max(top - label_h - conf_h - 10, 0)
            cv2.rectangle(
                output,
                (left, label_top),
                (left + max(label_w, conf_w) + 10, top),
                color,
                -1
            )
            
            # Draw name label
            cv2.putText(
                output,
                label,
                (left + 5, label_top + label_h + 5),
                font,
                font_scale,
                label_color,
                thickness
            )
            
            # Draw confidence label
            cv2.putText(
                output,
                conf_label,
                (left + 5, label_top + label_h + conf_h + 10),
                font,
                font_scale - 0.1,
                label_color,
                thickness - 1
            )
        
        # Draw FPS counter
        if show_fps:
            fps_text = f"FPS: {self.fps:.1f}"
            faces_text = f"Faces: {len(results)}"
            time_text = f"Time: {self.processing_time_ms:.1f}ms"
            
            # Draw semi-transparent background
            overlay = output.copy()
            cv2.rectangle(overlay, (10, 10), (300, 90), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, output, 0.4, 0, output)
            
            # Draw text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(output, fps_text, (20, 35), font, 0.7, (0, 255, 0), 2)
            cv2.putText(output, faces_text, (20, 60), font, 0.7, (0, 255, 0), 2)
            cv2.putText(output, time_text, (20, 85), font, 0.5, (0, 255, 0), 1)
        
        return output
    
    # Event System Methods (Story 2.5)
    
    def add_event_callback(
        self,
        event_type: EventType,
        callback: Callable[[RecognitionEvent], None]
    ) -> Optional[int]:
        """
        Register a callback for recognition events.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
            
        Returns:
            Callback ID for later removal (or None if events disabled)
            
        Example:
            >>> def greet_person(event: RecognitionEvent):
            >>>     print(f"Hello {event.person_name}!")
            >>> 
            >>> callback_id = pipeline.add_event_callback(
            >>>     EventType.PERSON_RECOGNIZED,
            >>>     greet_person
            >>> )
        """
        if self.event_manager is None:
            logger.warning("Event system not enabled - use enable_events=True")
            return None
        
        return self.event_manager.add_callback(event_type, callback)
    
    def remove_event_callback(self, callback_id: int) -> bool:
        """
        Remove an event callback.
        
        Args:
            callback_id: ID returned from add_event_callback()
            
        Returns:
            True if removed successfully
        """
        if self.event_manager is None:
            return False
        
        return self.event_manager.remove_callback(callback_id)
    
    def get_recent_events(self, limit: Optional[int] = None) -> List[RecognitionEvent]:
        """
        Get recent recognition events.
        
        Args:
            limit: Max events to return (None = all)
            
        Returns:
            List of recent events (most recent first)
        """
        if self.event_manager is None:
            return []
        
        return self.event_manager.get_recent_events(limit)
    
    def get_event_stats(self) -> Dict[str, Any]:
        """
        Get event system statistics.
        
        Returns:
            Dictionary with event statistics
        """
        if self.event_manager is None:
            return {}
        
        return self.event_manager.get_stats()
    
    def run_live(
        self,
        show_overlay: bool = True,
        window_name: str = "Face Recognition"
    ):
        """
        Run live recognition from camera with display.
        
        Args:
            show_overlay: If True, show visual overlay
            window_name: Name of display window
            
        Controls:
            'q' - Quit
            's' - Save snapshot
            'd' - Toggle debug overlay
            ' ' - Pause/resume
            
        Example:
            >>> pipeline = RecognitionPipeline()
            >>> pipeline.load_database("faces.json")
            >>> pipeline.run_live()
        """
        logger.info(f"Starting live recognition...")
        logger.info(f"Controls: 'q'=quit, 's'=snapshot, 'd'=toggle debug, space=pause")
        
        debug_overlay = show_overlay
        paused = False
        snapshot_count = 0
        
        try:
            while True:
                # Capture frame
                ret, frame = self.camera.read_frame()
                if not ret:
                    logger.error("Failed to read frame from camera")
                    break
                
                # Process frame (unless paused)
                if not paused:
                    results = self.process_frame(frame)
                else:
                    results = self.last_results
                
                # Draw overlay if enabled
                if debug_overlay:
                    display_frame = self.draw_results(frame, results)
                else:
                    display_frame = frame
                
                # Display frame
                cv2.imshow(window_name, display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    logger.info("Quit requested")
                    break
                elif key == ord('s'):
                    # Save snapshot
                    snapshot_count += 1
                    filename = f"snapshot_{snapshot_count:03d}.jpg"
                    cv2.imwrite(filename, display_frame)
                    logger.info(f"Saved snapshot: {filename}")
                elif key == ord('d'):
                    # Toggle debug overlay
                    debug_overlay = not debug_overlay
                    logger.info(f"Debug overlay: {'ON' if debug_overlay else 'OFF'}")
                elif key == ord(' '):
                    # Pause/resume
                    paused = not paused
                    logger.info(f"{'PAUSED' if paused else 'RESUMED'}")
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        finally:
            # Cleanup
            cv2.destroyAllWindows()
            logger.info(f"Processed {self.processed_frame_count} frames")
            logger.info(f"Average FPS: {self.fps:.1f}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "frame_count": self.frame_count,
            "processed_frame_count": self.processed_frame_count,
            "fps": self.fps,
            "processing_time_ms": self.processing_time_ms,
            "database_size": self.database.size(),
            "last_results_count": len(self.last_results),
            "process_every_n_frames": self.process_every_n_frames
        }


def main():
    """Demo script showing RecognitionPipeline usage."""
    print("=" * 60)
    print("Real-Time Face Recognition Pipeline - Story 2.4")
    print("=" * 60)
    
    # Create pipeline
    pipeline = RecognitionPipeline(
        recognition_threshold=0.6,
        process_every_n_frames=1  # Process every frame
    )
    
    # Load database
    db_path = Path("faces.json")
    if db_path.exists():
        pipeline.load_database(str(db_path))
        print(f"\n✓ Loaded {pipeline.database.size()} known faces")
    else:
        print(f"\n⚠ No database found at {db_path}")
        print("  Run face_database.py to create one first")
        print("  Continuing with empty database (all faces will be 'unknown')")
    
    # Print statistics
    print(f"\nPipeline Configuration:")
    print(f"  Recognition threshold: {pipeline.recognizer.get_threshold()}")
    print(f"  Process every N frames: {pipeline.process_every_n_frames}")
    print(f"  Known faces: {pipeline.database.size()}")
    
    # Run live recognition
    print(f"\nStarting live recognition...")
    print(f"Controls:")
    print(f"  'q' - Quit")
    print(f"  's' - Save snapshot")
    print(f"  'd' - Toggle debug overlay")
    print(f"  ' ' - Pause/resume")
    print("=" * 60)
    
    pipeline.run_live()
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("Session Statistics:")
    print("=" * 60)
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n✓ Recognition pipeline demo complete!")


if __name__ == "__main__":
    main()
