import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# === Deep directory structure with distractor files ===

dirs = [
    "src/coordinator",
    "src/executor",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "config",
    "docs",
    "legacy/old_runner",
    "legacy/deprecated",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - existing partial/wrong implementations

distractor_coordinator = """\
# Old coordinator - DO NOT USE
# This was the original implementation before the refactor

class OldCoordinator:
    def __init__(self):
        self.status = "idle"
    
    def run(self, task):
        self.status = "running"
        result = task()
        self.status = "done"
        return result
    
    def stop(self):
        self.status = "stopped"
"""
with open(os.path.join(workspace, "legacy/old_runner/coordinator.py"), "w") as f:
    f.write(distractor_coordinator)

distractor_executor = """\
# Simple executor - no state tracking
def execute_step(step_fn):
    try:
        return step_fn()
    except Exception as e:
        return {"error": str(e)}
"""
with open(os.path.join(workspace, "legacy/deprecated/executor.py"), "w") as f:
    f.write(distractor_executor)

# Wrong state names as a trap
wrong_states = """\
# DRAFT - state names brainstorm
# Options considered:
#   "pending", "processing", "done", "error", "paused"
#   "start", "running", "finish", "cancelled"
#   "init", "active", "complete", "blocked"
# Final decision: TBD
"""
with open(os.path.join(workspace, "docs/state_naming_draft.txt"), "w") as f:
    f.write(wrong_states)

# Config files
pipeline_config = {
    "pipeline_name": "ci-build-pipeline",
    "steps": ["lint", "build", "test", "deploy"],
    "timeout_seconds": 300,
    "allow_interrupts": True
}
with open(os.path.join(workspace, "config/pipeline.json"), "w") as f:
    json.dump(pipeline_config, f, indent=2)

retry_config = """\
[retry]
max_attempts = 3
backoff_factor = 2.0
retry_on = tool_failure
"""
with open(os.path.join(workspace, "config/retry.ini"), "w") as f:
    f.write(retry_config)

# Existing partial src files that are wrong
wrong_src = """\
# Placeholder - needs proper implementation
STATE_RUNNING = "running"
STATE_STOPPED = "stopped"
STATE_COMPLETE = "complete"

def get_next_state(current):
    pass  # TODO
"""
with open(os.path.join(workspace, "src/coordinator/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(workspace, "src/coordinator/states_draft.py"), "w") as f:
    f.write(wrong_src)

# Utils
with open(os.path.join(workspace, "src/utils/__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(workspace, "src/utils/logger.py"), "w") as f:
    f.write("import logging\nlogger = logging.getLogger('pipeline')\n")

with open(os.path.join(workspace, "src/executor/__init__.py"), "w") as f:
    f.write("")

# Test stubs (incomplete)
test_stub = """\
# Integration test stubs - to be filled once coordinator is implemented
import pytest

def test_coordinator_placeholder():
    pass  # TODO: implement once coordinator.py is ready
"""
with open(os.path.join(workspace, "tests/integration/test_pipeline.py"), "w") as f:
    f.write(test_stub)

unit_stub = """\
# Unit tests stub
def test_state_transitions():
    pass  # TODO
"""
with open(os.path.join(workspace, "tests/unit/test_states.py"), "w") as f:
    f.write(unit_stub)

# Scripts
with open(os.path.join(workspace, "scripts/run_pipeline.sh"), "w") as f:
    f.write("#!/bin/bash\npython src/coordinator/coordinator.py\n")

# A misleading README fragment in legacy
with open(os.path.join(workspace, "legacy/NOTES.txt"), "w") as f:
    f.write(
        "The old system used status='running'/'done'/'error'.\n"
        "New system should be better but architecture not finalized.\n"
        "Key requirement: must support mid-run intervention from operator.\n"
    )

# A requirements file
with open(os.path.join(workspace, "requirements.txt"), "w") as f:
    f.write("pytest\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_found, files in os.walk(workspace):
    for file in files:
        print(f"  {os.path.join(root, file)}")