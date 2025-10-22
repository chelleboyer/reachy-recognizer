"""
Unit Tests for Story 3.2: Text-to-Speech Integration

Tests the TTSManager class, greeting phrase generation, and TTS functionality.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import queue
from tts_module import (
    TTSManager,
    GreetingType,
    get_greeting,
    GREETINGS
)


class TestGreetingPhrases(unittest.TestCase):
    """Test greeting phrase generation (AC: 2)."""
    
    def test_greeting_templates_exist(self):
        """Test that all required greeting templates are defined."""
        self.assertIn('recognized', GREETINGS)
        self.assertIn('unknown', GREETINGS)
        self.assertIn('departed', GREETINGS)
        self.assertIn('general', GREETINGS)
        
        # Each type should have at least one phrase
        for greeting_type, phrases in GREETINGS.items():
            self.assertIsInstance(phrases, list)
            self.assertGreater(len(phrases), 0, 
                             f"{greeting_type} should have at least one phrase")
    
    def test_recognized_greeting_with_name(self):
        """Test recognized person greeting with name."""
        greeting = get_greeting('recognized', 'Alice', random_choice=False)
        self.assertIn('Alice', greeting)
        self.assertTrue(any(word in greeting.lower() for word in ['hello', 'hi', 'hey']))
    
    def test_unknown_greeting_no_name(self):
        """Test unknown person greeting (no name)."""
        greeting = get_greeting('unknown', random_choice=False)
        self.assertIn("I don't think we've met", greeting)
    
    def test_departed_greeting_with_name(self):
        """Test departed person greeting with name."""
        greeting = get_greeting('departed', 'Bob', random_choice=False)
        self.assertIn('Bob', greeting)
        self.assertTrue(any(word in greeting.lower() 
                          for word in ['goodbye', 'bye', 'see you']))
    
    def test_general_greeting(self):
        """Test general greeting."""
        greeting = get_greeting('general', random_choice=False)
        self.assertTrue(any(word in greeting.lower() 
                          for word in ['hello', 'hi', 'greetings']))
    
    def test_random_greeting_selection(self):
        """Test that random selection works."""
        # Get multiple greetings and check we get different ones
        greetings = [get_greeting('recognized', 'Test', random_choice=True) 
                    for _ in range(20)]
        
        # Should have at least 2 different greetings (with 20 samples)
        unique_greetings = len(set(greetings))
        self.assertGreater(unique_greetings, 1, 
                          "Random selection should produce variety")
    
    def test_greeting_enum_types(self):
        """Test GreetingType enum values."""
        self.assertEqual(GreetingType.RECOGNIZED.value, 'recognized')
        self.assertEqual(GreetingType.UNKNOWN.value, 'unknown')
        self.assertEqual(GreetingType.DEPARTED.value, 'departed')
        self.assertEqual(GreetingType.GENERAL.value, 'general')


class TestTTSManagerInitialization(unittest.TestCase):
    """Test TTSManager initialization (AC: 1, 6)."""
    
    @patch('tts_module.pyttsx3.init')
    def test_initialization_success(self, mock_pyttsx3_init):
        """Test successful TTS manager initialization."""
        # Mock pyttsx3 engine
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        
        # Mock voices
        mock_voice = Mock()
        mock_voice.name = "Microsoft Zira"
        mock_voice.id = "HKEY_LOCAL_MACHINE\\voice\\zira"
        mock_voice.languages = ['en']
        mock_engine.getProperty.return_value = [mock_voice]
        
        # Initialize
        tts = TTSManager(rate=160, volume=0.9)
        
        # Check initialization
        self.assertTrue(tts.engine_available)
        self.assertIsNotNone(tts.engine)
        self.assertEqual(tts.rate, 160)
        self.assertEqual(tts.volume, 0.9)
        
        # Check engine was configured
        mock_pyttsx3_init.assert_called_once()
        self.assertTrue(mock_engine.setProperty.called)
        
        # Check worker thread started
        self.assertIsNotNone(tts.worker_thread)
        self.assertTrue(tts.worker_thread.is_alive())
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_initialization_failure_graceful(self, mock_pyttsx3_init):
        """Test graceful handling of TTS initialization failure (AC: 6)."""
        # Simulate initialization failure
        mock_pyttsx3_init.side_effect = Exception("TTS not available")
        
        # Should not raise exception
        tts = TTSManager()
        
        # Should be in silent mode
        self.assertFalse(tts.engine_available)
        self.assertIsNone(tts.engine)
        
        # Should still accept speech requests (silent mode)
        result = tts.speak("Test")
        self.assertTrue(result)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_voice_configuration(self, mock_pyttsx3_init):
        """Test voice selection and configuration (AC: 3, 4)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        
        # Mock multiple voices
        zira = Mock()
        zira.name = "Microsoft Zira Desktop"
        zira.id = "zira_id"
        zira.languages = ['en_US']
        
        david = Mock()
        david.name = "Microsoft David Desktop"
        david.id = "david_id"
        david.languages = ['en_US']
        
        mock_engine.getProperty.return_value = [david, zira]
        
        # Initialize with female preference
        tts = TTSManager(rate=160, volume=0.9, voice_preference="female")
        
        # Should select Zira (female voice)
        calls = mock_engine.setProperty.call_args_list
        voice_calls = [call for call in calls if call[0][0] == 'voice']
        self.assertEqual(len(voice_calls), 1)
        self.assertEqual(voice_calls[0][0][1], "zira_id")
        
        # Should set rate and volume
        rate_calls = [call for call in calls if call[0][0] == 'rate']
        self.assertEqual(len(rate_calls), 1)
        self.assertEqual(rate_calls[0][0][1], 160)
        
        volume_calls = [call for call in calls if call[0][0] == 'volume']
        self.assertEqual(len(volume_calls), 1)
        self.assertEqual(volume_calls[0][0][1], 0.9)
        
        tts.shutdown()


