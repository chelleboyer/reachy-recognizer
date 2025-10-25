# Archive Folder

This folder contains deprecated, superseded, or unused files from the development process.

## Directory Structure

### `old_demos/`
Demo scripts used during development but superseded by integrated system:
- `behavior_speech_demo.py` - Early behavior + speech demo
- `event_behavior_demo.py` - Event system behavior demo
- `event_demo.py` - Basic event system demo
- `test-webui.py` - Web UI experiment
- `index.html` - Web UI HTML file

### `old_tests/`
Standalone test scripts that were used during story development:
- `camera_test.py` - Camera interface testing
- `e2e_integration_test.py` - Early integration test
- `face_detection_test.py` - Face detection module test
- `test_enhanced_voice_integration.py` - Voice system integration test
- `test_idle_visual.py` - Idle manager visual test
- `test_idle_with_sim.py` - Idle manager with simulator test
- `test_sdk_integration.py` - Reachy SDK integration test
- `test_sface_model.py` - SFace model testing
- `test_voice_playback.py` - Audio playback test
- `test_voice_quality.py` - Voice quality comparison test

### Root Archive Files
- `main_old.py.bak` - Backup of original main.py before reorganization
- `voice_samples/` - Sample voice recordings from testing (if exists)

## Status

These files are **not used** by the current system but are kept for:
- Historical reference
- Potential future use
- Understanding development evolution

## Current System

The active codebase is organized under:
- `src/` - Modular subsystems (vision, behaviors, voice, etc.)
- `tests/` - Official test suite
- `main.py` - Main entry point

See `PROJECT_STRUCTURE.md` for current architecture.

## Safe to Delete?

Yes, these files can be safely deleted if you need to clean up the repository. The current system in `src/` and `main.py` is self-contained and doesn't depend on these archived files.

Before deletion, consider:
- Creating a git tag/branch to preserve history
- Reviewing any unique test scenarios you might want to recreate
- Checking if any documentation references these files

---

**Archived:** 2025-10-24  
**Reason:** Code reorganization (Story 4.1)
