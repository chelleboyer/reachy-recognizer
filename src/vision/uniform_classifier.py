"""
Uniform classifier for staff vs customer classification.

This module implements Story 2.3: Staff vs Customer Classification
Uses feature vectors from Story 2.2 to classify people as staff or customers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import time
import logging

import numpy as np
import yaml

from .feature_extractor import UniformFeatures

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of staff vs customer classification."""
    
    label: str  # "staff" or "customer"
    confidence: float  # 0.0 to 1.0 probability
    is_certain: bool  # True if confidence >= threshold
    frame_count: int  # Number of frames used
    feature_vector: np.ndarray  # (512,) average features
    individual_votes: List[Tuple[str, float]]  # Per-frame (label, confidence)
    processing_time_ms: float
    person_id: str  # Links to TorsoROI
    timestamp: float  # Unix timestamp
    model_version: str  # Classifier version used
    
    def to_dict(self) -> dict:
        """Serialize to dictionary (exclude large arrays)."""
        return {
            'label': self.label,
            'confidence': self.confidence,
            'is_certain': self.is_certain,
            'frame_count': self.frame_count,
            'person_id': self.person_id,
            'timestamp': self.timestamp,
            'model_version': self.model_version,
            'processing_time_ms': self.processing_time_ms,
            'individual_votes': [
                {'label': v[0], 'confidence': v[1]} 
                for v in self.individual_votes
            ]
        }


