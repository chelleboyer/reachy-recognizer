"""
Reachy Recognizer - Face recognition and greeting robot system.

Package structure:
- vision: Camera, face detection, and recognition
- behaviors: Robot behaviors and movements
- voice: Text-to-speech and greeting selection
- events: Event system for recognition state changes
- coordination: High-level coordination of behaviors
- config: Configuration management
"""

__version__ = "1.0.0"
__author__ = "Michelle"

from .config.config_loader import load_config, get_config, Config

__all__ = ["load_config", "get_config", "Config"]
