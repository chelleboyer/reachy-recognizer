# Archive Summary - 2025-10-24

## Files Archived

Successfully moved unused files from root directory to `archive/` folder.

### Archived Demos (→ `archive/old_demos/`)
- ✅ `behavior_speech_demo.py` - Early behavior + speech integration demo
- ✅ `event_behavior_demo.py` - Event system with behavior demo
- ✅ `event_demo.py` - Basic event system testing
- ✅ `test-webui.py` - Web UI experiment
- ✅ `index.html` - Web UI HTML file

### Archived Tests (→ `archive/old_tests/`)
- ✅ `camera_test.py` - Camera interface testing
- ✅ `e2e_integration_test.py` - Early end-to-end integration
- ✅ `face_detection_test.py` - Face detection module test
- ✅ `test_enhanced_voice_integration.py` - Voice system integration test
- ✅ `test_idle_visual.py` - Idle manager visualization test
- ✅ `test_idle_with_sim.py` - Idle manager with simulator
- ✅ `test_sdk_integration.py` - Reachy SDK integration test
- ✅ `test_sface_model.py` - SFace model testing
- ✅ `test_voice_playback.py` - Audio playback testing
- ✅ `test_voice_quality.py` - Voice quality comparison

### Archived Backups (→ `archive/`)
- ✅ `main_old.py.bak` - Pre-reorganization main.py
- ✅ `voice_samples/` - Test voice recordings (if exists)

**Total Files Archived:** 13 Python files + 2 HTML files + 1 backup + 1 directory

## Clean Root Directory

Current root now contains only essential files:

### Configuration & Project Files
- `.env` - Environment variables (OpenAI API key)
- `.gitignore` - Git ignore rules
- `.python-version` - Python version specification
- `pyproject.toml` - Project dependencies
- `uv.lock` - Dependency lock file

### Documentation
- `README.md` - Main project documentation
- `PROJECT_STRUCTURE.md` - Code organization guide
- `REORGANIZATION.md` - Reorganization summary
- `SETUP.md` - Setup instructions
- `GITHUB_SETUP.md` - GitHub setup guide
- `RASPBERRY_PI_SETUP.md` - Raspberry Pi deployment guide
- `TTS_SETUP_GUIDE.md` - TTS configuration guide

### Application Entry Point
- `main.py` - Main application entry point (updated)

### Active Directories
- `src/` - Source code (modular subsystems)
- `tests/` - Official test suite
- `docs/` - Story and design documentation
- `models/` - ML model files
- `archive/` - **NEW** - Archived development files

## Benefits

✅ **Cleaner root directory** - Only essential files visible  
✅ **Preserved history** - All files saved in archive  
✅ **Clear organization** - Active vs archived code separated  
✅ **Easier navigation** - Focus on current codebase  
✅ **Documented** - Archive README explains what's there  

## Impact

- **No functional changes** - System still works the same
- **Improved maintainability** - Easier to find active code
- **Git history preserved** - All files still in version control

## Recovery

If you need any archived file:
```bash
# Copy from archive back to root
cp archive/old_tests/test_idle_with_sim.py .

# Or reference in place
python archive/old_tests/test_idle_with_sim.py
```

---

**Date:** 2025-10-24  
**Story:** 4.1 - Code Organization  
**Status:** ✅ Complete
