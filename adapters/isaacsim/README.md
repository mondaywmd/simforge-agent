# Isaac Sim adapter

Planned: import the mobile-base URDF as an articulation, validate wheel joints, collision geometry, inertia, and sensors, then produce a reusable USD asset.



## Scene-specific runtime examples (2026-09-24)

The general adapter remains planned. The [examples](examples/README.md) now contain tested motion control, local corridor collision checks, and native MP4 capture for the separate NavBot Isaac Sim project. They depend on its saved scenes and exact prim structure; no scene bundle is supplied here.

Read the [runtime evidence](../../docs/isaac-sim-runtime-validation.md) before interpreting a passing result as environment-wide validation.
