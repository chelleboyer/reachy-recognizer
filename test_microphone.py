"""
Microphone Test Utility

Tests microphone input and helps calibrate voice detection threshold.
"""

import pyaudio
import numpy as np
import time

def list_audio_devices():
    """List all available audio input devices."""
    audio = pyaudio.PyAudio()
    
    print("\n" + "=" * 70)
    print("Available Audio Input Devices:")
    print("=" * 70)
    
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"\nDevice {i}: {info['name']}")
            print(f"  Channels: {info['maxInputChannels']}")
            print(f"  Sample Rate: {info['defaultSampleRate']}")
    
    audio.terminate()
    print()


def test_microphone_levels(device_index=None, duration=10):
    """
    Test microphone and show audio levels in real-time.
    
    Args:
        device_index: Specific device index to test (None for default)
        duration: How long to test (seconds)
    """
    audio = pyaudio.PyAudio()
    
    # Open stream
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=16000,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=1024
    )
    
    print("\n" + "=" * 70)
    print("🎤 Microphone Level Test")
    print("=" * 70)
    print(f"\nTesting for {duration} seconds...")
    print("Speak into your microphone!")
    print()
    
    max_rms = 0
    start_time = time.time()
    
    try:
        while time.time() - start_time < duration:
            # Read audio
            data = stream.read(1024, exception_on_overflow=False)
            audio_array = np.frombuffer(data, dtype=np.int16)
            rms = np.sqrt(np.mean(audio_array**2))
            
            # Track max
            if rms > max_rms:
                max_rms = rms
            
            # Visual meter
            bar_length = int(rms / 100)
            bar = "█" * min(bar_length, 50)
            
            # Color based on level
            if rms > 1000:
                status = "🟢 LOUD"
            elif rms > 500:
                status = "🟡 GOOD"
            elif rms > 100:
                status = "🟠 QUIET"
            else:
                status = "🔴 SILENT"
            
            print(f"\rLevel: {int(rms):5d} {status} {bar:50s}", end="")
            
    except KeyboardInterrupt:
        print("\n\nTest stopped by user")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
    
    print("\n\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)
    print(f"Maximum RMS: {int(max_rms)}")
    print()
    print("Recommended thresholds based on your max level:")
    print(f"  Very sensitive: {int(max_rms * 0.1)}")
    print(f"  Sensitive: {int(max_rms * 0.2)}")
    print(f"  Normal: {int(max_rms * 0.3)}")
    print(f"  Less sensitive: {int(max_rms * 0.5)}")
    print()
    print("Use these values for 'silence_threshold' in AudioRecorder")
    print("=" * 70)


def main():
    """Run microphone tests."""
    print("\n" + "=" * 70)
    print("🎤 Microphone Test Utility")
    print("=" * 70)
    
    # List devices
    list_audio_devices()
    
    # Get device choice
    device = input("Enter device number to test (or press Enter for default): ").strip()
    device_index = int(device) if device else None
    
    # Test duration
    duration_str = input("Test duration in seconds (default 10): ").strip()
    duration = int(duration_str) if duration_str else 10
    
    # Run test
    test_microphone_levels(device_index, duration)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
