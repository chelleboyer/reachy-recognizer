# Story 2.2: Color-Pattern Feature Extraction

**Epic:** Epic 2 - Uniform Recognition System  
**Story Points:** 5  
**Priority:** P0 (Must Have)  
**Status:** Ready for Development

---

## Story Description

**As a** Reachy Mini robot  
**I want to** extract color histograms and pattern features from torso regions  
**So that** I can build feature vectors for staff/customer classification

---

## Acceptance Criteria

### AC1: HSV Color Histogram
- [ ] HSV color histogram computed from torso ROI
- [ ] 16 bins per channel (H, S, V) = 4096 dimensions
- [ ] Histogram normalized (L1 norm so values sum to 1)
- [ ] Configurable bin count via YAML

### AC2: Pattern Encoding
- [ ] Edge density computed in 3x3 grid over torso
- [ ] Pattern descriptor: 9 values (one per grid cell)
- [ ] Edge detection using Canny or Sobel
- [ ] Solid vs striped vs logo detection based on edge density

### AC3: Dominant Colors
- [ ] Top 3 dominant colors extracted with percentages
- [ ] Colors in HSV space for uniform representation
- [ ] Percentages sum to ≤100% (top 3 may not cover all pixels)

### AC4: Feature Vector Normalization
- [ ] Combined feature vector (4096 + 9 = 4105-dim)
- [ ] L2 normalization applied
- [ ] PCA reduction to 512-dim (trained on uniform dataset)

### AC5: Configurable Parameters
- [ ] Histogram bins configurable (default 16)
- [ ] Edge detection threshold configurable
- [ ] PCA dimensions configurable (default 512)

### AC6: Unit Tests
- [ ] Test histogram computation correctness
- [ ] Test pattern descriptor edge cases
- [ ] Test dominant color extraction
- [ ] Test feature normalization

### AC7: Integration Test
- [ ] End-to-end with sample uniform images
- [ ] Test with solid color uniforms
- [ ] Test with striped/patterned uniforms

---

## Technical Specification

### Input
```python
# From Story 2.1
torso_roi: TorsoROI  # Contains preprocessed torso image
```

### Output
```python
@dataclass
class UniformFeatures:
    """Color and pattern features extracted from torso."""
    hsv_histogram: np.ndarray  # (4096,) normalized histogram
    pattern_descriptor: np.ndarray  # (9,) edge density grid
    dominant_colors: List[Tuple[float, float, float]]  # Top 3 HSV colors
    color_percentages: List[float]  # Percentages for top 3
    feature_vector: np.ndarray  # (512,) PCA-reduced features
    roi_bbox: Tuple[int, int, int, int]  # x, y, w, h
    person_id: str  # Links to TorsoROI
    frame_id: str
    processing_time_ms: float
    
    def to_dict(self) -> dict:
        """Serialize to dictionary (exclude large arrays)."""
        return {
            'person_id': self.person_id,
            'frame_id': self.frame_id,
            'dominant_colors': self.dominant_colors,
            'color_percentages': self.color_percentages,
            'feature_dim': len(self.feature_vector),
            'processing_time_ms': self.processing_time_ms
        }
```

### Configuration
```yaml
# feature_extraction.yaml
feature_extraction:
  color_histogram:
    color_space: "HSV"  # HSV or RGB
    bins_per_channel: 16  # 16x16x16 = 4096 bins
    normalize: "L1"  # L1 (sum to 1) or L2 (unit vector)
    
  pattern_descriptor:
    grid_size: [3, 3]  # 3x3 grid over torso
    edge_detector: "canny"  # "canny" or "sobel"
    canny_threshold: [50, 150]
    edge_density_method: "mean"  # mean or max edge pixels per cell
    
  dominant_colors:
    num_colors: 3  # Top K colors to extract
    min_percentage: 5.0  # Ignore colors <5% of pixels
    clustering_method: "kmeans"  # kmeans or median_cut
    
  dimensionality_reduction:
    method: "pca"  # "pca" or "none"
    target_dimensions: 512
    pca_model_path: "models/uniform_pca.pkl"  # Pre-trained PCA
    
  normalization:
    final_norm: "L2"  # L2 normalization for feature vector
```

### API Design

