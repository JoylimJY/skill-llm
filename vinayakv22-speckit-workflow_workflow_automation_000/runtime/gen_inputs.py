import os
import random

random.seed(42)

# Create the workspace directory structure
base = "/workspace"

# === Core SpecKit skill package (simulating the agent's skill directory) ===
skill_dir = os.path.join(base, "skills", "speckit-workflow")
specify_template = os.path.join(skill_dir, ".specify")
os.makedirs(specify_template, exist_ok=True)
os.makedirs(os.path.join(specify_template, "memory"), exist_ok=True)
os.makedirs(os.path.join(specify_template, "templates"), exist_ok=True)

with open(os.path.join(specify_template, "memory", ".gitkeep"), "w") as f:
    f.write("")

with open(os.path.join(specify_template, "templates", "spec_template.md"), "w") as f:
    f.write("# Specification Template\n## Overview\n## Requirements\n## Acceptance Criteria\n")

with open(os.path.join(specify_template, "templates", "plan_template.md"), "w") as f:
    f.write("# Plan Template\n## Architecture\n## Components\n## Dependencies\n")

# subskills stubs
subskills_dir = os.path.join(skill_dir, "subskills")
os.makedirs(subskills_dir, exist_ok=True)
for sub in ["speckit-constitution", "speckit-specify", "speckit-clarify", "speckit-plan", "speckit-tasks", "speckit-analyze", "speckit-implement"]:
    with open(os.path.join(subskills_dir, f"{sub}.md"), "w") as f:
        f.write(f"# {sub}\nThis is the {sub} subskill stub.\n")

# === The half-finished drone project ===
project = os.path.join(base, "projects", "drone-fw", "collision-avoidance")
os.makedirs(project, exist_ok=True)

# .specify IS present (initialization done)
specify_project = os.path.join(project, ".specify")
os.makedirs(specify_project, exist_ok=True)
os.makedirs(os.path.join(specify_project, "memory"), exist_ok=True)
os.makedirs(os.path.join(specify_project, "templates"), exist_ok=True)

# constitution.md EXISTS -> Constitution phase complete
with open(os.path.join(specify_project, "memory", "constitution.md"), "w") as f:
    f.write("""# Project Constitution — collision-avoidance

## Code Quality Standards
- All C++ code must pass clang-tidy checks.
- Unit test coverage minimum: 85%.
- No dynamic memory allocation in interrupt handlers.

## Architectural Constraints
- Real-time loop must not exceed 1ms latency.
- Sensor fusion module must be decoupled from flight controller.

## Testing Standards
- Hardware-in-the-loop tests required for all sensor integrations.
- Mocked sensor inputs must match real hardware timing profiles.
""")

# spec.md EXISTS -> Specify phase complete
specs_feature = os.path.join(project, "specs", "lidar-obstacle-detection")
os.makedirs(specs_feature, exist_ok=True)

with open(os.path.join(specs_feature, "spec.md"), "w") as f:
    f.write("""# Feature Specification: LiDAR Obstacle Detection

## Overview
Implement real-time obstacle detection using onboard LiDAR sensor data for the collision-avoidance firmware module.

## Functional Requirements
- FR-001: System shall detect obstacles within a 5-meter radius at 20Hz.
- FR-002: System shall classify obstacles as static or dynamic.
- FR-003: System shall emit avoidance vectors to the flight controller within 50ms.

## Non-Functional Requirements
- NFR-001: Detection latency < 40ms end-to-end.
- NFR-002: False positive rate < 2%.

## Acceptance Criteria
- AC-001: Unit tests pass for all detection scenarios.
- AC-002: HIL test suite passes with simulated LiDAR data.
""")

# plan.md EXISTS -> Plan phase complete
with open(os.path.join(specs_feature, "plan.md"), "w") as f:
    f.write("""# Technical Plan: LiDAR Obstacle Detection

## Architecture
- LidarDriver (HAL layer) -> PointCloudProcessor -> ObstacleClassifier -> AvoidanceVectorEmitter

## Components
1. LidarDriver: Reads raw UART frames from RPLidar A3.
2. PointCloudProcessor: Converts raw data to cartesian point cloud, applies noise filter.
3. ObstacleClassifier: Clusters points using DBSCAN, labels static vs dynamic via velocity estimation.
4. AvoidanceVectorEmitter: Computes gradient descent avoidance vector, sends to FC via MAVLink.

## Dependencies
- Eigen3 for matrix operations
- MAVLink C library
- googletest for unit testing
""")

