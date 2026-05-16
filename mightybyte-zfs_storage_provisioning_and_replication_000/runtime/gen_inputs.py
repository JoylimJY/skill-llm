#!/usr/bin/env python3
import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# --- Directory Structure ---
dirs = [
    "storage_project/docs",
    "storage_project/scripts",
    "storage_project/configs/legacy",
    "storage_project/configs/proposed",
    "storage_project/reports",
    "storage_project/archive/2023",
    "storage_project/archive/2024",
    "storage_project/monitoring",
    "storage_project/references",
    "tmp_scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor Files ---
# Legacy config (wrong settings - ashift missing, wrong recordsize)
legacy_config = {
    "pool_name": "analytics_pool",
    "vdev_type": "stripe",
    "note": "DRAFT - do not use",
    "ashift": "NOT SET",
    "datasets": {
        "postgres": {"recordsize": "128K", "compression": "off"},
        "media": {"recordsize": "512K", "compression": "gzip"},
    }
}
(WORKSPACE / "storage_project/configs/legacy/pool_config_v1.json").write_text(
    json.dumps(legacy_config, indent=2)
)

# Another distractor: old notes
(WORKSPACE / "storage_project/docs/old_notes.txt").write_text(
    "TODO: figure out correct ashift for new drives\n"
    "Someone mentioned ashift=9 might work? Need to verify.\n"
    "recordsize for postgres - is it 64K or 128K?\n"
    "Don't forget to enable compression but gzip is probably fine.\n"
)

# Monitoring placeholder
(WORKSPACE / "storage_project/monitoring/alerts.txt").write_text(
    "ALERT: Pool utilization above 80% threshold on analytics_pool_OLD (decommissioned)\n"
    "ALERT: No scrub scheduled\n"
)

# Old shell script with wrong approach (file-backed but no ashift)
(WORKSPACE / "storage_project/scripts/old_setup.sh").write_text(
    "#!/bin/bash\n"
    "# OLD APPROACH - DO NOT USE\n"
    "truncate -s 5G /tmp/pool1.img\n"
    "zpool create analytics_pool /tmp/pool1.img\n"
    "zfs create analytics_pool/postgres\n"
    "echo 'Done'\n"
)

# References directory with some docs
(WORKSPACE / "storage_project/references/database_requirements.txt").write_text(
    "PostgreSQL Analytics DB Requirements:\n"
    "- Dataset: postgres\n"
    "- Expected size: 500GB\n"
    "- Critical data, must be durable\n"
    "- Access pattern: random 8K reads/writes\n\n"
    "Media Archive Requirements:\n"
    "- Dataset: media\n"
    "- Large sequential video/image files\n"
    "- Expected size: 2TB\n\n"
    "Backup Requirements:\n"
    "- Dataset: backups\n"
    "- Receives ZFS send streams from postgres and media\n"
    "- Must preserve original properties\n"
    "- Keep last 3 daily snapshots, destroy older ones\n"
)

# Proposed config (partially correct but missing key properties)
proposed_config = {
    "pool_name": "datastore",
    "backup_pool_name": "backupstore",
    "datasets": ["postgres", "media", "backups"],
    "status": "PENDING IMPLEMENTATION"
}
(WORKSPACE / "storage_project/configs/proposed/pool_config_v2.json").write_text(
    json.dumps(proposed_config, indent=2)
)

# Archive distractor files
for year in ["2023", "2024"]:
    for i in range(3):
        (WORKSPACE / f"storage_project/archive/{year}/report_{i}.txt").write_text(
            f"Archive report {i} from {year}\nStatus: completed\n"
        )

# Monitoring scripts (distractors)
(WORKSPACE / "storage_project/monitoring/check_disk.sh").write_text(
    "#!/bin/bash\ndf -h\n"
)

# Scratch files
for i in range(4):
    (WORKSPACE / f"tmp_scratch/scratch_{i}.tmp").write_text(f"temp data {random.randint(1000,9999)}\n")

# The target output file location hint embedded in the requirements doc (business context only)
(WORKSPACE / "storage_project/reports/.gitkeep").write_text("")

# Task specification
task_spec = {
    "task": "Storage Provisioning for Analytics Platform",
    "requester": "Infrastructure Team",
    "output_report": "storage_status.json",
    "output_report_location": "storage_project/reports/",
    "pools": {
        "primary": {
            "name": "datastore",
            "backing_files": ["/tmp/disk_primary_a.img", "/tmp/disk_primary_b.img"],
            "note": "Test/CI environment - file-backed is acceptable"
        },
        "backup": {
            "name": "backupstore",
            "backing_file": "/tmp/disk_backup.img",
            "note": "Test/CI environment - file-backed is acceptable"
        }
    },
    "datasets_on_primary": ["postgres", "media", "backups"],
    "snapshot_retention": {
        "prefix": "daily",
        "keep_count": 3,
        "note": "Simulate by creating 5 snapshots then rotating to keep only 3"
    }
}
(WORKSPACE / "storage_project/configs/proposed/task_spec.json").write_text(
    json.dumps(task_spec, indent=2)
)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")