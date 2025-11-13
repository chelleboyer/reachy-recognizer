# Product Requirements Document (PRD)

**Project Name:** Reachy Mini Store Assistant  
**Version:** 1.0  
**Date:** November 12, 2025  
**Author:** Michelle  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Product Vision

Transform Reachy Mini into an intelligent store assistant that uses computer vision and AI to support inventory management and staff interaction. The system prioritizes privacy (embeddings-only), speed (quick wins), and practical deployment in retail environments.

**Target Environment:** Convenience store with tobacco/cigarette inventory, managed staff, and high-value product monitoring needs.

### 1.2 Core Value Proposition

- **Inventory Accuracy:** Eliminate glare/occlusion issues on shiny cigarette packs through multi-angle capture
- **Privacy-First Staff ID:** Identify staff vs customers using uniform patterns instead of face recognition
- **Efficient Interaction:** Enable fast gesture-based controls for busy managers (faster than voice)

### 1.3 Success Metrics

- **Multi-Angle Capture:** 90%+ successful pack identification (vs current glare failures)
- **Uniform Recognition:** 85%+ staff vs customer classification accuracy
- **Gesture Controls:** <1 second response time, 95%+ gesture recognition rate
- **Manager Adoption:** 70%+ prefer gesture over voice after 1 week trial

---

## 2. Target Users

### 2.1 Primary Users

**Store Managers**
- **Need:** Fast, accurate inventory checks on high-theft tobacco products
- **Pain Points:** Glare on shiny packs, slow voice commands, awkward conversations with robots
- **Goals:** Complete tobacco wall scan in <5 minutes, approve/skip items quickly

**Store Staff (Stockers/Clerks)**
- **Need:** Quick interaction without stopping restocking work
- **Pain Points:** Hands full with boxes, can't type or tap screens
- **Goals:** Acknowledge robot requests with simple gestures while working

### 2.2 Secondary Users

**Customers**
- **Need:** Non-intrusive robot presence, clear staff identification
- **Benefit:** Robot recognizes staff uniforms, doesn't confuse customers with employees

---

## 3. Product Scope

### 3.1 In Scope (MVP - 4 weeks)

#### Feature 1: Multi-Angle Capture System
- Robot head swings to capture 3-5 angles of cigarette packs
- Frame quality assessment (glare detection, focus scoring)
- Best-frame selection or multi-frame fusion
- Eliminates glare/occlusion on shiny packaging

#### Feature 2: Uniform Color-Pattern Recognition
- Detect staff uniforms vs customer clothing
- Simple color-zone detection (vest/badge/shirt patterns)
- No face recognition, no PII storage
- Binary classification: staff / not-staff

#### Feature 3: Gesture-Based Quick Controls
- Three core gestures using MediaPipe:
  - 👍 Thumbs up → Approve/Continue
  - 👋 Wave → Skip/Next
  - ✋ Palm/Stop → Pause/Stop
- Visual confirmation feedback on screen
- Faster interaction than voice commands

### 3.2 Out of Scope (Future Phases)

**Phase 2 (Months 2-3):**
- Depth sensor integration (Intel D405/OAK-D-Lite)
- POS data fusion for predictive replenishment
- Phone notification push system
- QR marker-based SKU mapping

**Phase 3 (Months 4-6):**
- Multi-sensor fusion ("Truth Detector" system)
- Gaming HUD/AR shelf overlay
- Hospital runner assistant mode
- Amazon Kiva-style grid navigation

**Never in Scope:**
- Face recognition or face database storage
- Photo storage (embeddings only)
- Biometric identification beyond clothing patterns

---

## 4. Functional Requirements

### 4.1 Multi-Angle Capture System

#### FR-MAC-1: Head Movement Control
- **Description:** Robot shall move head to 3-5 predefined angles around target shelf
- **Acceptance Criteria:**
  - Angles span -45° to +45° horizontal sweep
  - Movement smooth (<2 sec per angle)
  - Camera stable before capture
- **Priority:** P0 (Must Have)

#### FR-MAC-2: Frame Quality Assessment
- **Description:** System shall assess each frame for glare, blur, and occlusion
- **Acceptance Criteria:**
  - Glare detection using brightness gradient analysis
  - Blur detection using Laplacian variance
  - Quality score 0-100 per frame
