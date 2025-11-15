"""
Person Detection with Torso ROI Extraction - Story 2.1

Detects people in camera frames using YOLOv8n and extracts torso regions
for uniform pattern analysis. Privacy-first: no face detection.
"""

import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional, Tuple
import uuid

import cv2
import numpy as np
import yaml

try:
    from ultralytics import YOLO  # type: ignore
except ImportError:
    YOLO = None  # Will be None in test environments without ultralytics


@dataclass
class TorsoROI:
    """Extracted torso region of interest from person detection."""
    
    person_bbox: Tuple[int, int, int, int]  # x, y, width, height (full person)
    torso_bbox: Tuple[int, int, int, int]  # x, y, width, height (torso only)
    torso_image: np.ndarray  # (224, 224, 3) preprocessed ROI
    confidence: float  # Detection confidence (0-1)
    person_id: str  # Unique ID for this detection
    frame_id: str  # Source frame identifier
    
    def to_dict(self) -> dict:
        """Serialize to dictionary for logging (exclude large arrays)."""
        return {
            'person_bbox': self.person_bbox,
            'torso_bbox': self.torso_bbox,
            'torso_image_shape': self.torso_image.shape,
            'confidence': self.confidence,
            'person_id': self.person_id,
            'frame_id': self.frame_id
        }


