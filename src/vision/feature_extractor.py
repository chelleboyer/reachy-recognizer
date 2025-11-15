"""
Feature Extraction from Torso ROIs - Story 2.2

Extracts color histograms and pattern features from torso regions for uniform
classification. Computes HSV histograms, edge density patterns, and dominant colors.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import pickle

import cv2
import numpy as np
import yaml

try:
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
except ImportError:
    KMeans = None  # type: ignore
    PCA = None  # type: ignore


@dataclass
class UniformFeatures:
    """Color and pattern features extracted from torso."""
    
    hsv_histogram: np.ndarray  # (4096,) normalized histogram
    pattern_descriptor: np.ndarray  # (9,) edge density grid
    dominant_colors: List[Tuple[float, float, float]]  # Top 3 HSV colors
    color_percentages: List[float]  # Percentages for top 3
    feature_vector: np.ndarray  # (512,) PCA-reduced features or (4105,) if no PCA
    roi_bbox: Tuple[int, int, int, int]  # x, y, w, h
    person_id: str  # Links to TorsoROI
    frame_id: str
    processing_time_ms: float
    
    def to_dict(self) -> dict:
        """Serialize to dictionary (exclude large arrays)."""
        return {
            'person_id': self.person_id,
            'frame_id': self.frame_id,
            'dominant_colors': [
                [float(c[0]), float(c[1]), float(c[2])] 
                for c in self.dominant_colors
            ],
            'color_percentages': [float(p) for p in self.color_percentages],
            'feature_dim': len(self.feature_vector),
            'processing_time_ms': float(self.processing_time_ms),
            'roi_bbox': self.roi_bbox
        }


class FeatureExtractor:
    """Extract color and pattern features from torso ROIs."""
    
    def __init__(self, config_path: str = "src/config/feature_extraction.yaml"):
        """
        Initialize feature extractor.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        self.config = self._load_config(config_path)
        self.extraction_count = 0
        
        # Extract configuration parameters
        fe_config = self.config.get('feature_extraction', {})
        
        color_cfg = fe_config.get('color_histogram', {})
        self.color_space = color_cfg.get('color_space', 'HSV')
        self.bins_per_channel = color_cfg.get('bins_per_channel', 16)
        self.hist_normalize = color_cfg.get('normalize', 'L1')
        
        pattern_cfg = fe_config.get('pattern_descriptor', {})
        self.grid_size = tuple(pattern_cfg.get('grid_size', [3, 3]))
        self.edge_detector = pattern_cfg.get('edge_detector', 'canny')
        self.canny_threshold = pattern_cfg.get('canny_threshold', [50, 150])
        self.edge_density_method = pattern_cfg.get('edge_density_method', 'mean')
        
        dominant_cfg = fe_config.get('dominant_colors', {})
        self.num_colors = dominant_cfg.get('num_colors', 3)
        self.min_percentage = dominant_cfg.get('min_percentage', 5.0)
        self.clustering_method = dominant_cfg.get('clustering_method', 'kmeans')
        
        reduction_cfg = fe_config.get('dimensionality_reduction', {})
        self.reduction_method = reduction_cfg.get('method', 'pca')
        self.target_dimensions = reduction_cfg.get('target_dimensions', 512)
        self.pca_model_path = reduction_cfg.get('pca_model_path', '')
        
        norm_cfg = fe_config.get('normalization', {})
        self.final_norm = norm_cfg.get('final_norm', 'L2')
        
        # Load PCA model after config parameters are set
        self.pca_model = self._load_pca_model()
    
    def _load_config(self, config_path: str) -> dict:
        """Load YAML configuration."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            if not isinstance(config, dict):
                raise ValueError("Config must be a dictionary")
            
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML config: {e}")
    
    def _load_pca_model(self) -> Optional[object]:
        """Load pre-trained PCA model if available."""
        if self.reduction_method != 'pca':
            return None
        
        pca_path = Path(self.pca_model_path) if hasattr(self, 'pca_model_path') else None
        
        if pca_path and pca_path.exists():
            try:
                with open(pca_path, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Warning: Failed to load PCA model: {e}")
                return None
        
        return None
    
    def extract_features(self, torso_roi) -> UniformFeatures:
        """
        Extract color and pattern features from torso ROI.
        
        Args:
            torso_roi: TorsoROI object from Story 2.1
            
        Returns:
            UniformFeatures object with all extracted features
            
        Raises:
            ValueError: If torso_image is None or invalid
        """
        start_time = time.time()
        
        # Validate input
        if torso_roi is None:
            raise ValueError("torso_roi cannot be None")
        
        if torso_roi.torso_image is None:
            raise ValueError("torso_roi.torso_image cannot be None")
        
        if not isinstance(torso_roi.torso_image, np.ndarray):
            raise ValueError("torso_image must be numpy array")
        
        if torso_roi.torso_image.size == 0:
            raise ValueError("torso_image cannot be empty")
        
        # Extract features
        hsv_histogram = self._compute_hsv_histogram(torso_roi.torso_image)
        pattern_descriptor = self._compute_pattern_descriptor(torso_roi.torso_image)
        dominant_colors, color_percentages = self._extract_dominant_colors(
            torso_roi.torso_image
        )
        
        # Create combined feature vector
        feature_vector = self._create_feature_vector(hsv_histogram, pattern_descriptor)
        
        # Apply PCA if model available
        if self.pca_model is not None:
            feature_vector = self._apply_pca(feature_vector)
        
        # Track statistics
        self.extraction_count += 1
        
        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return UniformFeatures(
            hsv_histogram=hsv_histogram,
            pattern_descriptor=pattern_descriptor,
            dominant_colors=dominant_colors,
            color_percentages=color_percentages,
            feature_vector=feature_vector,
            roi_bbox=torso_roi.torso_bbox,
            person_id=torso_roi.person_id,
            frame_id=torso_roi.frame_id,
            processing_time_ms=processing_time
        )
    
    def _compute_hsv_histogram(self, image: np.ndarray) -> np.ndarray:
        """
        Compute HSV color histogram.
        
        Args:
            image: RGB image (H, W, 3) with values in [0, 1]
            
        Returns:
            Normalized histogram (bins^3,)
        """
        # Convert [0, 1] to [0, 255] if needed
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
        
        # Convert RGB to HSV
        image_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Compute 3D histogram
        hist = cv2.calcHist(
            [image_hsv],
            channels=[0, 1, 2],  # H, S, V
            mask=None,
            histSize=[self.bins_per_channel] * 3,
            ranges=[0, 180, 0, 256, 0, 256]  # HSV ranges in OpenCV
        )
        
        # Flatten and normalize
        hist = hist.flatten()
        
        if self.hist_normalize == 'L1':
            # L1 norm: values sum to 1
            hist = hist / (hist.sum() + 1e-7)
        elif self.hist_normalize == 'L2':
            # L2 norm: unit vector
            norm = np.linalg.norm(hist)
            hist = hist / (norm + 1e-7)
        
        return hist
    
    def _compute_pattern_descriptor(self, image: np.ndarray) -> np.ndarray:
        """
        Compute edge density in grid cells.
        
        Args:
            image: RGB image (H, W, 3) with values in [0, 1]
            
        Returns:
            Edge density descriptor (grid_rows * grid_cols,)
        """
        # Convert [0, 1] to [0, 255] if needed
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Edge detection
        if self.edge_detector == 'canny':
            edges = cv2.Canny(
                gray, 
                self.canny_threshold[0], 
                self.canny_threshold[1]
            )
        elif self.edge_detector == 'sobel':
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edges = np.sqrt(sobelx**2 + sobely**2)
            edges = ((edges / edges.max()) * 255).astype(np.uint8)
        else:
            raise ValueError(f"Unknown edge detector: {self.edge_detector}")
        
        # Divide into grid
        h, w = edges.shape
        cell_h = h // self.grid_size[0]
        cell_w = w // self.grid_size[1]
        
        descriptor = []
        for i in range(self.grid_size[0]):
            for j in range(self.grid_size[1]):
                # Extract cell
                y_start = i * cell_h
                y_end = (i + 1) * cell_h if i < self.grid_size[0] - 1 else h
                x_start = j * cell_w
                x_end = (j + 1) * cell_w if j < self.grid_size[1] - 1 else w
                
                cell = edges[y_start:y_end, x_start:x_end]
                
                # Compute edge density
                if self.edge_density_method == 'mean':
                    edge_density = cell.mean() / 255.0
                elif self.edge_density_method == 'max':
                    edge_density = cell.max() / 255.0
                else:
                    edge_density = cell.mean() / 255.0
                
                descriptor.append(edge_density)
        
        return np.array(descriptor)
    
    def _extract_dominant_colors(
        self, 
        image: np.ndarray
    ) -> Tuple[List[Tuple[float, float, float]], List[float]]:
        """
        Extract top K dominant colors and percentages.
        
        Args:
            image: RGB image (H, W, 3) with values in [0, 1]
            
        Returns:
            Tuple of (colors, percentages)
            - colors: List of K HSV tuples
            - percentages: List of K percentages
        """
        if KMeans is None:
            raise ImportError(
                "scikit-learn not installed. "
                "Install with: pip install scikit-learn>=1.3.0"
            )
        
        # Convert [0, 1] to [0, 255] if needed
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
        
        # Convert RGB to HSV
        image_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Reshape to (N, 3) for clustering
        pixels = image_hsv.reshape(-1, 3).astype(np.float32)
        
        # K-means clustering
        kmeans = KMeans(
            n_clusters=self.num_colors, 
            random_state=42, 
            n_init=10
        )
        labels = kmeans.fit_predict(pixels)
        
        # Get cluster centers (dominant colors)
        centers = kmeans.cluster_centers_
        
        # Compute percentages
        unique, counts = np.unique(labels, return_counts=True)
        percentages = (counts / len(labels)) * 100
        
        # Sort by percentage (descending)
        sorted_idx = np.argsort(percentages)[::-1]
        
        # Filter by minimum percentage and convert to list
        colors = []
        filtered_percentages = []
        for idx in sorted_idx:
            if percentages[idx] >= self.min_percentage or len(colors) == 0:
                # Always include at least one color
                colors.append(tuple(float(c) for c in centers[idx]))
                filtered_percentages.append(float(percentages[idx]))
        
        # Ensure we have at least num_colors (pad with zeros if needed)
        while len(colors) < self.num_colors:
            colors.append((0.0, 0.0, 0.0))
            filtered_percentages.append(0.0)
        
        return colors[:self.num_colors], filtered_percentages[:self.num_colors]
    
    def _create_feature_vector(
        self, 
        histogram: np.ndarray, 
        pattern: np.ndarray
    ) -> np.ndarray:
        """
        Combine histogram and pattern into feature vector.
        
        Args:
            histogram: HSV histogram (4096,)
            pattern: Pattern descriptor (9,)
            
        Returns:
            Combined feature vector (4105,) with L2 normalization
        """
        # Concatenate features
        features = np.concatenate([histogram, pattern])
        
        # Apply final normalization
        if self.final_norm == 'L2':
            norm = np.linalg.norm(features)
            features = features / (norm + 1e-7)
        elif self.final_norm == 'L1':
            features = features / (features.sum() + 1e-7)
        
        return features
    
    def _apply_pca(self, features: np.ndarray) -> np.ndarray:
        """
        Reduce dimensionality using PCA.
        
        Args:
            features: Feature vector (4105,)
            
        Returns:
            Reduced feature vector (target_dimensions,)
        """
        if self.pca_model is None:
            return features
        
        # PCA expects 2D input
        features_2d = features.reshape(1, -1)
        reduced = self.pca_model.transform(features_2d)  # type: ignore
        
        return reduced.flatten()
    
    def get_statistics(self) -> dict:
        """Return extraction statistics."""
        return {
            'total_extractions': self.extraction_count,
            'feature_dim': self.target_dimensions if self.pca_model else (
                self.bins_per_channel ** 3 + self.grid_size[0] * self.grid_size[1]
            ),
            'pca_enabled': self.pca_model is not None,
            'color_space': self.color_space,
            'histogram_bins': self.bins_per_channel,
            'grid_size': self.grid_size
        }
    
    def reset_statistics(self):
        """Reset extraction counters."""
        self.extraction_count = 0


def extract_features_quick(torso_roi) -> UniformFeatures:
    """
    Quick feature extraction with default config.
    
    Args:
        torso_roi: TorsoROI object from Story 2.1
        
    Returns:
        UniformFeatures object
    """
    extractor = FeatureExtractor()
    return extractor.extract_features(torso_roi)