- **Priority:** P0 (Must Have)

#### FR-MAC-3: Best Frame Selection
- **Description:** System shall select highest-quality frame(s) for OCR/detection
- **Acceptance Criteria:**
  - Selects top frame if score >80
  - Fuses top 2-3 frames if scores 60-80
  - Flags failure if all scores <60
- **Priority:** P0 (Must Have)

#### FR-MAC-4: Shelf Region Tracking
- **Description:** System shall maintain consistent shelf region across angles
- **Acceptance Criteria:**
  - ROI (Region of Interest) tracked across frames
  - Perspective correction applied per angle
  - Consistent product alignment
- **Priority:** P1 (Should Have)

### 4.2 Uniform Recognition System

#### FR-UR-1: Color-Zone Detection
- **Description:** System shall detect clothing in torso region and extract color patterns
- **Acceptance Criteria:**
  - YOLO person detection with torso bounding box
  - Color histogram extraction (HSV space)
  - Pattern detection (stripes, solid, logo shapes)
- **Priority:** P0 (Must Have)

#### FR-UR-2: Staff Classification
- **Description:** System shall classify person as staff/customer based on uniform
- **Acceptance Criteria:**
  - Training on 50+ staff uniform samples
  - Training on 50+ customer clothing samples
  - Binary classification (staff/customer)
  - Confidence score output
- **Priority:** P0 (Must Have)

#### FR-UR-3: Multi-Sample Verification
- **Description:** System shall verify classification across multiple frames
- **Acceptance Criteria:**
  - Captures 3-5 frames per person
  - Majority vote classification
  - Flags uncertainty if votes split
- **Priority:** P1 (Should Have)

#### FR-UR-4: No PII Storage
- **Description:** System shall NOT store photos or face data, only embeddings
- **Acceptance Criteria:**
  - No image files written to disk
  - Only color histogram vectors stored
  - Face regions excluded from processing
- **Priority:** P0 (Must Have - Legal/Privacy)

### 4.3 Gesture Control System

#### FR-GC-1: Hand Detection
- **Description:** System shall detect hands in camera frame using MediaPipe
- **Acceptance Criteria:**
  - MediaPipe Hands running on Pi5
  - 21 hand landmarks tracked per hand
  - Min 10 FPS detection rate
- **Priority:** P0 (Must Have)

#### FR-GC-2: Gesture Recognition
- **Description:** System shall recognize 3 core gestures
- **Acceptance Criteria:**
  - Thumbs up (thumb extended, fingers curled)
  - Wave (hand side-to-side motion >2 swings)
  - Palm/Stop (open hand, fingers extended)
  - Recognition within 0.5 seconds
- **Priority:** P0 (Must Have)

#### FR-GC-3: Command Mapping
- **Description:** Gestures shall trigger robot actions
- **Acceptance Criteria:**
  - 👍 → Approve current scan, continue to next item
  - 👋 → Skip current item, move to next
  - ✋ → Pause scanning, await further input
- **Priority:** P0 (Must Have)

#### FR-GC-4: Visual Feedback
- **Description:** System shall display visual confirmation of detected gesture
- **Acceptance Criteria:**
  - On-screen icon appears <0.2 sec after gesture
  - Icon matches gesture (thumb/wave/palm emoji)
  - Brief animation confirms command received
- **Priority:** P1 (Should Have)

#### FR-GC-5: False Positive Prevention
- **Description:** System shall ignore accidental gestures
- **Acceptance Criteria:**
  - Gesture must be held for 0.5 seconds
  - Hand must be within 1-3 meters from camera
  - Ignore gestures during robot movement
- **Priority:** P1 (Should Have)

---

## 5. Non-Functional Requirements

### 5.1 Performance

- **NFR-PERF-1:** Multi-angle capture sequence completes in <10 seconds
- **NFR-PERF-2:** Gesture recognition responds in <1 second
- **NFR-PERF-3:** Uniform classification processes in <2 seconds per person
- **NFR-PERF-4:** System runs on Raspberry Pi 5 without overheating (<75°C sustained)

### 5.2 Reliability

- **NFR-REL-1:** 95%+ uptime during 8-hour store shift
- **NFR-REL-2:** Graceful degradation if one sensor fails (e.g., gesture fallback to voice)
- **NFR-REL-3:** Auto-recovery from camera disconnection within 10 seconds

