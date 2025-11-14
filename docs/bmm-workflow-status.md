# BMM Workflow Status# BMM Workflow Status



## Project Configuration## Project Configuration



PROJECT_NAME: Reachy Mini Store AssistantPROJECT_NAME: Reachy Recognizer

PROJECT_TYPE: softwarePROJECT_TYPE: software

PROJECT_LEVEL: 2PROJECT_LEVEL: 2

FIELD_TYPE: greenfieldFIELD_TYPE: greenfield

START_DATE: 2025-11-12START_DATE: 2025-10-22

WORKFLOW_PATH: greenfield-level-2.yamlWORKFLOW_PATH: greenfield-level-2.yaml



## Current State## Current State



CURRENT_PHASE: 1-PlanningCURRENT_PHASE: 4-Implementation

CURRENT_WORKFLOW: PRD & Architecture DesignCURRENT_WORKFLOW: Story 4.1 - YAML Configuration System

CURRENT_AGENT: pmCURRENT_AGENT: dev

PHASE_1_COMPLETE: falsePHASE_1_COMPLETE: true

PHASE_2_COMPLETE: falsePHASE_2_COMPLETE: true

PHASE_3_COMPLETE: falsePHASE_3_COMPLETE: true

PHASE_4_COMPLETE: falsePHASE_4_COMPLETE: false



## Project Overview## Next Action



**Goal:** Build CV + AI app for Reachy Mini to support store inventory management and staff interactionNEXT_ACTION: Implement YAML configuration system

NEXT_COMMAND: *develop (Story 4.1)

**Key Constraints:**NEXT_AGENT: dev

- Privacy-first: embeddings only, no face recognition or photo storage

- Quick wins: 4-week MVP timeline## Story Backlog

- Hardware: Raspberry Pi 5 + Hailo-8L AI HAT (26 TOPS)

- Deployment: Convenience store with tobacco/cigarette inventory### Epic 4: Configuration & Monitoring (CURRENT)

- Story 4.1: YAML Configuration System (NEXT)

**Top 3 Features (MVP):**- Story 4.2: Performance Logging & Analytics

1. Multi-Angle Capture System (Week 1)- Story 4.3: End-to-End Demo & Documentation

2. Uniform Recognition System (Weeks 2-3)

3. Gesture Control System (Weeks 2-3)## Completed Stories



## Next Action### Epic 1: Foundation & Camera Setup ✅

- Story 1.1: Project Setup & Dependencies (2025-10-22) ✅

NEXT_ACTION: Begin Epic 1 (Multi-Angle Capture) - Story 1.1 implementation- Story 1.2: Reachy SIM Connection (2025-10-22) ✅

NEXT_COMMAND: *develop (Story 1.1)- Story 1.3: Camera Input Pipeline (2025-10-22) ✅

NEXT_AGENT: dev- Story 1.4: End-to-End Integration Test (2025-10-22) ✅



## Story Backlog### Epic 2: Vision & Recognition Pipeline ✅

- Story 2.1: Face Detection Module (2025-10-22) ✅

### Epic 1: Multi-Angle Capture System (NEXT - Week 1)- Story 2.2: Face Encoding Database (2025-10-22) ✅

- Story 1.1: Basic Multi-Angle Head Movement (5 pts) - READY- Story 2.3: Face Recognition Engine (2025-10-22) ✅

- Story 1.2: Frame Quality Assessment (8 pts)- Story 2.4: Real-Time Recognition Pipeline (2025-10-22) ✅

- Story 1.3: Best Frame Selection & OCR (8 pts)- Story 2.5: Recognition Event System (2025-10-22) ✅



### Epic 2: Uniform Recognition System (Weeks 2-3)### Epic 3: Behavior Engine ✅

- Story 2.1: Person Detection with Torso ROI (5 pts)- Story 3.1: Greeting Behavior Module (2025-10-22) ✅

- Story 2.2: Color-Pattern Feature Extraction (5 pts)- Story 3.2: Text-to-Speech Integration (2025-10-22) ✅

- Story 2.3: Staff vs Customer Classification (13 pts)- Story 3.3: Coordinated Greeting Response (2025-10-22) ✅

- Story 3.3.5: Reachy SDK Integration (2025-10-22) ✅

### Epic 3: Gesture Control System (Weeks 2-3)- Story 3.4: Unknown & Idle Behaviors (2025-10-24) ✅

- Story 3.1: MediaPipe Hand Detection Setup (3 pts)

- Story 3.2: Three-Gesture Recognition (13 pts)---

- Story 3.3: Gesture-to-Command Mapping (5 pts)

- Story 3.4: Visual Feedback & UI Integration (5 pts)_Last Updated: 2025-10-24_

_Status Version: 4.0_

### Epic 4: Integration & Testing (Week 4)_Total Stories: 16 across 4 epics_

- Story 4.1: End-to-End Integration Testing_Completed: 13 stories (81% complete)_

- Story 4.2: Store Pilot Deployment Prep_Remaining: 3 stories (Epic 4.1-4.3)_

- Story 4.3: Performance Optimization & Documentation

## Completed Work

### Phase 0: Discovery & Planning ✅
- Brainstorming session (SCAMPER techniques) - 26+ features generated (2025-11-02) ✅
- Feature prioritization & categorization (2025-11-02) ✅
- PRD creation with 4-week timeline (2025-11-12) ✅
- Hailo PoC documentation & setup guides (2025-11-12) ✅
- Demo project archived (2025-11-12) ✅

## Technical Stack

**Hardware:**
- Reachy Mini (tethered/wired)
- Raspberry Pi 5 (8GB RAM, ARM64)
- Hailo-8L AI HAT (26 TOPS)
- Reachy built-in camera

**Software - ML/CV:**
- YOLOv8 nano (.hef on Hailo) - person detection
- MediaPipe Hands - gesture recognition
- OpenCV - frame quality assessment
- scikit-image - color analysis

**Software - Infrastructure:**
- Python 3.11+
- Reachy SDK - motor control
- YAML config
- Event coordination system (from demo project)

## Success Metrics (MVP)

- **Multi-Angle Success:** 90%+ cigarette pack identification
- **Uniform Accuracy:** 85%+ staff vs customer classification
- **Gesture Recognition:** 95%+ recognition rate, <1s response
- **Manager Adoption:** 70%+ prefer gesture over voice after 1 week
- **System Uptime:** 95%+ during 8-hour shifts

## Risks & Blockers

### Active Blockers
- **BLOCKER:** Hailo YOLO model not yet downloaded (need .hef file)
  - Impact: Cannot test person detection until resolved
  - Mitigation: Follow download guides in hailo_poc/

### Monitoring Risks
- Multi-angle capture speed (target: <10 sec sequence)
- MediaPipe performance on Pi5 (target: 10+ FPS)
- Uniform classifier accuracy with varied lighting
- Gesture false positives

## Related Documents

- [PRD](./prd.md) - Product Requirements Document
- [Brainstorming Results](./brainstorming-session-results-2025-11-02.md) - Full SCAMPER session
- [Hailo PoC Status](../hailo_poc/STATUS.md) - Hardware setup status
- [Demo Archive](./demo-archive/) - Original demo project docs

---

_Last Updated: 2025-11-12_
_Status Version: 1.0_
_Total Stories: 13 stories across 4 epics_
_Completed: 0 stories (0% implementation)_
_Planning Phase: Complete (PRD ready)_
_Next Milestone: Week 1 - Multi-Angle Capture working_
