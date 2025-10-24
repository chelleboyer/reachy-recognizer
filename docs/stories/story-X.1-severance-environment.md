# Story X.1: Severance-Inspired Hallway Environment

**Epic**: Quality of Life / Visual Enhancement  
**Priority**: Medium (Enhancement)  
**Estimated Effort**: 4-6 hours  
**Status**: Not Started

## Overview

Create a custom MuJoCo environment that resembles the iconic minimalist hallways from the TV show "Severance" - featuring clean white/beige walls, fluorescent lighting, geometric patterns, and the distinctive corporate aesthetic.

## User Story

**As a** developer testing Reachy's greeting behaviors  
**I want** the simulator background to look like a Severance hallway  
**So that** the testing environment is more visually interesting and thematically consistent

## Business Value

- **Visual Polish**: Makes demos and testing more engaging
- **Thematic Consistency**: Aligns with a recognizable aesthetic
- **Mood Setting**: Creates appropriate atmosphere for corporate greeting scenarios
- **Demo Quality**: Better screenshots/videos for documentation

## Acceptance Criteria

1. ✅ MuJoCo scene XML file created with Severance-inspired hallway
2. ✅ Clean white/beige walls with subtle texture
3. ✅ Geometric floor pattern (squares/rectangles)
4. ✅ Appropriate lighting (cool fluorescent feel)
5. ✅ Minimal but distinctive visual elements (no clutter)
6. ✅ Scene loads in reachy-mini-daemon --sim
7. ✅ Performance: No FPS drop compared to default scene

## Technical Design

### Severance Hallway Characteristics

