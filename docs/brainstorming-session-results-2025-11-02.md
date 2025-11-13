# Brainstorming Session Results

**Session Date:** 2025-11-02
**Facilitator:** BMad Master
**Participant:** Michelle

## Executive Summary

**Topic:** Building a CV + AI app for Reachy Mini (physical robot) - person recognition & interaction

**Session Goals:** Feature ideation for app deployment in store environment (inventory analysis + staff interaction). Privacy-first approach (embeddings only). Move fast with current tethered setup, plan for RPi5 + AI hat upgrade.

**Techniques Used:** {{techniques_list}}

**Total Ideas Generated:** {{total_ideas}}

### Key Themes Identified:

{{key_themes}}

## Technique Sessions

### SCAMPER Technique - SUBSTITUTE

#### 1. Substitute Inputs for Better Inventory Analysis
**Goal:** Replace single-camera photos with richer, more structured signals

- **Multi-angle capture** - Robot swings to capture 3-5 angles, eliminates glare/occlusion on cigarette packs
- **Depth sensors** (VL53L0X ToF, Intel D405, Luxonis OAK-D-Lite) - Detect shelf depth/fullness and gaps
- **Pressure sensors on shelves** - Detect item removal/addition even with bad visibility
- **Model-based visual classifiers** (CLIP/SigLIP embeddings) - Direct brand→UPC inference without lookup tables
- **QR/Marker tags** - Tiny markers next to facings for instant SKU mapping

#### 2. Substitute Conversation for Faster Staff Interaction
**Goal:** Replace slow voice conversation with faster interaction modes

- **Head nod/hand signal recognition** - Simple gestures (👍 approve, 👋 skip, ✋ stop) using MediaPipe/YOLO
- **Phone notifications** - Push alerts to staff phones for faster review/approval
- **Badge tap/NFC reader** - Tap badge to switch robot modes, eliminate voice login
- **Pre-set buttons on tablet** - Big controls: Scan, Review, Send Order (for managers who hate talking to machines)
- **Walkie-style push-to-respond** - Short voice commands ("Scan", "Approve", "Next") to reduce STT failures

#### 3. Substitute Face Detection with Other Recognition for Store Value
**Goal:** Replace privacy-complex face recognition with role/behavior detection

- **Uniform/vest/badge color-pattern recognition** - Identify staff vs customers by clothing zones (no PII)
- **Skeleton-based pose recognition** - Detect activities: stocking, browsing, rapid removal (MediaPipe Pose)
- **Gait recognition** - Identify roles by distinctive walking patterns (managers, stockers, customers)
- **Tool/object-in-hand recognition** - Recognize inventory gun, tablet, trash grabber to infer role
- **Proximity + engagement detection** - ToF/ultrasonic to detect when someone stands close and looks at robot

**Total ideas generated: 15**

---

### SCAMPER Technique - COMBINE

#### 1. The "Truth Detector" Scan System
**Fusion:** Camera + Depth + Pressure + POS History → Guaranteed Shelf Accuracy

**How it works:**
- Camera identifies item shape/label/brand
- Depth sensor confirms number of facings (no shadow vs hole confusion)
- Pressure strips validate actual removal/addition
- POS history provides expected sales velocity

**Compound Value:**
- "Shelf says 7 packs, vision says 6, pressure says 5, POS expects 4 → reorder recommended"
- Detects: phantom facings, incorrect counts, misplaced products, orphaned shelf tags

**Role Fusion:** Quality Assurance Inspector + Inventory Auditor

---

#### 2. The "Silent Supervisor" Interaction Mode
**Fusion:** Voice Commands + Gesture Recognition + On-Screen Prompts → Zero-Friction Workflow

**How it works:**
- Manager approaches → 3 quick actions displayed: Scan / Approve / Skip
- Manager can: gesture 👍, say "Scan next", OR tap screen
- Reachy adapts to whichever input used first

**Compound Value:**
- Faster than conversation alone
- More reliable than gestures alone
- Hands-free when carrying boxes

