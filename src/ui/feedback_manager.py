"""
Visual feedback manager for gesture recognition.

Displays animated emoji icons when gestures are detected, providing immediate
visual confirmation to users. Uses non-blocking animations with fade-in, pulse,
and fade-out effects.
"""

import time
import math
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, Tuple, Dict, Any
import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.vision.gesture_recognizer import GestureType, GestureResult


class FeedbackAnimation(Enum):
    """Animation phases for gesture feedback display."""
    FADE_IN = "fade_in"       # 0.0-0.2s: alpha 0→1
    PULSE = "pulse"           # 0.2-0.8s: scale 1.0→1.2→1.0
    FADE_OUT = "fade_out"     # 0.8-1.0s: alpha 1→0
    COMPLETE = "complete"     # Animation finished


@dataclass
class FeedbackState:
    """State of an active feedback animation."""
    gesture_type: GestureType
    icon: str
    animation_phase: FeedbackAnimation
    start_time: float
    elapsed_time: float
    alpha: float              # Transparency 0-1
    scale: float              # Size multiplier
    position: Tuple[int, int] # (x, y) on screen


class FeedbackManager:
    """
    Manages visual feedback for gesture recognition.
    
    Displays animated emoji icons as overlays when gestures are detected.
    Runs animations in a separate thread to avoid blocking the main process.
    
    Features:
    - Non-blocking animations (separate thread)
    - Smooth transitions (fade-in, pulse, fade-out)
    - Configurable icons, colors, and timing
    - Performance tracking (<200ms latency target)
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None,
        headless: bool = False
    ):
        """
        Initialize FeedbackManager.
        
        Args:
            config_path: Path to feedback_ui.yaml configuration file
            config: Direct configuration dictionary (overrides config_path)
            headless: If True, don't render to display (for testing)
        """
        self.headless = headless
        self.config = config if config is not None else self._load_config(config_path)
        
        # Animation settings
        self.total_duration = self.config.get('animation', {}).get('total_duration_seconds', 1.0)
        self.fade_in_duration = self.config.get('animation', {}).get('fade_in_duration', 0.2)
        self.pulse_duration = self.config.get('animation', {}).get('pulse_duration', 0.6)
        self.fade_out_duration = self.config.get('animation', {}).get('fade_out_duration', 0.2)
        
        # Visual settings
        icons_config = self.config.get('icons', {})
        self.icon_map = {
            GestureType.THUMBS_UP: icons_config.get('thumbs_up', '👍'),
            GestureType.WAVE: icons_config.get('wave', '👋'),
            GestureType.PALM_STOP: icons_config.get('palm_stop', '✋'),
        }
        self.icon_size = icons_config.get('size_pixels', 200)
        self.scale_pulse_max = icons_config.get('scale_pulse_max', 1.2)
        
        # Display position
        position_config = self.config.get('position', {})
        self.position_x = position_config.get('x', 'center')
        self.position_y = position_config.get('y', 'center')
        self.offset_x = position_config.get('offset_x', 0)
        self.offset_y = position_config.get('offset_y', -50)
        
        # Colors
        colors_config = self.config.get('colors', {})
        self.icon_color = tuple(colors_config.get('icon_color', [255, 255, 255, 255]))
        self.bg_color = tuple(colors_config.get('background_color', [0, 0, 0, 128]))
        self.bg_enabled = colors_config.get('background_enabled', True)
        self.bg_radius = colors_config.get('background_radius', 120)
        
        # Performance settings
        self.target_latency_ms = self.config.get('target_latency_ms', 200)
        self.frame_rate = self.config.get('frame_rate', 30)
        self.max_queue_size = self.config.get('max_queue_size', 3)
        
        # Animation queue and thread
        self.animation_queue: Queue = Queue(maxsize=self.max_queue_size)
        self.current_state: Optional[FeedbackState] = None
        self.running = False
        self.animation_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'animations_shown': 0,
            'total_latency_ms': 0.0,
            'dropped_frames': 0,
        }
        
        # Emoji cache
        self._emoji_cache: Dict[str, np.ndarray] = {}
        
    def _load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_path is None:
            # Default to config directory
            config_path = Path(__file__).parent.parent / 'config' / 'feedback_ui.yaml'
        
        if not config_path.exists():
            # Return default configuration
            return {
                'animation': {
                    'total_duration_seconds': 1.0,
                    'fade_in_duration': 0.2,
                    'pulse_duration': 0.6,
                    'fade_out_duration': 0.2,
                },
                'icons': {
                    'thumbs_up': '👍',
                    'wave': '👋',
                    'palm_stop': '✋',
                    'size_pixels': 200,
                    'scale_pulse_max': 1.2,
                },
                'position': {
                    'x': 'center',
                    'y': 'center',
                    'offset_x': 0,
                    'offset_y': -50,
                },
                'colors': {
                    'icon_color': [255, 255, 255, 255],
                    'background_color': [0, 0, 0, 128],
                    'background_enabled': True,
                    'background_radius': 120,
                },
                'target_latency_ms': 200,
                'frame_rate': 30,
                'max_queue_size': 3,
            }
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            return config_data.get('feedback_ui', {})
    
    def start(self) -> None:
        """Start the animation thread."""
        if not self.running:
            self.running = True
            self.animation_thread = threading.Thread(
                target=self._animation_loop,
                daemon=True
            )
            self.animation_thread.start()
    
    def stop(self) -> None:
        """Stop the animation thread gracefully."""
        self.running = False
        if self.animation_thread is not None:
            self.animation_thread.join(timeout=2.0)
    
    def cleanup(self) -> None:
        """Release resources."""
        self.stop()
        self._emoji_cache.clear()
    
    def show_gesture_feedback(self, gesture_result: GestureResult) -> None:
        """
        Display visual feedback for a detected gesture.
        
        Args:
            gesture_result: The recognized gesture to display
        """
        start_time = time.time()
        
        # Get icon for gesture
        icon = self._get_icon_for_gesture(gesture_result.gesture_type)
        if icon is None:
            return
        
        # Create initial feedback state
        position = self._calculate_position(640, 480)  # Default frame size
        state = FeedbackState(
            gesture_type=gesture_result.gesture_type,
            icon=icon,
            animation_phase=FeedbackAnimation.FADE_IN,
            start_time=start_time,
            elapsed_time=0.0,
            alpha=0.0,
            scale=0.8,
            position=position
        )
        
        # Add to queue (non-blocking)
        try:
            self.animation_queue.put_nowait(state)
            
            # Track latency
            latency_ms = (time.time() - start_time) * 1000
            with self._lock:
                self.stats['animations_shown'] += 1
                self.stats['total_latency_ms'] += latency_ms
        except:
            # Queue full, drop animation
            with self._lock:
                self.stats['dropped_frames'] += 1
    
    def render_overlay(
        self,
        frame: Optional[np.ndarray] = None,
        width: int = 640,
        height: int = 480
    ) -> Optional[np.ndarray]:
        """
        Render current animation frame as overlay.
        
        Args:
            frame: Base frame to render on (optional)
            width: Frame width if no base frame provided
            height: Frame height if no base frame provided
            
        Returns:
            Rendered frame with overlay, or None if no active animation
        """
        with self._lock:
            state = self.current_state
        
        if state is None or state.animation_phase == FeedbackAnimation.COMPLETE:
            return frame
        
        # Create overlay
        if frame is not None:
            height, width = frame.shape[:2]
            result = frame.copy()
        else:
            result = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Render background circle (optional)
        if self.bg_enabled:
            result = self._draw_background(result, state)
        
        # Render icon
        result = self._draw_icon(result, state)
        
        return result
    
    def _animation_loop(self) -> None:
        """Main animation loop running in separate thread."""
        frame_duration = 1.0 / self.frame_rate
        
        while self.running:
            # Check for new animations in queue
            try:
                new_state = self.animation_queue.get_nowait()
                with self._lock:
                    self.current_state = new_state
            except Empty:
                pass
            
            # Update current animation
            with self._lock:
                if self.current_state is not None:
                    self.current_state.elapsed_time = time.time() - self.current_state.start_time
                    self.current_state = self._update_animation_state(self.current_state)
                    
                    # Remove completed animations
                    if self.current_state.animation_phase == FeedbackAnimation.COMPLETE:
                        self.current_state = None
            
            # Sleep for frame duration
            time.sleep(frame_duration)
    
    def _update_animation_state(self, state: FeedbackState) -> FeedbackState:
        """Update animation state based on elapsed time."""
        elapsed = state.elapsed_time
        
        # Determine phase and update alpha/scale
        if elapsed < self.fade_in_duration:
            # Fade-in phase
            state.animation_phase = FeedbackAnimation.FADE_IN
            state = self._animate_fade_in(state)
        elif elapsed < self.fade_in_duration + self.pulse_duration:
            # Pulse phase
            state.animation_phase = FeedbackAnimation.PULSE
            state = self._animate_pulse(state)
        elif elapsed < self.total_duration:
            # Fade-out phase
            state.animation_phase = FeedbackAnimation.FADE_OUT
            state = self._animate_fade_out(state)
        else:
            # Complete
            state.animation_phase = FeedbackAnimation.COMPLETE
            state.alpha = 0.0
        
        return state
    
    def _animate_fade_in(self, state: FeedbackState) -> FeedbackState:
        """Animate fade-in phase (0.0-0.2s)."""
        t = state.elapsed_time / self.fade_in_duration
        t = min(t, 1.0)
        
        # Linear alpha
        state.alpha = t
        
        # Ease-out scale (cubic)
        scale_t = 1.0 - pow(1.0 - t, 3)
        state.scale = 0.8 + 0.2 * scale_t
        
        return state
    
    def _animate_pulse(self, state: FeedbackState) -> FeedbackState:
        """Animate pulse phase (0.2-0.8s)."""
        t = (state.elapsed_time - self.fade_in_duration) / self.pulse_duration
        t = min(t, 1.0)
        
        # Constant alpha
        state.alpha = 1.0
        
        # Sine wave scale
        scale_offset = (self.scale_pulse_max - 1.0) * math.sin(math.pi * t)
        state.scale = 1.0 + scale_offset
        
        return state
    
    def _animate_fade_out(self, state: FeedbackState) -> FeedbackState:
        """Animate fade-out phase (0.8-1.0s)."""
        t = (state.elapsed_time - self.fade_in_duration - self.pulse_duration) / self.fade_out_duration
        t = min(t, 1.0)
        
        # Linear alpha (reverse)
        state.alpha = 1.0 - t
        
        # Linear scale increase
        state.scale = 1.0 + (self.scale_pulse_max - 1.0) * t
        
        return state
    
    def _get_icon_for_gesture(self, gesture_type: GestureType) -> Optional[str]:
        """Map gesture type to emoji icon."""
        return self.icon_map.get(gesture_type)
    
    def _calculate_position(self, width: int, height: int) -> Tuple[int, int]:
        """Calculate icon position based on configuration."""
        # X position
        if self.position_x == 'center':
            x = width // 2
        elif self.position_x == 'left':
            x = self.icon_size
        elif self.position_x == 'right':
            x = width - self.icon_size
        else:
            x = int(self.position_x)
        
        # Y position
        if self.position_y == 'center':
            y = height // 2
        elif self.position_y == 'top':
            y = self.icon_size
        elif self.position_y == 'bottom':
            y = height - self.icon_size
        else:
            y = int(self.position_y)
        
        # Apply offsets
        x += self.offset_x
        y += self.offset_y
        
        return (x, y)
    
    def _draw_background(self, canvas: np.ndarray, state: FeedbackState) -> np.ndarray:
        """Draw semi-transparent circle behind icon."""
        try:
            import cv2
        except ImportError:
            # cv2 not available, return canvas unchanged
            return canvas
            
        overlay = canvas.copy()
        
        # Calculate radius with scale
        radius = int(self.bg_radius * state.scale)
        
        # Draw filled circle
        center = state.position
        color = self.bg_color[:3]  # RGB only for OpenCV
        
        # Create a separate overlay for alpha blending
        cv2.circle(overlay, center, radius, color, -1)
        
        # Apply alpha based on state alpha and background alpha
        bg_alpha = (self.bg_color[3] / 255.0) * state.alpha
        try:
            canvas = cv2.addWeighted(overlay, bg_alpha, canvas, 1 - bg_alpha, 0)
        except:
            pass
        
        return canvas
    
    def _draw_icon(self, canvas: np.ndarray, state: FeedbackState) -> np.ndarray:
        """Draw emoji icon on canvas."""
        icon = state.icon
        
        # Check cache
        cache_key = f"{icon}_{state.scale:.2f}"
        if cache_key not in self._emoji_cache:
            self._emoji_cache[cache_key] = self._render_emoji(icon, state.scale)
        
        emoji_img = self._emoji_cache[cache_key]
        
        # Apply alpha
        if state.alpha < 1.0:
            emoji_img = emoji_img.copy()
            emoji_img[:, :, 3] = (emoji_img[:, :, 3] * state.alpha).astype(np.uint8)
        
        # Composite onto canvas
        canvas = self._composite_overlay(canvas, emoji_img, state.position)
        
        return canvas
    
    def _render_emoji(self, emoji: str, scale: float) -> np.ndarray:
        """Render emoji character using Pillow."""
        size = int(self.icon_size * scale)
        
        # Create PIL image
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Try to load emoji font
        font = self._get_emoji_font(size)
        
        if font is not None:
            # Draw emoji centered
            bbox = draw.textbbox((0, 0), emoji, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((size - text_width) // 2 - bbox[0], (size - text_height) // 2 - bbox[1])
            draw.text(position, emoji, font=font, fill=self.icon_color, embedded_color=True)
        else:
            # Fallback: draw colored circle with letter
            fallback_map = {
                '👍': ('T', (76, 175, 80)),    # Green
                '👋': ('W', (33, 150, 243)),   # Blue
                '✋': ('P', (244, 67, 54)),     # Red
            }
            letter, color = fallback_map.get(emoji, ('?', (128, 128, 128)))
            
            # Draw circle
            import cv2
            np_img = np.array(img)
            cv2.circle(np_img, (size // 2, size // 2), size // 2 - 5, color + (255,), -1)
            
            # Draw letter (convert back to PIL for text)
            img = Image.fromarray(np_img)
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", size=int(size * 0.6))
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), letter, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((size - text_width) // 2 - bbox[0], (size - text_height) // 2 - bbox[1])
            draw.text(position, letter, font=font, fill=(255, 255, 255, 255))
        
        # Convert to numpy array
        return np.array(img)
    
    def _get_emoji_font(self, size: int) -> Optional[ImageFont.FreeTypeFont]:
        """Get emoji font for rendering (platform-dependent)."""
        font_size = int(size * 0.8)
        
        # Try platform-specific emoji fonts
        font_paths = [
            "C:\\Windows\\Fonts\\seguiemj.ttf",  # Windows: Segoe UI Emoji
            "/System/Library/Fonts/Apple Color Emoji.ttc",  # macOS
            "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",  # Linux
        ]
        
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size=font_size)
            except:
                continue
        
        return None
    
    def _composite_overlay(
        self,
        canvas: np.ndarray,
        overlay: np.ndarray,
        position: Tuple[int, int]
    ) -> np.ndarray:
        """Composite RGBA overlay onto RGB canvas at position."""
        if overlay.shape[2] != 4:
            return canvas
        
        # Calculate overlay region
        h, w = overlay.shape[:2]
        x, y = position
        x1 = max(0, x - w // 2)
        y1 = max(0, y - h // 2)
        x2 = min(canvas.shape[1], x1 + w)
        y2 = min(canvas.shape[0], y1 + h)
        
        # Crop overlay if needed
        overlay_x1 = max(0, w // 2 - x)
        overlay_y1 = max(0, h // 2 - y)
        overlay_x2 = overlay_x1 + (x2 - x1)
        overlay_y2 = overlay_y1 + (y2 - y1)
        
        if x2 <= x1 or y2 <= y1:
            return canvas
        
        overlay_crop = overlay[overlay_y1:overlay_y2, overlay_x1:overlay_x2]
        
        # Alpha blend
        alpha = overlay_crop[:, :, 3:4] / 255.0
        canvas[y1:y2, x1:x2] = (
            canvas[y1:y2, x1:x2] * (1 - alpha) +
            overlay_crop[:, :, :3] * alpha
        ).astype(np.uint8)
        
        return canvas
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics."""
        with self._lock:
            stats = self.stats.copy()
            if stats['animations_shown'] > 0:
                stats['avg_latency_ms'] = stats['total_latency_ms'] / stats['animations_shown']
            else:
                stats['avg_latency_ms'] = 0.0
            return stats
    
    def reset_statistics(self) -> None:
        """Reset statistics."""
        with self._lock:
            self.stats = {
                'animations_shown': 0,
                'total_latency_ms': 0.0,
                'dropped_frames': 0,
            }
