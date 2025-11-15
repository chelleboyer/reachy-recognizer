"""
Pytest configuration for reachy-recognizer tests.

This file ensures that the src module is properly importable
and sets up common test fixtures.
"""

import sys
from pathlib import Path

# Add project root to Python path so 'src' can be imported
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
