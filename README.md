# SimForge Agent

**An AI-agent workflow for creating simulation-ready environments and robot assets across Blender, Isaac Sim, MuJoCo, Gazebo, and ROS.**

SimForge Agent is an early-stage experiment in connecting natural-language agents, digital-content tools, and robotics simulators. The first end-to-end example turns a TurtleBot3 Burger from a ROS/Gazebo workspace into an editable Blender navigation scene, static renders, and an animated navigation sequence.

This repository grew out of an earlier **Gazebo NavBot reinforcement-learning project**. That project established the robot, sensing, navigation baselines, obstacle-avoidance experiments, and evaluation methodology that motivated the asset-generation workflow documented here. SimForge Agent is therefore not a disconnected Blender demo: it is the next infrastructure layer for building reusable digital environments around an existing robotics research pipeline.

![Navigation arena overview](renders/images/navbot_arena_overview.png)

### Navigation animation

The 410-frame Blender navigation sequence plays inline as a lightweight GIF preview:

![NavBot navigation animation](renders/videos/navbot_navigation_preview.gif)

**[Download the full-quality MP4](renders/videos/navbot_navigation_animation.mp4)**

The animation shows the TurtleBot3 Burger leaving its start zone, steering through the generated obstacle layout, rotating its wheels in sync with motion, and stopping at the goal.

## What this repository demonstrates

1. Connect VS Code and a Codex agent to a Blender automation workflow.
2. Validate scene control with a simple red-sphere test.
3. Locate and collect a Gazebo robot's URDF, xacro, and mesh dependencies from WSL.
4. Import TurtleBot3 Burger into Blender while preserving scale, link hierarchy, object origins, and joint metadata.
5. Reconstruct a navigation arena from requirements and visual references.
6. Render static overview and robot-detail frames.
7. Add a collision-checked navigation animation with synchronized wheel rotation.
8. Prepare the asset structure for future Isaac Sim, MuJoCo, Gazebo, and ROS adapters.

## Origin: Gazebo NavBot project

The source project studies TurtleBot3 Burger navigation in Gazebo using camera and LiDAR observations, ROS velocity control, and a sequence of classical and learning-based controllers. Its protected direct-goal baseline was validated after restart over ten episodes with 10/10 successes, zero collisions, and zero timeouts.

The project then introduced a reproducible blocked-route benchmark: the robot starts at `(0, 0)`, an orange pillar blocks the direct path at `(1, 0)`, and the target lies at `(2, 0)`. A pure goal-seeking controller intentionally collides with the pillar, giving the experiments a clear control case and a measurable reason to learn a bypass behavior.

The experimental sequence includes:

- bounded residual actions layered over a direct-goal controller;
- native residual PPO rollout and deterministic checkpoint evaluation;
- a LiDAR-triggered control gate for obstacle takeover;
- reward shaping for safer and more efficient bypass behavior;
- behavior cloning from successful demonstrations;
- balanced curriculum and adversarial out-of-distribution evaluation;
- held-out scenario evaluation;
- failure-mode generalization across pose and obstacle variations.

The existing Gazebo work exposed a broader bottleneck: robot-learning experiments need many trustworthy scenes, assets, sensor configurations, and controlled variations. Building those environments manually does not scale. SimForge Agent explores how an AI agent can use Blender or Houdini as an intermediate asset-processing layer, generate simulation-ready environments, apply domain randomization, and export validated assets back to Isaac Sim, MuJoCo, Gazebo, and ROS.

```text
Gazebo NavBot navigation research
        |
        v
Need for repeatable scenes and asset variation
        |
        v
Codex Agent + Blender/Houdini asset pipeline
        |
        v
Simulation-ready environments + domain randomization
        |
        v
Isaac Sim / MuJoCo / Gazebo / ROS
```

This repository includes only the Blender/asset-pipeline case study. The complete NavBot training code, checkpoints, experiment logs, and detailed evaluation results are intentionally reserved for a dedicated future repository. See [NavBot project background](docs/navbot-project-background.md).

![Robot detail](renders/images/navbot_arena_detail.png)

## Current pipeline

```text
VS Code + Codex Agent
        |
        v
Blender Python automation
        |
        +-- Red-sphere connectivity test
        +-- Gazebo/URDF robot import
        +-- Reference-guided environment generation
        +-- Static frame validation
        +-- Navigation animation
        +-- GPU rendering
        |
        v
Simulation-ready asset preparation
        |
        +-- Isaac Sim / USD
        +-- MuJoCo / MJCF
        +-- Gazebo / SDF + URDF
        +-- ROS / ROS 2 packages
```

## Quick start

Open one of the Blender files:

- `blender/navbot.blend` — imported robot asset.
- `blender/navbot_navigation_arena.blend` — static navigation arena.
- `blender/navbot_navigation_animation.blend` — animated scene.

To reproduce the stages inside Blender's Scripting workspace:

1. Run `scripts/import_navbot.py` in an empty scene.
2. Run `scripts/build_navigation_arena.py` to build the environment.
3. Run `scripts/animate_navigation.py` to create the animation.

The bundled URDF resolves meshes locally under `assets/`; WSL and ROS are not required to open the Blender files.

## Repository structure

```text
assets/      TurtleBot3 visual assets and upstream license
urdf/        Expanded TurtleBot3 Burger URDF
blender/     Robot, arena, and animation scenes
scripts/     Repeatable Blender automation scripts
renders/     Static images and future videos
examples/    Machine-readable import and animation reports
docs/        Workflow, architecture, work log, and roadmap
adapters/    Planned simulator/export adapters
```

## Design principle

Blender is used as a visual and asset-processing layer, not as a replacement for the robot description. The URDF remains authoritative for links, joints, collision geometry, inertia, and physical scale. Visual meshes remain separate so the robot can later be imported as an articulation rather than a single merged object.

For cross-simulator support, the project will evolve toward a canonical scene representation containing visual geometry, collision geometry, materials, semantic labels, rigid bodies, joints, inertial properties, sensors, and coordinate conventions. Platform-specific adapters will generate USD, MJCF, SDF, and ROS assets from that representation.

## Roadmap

- [x] Add the completed navigation MP4.
- [x] Add a lightweight preview GIF for inline playback.
- Add Isaac Sim URDF/USD validation.
- Add MuJoCo MJCF and Gazebo SDF adapters.
- Generate collision proxies, inertial estimates, and semantic labels.
- Ingest photographs, video, depth data, and LiDAR.
- Add Blender/Houdini procedural asset cleanup.
- Add domain randomization for geometry, materials, lighting, sensors, and physics.
- Build closed-loop validation across simulators.

See [Architecture](docs/architecture.md), [AI work log](docs/ai-work-log.md), and [Roadmap](docs/roadmap.md).

## Third-party assets

TurtleBot3 description files and meshes are derived from ROBOTIS TurtleBot3 version 1.2.0 and retain the upstream Apache License 2.0 at `assets/turtlebot3_description/LICENSE`. The original WSL/ROS/Gazebo workspace was not modified.

## Status

Research prototype. The Blender workflow is reproducible; simulator adapters and bidirectional validation are planned work.
