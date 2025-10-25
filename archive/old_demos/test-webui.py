"""FastAPI server for Reachy Mini move controller UI."""

import asyncio
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

# Import all rhythmic motion components so they are available for exec()
from reachy_mini_dances_library.collection.dance import AVAILABLE_MOVES
from reachy_mini_dances_library.rhythmic_motion import *

# Load environment variables from .env file
load_dotenv()

# ─────────────────────── CONFIGURATION ───────────────────────
reachy_instance: Optional[ReachyMini] = None
openai_client: Optional[OpenAI] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global reachy_instance, openai_client
    print("🤖 Initializing Reachy Mini...")
    try:
        reachy_instance = ReachyMini()
        reachy_instance.__enter__()
        print("✅ Reachy Mini initialized")
    except Exception as e:
        print(f"⚠️ Could not connect to Reachy Mini: {e}")
        print("📝 Running in demo mode without robot connection")
        reachy_instance = None
    
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    
    # Try custom endpoint first, fallback to OpenAI
    try:
        if base_url and base_url != "https://llm.your.url/v1":
            # Try custom endpoint
            openai_client = OpenAI(api_key=api_key, base_url=base_url)
            # Test the connection
            openai_client.models.list()
            print(f"✅ Custom OpenAI endpoint initialized: {base_url}")
        else:
            raise Exception("Using OpenAI directly")
    except Exception as e:
        try:
            # Fallback to real OpenAI API
            openai_client = OpenAI(api_key=api_key)
            # Test the connection
            openai_client.models.list()
            print("✅ OpenAI API initialized (direct)")
        except Exception as e2:
            print(f"⚠️ OpenAI initialization failed: {e2}")
            openai_client = None
    
    yield
    print("🛑 Shutting down...")
    if reachy_instance:
        try:
            reachy_instance.__exit__(None, None, None)
        except:
            pass


app = FastAPI(lifespan=lifespan)
STATIC_DIR = Path(__file__).parent
STATIC_DIR.mkdir(exist_ok=True)


class MoveRequest(BaseModel):
    move_name: str
    duration_beats: Optional[float] = None
    parameters: Optional[dict] = None


class ManualControlRequest(BaseModel):
    head_pitch: float = 0.0
    head_roll: float = 0.0
    head_yaw: float = 0.0
    head_x: float = 0.0
    head_y: float = 0.0
    head_z: float = 0.0
    antenna_left: float = 0.0
    antenna_right: float = 0.0
    body_yaw: float = 0.0


class GenerateMoveRequest(BaseModel):
    description: str
    duration_beats: float = 4.0


class PlayGeneratedMoveRequest(BaseModel):
    """Request to execute a dynamically generated move."""

    code: str
    duration_beats: float


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/moves")
async def get_available_moves():
    moves = [
        {
            "name": name,
            "description": metadata.get("description", ""),
            "default_duration_beats": metadata.get("default_duration_beats", 4),
            "parameters": params,
        }
        for name, (_, params, metadata) in AVAILABLE_MOVES.items()
    ]
    return {"moves": moves}


async def _execute_move(move_func, duration, params):
    """Generic helper to execute a move function over time."""
    start_time = time.time()
    beat_frequency = 1.0
    while True:
        elapsed = time.time() - start_time
        t_beats = elapsed * beat_frequency
        if t_beats >= duration:
            break
        result = move_func(t_beats, **params) if params else move_func(t_beats)

        # Handle both plain MoveOffsets and tuple (MoveOffsets, body_yaw)
        if isinstance(result, tuple):
            offsets, body_yaw = result
        else:
            offsets = result
            body_yaw = 0.0

        head_pose = create_head_pose(
            pitch=np.rad2deg(offsets.orientation_offset[0]),
            roll=np.rad2deg(offsets.orientation_offset[1]),
            yaw=np.rad2deg(offsets.orientation_offset[2]),
            x=offsets.position_offset[0] * 1000,
            y=offsets.position_offset[1] * 1000,
            z=offsets.position_offset[2] * 1000,
            mm=True,
            degrees=True,
        )

        if reachy_instance:
            reachy_instance.goto_target(
                head=head_pose,
                antennas=[offsets.antennas_offset[0], offsets.antennas_offset[1]],
                body_yaw=body_yaw,
                duration=0.05,
            )
        await asyncio.sleep(0.05)