**Role Fusion:** Inventory Assistant + Workflow Hub + Notification Station

---

#### 3. The "Predictive Replenisher" Engine
**Fusion:** Real-Time Visual Detection + Historical Trends + Vendor Pack Rules + POS Data

**How it works:**
- Vision detects shelf gaps
- POS reveals time-of-day sales patterns
- Vendor pack sizes inform case/pack ordering
- Historical patterns predict tomorrow's shortages

**Compound Value:**
- "Not missing yet, but projected to be missing tonight"
- Automatically creates Suggested Order for MOS
- Smart instead of reactive

**Role Fusion:** Forecasting Analyst + Replenishment Planner + MOS Integrator

---

#### 4. The "Smart Greeter That Also Guards the Cigarette Wall"
**Fusion:** Proximity + Audio Direction + Pose Recognition + Visual Inventory Monitoring

**How it works:**
- Greets customers entering store (friendly, non-spooky)
- Internally tracks movement near high-theft categories:
  - Pose detection sees reaching/grabbing/hiding motions
  - Audio direction localizes sudden noises/arguments
  - Proximity sensor detects lingering/crowding

**Compound Value:**
- Polite front-of-house: "Welcome in!"
- Protective back-of-house: watches tobacco wall, records anomalies
- No face recognition needed

**Role Fusion:** Customer Greeter + Soft Security Observer + Inventory Sentinel

---

#### 5. The "Shelf Coach" for Store Staff
**Fusion:** Vision + Depth + On-Screen Heatmap + Gesture Approval + Audio Feedback

**How it works:**
- Robot scans aisle, displays heatmap on tablet:
  - Red = out of stock
  - Yellow = low
  - Green = good
- Manager navigates via gesture, voice, or tap
- Robot explains priority: "Copenhagen Wintergreen sells 28/day. Needs 4 more facings."

**Compound Value:**
- Visual problem identification without reading reports
- Context-aware coaching on why items matter

**Role Fusion:** Coach + Visual Analyst + Interactive Teaching Tool

---

**Key Combination Patterns Unlocked:**

1. **Multi-Sensor Fusion** - 2-4 sensors together eliminate false readings, give near-human shelf intuition
2. **Multi-Modal Interaction** - Voice + gestures + tablet UI = fast, flexible interaction
3. **Data Fusion** - Live vision + POS history + vendor rules + trends = predictive intelligence
4. **Multi-Role Behavior** - Simultaneous jobs: Greeter+Auditor, Supervisor+Security, Analyst+Teacher

**Total new ideas: 5 compound systems (20+ sub-features)**

---

### SCAMPER Technique - ADAPT

#### 1. Amazon Kiva Brain → Aisle-Smart Micro-Navigation
**Borrowed from:** Amazon warehouse robots, autonomous forklifts, AGVs

**Adaptation:**
- Break store aisles into "navigation cells" (2ft × 2ft grid squares)
- Robot plans shortest path to next shelf target
- Sensors create micro-adjustments for humans, carts, spills

**Why it's gold:**
- Stores are chaotic; grid navigation gives Reachy predictability
- Keeps Reachy out of "manager stocking cooler" zones
- Enables recurring nighttime auto-scans like warehouse cycle counts

**Unlocks:** Reachy as micro-Kiva bot for visual inventory

---

#### 2. Self-Checkout Loss-Detection → Tobacco-Wall Compliance Alerts
**Borrowed from:** Retail SCO (Self-Checkout) systems

**Adaptation:**
- Port SCO theft detection logic: weight sensors, unexpected item detection, pattern recognition
- Apply to tobacco/OTP wall:
  - "Arm movement without POS ring"
  - "Removed two packs but only one rang up"
  - "Shelf disturbance after closing hours"

**Why it matters:**
- No creepy face recognition
- Just motion + pattern → event classification

**Unlocks:** Soft security without being a narc

---

#### 3. Hospital Delivery Bots → Store Runner Assistant Mode
**Borrowed from:** Aethon TUG robots, hospital service robots

