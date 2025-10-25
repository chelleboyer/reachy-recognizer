"""
Voice Quality Test - Compare TTS backends

Tests OpenAI TTS with various voices to find the best quality
for Reachy's greeting system.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("\n" + "="*70)
print("🎤 Reachy Voice Quality Test")
print("="*70)

# Check for OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    print("   Please set it in your .env file or environment")
    exit(1)

print(f"✓ OpenAI API key found (length: {len(api_key)})")

# Import OpenAI
try:
    from openai import AsyncOpenAI
    print("✓ OpenAI library available")
except ImportError:
    print("❌ OpenAI library not installed")
    print("   Install with: pip install openai")
    exit(1)

# Initialize client
client = AsyncOpenAI(api_key=api_key)

# Test greetings
test_greetings = [
    ("Welcome back, Sarah!", "warm greeting"),
    ("Hello there! I'm Reachy. Nice to meet you!", "friendly introduction"),
    ("Hey Sarah, glad you're here!", "enthusiastic greeting"),
    ("Good morning! Great to see you.", "professional greeting"),
    ("Oh hello! Are you new here?", "curious greeting"),
]

# Available voices
voices = {
    'alloy': 'Neutral, balanced (good for professional)',
    'echo': 'Male, clear',
    'fable': 'British male, expressive',
    'onyx': 'Deep male, authoritative', 
    'nova': '⭐ Warm female, engaging (RECOMMENDED)',
    'shimmer': 'Bright female, energetic'
}


async def test_voice(voice_name: str, text: str, description: str, index: int):
    """Generate speech sample with specific voice."""
    print(f"\n{index}. Testing '{voice_name}' voice")
    print(f"   Description: {voices[voice_name]}")
    print(f"   Text: \"{text}\"")
    print(f"   Context: {description}")
    
    try:
        # Generate speech
        response = await client.audio.speech.create(
            model="tts-1",  # Fast model for real-time
            voice=voice_name,
            input=text
        )
        
        # Save to file
        output_dir = Path("voice_samples")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"sample_{index}_{voice_name}.mp3"
        filepath = output_dir / filename
        
        # Write audio data
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        size_kb = len(response.content) / 1024
        print(f"   ✓ Generated: {filepath} ({size_kb:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False


async def main():
    """Run voice quality tests."""
    
    print("\n" + "-"*70)
    print("Generating voice samples...")
    print("-"*70)
    
    # Test recommended voices with different greetings
    test_cases = [
        ('nova', test_greetings[0][0], test_greetings[0][1]),      # Warm greeting
        ('nova', test_greetings[1][0], test_greetings[1][1]),      # Friendly intro
        ('shimmer', test_greetings[2][0], test_greetings[2][1]),   # Enthusiastic
        ('alloy', test_greetings[3][0], test_greetings[3][1]),     # Professional
        ('nova', test_greetings[4][0], test_greetings[4][1]),      # Curious
    ]
    
    results = []
    for i, (voice, text, desc) in enumerate(test_cases, 1):
        success = await test_voice(voice, text, desc, i)
        results.append(success)
        await asyncio.sleep(0.5)  # Small delay between requests
    
    # Summary
    print("\n" + "="*70)
    print("📊 Test Summary")
    print("="*70)
    
    successful = sum(results)
    print(f"\nGenerated: {successful}/{len(results)} samples")
    print(f"Location: voice_samples/")
    
    print("\n🎧 Listen to the samples to compare quality!")
    print("\n💡 Recommendations:")
    print("   • 'nova' - Best for warm, natural greetings (DEFAULT)")
    print("   • 'shimmer' - Great for excited/playful greetings")
    print("   • 'alloy' - Good for calm/professional tone")
    
    print("\n✓ Voice quality test complete!")
    print("\nThese voices are MUCH better than pyttsx3!")
    print("OpenAI TTS provides natural, engaging speech perfect for Reachy.")


if __name__ == "__main__":
    asyncio.run(main())
