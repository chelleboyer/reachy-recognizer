# Reachy Recognizer - Epic Breakdown

**Author:** Michelle
**Date:** 2025-10-22
**Project Level:** 2
**Target Scale:** 12-16 stories across 4 epics

---

## Overview

This document provides the detailed epic breakdown for Reachy Recognizer, expanding on the high-level requirements in the [PRD](./prd.md).

Each epic includes:
- Expanded goal and value proposition
- Complete story breakdown with user stories
- Acceptance criteria for each story
- Story sequencing and dependencies

**Epic Sequencing Principles:**
- Epic 1 establishes foundational infrastructure and initial functionality
- Subsequent epics build progressively, each delivering significant end-to-end value
- Stories within epics are vertically sliced and sequentially ordered
- No forward dependencies - each story builds only on previous work

---

## Epic 1: Foundation & Simulation Setup

**Goal:** Establish project infrastructure, development environment, and verify basic Reachy SIM integration with camera input working end-to-end. This epic delivers the foundational pieces needed for all subsequent development and proves the core technical approach is viable.

**Value:** Enables the team to begin development with confidence, reduces technical risk early, and provides a working baseline for iteration.

**Estimated Stories:** 4

---

### Story 1.1: Project Setup & Dependencies

As a **developer**,
I want to set up the Python project structure with all required dependencies,
So that I have a consistent development environment ready for implementation.

**Acceptance Criteria:**
1. Python 3.10+ virtual environment created and activated
2. Project directory structure created (src/, config/, tests/, docs/)
3. All dependencies installed: `reachy_mini`, `opencv-python`, `face_recognition`, `numpy`, `pyttsx3`
4. requirements.txt or pyproject.toml file created with pinned versions
5. Git repository initialized with .gitignore configured for Python
6. README.md created with setup instructions

**Prerequisites:** None (foundational story)

---

### Story 1.2: Reachy SIM Connection

As a **developer**,
I want to establish a reliable connection to the Reachy simulator,
So that I can programmatically control the robot's movements.

**Acceptance Criteria:**
1. Reachy daemon running in simulation mode (`reachy-mini-daemon --sim`)
2. Python script successfully connects to simulator using ReachyMini SDK
3. Script can read current head position
4. Script can command basic head movements (pan, tilt, roll)
5. Connection error handling implemented (daemon not running, connection lost)
6. Simple test script demonstrates connection and movement control

**Prerequisites:** Story 1.1 (dependencies installed)

---

### Story 1.3: Camera Input Pipeline

As a **developer**,
I want to capture and process frames from the laptop webcam,
So that I have video input ready for face detection.

**Acceptance Criteria:**
1. OpenCV successfully accesses laptop webcam (device index 0)
2. Continuous frame capture at 30 FPS
3. Frames converted to RGB format for processing
4. Frame dimensions and quality validated (minimum 640x480)
5. Camera error handling (camera not found, permission denied)
6. Simple display window shows live camera feed
7. Graceful shutdown releases camera resources

**Prerequisites:** Story 1.1 (OpenCV installed)

---

### Story 1.4: End-to-End Integration Test

As a **developer**,
I want to verify the complete pipeline from camera to Reachy movement,
So that I have confidence all foundational components work together.

**Acceptance Criteria:**
1. Single test script combines camera capture + Reachy control
2. When any face is detected in frame (using simple Haar cascade), Reachy looks toward camera
3. When no face detected, Reachy returns to neutral position
4. Test runs continuously for 2 minutes without errors
5. Console logs show detection events and Reachy commands
6. Documentation updated with "getting started" instructions
7. Demo video or screenshot captured showing working system

**Prerequisites:** Story 1.2 (Reachy control), Story 1.3 (camera input)

---

## Epic 2: Vision & Recognition Pipeline

**Goal:** Implement robust face detection and recognition system that identifies known individuals from the webcam feed and distinguishes them from unknown faces. This epic delivers the core AI capability that makes Reachy "aware" of who it's interacting with.

**Value:** Enables personalized interactions, demonstrates the project's primary technical innovation, and provides the foundation for behavioral responses.

**Estimated Stories:** 5

---

### Story 2.1: Face Detection Module

As a **developer**,
I want to reliably detect human faces in camera frames,
So that the system can identify regions of interest for recognition.

**Acceptance Criteria:**
1. Face detection implemented using `face_recognition` library (HOG-based detector)
2. Detection runs on every frame from camera pipeline
3. Bounding boxes calculated for all detected faces
4. Detection performance: < 100ms per frame on typical laptop
5. Handles multiple faces in frame (returns list of face locations)
6. Edge cases handled: no faces, partially visible faces, profile views
7. Unit tests validate detection on sample images