**Adaptation:**
- Task queueing for deliveries
- Elevator/door logic
- Automatic rerouting around humans
- Applied to store tasks:
  - Deliver handheld scanners to managers
  - Run empty cartons to backroom
  - Carry price labels/POP to different aisles
  - "Follow me mode" for training new hires

**Key inspiration:** Quiet, reliable task execution

**Unlocks:** Reachy becomes "the quiet reliable intern who actually does their job"

---

#### 4. Gaming Mini-Map + AR Halo → Shelf Overlay Guidance
**Borrowed from:** Video games (Zelda, Fortnite, Diablo, FPS HUDs) + AR apps

**Adaptation:**
- Turn Reachy's tablet into game HUD:
  - Mini-map of store with alert icons for missing items
  - AR arrows pointing to low-stock facings
  - Heatmaps like "loot rarity" → red items need urgent stocking
  - Floating labels: "Copenhagen Wintergreen L2 missing 1 facing"

**Why it works:**
- People learn game interfaces instantly
- Managers love fast-glance "where do I go?" UI

**Unlocks:** Planogram compliance becomes a video game level

---

#### 5. iPhone Intelligence + Apple Watch Nudges → Micro-Feedback Loop
**Borrowed from:** iPhone Vision Pro stack, Apple Watch haptics, Siri interactions

**Adaptation:**
- iPhone-style object detection ("This looks like a Copenhagen pack")
- Tap-to-focus → tap product on screen to compare SKU-to-SKU
- Haptic feedback: watch buzzes when Reachy detects out-of-stocks
- On-screen animations for "good scan" or "unstable reading"
- Siri-style short utterances: "Next," "Repeat," "Details"

**Why this is powerful:**
- iPhone solved human-device interaction at scale
- Stealing patterns = instant user adoption

**Unlocks:** Managers get subtle nudges and visual clarity without reading reports

---

#### BONUS: Smart Cart Pattern → Mobile Real-Time POS-Linked Inventory
**Borrowed from:** Amazon Dash Carts, Kroger KroGo, Caper carts

**Adaptation:**
- Lightweight camera on Reachy's basket
- Weight plate to confirm item pickup
- POS integration to auto-log movement
- Running list of shelf changes

**Unlocks:** Instant "what changed on this aisle since last hour?" timeline

---

**Adaptation Sources Summary:**
- **Warehouses:** Grid navigation → reliable aisle scanning
- **Self-Checkout:** Loss detection → tobacco compliance monitoring
- **Hospitals:** Task routing → store runner assistant mode
- **Games & AR:** Mini-maps + overlays → instant inventory visualization
- **iPhone & Watch:** Gesture + voice + alerts → smooth UX
- **Smart Carts:** Sensor fusion → live shelf change tracking

**Total new ideas: 6 cross-industry adaptations**

---

## Idea Categorization

### Immediate Opportunities
_Ideas ready to implement now (High Impact + High Feasibility + Quick Win)_

#### 1. **Gesture-Based Quick Controls** (SUBSTITUTE #2A)
**Why now:** Simple MediaPipe/YOLO integration, proven UX pattern
- 👍 approve, 👋 skip, ✋ stop
- No custom hardware needed
- Faster than voice for busy managers
**Tech stack:** MediaPipe Pose/Hands on Pi5, existing camera
**Timeline:** 1-2 weeks

#### 2. **Multi-Angle Capture for Cigarette Packs** (SUBSTITUTE #1A)
**Why now:** Software-only solution, immediate glare/occlusion fix
- Robot swings head 3-5 angles
- Combine best frames
- Solves #1 pain point (shiny packs)
**Tech stack:** Existing camera + motor control
**Timeline:** 1 week

#### 3. **Uniform Color-Pattern Recognition** (SUBSTITUTE #3A)
**Why now:** Privacy-friendly, simple color detection, no PII
- Staff vs customer identification
- No face database needed
- Lightweight model
**Tech stack:** Simple color detection + YOLO for clothing zones
**Timeline:** 1-2 weeks

