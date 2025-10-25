"""
Configuration Loader - Story 4.1

Loads and validates YAML configuration with environment variable overrides.
Provides type-safe access to configuration values with defaults.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@dataclass
class CameraConfig:
    """Camera configuration settings."""
    device_id: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    process_every_n_frames: int = 1


@dataclass
class FaceDetectionConfig:
    """Face detection configuration."""
    model: str = "hog"
    upsample_times: int = 1
    min_face_size: int = 80


@dataclass
class FaceRecognitionConfig:
    """Face recognition configuration."""
    threshold: float = 0.6
    tolerance: float = 0.6
    database_path: str = "face_database.pkl"
    distance_metric: str = "euclidean"


@dataclass
class EventsConfig:
    """Event system configuration."""
    debounce_seconds: float = 3.0
    departed_threshold_seconds: float = 3.0
    max_event_history: int = 100
    min_greeting_interval_seconds: float = 60.0


@dataclass
class BehaviorTimingConfig:
    """Behavior timing settings."""
    greeting_wave_duration: float = 1.2
    curious_tilt_duration: float = 1.5
    idle_drift_duration: float = 3.0
    neutral_return_duration: float = 0.5


@dataclass
class IdleBehaviorConfig:
    """Idle behavior settings."""
    activation_threshold: float = 5.0
    movement_interval: float = 3.0
    roll_range: list = field(default_factory=lambda: [-5, 5])
    pitch_range: list = field(default_factory=lambda: [-5, 5])
    yaw_range: list = field(default_factory=lambda: [-10, 10])


@dataclass
class BehaviorsConfig:
    """Behavior system configuration."""
    enable_robot: bool = True
    gesture_speech_delay: float = 0.3
    timing: BehaviorTimingConfig = field(default_factory=BehaviorTimingConfig)
    idle: IdleBehaviorConfig = field(default_factory=IdleBehaviorConfig)


@dataclass
class OpenAITTSConfig:
    """OpenAI TTS settings."""
    model: str = "tts-1"
    voice: str = "nova"
    speed: float = 1.0


@dataclass
class Pyttsx3Config:
    """Pyttsx3 TTS settings."""
    rate: int = 150
    volume: float = 0.9
    voice_index: int = 1


@dataclass
class TTSCacheConfig:
    """TTS cache settings."""
    enabled: bool = True
    max_size: int = 50
    ttl_seconds: int = 3600


@dataclass
class TTSConfig:
    """Text-to-speech configuration."""
    use_enhanced_voice: bool = True
    backend_priority: list = field(default_factory=lambda: ["openai", "pyttsx3"])
    openai: OpenAITTSConfig = field(default_factory=OpenAITTSConfig)
    pyttsx3: Pyttsx3Config = field(default_factory=Pyttsx3Config)
    cache: TTSCacheConfig = field(default_factory=TTSCacheConfig)


@dataclass
class TimeOfDayConfig:
    """Time of day settings."""
    morning_start: int = 6
    afternoon_start: int = 12
    evening_start: int = 18
    night_start: int = 22


@dataclass
class GreetingsConfig:
    """Greeting system configuration."""
    personality: str = "warm"
    repetition_window: int = 5
    time_of_day: TimeOfDayConfig = field(default_factory=TimeOfDayConfig)
    custom_phrases: Optional[Dict[str, list]] = None


@dataclass
class PerformanceConfig:
    """Performance monitoring configuration."""
    target_latency_ms: int = 400
    stats_interval: int = 60
    frame_timeout: float = 5.0
    process_every_n_frames: int = 1


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file_path: Optional[str] = "logs/reachy_recognizer.log"
    max_bytes: int = 10485760  # 10 MB
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    json_format: bool = False


@dataclass
class SystemConfig:
    """System-level configuration."""
    reachy_host: str = "localhost"
    reachy_port: int = 50055
    shutdown_timeout: float = 5.0
    debug_display: bool = False


@dataclass
class Config:
    """
    Main configuration class containing all subsystem configs.
    """
    camera: CameraConfig = field(default_factory=CameraConfig)
    face_detection: FaceDetectionConfig = field(default_factory=FaceDetectionConfig)
    face_recognition: FaceRecognitionConfig = field(default_factory=FaceRecognitionConfig)
    events: EventsConfig = field(default_factory=EventsConfig)
    behaviors: BehaviorsConfig = field(default_factory=BehaviorsConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    greetings: GreetingsConfig = field(default_factory=GreetingsConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    system: SystemConfig = field(default_factory=SystemConfig)


class ConfigLoader:
    """
    Loads and manages system configuration from YAML files and environment variables.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Path to YAML config file (default: config.yaml in project root)
        """
        if config_path is None:
            # Try to find config.yaml in config directory
            config_path = Path(__file__).parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = Config()
        
    def load(self) -> Config:
        """
        Load configuration from YAML file and apply environment variable overrides.
        
        Returns:
            Loaded and validated Config object
            
        Raises:
            ConfigurationError: If config file not found or invalid
        """
        # Load from YAML if file exists
        if self.config_path.exists():
            logger.info(f"Loading configuration from {self.config_path}")
            self._load_yaml()
        else:
            logger.warning(f"Config file not found: {self.config_path}")
            logger.info("Using default configuration")
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate()
        
        logger.info("✓ Configuration loaded successfully")
        return self.config
    
    def _load_yaml(self):
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
            
            if not yaml_data:
                logger.warning("Empty YAML config file, using defaults")
                return
            
            # Parse each section
            if 'camera' in yaml_data:
                self.config.camera = CameraConfig(**yaml_data['camera'])
            
            if 'face_detection' in yaml_data:
                self.config.face_detection = FaceDetectionConfig(**yaml_data['face_detection'])
            
            if 'face_recognition' in yaml_data:
                self.config.face_recognition = FaceRecognitionConfig(**yaml_data['face_recognition'])
            
            if 'events' in yaml_data:
                self.config.events = EventsConfig(**yaml_data['events'])
            
            if 'behaviors' in yaml_data:
                b = yaml_data['behaviors']
                timing = BehaviorTimingConfig(**b.get('timing', {}))
                idle = IdleBehaviorConfig(**b.get('idle', {}))
                self.config.behaviors = BehaviorsConfig(
                    enable_robot=b.get('enable_robot', True),
                    gesture_speech_delay=b.get('gesture_speech_delay', 0.3),
                    timing=timing,
                    idle=idle
                )
            
            if 'tts' in yaml_data:
                t = yaml_data['tts']
                openai_cfg = OpenAITTSConfig(**t.get('openai', {}))
                pyttsx3_cfg = Pyttsx3Config(**t.get('pyttsx3', {}))
                cache_cfg = TTSCacheConfig(**t.get('cache', {}))
                self.config.tts = TTSConfig(
                    use_enhanced_voice=t.get('use_enhanced_voice', True),
                    backend_priority=t.get('backend_priority', ["openai", "pyttsx3"]),
                    openai=openai_cfg,
                    pyttsx3=pyttsx3_cfg,
                    cache=cache_cfg
                )
            
            if 'greetings' in yaml_data:
                g = yaml_data['greetings']
                tod = TimeOfDayConfig(**g.get('time_of_day', {}))
                self.config.greetings = GreetingsConfig(
                    personality=g.get('personality', 'warm'),
                    repetition_window=g.get('repetition_window', 5),
                    time_of_day=tod,
                    custom_phrases=g.get('custom_phrases')
                )
            
            if 'performance' in yaml_data:
                self.config.performance = PerformanceConfig(**yaml_data['performance'])
            
            if 'logging' in yaml_data:
                self.config.logging = LoggingConfig(**yaml_data['logging'])
            
            if 'system' in yaml_data:
                self.config.system = SystemConfig(**yaml_data['system'])
                
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML syntax: {e}")
        except TypeError as e:
            raise ConfigurationError(f"Invalid configuration value: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load config: {e}")
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides using REACHY_ prefix."""
        prefix = "REACHY_"
        
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue
            
            # Parse environment variable name
            # Format: REACHY_SECTION_KEY or REACHY_SECTION_SUBSECTION_KEY
            parts = env_key[len(prefix):].lower().split('_')
            
            if len(parts) < 2:
                continue
            
            try:
                self._set_config_value(parts, env_value)
                logger.debug(f"Applied env override: {env_key}={env_value}")
            except Exception as e:
                logger.warning(f"Failed to apply env override {env_key}: {e}")
    
    def _set_config_value(self, parts: list, value: str):
        """Set configuration value from environment variable."""
        section = parts[0]
        key = parts[1] if len(parts) == 2 else '_'.join(parts[1:])
        
        # Get the config section
        if not hasattr(self.config, section):
            return
        
        config_obj = getattr(self.config, section)
        
        # Convert string value to appropriate type
        if hasattr(config_obj, key):
            current_value = getattr(config_obj, key)
            typed_value = self._convert_type(value, type(current_value))
            setattr(config_obj, key, typed_value)
    
    def _convert_type(self, value: str, target_type: type) -> Any:
        """Convert string value to target type."""
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == list:
            return value.split(',')
        else:
            return value
    
    def _validate(self):
        """Validate configuration values."""
        errors = []
        
        # Validate camera config
        if self.config.camera.device_id < 0:
            errors.append("camera.device_id must be >= 0")
        if self.config.camera.fps <= 0:
            errors.append("camera.fps must be > 0")
        
        # Validate recognition threshold
        if not 0.0 <= self.config.face_recognition.threshold <= 1.0:
            errors.append("face_recognition.threshold must be between 0.0 and 1.0")
        
        # Validate TTS voice
        valid_voices = ['alloy', 'echo', 'fable', 'onyx', 'nova', 'shimmer']
        if self.config.tts.openai.voice not in valid_voices:
            errors.append(f"tts.openai.voice must be one of {valid_voices}")
        
        # Validate logging level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.config.logging.level.upper() not in valid_levels:
            errors.append(f"logging.level must be one of {valid_levels}")
        
        # Validate greeting personality
        valid_personalities = ['warm', 'professional', 'casual', 'enthusiastic']
        if self.config.greetings.personality not in valid_personalities:
            errors.append(f"greetings.personality must be one of {valid_personalities}")
        
        if errors:
            raise ConfigurationError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