# tasks.md EXISTS -> Tasks phase complete
# Mix of simple and complex tasks to trigger chunking logic
with open(os.path.join(specs_feature, "tasks.md"), "w") as f:
    f.write("""# Task List: LiDAR Obstacle Detection

## Tasks

- [ ] T001: Create `LidarDriver` class skeleton with constructor and destructor (Simple)
- [ ] T002: Implement `openSerialPort()` method in `LidarDriver` (Simple)
- [ ] T003: Implement `closeSerialPort()` method in `LidarDriver` (Simple)
- [ ] T004: Write unit tests for `LidarDriver` constructor and port open/close (Simple)
- [ ] T005: Add CMakeLists.txt entry for `LidarDriver` build target (Simple)
- [ ] T006: Implement full UART frame parsing with checksum validation and error recovery in `LidarDriver` (Complex)
- [ ] T007: Implement `PointCloudProcessor` including cartesian conversion and Gaussian noise filter (Complex)
- [X] T008: Set up googletest harness and CI pipeline configuration (Simple) — ALREADY DONE
- [ ] T009: Implement DBSCAN clustering algorithm in `ObstacleClassifier` (Complex)
- [ ] T010: Implement velocity estimation for dynamic obstacle classification (Complex)
- [ ] T011: Write unit tests for `ObstacleClassifier` with mock point cloud data (Simple)
- [ ] T012: Implement `AvoidanceVectorEmitter` gradient descent computation (Complex)
- [ ] T013: Implement MAVLink message encoding in `AvoidanceVectorEmitter` (Simple)
- [ ] T014: Write integration test for full pipeline with simulated LiDAR replay data (Complex)
- [ ] T015: Write integration test for edge case: obstacle appearing at boundary radius (Simple)
""")

# === Distractor files (realistic firmware project noise) ===
src_dir = os.path.join(project, "src")
os.makedirs(src_dir, exist_ok=True)

with open(os.path.join(src_dir, "main.cpp"), "w") as f:
    f.write("// Main entry point\n#include <iostream>\nint main() { return 0; }\n")

with open(os.path.join(src_dir, "CMakeLists.txt"), "w") as f:
    f.write("cmake_minimum_required(VERSION 3.16)\nproject(collision_avoidance)\n")

tests_dir = os.path.join(project, "tests")
os.makedirs(tests_dir, exist_ok=True)

with open(os.path.join(tests_dir, "test_placeholder.cpp"), "w") as f:
    f.write("// Placeholder test\n#include <gtest/gtest.h>\nTEST(Placeholder, Empty) { SUCCEED(); }\n")

with open(os.path.join(tests_dir, "ci_config.yml"), "w") as f:
    f.write("name: CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n")

docs_dir = os.path.join(project, "docs")
os.makedirs(docs_dir, exist_ok=True)

with open(os.path.join(docs_dir, "architecture_notes.md"), "w") as f:
    f.write("# Architecture Notes\nSensor fusion approach TBD.\nReview lidar datasheet v2.3.\n")

with open(os.path.join(docs_dir, "lidar_datasheet_summary.txt"), "w") as f:
    f.write("RPLidar A3: 360-degree scan, 16000 samples/sec, UART 256000 baud.\n")

with open(os.path.join(docs_dir, "meeting_notes_2024_03_15.txt"), "w") as f:
    f.write("Discussed sensor fusion approach. Agreed on DBSCAN for clustering.\nAction: prototype by sprint end.\n")

scripts_dir = os.path.join(project, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

with open(os.path.join(scripts_dir, "flash_firmware.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Flashing firmware...'\n")

with open(os.path.join(scripts_dir, "run_hil_tests.sh"), "w") as f:
    f.write("#!/bin/bash\necho 'Running HIL tests...'\n")

with open(os.path.join(scripts_dir, "generate_pointcloud_replay.py"), "w") as f:
    f.write("# Generates replay LiDAR data for testing\nimport json\nprint(json.dumps({'frames': []}))\n")

# A misleading partial spec for a different feature (distractor)
other_feature = os.path.join(project, "specs", "gps-denied-navigation")
os.makedirs(other_feature, exist_ok=True)

with open(os.path.join(other_feature, "spec.md"), "w") as f:
    f.write("""# Feature Specification: GPS-Denied Navigation

## Overview
Navigate using optical flow and IMU when GPS signal is lost.
## Status: DRAFT — Not yet planned.
""")
# Note: NO plan.md or tasks.md for gps-denied-navigation, so it's earlier phase

# Add a stale old tasks file for a completed feature (distractor)
completed_feature = os.path.join(project, "specs", "battery-monitor")
os.makedirs(completed_feature, exist_ok=True)

with open(os.path.join(completed_feature, "tasks.md"), "w") as f:
    f.write("""# Task List: Battery Monitor

- [X] T001: Implement ADC sampling (Simple)
- [X] T002: Implement voltage threshold alerts (Simple)
- [X] T003: Write unit tests (Simple)
""")

# A random log file at project root
with open(os.path.join(project, "build.log"), "w") as f:
    f.write("Build started 2024-03-20 09:15:00\nCompiling main.cpp... OK\nBuild complete.\n")

with open(os.path.join(project, ".gitignore"), "w") as f:
    f.write("build/\n*.o\n*.d\n.DS_Store\n")

print("Workspace generated successfully.")
print(f"Project root: {project}")