class PersonDetector:
    """Detect people and extract torso ROIs for uniform analysis."""
    
    def __init__(self, config_path: str = "src/config/person_detection.yaml"):
        """
        Initialize detector with YOLOv8n model.
        
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
        
        if 'person_detection' not in config:
            raise ValueError("Config missing 'person_detection' section")
        
        pd_config = config['person_detection']
        
        # Load model configuration
        model_cfg = pd_config.get('model', {})
        self.model_name = model_cfg.get('name', 'yolov8n')
        self.confidence_threshold = model_cfg.get('confidence_threshold', 0.7)
        self.iou_threshold = model_cfg.get('iou_threshold', 0.5)
        self.device = model_cfg.get('device', 'cpu')
        
        # Load torso extraction parameters
        torso_cfg = pd_config.get('torso_extraction', {})
        self.vertical_range = torso_cfg.get('vertical_range', [0.0, 0.6])
        self.horizontal_center = torso_cfg.get('horizontal_center', True)
        self.min_width = torso_cfg.get('min_width', 50)
        self.min_height = torso_cfg.get('min_height', 80)
        
        # Load preprocessing parameters
        preproc_cfg = pd_config.get('preprocessing', {})
        self.resize_size = tuple(preproc_cfg.get('resize_size', [224, 224]))
        self.normalization = preproc_cfg.get('normalization', 'standard')
        self.interpolation = preproc_cfg.get('interpolation', 'bilinear')
        
        # Performance settings
        perf_cfg = pd_config.get('performance', {})
        self.max_detections = perf_cfg.get('max_detections', 10)
        
        # Statistics
        self.detection_count = 0
        self.total_confidence = 0.0
        
        # Load YOLO model
        self.model = self._load_yolo_model()
    
    def _load_yolo_model(self):
        """Load YOLOv8n model."""
        if YOLO is None:
            raise ImportError(
                "ultralytics package not found. "
                "Install with: pip install ultralytics>=8.0.0"
            )
        
        # Load YOLOv8n model (will download if not cached)
        model = YOLO(f'{self.model_name}.pt')
        model.to(self.device)
        
        return model
    
    def detect_people(
        self, 
        frame: np.ndarray, 
        frame_id: str
    ) -> List[TorsoROI]:
        """
        Detect people in frame and extract torso ROIs.
        
        Args:
            frame: Input RGB image (H, W, 3)
            frame_id: Unique frame identifier
            
        Returns:
            List of TorsoROI objects, one per detected person
            
        Raises:
            ValueError: If frame is None or empty
        """
        if frame is None or frame.size == 0:
            raise ValueError("Frame is None or empty")
        
        # Run YOLO detection
        results = self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            classes=[0],  # Class 0 = person in COCO dataset
            verbose=False
        )
        
        torso_rois = []
        
        # Process each detection
        for result in results:
            boxes = result.boxes
            
            if boxes is None or len(boxes) == 0:
                continue
            
            for box in boxes[:self.max_detections]:
                # Extract bbox coordinates and confidence
                # Handle both PyTorch tensors and numpy arrays (for testing)
                xyxy = box.xyxy[0]
                conf = box.conf[0]
                
                if hasattr(xyxy, 'cpu'):
                    # PyTorch tensor from real YOLO
                    x1, y1, x2, y2 = xyxy.cpu().numpy()
                    confidence = float(conf.cpu().numpy())
                else:
                    # Numpy array from mock
                    x1, y1, x2, y2 = xyxy
                    confidence = float(conf.item() if hasattr(conf, 'item') else conf)
                
                # Convert to (x, y, width, height)
                person_bbox = (
                    int(x1),
                    int(y1),
                    int(x2 - x1),
                    int(y2 - y1)
                )
                
                # Generate unique person ID
                person_id = f"person_{uuid.uuid4().hex[:8]}"
                
                # Extract torso ROI
                torso_roi = self._extract_torso_roi(
                    frame,
                    person_bbox,
                    confidence,
                    person_id,
                    frame_id
                )
                
                if torso_roi is not None:
                    torso_rois.append(torso_roi)
                    self.detection_count += 1
                    self.total_confidence += confidence
        
        return torso_rois
    
    def _extract_torso_roi(
        self,
        frame: np.ndarray,
        person_bbox: Tuple[int, int, int, int],
        confidence: float,
        person_id: str,
        frame_id: str
    ) -> Optional[TorsoROI]:
        """
        Extract and preprocess torso region from person bbox.
        
        Args:
            frame: Full frame image
            person_bbox: (x, y, width, height) of person
            confidence: Detection confidence
            person_id: Unique person identifier
            frame_id: Frame identifier
            
        Returns:
            TorsoROI object or None if invalid
        """
        x, y, w, h = person_bbox
        
        # Calculate torso bbox (top 60% of person by default)
        torso_height = int(h * (self.vertical_range[1] - self.vertical_range[0]))
        torso_y = y + int(h * self.vertical_range[0])
        
        # Center horizontally if configured
        if self.horizontal_center:
            torso_x = x
            torso_width = w
        else:
            torso_x = x
            torso_width = w
        
        # Validate torso dimensions
        if torso_width < self.min_width or torso_height < self.min_height:
            return None
        
        # Clip to frame boundaries
        frame_h, frame_w = frame.shape[:2]
        torso_x = max(0, min(torso_x, frame_w - 1))
        torso_y = max(0, min(torso_y, frame_h - 1))
        torso_width = min(torso_width, frame_w - torso_x)
        torso_height = min(torso_height, frame_h - torso_y)
        
        # Extract torso region
        try:
            torso_region = frame[
                torso_y:torso_y + torso_height,
                torso_x:torso_x + torso_width
            ]
        except Exception:
            return None
        
        if torso_region.size == 0:
            return None
        
        # Preprocess ROI
        torso_image = self._preprocess_roi(torso_region)
        
        torso_bbox = (torso_x, torso_y, torso_width, torso_height)
        
        return TorsoROI(
            person_bbox=person_bbox,
            torso_bbox=torso_bbox,
            torso_image=torso_image,
            confidence=confidence,
            person_id=person_id,
            frame_id=frame_id
        )
    
    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        Resize and normalize ROI.
        
        Args:
            roi: Raw torso region (H, W, 3)
            
        Returns:
            Preprocessed torso image (224, 224, 3)
        """
        # Select interpolation method
        if self.interpolation == 'bilinear':
            interp = cv2.INTER_LINEAR
        elif self.interpolation == 'nearest':
            interp = cv2.INTER_NEAREST
        elif self.interpolation == 'cubic':
            interp = cv2.INTER_CUBIC
        else:
            interp = cv2.INTER_LINEAR
        
        # Resize to target size
        resized = cv2.resize(roi, self.resize_size, interpolation=interp)
        
        # Normalize pixel values
        if self.normalization == 'standard':
            # Normalize to [0, 1]
            normalized = resized.astype(np.float32) / 255.0
        elif self.normalization == 'imagenet':
            # Normalize to [-1, 1] (ImageNet style)
            normalized = (resized.astype(np.float32) / 127.5) - 1.0
        else:
            # No normalization
            normalized = resized.astype(np.float32)
        
        return normalized
    
    def get_statistics(self) -> dict:
        """Return detection statistics."""
        avg_conf = (
            self.total_confidence / self.detection_count 
            if self.detection_count > 0 
            else 0.0
        )
        
        return {
            'total_detections': self.detection_count,
            'avg_confidence': avg_conf,
            'model_name': self.model_name,
            'confidence_threshold': self.confidence_threshold
        }
    
    def reset_statistics(self):
        """Reset detection counters."""
        self.detection_count = 0
        self.total_confidence = 0.0


def detect_people_quick(
    frame: np.ndarray, 
    frame_id: str = "frame_0"
) -> List[TorsoROI]:
    """
    Quick person detection with default config.
    
    Args:
        frame: Input RGB image
        frame_id: Frame identifier
        
    Returns:
        List of TorsoROI objects
    """
    detector = PersonDetector()
    return detector.detect_people(frame, frame_id)
