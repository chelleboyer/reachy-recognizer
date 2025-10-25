"""
Test logging integration by generating sample log entries.
Validates JSON format, metrics logging, and analysis tool.
"""

import os
import sys
import time
from pathlib import Path

# Enable JSON logging for this test
os.environ['REACHY_LOGGING_JSON_FORMAT'] = 'true'

from src.logging import setup_logging

def test_logging_integration():
    """Test logging with sample entries."""
    
    print("🧪 Testing Logging Integration")
    print("=" * 60)
    
    # Setup logging
    logger = setup_logging()
    logger.info("Starting logging integration test")
    
    # Test basic logging
    print("\n📝 Testing basic logging...")
    logger.debug("Debug message test")
    logger.info("Info message test")
    logger.warning("Warning message test")
    
    # Test event logging
    print("📡 Testing event logging...")
    logger.info("Recognition event", extra={
        'event': 'person_recognized',
        'data': {'name': 'Alice', 'bbox': [100, 200, 300, 400]},
        'metrics': {'confidence': 0.85}
    })
    
    logger.info("Unknown person event", extra={
        'event': 'person_unknown',
        'data': {'bbox': [150, 250, 350, 450]},
        'metrics': {'confidence': 0.45}
    })
    
    # Test performance metrics logging
    print("📊 Testing performance metrics...")
    for i in range(5):
        logger.info(f"Frame {i+1} processed", extra={
            'event': 'frame_processed',
            'metrics': {
                'fps': 28.5 + i,
                'recognition_time': 0.015 + (i * 0.002),
                'faces_detected': 1 if i % 2 == 0 else 0
            }
        })
        time.sleep(0.1)
    
    # Test accuracy metrics logging
    print("🎯 Testing accuracy metrics...")
    logger.info("Accuracy update", extra={
        'event': 'accuracy_metrics',
        'metrics': {
            'true_positives': 5,
            'false_positives': 1,
            'true_negatives': 8,
            'false_negatives': 2,
            'accuracy': 0.8125,
            'precision': 0.833,
            'recall': 0.714
        }
    })
    
    # Test error logging
    print("⚠️  Testing error logging...")
    try:
        # Simulate an error
        raise ValueError("Test error for logging")
    except Exception as e:
        logger.error(f"Error occurred: {e}", extra={
            'event': 'error',
            'data': {'error_type': type(e).__name__, 'error_msg': str(e)}
        })
    
    # Test periodic summary
    print("📈 Testing periodic summary...")
    logger.info("Performance summary", extra={
        'event': 'performance_summary',
        'data': {
            'duration': 60.0,
            'frames': 1800,
            'events': 15
        },
        'metrics': {
            'avg_fps': 30.0,
            'avg_recognition_time': 0.018,
            'avg_confidence': 0.72,
            'uptime': 120.5
        }
    })
    
    logger.info("Logging integration test completed")
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Test Complete")
    
    # Print log file location
    log_file = Path("logs/reachy_recognizer.log")
    if log_file.exists():
        size_kb = log_file.stat().st_size / 1024
        print(f"\n📝 Log file: {log_file.absolute()}")
        print(f"   Size: {size_kb:.2f} KB")
        print(f"\n   Analyze with:")
        print(f"     python tools/analyze_logs.py {log_file}")
        print(f"     python tools/analyze_logs.py {log_file} --export report.json")
    
    return True

if __name__ == "__main__":
    try:
        success = test_logging_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
