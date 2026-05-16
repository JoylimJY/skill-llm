#!/usr/bin/env python3
"""
Generate a realistic, messy workspace that simulates an engineering team's
partially-attempted project setup for a smart-home hub firmware tracker.
The agent must create the CORRECT structure from scratch under projects/smarthome-hub/
"""

import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── 1. Distractor files: old/unrelated engineering artifacts ─────────────────

# Old build system leftovers
build_old = workspace / "build_old"
build_old.mkdir(exist_ok=True)
(build_old / "Makefile.bak").write_text("""# DEPRECATED - do not use
CC=gcc
CFLAGS=-Wall -O2
all: firmware.bin
firmware.bin: main.c
\t$(CC) $(CFLAGS) -o firmware.bin main.c
""")
(build_old / "firmware.bin.bak").write_bytes(bytes(random.getrandbits(8) for _ in range(256)))
(build_old / "linker.ld.old").write_text("/* old linker script - replaced 2024-01 */\nMEMORY { FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 512K }")

# Stale CI configs
ci_dir = workspace / ".ci_archive"
ci_dir.mkdir(exist_ok=True)
(ci_dir / "jenkins_old.xml").write_text("""<?xml version='1.1'?>
<project>
  <builders>
    <hudson.tasks.Shell>
      <command>make all 2>&amp;1</command>
    </hudson.tasks.Shell>
  </builders>
</project>""")
(ci_dir / "drone_v1.yml").write_text("""pipeline:
  build:
    image: gcc:9
    commands:
      - make all
  test:
    image: gcc:9
    commands:
      - make test
""")

# Miscellaneous notes and temp files
notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "meeting_2024_11.txt").write_text("""Meeting notes - Nov 2024
Attendees: Alice, Bob, Chen
Topics:
- Hub v2 firmware scope discussion
- WiFi stack upgrade needed
- OTA update mechanism required
- Memory constraints: 512KB flash, 128KB RAM
Action items: Bob to start project tracker (PENDING)
""")
(notes_dir / "todo_scratch.txt").write_text("""TODO (personal scratch - NOT official)
- setup project somehow
- write feature list?? 
- maybe use some kind of tracker
- ask about json format
""")
(notes_dir / "hardware_specs.txt").write_text("""SmartHome Hub v2 Hardware
MCU: STM32F4 @ 168MHz
Flash: 512KB
RAM: 128KB
WiFi: ESP8266 module (UART)
BLE: nRF52 module (SPI)
GPIO: 24 pins
ADC: 12-bit, 8 channels
UART: 3x
I2C: 2x
""")

# A WRONG/INCOMPLETE attempt at the project structure (bad schema, wrong location)
bad_attempt = workspace / "project_attempt_WRONG"
bad_attempt.mkdir(exist_ok=True)
# Wrong features format (missing required fields, wrong field names)
wrong_features = {
    "name": "smarthome-hub",
    "tasks": [  # WRONG: should be "features"
        {
            "task_id": "t1",  # WRONG: should be "id"
            "title": "WiFi Init",  # WRONG: should be "name"
            "done": False,  # WRONG: should be "passes"
            # Missing: description, category, priority, tests, notes
        },
        {
            "task_id": "t2",
            "title": "OTA Update",
            "done": False,
        }
    ]
}
(bad_attempt / "tasks.json").write_text(json.dumps(wrong_features, indent=2))
# Wrong progress format (free text, not structured)
(bad_attempt / "log.txt").write_text("""started project 2024-11-15
added some tasks
not sure what to do next
""")

# Random data files that could confuse an agent
data_dir = workspace / "data_dumps"
data_dir.mkdir(exist_ok=True)
(data_dir / "sensor_readings.csv").write_text("""timestamp,sensor_id,value,unit
2024-11-01T10:00:00,temp_01,23.4,celsius
2024-11-01T10:00:00,humidity_01,55.2,percent
2024-11-01T10:05:00,temp_01,23.6,celsius
2024-11-01T10:05:00,humidity_01,54.8,percent
""")
(data_dir / "error_codes.json").write_text(json.dumps({
    "E001": "WiFi connection timeout",
    "E002": "BLE pairing failed",
    "E003": "OTA checksum mismatch",
    "E004": "Flash write error",
    "E005": "Sensor read timeout"
}, indent=2))

# Old git repo in wrong place
wrong_git = workspace / "old_repo"
wrong_git.mkdir(exist_ok=True)
(wrong_git / "README.md").write_text("# Old prototype - ARCHIVED\nDo not use this.")
os.system(f"cd {wrong_git} && git init && git add . && git commit -m 'archive' 2>/dev/null")

# Some source files that look like they belong to the project but are stranded
stranded_src = workspace / "stranded_src"
stranded_src.mkdir(exist_ok=True)
(stranded_src / "wifi_driver.c").write_text("""/* WiFi driver stub - NOT integrated */
#include <stdint.h>

int wifi_init(const char *ssid, const char *password) {
    // TODO: implement
    return -1;
}

int wifi_connect(void) {
    // TODO: implement  
    return -1;
}
""")
(stranded_src / "ota_stub.h").write_text("""#ifndef OTA_H
#define OTA_H
/* OTA update interface - stub only */
int ota_check_update(void);
int ota_download(const char *url);
int ota_apply(void);
#endif
""")

# ── 2. A valid-looking but INCOMPLETE project directory (not in projects/) ───
partial_project = workspace / "hub_project_partial"
partial_project.mkdir(exist_ok=True)
# Has PROJECT.md but it's incomplete
(partial_project / "PROJECT.md").write_text("""# SmartHome Hub Firmware
Goal: firmware for hub
Tech: C, STM32
""")
# Missing features.json, progress.md, git init, src/, tests/

# ── 3. Config files with misleading names ────────────────────────────────────
(workspace / "features_template.txt").write_text("""This is NOT the features.json format.
Use this as inspiration only.
Fields to think about: name, status, priority
""")
(workspace / "progress_old.md").write_text("""# Very old progress doc
## 2023-01-01
Did some stuff. Not relevant anymore.
""")

# ── 4. A legitimate SKILL.md reference so agent can find it ──────────────────
# (The SKILL.md is assumed to be in the workspace per the problem statement)
# We do NOT create it here - it's part of the container image via the harness

# ── 5. Verification: print what was created ──────────────────────────────────
print("Generated workspace structure:")
for p in sorted(workspace.rglob("*")):
    if ".git" not in str(p):
        rel = p.relative_to(workspace)
        indent = "  " * (len(rel.parts) - 1)
        print(f"{indent}{rel.name}{'/' if p.is_dir() else ''}")
print("\nWorkspace generation complete.")