@app.post("/api/moves/play")
async def play_move(request: MoveRequest):
    if not reachy_instance:
        # In demo mode, just simulate the move
        await asyncio.sleep(2)  # Simulate move duration
        return {"status": "success (demo mode)", "move": request.move_name}
    
    if request.move_name not in AVAILABLE_MOVES:
        raise HTTPException(status_code=404, detail=f"Move '{request.move_name}' not found")
    try:
        move_func, default_params, metadata = AVAILABLE_MOVES[request.move_name]
        params = {**default_params, **(request.parameters or {})}
        duration = request.duration_beats or metadata.get("default_duration_beats", 4)
        await _execute_move(move_func, duration, params)
        return {"status": "success", "move": request.move_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _ease(t: float) -> float:
    """Smoothing function for choreographed transitions."""
    t_clipped = np.clip(t, 0.0, 1.0)
    return t_clipped * t_clipped * (3 - 2 * t_clipped)


@app.post("/api/moves/play-generated")
async def play_generated_move(request: PlayGeneratedMoveRequest):
    """Executes Python code for a move received from the client."""
    if not reachy_instance:
        # In demo mode, just simulate the move
        await asyncio.sleep(2)  # Simulate move duration
        return {"status": "success (demo mode)", "move": "generated_move"}

    try:
        # Find the function name in the provided code
        match = re.search(r"def\s+(\w+)\s*\(", request.code)
        if not match:
            raise ValueError("Could not find function definition in code.")
        func_name = match.group(1)

        # Execute the code in a controlled namespace
        # All rhythmic_motion functions are already imported globally
        # Include the ease function for choreographed moves
        exec_namespace = {"ease": _ease}
        exec(request.code, {**globals(), "ease": _ease}, exec_namespace)

        move_func = exec_namespace.get(func_name)
        if not callable(move_func):
            raise ValueError(f"Function '{func_name}' not found after executing code.")

        # Execute the move without parameters
        await _execute_move(move_func, request.duration_beats, params=None)

        return {"status": "success", "move": func_name}
    except Exception as e:
        print(f"Error playing generated move: {e}")
        raise HTTPException(status_code=400, detail=f"Execution Error: {e}")


@app.post("/api/manual-control")
async def manual_control(request: ManualControlRequest):
    if not reachy_instance:
        # In demo mode, just return success
        return {"status": "success (demo mode)"}
    
    try:
        head_pose = create_head_pose(
            pitch=request.head_pitch,
            roll=request.head_roll,
            yaw=request.head_yaw,
            x=request.head_x,
            y=request.head_y,
            z=request.head_z,
            mm=True,
            degrees=True,
        )
        reachy_instance.set_target(
            head=head_pose,
            antennas=[request.antenna_left, request.antenna_right],
            body_yaw=np.deg2rad(request.body_yaw),
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_demo_move(description, duration, timestamp):
    """Generate varied demo moves based on description keywords."""
    desc = description.lower()
    
    # Keywords for different move types
    if any(word in desc for word in ['shy', 'peek', 'cautious', 'nervous']):
        return f'''def move_shy_peek_{timestamp}(t_beats):
    # Shy peek move: {description}
    # Slow cautious movement with pauses
    amplitude_yaw = 0.3
    amplitude_pitch = 0.15
    subcycles = 0.5  # Slower movement
    
    # Shy yaw movement (left-right peek)
    yaw = atomic_yaw(t_beats, OscillationParams(amplitude_yaw, subcycles, 0.0, "sin"))
    
    # Slight downward tilt (shy behavior)
    pitch = atomic_pitch(t_beats, OscillationParams(amplitude_pitch, subcycles * 0.7, 0.25, "sin"))
    
    # Subtle antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.4, subcycles * 1.5))
    
    return combine_offsets([yaw, pitch, antennas])'''
    
    elif any(word in desc for word in ['happy', 'excited', 'bouncing', 'energetic', 'joy']):
        return f'''def move_happy_bounce_{timestamp}(t_beats):
    # Happy bouncing move: {description}
    # Energetic multi-axis movement
    amplitude_z = 0.03  # Up-down bounce
    amplitude_pitch = 0.25
    subcycles_fast = 1.5  # Faster movement
    
    # Bouncing z movement
    z_bounce = atomic_z_pos(t_beats, OscillationParams(amplitude_z, subcycles_fast, 0.0, "sin"))
    
    # Happy nodding
    pitch = atomic_pitch(t_beats, OscillationParams(amplitude_pitch, subcycles_fast * 0.8, 0.0, "sin"))
    
    # Excited antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["both"](t_beats, OscillationParams(0.9, subcycles_fast))
    
    return combine_offsets([z_bounce, pitch, antennas])'''
    
    elif any(word in desc for word in ['sleepy', 'slow', 'tired', 'sway', 'gentle']):
        return f'''def move_sleepy_sway_{timestamp}(t_beats):
    # Sleepy swaying move: {description}
    # Slow gentle movement
    amplitude_roll = 0.2
    amplitude_y = 0.02  # Side sway
    subcycles_slow = 0.3  # Very slow
    
    # Gentle roll sway
    roll = atomic_roll(t_beats, OscillationParams(amplitude_roll, subcycles_slow, 0.0, "sin"))
    
    # Side-to-side position sway
    y_sway = atomic_y_pos(t_beats, OscillationParams(amplitude_y, subcycles_slow, 0.25, "sin"))
    
    # Slow antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.3, subcycles_slow))
    
    return combine_offsets([roll, y_sway, antennas])'''
    
    elif any(word in desc for word in ['shake', 'no', 'dramatic', 'head shake', 'refuse']):
        return f'''def move_dramatic_shake_{timestamp}(t_beats):
    # Dramatic head shake move: {description}
    # Strong yaw movement with attitude
    amplitude_yaw = 0.4
    subcycles = 1.2  # Medium-fast
    
    # Strong yaw shake
    yaw = atomic_yaw(t_beats, OscillationParams(amplitude_yaw, subcycles, 0.0, "triangle"))
    
    # Slight pitch for emphasis
    pitch = atomic_pitch(t_beats, OscillationParams(0.1, subcycles * 0.5, 0.5, "triangle"))
    
    # Emphatic antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["both"](t_beats, OscillationParams(0.8, subcycles))
    
    return combine_offsets([yaw, pitch, antennas])'''
    
    elif any(word in desc for word in ['nod', 'yes', 'agree', 'approval', 'up', 'down']):
        return f'''def move_enthusiastic_nod_{timestamp}(t_beats):
    # Enthusiastic nodding move: {description}
    # Strong pitch movement
    amplitude_pitch = 0.35
    subcycles = 1.0
    
    # Strong pitch nod
    pitch = atomic_pitch(t_beats, OscillationParams(amplitude_pitch, subcycles, 0.0, "sin"))
    
    # Supporting z movement for emphasis
    z_move = atomic_z_pos(t_beats, OscillationParams(0.015, subcycles, 0.0, "sin"))
    
    # Active antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.7, subcycles))
    
    return combine_offsets([pitch, z_move, antennas])'''
    
    elif any(word in desc for word in ['curious', 'look', 'search', 'explore', 'around']):
        return f'''def move_curious_look_{timestamp}(t_beats):
    # Curious looking move: {description}
    # Multi-axis exploration movement
    amplitude_yaw = 0.3
    amplitude_pitch = 0.2
    subcycles_yaw = 0.8
    subcycles_pitch = 0.6
    
    # Curious yaw scanning
    yaw = atomic_yaw(t_beats, OscillationParams(amplitude_yaw, subcycles_yaw, 0.0, "sin"))
    
    # Pitch variation for depth
    pitch = atomic_pitch(t_beats, OscillationParams(amplitude_pitch, subcycles_pitch, 0.3, "sin"))
    
    # Alert antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.6, subcycles_yaw * 1.2))
    
    return combine_offsets([yaw, pitch, antennas])'''
    
    else:
        # Default: complex multi-axis movement
        return f'''def move_expressive_{timestamp}(t_beats):
    # Expressive move: {description}
    # Multi-axis coordinated movement
    amplitude_pitch = 0.2
    amplitude_roll = 0.15
    amplitude_yaw = 0.25
    subcycles = 0.8
    
    # Coordinated rotation
    pitch = atomic_pitch(t_beats, OscillationParams(amplitude_pitch, subcycles, 0.0, "sin"))
    roll = atomic_roll(t_beats, OscillationParams(amplitude_roll, subcycles, 0.25, "sin"))
    yaw = atomic_yaw(t_beats, OscillationParams(amplitude_yaw, subcycles * 0.7, 0.5, "sin"))
    
    # Coordinated antenna movement
    antennas = AVAILABLE_ANTENNA_MOVES["both"](t_beats, OscillationParams(0.7, subcycles))
    
    return combine_offsets([pitch, roll, yaw, antennas])'''


@app.post("/api/moves/generate")
async def generate_move(request: GenerateMoveRequest):
    if not openai_client:
        # Generate varied demo moves based on description keywords
        demo_code = generate_demo_move(request.description, request.duration_beats, int(time.time()))
        return {"status": "success (demo mode)", "code": demo_code}

    prompt = f"""You are an expert at creating expressive dance move functions for the Reachy Mini robot using its rhythmic motion library.

## Core Requirements

1. **Function Signature**: Create a single Python function that takes only `t_beats` as a parameter (continuous time in beats, increases by 1 every beat).

2. **Default Parameters**: All configuration must be defined as local variables at the function start, with reasonable physical defaults:
   - Amplitudes in radians (typically 0.1–0.5 rad / ~6–30°)
   - Distances in meters (typically 0.01–0.05 m)
   - `subcycles_per_beat` (typically 0.25–1.0 for rhythmic, 0.5 for transient)
   - Waveform choices: `"sin"` (smooth), `"triangle"` (sharp), or `"square"` (stiff)

3. **Return Value**: 
   - **IMPORTANT**: ALWAYS use `combine_offsets([...])` to merge all motion components into a single MoveOffsets object.
   - **Simple case**: Return `combine_offsets([motion1, motion2, ...])` for head-only moves.
   - **With body rotation**: Return a tuple: `(combine_offsets([...]), body_yaw_value)` where `body_yaw_value` is a float in radians.

4. **Output Format**: Provide ONLY the raw Python function code—no markdown, no explanations, no imports.

## CRITICAL: Combining Motions

You MUST always wrap individual motion components into `MoveOffsets` objects before combining them. Do NOT try to add floats or raw motion values directly.

**WRONG:**
```python
x_motion = transient_motion(t_beats, TransientParams(...))
base = MoveOffsets(np.array([x_motion, 0, 0]), np.zeros(3), np.zeros(2))
combined = base + x_motion  # ❌ ERROR: Can't add float to MoveOffsets
```

**CORRECT:**
```python
x_motion = transient_motion(t_beats, TransientParams(...))
base = MoveOffsets(np.array([x_motion, 0, 0]), np.zeros(3), np.zeros(2))
antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(...))
return combine_offsets([base, antennas])  # ✅ Properly combined
```

## Available Building Blocks

### Atomic Motion Functions
```
atomic_pitch(t_beats, OscillationParams(...))    # Nod up/down
atomic_roll(t_beats, OscillationParams(...))     # Tilt side-to-side
atomic_yaw(t_beats, OscillationParams(...))      # Turn left/right
atomic_x_pos(t_beats, OscillationParams(...))    # Forward/backward translation
atomic_y_pos(t_beats, OscillationParams(...))    # Left/right sway
atomic_z_pos(t_beats, OscillationParams(...))    # Up/down bounce
```

### Parameter Classes
```
OscillationParams(amplitude, subcycles_per_beat, phase_offset=0.0, waveform="sin")
  - amplitude: float (radians for rotation, meters for translation)
  - subcycles_per_beat: float (cycles per beat; 1.0 = once per beat)
  - phase_offset: float (normalized 0–1, shifts by fraction of cycle)
  - waveform: str ("sin", "triangle", "square")

TransientParams(amplitude, duration_in_beats=0.3, delay_beats=0.0, repeat_every=1.0)
  - For sharp, percussive motions (pecks, twitches, recoils)
  - Returns a scalar value (float) for position offset
  - Call: transient_motion(t_beats, TransientParams(...))
```

### Antenna Control
```
AVAILABLE_ANTENNA_MOVES[antenna_move_name](t_beats, OscillationParams(...))
  - Options: "wiggle" (simple oscillation), "both" (coordinated pair)
  - Typical antenna_amplitude_rad: 0.7–0.9 rad (~40–50°)
  - Returns a MoveOffsets object for antennas
```

### Combining Motions
```
combine_offsets([motion1, motion2, ...])
  - ALWAYS use this to merge multiple motion components
  - Input: List of MoveOffsets objects
  - Output: Single merged MoveOffsets object
```

### MoveOffsets Construction
```
MoveOffsets(position_offset, orientation_offset, antennas_offset)
  - position_offset: np.array([x, y, z]) in meters
  - orientation_offset: np.array([pitch, roll, yaw]) in radians
  - antennas_offset: np.array([left, right]) in radians
```

## Sequencing & Choreography

You can create choreographed sequences where different actions occur in distinct phases over the move's duration.

### Phase-based Sequencing Pattern

Use `t_in_period = t_beats % period` and conditional logic to define phases:

```python
def move_choreographed_example(t_beats):
    period = 10.0  # Total duration in beats
    t_in_period = t_beats % period
    pos, ori = np.zeros(3), np.zeros(3)
    
    # Define phase boundaries
    if t_in_period < 2.0:  # Phase 1: Look left
        phase1_time = t_in_period / 2.0
        yaw = -0.5 * ease(phase1_time)
        ori[2] = yaw
    elif t_in_period < 5.0:  # Phase 2: Rotate body while maintaining yaw
        phase2_time = (t_in_period - 2.0) / 3.0
        pitch = 0.3 * np.sin(phase2_time * np.pi)
        ori[1] = pitch
    elif t_in_period < 7.0:  # Phase 3: Look right with opposite yaw
        phase3_time = (t_in_period - 5.0) / 2.0
        yaw = 0.5 * ease(phase3_time)
        ori[2] = yaw
    else:  # Phase 4: Return to neutral
        phase4_time = (t_in_period - 7.0) / 3.0
        ori = np.array([0, 0, 0.5 * (1 - ease(phase4_time))])
    
    base = MoveOffsets(pos, ori, np.zeros(2))
    antenna_params = OscillationParams(0.5, 1.0)
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, antenna_params)
    return combine_offsets([base, antennas])
```

### Helper Function: `ease(t)`

A smoothing function is **automatically available** for clean transitions between phases:

```python
ease(t)  # Smooth hermite interpolation, pre-defined globally
# Just call it directly, no need to define it
```

### Sequencing Tips

- **Define `period`**: Total duration of the full choreography in beats.
- **Calculate `t_in_period`**: Normalizes time within the cycle for phase detection.
- **Use phase boundaries**: Compare `t_in_period` to define when each action occurs.
- **Apply easing**: Use `ease(t)` to smooth transitions between phases for natural motion.
- **Maintain state across phases**: Initialize `pos` and `ori` as `np.zeros(3)`, update them conditionally.
- **Always combine with combine_offsets()**: Never add motion objects directly, always use `combine_offsets([...])`.
- **Always add antennas**: Include antenna motion for expressiveness even during choreographed sequences.

## Design Patterns from Library

- **Smooth continuous motions**: Use `OscillationParams` with `waveform="sin"`, adjust `subcycles_per_beat` for speed.
- **Sharp percussive motions**: Use `TransientParams` with `transient_motion()`, set `repeat_every` for rhythm.
- **Phase-offset layering**: Offset different axes by 0.25–0.5 to create complex spirals or coordinated patterns.
- **Multi-axis combinations**: Combine `pitch` + `roll` for circular motions, `yaw` + `sway` for lateral spirals, etc.
- **Antenna control**: Include antenna motion for expressive moves (use `"both"` for coordinated, `"wiggle"` for subtle), or set antennas to 0 for still movement.

## Example Patterns

**Simple rhythmic nod:**
```python
def move_custom_nod(t_beats):
    amplitude_rad = 0.2
    base = atomic_pitch(t_beats, OscillationParams(amplitude_rad, 1.0, 0.0, "sin"))
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.8, 1.0, 0.0, "sin"))
    return combine_offsets([base, antennas])
```

**Transient peck:**
```python
def move_custom_peck(t_beats):
    amplitude_m = 0.02
    repeat_every = 1.0
    x_peck = transient_motion(t_beats, TransientParams(amplitude_m, 0.3, repeat_every=repeat_every))
    base = MoveOffsets(np.array([x_peck, 0, 0]), np.zeros(3), np.zeros(2))
    antennas = AVAILABLE_ANTENNA_MOVES["both"](t_beats, OscillationParams(0.5, 1.0))
    return combine_offsets([base, antennas])
```

**Multi-axis spiral:**
```python
def move_custom_spiral(t_beats):
    roll = atomic_roll(t_beats, OscillationParams(0.15, 0.5, 0.0, "sin"))
    pitch = atomic_pitch(t_beats, OscillationParams(0.15, 0.25, 0.25, "sin"))
    yaw = atomic_yaw(t_beats, OscillationParams(0.15, 0.125, 0.5, "sin"))
    antennas = AVAILABLE_ANTENNA_MOVES["wiggle"](t_beats, OscillationParams(0.7, 1.0))
    return combine_offsets([roll, pitch, yaw, antennas])
```

## Physical Constraints

- Keep rotational amplitudes **under 0.6 rad** (~35°) for stability.
- Keep translational amplitudes **under 0.06 m** (~6 cm) to avoid mechanical strain.
- Use `subcycles_per_beat ≥ 0.125` for smooth playback; avoid values that are too small.
- Phase offsets should be multiples of 0.25 for clean synchronization (e.g., 0.0, 0.25, 0.5, 0.75).

## Interpret User Requests

- **"Subtle / smooth"** → Use `"sin"` waveform, lower amplitudes, `subcycles_per_beat ≤ 0.5`.
- **"Sharp / snappy"** → Use `"triangle"` waveform, or `TransientParams` for percussive hits.
- **"Energetic / complex"** → Combine multiple axes with different `subcycles_per_beat` values and phase offsets.
- **"Sequential / choreographed"** → Use phase-based sequencing with `t_in_period` and conditional logic.
- **"Duration in beats"** → Structure your motion frequency and phase boundaries to fit naturally within that timeframe.

USER REQUEST: A move described as '{request.description}' over {request.duration_beats} beats.
"""

    model = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Use GPT-4o-mini as default
    # If using custom model name, fallback to OpenAI model
    if model not in ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]:
        model = "gpt-4o-mini"
    
    try:
        response = openai_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1500,
        )
        code = response.choices[0].message.content or ""
        # Clean up potential markdown formatting from the response
        cleaned_code = re.sub(r"```python\n|```", "", code).strip()
        return {"status": "success", "code": cleaned_code}
    except Exception as e:
        print(f"OpenAI generation error: {e}")
        # Fallback to demo mode if OpenAI fails
        demo_code = generate_demo_move(request.description, request.duration_beats, int(time.time()))
        return {"status": "success (demo mode)", "code": demo_code}


@app.post("/api/reset")
async def reset_robot():
    if not reachy_instance:
        # In demo mode, just return success
        return {"status": "success (demo mode)"}
    
    try:
        reachy_instance.goto_target(
            head=create_head_pose(),
            antennas=[0, 0],
            body_yaw=0,
            duration=1.0,
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("test-webui:app", host="0.0.0.0", port=8001, reload=True)