#### 4. **Phone Notification Push** (SUBSTITUTE #2B)
**Why now:** Standard API integration, modern workflow
- Push alerts to manager phones
- Faster approval workflow
- Less awkward than robot talking
**Tech stack:** Simple webhook/push API (Firebase/Twilio)
**Timeline:** 3-5 days

#### 5. **QR/Marker-Based SKU Mapping** (SUBSTITUTE #1E)
**Why now:** Instant, reliable, low-tech solution
- Tiny markers next to facings
- Robot detects marker → maps to SKU
- Zero ambiguity
**Tech stack:** OpenCV QR detection
**Timeline:** 3-5 days

---

### Future Innovations
_Ideas requiring development/research (High Impact + Medium-High Feasibility)_

#### 1. **"Truth Detector" Multi-Sensor Fusion** (COMBINE #1)
**Why later:** Requires depth sensors + pressure hardware
- Camera + depth + pressure + POS fusion
- Guaranteed shelf accuracy
- Detects phantom facings
**Tech stack:** Intel D405/OAK-D-Lite + pressure strips + POS API
**Timeline:** 1-2 months (hardware procurement + integration)

#### 2. **"Predictive Replenisher" Engine** (COMBINE #3)
**Why later:** Requires historical data pipeline + ML training
- Real-time vision + POS + vendor rules + trends
- Proactive ordering suggestions
- MOS integration
**Tech stack:** Time-series forecasting, data pipeline, MOS API
**Timeline:** 2-3 months (data collection + model training)

#### 3. **Gaming HUD + AR Shelf Overlay** (ADAPT #4)
**Why later:** Requires AR development + spatial mapping
- Mini-map with alert icons
- AR arrows to low-stock items
- Heatmap visualization
**Tech stack:** AR.js or Unity AR, spatial mapping
**Timeline:** 1-2 months (AR development)

#### 4. **Hospital Runner Assistant Mode** (ADAPT #3)
**Why later:** Requires navigation stack + task queueing
- Deliver scanners, carry cartons
- "Follow me" training mode
- Elevator/door logic
**Tech stack:** ROS navigation, task scheduler
**Timeline:** 2-3 months (navigation + manipulation)

#### 5. **Amazon Kiva Grid Navigation** (ADAPT #1)
**Why later:** Requires SLAM + path planning
- 2ft × 2ft grid cells
- Micro-navigation with obstacle avoidance
- Nighttime auto-scans
**Tech stack:** ROS Navigation2, SLAM, occupancy grid
**Timeline:** 1-2 months (navigation development)

#### 6. **Depth Sensor Shelf Fullness Detection** (SUBSTITUTE #1B)
**Why later:** Requires depth camera hardware
- VL53L0X ToF / Intel D405 / OAK-D-Lite
- Detect shelf gaps with precision
- 3D shelf mapping
**Tech stack:** Depth camera + 3D point cloud processing
**Timeline:** 1 month (hardware + software)

---

### Moonshots
_Ambitious, transformative concepts (High Impact + Lower Feasibility + Long-term)_

#### 1. **"Smart Greeter + Cigarette Wall Guard"** (COMBINE #4)
**Why moonshot:** Multi-modal security + behavioral AI
- Proximity + audio direction + pose + inventory fusion
- Greets customers, watches tobacco wall
- Anomaly detection without face recognition
**Tech stack:** Audio beamforming, pose tracking, event correlation ML
**Timeline:** 3-6 months (sensor fusion + anomaly detection)
**Challenge:** Balancing friendly vs surveillance perception

#### 2. **"Shelf Coach" Interactive Training** (COMBINE #5)
**Why moonshot:** Advanced AI teaching system
- Vision + depth + heatmap + gesture + audio feedback
- Explains why items matter
- Real-time coaching
**Tech stack:** NLP context engine, teaching AI, multi-modal interaction
**Timeline:** 4-6 months (AI coaching logic)
**Challenge:** Natural language understanding + domain knowledge base

