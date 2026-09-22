# Architecture

## Vision

SimForge Agent aims to turn real-world observations and natural-language intent into simulation-ready environments and robot assets.

```text
Photos / Video / LiDAR / Depth / CAD / Text
                    |
                    v
                AI Agent
                    |
                    v
       Scene and asset understanding
                    |
                    v
          Blender / Houdini layer
                    |
       +------------+-------------+
       |            |             |
 geometry cleanup  procedural    visual QA
                   generation
                    |
                    v
       Canonical scene representation
                    |
     +--------------+---------------+
     |              |               |
 Isaac Sim       MuJoCo          Gazebo
 USD             MJCF            SDF/URDF
     \              |               /
                    v
                 ROS / ROS 2
```

## Canonical representation

A portable intermediate representation should preserve:

- visual and collision geometry;
- materials and textures;
- semantic class and instance labels;
- rigid bodies, links, and joints;
- mass, center of mass, and inertia;
- sensors and coordinate frames;
- units, axes, and simulator-specific metadata.

Direct round-tripping between URDF, SDF, MJCF, and USD is not guaranteed to be lossless. The preferred architecture is a canonical model plus tested platform adapters.

## Domain randomization

Planned randomized dimensions include lighting, materials, textures, obstacle layout, object geometry, friction, mass, robot and goal poses, camera intrinsics/extrinsics, LiDAR noise, missing returns, fog, exposure, and weather.