### 5.3 Usability

- **NFR-USE-1:** Manager can learn gesture controls in <2 minutes
- **NFR-USE-2:** Visual feedback clear from 3 meters away
- **NFR-USE-3:** No training required for staff uniform recognition (automatic)

### 5.4 Privacy & Security

- **NFR-PRIV-1:** Zero face images stored on disk or transmitted
- **NFR-PRIV-2:** Only color embeddings stored (no reconstructable images)
- **NFR-PRIV-3:** Staff uniform data anonymized (no personal identifiers)
- **NFR-PRIV-4:** Local processing only (no cloud uploads of customer/staff data)

### 5.5 Maintainability

- **NFR-MAIN-1:** Modular architecture (each feature independent module)
- **NFR-MAIN-2:** Configuration via YAML (no code changes for tuning)
- **NFR-MAIN-3:** Logging for debugging (frame quality scores, gesture confidence, errors)

---

## 6. Technical Architecture

### 6.1 System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Reachy Mini Robot                     │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Raspberry Pi 5 + Hailo AI HAT             │ │
│  │  ┌──────────────────────────────────────────────┐ │ │
│  │  │         Vision Processing Layer               │ │ │
│  │  │  ┌────────────────────────────────────────┐  │ │ │
│  │  │  │  Multi-Angle    Uniform      Gesture   │  │ │ │
│  │  │  │   Capture    Recognition    Controls   │  │ │ │
│  │  │  └────────────────────────────────────────┘  │ │ │
│  │  │                      │                        │ │ │
│  │  │         ┌────────────┼────────────┐          │ │ │
│  │  │         │            │            │          │ │ │
│  │  │     ┌───▼───┐   ┌───▼───┐   ┌───▼───┐      │ │ │
│  │  │     │Camera │   │ YOLO  │   │Media- │      │ │ │
│  │  │     │ Feed  │   │ Hailo │   │ Pipe  │      │ │ │
│  │  │     └───────┘   └───────┘   └───────┘      │ │ │
│  │  └──────────────────────────────────────────────┘ │ │
│  │                       │                            │ │
│  │  ┌────────────────────▼──────────────────────┐   │ │
│  │  │      Coordination & Event System          │   │ │
│  │  └────────────────────┬──────────────────────┘   │ │
│  │                       │                            │ │
│  │  ┌────────────────────▼──────────────────────┐   │ │
│  │  │    Motor Control + Screen UI + Audio      │   │ │
│  │  └───────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────┐ │
└─────────────────────────────────────────────────────┘
```

### 6.2 Technology Stack

#### Hardware
- **Robot:** Reachy Mini (tethered/wired version)
- **Compute:** Raspberry Pi 5 (8GB RAM, ARM64)
- **Accelerator:** Hailo-8L AI HAT (26 TOPS)
- **Camera:** Reachy built-in camera (head-mounted)
- **Display:** Reachy tablet/screen for visual feedback

#### Software - Core
- **OS:** Raspberry Pi OS (Debian Bookworm)
- **Language:** Python 3.11+
- **Framework:** Reachy SDK for motor control

#### Software - ML/CV
- **Person Detection:** YOLOv8 nano (.hef format on Hailo)
- **Gesture Recognition:** MediaPipe Hands (CPU/GPU)
- **Frame Quality:** OpenCV (glare/blur detection)
- **Color Analysis:** scikit-image (HSV histograms)

#### Software - Infrastructure
- **Logging:** Python logging module + JSON structured logs
- **Config:** YAML configuration files
- **Event System:** Existing event coordinator from demo project

### 6.3 Data Flow

#### Multi-Angle Capture Flow
```
1. Target shelf identified → 2. Head moves to angle 1 → 3. Capture frame
   → 4. Assess quality → 5. Repeat for angles 2-5
   → 6. Select best frame(s) → 7. Run OCR/detection → 8. Return results
```

#### Uniform Recognition Flow
```
1. Person enters frame → 2. YOLO detects person → 3. Extract torso ROI
   → 4. Compute color histogram → 5. Classify staff/customer
   → 6. Multi-frame verification → 7. Output classification + confidence