class TestTTSSpeaking(unittest.TestCase):
    """Test TTS speaking functionality (AC: 2, 5)."""
    
    @patch('tts_module.pyttsx3.init')
    def test_speak_non_blocking(self, mock_pyttsx3_init):
        """Test that speak() is non-blocking (AC: 5)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Measure time to queue speech
        start = time.time()
        result = tts.speak("This is a test")
        duration = time.time() - start
        
        # Should return immediately (< 100ms)
        self.assertTrue(result)
        self.assertLess(duration, 0.1, "speak() should be non-blocking")
        
        # Speech should be queued
        self.assertEqual(tts.speeches_queued, 1)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_speak_multiple_requests(self, mock_pyttsx3_init):
        """Test queuing multiple speech requests."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Queue multiple speeches
        phrases = ["Hello", "How are you", "Goodbye"]
        for phrase in phrases:
            result = tts.speak(phrase)
            self.assertTrue(result)
        
        self.assertEqual(tts.speeches_queued, 3)
        
        # Wait for processing
        time.sleep(0.5)
        
        # All should be processed (in mock mode)
        self.assertGreater(tts.speeches_spoken, 0)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_speak_empty_text(self, mock_pyttsx3_init):
        """Test handling of empty text."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Empty string
        result = tts.speak("")
        self.assertFalse(result)
        self.assertEqual(tts.speeches_queued, 0)
        
        # Whitespace only
        result = tts.speak("   ")
        self.assertFalse(result)
        self.assertEqual(tts.speeches_queued, 0)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_speak_greeting_recognized(self, mock_pyttsx3_init):
        """Test speak_greeting for recognized person (AC: 2)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        result = tts.speak_greeting(GreetingType.RECOGNIZED, "Alice")
        self.assertTrue(result)
        self.assertEqual(tts.speeches_queued, 1)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_speak_greeting_unknown(self, mock_pyttsx3_init):
        """Test speak_greeting for unknown person (AC: 2)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        result = tts.speak_greeting(GreetingType.UNKNOWN)
        self.assertTrue(result)
        self.assertEqual(tts.speeches_queued, 1)
        
        tts.shutdown()


class TestTTSErrorHandling(unittest.TestCase):
    """Test TTS error handling (AC: 6)."""
    
    @patch('tts_module.pyttsx3.init')
    def test_speech_synthesis_error(self, mock_pyttsx3_init):
        """Test handling of speech synthesis errors."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        # Make runAndWait raise exception
        mock_engine.runAndWait.side_effect = Exception("Speech error")
        
        tts = TTSManager()
        
        # Speech should still queue
        result = tts.speak("Test")
        self.assertTrue(result)
        
        # Wait for worker to process
        time.sleep(0.5)
        
        # Error should be counted
        self.assertGreater(tts.errors, 0)
        
        # Manager should still be functional
        result = tts.speak("Another test")
        self.assertTrue(result)
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_silent_mode_operation(self, mock_pyttsx3_init):
        """Test operation in silent mode (engine unavailable)."""
        # Simulate engine failure
        mock_pyttsx3_init.side_effect = Exception("No TTS")
        
        tts = TTSManager()
        self.assertFalse(tts.engine_available)
        
        # Should still accept and process speech (silently)
        result = tts.speak("Test speech")
        self.assertTrue(result)
        self.assertEqual(tts.speeches_queued, 1)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Should mark as spoken even in silent mode
        self.assertGreater(tts.speeches_spoken, 0)
        
        tts.shutdown()


