# 🧾 **Product Requirements Document (PRD.md)**

**Project Name:** Reachy Recognizer – Human-Aware AI Companion
**Prepared by:** John (PM Agent, BMAD)
**Version:** 1.0
**Date:** October 2025

---

## 🎯 **1. Product Overview**

Reachy Recognizer aims to make AI *approachable and alive* by transforming the Reachy Mini robot into a socially aware desk companion.
The system recognizes people via camera input, calls them by name, and reacts naturally with gestures, movement, and speech.

The project begins fully in simulation, ensuring reliability before hardware integration.
Eventually, Reachy Recognizer will integrate more advanced computer vision modules (e.g., planogram analysis) as an intelligent perception layer.

---

## 🧩 **2. Phased Development Plan**

| Phase | Title                         | Goal                                                        | Environment                                 |
| ----- | ----------------------------- | ----------------------------------------------------------- | ------------------------------------------- |
| **0** | **Simulation Mode**           | Build full CV → recognition → behavior loop in Reachy SIM   | Laptop w/ built-in camera, Reachy simulator |
| **1** | **Desk Companion Mode**       | Connect real Reachy Mini, replicate sim behavior physically | Laptop + Reachy Mini                        |
| **2** | **Autonomous Boom Box Mode**  | Offload CV to Raspberry Pi 5 + Hailo AI HAT                 | Reachy Mini + Pi/Hailo                      |
| **3** | **Mobile Companion Mode**     | Explore portable (backpack) configuration                   | Reachy Mini + Battery system                |
| **4** | **Retail Vision Integration** | Add planogram/out-of-stock CV capability                    | Reachy Mini + Pi/Hailo                      |

---

## 🧠 **3. Product Goals**

### 3.1 Primary Goals

* Enable Reachy to detect and recognize known individuals.
* Trigger corresponding greeting behaviors (speech, gestures).
* Run entirely in simulation (Phase 0) before deploying to hardware.
* Achieve sub-400 ms average latency between recognition and response.

### 3.2 Secondary Goals

* Modular design (easily switch input/output devices).
* Configurable recognition database (faces, names).
* Logging and analytics for recognition accuracy.
* Foundation for later CV extensions (object detection, planogram).

---

## ⚙️ **4. Functional Requirements**

| ID       | Feature                  | Description                                                              | Priority |
| -------- | ------------------------ | ------------------------------------------------------------------------ | -------- |
| **FR-1** | Face Detection           | System detects human faces in camera feed.                               | ⭐⭐⭐⭐     |
| **FR-2** | Face Recognition         | System identifies known individuals via stored embeddings.               | ⭐⭐⭐⭐     |
| **FR-3** | Greeting Behavior        | When a recognized face is found, Reachy performs gesture + speech.       | ⭐⭐⭐⭐     |
| **FR-4** | Simulator Integration    | Entire pipeline must work with Reachy SIM (no hardware).                 | ⭐⭐⭐⭐     |
| **FR-5** | Configuration Management | Names, greetings, thresholds, and camera settings are YAML-configurable. | ⭐⭐⭐      |
| **FR-6** | Unknown Handling         | If an unrecognized face is detected, Reachy gives a neutral response.    | ⭐⭐⭐      |
| **FR-7** | Performance Logging      | System logs recognition time and accuracy per event.                     | ⭐⭐       |
| **FR-8** | Modular Architecture     | Clear separation of CV, Behavior, and Communication modules.             | ⭐⭐⭐⭐     |

---

## 💬 **5. Behavioral Requirements**

| Event                     | Input                        | Reachy Response                                                          |
| ------------------------- | ---------------------------- | ------------------------------------------------------------------------ |
| **Known Person Detected** | Face matches known embedding | Reachy looks toward camera, smiles (gesture), says “Hello [Name]!”       |
| **Unknown Person**        | Face not in database         | Reachy tilts head, blinks, says “Hi there! I don’t think we’ve met yet.” |
| **No Face Detected**      | No faces in frame            | Reachy idles with micro-motions (head drift, slow pan).                  |
| **Multiple Faces**        | Several people detected      | Reachy greets one (highest confidence), logs others.                     |
| **Error State**           | CV failure / camera offline  | Reachy displays neutral idle and logs error.                             |

