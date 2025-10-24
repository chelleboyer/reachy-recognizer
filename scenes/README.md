# Custom MuJoCo Scenes for Reachy Mini

This directory contains custom MuJoCo scene files for use with the Reachy Mini simulator.

## Available Scenes

### severance.xml
**Minimalist Corporate Hallway**
- Off-white walls (0.97 RGB), gray ceiling (0.75 RGB), dark floor (0.45 RGB)
- 6 recessed linear ceiling lights for even, fluorescent-style illumination
- Vertical wall panels and dark baseboards for depth
- Camera: azimuth=180, elevation=-5 (facing Reachy from front)
- Inspired by the TV show "Severance" - clean, institutional aesthetic

### halloween.xml
**Spooky Halloween Atmosphere**
- 3 jack-o-lanterns with carved faces (triangular eyes, jagged mouth)
- Glowing interiors with orange emission (1.2)
- Orange candlelight and purple moonlight
- Dark night sky (0.1 0.05 0.15 RGB)
- Low mist effect on dark floor
- Camera: azimuth=165, elevation=-15

### techlab.xml
**Futuristic Sci-Fi Tech Lab**
- 3 holographic displays with cyan/pink neon accents
- Metallic walls and tech pillars with status lights
- LED strips along floor edges
- Floor at z=-0.1, holograms at y=1.5-2.5 (in front of Reachy)
- Pillars at y=-2 (behind Reachy)
- Camera: azimuth=0, elevation=-8

### balloons.xml
**Clean Grid Room**
- Checkered grid floor and all four walls (0.8/0.2 RGB checker pattern)
- Minimalist box room with even lighting
- Simple testing environment
- Camera: azimuth=90, elevation=-10

### empty.xml
**Default Empty Scene**
- Basic ground plane only
- Minimal lighting
- Standard testing environment

### minimal.xml
**Minimal Scene**
- Similar to empty with slight variations

## Installation

To use these scenes with Reachy Mini daemon:

1. Copy scene file to installed package location:
```powershell
Copy-Item "c:\code\reachy-mini-dev\scenes\<scene_name>.xml" "C:\Users\<username>\AppData\Local\uv\cache\archive-v0\<hash>\Lib\site-packages\reachy_mini\descriptions\reachy_mini\mjcf\scenes\<scene_name>.xml" -Force
```

2. Launch daemon with scene parameter:
```bash
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim --scene <scene_name>
```

Example:
```bash
uvx --from reachy-mini[mujoco] reachy-mini-daemon --sim --scene severance
```

## Scene Structure

All scenes follow this basic structure:

```xml
<mujoco model="Scene Name">
  <include file="../reachy_mini.xml"/>
  <compiler meshdir="../assets" texturedir="../assets"/>
  
  <asset>
    <!-- Materials and textures -->
  </asset>
  
  <visual>
    <!-- Visual settings (lighting, camera) -->
  </visual>
  
  <worldbody>
    <!-- Geometry (floor, walls, objects) -->
    <!-- Lights -->
  </worldbody>
</mujoco>
```

### Key Requirements

1. **Include Reachy model**: `<include file="../reachy_mini.xml"/>`
2. **Compiler paths**: `<compiler meshdir="../assets" texturedir="../assets"/>` (required for STL mesh loading)
3. **Worldbody**: All scene geometry must be in `<worldbody>` section

## Creating Custom Scenes

### Basic Template

```xml
<mujoco model="My Custom Scene">
  <include file="../reachy_mini.xml"/>
  <compiler meshdir="../assets" texturedir="../assets"/>
  
  <asset>
    <texture name="grid" type="2d" builtin="checker" width="512" height="512" 
             rgb2="0.2 0.2 0.2" rgb1="0.8 0.8 0.8"/>
    <material name="grid" texture="grid" texrepeat="3 3" texuniform="true" reflectance=".3"/>
  </asset>
  
  <visual>
    <headlight ambient="0.5 0.5 0.5" diffuse="0.8 0.8 0.8" specular="0.3 0.3 0.3"/>
    <map znear="0.01"/>
    <quality shadowsize="2048"/>
    <global azimuth="180" elevation="-10"/>
  </visual>
  
  <worldbody>
    <light pos="2 2 3" dir="-0.5 -0.5 -1" castshadow="true"/>
    <geom name="ground" type="plane" size="3 3 .05" pos="0 0 0" material="grid"/>
  </worldbody>
</mujoco>
```

### Tips

**Lighting:**
- Use multiple lights for even illumination
- `castshadow="true"` for realistic shadows (performance cost)
- Adjust `ambient`, `diffuse`, `specular` for different moods
- Cool colors (blue tint) for corporate/tech feel
- Warm colors (orange/yellow) for cozy atmospheres

**Materials:**
- Checker textures: `builtin="checker" rgb1="..." rgb2="..."`
- Solid colors: `rgba="r g b a"` (0-1 range)
- Reflectance: `reflectance="0.3"` for shiny surfaces
- Emission: `emission="1.2"` for glowing objects

**Camera:**
- `azimuth`: Rotation around vertical axis (0-360 degrees)
  - 0° = front view
  - 90° = side view (right)
  - 180° = back view
  - 270° = side view (left)
- `elevation`: Up/down angle (-90 to 90 degrees)
  - Negative values look down at Reachy
  - -10 to -15 typical for good view

**Coordinate Transformations:**
- Use `<frame euler="x y z">` wrapper for rotations
- Don't try to modify included body definitions directly
- Reachy spawns at origin (0, 0, 0) by default

**Performance:**
- Keep polygon count reasonable
- Limit number of lights (3-5 typical)
- Use procedural textures when possible
- Avoid complex physics unless needed

## Troubleshooting

**Error: "No such file or directory" for STL files**
- Add `<compiler meshdir="../assets" texturedir="../assets"/>` after include

**Error: "XML parse error MISMATCHED_ELEMENT"**
- Check all tags are properly closed
- Validate XML structure
- Ensure worldbody is properly formatted

**Reachy floating or mispositioned**
- Check ground plane is at z=0
- Verify Reachy's spawn position in parent file

**Scene not loading**
- Ensure file is copied to installed package location (not local dev directory)
- Check scene name matches filename (without .xml)
- Verify XML syntax is valid

## Reference

- [MuJoCo XML Documentation](https://mujoco.readthedocs.io/en/stable/XMLreference.html)
- [MuJoCo Example Models](https://github.com/google-deepmind/mujoco/tree/main/model)
- [Reachy Mini Documentation](https://github.com/pollen-robotics/reachy_mini)

## Contributing

To add a new scene:
1. Create XML file in this directory
2. Test with standalone MuJoCo viewer first
3. Copy to installed location and test with daemon
4. Document features in this README
5. Commit to repository

---

**Created**: October 2025  
**Repository**: chelleboyer/reachy-recognizer  
**Related Story**: X.1 - Severance-Inspired Hallway Environment