**Prerequisites:** Story 1.3 (camera pipeline working)

---

### Story 2.2: Face Encoding Database

As a **developer**,
I want to create and manage a database of known face encodings,
So that the system can compare detected faces against known individuals.

**Acceptance Criteria:**
1. Database module created (simple JSON file storage initially)
2. Function to encode face from image file and store with name/metadata
3. Function to load all encodings from database into memory
4. Database schema includes: name, encoding (128-d vector), date_added, image_path
5. Sample database created with 2-3 known faces for testing
6. Add/update/delete functions implemented
7. Database validation (detect corrupted entries)

**Prerequisites:** Story 2.1 (face detection working)

---

### Story 2.3: Face Recognition Engine

As a **developer**,
I want to match detected faces against the known face database,
So that the system can identify recognized individuals.

**Acceptance Criteria:**
1. Recognition module compares detected face encodings against database
2. Returns best match with confidence score (0.0-1.0)
3. Configurable recognition threshold (default 0.6)
4. Handles "unknown" case when no match above threshold
5. Performance: Recognition completes within 50ms per face
6. Returns person name + confidence for recognized faces
7. Unit tests validate recognition accuracy on test images

**Prerequisites:** Story 2.2 (face database exists)

---

### Story 2.4: Real-Time Recognition Pipeline

As a **developer**,
I want to integrate face recognition into the live camera feed,
So that the system continuously identifies people in real-time.

**Acceptance Criteria:**
1. Pipeline processes: camera frame → detect faces → recognize → return results
2. Frame processing rate: ≥ 5 FPS with recognition enabled
3. Results include: list of (name, confidence, bounding_box) for each detected face
4. Handles frame with no faces gracefully (empty results list)
5. Handles multiple faces (processes all, returns all results)
6. Recognition events logged with timestamp
7. Visual overlay option: draws boxes and names on frame for debugging

**Prerequisites:** Story 2.3 (recognition engine working)

---

### Story 2.5: Recognition Event System

As a **developer**,
I want to generate discrete recognition events when people are identified,
So that the behavior system can respond appropriately.

**Acceptance Criteria:**
1. Event system detects state changes: new person detected, person left frame
2. Debouncing logic prevents duplicate events (person must be seen for 3 consecutive frames)
3. Event types: PERSON_RECOGNIZED, PERSON_UNKNOWN, PERSON_DEPARTED, NO_FACES
4. Events include: event_type, person_name (if recognized), confidence, timestamp
5. Event callback mechanism for behavior system to subscribe
6. Event history stored (last 100 events) for logging/debugging
7. Unit tests validate event generation and debouncing logic

**Prerequisites:** Story 2.4 (real-time recognition pipeline)

---

## Epic 3: Behavior Engine & Response System

**Goal:** Connect recognition events to Reachy's physical responses (gestures, head movements, speech), creating natural and delightful interactions. This epic brings the robot to life and delivers the core user-facing value.

**Value:** Transforms technical capability into human-centered experience, demonstrates the project's vision, and validates the end-to-end user journey.

**Estimated Stories:** 4

---

### Story 3.1: Greeting Behavior Module

As a **developer**,
I want to define greeting behaviors for different recognition scenarios,
So that Reachy can respond appropriately to recognized and unknown people.

**Acceptance Criteria:**
1. Behavior module maps recognition events to Reachy actions
2. Recognized person behavior: look at camera, perform "wave" gesture (if available in SDK)
3. Unknown person behavior: curious head tilt, neutral expression
4. No person behavior: idle micro-movements (subtle head drift)
5. Behaviors defined as sequences of head poses with timing
6. Behavior execution is non-blocking (can be interrupted)
7. Unit tests validate behavior definitions

**Prerequisites:** Story 1.2 (Reachy control working), Story 2.5 (event system)

---

### Story 3.2: Text-to-Speech Integration

As a **developer**,
I want Reachy to speak greetings using text-to-speech,
So that interactions feel more natural and engaging.

**Acceptance Criteria:**
1. TTS module implemented using `pyttsx3` (local TTS)
2. Greeting phrases defined: recognized ("Hello [Name]!"), unknown ("Hi there! I don't think we've met yet.")
3. TTS voice configured (select natural-sounding voice if available)
4. Speech rate adjusted for clarity (not too fast)
5. TTS runs in separate thread to avoid blocking
6. Error handling: TTS fails gracefully, logs error, continues without speech
7. Test script validates TTS working with sample phrases

**Prerequisites:** Story 1.1 (pyttsx3 installed)

---

### Story 3.3: Coordinated Greeting Response

As a **user**,
I want Reachy to greet me by name with coordinated gesture and speech,
So that I experience a natural, personalized interaction.