---

## 🧩 **6. Technical Requirements**

| Category            | Requirement                                                          |
| ------------------- | -------------------------------------------------------------------- |
| **Language**        | Python 3.10+                                                         |
| **SDK Integration** | `reachy_mini`, `reachy_mini_toolbox`, `reachy_mini_dances_library`   |
| **CV Libraries**    | `opencv-python`, `face_recognition`, `mediapipe` (optional), `numpy` |
| **Speech**          | `pyttsx3` (local TTS), optional `gTTS`                               |
| **Simulation Mode** | Must use `ReachyMiniClient(sim=True)` or daemon `--sim` flag         |
| **Latency Target**  | < 400 ms from detection → action                                     |
| **OS**              | macOS / Windows / Linux                                              |
| **Environment**     | Local simulation, no cloud dependency                                |
| **Camera Input**    | Laptop webcam (via OpenCV)                                           |

---

## 🧱 **7. Architecture Summary**

**Subsystems:**

1. **Vision Module:** Handles camera capture, detection, and recognition.
2. **Recognition Database:** Stores known encodings and metadata.
3. **Behavior Engine:** Maps recognition events to gestures, speech, and LEDs.
4. **Communication Layer:** Connects to Reachy SIM or real robot.
5. **Config Manager:** YAML configuration for user preferences and model paths.

---

## 🚀 **8. Milestones & Deliverables**

| Milestone | Deliverable                  | Definition of Done                                           | Target   |
| --------- | ---------------------------- | ------------------------------------------------------------ | -------- |
| **M0**    | Simulation Environment Setup | Reachy SIM running + camera feed acquired                    | ✅ Week 1 |
| **M1**    | Face Recognition Pipeline    | Detects and labels known faces from webcam                   | ✅ Week 2 |
| **M2**    | Behavior Mapping             | Reachy SIM performs gestures/speech for each recognized user | ✅ Week 3 |
| **M3**    | Configuration & Logging      | Config YAML, recognition accuracy logs                       | ✅ Week 4 |
| **M4**    | Demo Build                   | End-to-end sim demonstration video + log summary             | ✅ Week 5 |

---

## 🎯 **9. Success Metrics**

| Metric                           | Target                                        |
| -------------------------------- | --------------------------------------------- |
| **Recognition Accuracy**         | ≥ 90 % on known users in consistent lighting  |
| **Latency (Sim)**                | ≤ 400 ms from capture → response              |
| **False Positive Rate**          | ≤ 10 %                                        |
| **Simulation Runtime Stability** | 1 hr continuous operation without crash       |
| **User Delight Score**           | Positive qualitative feedback from test group |

---

## ⚠️ **10. Risks and Mitigations**

| Risk                               | Impact | Mitigation                                    |
| ---------------------------------- | ------ | --------------------------------------------- |
| Webcam quality affects recognition | Medium | Use well-lit scenes, adjust camera exposure   |
| Speech engine latency              | Low    | Preload TTS voices, or play short audio clips |
| SDK updates                        | Low    | Pin Reachy Mini repos to working commits      |
| Overfitting to few faces           | Medium | Capture diverse samples, augment images       |
| Transition to Pi/Hailo             | Medium | Abstract hardware layer in CV pipeline        |

---

## 💬 **11. Open Questions**

* Should gestures vary per person (custom personalities)?
* Should Reachy store long-term memory of interactions (date/time last seen)?
* Will we need a lightweight GUI/dashboard for monitoring recognition events?

These will be revisited after the simulation milestone.

---

## ✅ **12. Acceptance Criteria**

Reachy Recognizer v0.1 (Simulation Phase) is **complete** when:

1. The Reachy SIM detects and recognizes users via the laptop camera.
2. Reachy performs corresponding gestures and speech for recognized names.
3. Unknowns are handled gracefully.
4. Logs and config files are functional.
5. The system runs stable for at least one hour in simulation.

---

**End of Document**
*Prepared by John (PM Agent, BMAD v6 ALL)*
