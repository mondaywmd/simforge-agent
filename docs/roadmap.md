# Roadmap

## Related NavBot publication

- [x] Document NavBot as the origin and first SimForge Agent case study.
- [x] Publish a separate NavBot repository with training code and reproducible setup.
- [ ] Add protected baseline validation and single-pillar benchmark documentation.
- [ ] Publish experiment configurations, checkpoints, evaluation tables, and failure analyses after review.

## Phase 1 — Agent-to-Blender workflow

- [x] Connect the Codex workflow to Blender automation.
- [x] Validate object creation and material assignment with a red sphere.
- [x] Save and inspect generated Blender scenes.

## Phase 2 — Gazebo robot import

- [x] Identify TurtleBot3 Burger from the ROS launch configuration.
- [x] Locate URDF, xacro, and meshes in WSL.
- [x] Collect dependencies without modifying the source workspace.
- [x] Restore missing official wheel visual meshes.
- [x] Preserve scale, link parenting, joint metadata, and mass metadata.

## Phase 3 — Environment and rendering

- [x] Build a navigation test arena.
- [x] Add reference-guided materials, lighting, and cameras.
- [x] Render overview and robot-detail frames.
- [x] Add a navigation animation with rotating wheels.
- [x] Publish final MP4 and preview GIF.

## Phase 4 — Simulation adapters

- [x] Prepare a portable corridor USD package with separated visual and collision layers.
- [x] Add static validation, portability checks, route probing, and round-trip preview.
- [x] Run local Isaac Sim cube contact, NavBot drive/turn and corridor wall-blocking tests.
- [x] Publish scene-specific motion, collision and recording examples with runtime evidence.
- [ ] Expand collision coverage and validate navigation, RGB, depth, and RTX LiDAR.
- [ ] Generate and validate MuJoCo MJCF.
- [ ] Generate and validate Gazebo SDF/URDF packages.
- [ ] Add ROS 2 package and launch examples.

## Phase 5 — Sim-ready generation

- [x] Generate static collision geometry and initial physics-material assumptions for the corridor.
- [ ] Add semantic and instance labels.
- [x] Ingest photographs and Scaniverse LiDAR for a real indoor corridor study.
- [x] Compare photo-reference, repaired LiDAR mesh, and Gaussian Splatting workflows.
- [x] Add Blender reconstruction, hierarchy organization, and LiDAR cleanup stages.
- [ ] Implement domain-randomization recipes.
- [ ] Automate cross-simulator validation and regression tests.
