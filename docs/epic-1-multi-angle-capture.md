# Epic 1: Multi-Angle Capture System

**Epic ID:** EPIC-1  
**Status:** READY  
**Priority:** P0 (Must Have)  
**Timeline:** Week 1 (5 days)  
**Story Points:** 21 total (3 stories)

---

## Epic Goal

Enable Reachy Mini to automatically capture multiple angles of cigarette packs/shelves to eliminate glare and occlusion issues that prevent accurate product identification.

## Business Value

**Current Problem:** Shiny cigarette packaging causes glare in single-angle captures, leading to failed OCR and misidentification.

**Solution Impact:**
- 90%+ successful pack identification (vs current glare failures)
- Automated quality assessment reduces manual intervention
- Foundation for all future vision-based inventory features

## Success Metrics

- Multi-angle capture sequence completes in <10 seconds
- Frame quality scoring achieves 85%+ accuracy on glare detection
- Best-frame selection improves OCR success rate by 40%+ vs single capture
- System successfully identifies 90%+ of cigarette packs in pilot test

## Technical Approach

### Architecture
```
┌─────────────────────────────────────────────┐
│     Multi-Angle Capture Controller          │
│  ┌────────────────────────────────────────┐ │
│  │  1. Head Movement Sequencer            │ │
│  │     - Move to predefined angles        │ │
│  │     - Stabilize camera                 │ │
│  │     - Trigger capture                  │ │
│  └────────────────┬───────────────────────┘ │
│                   │                          │
│  ┌────────────────▼───────────────────────┐ │
│  │  2. Frame Quality Assessor             │ │
│  │     - Glare detection (brightness)     │ │
│  │     - Blur detection (Laplacian)       │ │
│  │     - Score 0-100 per frame            │ │
│  └────────────────┬───────────────────────┘ │
│                   │                          │
│  ┌────────────────▼───────────────────────┐ │
│  │  3. Best Frame Selector                │ │
│  │     - Select highest quality frame     │ │
│  │     - Or fuse multiple frames          │ │
│  │     - Pass to OCR/detection            │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Key Technologies
- **Reachy SDK:** Head motor control (neck pitch/yaw)
- **OpenCV:** Frame quality assessment (glare, blur, focus)
- **NumPy:** Frame scoring and ranking
- **Configuration:** YAML-based angle definitions

## Dependencies

### Prerequisites
- ✅ Reachy SIM connection established (Story 1.2)
- ✅ Camera input pipeline working (Story 1.3)
- ✅ Reachy SDK integrated (Story 3.3.5)

### External Dependencies
- Reachy Mini hardware available for testing
- Tobacco wall/cigarette packs for target testing
- Adequate lighting conditions in test environment

## Stories in Epic

### Story 1.1: Basic Multi-Angle Head Movement (5 pts) - READY
**Goal:** Robot moves head to 5 predefined angles and captures frames  
**Value:** Foundation for multi-angle capture system  
**Acceptance:** 5 angles in <10 seconds, stable captures

### Story 1.2: Frame Quality Assessment (8 pts)
**Goal:** Automatically assess each frame for glare and blur  
**Value:** Eliminates bad frames before OCR/detection  
**Acceptance:** Quality scores 0-100, glare/blur detection working

### Story 1.3: Best Frame Selection & OCR (8 pts)
**Goal:** Select highest-quality frame(s) for product detection  
**Value:** Maximizes OCR success rate  
**Acceptance:** Intelligent selection based on quality scores

## Definition of Done (Epic Level)

- [ ] All 3 stories completed and tested
- [ ] End-to-end capture sequence runs in <10 seconds
- [ ] System successfully captures readable frames 90%+ of time
- [ ] Frame quality assessment validated with test dataset
- [ ] Integration test passes: trigger capture → receive best frame
- [ ] Documentation complete (API usage, configuration guide)
- [ ] Demo video showing multi-angle capture on tobacco wall

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Head movement too slow (>10 sec total) | High | Pre-optimize motor speeds, reduce to 3 angles if needed |
| Camera not stabilizing between moves | High | Add configurable pause duration per angle |
| Glare detection inaccurate | Medium | Test on varied lighting, tune thresholds |
| Best-frame selection fails on all bad frames | Medium | Add "no good frames" failure mode with alert |

## Out of Scope (Future Work)

- Depth sensor integration for 3D capture
- Real-time frame fusion (vs best-frame selection)
- Adaptive angle calculation based on shelf geometry
- Multi-camera capture (additional viewpoints)

## Testing Strategy

### Unit Tests
- Head movement: Verify angles reached within tolerance
- Quality assessment: Test glare/blur detection with synthetic frames
- Frame selection: Test ranking logic with known quality scores

### Integration Tests
- End-to-end: Trigger capture → head moves → frames assessed → best selected
- Edge cases: All frames bad, all frames good, mixed quality

### Field Tests
- Real tobacco wall scans (10+ products)
- Varied lighting conditions (morning, afternoon, evening)
- Different shelf positions (top, middle, bottom)

## Related Documents

- [PRD Section 4.1: Multi-Angle Capture Requirements](./prd.md#41-multi-angle-capture-system)
- [User Stories 7.1: Epic 1 Stories](./prd.md#71-epic-1-multi-angle-capture-system)
- [Implementation Timeline: Week 1](./prd.md#week-1-multi-angle-capture)

---

**Created:** 2025-11-14  
**Last Updated:** 2025-11-14  
**Version:** 1.0
