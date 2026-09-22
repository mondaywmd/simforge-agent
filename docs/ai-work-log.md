# AI-Assisted Blender Work Log

**Date:** 2026-09-22  
**Case study:** NavBot / TurtleBot3 Burger

## Objective

Establish an end-to-end workflow from a ROS/Gazebo robot asset to an editable Blender environment, static renders, and an animated navigation demonstration, while preserving a path toward physics-capable assets in Isaac Sim, MuJoCo, Gazebo, and ROS.

The immediate source was the earlier Gazebo NavBot PPO project. Its direct-goal baseline, reproducible single-pillar failure case, residual-control experiments, behavior-cloning work, and generalization evaluations established both the robot configuration and the need for a scalable environment-production workflow. Full NavBot training artifacts remain outside this repository and are planned for a dedicated publication.

## Milestones

### 1. VS Code and agent setup

The workflow began by connecting the development environment and Codex agent to Blender automation. A red sphere was used as the smallest useful integration test: create an object from natural language, assign a material, place a camera and light, save the scene, and inspect the result.

### 2. Robot discovery

The Windows source tree did not contain a robot URDF. Inspection of the launch and control code identified the model as `turtlebot3_burger`. The actual description package was located in Ubuntu WSL under the NavBot ROS workspace.

The collected source included an expanded URDF, reference xacro files, the Burger base mesh, LiDAR mesh, and wheel meshes. The local WSL package lacked the two wheel visual meshes even though the URDF referenced them. Gazebo remained operational because the wheels also had primitive cylindrical collision geometry. Matching wheel meshes were restored from the official ROBOTIS TurtleBot3 1.2.0 release.

### 3. Blender import

The robot was imported with real-world scale, link parenting, object origins, joint axes/types, visual materials, and mass metadata. Robot parts were intentionally kept separate. The Blender scene is a visual and asset-processing copy; the original WSL project was not modified.

### 4. Reference-guided environment

A compact navigation arena was created with a neutral floor, low walls, box and cylinder obstacles, start/goal markings, soft lighting, a full-arena camera, and a robot-detail camera. Static renders were generated before animation to validate framing, geometry, and appearance at low cost.

### 5. Animation

A 410-frame, 30 FPS navigation sequence was authored. The robot departs, turns around obstacles, approaches the goal, and stops. Wheel rotation is synchronized with motion, and the route was checked for obvious obstacle intersections.

### 6. Rendering investigation

Cycles rendered on an RTX 4070 at roughly 13 seconds per frame, compared with roughly 30 seconds on CPU. Blender's internal FFmpeg encoder wrote H.264 video data directly into an open MP4. Windows Explorer temporarily displayed zero bytes because directory metadata was not refreshed while the file handle remained open. A shared read confirmed that MP4 headers and media data were present.

Because the render did not keep individual PNG frames, an interruption could leave an MP4 without its final `moov` index and without a reliable resume point. Future long renders should use a PNG image sequence followed by a separate FFmpeg encode.

## Lessons learned

- Use a minimal scene to validate agent integration before importing complex assets.
- Treat URDF as the authoritative robot structure and Blender as an editable visual layer.
- Keep visual and collision geometry conceptually separate.
- Preserve links, joints, origins, axes, units, and inertial metadata for downstream simulation.
- Validate static frames before committing to an animation render.
- Prefer image sequences for long or important renders.
- Build simulator adapters around a canonical representation instead of assuming lossless direct conversion.