#### 3. **Self-Checkout Loss Detection for Tobacco Wall** (ADAPT #2)
**Why moonshot:** Complex behavioral analysis
- Detect arm movement without POS ring
- Pattern recognition for compliance
- Post-hours disturbance detection
**Tech stack:** Behavioral analytics ML, POS event correlation
**Timeline:** 3-4 months (behavioral model training)
**Challenge:** False positive rate, privacy concerns

#### 4. **Gait Recognition for Role Identification** (SUBSTITUTE #3C)
**Why moonshot:** Advanced computer vision + training data
- Distinguish managers, stockers, customers by walking patterns
- Non-PII role detection
**Tech stack:** Gait recognition ML (complex training)
**Timeline:** 6+ months (requires extensive training data)
**Challenge:** Accuracy, diversity of gaits, lighting conditions

#### 5. **Smart Cart Real-Time Change Tracking** (ADAPT #6)
**Why moonshot:** Requires mobile platform modification
- Camera on basket + weight plate + POS link
- Live shelf change timeline
**Tech stack:** Weight sensors, mobile platform, streaming data
**Timeline:** 3-4 months (hardware modification + integration)
**Challenge:** Payload capacity, sensor calibration

---

### Insights and Learnings
_Key realizations from the session_

#### Core Value Pillars Discovered:

1. **Privacy-First Intelligence**
   - Multiple ways to identify roles without face recognition
   - Uniform colors, pose, gait, tools-in-hand, proximity
   - Behavioral analysis > identity tracking

2. **Multi-Modal Interaction Wins**
   - Voice + gestures + screen = flexible, fast UX
   - Adapt to user preference (Silent Supervisor pattern)
   - Hands-free when needed, precise when desired

3. **Sensor Fusion = Truth**
   - Single sensors lie, multiple sensors triangulate accuracy
   - Camera + depth + pressure + POS = guaranteed shelf truth
   - Cross-validation eliminates false readings

4. **Steal Proven UX Patterns**
   - Gaming HUDs, iPhone gestures, hospital task routing
   - Users already trained on these patterns
   - Zero learning curve = instant adoption

5. **Multi-Role Robots Have Higher ROI**
   - Greeter + Guard, Coach + Analyst, Assistant + Sentinel
   - Maximize hardware utilization
   - Justify investment with compound value

#### Technical Feasibility Insights:

**Quick Wins (Software-Only):**
- Gesture recognition (MediaPipe)
- Multi-angle capture (motor control)
- Color-based staff detection
- Phone notifications (APIs)
- QR markers (OpenCV)

**Medium Effort (Some Hardware):**
- Depth sensors (~$50-200)
- Pressure strips (~$100-300)
- Audio direction (mic array ~$50)

**Long-Term (Complex Integration):**
- POS data pipelines
- MOS integration
- Navigation stacks
- Behavioral ML models

#### Store Deployment Considerations:

