"""
OCR Engine Module

This module provides text extraction from frames using OCR (Optical Character Recognition).
Supports EasyOCR and Tesseract engines with preprocessing for improved accuracy.

Story: 1.3 - Best Frame Selection & OCR
Epic: 1 - Multi-Angle Capture System
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import time

import cv2
import numpy as np
import yaml


@dataclass
class Box:
    """Bounding box for detected text region.
    
    Attributes:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Box width in pixels
        height: Box height in pixels
    """
    x: int
    y: int
    width: int
    height: int
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {'x': self.x, 'y': self.y, 'width': self.width, 'height': self.height}


@dataclass
class OCRResult:
    """Result of OCR text extraction.
    
    Attributes:
        detected_text: List of all text strings found
        confidence_scores: Per-text confidence scores (0-1 scale)
        bounding_boxes: Per-text location boxes
        processing_time_ms: Time taken for OCR processing
        frame_id: Reference to source frame
        engine: OCR engine used
    """
    detected_text: List[str]
    confidence_scores: List[float]
    bounding_boxes: List[Box]
    processing_time_ms: float
    frame_id: str
    engine: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'detected_text': self.detected_text,
            'confidence_scores': [round(c, 3) for c in self.confidence_scores],
            'bounding_boxes': [box.to_dict() for box in self.bounding_boxes],
            'processing_time_ms': round(self.processing_time_ms, 2),
            'frame_id': self.frame_id,
            'engine': self.engine,
            'text_count': len(self.detected_text)
        }


class OCREngine:
    """Extract text from frames using OCR.
    
    This class provides a unified interface for different OCR engines
    (EasyOCR, Tesseract) with preprocessing to improve accuracy on
    challenging images like cigarette package labels.
    
    Usage:
        engine = OCREngine(engine="easyocr", config_path="config/frame_selection.yaml")
        result = engine.extract_text(frame, frame_id="frame_001")
        
        for text, confidence in zip(result.detected_text, result.confidence_scores):
            print(f"Detected: '{text}' (confidence: {confidence:.2f})")
    """
    
    def __init__(self, engine: str = "mock", config_path: Optional[str] = None):
        """Initialize OCR engine.
        
        Args:
            engine: OCR engine to use ("easyocr", "tesseract", or "mock")
            config_path: Path to YAML config (optional, will use defaults if not provided)
            
        Raises:
            ValueError: If engine is not supported
        """
        self.engine_name = engine.lower()
        
        if self.engine_name not in ["easyocr", "tesseract", "mock"]:
            raise ValueError(
                f"Unsupported OCR engine: {engine}. "
                "Use 'easyocr', 'tesseract', or 'mock'"
            )
        
        # Load configuration
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            ocr_cfg = config.get('ocr', {})
        else:
            # Default configuration
            ocr_cfg = {}
        
        # Preprocessing parameters
        preproc = ocr_cfg.get('preprocessing', {})
        self.do_grayscale = preproc.get('grayscale', True)
        self.do_contrast = preproc.get('contrast_enhancement', True)
        self.do_denoise = preproc.get('denoise', True)
        self.do_sharpen = preproc.get('sharpen', False)
        
        # CLAHE parameters
        self.clahe_clip = preproc.get('clahe_clip_limit', 2.0)
        self.clahe_tile_size = tuple(preproc.get('clahe_tile_grid_size', [8, 8]))
        
        # Bilateral filter parameters
        self.bilateral_d = preproc.get('bilateral_d', 9)
        self.bilateral_sigma_color = preproc.get('bilateral_sigma_color', 75)
        self.bilateral_sigma_space = preproc.get('bilateral_sigma_space', 75)
        
        # Performance parameters
        perf = ocr_cfg.get('performance', {})
        self.max_time_sec = perf.get('max_processing_time_sec', 3)
        
        # Initialize OCR engine
        self.reader = None
        if self.engine_name == "easyocr":
            self._init_easyocr(ocr_cfg)
        elif self.engine_name == "tesseract":
            self._init_tesseract(ocr_cfg)
        # Mock engine doesn't need initialization
        
        # Statistics
        self.total_extractions = 0
        self.total_processing_time_ms = 0.0
    
    def _init_easyocr(self, config: dict):
        """Initialize EasyOCR reader.
        
        Args:
            config: OCR configuration dictionary
        """
        try:
            import easyocr
            
            languages = config.get('languages', ['en'])
            gpu = config.get('gpu', False)
            
            self.reader = easyocr.Reader(languages, gpu=gpu)
            
        except ImportError:
            raise ImportError(
                "EasyOCR not installed. Install with: pip install easyocr"
            )
    
    def _init_tesseract(self, config: dict):
        """Initialize Tesseract OCR.
        
        Args:
            config: OCR configuration dictionary
        """
        try:
            import pytesseract
            self.reader = pytesseract
            
        except ImportError:
            raise ImportError(
                "pytesseract not installed. Install with: pip install pytesseract"
            )
    
    def extract_text(
        self,
        frame: np.ndarray,
        frame_id: str = "unknown",
        roi: Optional[Box] = None
    ) -> OCRResult:
        """Extract text from frame.
        
        Args:
            frame: Input image in BGR format
            frame_id: Identifier for this frame
            roi: Optional region of interest (crop before OCR)
            
        Returns:
            OCRResult with detected text and metadata
            
        Raises:
            ValueError: If frame is invalid
            TimeoutError: If OCR exceeds max processing time
        """
        start_time = time.perf_counter()
        
        # Validate input
        if frame is None or frame.size == 0:
            raise ValueError("Frame is None or empty")
        
        # Crop to ROI if specified
        if roi:
            frame = frame[roi.y:roi.y+roi.height, roi.x:roi.x+roi.width]
        
        # Preprocess frame
        preprocessed = self._preprocess_frame(frame)
        
        # Run OCR based on engine
        if self.engine_name == "easyocr":
            result = self._run_easyocr(preprocessed, frame_id)
        elif self.engine_name == "tesseract":
            result = self._run_tesseract(preprocessed, frame_id)
        else:  # mock
            result = self._run_mock_ocr(preprocessed, frame_id)
        
        # Calculate processing time
        end_time = time.perf_counter()
        processing_time_ms = (end_time - start_time) * 1000
        result.processing_time_ms = processing_time_ms
        
        # Update statistics
        self.total_extractions += 1
        self.total_processing_time_ms += processing_time_ms
        
        # Check timeout
        if processing_time_ms / 1000 > self.max_time_sec:
            print(f"Warning: OCR took {processing_time_ms/1000:.1f}s "
                  f"(exceeds target of {self.max_time_sec}s)")
        
        return result
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for better OCR accuracy.
        
        Pipeline:
        1. Convert to grayscale (if enabled)
        2. Apply CLAHE for contrast (if enabled)
        3. Denoise with bilateral filter (if enabled)
        4. Sharpen (if enabled)
        
        Args:
            frame: Input BGR image
            
        Returns:
            Preprocessed image
        """
        processed = frame.copy()
        
        # Convert to grayscale
        if self.do_grayscale and len(processed.shape) == 3:
            processed = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        
        # Contrast enhancement with CLAHE
        if self.do_contrast:
            clahe = cv2.createCLAHE(
                clipLimit=self.clahe_clip,
                tileGridSize=self.clahe_tile_size
            )
            if len(processed.shape) == 2:
                processed = clahe.apply(processed)
            else:
                # Apply to each channel
                channels = cv2.split(processed)
                processed = cv2.merge([clahe.apply(ch) for ch in channels])
        
        # Denoise with bilateral filter
        if self.do_denoise:
            processed = cv2.bilateralFilter(
                processed,
                d=self.bilateral_d,
                sigmaColor=self.bilateral_sigma_color,
                sigmaSpace=self.bilateral_sigma_space
            )
        
        # Sharpen (optional)
        if self.do_sharpen:
            # Gaussian blur
            blurred = cv2.GaussianBlur(processed, (0, 0), 1.0)
            # Unsharp mask
            processed = cv2.addWeighted(processed, 1.5, blurred, -0.5, 0)
        
        return processed
    
    def _run_easyocr(self, frame: np.ndarray, frame_id: str) -> OCRResult:
        """Run EasyOCR on preprocessed frame.
        
        Args:
            frame: Preprocessed image
            frame_id: Frame identifier
            
        Returns:
            OCRResult with detected text
        """
        if self.reader is None:
            raise RuntimeError("EasyOCR reader not initialized")
        
        # Run detection and recognition
        results = self.reader.readtext(frame)
        
        # Parse results
        detected_text = []
        confidence_scores = []
        bounding_boxes = []
        
        for detection in results:
            bbox_coords, text, confidence = detection
            
            detected_text.append(text)
            confidence_scores.append(float(confidence))
            
            # Convert bounding box to Box format
            # bbox_coords is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [p[0] for p in bbox_coords]
            y_coords = [p[1] for p in bbox_coords]
            x, y = int(min(x_coords)), int(min(y_coords))
            width = int(max(x_coords) - x)
            height = int(max(y_coords) - y)
            
            bounding_boxes.append(Box(x, y, width, height))
        
        return OCRResult(
            detected_text=detected_text,
            confidence_scores=confidence_scores,
            bounding_boxes=bounding_boxes,
            processing_time_ms=0.0,  # Will be set by caller
            frame_id=frame_id,
            engine="easyocr"
        )
    
    def _run_tesseract(self, frame: np.ndarray, frame_id: str) -> OCRResult:
        """Run Tesseract OCR on preprocessed frame.
        
        Args:
            frame: Preprocessed image
            frame_id: Frame identifier
            
        Returns:
            OCRResult with detected text
        """
        if self.reader is None:
            raise RuntimeError("Tesseract not initialized")
        
        # Run OCR with data
        data = self.reader.image_to_data(frame, output_type=self.reader.Output.DICT)
        
        # Parse results
        detected_text = []
        confidence_scores = []
        bounding_boxes = []
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            if text:  # Only include non-empty text
                conf = float(data['conf'][i]) / 100.0  # Normalize to 0-1
                if conf > 0:  # Only include confident detections
                    detected_text.append(text)
                    confidence_scores.append(conf)
                    
                    box = Box(
                        x=data['left'][i],
                        y=data['top'][i],
                        width=data['width'][i],
                        height=data['height'][i]
                    )
                    bounding_boxes.append(box)
        
        return OCRResult(
            detected_text=detected_text,
            confidence_scores=confidence_scores,
            bounding_boxes=bounding_boxes,
            processing_time_ms=0.0,
            frame_id=frame_id,
            engine="tesseract"
        )
    
    def _run_mock_ocr(self, frame: np.ndarray, frame_id: str) -> OCRResult:
        """Run mock OCR for testing (returns dummy data).
        
        Args:
            frame: Preprocessed image
            frame_id: Frame identifier
            
        Returns:
            OCRResult with mock data
        """
        # Mock data for testing
        detected_text = ["MARLBORO", "RED", "20 CLASS A CIGARETTES"]
        confidence_scores = [0.95, 0.88, 0.92]
        bounding_boxes = [
            Box(100, 50, 200, 40),
            Box(100, 100, 80, 30),
            Box(100, 140, 250, 25)
        ]
        
        return OCRResult(
            detected_text=detected_text,
            confidence_scores=confidence_scores,
            bounding_boxes=bounding_boxes,
            processing_time_ms=0.0,
            frame_id=frame_id,
            engine="mock"
        )
    
    def get_statistics(self) -> dict:
        """Get OCR processing statistics.
        
        Returns:
            Dictionary with extraction counts and timing
        """
        avg_time = (self.total_processing_time_ms / self.total_extractions
                   if self.total_extractions > 0 else 0)
        
        return {
            'total_extractions': self.total_extractions,
            'avg_processing_time_ms': round(avg_time, 2),
            'total_processing_time_ms': round(self.total_processing_time_ms, 2),
            'engine': self.engine_name
        }
    
    def reset_statistics(self):
        """Reset processing statistics counters."""
        self.total_extractions = 0
        self.total_processing_time_ms = 0.0


# Convenience function for quick OCR
def extract_text_quick(
    frame: np.ndarray,
    frame_id: str = "unknown",
    engine: str = "mock",
    config_path: Optional[str] = None
) -> OCRResult:
    """Quick text extraction with specified engine.
    
    Args:
        frame: Input BGR image
        frame_id: Frame identifier
        engine: OCR engine ("easyocr", "tesseract", "mock")
        config_path: Optional config file path
        
    Returns:
        OCRResult with detected text
    """
    ocr = OCREngine(engine=engine, config_path=config_path)
    return ocr.extract_text(frame, frame_id)