# Global config instance
_config: Optional[Config] = None


def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load global configuration.
    
    Args:
        config_path: Path to config file (default: config.yaml)
        
    Returns:
        Loaded Config object
    """
    global _config
    
    if _config is None:
        loader = ConfigLoader(config_path)
        _config = loader.load()
    
    return _config


def get_config() -> Config:
    """
    Get global configuration (loads if not already loaded).
    
    Returns:
        Config object
    """
    if _config is None:
        return load_config()
    return _config


def reload_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Reloaded Config object
    """
    global _config
    _config = None
    return load_config(config_path)


if __name__ == "__main__":
    # Test configuration loading
    print("="*70)
    print("Configuration Loader Test")
    print("="*70)
    
    try:
        config = load_config()
        
        print("\n✓ Configuration loaded successfully!\n")
        print(f"Camera device: {config.camera.device_id}")
        print(f"Recognition threshold: {config.face_recognition.threshold}")
        print(f"TTS voice: {config.tts.openai.voice}")
        print(f"Greeting personality: {config.greetings.personality}")
        print(f"Enable robot: {config.behaviors.enable_robot}")
        print(f"Idle activation: {config.behaviors.idle.activation_threshold}s")
        print(f"Logging level: {config.logging.level}")
        
    except ConfigurationError as e:
        print(f"\n✗ Configuration error: {e}")
    
    print("\n" + "="*70)