```python
class FeatureExtractor:
    """Extract color and pattern features from torso ROIs."""
    
    def __init__(self, config_path: str = "src/config/feature_extraction.yaml"):
        """Initialize feature extractor."""
        self.config = self._load_config(config_path)
        self.pca_model = self._load_pca_model()
        self.extraction_count = 0
        
    def extract_features(
        self, 
        torso_roi: TorsoROI
    ) -> UniformFeatures:
        """
        Extract color and pattern features from torso ROI.
        
        Args:
            torso_roi: TorsoROI object from Story 2.1
            
        Returns:
            UniformFeatures object with all extracted features
            
        Raises:
            ValueError: If torso_image is None or invalid
        """
        pass
        
    def _compute_hsv_histogram(self, image: np.ndarray) -> np.ndarray:
        """Compute HSV color histogram."""
        pass
        
    def _compute_pattern_descriptor(self, image: np.ndarray) -> np.ndarray:
        """Compute edge density in 3x3 grid."""
        pass
        
    def _extract_dominant_colors(
        self, 
        image: np.ndarray
    ) -> Tuple[List[Tuple], List[float]]:
        """Extract top K dominant colors and percentages."""
        pass
        
    def _create_feature_vector(
        self, 
        histogram: np.ndarray, 
        pattern: np.ndarray
    ) -> np.ndarray:
        """Combine histogram and pattern into feature vector."""
        pass
        
    def _apply_pca(self, features: np.ndarray) -> np.ndarray:
        """Reduce dimensionality using PCA."""
        pass
        
    def get_statistics(self) -> dict:
        """Return extraction statistics."""
        return {
            'total_extractions': self.extraction_count,
            'feature_dim': self.config['dimensionality_reduction']['target_dimensions'],
            'pca_enabled': self.pca_model is not None
        }
        
    def reset_statistics(self):
        """Reset extraction counters."""
        pass


# Convenience function
def extract_features_quick(torso_roi: TorsoROI) -> UniformFeatures:
    """Quick feature extraction with default config."""
    extractor = FeatureExtractor()
    return extractor.extract_features(torso_roi)
```

---

## Implementation Notes

### HSV Histogram Computation
```python
def compute_hsv_histogram(image_rgb, bins=16):
    """
    Compute HSV histogram with 16 bins per channel.
    
    Args:
        image_rgb: (H, W, 3) RGB image
        bins: Bins per channel (default 16)
        
    Returns:
        histogram: (bins^3,) normalized histogram
    """
    # Convert RGB to HSV
    image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    
    # Compute 3D histogram
    hist = cv2.calcHist(
        [image_hsv], 
        channels=[0, 1, 2],  # H, S, V
        mask=None,
        histSize=[bins, bins, bins],
        ranges=[0, 180, 0, 256, 0, 256]  # HSV ranges in OpenCV
    )
    
    # Flatten and normalize (L1 norm)
    hist = hist.flatten()
    hist = hist / (hist.sum() + 1e-7)  # Avoid division by zero
    
    return hist  # (4096,) for 16 bins
```

### Pattern Descriptor (Edge Density)
```python
def compute_pattern_descriptor(image_rgb, grid_size=(3, 3)):
    """
    Compute edge density in grid cells.
    
    Args:
        image_rgb: (H, W, 3) RGB image
        grid_size: (rows, cols) grid dimensions
        
    Returns:
        descriptor: (rows*cols,) edge density per cell
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    
    # Canny edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Divide into grid
    h, w = edges.shape
    cell_h, cell_w = h // grid_size[0], w // grid_size[1]
    
    descriptor = []
    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            # Extract cell
            cell = edges[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
            
            # Edge density = percentage of edge pixels
            edge_density = cell.mean() / 255.0
            descriptor.append(edge_density)
    
    return np.array(descriptor)  # (9,) for 3x3 grid
```

