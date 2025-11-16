"""
Test the Gradio app locally before deploying to Hugging Face
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import gradio as gr
    print("✅ Gradio installed")
except ImportError:
    print("❌ Gradio not installed. Install with: pip install gradio")
    sys.exit(1)

try:
    import requests
    print("✅ Requests installed")
except ImportError:
    print("❌ Requests not installed. Install with: pip install requests")
    sys.exit(1)

print("\n🚀 Starting Gradio app...")
print("=" * 60)

from app import create_interface

demo = create_interface()

print("\n✅ App created successfully!")
print("📱 Opening in browser...")
print("   Press Ctrl+C to stop\n")

demo.launch(share=False, server_name="127.0.0.1", server_port=7860)
