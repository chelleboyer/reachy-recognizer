"""
Speech-to-Text Module

Captures audio from microphone and transcribes it using OpenAI Whisper API.
Supports real-time voice activity detection and streaming transcription.
"""

import logging
import pyaudio
import wave
import tempfile
import os
from typing import Optional, Callable
from dataclasses import dataclass
import threading
import queue
import time
import numpy as np
from openai import OpenAI

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""
    text: str
    confidence: float = 1.0
    duration: float = 0.0
    language: Optional[str] = None


class AudioRecorder:
    """
    Records audio from microphone with voice activity detection.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        silence_threshold: float = 500,
        silence_duration: float = 1.5
    ):
        """
        Initialize audio recorder.
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Audio chunk size (samples)
            channels: Number of audio channels
            silence_threshold: RMS threshold for voice detection
            silence_duration: Seconds of silence before stopping
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.is_recording = False
        
        logger.info(f"AudioRecorder initialized: {sample_rate}Hz, threshold={silence_threshold}")
    
    def _calculate_rms(self, audio_data: bytes) -> float:
        """Calculate RMS (volume) of audio data."""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        return np.sqrt(np.mean(audio_array**2))
    
    def record_until_silence(self) -> bytes:
        """
        Record audio until silence is detected.
        
        Returns:
            Raw audio data (WAV format)
        """
        frames = []
        silence_chunks = 0
        max_silence_chunks = int(self.silence_duration * self.sample_rate / self.chunk_size)
        started = False
        
        # Open stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        logger.info("🎤 Listening... (speak now)")
        self.is_recording = True
        
        try:
            while self.is_recording:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                
                # Check volume
                rms = self._calculate_rms(data)
                
                if rms > self.silence_threshold:
                    silence_chunks = 0
                    if not started:
                        started = True
                        logger.info("🔊 Voice detected, recording...")
                else:
                    if started:
                        silence_chunks += 1
                        if silence_chunks > max_silence_chunks:
                            logger.info("🔇 Silence detected, stopping...")
                            break
        
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.is_recording = False
        
        # Convert to WAV format
        return self._frames_to_wav(frames)
    
    def _frames_to_wav(self, frames: list) -> bytes:
        """Convert audio frames to WAV format."""
        import io
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
        
        return wav_buffer.getvalue()
    
    def stop(self):
        """Stop recording."""
        self.is_recording = False
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        self.audio.terminate()
        logger.info("AudioRecorder cleaned up")


class SpeechToText:
    """
    Speech-to-text using OpenAI Whisper API.
    """
    
    def __init__(
        self,
        model: str = "whisper-1",
        language: Optional[str] = None
    ):
        """
        Initialize speech-to-text.
        
        Args:
            model: Whisper model to use
            language: Language code (None for auto-detect)
        """
        self.model = model
        self.language = language
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"SpeechToText initialized: model={model}")
    
    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Audio data in WAV format
            
        Returns:
            Transcription result
        """
        start_time = time.time()
        
        try:
            # Save to temporary file (Whisper API requires file input)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name
            
            try:
                # Transcribe with Whisper API
                with open(tmp_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        language=self.language
                    )
                
                duration = time.time() - start_time
                text = response.text.strip()
                
                logger.info(f"✓ Transcribed in {duration:.2f}s: \"{text}\"")
                
                return TranscriptionResult(
                    text=text,
                    duration=duration,
                    language=getattr(response, 'language', None)
                )
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    def transcribe_from_microphone(
        self,
        recorder: Optional[AudioRecorder] = None,
        cleanup: bool = False
    ) -> TranscriptionResult:
        """
        Record from microphone and transcribe.
        
        Args:
            recorder: AudioRecorder instance (creates new one if None)
            cleanup: Whether to cleanup recorder after use
            
        Returns:
            Transcription result
        """
        created_recorder = False
        if recorder is None:
            recorder = AudioRecorder()
            created_recorder = True
        
        try:
            audio_data = recorder.record_until_silence()
            return self.transcribe(audio_data)
        finally:
            if created_recorder or cleanup:
                recorder.cleanup()


class VoiceConversationLoop:
    """
    Manages voice-based conversation loop with STT and TTS.
    """
    
    def __init__(
        self,
        on_transcription: Callable[[str], str],
        auto_start: bool = False
    ):
        """
        Initialize voice conversation loop.
        
        Args:
            on_transcription: Callback function that takes transcribed text
                             and returns response text
            auto_start: Start listening automatically
        """
        self.on_transcription = on_transcription
        self.recorder = AudioRecorder()
        self.stt = SpeechToText()
        self.is_running = False
        
        logger.info("VoiceConversationLoop initialized")
        
        if auto_start:
            self.start()
    
    def start(self):
        """Start conversation loop."""
        self.is_running = True
        logger.info("▶️ Voice conversation started")
        
        while self.is_running:
            try:
                # Listen for speech
                print("\n🎤 Listening... (speak now, or Ctrl+C to exit)")
                result = self.stt.transcribe_from_microphone(self.recorder)
                
                if result.text:
                    print(f"You said: {result.text}")
                    
                    # Get response
                    response = self.on_transcription(result.text)
                    print(f"Response: {response}")
                else:
                    print("⚠️ No speech detected")
            
            except KeyboardInterrupt:
                print("\n⏹️ Stopping conversation loop...")
                break
            except Exception as e:
                logger.error(f"Conversation loop error: {e}")
                time.sleep(1)
        
        self.stop()
    
    def stop(self):
        """Stop conversation loop."""
        self.is_running = False
        self.recorder.cleanup()
        logger.info("Voice conversation stopped")


# Demo/Testing
def main():
    """Demo speech-to-text."""
    print("=" * 70)
    print("Speech-to-Text Demo")
    print("=" * 70)
    print()
    
    print("This demo will:")
    print("1. Record audio from your microphone")
    print("2. Detect when you stop speaking (1.5s silence)")
    print("3. Transcribe using OpenAI Whisper")
    print()
    
    input("Press Enter to start recording...")
    
    stt = SpeechToText()
    recorder = AudioRecorder()
    
    try:
        result = stt.transcribe_from_microphone(recorder)
        
        print("\n" + "=" * 70)
        print("Results:")
        print("=" * 70)
        print(f"Text: {result.text}")
        print(f"Duration: {result.duration:.2f}s")
        if result.language:
            print(f"Language: {result.language}")
        
        print("\n✅ Demo complete!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        recorder.cleanup()


if __name__ == "__main__":
    main()