### Dominant Color Extraction
```python
def extract_dominant_colors(image_rgb, k=3):
    """
    Extract top K dominant colors using K-means.
    
    Args:
        image_rgb: (H, W, 3) RGB image
        k: Number of dominant colors
        
    Returns:
        colors: List of K HSV tuples
        percentages: List of K percentages
    """
    # Convert to HSV
    image_hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    
    # Reshape to (N, 3) for clustering
    pixels = image_hsv.reshape(-1, 3).astype(np.float32)
    
    # K-means clustering
    from sklearn.cluster import KMeans
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(pixels)
    
    # Get cluster centers (dominant colors)
    colors = kmeans.cluster_centers_
    
    # Compute percentages
    unique, counts = np.unique(labels, return_counts=True)
    percentages = (counts / len(labels)) * 100
    
    # Sort by percentage (descending)
    sorted_idx = np.argsort(percentages)[::-1]
    colors = [tuple(colors[i]) for i in sorted_idx]
    percentages = [float(percentages[i]) for i in sorted_idx]
    
    return colors, percentages
```

### PCA Training (Separate Script)
```python
# tools/train_pca.py
"""
Train PCA model on uniform dataset for dimensionality reduction.

Usage: python tools/train_pca.py --data data/uniforms/ --output models/uniform_pca.pkl
"""
from sklearn.decomposition import PCA
import pickle

def train_pca(feature_matrix, n_components=512):
    """
    Train PCA to reduce 4105-dim to 512-dim.
    
    Args:
        feature_matrix: (N, 4105) array of features from N uniform samples
        n_components: Target dimensions
        
    Returns:
        pca_model: Trained PCA transformer
    """
    pca = PCA(n_components=n_components)
    pca.fit(feature_matrix)
    
    print(f"Explained variance: {pca.explained_variance_ratio_.sum():.3f}")
    
    return pca
```

---

## Testing Strategy

### Unit Tests (`tests/test_story_2_2_feature_extraction.py`)

```python
class TestFeatureExtractor:
    - test_load_config()
    - test_missing_config_raises_error()
    - test_pca_model_loads()
    
class TestHSVHistogram:
    - test_compute_histogram_16_bins()
    - test_histogram_normalized()
    - test_histogram_sum_equals_one()
    - test_solid_color_image_histogram()
    
class TestPatternDescriptor:
    - test_edge_density_3x3_grid()
    - test_solid_image_low_edge_density()
    - test_striped_image_high_edge_density()
    - test_pattern_values_in_range_0_to_1()
    
class TestDominantColors:
    - test_extract_top_3_colors()
    - test_percentages_sum_less_equal_100()
    - test_colors_in_hsv_space()
    - test_single_color_image()
    
class TestFeatureVector:
    - test_feature_vector_4105_dim()
    - test_feature_vector_512_dim_after_pca()
    - test_L2_normalized()
    
class TestEdgeCases:
    - test_invalid_torso_roi_raises_error()
    - test_empty_image_raises_error()
    - test_grayscale_image_converted()
```

### Integration Tests (`tests/test_story_2_2_integration.py`)

```python
class TestEndToEndExtraction:
    - test_extract_features_from_uniform_sample()
    - test_extract_features_solid_blue_vest()
    - test_extract_features_striped_shirt()
    - test_extract_features_customer_clothing()
    
class TestWithStory21:
    - test_detect_and_extract_features()  # Integration with Story 2.1
    - test_multiple_people_feature_extraction()
```

---

## Definition of Done

- [ ] FeatureExtractor class implemented
- [ ] UniformFeatures dataclass implemented
- [ ] Configuration YAML created
- [ ] HSV histogram extraction working
- [ ] Pattern descriptor computation working
- [ ] Dominant color extraction working
- [ ] PCA integration (with mock model for testing)
- [ ] 20+ unit tests passing
- [ ] 5+ integration tests passing
- [ ] Code reviewed for efficiency
- [ ] Documentation updated (API docs, feature description)

---

## Dependencies

### Python Packages
- `opencv-python` (already installed)
- `numpy` (already installed)
- `scikit-learn>=1.3.0` (for PCA and K-means)
- `pyyaml` (already installed)

### Prior Work
- **Story 2.1:** Provides TorsoROI input

### Data
- Uniform samples for PCA training (can use synthetic data initially)

---

## Estimated Effort

**5 Story Points** = ~1-2 days

- HSV histogram implementation: 0.5 days
- Pattern descriptor: 0.5 days
- Dominant colors: 0.25 days
- PCA integration: 0.25 days
- Unit tests: 0.5 days
- Integration tests: 0.25 days

---

**Story Created:** 2025-11-15  
**Ready for Development:** Yes  
**Assigned Agent:** dev
