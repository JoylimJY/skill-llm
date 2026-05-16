#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the A-MEM memory organization task.
Domain: Autonomous robotics firmware team engineering observations.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
base = Path(WORKSPACE)

# --- Directory structure (distractor files) ---
dirs = [
    "firmware/hal/drivers",
    "firmware/hal/tests",
    "firmware/planner/src",
    "firmware/planner/tests",
    "firmware/comms/can_bus",
    "firmware/comms/eth",
    "docs/architecture",
    "docs/runbooks",
    "ci/scripts",
    "tools/sim",
    "memory",  # will be used by agent
]
for d in dirs:
    (base / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic firmware project noise) ---
distractor_files = {
    "firmware/hal/drivers/motor_ctrl.c": "// Motor control HAL driver\n#include <stdint.h>\nvoid motor_set_pwm(uint8_t ch, uint16_t duty) {}\n",
    "firmware/hal/drivers/encoder.c": "// Encoder read driver\n#include <stdint.h>\nint32_t encoder_read(uint8_t id) { return 0; }\n",
    "firmware/hal/tests/test_motor.py": "def test_motor_pwm():\n    assert True\n",
    "firmware/planner/src/path_planner.cpp": "// A* path planner stub\n#include <vector>\nstd::vector<int> plan() { return {}; }\n",
    "firmware/planner/tests/test_planner.py": "def test_plan_empty():\n    pass\n",
    "firmware/comms/can_bus/can_frame.h": "#pragma once\ntypedef struct { uint32_t id; uint8_t data[8]; } can_frame_t;\n",
    "firmware/comms/eth/udp_sink.py": "import socket\ndef send(data): pass\n",
    "docs/architecture/system_overview.md": "# System Overview\nThe robot uses a 3-layer control stack.\n",
    "docs/architecture/power_budget.md": "# Power Budget\nTotal: 48V 20A\n",
    "docs/runbooks/deploy_firmware.md": "# Deploy Firmware\n1. Flash via JTAG\n2. Verify checksum\n",
    "ci/scripts/build.sh": "#!/bin/bash\ncmake -B build && cmake --build build\n",
    "ci/scripts/lint.sh": "#!/bin/bash\ncppcheck firmware/\n",
    "tools/sim/sim_runner.py": "# Simulation runner\nimport subprocess\nsubprocess.run(['./sim_binary'])\n",
    "tools/sim/robot_model.urdf": "<robot name='bot'><link name='base'/></robot>\n",
}

for rel_path, content in distractor_files.items():
    fp = base / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# --- THE CORE PROBLEM: Raw, unstructured engineering observations ---
# The agent must convert these into structured A-MEM notes.
# Observations are intentionally messy, contain contradictions, and some supersede others.

raw_observations = """
ROBOTICS FIRMWARE PROJECT - ENGINEERING LOG
============================================
These are raw notes captured from stand-ups, code reviews, and incident post-mortems.
They need to be organized into a proper memory store for the new team.

--- OBS-1 ---
We decided early on that all inter-process communication between the planner and the HAL layer
must go through a shared-memory ring buffer. This is faster than sockets for our 1ms cycle time
requirement. This was decided in sprint 3 when we hit latency issues with UDP.

--- OBS-2 ---
The CAN bus driver has a known bug: if two frames arrive within the same 50us window,
the second frame is silently dropped. Workaround: add 60us spacing in the sender firmware.
Ticket: FW-449.

--- OBS-3 ---
The team prefers Python for all test harnesses and simulation tooling. C++ is only for
embedded runtime code. This is a strict convention.

--- OBS-4 ---
NOTE: OBS-1 is now outdated. After sprint 7, the team switched from the ring buffer to
a lock-free SPSC queue library (readerwriterqueue). The 1ms cycle time is still the requirement
but the ring buffer approach had race conditions under high load. The SPSC queue is now
the canonical IPC mechanism between planner and HAL.

--- OBS-5 ---
The motor controller uses 12-bit PWM resolution. When setting duty cycle, values must be
in range 0-4095. Anything above 4095 clips to 4095 silently in hardware. This burned us
once during a demo when a calibration offset pushed values over the limit.

--- OBS-6 ---
We use CMake 3.22 as the build system. The firmware was migrated from Makefile in sprint 1.
All new modules must have a CMakeLists.txt. The CI pipeline runs cmake -B build && cmake --build build.

--- OBS-7 ---
Encoder overflow bug: the 16-bit encoder counter wraps around after 65535 counts.
At max speed (3000 RPM, 1024 CPR), this can happen in under 1.3 seconds. The odometry
module must handle rollover explicitly. This is related to OBS-2 (both are HAL-layer bugs).

--- OBS-8 ---
The simulation environment uses a URDF model for the robot. The team decided all physics
simulation runs at 500Hz, but the real robot control loop runs at 1000Hz. This mismatch
must be documented and any sim-to-real transfer must account for the 2x frequency difference.
"""

# Write raw observations to workspace
obs_file = base / "raw_engineering_log.txt"
obs_file.write_text(raw_observations)

# Also write a brief task instruction file so the agent knows what to do
task_brief = """
TASK BRIEF FOR KNOWLEDGE MANAGEMENT SYSTEM
===========================================
Our robotics firmware team has accumulated engineering notes over several sprints (see raw_engineering_log.txt).
We need these organized into a proper machine-readable memory store that the team (and future AI agents)
can query, navigate, and build upon.

Please:
1. Convert all observations into structured memory notes and store them in a file called notes.json
   inside a folder called memory/.
2. Make sure related observations are properly connected to each other.
3. Where a newer observation explicitly contradicts or replaces an older one, the older note should
   reflect that it has been superseded.

The goal is a high-quality, navigable knowledge base — not a flat dump of text.
"""

(base / "TASK_BRIEF.txt").write_text(task_brief)

print(f"Workspace generated at: {WORKSPACE}")
print(f"Files created: {len(distractor_files)} distractor files + raw_engineering_log.txt + TASK_BRIEF.txt")