"""Vision subsystem - Camera input, face detection, and recognition."""

from .camera_interface import CameraInterface
from .face_detector import FaceDetector
from .face_recognizer import FaceRecognizer
from .recognition_pipeline import RecognitionPipeline

__all__ = [
    "CameraInterface",
    "FaceDetector", 
    "FaceRecognizer",
    "RecognitionPipeline"
]
