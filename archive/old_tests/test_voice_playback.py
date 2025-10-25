"""
Voice Playback Test - Listen to OpenAI TTS quality

Generates and plays voice samples so you can hear the quality.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

print("\n" + "="*70)
print("🎤 Reachy Voice Playback Test")
print("="*70)

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)

print(f"✓ OpenAI API key found")

# Import libraries
try:
    from openai import AsyncOpenAI
    print("✓ OpenAI library available")
except ImportError:
    print("❌ OpenAI library not installed")
    exit(1)

try:
    from pydub import AudioSegment
    from pydub.playback import play
    print("✓ Audio playback available")
    PLAYBACK_AVAILABLE = True
except ImportError:
    print("⚠ pydub not installed - will save files only")
    print("  Install with: pip install pydub")
    PLAYBACK_AVAILABLE = False

# Initialize client
client = AsyncOpenAI(api_key=api_key)

# Test greetings with different voices
test_cases = [
    {
        'voice': 'nova',
        'text': 'Welcome back, Sarah! Good to see you!',
        'description': '⭐ NOVA - Warm, engaging (RECOMMENDED)'
    },
    {
        'voice': 'shimmer', 
        'text': 'Hey Sarah, glad you\'re here!',
        'description': 'SHIMMER - Bright, energetic'
    },
    {
        'voice': 'alloy',
        'text': 'Hello Sarah, nice to see you.',
        'description': 'ALLOY - Neutral, professional'
    },
    {
        'voice': 'nova',
        'text': 'Hello there! I\'m Reachy. Nice to meet you!',
        'description': '⭐ NOVA - Unknown person greeting'
    },
]


async def generate_and_play(voice: str, text: str, description: str, index: int):
    """Generate and play audio sample."""
    print(f"\n{'-'*70}")
    print(f"{index}. {description}")
    print(f"   Text: \"{text}\"")
    print(f"   Generating...")
    
    try:
        # Generate speech
        start_time = time.time()
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        latency = time.time() - start_time
        
        # Save to file
        output_dir = Path("voice_samples")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"demo_{index}_{voice}.mp3"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size_kb = len(response.content) / 1024
        print(f"   ✓ Generated in {latency:.2f}s ({size_kb:.1f} KB)")
        print(f"   📁 Saved: {filepath}")
        
        # Play audio
        if PLAYBACK_AVAILABLE:
            print(f"   🔊 Playing...")
            audio = AudioSegment.from_mp3(str(filepath))
            play(audio)
            print(f"   ✓ Playback complete")
        else:
            print(f"   ℹ Open {filepath} to listen")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


async def main():
    """Run voice playback test."""
    
    print("\n" + "="*70)
    print("Generating and playing voice samples...")
    print("="*70)
    print("\nYou'll hear 4 different greeting samples.")
    print("Listen for naturalness, emotion, and engagement!")
    
    if not PLAYBACK_AVAILABLE:
        print("\n⚠ Note: Audio files will be saved but not played automatically")
        print("  Open voice_samples/*.mp3 files to listen")
    
    input("\nPress Enter to start...")
    
    results = []
    for i, test in enumerate(test_cases, 1):
        success = await generate_and_play(
            test['voice'],
            test['text'],
            test['description'],
            i
        )
        results.append(success)
        
        if i < len(test_cases) and PLAYBACK_AVAILABLE:
            print(f"\n   ⏸ Pausing 2 seconds before next sample...")
            await asyncio.sleep(2)
    
    # Summary
    print("\n" + "="*70)
    print("📊 Summary")
    print("="*70)
    
    successful = sum(results)
    print(f"\nGenerated: {successful}/{len(results)} samples")
    print(f"Location: voice_samples/")
    
    print("\n💡 Comparison:")
    print("   Current (pyttsx3):  Robotic, mechanical         Quality: 5/10")
    print("   OpenAI (nova):      Natural, warm, engaging    Quality: 9/10")
    print("   OpenAI (shimmer):   Bright, energetic          Quality: 9/10")
    
    print("\n✨ This is the voice quality Reachy will have!")
    print("   Much more natural and engaging than pyttsx3.")
    
    print("\n✓ Voice playback test complete!")


if __name__ == "__main__":
    asyncio.run(main())