**Acceptance Criteria:**
1. PERSON_RECOGNIZED event triggers coordinated response
2. Sequence: Reachy looks at camera → performs gesture → speaks greeting with name
3. Timing coordinated: gesture starts before speech, completes during speech
4. Response latency: < 400ms from event to first movement
5. Multiple people: Reachy greets person with highest confidence first
6. Response only triggers once per person per session (no repeated greetings)
7. Integration test demonstrates full user journey

**Prerequisites:** Story 3.1 (behaviors defined), Story 3.2 (TTS working)

---

### Story 3.4: Unknown & Idle Behaviors

As a **user**,
I want Reachy to respond appropriately when it doesn't recognize me or when no one is present,
So that the robot feels alive and responsive in all scenarios.

**Acceptance Criteria:**
1. PERSON_UNKNOWN event triggers curious response (head tilt + generic greeting)
2. NO_FACES event (after 5 seconds) triggers idle behavior
3. Idle behavior: subtle head movements (slow pan/tilt within small range)
4. Idle movement randomized to feel natural (not mechanical loop)
5. Idle behavior pauses immediately when face detected
6. PERSON_DEPARTED event logged but no special action
7. All scenarios tested and validated

**Prerequisites:** Story 3.1 (behaviors), Story 3.2 (TTS)

---

## Epic 4: Configuration & Monitoring

**Goal:** Add production-ready configuration management and logging/analytics capabilities, making the system maintainable, debuggable, and measurable. This epic polishes the system for demonstration and future extension.

**Value:** Enables easy customization, provides visibility into system performance, and sets foundation for continuous improvement.

**Estimated Stories:** 3

---

### Story 4.1: YAML Configuration System

As a **developer**,
I want to externalize all configuration to YAML files,
So that the system can be customized without code changes.

**Acceptance Criteria:**
1. config.yaml created with all configurable parameters
2. Settings include: camera_device_id, recognition_threshold, greeting_phrases, tts_voice, behavior_timing
3. Config loader module validates YAML structure and types
4. Default config values provided for all settings
5. Config can be overridden via environment variables for testing
6. Invalid config fails fast at startup with clear error message
7. Documentation includes config reference with all parameters explained

**Prerequisites:** Story 3.3 (system working end-to-end)

---

### Story 4.2: Performance Logging & Analytics

As a **developer**,
I want to log recognition events and performance metrics,
So that I can analyze system behavior and identify issues.

**Acceptance Criteria:**
1. Structured logging implemented (JSON format for parsing)
2. Log levels configured: DEBUG (frame processing), INFO (events), ERROR (failures)
3. Metrics logged: recognition_time_ms, detection_confidence, fps, event_counts
4. Logs written to both console and rotating file (max 10MB per file)
5. Recognition accuracy tracked: true_positives, false_positives, unknown_counts
6. Performance summary printed every 60 seconds (avg fps, avg recognition time)
7. Log analysis script provided (reads logs, generates summary report)

**Prerequisites:** Story 2.5 (event system), Story 3.3 (behaviors)

---

### Story 4.3: End-to-End Demo & Documentation

As a **stakeholder**,
I want a polished demo and comprehensive documentation,
So that I can understand, evaluate, and share the project.

**Acceptance Criteria:**
1. Demo script runs complete scenario: setup → recognize known person → recognize unknown → idle
2. Demo video recorded (2-3 minutes) showing all scenarios
3. README.md updated with: project overview, setup instructions, running demo, architecture diagram
4. User guide created: how to add faces to database, configure settings, troubleshoot issues
5. Architecture documentation: system diagram, subsystem descriptions, data flow
6. Performance benchmarks documented: recognition accuracy (≥90%), latency (<400ms), stability (1 hr runtime)
7. Known limitations and future enhancements documented

**Prerequisites:** All previous stories (complete system)

---

## Story Summary

**Total Stories:** 16 across 4 epics

**Epic 1 (Foundation):** 4 stories
**Epic 2 (Vision & Recognition):** 5 stories  
**Epic 3 (Behavior & Response):** 4 stories
**Epic 4 (Configuration & Monitoring):** 3 stories

**Estimated Total Effort:** 32-64 hours (2-4 hours per story)

**Critical Path:** Stories must be completed sequentially within each epic, and epics must be completed in order (1→2→3→4).

---

## Next Steps

1. **Review & Approve:** Review this epic breakdown with stakeholders
2. **Architecture Phase:** Run `create-architecture` workflow to design technical implementation
3. **Sprint Planning:** Run `sprint-planning` workflow to initialize story tracking
4. **Implementation:** Use `create-story` workflow for each story to generate detailed implementation plans

---

**For implementation:** Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown.
