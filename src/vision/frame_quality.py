"""
Frame Quality Assessment Module

This module implements quality assessment for captured frames, detecting glare
and blur to enable intelligent frame selection for OCR and product detection.

Story: 1.2 - Frame Quality Assessment
Epic: 1 - Multi-Angle Capture System
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import time

import cv2
import numpy as np
import yaml


@dataclass
class QualityMetrics:
    """Quality assessment results for a single frame.
    
    Attributes:
        quality_score: Overall quality score 0-100 (higher is better)
        glare_score: Glare intensity 0-100 (higher means more glare)
        blur_score: Focus sharpness 0-100 (higher is sharper)
        has_glare: True if glare_score exceeds threshold
        is_blurry: True if blur_score is below threshold
        timestamp: When the assessment was performed
        frame_id: Reference identifier for the source frame
        processing_time_ms: Time taken to assess this frame (milliseconds)
    """
    quality_score: float
    glare_score: float
    blur_score: float
    has_glare: bool
    is_blurry: bool
    timestamp: float
    frame_id: str
    processing_time_ms: float
    
    def to_dict(self) -> dict:
        """Convert metrics to dictionary for JSON serialization."""
        return {
            'quality_score': round(self.quality_score, 2),
            'glare_score': round(self.glare_score, 2),
            'blur_score': round(self.blur_score, 2),
            'has_glare': self.has_glare,
            'is_blurry': self.is_blurry,
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'processing_time_ms': round(self.processing_time_ms, 2)
        }


class FrameQualityAssessor:
    """Analyzes frames for glare, blur, and overall quality.
    
    This class implements automated quality assessment to identify the best
    frames for OCR processing. It detects glare (bright spots that obscure
    text) and blur (out-of-focus images) using computer vision techniques.
    
    Usage:
        assessor = FrameQualityAssessor("config/frame_quality.yaml")
        metrics = assessor.assess_frame(frame)
        
        if metrics.quality_score > 70:
            print("High quality frame - good for OCR")
        elif metrics.has_glare:
            print("Frame has glare - try different angle")
        elif metrics.is_blurry:
            print("Frame is blurry - check focus")
    """
    
    def __init__(self, config_path: str):
        """Initialize the quality assessor with configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid or missing required fields
        """
        self.config_path = Path(config_path)
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if 'frame_quality' not in config:
            raise ValueError("Config missing 'frame_quality' section")
        
        fq_config = config['frame_quality']
        
        # Load glare detection parameters
        glare_cfg = fq_config.get('glare_detection', {})
        self.glare_threshold = glare_cfg.get('threshold', 70)
        self.bright_pixel_value = glare_cfg.get('bright_pixel_value', 200)
        self.min_region_size = glare_cfg.get('min_region_size', 0.05)
        
        # Load blur detection parameters
        blur_cfg = fq_config.get('blur_detection', {})
        self.blur_threshold = blur_cfg.get('threshold', 50)
        self.laplacian_kernel_size = blur_cfg.get('laplacian_kernel_size', 3)
        self.variance_min = blur_cfg.get('variance_min', 100)
        self.variance_max = blur_cfg.get('variance_max', 2000)  # For normalization
        
        # Load quality scoring parameters
        quality_cfg = fq_config.get('quality_scoring', {})
        self.glare_weight = quality_cfg.get('glare_weight', 0.5)
        self.blur_weight = quality_cfg.get('blur_weight', 0.5)
        self.low_quality_threshold = quality_cfg.get('low_quality_threshold', 40)
        
        # Load performance parameters
        perf_cfg = fq_config.get('performance', {})
        self.max_processing_time_ms = perf_cfg.get('max_processing_time_ms', 100)
        
        # Statistics tracking
        self.total_assessments = 0
        self.total_processing_time_ms = 0.0
        
    def assess_frame(self, frame: np.ndarray, frame_id: Optional[str] = None) -> QualityMetrics:
        """Analyze a single frame for quality metrics.
        
        This method performs the complete quality assessment pipeline:
        1. Glare detection using brightness analysis
        2. Blur detection using Laplacian variance
        3. Composite quality score calculation
        4. Flag setting based on thresholds
        
        Args:
            frame: Input image in BGR format (OpenCV standard)
            frame_id: Optional identifier for tracking (default: auto-generated)
            
        Returns:
            QualityMetrics object with all assessment results
            
        Raises:
            ValueError: If frame is None, empty, or invalid format
            
        Example:
            >>> frame = cv2.imread('test.jpg')
            >>> metrics = assessor.assess_frame(frame, 'frame_001')
            >>> print(f"Quality: {metrics.quality_score:.1f}")
            Quality: 75.3
        """
        start_time = time.perf_counter()
        
        # Validate input
        if frame is None or frame.size == 0:
            raise ValueError("Frame is None or empty")
        
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            raise ValueError(f"Expected BGR image with 3 channels, got shape {frame.shape}")
        
        # Generate frame ID if not provided
        if frame_id is None:
            frame_id = f"frame_{self.total_assessments:04d}"
        
        # Compute individual quality metrics
        glare_score = self._compute_glare_score(frame)
        blur_score = self._compute_blur_score(frame)
        quality_score = self._compute_quality_score(glare_score, blur_score)
        
        # Determine flags
        has_glare = glare_score > self.glare_threshold
        is_blurry = blur_score < self.blur_threshold
        
        # Calculate processing time
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        
        # Update statistics
        self.total_assessments += 1
        self.total_processing_time_ms += processing_time_ms
        
        # Warn if processing takes too long
        if processing_time_ms > self.max_processing_time_ms:
            print(f"Warning: Frame assessment took {processing_time_ms:.1f}ms "
                  f"(exceeds target of {self.max_processing_time_ms}ms)")
        
        return QualityMetrics(
            quality_score=quality_score,
            glare_score=glare_score,
            blur_score=blur_score,
            has_glare=has_glare,
            is_blurry=is_blurry,
            timestamp=time.time(),
            frame_id=frame_id,
            processing_time_ms=processing_time_ms
        )
    
    def assess_sequence(self, frames: List[tuple]) -> List[QualityMetrics]:
        """Batch assess all frames in a capture sequence.
        
        This is a convenience method for assessing multiple frames from
        a multi-angle capture sequence. It preserves frame metadata and
        provides batch processing.
        
        Args:
            frames: List of (frame, frame_id) tuples or CapturedFrame objects
            
        Returns:
            List of QualityMetrics in same order as input frames
            
        Example:
            >>> from src.vision.multi_angle_capture import CapturedFrame
            >>> captured_frames = [...]  # From multi-angle capture
            >>> frame_tuples = [(f.frame, f.capture_id) for f in captured_frames]
            >>> metrics_list = assessor.assess_sequence(frame_tuples)
        """
        results = []
        
        for item in frames:
            # Handle different input formats
            if hasattr(item, 'frame') and hasattr(item, 'capture_id'):
                # CapturedFrame object
                frame = item.frame  # type: ignore[attr-defined]
                frame_id = item.capture_id  # type: ignore[attr-defined]
            elif isinstance(item, tuple) and len(item) >= 2:
                # (frame, frame_id) tuple
                frame, frame_id = item[0], item[1]
            else:
                # Just a frame array
                frame = item  # type: ignore[assignment]
                frame_id = None
            
            metrics = self.assess_frame(frame, frame_id)  # type: ignore[arg-type]
            results.append(metrics)
        
        return results
    
    def _compute_glare_score(self, frame: np.ndarray) -> float:
        """Detect glare using brightness analysis.
        
        Algorithm:
        1. Convert BGR to grayscale
        2. Find bright regions where pixel value > threshold (default 200)
        3. Calculate percentage of frame covered by bright regions
        4. Apply severity factor based on region size and intensity
        5. Normalize to 0-100 scale (0 = no glare, 100 = severe glare)
        
        Glare is detected by finding areas with abnormally high brightness
        that could obscure text on cigarette packages. The algorithm considers
        both the extent of bright regions and their intensity.
        
        Args:
            frame: Input BGR image
            
        Returns:
            Glare score from 0 (no glare) to 100 (severe glare)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Find bright pixels that could indicate glare
        bright_mask = gray > self.bright_pixel_value
        
        # Calculate percentage of frame with bright pixels
        total_pixels = gray.size
        bright_pixels = np.sum(bright_mask)
        bright_percentage = bright_pixels / total_pixels
        
        # If no significant bright regions, no glare
        if bright_percentage < self.min_region_size:
            return 0.0
        
        # Calculate average intensity of bright regions
        if bright_pixels > 0:
            bright_intensity = float(np.mean(gray[bright_mask]))  # type: ignore[arg-type]
            # Normalize intensity (200-255 range -> 0-1 scale)
            intensity_factor = (bright_intensity - self.bright_pixel_value) / (255 - self.bright_pixel_value)
        else:
            intensity_factor = 0.0
        
        # Combine extent and intensity for glare score
        # More bright pixels = higher score
        # Higher intensity in those pixels = higher score
        extent_score = min(100, bright_percentage * 1000)  # Scale up for sensitivity
        glare_score = extent_score * (0.5 + 0.5 * intensity_factor)
        
        return float(np.clip(glare_score, 0, 100))
    
    def _compute_blur_score(self, frame: np.ndarray) -> float:
        """Detect blur using Laplacian variance method.
        
        Algorithm:
        1. Convert BGR to grayscale
        2. Apply Laplacian operator for edge detection
        3. Calculate variance of Laplacian output
        4. Higher variance indicates sharper edges (less blur)
        5. Normalize to 0-100 scale (0 = severe blur, 100 = sharp focus)
        
        The Laplacian operator detects edges by computing second derivatives.
        Blurry images have weak edges (low variance), while sharp images
        have strong edges (high variance).
        
        Reference: "Blur detection for digital images using wavelet transform"
        Tong et al., 2004
        
        Args:
            frame: Input BGR image
            
        Returns:
            Blur score from 0 (severe blur) to 100 (sharp focus)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Laplacian operator
        # This detects edges by computing second derivative
        laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=self.laplacian_kernel_size)
        
        # Calculate variance of Laplacian
        # Sharp images have high variance (strong edges)
        # Blurry images have low variance (weak edges)
        variance = laplacian.var()
        
        # Normalize to 0-100 scale
        # variance_min (default 100) = very blurry -> score 0
        # variance_max (default 2000) = very sharp -> score 100
        if variance < self.variance_min:
            blur_score = 0.0
        elif variance > self.variance_max:
            blur_score = 100.0
        else:
            # Linear interpolation between min and max
            normalized = (variance - self.variance_min) / (self.variance_max - self.variance_min)
            blur_score = normalized * 100
        
        return float(np.clip(blur_score, 0, 100))
    
    def _compute_quality_score(self, glare_score: float, blur_score: float) -> float:
        """Combine glare and blur metrics into composite quality score.
        
        The quality score represents overall frame usability for OCR:
        - High quality (>80): Excellent for OCR, minimal issues
        - Medium quality (40-80): Usable but may have challenges
        - Low quality (<40): Poor for OCR, should avoid if possible
        
        Formula:
            quality = (100 - glare_score) * glare_weight + blur_score * blur_weight
        
        Where:
        - (100 - glare_score): Inverted glare (lower glare = better quality)
        - blur_score: Direct (higher blur score = better quality)
        - Weights: Configurable balance between glare and blur importance
        
        Args:
            glare_score: Glare intensity 0-100 (higher = worse)
            blur_score: Focus sharpness 0-100 (higher = better)
            
        Returns:
            Composite quality score from 0 (worst) to 100 (best)
        """
        # Invert glare score (high glare = bad quality)
        glare_quality = 100 - glare_score
        
        # Combine with configurable weights
        quality_score = (glare_quality * self.glare_weight + 
                        blur_score * self.blur_weight)
        
        return float(np.clip(quality_score, 0, 100))
    
    def get_statistics(self) -> dict:
        """Get assessment statistics for monitoring and debugging.
        
        Returns:
            Dictionary with processing statistics:
            - total_assessments: Number of frames assessed
            - avg_processing_time_ms: Average time per frame
            - total_processing_time_ms: Cumulative processing time
        """
        avg_time = (self.total_processing_time_ms / self.total_assessments 
                   if self.total_assessments > 0 else 0)
        
        return {
            'total_assessments': self.total_assessments,
            'avg_processing_time_ms': round(avg_time, 2),
            'total_processing_time_ms': round(self.total_processing_time_ms, 2)
        }
    
    def reset_statistics(self):
        """Reset processing statistics counters."""
        self.total_assessments = 0
        self.total_processing_time_ms = 0.0


# Convenience function for quick assessment
def assess_frame_quick(frame: np.ndarray, 
                      config_path: str = "src/config/frame_quality.yaml") -> QualityMetrics:
    """Quick frame assessment with default configuration.
    
    This is a convenience function for one-off assessments. For batch
    processing, create a FrameQualityAssessor instance and reuse it.
    
    Args:
        frame: Input BGR image
        config_path: Path to config file (default: standard location)
        
    Returns:
        QualityMetrics for the frame
    """
    assessor = FrameQualityAssessor(config_path)
    return assessor.assess_frame(frame)