```

#### Gesture Control Flow
```
1. MediaPipe detects hands → 2. Track landmarks → 3. Classify gesture
   → 4. Validate (distance, duration) → 5. Map to command
   → 6. Display visual feedback → 7. Execute robot action
```

---

## 7. User Stories & Acceptance Criteria

### 7.1 Epic 1: Multi-Angle Capture System

#### Story 1.1: Basic Multi-Angle Head Movement
**As a** store manager  
**I want** the robot to automatically capture multiple angles of a cigarette shelf  
**So that** glare doesn't prevent product identification

**Acceptance Criteria:**
- [ ] Robot moves head to 5 predefined angles (-45°, -22°, 0°, +22°, +45°)
- [ ] Each angle completes in <2 seconds
- [ ] Camera stabilizes before capture (100ms pause)
- [ ] Total sequence completes in <10 seconds

**Story Points:** 5

---

#### Story 1.2: Frame Quality Assessment
**As a** system  
**I want** to automatically assess each frame for glare and blur  
**So that** I can select the clearest image for product detection

**Acceptance Criteria:**
- [ ] Glare detection algorithm scores frames 0-100
- [ ] Blur detection using Laplacian variance
- [ ] Each frame tagged with quality metrics (JSON)
- [ ] Low-quality frames (<40 score) flagged for review

**Story Points:** 8

---

#### Story 1.3: Best Frame Selection & OCR
**As a** store manager  
**I want** the system to automatically use the clearest frame for product detection  
**So that** I get accurate inventory counts without manual intervention

**Acceptance Criteria:**
- [ ] System selects highest-quality frame if score >80
- [ ] Fuses 2-3 frames if scores in 60-80 range
- [ ] Flags failure if all frames <60 (requests manual review)
- [ ] OCR/detection runs on selected frame(s)
- [ ] Results displayed with confidence scores

**Story Points:** 8

---

### 7.2 Epic 2: Uniform Recognition System

#### Story 2.1: Person Detection with Torso ROI
**As a** system  
**I want** to detect people in the camera frame and isolate their torso region  
**So that** I can analyze clothing without processing faces

**Acceptance Criteria:**
- [ ] YOLO person detection runs on Hailo at 20+ FPS
- [ ] Torso bounding box calculated (exclude head, legs)
- [ ] ROI cropped and normalized (256x256)
- [ ] Multiple people tracked independently

**Story Points:** 5

---

#### Story 2.2: Color-Pattern Feature Extraction
**As a** system  
**I want** to extract color histograms from clothing regions  
**So that** I can distinguish staff uniforms from customer clothing

**Acceptance Criteria:**
- [ ] HSV color histogram computed (16 bins per channel)
- [ ] Dominant color(s) extracted (top 3)
- [ ] Pattern features: solid vs striped vs logo (basic heuristic)
- [ ] Feature vector normalized and stored

**Story Points:** 5

---

#### Story 2.3: Staff vs Customer Classification
**As a** store manager  
**I want** the robot to automatically identify staff by uniform  
**So that** I can interact differently with staff vs customers

**Acceptance Criteria:**
- [ ] Training dataset: 50+ staff uniform samples, 50+ customer samples
- [ ] Simple classifier (logistic regression or lightweight CNN)
- [ ] Binary output: staff / customer
- [ ] Confidence score >80% for reliable classification
- [ ] Multi-frame verification (3-5 frames, majority vote)

**Story Points:** 13

---

### 7.3 Epic 3: Gesture Control System

#### Story 3.1: MediaPipe Hand Detection Setup
**As a** developer  
**I want** MediaPipe Hands running on the Raspberry Pi 5  
**So that** I can track hand landmarks in real-time

**Acceptance Criteria:**
- [ ] MediaPipe Hands installed on Pi5
- [ ] Hand detection runs at 10+ FPS
- [ ] 21 landmarks tracked per hand
- [ ] Left/right hand differentiated

**Story Points:** 3

---

#### Story 3.2: Three-Gesture Recognition
**As a** store manager  
**I want** to control the robot with simple hand gestures  
**So that** I can interact faster than voice commands

**Acceptance Criteria:**
- [ ] Thumbs up gesture recognized (thumb extended, 4 fingers curled)
- [ ] Wave gesture recognized (hand side-to-side motion, 2+ swings)
- [ ] Palm/Stop gesture recognized (open hand, 5 fingers extended)
- [ ] Gesture recognition within 0.5 seconds
- [ ] False positive rate <5% (ignore random hand movements)

**Story Points:** 13

---

#### Story 3.3: Gesture-to-Command Mapping
**As a** store manager  
**I want** gestures to trigger robot actions immediately  
**So that** I can quickly approve/skip items during inventory scans

**Acceptance Criteria:**
- [ ] 👍 → "Approve" command sent to coordination layer
- [ ] 👋 → "Skip" command sent
- [ ] ✋ → "Pause" command sent
- [ ] Visual feedback appears <0.2 seconds after gesture
- [ ] Audio confirmation optional (short beep/tone)

**Story Points:** 5

---

#### Story 3.4: Visual Feedback & UI Integration
**As a** store manager  
**I want** to see confirmation when the robot recognizes my gesture  
**So that** I know my command was received

**Acceptance Criteria:**
- [ ] On-screen icon displays detected gesture (emoji: 👍👋✋)
- [ ] Icon appears within 0.2 seconds
- [ ] Brief animation (fade-in, pulse, fade-out over 1 second)
- [ ] Screen returns to normal state after confirmation

**Story Points:** 5

---

## 8. Implementation Timeline

### Week 1: Multi-Angle Capture
- **Days 1-2:** Head movement control, angle calibration
- **Days 3-4:** Frame quality assessment (glare/blur detection)
- **Day 5:** Best frame selection, testing on tobacco wall

**Deliverable:** Multi-angle capture module with quality scoring

---

### Week 2: Uniform Recognition (Part 1)
- **Days 1-2:** YOLO person detection, torso ROI extraction
- **Days 3-5:** Data collection (50+ staff uniforms, 50+ customer samples)

**Deliverable:** Dataset collected, person detection running

---

### Week 3: Uniform Recognition (Part 2)
- **Days 1-3:** Color histogram extraction, feature engineering
- **Days 4-5:** Train classifier, test classification accuracy

**Deliverable:** Staff vs customer classifier with 85%+ accuracy

---

### Week 4: Gesture Controls & Integration
- **Days 1-2:** MediaPipe setup, hand detection testing
- **Days 3-4:** Gesture recognition, command mapping
- **Day 5:** Visual feedback UI, end-to-end integration testing

**Deliverable:** Full system with all 3 features operational

---

## 9. Testing Strategy

### 9.1 Unit Testing
- Multi-angle capture: Test frame quality scoring algorithm with synthetic glare
- Uniform recognition: Test color extraction with known uniform samples
- Gesture recognition: Test with pre-recorded hand landmark sequences

### 9.2 Integration Testing
- End-to-end flow: Person approaches → uniform detected → gesture recognized → command executed
- Multi-angle + gesture: Manager gestures to trigger scan, robot captures angles

### 9.3 Field Testing
- Store pilot: 1 week deployment at target convenience store
- Manager feedback: Usability survey after 3 days, 7 days
- Performance metrics: Log all frame quality scores, classification confidence, gesture recognition rates

### 9.4 Privacy Validation
- Manual audit: Verify no images stored on disk
- Code review: Confirm face regions excluded from processing
- Legal review: Privacy policy compliance check

---

## 10. Success Criteria & KPIs

### 10.1 Technical KPIs
- **Multi-Angle Success Rate:** 90%+ cigarette packs identified (vs current glare failures)
- **Uniform Classification Accuracy:** 85%+ correct staff/customer distinction
- **Gesture Recognition Rate:** 95%+ gestures correctly recognized
- **Gesture Response Time:** <1 second from gesture to action

### 10.2 User Experience KPIs
- **Manager Preference:** 70%+ prefer gesture over voice after 1 week
- **Interaction Speed:** 50% faster inventory approval vs voice commands
- **Learning Curve:** 100% of managers use gestures correctly within first 5 minutes

### 10.3 Business KPIs
- **Inventory Accuracy:** 15% improvement in tobacco wall counts
- **Manager Time Savings:** 30% reduction in tobacco inventory check time
- **System Uptime:** 95%+ during 8-hour shifts

### 10.4 Privacy KPIs
- **Zero PII Incidents:** No face images stored or transmitted
- **Audit Compliance:** 100% pass rate on privacy audits
- **Staff Comfort:** 80%+ staff comfortable with uniform-based recognition

---

## 11. Risks & Mitigations

### 11.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Multi-angle capture too slow (>10 sec) | High | Medium | Pre-optimize motor movements, reduce angles to 3 if needed |
| Uniform recognition fails with varied lighting | High | Medium | Collect training data in multiple lighting conditions |
| Gesture false positives (accidental triggers) | Medium | High | Require 0.5s hold time, distance validation, ignore during robot movement |
| MediaPipe too slow on Pi5 (<10 FPS) | Medium | Low | Use MediaPipe Lite models, GPU acceleration, reduce resolution |
| Hailo model unavailable for YOLO | High | Low | Use CPU-based YOLO as fallback (accept slower FPS) |

### 11.2 User Adoption Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Managers don't trust robot counts | High | Medium | Display frame quality scores, show best-frame image for verification |
| Staff uncomfortable with uniform tracking | Medium | Medium | Emphasize no face recognition, show only color histograms (not photos) |
| Gestures feel awkward/silly | Low | Medium | Offer voice fallback, make gestures optional during training phase |

### 11.3 Deployment Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Store WiFi unreliable for updates | Low | High | Design for offline operation, log locally |
| Robot tether limits movement range | Medium | High | Plan scanning zones within tether reach, consider wireless upgrade |
| Customers distracted by robot | Low | Medium | Schedule scans during off-peak hours initially |

---

## 12. Future Roadmap

### Phase 2 (Months 2-3): Enhanced Sensing
- **Depth Sensor Integration:** Intel D405 or OAK-D-Lite for shelf gap detection
- **Phone Notifications:** Push alerts to manager phones for approvals
- **QR Marker System:** Fast SKU mapping with shelf markers

### Phase 3 (Months 4-6): Intelligence Layer
- **Multi-Sensor Fusion:** "Truth Detector" system (camera + depth + pressure)
- **Predictive Replenishment:** POS data fusion for forecasting
- **Gaming HUD/AR Overlay:** Visual shelf heatmaps and AR arrows

### Phase 4 (Months 7-12): Advanced Autonomy
- **Grid Navigation:** Amazon Kiva-style aisle navigation
- **Hospital Runner Mode:** Deliver items, follow staff
- **SCO Loss Detection:** Tobacco wall compliance monitoring

---

## 13. Open Questions

1. **POS Integration:** What's the API for accessing MOS (Manager Order System) data?
2. **Uniform Variability:** Do staff wear consistent uniforms, or are there multiple styles?
3. **Store Layout:** What's the tether length? Can we reach all tobacco wall sections?
4. **Manager Devices:** iOS or Android phones for push notifications?
5. **WiFi Bandwidth:** Can we stream logs/metrics, or only sync at end of shift?
6. **Shelf Lighting:** Are shelves backlit, or front-lit? (Affects glare patterns)

---

## 14. Approval & Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | Michelle | 2025-11-12 | ___________ |
| Tech Lead | TBD | | ___________ |
| Privacy Officer | TBD | | ___________ |
| Store Manager (Pilot) | TBD | | ___________ |

---

## 15. Appendix

### A. Related Documents
- [Brainstorming Session Results (2025-11-02)](./brainstorming-session-results-2025-11-02.md)
- [Hailo PoC Status](../hailo_poc/STATUS.md)
- [Demo Project Archive](./demo-archive/)

### B. Glossary
- **Hailo-8L:** AI accelerator HAT for Raspberry Pi (26 TOPS compute)
- **HEF:** Hailo Executable Format (compiled neural network for Hailo)
- **MediaPipe:** Google's ML framework for body/hand/face tracking
- **MOS:** Manager Order System (store inventory ordering system)
- **OCR:** Optical Character Recognition (reading text from images)
- **PII:** Personally Identifiable Information
- **ROI:** Region of Interest (cropped image area)
- **YOLO:** You Only Look Once (real-time object detection model)

### C. Reference Links
- [Reachy Mini SDK Documentation](https://docs.pollen-robotics.com/)
- [Hailo AI Developer Zone](https://hailo.ai/developer-zone/)
- [MediaPipe Documentation](https://developers.google.com/mediapipe)
- [YOLOv8 Hailo Models](https://github.com/hailo-ai/hailo_model_zoo)