**Color Palette:**
- Walls: Off-white (#F5F5F0), cream (#FFFDD0)
- Floor: Light gray (#D3D3D3) with darker grid lines (#A9A9A9)
- Accent: Muted blue-green (#7C9082)
- Lighting: Cool white with slight blue tint

**Geometric Elements:**
- Grid floor pattern (2ft x 2ft squares typical)
- Clean rectangular walls
- Simple ceiling with recessed lighting
- Minimal doorways or alcoves
- Symmetrical layout

**Lighting:**
- Even, diffuse overhead lighting
- No harsh shadows
- Slightly cooler color temperature (5000-6000K)
- Ambient occlusion for subtle depth

### MuJoCo Scene Structure

```xml
<mujoco model="severance_hallway">
  <asset>
    <!-- Materials -->
    <material name="wall_material" rgba="0.96 0.96 0.94 1.0" />
    <material name="floor_material" rgba="0.83 0.83 0.83 1.0" />
    <material name="grid_line" rgba="0.66 0.66 0.66 1.0" />
    <material name="ceiling" rgba="0.98 0.98 0.98 1.0" />
    
    <!-- Textures (optional) -->
    <texture name="floor_grid" type="2d" 
             builtin="checker" rgb1="0.83 0.83 0.83" rgb2="0.66 0.66 0.66"
             width="512" height="512" />
  </asset>
  
  <worldbody>
    <!-- Lighting -->
    <light name="top_light_1" pos="0 0 3" dir="0 0 -1" 
           directional="false" diffuse="0.9 0.92 0.95" 
           specular="0.3 0.3 0.3" />
    <light name="top_light_2" pos="0 2 3" dir="0 0 -1" 
           directional="false" diffuse="0.9 0.92 0.95" />
    <light name="ambient" directional="true" 
           diffuse="0.5 0.52 0.55" specular="0.1 0.1 0.1" />
    
    <!-- Floor with grid pattern -->
    <geom name="floor" type="plane" size="5 5 0.1" 
          material="floor_material" />
    
    <!-- Walls (hallway extending forward) -->
    <geom name="wall_left" type="box" 
          pos="-2 0 1.5" size="0.1 5 1.5" 
          material="wall_material" />
    <geom name="wall_right" type="box" 
          pos="2 0 1.5" size="0.1 5 1.5" 
          material="wall_material" />
    <geom name="wall_back" type="box" 
          pos="0 -5 1.5" size="2 0.1 1.5" 
          material="wall_material" />
    
    <!-- Ceiling -->
    <geom name="ceiling" type="box" 
          pos="0 0 3" size="2 5 0.05" 
          material="ceiling" />
  </worldbody>
</mujoco>
```

### Integration Options

**Option 1: Custom Scene File**
- Create `severance_hallway.xml` in MuJoCo format
- Modify reachy-mini-daemon to load custom scene
- Use `--scene` parameter: `reachy-mini-daemon --sim --scene severance_hallway.xml`

**Option 2: Environment Override**
- Place scene file in reachy-mini package data
- Auto-load if environment variable set
- `REACHY_SCENE=severance python ...`

**Option 3: Runtime Configuration**
- Modify MuJoCo model after initialization
- Swap background elements programmatically
- More complex but flexible

### Implementation Tasks

- [ ] Research Severance hallway reference images
- [ ] Create color palette and measurements
- [ ] Write MuJoCo XML scene file
- [ ] Test scene loading in MuJoCo viewer standalone
- [ ] Integrate with reachy-mini-daemon
- [ ] Add textures if needed (procedural or image-based)
- [ ] Adjust lighting for desired mood
- [ ] Test with Reachy model (ensure no collisions)
- [ ] Performance test (FPS comparison)
- [ ] Add scene selection to configuration
- [ ] Document scene file format and customization

## Reference Assets Needed

**Visual References:**
- Severance hallway screenshots (white walls, grid floor)
- Lumon Industries office aesthetic
- Minimalist corporate architecture

**Color Values:**
- Wall paint: Benjamin Moore "White Dove" equivalent
- Floor: Polished concrete gray
- Lighting: Cool fluorescent (5500K)

**Dimensions:**
- Ceiling height: ~3 meters (10 feet)
- Hallway width: ~2.5 meters (8 feet)
- Floor grid: ~0.6 meters (2 feet) squares

## Testing Strategy

1. **Visual Verification**:
   - Screenshot comparison with Severance reference images
   - Check color accuracy in different lighting
   - Verify geometric proportions

2. **Performance Testing**:
   - Measure FPS with default scene
   - Measure FPS with Severance scene
   - Ensure < 5% performance impact

3. **Integration Testing**:
   - Load scene with reachy-mini-daemon
   - Verify Reachy model renders correctly
   - Test camera angles and positioning
   - Ensure no geometry conflicts

4. **User Acceptance**:
   - Compare side-by-side with Severance footage
   - Get feedback on aesthetic match
   - Adjust colors/lighting based on feedback

## Edge Cases

1. **Performance on Lower-End Systems**:
   - Scene too complex → Simplify geometry, reduce lights
   - Use LOD (level of detail) if needed

2. **Scene File Path Issues**:
   - File not found → Provide clear error message
   - Fall back to default scene

3. **Reachy Model Conflicts**:
   - Collision with walls → Adjust spawn position
   - Lighting too dark → Add fill lights

4. **Customization Requests**:
   - Different hallway layouts → Parameterize scene
   - Variable colors → Material system with config

## Success Metrics

- Scene loads successfully in MuJoCo
- Visual similarity to Severance hallways (subjective: 8/10+)
- No performance degradation (FPS within 5% of default)
- Easy to enable/disable (single config change)
- Works with all existing Reachy behaviors

## Dependencies

**Required:**
- MuJoCo simulation environment
- reachy-mini package with scene loading capability
- Basic XML editing skills

**Optional:**
- Image editing for custom textures
- 3D modeling for complex geometry
- Blender export to MuJoCo format

## Future Enhancements

- Multiple scene variants (different hallway sections)
- Animated elements (subtle lighting changes)
- Add "Lumon" branding elements (if desired)
- Conference room scene variant
- Elevator scene for "entering/exiting" demos
- Dynamic lighting based on time of day
- Procedural hallway generation (infinite corridor)

## Notes

**Design Philosophy:**
- "Less is more" - Severance aesthetic is minimalist
- Subtle details matter (slight texture, soft shadows)
- Color temperature creates mood (cool = corporate)
- Symmetry and geometry are key visual elements

**MuJoCo Limitations:**
- Limited texture support (use procedural when possible)
- Lighting is somewhat basic (no ray tracing)
- Keep polygon count reasonable for performance

**Alternative Approaches:**
- Could use skybox/background image for distant walls
- Procedural floor pattern via shader/texture
- Multiple lighting configs for different moods

**Severance Aesthetic Checklist:**
- ✅ Minimalist (no clutter)
- ✅ Clean lines and geometry
- ✅ Muted color palette
- ✅ Even, fluorescent-style lighting
- ✅ Grid/pattern elements
- ✅ Corporate/institutional feel
- ✅ Slightly unsettling perfection