**Must-Haves:**
- Non-intrusive (not creepy)
- Fast (managers are busy)
- Reliable (can't be "that robot that's always broken")
- Privacy-friendly (no face database drama)

**Nice-to-Haves:**
- Multi-purpose (justify the hardware)
- Teaching/coaching (upskill staff)
- Predictive (not just reactive)

**Dealbreakers:**
- Slow interaction (voice-only)
- Single-failure-point sensors
- Face recognition requirement
- Complicated training

## Idea Categorization

### Immediate Opportunities

_Ideas ready to implement now_

{{immediate_opportunities}}

### Future Innovations

_Ideas requiring development/research_

{{future_innovations}}

### Moonshots

_Ambitious, transformative concepts_

{{moonshots}}

### Insights and Learnings

_Key realizations from the session_

{{insights_learnings}}

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: {{priority_1_name}}

- Rationale: {{priority_1_rationale}}
- Next steps: {{priority_1_steps}}
- Resources needed: {{priority_1_resources}}
- Timeline: {{priority_1_timeline}}

#### #2 Priority: {{priority_2_name}}

- Rationale: {{priority_2_rationale}}
- Next steps: {{priority_2_steps}}
- Resources needed: {{priority_2_resources}}
- Timeline: {{priority_2_timeline}}

#### #3 Priority: {{priority_3_name}}

- Rationale: {{priority_3_rationale}}
- Next steps: {{priority_3_steps}}
- Resources needed: {{priority_3_resources}}
- Timeline: {{priority_3_timeline}}

## Reflection and Follow-up

### What Worked Well

{{what_worked}}

### Areas for Further Exploration

{{areas_exploration}}

### Recommended Follow-up Techniques

{{recommended_techniques}}

### Questions That Emerged

{{questions_emerged}}

### Next Session Planning

- **Suggested topics:** {{followup_topics}}
- **Recommended timeframe:** {{timeframe}}
- **Preparation needed:** {{preparation}}

---

- Complicated training

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Multi-Angle Capture for Cigarette Packs

- Rationale: Solves #1 pain point (glare on shiny packs), software-only, immediate improvement
- Next steps: Create multi-angle capture module, frame combination algorithm, test on tobacco wall
- Resources needed: Reachy camera + motor control API, OpenCV, 2-3 test sessions
- Timeline: 1 week

#### #2 Priority: Uniform Color-Pattern Recognition

- Rationale: Privacy-first staff ID, lightweight model, enables staff vs customer detection
- Next steps: Collect uniform samples, train color classifier, integrate with YOLO person detection
- Resources needed: 50-100 uniform photos, 50-100 customer photos, simple CNN/color histogram
- Timeline: 1-2 weeks

#### #3 Priority: Gesture-Based Quick Controls

- Rationale: Fastest interaction (faster than voice!), works hands-free, proven UX pattern
- Next steps: Install MediaPipe on Pi5, implement 3 gestures (👍👋✋), visual feedback
- Resources needed: MediaPipe Hands/Pose, gesture classifier, command queue integration
- Timeline: 1-2 weeks

### Implementation Timeline

**Week 1:** Multi-angle capture prototype, cigarette wall testing, accuracy benchmark
**Week 2:** Uniform color data collection, model training, multi-angle refinement
**Week 3:** MediaPipe gesture setup, classifier training, uniform recognition integration
**Week 4:** Integration testing all 3 features, store pilot, performance optimization

**Total: 4 weeks to MVP with 3 core features**

## Reflection and Follow-up

### What Worked Well

- SCAMPER framework generated diverse, actionable ideas across multiple domains
- Cross-industry adaptation unlocked proven UX patterns (gaming, iPhone, warehouses)
- Privacy-first constraint led to creative non-face-recognition solutions
- Store context kept ideas grounded in real deployment scenarios

### Areas for Further Exploration

- POS data integration strategies (API access, data formats, update frequency)
- Depth sensor selection and procurement (Intel D405 vs OAK-D-Lite vs VL53L0X)
- Navigation stack architecture (ROS2 vs custom, SLAM requirements)
- MOS integration workflow (data format, approval process, order submission)

### Recommended Follow-up Techniques

- **Technical Architecture Deep Dive** - Design system architecture for Top 3 priorities
- **User Story Mapping** - Create detailed user stories for manager interaction flows
- **Risk Assessment** - Identify technical and operational risks for store deployment

### Questions That Emerged

- What's the POS system API? (Need MOS integration details)
- Camera field of view limitations? (For multi-angle capture planning)
- Store WiFi reliability? (For phone notification feature)
- Manager device platforms? (iOS/Android for push notifications)
- Shelf spacing variations? (For depth sensor selection)

### Next Session Planning

- **Suggested topics:** System architecture design, PRD creation for Top 3 features, technical spike planning
- **Recommended timeframe:** This week (strike while ideas are fresh)
- **Preparation needed:** Access to Reachy Mini hardware, sample store photos, manager interview time

---

_Session facilitated using the BMAD CIS brainstorming framework_
