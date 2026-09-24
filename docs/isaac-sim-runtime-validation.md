# Isaac Sim runtime validation — 2026-09-24

The Blender corridor's portable USD handoff has now been exercised with a dynamic body and NavBot in **Isaac Sim 6.1.0 on native Windows, RTX 4070**. This is local runtime evidence for the generated environment, not full-room validation or an autonomous-navigation result.

![NavBot at the corridor test spawn](../renders/isaacsim/navbot-corridor.png)

**[Watch the 20-second test video](https://mondaywmd.github.io/monday-robotics-universe/assets/omniverse/navbot-corridor/corridor-test.mp4)** · **[Full illustrated devlog and UI instructions](https://mondaywmd.github.io/monday-robotics-universe/isaac-navbot.html)**

The video is hosted on the project website rather than duplicated here. Its two independently recorded segments show forward/brake and side-wall blocking; the orientation change between clips is a reset, not autonomous turning or avoidance.

## What was connected

- Environment: photographs / LiDAR → modular Blender reconstruction → visual/collision USD → Isaac Sim.
- Robot: the existing TurtleBot3 / NavBot URDF plus repaired mesh dependencies → Isaac Sim URDF Importer → articulated robot USD.
- Blender remains the robot visual-asset workflow. URDF supplies links, joints, mass, inertia, collision and joint limits.
- The runtime import exposed four visual mesh instances, six rigid bodies, six colliders, two wheel revolute joints and three fixed joints. Visible sensor housings do not imply working LiDAR or camera observations.

The robot USD and composed Isaac Sim scenes remain in the separate NavBot Isaac Sim project. This repository records downstream results and scene-specific examples; it does not claim a complete standalone Isaac Sim scene bundle.

## Evidence and scope

| Experiment | Observed result | Limit |
| --- | --- | --- |
| Cube drop | A dynamic cube settles on the corridor floor at a selected position. | A different initial placement fell through and remains unexplained. |
| Physics material | A separate material with restitution 0.8 and max restitution combine gives visible bounce while retaining the visual shader. | Qualitative demonstration; no real-material calibration. |
| Flat-ground forward | Both wheels at 3 rad/s move about 0.27 m over about 3 simulation seconds. | Short low-speed drive, not tracking accuracy. |
| Flat-ground turn | Left −2, right +2 rad/s turns about 104° with millimetre-scale position drift. | Separate test reset before the turn. |
| Corridor floor | Downward raycast hits Floor at Z=0; base_link settles near Z=0.010 m. | One spawn and local support region. |
| Corridor forward | About 0.376 m over 4.07 simulation seconds, under 1 mm lateral drift. | One short path, not the entire corridor. |
| Side wall | Query hits Walls near X=0.248 m; robot base stops near X=0.169 m while drive continues. | Pose-based blocking check, not a contact-force measurement. |

Latest public-script rerun measurements are retained in [drive-test.json](../examples/isaacsim/drive-test.json) and [corridor-collision.json](../examples/isaacsim/corridor-collision.json). Small differences from earlier measurements arise from sampling the requested duration at the next simulation update. The video is a subsequent illustrative recording, not the source of these measurements.

## Repeatable Python examples

| Script | Required scene | Operation |
| --- | --- | --- |
| [control_navbot.py](../adapters/isaacsim/examples/control_navbot.py) | `isaacsim/scenes/navbot_drive_test.usda` | Forward, left turn, brake; reads base pose with the tensor API. |
| [test_corridor_collision.py](../adapters/isaacsim/examples/test_corridor_collision.py) | `isaacsim/scenes/navbot_corridor_test.usda` | Floor raycast, height and displacement checks, side-wall blocking. |
| [record_corridor.py](../adapters/isaacsim/examples/record_corridor.py) | Same corridor scene | Native viewport capture: 8-second forward and 12-second wall clips at 720p/30 FPS. |

Open the required saved scene, Stop, then load one script in Isaac Sim's Script Editor and Run. The scripts include an async entry point; do not run them in ordinary system Python. All three public versions completed in Isaac Sim before publication: [validation record](../examples/isaacsim/script-validation.json).

They expect this project's `/World/NavBot` hierarchy, wheel joint names, `/World/Camera`, the documented corridor geometry and spawn `(-0.28, -3.0, 0.03)` with +Y heading. Output paths are derived from the project containing `isaacsim/scenes/`. Scripts zero targets and stop afterwards; they leave edits in memory and do not automatically save the USD. Named measurement reports are replaced, while video names include timestamps. See [example prerequisites](../adapters/isaacsim/examples/README.md).

**These are scene-specific validation examples, not a general collision validator or production simulator adapter.** To use another environment, adapt prim paths, spawn, geometry checks and thresholds. Robot assets and test scenes are not bundled in this example directory.

## Playback crash investigation

Two GUI Play attempts crashed with `usd_usd.dll` access violations. That identifies the failing module, not the root cause. An additional diagnostic started playback before scene loading completed and crashed in debug drawing; this was a test-ordering mistake, kept separate from the user-triggered failures.

Isaac Sim Full can automatically toggle asynchronous rendering when playback changes. The tested workaround disabled the toggle and kept synchronous rendering:

```text
--/exts/isaacsim.core.throttling/enable_async=false
--/app/asyncRendering=false
--/app/asyncRenderingLowLatency=false
```

Five independent Play/Stop cycles then passed, followed by motion, corridor and recording runs without another observed crash. This is a workaround under evaluation, not a confirmed engine fix. It did not change robot mass, collisions or wheel parameters. [NVIDIA async-rendering documentation](https://docs.isaacsim.omniverse.nvidia.com/6.1.0/reference_material/sim_performance_optimization_handbook.html#asynchronous-rendering).

## Timing and capture lessons

Counting viewport updates is not a reliable simulation timer. The first corridor attempt counted updates and missed a distance threshold; the new top layer also lacked a useful authored timeline range. After setting 60 time codes/s and range 0..1000000, the test used elapsed simulation time and passed without lowering the distance threshold.

`omni.kit.capture.viewport` and `omni.videoencoding` captured the actual running simulation, with a scripted velocity schedule. FFmpeg later combined and labelled the clips. The published capture script produces the original segments; it does not add the final titles. UI Movie Capture only records: it does not automatically recreate the controller schedule. [UI walkthrough](https://mondaywmd.github.io/monday-robotics-universe/isaac-navbot.html#ui-guide).

## Remaining gates

- Investigate the original cube fall-through position and expand floor / wall / doorway coverage.
- Check full-route clearance, wheel contact and physical dimensions; calibrate friction if needed.
- Integrate runtime RGB / depth / RTX LiDAR observations and inspect thin or reflective features.
- Add navigation and later reuse Rule-only + PPO correction; compare with the Gazebo baseline.
- Continue stability checks before claiming the Play crash resolved.

The result advances **environment generation → USD delivery → local Isaac Sim runtime validation**. It does not establish full autonomous navigation, sensor correctness or sim-to-real fidelity.
