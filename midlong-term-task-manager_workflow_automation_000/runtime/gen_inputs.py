import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Create the skill directory structure (scripts exist but don't need to run) ──
skill_dir = Path.home() / ".openclaw/skills/midlong-term-task-manager/scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

# Stub scripts (they exist as per skill docs, agent should use CLI wrappers or direct JSON manipulation)
(skill_dir / "task_check.sh").write_text("#!/bin/bash\necho 'task_check'\n")
(skill_dir / "daily_summary.sh").write_text("#!/bin/bash\necho 'daily_summary'\n")
(skill_dir / "weekly_review.sh").write_text("#!/bin/bash\necho 'weekly_review'\n")
for f in skill_dir.iterdir():
    f.chmod(0o755)

# ── Create workspace task directory with ONE existing in-progress task ──
tasks_dir = workspace / ".tasks"
logs_dir = tasks_dir / "logs"
tasks_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

existing_tasks = {
    "tasks": [
        {
            "id": "TSK-20260310-001",
            "name": "无人机传感器融合模块开发",
            "description": "为自主导航无人机开发IMU+视觉传感器融合算法",
            "type": "development",
            "priority": "high",
            "status": "in_progress",
            "created_at": "2026-03-10T09:00:00+08:00",
            "due_date": "2026-04-20",
            "decomposed": [
                {
                    "subtask": "调研现有融合算法",
                    "status": "done",
                    "due_date": "2026-03-15"
                },
                {
                    "subtask": "实现卡尔曼滤波器原型",
                    "status": "done",
                    "due_date": "2026-03-25"
                },
                {
                    "subtask": "集成视觉里程计",
                    "status": "done",
                    "due_date": "2026-04-05"
                },
                {
                    "subtask": "硬件在环测试",
                    "status": "pending",
                    "due_date": "2026-04-15"
                }
            ],
            "progress": 25,
            "last_updated": "2026-03-10T09:00:00+08:00",
            "blocked_by": None,
            "depends_on": [],
            "tags": ["sensor-fusion", "navigation", "hardware"]
        }
    ]
}

(tasks_dir / "tasks.json").write_text(json.dumps(existing_tasks, ensure_ascii=False, indent=2))

# ── Distractor files scattered around the workspace ──
distractor_dirs = [
    workspace / "src/navigation",
    workspace / "src/perception",
    workspace / "docs/hardware",
    workspace / "docs/meetings",
    workspace / "experiments/flight_logs",
    workspace / "experiments/sim_results",
    workspace / "config",
    workspace / "tests",
    workspace / "reports/q1",
    workspace / "memory",  # three-layer memory skill's domain — agent must NOT write here
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# memory/ dir — a trap: agent must write logs to .tasks/logs/, NOT here
(workspace / "memory" / "2026-03-28.md").write_text(
    "# Memory Log 2026-03-28\n\n- Completed initial flight test\n- Sensor latency issue identified\n"
)
(workspace / "memory" / "2026-03-29.md").write_text(
    "# Memory Log 2026-03-29\n\n- Reviewed sensor fusion literature\n"
)

(workspace / "src/navigation" / "kalman_filter.py").write_text(
    "# Kalman Filter Implementation\nimport numpy as np\n\nclass KalmanFilter:\n    pass\n"
)
(workspace / "src/navigation" / "waypoint_planner.py").write_text(
    "# Waypoint Planner\nclass WaypointPlanner:\n    def plan(self, start, goal): pass\n"
)
(workspace / "src/perception" / "visual_odometry.py").write_text(
    "# Visual Odometry Module\nclass VO:\n    pass\n"
)
(workspace / "src/perception" / "lidar_processor.py").write_text(
    "# LiDAR Point Cloud Processor\n"
)
(workspace / "docs/hardware" / "drone_specs.md").write_text(
    "# Drone Specifications\n\n- Frame: 450mm\n- Motors: 2312 960kv\n- Flight controller: Pixhawk 6C\n"
)
(workspace / "docs/meetings" / "2026-03-28-standup.md").write_text(
    "## Standup 2026-03-28\n\n- Sensor fusion 25% done\n- Need to finish Kalman filter by end of week\n"
)
(workspace / "experiments/flight_logs" / "flight_001.csv").write_text(
    "timestamp,x,y,z,roll,pitch,yaw\n1,0.0,0.0,1.5,0.01,-0.02,0.0\n"
)
(workspace / "experiments/sim_results" / "sim_run_042.json").write_text(
    json.dumps({"run_id": 42, "success": True, "distance_error_m": 0.3}, indent=2)
)
(workspace / "config" / "flight_params.yaml").write_text(
    "max_altitude: 120\nmax_speed: 15\nrtl_altitude: 30\n"
)
(workspace / "tests" / "test_kalman.py").write_text(
    "import pytest\ndef test_kalman_convergence(): assert True\n"
)
(workspace / "reports/q1" / "q1_progress.md").write_text(
    "# Q1 Progress Report\n\n## Summary\nSensor fusion module 25% complete.\n"
)

# ── A stale/incomplete tasks.json backup to confuse naive agents ──
(tasks_dir / "tasks.json.bak").write_text(
    '{"tasks": [{"id": "TSK-OLD-001", "name": "old task", "status": "cancelled"}]}'
)

# ── A fake task log in wrong location (distractor) ──
(workspace / "reports/q1" / "task_log_old.md").write_text(
    "# Old Task Log\n\nThis is a legacy log file from before the task manager.\n"
)

print("Workspace initialized successfully.")
print(f"Existing task: TSK-20260310-001 (sensor fusion, 25% progress, 1/4 subtasks done)")
print(f"Distractor memory/ dir created at {workspace / 'memory'}")