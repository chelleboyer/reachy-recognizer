"""
Best Frame Selection Module

This module implements intelligent frame selection from multi-angle capture sequences
based on quality assessment. It selects the optimal frame(s) for OCR and product
detection, using single best frame or multi-frame fusion strategies.

Story: 1.3 - Best Frame Selection & OCR
Epic: 1 - Multi-Angle Capture System
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
import time

import numpy as np
import yaml


@dataclass
class SelectionResult:
    """Result of best frame selection process.
    
    Attributes:
        strategy: Selection strategy used ("single_best", "multi_frame_fusion", "failure")
        selected_frames: List of frames selected (indices into original sequence)
        fused_frame: If fusion used, the resulting fused frame; otherwise None
        quality_scores: Quality scores of all selected frames
        best_score: Highest quality score in selection
        reason: Human-readable explanation of selection decision
        timestamp: When selection was performed
        processing_time_ms: Time taken to select frames
    """
    strategy: str
    selected_frames: List[int]  # Frame indices
    fused_frame: Optional[np.ndarray]
    quality_scores: List[float]
    best_score: float
    reason: str
    timestamp: float
    processing_time_ms: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'strategy': self.strategy,
            'selected_frame_indices': self.selected_frames,
            'has_fused_frame': self.fused_frame is not None,
            'quality_scores': [round(s, 2) for s in self.quality_scores],
            'best_score': round(self.best_score, 2),
            'reason': self.reason,
            'timestamp': self.timestamp,
            'processing_time_ms': round(self.processing_time_ms, 2)
        }


class NoGoodFramesError(Exception):
    """Raised when all frames in sequence have quality below minimum threshold."""
    pass


class BestFrameSelector:
    """Selects optimal frame(s) from quality-assessed sequence for OCR/detection.
    
    This class implements intelligent frame selection using three strategies:
    1. Single Best: If any frame has quality >80, use the highest-scoring frame
    2. Multi-Frame Fusion: If multiple frames score 60-80, fuse top 2-3 frames
    3. Failure: If all frames score <60, raise error (don't process bad frames)
    
    Usage:
        selector = BestFrameSelector("config/frame_selection.yaml")
        result = selector.select_best_frames(captured_frames, quality_metrics)
        
        if result.strategy == "single_best":
            best_idx = result.selected_frames[0]
            frame_to_process = captured_frames[best_idx].frame
        elif result.strategy == "multi_frame_fusion":
            frame_to_process = result.fused_frame
        else:
            # Handle failure case
            print(f"No good frames: {result.reason}")
    """
    
    def __init__(self, config_path: str):
        """Initialize the frame selector with configuration.
        
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
        
        if 'frame_selector' not in config:
            raise ValueError("Config missing 'frame_selector' section")
        
        selector_cfg = config['frame_selector']
        
        # Load threshold parameters
        thresholds = selector_cfg.get('thresholds', {})
        self.excellent_quality = thresholds.get('excellent_quality', 80)
        self.acceptable_quality = thresholds.get('acceptable_quality', 60)
        self.minimum_quality = thresholds.get('minimum_quality', 60)
        
        # Load fusion parameters
        fusion_cfg = selector_cfg.get('fusion', {})
        self.max_frames_to_fuse = fusion_cfg.get('max_frames_to_fuse', 3)
        self.weight_by_quality = fusion_cfg.get('weight_by_quality', True)
        self.normalization = fusion_cfg.get('normalization', 'softmax')
        
        # Load failure handling parameters
        failure_cfg = selector_cfg.get('failure_handling', {})
        self.log_all_scores = failure_cfg.get('log_all_scores', True)
        self.send_alert = failure_cfg.get('send_alert', False)
        self.fallback_to_best = failure_cfg.get('fallback_to_best', False)
        
        # Statistics
        self.total_selections = 0
        self.strategy_counts = {
            'single_best': 0,
            'multi_frame_fusion': 0,
            'failure': 0
        }
    
    def select_best_frames(
        self,
        frames: List,  # List of CapturedFrame objects or frame arrays
        quality_metrics: List  # List of QualityMetrics objects
    ) -> SelectionResult:
        """Select best frame(s) for OCR based on quality scores.
        
        This is the main entry point for frame selection. It analyzes quality
        metrics and chooses the optimal strategy:
        - Single best if excellent quality exists (>80)
        - Multi-frame fusion if multiple acceptable frames (60-80)
        - Failure if all frames are poor quality (<60)
        
        Args:
            frames: Captured frames (CapturedFrame objects or arrays)
            quality_metrics: Quality assessments (QualityMetrics objects)
            
        Returns:
            SelectionResult with selected frame(s) and strategy used
            
        Raises:
            NoGoodFramesError: If all frames below quality threshold and
                              fallback_to_best is False
            ValueError: If frames and metrics lists have different lengths
            
        Example:
            >>> frames = await capture_controller.capture_sequence()
            >>> metrics = quality_assessor.assess_sequence(frames)
            >>> result = selector.select_best_frames(frames, metrics)
            >>> print(f"Strategy: {result.strategy}, Best score: {result.best_score}")
            Strategy: single_best, Best score: 85.3
        """
        start_time = time.perf_counter()
        
        # Validate inputs
        if len(frames) != len(quality_metrics):
            raise ValueError(
                f"Frame count ({len(frames)}) doesn't match "
                f"quality metrics count ({len(quality_metrics)})"
            )
        
        if len(frames) == 0:
            raise ValueError("Cannot select from empty frame list")
        
        # Extract quality scores
        scores = [m.quality_score for m in quality_metrics]
        max_score = max(scores)
        
        # Determine strategy based on quality scores
        if max_score >= self.excellent_quality:
            # Strategy 1: Single best frame
            result = self._select_single_best(frames, quality_metrics, scores)
            self.strategy_counts['single_best'] += 1
            
        elif max_score >= self.acceptable_quality:
            # Strategy 2: Multi-frame fusion
            result = self._fuse_multiple_frames(frames, quality_metrics, scores)
            self.strategy_counts['multi_frame_fusion'] += 1
            
        else:
            # Strategy 3: Failure (all frames poor quality)
            if self.fallback_to_best:
                # Fallback: use best available despite low quality
                result = self._select_single_best(frames, quality_metrics, scores)
                result.reason += " (FALLBACK - quality below threshold)"
                self.strategy_counts['failure'] += 1
            else:
                result = self._handle_failure(quality_metrics, scores)
                self.strategy_counts['failure'] += 1
                raise NoGoodFramesError(result.reason)
        
        # Calculate processing time
        end_time = time.perf_counter()
        result.processing_time_ms = (end_time - start_time) * 1000
        result.timestamp = time.time()
        
        # Update statistics
        self.total_selections += 1
        
        return result
    
    def _select_single_best(
        self,
        frames: List,
        metrics: List,
        scores: List[float]
    ) -> SelectionResult:
        """Select single highest-quality frame.
        
        Used when at least one frame has excellent quality (>80).
        Simply selects the frame with the highest quality score.
        
        Args:
            frames: List of captured frames
            metrics: List of quality metrics
            scores: Pre-extracted quality scores for efficiency
            
        Returns:
            SelectionResult with single frame selected
        """
        # Find index of highest quality score
        best_idx = scores.index(max(scores))
        best_score = scores[best_idx]
        
        reason = (
            f"Selected frame {best_idx} with quality {best_score:.1f} "
            f"(highest score, above excellent threshold {self.excellent_quality})"
        )
        
        return SelectionResult(
            strategy="single_best",
            selected_frames=[best_idx],
            fused_frame=None,
            quality_scores=[best_score],
            best_score=best_score,
            reason=reason,
            timestamp=0.0,  # Will be set by caller
            processing_time_ms=0.0  # Will be set by caller
        )
    
    def _fuse_multiple_frames(
        self,
        frames: List,
        metrics: List,
        scores: List[float]
    ) -> SelectionResult:
        """Fuse top 2-3 frames with weighted average.
        
        Used when multiple frames have acceptable quality (60-80) but no
        single excellent frame. Combines multiple frames to potentially
        create a better result than any individual frame.
        
        Algorithm:
        1. Sort frames by quality score (descending)
        2. Take top N frames (N = min(max_frames_to_fuse, available frames))
        3. Normalize quality scores to weights (softmax or linear)
        4. Compute weighted average: fused[x,y] = Σ(frame_i[x,y] * weight_i)
        5. Clip result to valid pixel range [0, 255]
        
        Args:
            frames: List of captured frames
            metrics: List of quality metrics
            scores: Pre-extracted quality scores
            
        Returns:
            SelectionResult with fused frame
        """
        # Sort frames by quality score (descending)
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        # Take top N frames for fusion
        n_frames = min(self.max_frames_to_fuse, len(frames))
        top_indices = sorted_indices[:n_frames]
        top_scores = [scores[i] for i in top_indices]
        
        # Compute fusion weights from quality scores
        weights = self._compute_fusion_weights(top_scores)
        
        # Extract frame arrays
        frame_arrays = []
        for idx in top_indices:
            frame = frames[idx]
            # Handle both CapturedFrame objects and raw arrays
            if hasattr(frame, 'frame'):
                frame_arrays.append(frame.frame)  # type: ignore[attr-defined]
            else:
                frame_arrays.append(frame)  # type: ignore[arg-type]
        
        # Perform weighted fusion
        fused = self._weighted_average_fusion(frame_arrays, weights)
        
        reason = (
            f"Fused {n_frames} frames (indices {top_indices}) "
            f"with quality scores {[f'{s:.1f}' for s in top_scores]} "
            f"and weights {[f'{w:.3f}' for w in weights]}"
        )
        
        return SelectionResult(
            strategy="multi_frame_fusion",
            selected_frames=top_indices,
            fused_frame=fused,
            quality_scores=top_scores,
            best_score=max(top_scores),
            reason=reason,
            timestamp=0.0,
            processing_time_ms=0.0
        )
    
    def _compute_fusion_weights(self, scores: List[float]) -> List[float]:
        """Compute fusion weights from quality scores.
        
        Args:
            scores: Quality scores for frames to fuse
            
        Returns:
            Normalized weights that sum to 1.0
        """
        if not self.weight_by_quality:
            # Equal weights
            return [1.0 / len(scores)] * len(scores)
        
        if self.normalization == 'softmax':
            # Softmax normalization (emphasizes differences)
            exp_scores = np.exp(np.array(scores) / 10.0)  # Temperature scaling
            weights = exp_scores / np.sum(exp_scores)
            return weights.tolist()
        else:
            # Linear normalization
            total = sum(scores)
            if total == 0:
                return [1.0 / len(scores)] * len(scores)
            return [s / total for s in scores]
    
    def _weighted_average_fusion(
        self,
        frames: List[np.ndarray],
        weights: List[float]
    ) -> np.ndarray:
        """Perform weighted average fusion of multiple frames.
        
        Args:
            frames: List of frame arrays to fuse
            weights: Corresponding weights (must sum to 1.0)
            
        Returns:
            Fused frame as uint8 array
        """
        # Convert frames to float for weighted averaging
        frames_float = [frame.astype(np.float32) for frame in frames]
        
        # Compute weighted average
        fused = np.zeros_like(frames_float[0])
        for frame, weight in zip(frames_float, weights):
            fused += frame * weight
        
        # Clip to valid range and convert back to uint8
        fused = np.clip(fused, 0, 255).astype(np.uint8)
        
        return fused
    
    def _handle_failure(
        self,
        metrics: List,
        scores: List[float]
    ) -> SelectionResult:
        """Handle case where all frames have low quality.
        
        Args:
            metrics: Quality metrics for all frames
            scores: Quality scores for all frames
            
        Returns:
            SelectionResult with failure strategy
        """
        max_score = max(scores) if scores else 0.0
        
        reason = (
            f"All {len(scores)} frames below minimum quality threshold "
            f"({self.minimum_quality}). Best score: {max_score:.1f}"
        )
        
        if self.log_all_scores:
            scores_str = ", ".join([f"{s:.1f}" for s in scores])
            reason += f". All scores: [{scores_str}]"
        
        return SelectionResult(
            strategy="failure",
            selected_frames=[],
            fused_frame=None,
            quality_scores=scores,
            best_score=max_score,
            reason=reason,
            timestamp=0.0,
            processing_time_ms=0.0
        )
    
    def get_statistics(self) -> dict:
        """Get selection statistics for monitoring.
        
        Returns:
            Dictionary with strategy usage counts and percentages
        """
        total = self.total_selections
        if total == 0:
            return {
                'total_selections': 0,
                'strategy_counts': self.strategy_counts.copy(),
                'strategy_percentages': {k: 0.0 for k in self.strategy_counts}
            }
        
        percentages = {
            strategy: (count / total) * 100
            for strategy, count in self.strategy_counts.items()
        }
        
        return {
            'total_selections': total,
            'strategy_counts': self.strategy_counts.copy(),
            'strategy_percentages': percentages
        }
    
    def reset_statistics(self):
        """Reset selection statistics counters."""
        self.total_selections = 0
        self.strategy_counts = {
            'single_best': 0,
            'multi_frame_fusion': 0,
            'failure': 0
        }


# Convenience function for quick selection
def select_best_frame_quick(
    frames: List,
    quality_metrics: List,
    config_path: str = "src/config/frame_selection.yaml"
) -> SelectionResult:
    """Quick frame selection with default configuration.
    
    This is a convenience function for one-off selections. For repeated
    use, create a BestFrameSelector instance and reuse it.
    
    Args:
        frames: Captured frames
        quality_metrics: Quality assessments
        config_path: Path to config file (default: standard location)
        
    Returns:
        SelectionResult for the frames
        
    Raises:
        NoGoodFramesError: If all frames have quality below threshold
    """
    selector = BestFrameSelector(config_path)
    return selector.select_best_frames(frames, quality_metrics)
