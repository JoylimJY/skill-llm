#!/usr/bin/env python3
"""
Generate the sandbox workspace for the aria2 download pipeline audit task.
Creates the skill directory structure, distractor files, and a pre-seeded
mock server state file.
"""

import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Create distractor directory structure ──────────────────────────────────
dirs = [
    "projects/media-ingest/raw",
    "projects/media-ingest/processed",
    "projects/media-ingest/archive",
    "projects/media-ingest/logs",
    "projects/vfx/renders/shot_001",
    "projects/vfx/renders/shot_002",
    "tools/ffmpeg-wrappers",
    "tools/color-grading",
    "config/profiles",
    "config/presets",
    "reports",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/media-ingest/logs/ingest_2024-01-15.log": "INFO: 42 assets ingested\nWARN: 3 assets skipped\n",
    "projects/media-ingest/logs/ingest_2024-01-16.log": "INFO: 17 assets ingested\n",
    "projects/media-ingest/archive/manifest_jan.csv": "filename,size,status\nshot_001.mov,4294967296,archived\nshot_002.mov,2147483648,archived\n",
    "projects/vfx/renders/shot_001/render.log": "[frame 001/240] rendered\n[frame 002/240] rendered\n",
    "projects/vfx/renders/shot_002/render.log": "[frame 001/120] rendered\n",
    "tools/ffmpeg-wrappers/transcode.sh": "#!/bin/bash\nffmpeg -i $1 -c:v libx264 $2\n",
    "tools/color-grading/lut_apply.py": "# LUT application script\nprint('applying LUT')\n",
    "config/profiles/high_quality.json": json.dumps({"bitrate": "50M", "codec": "prores"}),
    "config/profiles/proxy.json": json.dumps({"bitrate": "5M", "codec": "h264"}),
    "config/presets/ingest_default.json": json.dumps({"fps": 24, "resolution": "4K"}),
    "tmp/old_download_list.txt": "# old downloads - do not use\nhttp://old-server/file1.mxf\n",
    "reports/.gitkeep": "",
}
for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── 2. Create the aria2-json-rpc skill directory structure ────────────────────
skill_base = os.path.join(WORKSPACE, "skills", "aria2-json-rpc")
skill_scripts = os.path.join(skill_base, "scripts")
skill_examples = os.path.join(skill_scripts, "examples")
skill_refs = os.path.join(skill_base, "references")

for d in [skill_scripts, skill_examples, skill_refs]:
    os.makedirs(d, exist_ok=True)

# ── 3. Create mock server state (the fake aria2 RPC state) ───────────────────
# This file will be read by the mock server to serve deterministic responses.
# Pre-seeded downloads: 2 active, 1 paused, 2 complete, 1 error
mock_state = {
    "downloads": {
        "aabbccdd11223344": {
            "gid": "aabbccdd11223344",
            "status": "active",
            "totalLength": "1073741824",
            "completedLength": "536870912",
            "downloadSpeed": "2097152",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/4K_master_shot001.mxf", "length": "1073741824", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        },
        "bbccddee22334455": {
            "gid": "bbccddee22334455",
            "status": "active",
            "totalLength": "524288000",
            "completedLength": "104857600",
            "downloadSpeed": "1048576",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/proxy_shot002.mp4", "length": "524288000", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        },
        "ccddee0033445566": {
            "gid": "ccddee0033445566",
            "status": "paused",
            "totalLength": "2147483648",
            "completedLength": "0",
            "downloadSpeed": "0",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/4K_master_shot003.mxf", "length": "2147483648", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        },
        "ddeeff0044556677": {
            "gid": "ddeeff0044556677",
            "status": "complete",
            "totalLength": "314572800",
            "completedLength": "314572800",
            "downloadSpeed": "0",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/audio_mix_v3.wav", "length": "314572800", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        },
        "eeff001155667788": {
            "gid": "eeff001155667788",
            "status": "complete",
            "totalLength": "157286400",
            "completedLength": "157286400",
            "downloadSpeed": "0",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/subtitle_pack_en.zip", "length": "157286400", "selected": "true"}],
            "errorCode": "0",
            "errorMessage": ""
        },
        "ff00112266778899": {
            "gid": "ff00112266778899",
            "status": "error",
            "totalLength": "1048576000",
            "completedLength": "52428800",
            "downloadSpeed": "0",
            "uploadSpeed": "0",
            "files": [{"path": "/downloads/vfx_plates_raw.dpx", "length": "1048576000", "selected": "true"}],
            "errorCode": "3",
            "errorMessage": "Resource not found"
        }
    },
    "global_stat": {
        "downloadSpeed": "3145728",
        "uploadSpeed": "0",
        "numActive": "2",
        "numWaiting": "1",
        "numStopped": "3",
        "numStoppedTotal": "3"
    },
    "global_options": {
        "max-concurrent-downloads": "5",
        "max-overall-download-limit": "0",
        "max-overall-upload-limit": "0",
        "dir": "/downloads"
    },
    "version": {
        "version": "1.36.0",
        "enabledFeatures": ["BitTorrent", "Firefox3 Cookie", "GZip", "HTTPS", "Message Digest", "Metalink", "XML-RPC", "SFTP"]
    },
    "options": {
        "aabbccdd11223344": {"max-download-limit": "0", "max-upload-limit": "0", "split": "5"},
        "bbccddee22334455": {"max-download-limit": "0", "max-upload-limit": "0", "split": "5"},
        "ccddee0033445566": {"max-download-limit": "0", "max-upload-limit": "0", "split": "5"},
    },
    "removed_results": []
}

state_file = os.path.join(WORKSPACE, "mock_aria2_state.json")
with open(state_file, "w") as f:
    json.dump(mock_state, f, indent=2)

# ── 4. Write the task brief (the agent's assignment) ─────────────────────────
task_brief = {
    "task": "download_pipeline_audit",
    "new_downloads": [
        {
            "url": "http://media-server.studio.local/rushes/day12_cam_A.mxf",
            "speed_limit_bytes": 512000,
            "label": "day12_cam_A"
        },
        {
            "url": "http://media-server.studio.local/rushes/day12_cam_B.mxf",
            "speed_limit_bytes": 512000,
            "label": "day12_cam_B"
        }
    ],
    "throttle_target_gid": "aabbccdd11223344",
    "throttle_speed_bytes": 512000
}

with open(os.path.join(WORKSPACE, "task_brief.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace generated successfully.")
print(f"Mock state file: {state_file}")
print(f"Task brief: {os.path.join(WORKSPACE, 'task_brief.json')}")