class UniformClassifier:
    """Classify people as staff or customer based on uniform features."""
    
    def __init__(self, config_path: str = "src/config/uniform_classifier.yaml"):
        """
        Initialize classifier.
        
        Args:
            config_path: Path to configuration YAML file
            
        Raises:
            FileNotFoundError: If config or model file not found
            ValueError: If config is invalid
        """
        self.config = self._load_config(config_path)
        self.model = self._load_model()
        self.classification_count = 0
        self.frame_buffer: Dict[str, List[UniformFeatures]] = {}
        
        # Extract commonly used config values
        self.confidence_threshold = self.config['classification']['confidence_threshold']
        self.multi_frame_enabled = self.config['multi_frame']['enabled']
        self.num_frames = self.config['multi_frame']['num_frames']
        self.min_frames = self.config['multi_frame']['min_frames']
        self.voting_method = self.config['multi_frame']['voting_method']
        self.model_version = self.config['model']['version']
        self.labels = self.config['classification']['labels']
        
        logger.info(
            f"UniformClassifier initialized (model_version={self.model_version}, "
            f"threshold={self.confidence_threshold})"
        )
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            
        if 'uniform_classifier' not in config:
            raise ValueError("Config must contain 'uniform_classifier' key")
            
        return config['uniform_classifier']
        
    def _load_model(self) -> object:
        """
        Load trained classifier model.
        
        Returns:
            Trained model object (SVM or MLP)
            
        Note:
            In testing, this returns a mock model for deterministic predictions.
            In production, this would load a real trained sklearn/torch model.
        """
        model_path = Path(self.config['model']['model_path'])
        
        # Check if model exists
        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}, using mock model")
            return self._create_mock_model()
            
        # In production, load real model:
        # import joblib
        # model_data = joblib.load(model_path)
        # return model_data['model']
        
        # For now, use mock model
        return self._create_mock_model()
        
    def _create_mock_model(self) -> object:
        """
        Create a mock model for testing.
        
        Mock model logic:
        - If mean of first 100 features > 0.5: classify as "staff" (uniform-like)
        - Otherwise: classify as "customer"
        - Confidence based on distance from threshold
        """
        class MockModel:
            def predict_proba(self, X: np.ndarray) -> np.ndarray:
                """
                Predict probabilities for binary classification.
                
                Args:
                    X: (N, D) feature matrix
                    
                Returns:
                    (N, 2) probability matrix [P(customer), P(staff)]
                """
                # Simple heuristic: staff uniforms have higher mean intensity in first features
                # (darker/solid colors in HSV histogram low bins)
                scores = []
                for features in X:
                    # Use first 100 features as proxy for uniform presence
                    mean_intensity = np.mean(features[:100])
                    
                    # Staff uniforms tend to have more concentrated color histograms
                    # (higher values in fewer bins)
                    std_intensity = np.std(features[:100])
                    
                    # Combine mean and std for classification
                    # High mean + high std = uniform-like = staff
                    # Scale to make differences more pronounced
                    staff_score = (mean_intensity * 2.0 + std_intensity * 1.5)
                    
                    # Clip to [0.1, 0.9] range for realistic probabilities
                    staff_score = np.clip(staff_score, 0.1, 0.9)
                    customer_score = 1.0 - staff_score
                    
                    scores.append([customer_score, staff_score])
                    
                return np.array(scores)
        
        return MockModel()
        
    def classify(
        self, 
        features: UniformFeatures,
        person_id: Optional[str] = None
    ) -> Optional[ClassificationResult]:
        """
        Classify a person as staff or customer.
        
        If multi-frame enabled, buffers features until enough frames collected,
        then returns classification. Otherwise classifies immediately.
        
        Args:
            features: UniformFeatures from Story 2.2
            person_id: Optional person ID for multi-frame tracking
            
        Returns:
            ClassificationResult (or None if waiting for more frames)
            
        Raises:
            ValueError: If features are invalid
        """
        start_time = time.time()
        
        if features is None:
            raise ValueError("Features cannot be None")
            
        if features.feature_vector is None or len(features.feature_vector) == 0:
            raise ValueError("Feature vector is empty")
            
        # Generate person_id if not provided
        if person_id is None:
            person_id = f"person_{int(time.time() * 1000)}"
            
        # Multi-frame mode: buffer frames
        if self.multi_frame_enabled:
            # Initialize buffer for this person
            if person_id not in self.frame_buffer:
                self.frame_buffer[person_id] = []
                
            # Add features to buffer
            self.frame_buffer[person_id].append(features)
            
            # Check if we have enough frames
            if len(self.frame_buffer[person_id]) < self.min_frames:
                logger.debug(
                    f"Buffering frame {len(self.frame_buffer[person_id])}/{self.min_frames} "
                    f"for {person_id}"
                )
                return None  # Not enough frames yet
                
            # Check if we've reached target frames or should classify
            if len(self.frame_buffer[person_id]) >= self.num_frames:
                feature_sequence = self.frame_buffer[person_id]
                result = self.classify_multi_frame(feature_sequence, person_id)
                
                # Clear buffer after classification
                del self.frame_buffer[person_id]
                
                return result
            else:
                return None  # Still collecting frames
                
        # Single-frame mode: classify immediately
        feature_vector = features.feature_vector.reshape(1, -1)
        label, confidence = self._predict(feature_vector)
        
        is_certain = confidence >= self.confidence_threshold
        processing_time_ms = (time.time() - start_time) * 1000
        
        self.classification_count += 1
        
        return ClassificationResult(
            label=label,
            confidence=confidence,
            is_certain=is_certain,
            frame_count=1,
            feature_vector=features.feature_vector,
            individual_votes=[(label, confidence)],
            processing_time_ms=processing_time_ms,
            person_id=person_id,
            timestamp=time.time(),
            model_version=self.model_version
        )
        
    def classify_multi_frame(
        self, 
        feature_sequence: List[UniformFeatures],
        person_id: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify using multiple frames (batch mode).
        
        Args:
            feature_sequence: List of features from different frames
            person_id: Optional person ID for tracking
            
        Returns:
            ClassificationResult with averaged features
            
        Raises:
            ValueError: If feature_sequence is empty or invalid
        """
        start_time = time.time()
        
        if not feature_sequence:
            raise ValueError("Feature sequence cannot be empty")
            
        if len(feature_sequence) < self.min_frames:
            raise ValueError(
                f"Need at least {self.min_frames} frames, got {len(feature_sequence)}"
            )
            
        if person_id is None:
            person_id = f"person_{int(time.time() * 1000)}"
            
        # Method 1: Average features, then classify
        if self.voting_method == "average_features":
            avg_features = self._average_features(feature_sequence)
            label, confidence = self._predict(avg_features.reshape(1, -1))
            individual_votes = [(label, confidence)]  # Single vote from averaged features
            
        # Method 2: Classify each frame, then majority vote
        elif self.voting_method == "majority_vote":
            individual_votes = []
            for features in feature_sequence:
                feature_vector = features.feature_vector.reshape(1, -1)
                frame_label, frame_confidence = self._predict(feature_vector)
                individual_votes.append((frame_label, frame_confidence))
                
            label, confidence = self._majority_vote(individual_votes)
            avg_features = self._average_features(feature_sequence)
            
        else:
            raise ValueError(f"Unknown voting method: {self.voting_method}")
            
        is_certain = confidence >= self.confidence_threshold
        processing_time_ms = (time.time() - start_time) * 1000
        
        self.classification_count += 1
        
        return ClassificationResult(
            label=label,
            confidence=confidence,
            is_certain=is_certain,
            frame_count=len(feature_sequence),
            feature_vector=avg_features,
            individual_votes=individual_votes,
            processing_time_ms=processing_time_ms,
            person_id=person_id,
            timestamp=time.time(),
            model_version=self.model_version
        )
        
    def _predict(self, feature_vector: np.ndarray) -> Tuple[str, float]:
        """
        Run model inference.
        
        Args:
            feature_vector: (1, D) feature matrix
            
        Returns:
            (label, confidence) tuple
        """
        # Get probability predictions
        proba = self.model.predict_proba(feature_vector)  # type: ignore  # (1, 2) -> [P(customer), P(staff)]
        
        # Extract probabilities
        customer_prob = proba[0, 0]
        staff_prob = proba[0, 1]
        
        # Determine label (higher probability)
        if staff_prob > customer_prob:
            label = "staff"
            confidence = staff_prob
        else:
            label = "customer"
            confidence = customer_prob
            
        return label, confidence
        
    def _average_features(
        self, 
        feature_sequence: List[UniformFeatures]
    ) -> np.ndarray:
        """
        Average feature vectors across frames.
        
        Args:
            feature_sequence: List of UniformFeatures objects
            
        Returns:
            (D,) averaged feature vector
        """
        feature_matrix = np.array([f.feature_vector for f in feature_sequence])
        return np.mean(feature_matrix, axis=0)
        
    def _majority_vote(
        self, 
        predictions: List[Tuple[str, float]]
    ) -> Tuple[str, float]:
        """
        Compute majority vote from individual predictions.
        
        Args:
            predictions: List of (label, confidence) tuples
            
        Returns:
            (majority_label, average_confidence) tuple
        """
        # Count votes for each label
        votes = {}
        confidences = {}
        
        for label, confidence in predictions:
            if label not in votes:
                votes[label] = 0
                confidences[label] = []
            votes[label] += 1
            confidences[label].append(confidence)
            
        # Find majority label
        majority_label = max(votes, key=votes.get)  # type: ignore
        
        # Average confidence for majority label
        avg_confidence = np.mean(confidences[majority_label])
        
        return majority_label, float(avg_confidence)
        
    def get_statistics(self) -> dict:
        """Return classification statistics."""
        return {
            'total_classifications': self.classification_count,
            'model_version': self.model_version,
            'confidence_threshold': self.confidence_threshold,
            'multi_frame_enabled': self.multi_frame_enabled,
            'buffered_people': len(self.frame_buffer)
        }
        
    def reset_statistics(self):
        """Reset classification counters."""
        self.classification_count = 0
        self.frame_buffer.clear()


# Convenience function
def classify_person_quick(features: UniformFeatures) -> ClassificationResult:
    """
    Quick classification with default config.
    
    Args:
        features: UniformFeatures from Story 2.2
        
    Returns:
        ClassificationResult
    """
    classifier = UniformClassifier()
    return classifier.classify(features, person_id="quick_classify")  # type: ignore
