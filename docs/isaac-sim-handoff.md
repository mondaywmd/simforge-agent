# Isaac Sim handoff: what is ready and what remains

The corridor was prepared as a portable USD asset package, not declared fully validated in Isaac Sim. This distinction keeps offline asset checks separate from simulator runtime evidence.

## Package design

- `corridor.usda` is the environment composition entry.
- `visual.usdc` holds the appearance layer.
- `collision.usda` holds simplified static collision geometry.
- `test_scene.usda` supplies a minimal test stage.
- All references and textures use relative paths.
- Meters and Z-up are explicit.
- One root transform normalizes the floor to `Z=0` for visual geometry, collision geometry, cameras, and lights together.
- A manifest, checksums, dependency notes, component transforms, and conversion audit describe the handoff.

## Blender organization

![Sim-ready Blender Outliner](../renders/reality-capture/sim-ready-blender-outliner.png)

`SIM_Visual` preserves the detailed scene. `SIM_Collision` contains the separate physics representation. This allows render detail to remain rich without forcing noisy or unnecessarily complex geometry into collision queries.

## Offline verification completed

- Layer and texture references resolve through relative paths.
- Units, axis, transforms, and floor normalization are recorded.
- Door openings and major obstacle regions remain represented.
- A conservative robot footprint and route probe are checked geometrically.
- The complete folder is copied to another location and checked again for portability.
- Exported USD is reopened and rendered as a round-trip appearance check.

![USD round-trip preview](../renders/reality-capture/usd-roundtrip-preview.png)

“Round trip” means Blender scene → USD package → reopened USD → verification render. It answers whether the exported asset can be reconstructed from its own portable references. It does **not** mean the asset has completed robot or sensor validation.

## Required target-machine tests

1. Open `test_scene.usda` in the intended Isaac Sim version and confirm no missing assets or schema errors.
2. Drop a dynamic body onto the floor and raycast the floor, walls, and major obstacles.
3. Spawn the intended robot at the documented start pose and calibrate root height, wheel contact, friction, and clearance.
4. Drive the full corridor at low speed before running learned navigation.
5. Compare RGB and depth output from robot-height cameras.
6. Configure RTX LiDAR using the real sensor height, field of view, range, and frequency; inspect thin features, glass, mirrors, and hidden collision geometry.
7. Recheck physical scale against at least one measured corridor or doorway dimension.

The portable package is therefore a reproducible handoff with explicit validation gates—not a claim of completed Isaac Sim certification.