class TestTTSStatistics(unittest.TestCase):
    """Test TTS statistics tracking."""
    
    @patch('tts_module.pyttsx3.init')
    def test_statistics_tracking(self, mock_pyttsx3_init):
        """Test that statistics are tracked correctly."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Initial stats
        stats = tts.get_stats()
        self.assertEqual(stats['speeches_queued'], 0)
        self.assertEqual(stats['speeches_spoken'], 0)
        self.assertEqual(stats['errors'], 0)
        self.assertTrue(stats['engine_available'])
        
        # Queue some speeches
        tts.speak("Test 1")
        tts.speak("Test 2")
        
        stats = tts.get_stats()
        self.assertEqual(stats['speeches_queued'], 2)
        
        # Wait for processing
        time.sleep(0.5)
        
        stats = tts.get_stats()
        self.assertGreater(stats['speeches_spoken'], 0)
        
        tts.shutdown()


class TestTTSShutdown(unittest.TestCase):
    """Test TTS graceful shutdown."""
    
    @patch('tts_module.pyttsx3.init')
    def test_graceful_shutdown(self, mock_pyttsx3_init):
        """Test that TTS shuts down gracefully."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Worker thread should be running
        self.assertTrue(tts.worker_thread.is_alive())
        
        # Shutdown
        tts.shutdown()
        
        # Wait for thread to stop
        time.sleep(1.0)
        
        # Thread should be stopped
        self.assertFalse(tts.worker_thread.is_alive())
        
        # Engine should be stopped
        mock_engine.stop.assert_called_once()


# Performance benchmark (not a test)
class TestTTSPerformance(unittest.TestCase):
    """Benchmark TTS performance."""
    
    @patch('tts_module.pyttsx3.init')
    def test_initialization_time(self, mock_pyttsx3_init):
        """Benchmark initialization time (should be < 500ms)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        start = time.time()
        tts = TTSManager()
        init_time = time.time() - start
        
        print(f"\nTTS initialization time: {init_time*1000:.2f}ms")
        self.assertLess(init_time, 0.5, "Initialization should take < 500ms")
        
        tts.shutdown()
    
    @patch('tts_module.pyttsx3.init')
    def test_queuing_latency(self, mock_pyttsx3_init):
        """Benchmark speech queuing latency (should be < 10ms)."""
        mock_engine = MagicMock()
        mock_pyttsx3_init.return_value = mock_engine
        mock_engine.getProperty.return_value = []
        
        tts = TTSManager()
        
        # Measure queuing time
        latencies = []
        for i in range(10):
            start = time.time()
            tts.speak(f"Test {i}")
            latency = time.time() - start
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        print(f"\nAverage queuing latency: {avg_latency*1000:.2f}ms")
        print(f"Max queuing latency: {max_latency*1000:.2f}ms")
        
        self.assertLess(avg_latency, 0.01, "Average queuing should be < 10ms")
        self.assertLess(max_latency, 0.05, "Max queuing should be < 50ms")
        
        tts.shutdown()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
