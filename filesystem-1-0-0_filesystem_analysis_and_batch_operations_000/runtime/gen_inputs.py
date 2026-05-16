#!/usr/bin/env python3
import os
import random
import string
import time

random.seed(42)

BASE = "/workspace/project_archive"

# Directory structure for a post-production studio archive
dirs = [
    "project_archive",
    "project_archive/renders/episode_01",
    "project_archive/renders/episode_02",
    "project_archive/renders/episode_03",
    "project_archive/audio/dialogue",
    "project_archive/audio/sfx",
    "project_archive/audio/music",
    "project_archive/logs/transcode",
    "project_archive/logs/render",
    "project_archive/logs/export",
    "project_archive/assets/textures",
    "project_archive/assets/models",
    "project_archive/assets/scripts",
    "project_archive/temp",
    "project_archive/temp/scratch",
    "project_archive/deliverables/final",
    "project_archive/deliverables/review",
    "project_archive/archive_old",
    "project_archive/archive_old/season1",
    "project_archive/cache",
    "project_archive/cache/previews",
]

for d in dirs:
    os.makedirs(f"/workspace/{d}", exist_ok=True)

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def write_binary_file(path, size_bytes):
    with open(path, 'wb') as f:
        f.write(bytes(random.getrandbits(8) for _ in range(size_bytes)))

# --- Markdown / config files (distractors) ---
write_file(f"{BASE}/renders/episode_01/shot_001.md",
    "# Shot 001\nStatus: APPROVED\nNotes: Final color grade done.\nTIMECODE: 00:01:23\n")
write_file(f"{BASE}/renders/episode_01/shot_002.md",
    "# Shot 002\nStatus: PENDING\nNotes: Awaiting VFX compositing.\nTIMECODE: 00:02:10\n")
write_file(f"{BASE}/renders/episode_02/shot_010.md",
    "# Shot 010\nStatus: APPROVED\nNotes: Scene transition.\nTIMECODE: 00:05:44\n")
write_file(f"{BASE}/renders/episode_02/shot_011.md",
    "# Shot 011\nStatus: REVISION\nNotes: Re-render required.\nTIMECODE: 00:06:02\n")
write_file(f"{BASE}/renders/episode_03/shot_020.md",
    "# Shot 020\nStatus: APPROVED\nNotes: Done.\nTIMECODE: 00:10:00\n")
write_file(f"{BASE}/assets/scripts/pipeline.py",
    "# Pipeline automation\nimport os\n\ndef process():\n    pass\n# TIMECODE: 00:00:00\n")
write_file(f"{BASE}/assets/scripts/color_grade.py",
    "# Color grading script\n# Status: APPROVED\n\ndef apply_lut(lut_path):\n    pass\n")
write_file(f"{BASE}/assets/scripts/export_dcp.py",
    "# DCP Export\n# Status: REVISION\n\ndef export():\n    pass\n")
write_file(f"{BASE}/deliverables/final/episode_01_v3.txt",
    "Delivery package: episode_01_v3\nStatus: APPROVED\nRecipient: Broadcast\n")
write_file(f"{BASE}/deliverables/review/episode_02_draft.txt",
    "Delivery package: episode_02_draft\nStatus: PENDING\nRecipient: Director\n")
write_file(f"{BASE}/audio/dialogue/ep01_dialogue_mix.wav.meta",
    "codec: PCM\nsample_rate: 48000\nStatus: APPROVED\n")
write_file(f"{BASE}/audio/sfx/ep01_sfx.wav.meta",
    "codec: PCM\nsample_rate: 48000\nStatus: APPROVED\n")
write_file(f"{BASE}/audio/music/ep01_score.wav.meta",
    "composer: John Smith\nStatus: REVISION\n")

# --- .tmp files (to be cleaned) ---
for i in range(6):
    write_file(f"{BASE}/temp/scratch/work_{i}.tmp",
        f"scratch data {i}\n" + "x" * random.randint(100, 500))
write_file(f"{BASE}/cache/tmp_preview_001.tmp",
    "cache preview data\n" * 10)
write_file(f"{BASE}/cache/tmp_preview_002.tmp",
    "cache preview data 2\n" * 10)
write_file(f"{BASE}/renders/episode_01/render_temp.tmp",
    "intermediate render buffer\n" * 5)

# --- Log files: some "old" (simulate >30 days), some recent ---
# Old transcode logs (should be found as stale)
old_time = time.time() - (35 * 24 * 3600)  # 35 days ago

old_log_paths = [
    f"{BASE}/logs/transcode/ep01_transcode_2024.log",
    f"{BASE}/logs/transcode/ep02_transcode_2024.log",
    f"{BASE}/logs/render/ep01_render_batch_jan.log",
]
for p in old_log_paths:
    write_file(p, f"[INFO] Transcode started\n[INFO] Processing frames...\n[ERROR] Frame drop detected\n[INFO] Transcode complete\n" * 20)
    os.utime(p, (old_time, old_time))

# Recent logs (should NOT be deleted)
recent_log_paths = [
    f"{BASE}/logs/transcode/ep03_transcode_latest.log",
    f"{BASE}/logs/render/ep03_render_batch_latest.log",
    f"{BASE}/logs/export/ep03_export.log",
]
for p in recent_log_paths:
    write_file(p, f"[INFO] Processing started\n[INFO] All frames OK\n[INFO] Done\n" * 10)

# --- Large asset files (>1MB) to identify ---
# These should be flagged as "large"
write_binary_file(f"{BASE}/assets/textures/env_texture_4k.exr", 2 * 1024 * 1024)   # 2MB
write_binary_file(f"{BASE}/assets/textures/char_texture_hd.exr", 1 * 1024 * 1024 + 512)  # ~1MB
write_binary_file(f"{BASE}/assets/models/hero_char_v2.obj", 1 * 1024 * 1024 + 100)   # ~1MB
write_binary_file(f"{BASE}/archive_old/season1/ep01_raw_export.mxf", 3 * 1024 * 1024)  # 3MB

# Small files for contrast
write_file(f"{BASE}/assets/textures/logo_small.png", "PNG_STUB\n" * 10)
write_file(f"{BASE}/assets/models/prop_chair.obj", "v 0 0 0\nv 1 0 0\nf 1 2\n")
write_file(f"{BASE}/archive_old/season1/notes.txt", "Season 1 archival notes\nDo not delete.\n")

# --- Files with "REVISION" status (to be moved to quarantine) ---
# Already created some above; add more
write_file(f"{BASE}/renders/episode_03/shot_021.md",
    "# Shot 021\nStatus: REVISION\nNotes: Motion blur issue.\nTIMECODE: 00:11:30\n")
write_file(f"{BASE}/deliverables/review/ep03_revision_notes.txt",
    "Status: REVISION\nRequired changes: Color timing off in act 2.\n")
write_file(f"{BASE}/assets/scripts/ingest_tool.py",
    "# Ingest tool\n# Status: REVISION\n\ndef ingest(path):\n    raise NotImplementedError\n")

# --- Empty directories (should be cleaned up) ---
os.makedirs(f"{BASE}/cache/previews/empty_batch_1", exist_ok=True)
os.makedirs(f"{BASE}/cache/previews/empty_batch_2", exist_ok=True)
os.makedirs(f"{BASE}/temp/scratch/empty_job_99", exist_ok=True)

print("Workspace generated successfully.")
print(f"Structure rooted at: {BASE}")