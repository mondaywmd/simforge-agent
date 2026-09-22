# Gazebo NavBot Project Background

## Why NavBot comes first

SimForge Agent originated from a Gazebo navigation research project rather than from a standalone computer-graphics exercise. The original NavBot project uses TurtleBot3 Burger, ROS, Gazebo, RGB camera observations, LiDAR, `cmd_vel` control, and Gazebo model-state services to study goal-directed navigation and obstacle avoidance.

The first protected baseline is a direct-goal controller with heading compensation. Its restart validation completed ten of ten episodes successfully, with zero collisions and zero timeouts. This baseline provides a stable reference behavior that later experiments must preserve outside obstacle-intervention regions.

## Reproducible single-pillar benchmark

A controlled failure case was constructed to make progress measurable:

- robot: `(0, 0)`;
- orange pillar: `(1, 0)`;
- target: `(2, 0)`;
- direct path: deliberately blocked.

The nominal goal-seeking controller drives along the centerline and collides. Gazebo model-state checks and LiDAR termination checks verify that the physical scene matches the experimental definition. This gives every learning or hybrid controller the same basic question: can it bypass the pillar safely and still reach the target?

## Experiment progression

### V1 — Residual PPO foundation

The first experiment adds bounded linear and angular corrections to the nominal controller. A zero residual reproduces the baseline command exactly. Unit and smoke tests verify finite observations and rewards, velocity bounds, termination accounting, and end-to-end Gazebo command execution. A short fixed-scene PPO run did not yet learn a successful bypass, establishing a documented negative result rather than silently moving the goalposts.

### V2 — LiDAR control gate

A forward-LiDAR gate activates the residual controller near obstacles while preserving the original baseline elsewhere. Manual maximum-residual tests demonstrated that at least one steering direction can physically bypass the pillar and reach the goal, while zero residual still collides. This separated control feasibility from policy-learning difficulty.

### V3 — Reward shaping

Reward design was refined to distinguish merely avoiding a collision from making safe, efficient progress toward the target.

### V4 — Behavior cloning

Successful demonstrations were collected and used to initialize a policy before residual PPO updates. Deterministic Gazebo validation tested whether the cloned actor could reproduce the demonstrated bypass behavior.

### V5 — Curriculum and out-of-distribution evaluation

Balanced curricula and adversarial/held-out cases expanded the project beyond one memorized pillar configuration. These experiments test whether behavior survives perturbations rather than succeeding only in the training scene.

### V6 — Failure-mode generalization

The later stage organizes scenarios around known failure modes and varies robot pose, obstacle placement, and target geometry. The objective is controlled generalization with explicit checks, not unbounded randomization.

## Connection to SimForge Agent

The NavBot experiments revealed that data and environment production are part of the learning system. A policy cannot be evaluated meaningfully without reproducible geometry, accurate physical metadata, stable sensors, semantic scene structure, and controlled variations.

SimForge Agent extends the research in a new direction:

1. ingest existing ROS/Gazebo assets and real-world references;
2. use an AI agent to orchestrate Blender or Houdini;
3. reconstruct and validate editable digital environments;
4. add collision, inertial, semantic, and sensor metadata;
5. generate systematic domain variations;
6. export through tested adapters to Isaac Sim, MuJoCo, Gazebo, and ROS;
7. return the resulting scenes to training and evaluation loops.

The TurtleBot3 Blender scene in this repository is the first visible proof of that transition. A separate future NavBot repository will contain the complete navigation implementation, checkpoints, experiment artifacts, and quantitative evaluation history.

