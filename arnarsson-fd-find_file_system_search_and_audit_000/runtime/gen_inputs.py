import os
import random
import time
import subprocess
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "studio/projects/album_alpha/tracks",
    "studio/projects/album_alpha/stems",
    "studio/projects/album_beta/tracks",
    "studio/projects/album_beta/stems",
    "studio/projects/album_beta/fx",
    "studio/projects/archive/2022/sessions",
    "studio/projects/archive/2023/sessions",
    "studio/staging/incoming",          # will be gitignored
    "studio/staging/review",            # will be gitignored
    "studio/assets/sfx/nature",
    "studio/assets/sfx/urban",
    "studio/assets/music/loops",
    "studio/assets/music/oneshots",
    "studio/tools/scripts",
    "studio/tools/configs",
    "studio/exports/final",
    "studio/exports/drafts",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Init git repo so .gitignore is respected ─────────────────────────────────
subprocess.run(["git", "init", str(WORKSPACE / "studio")], check=True,
               capture_output=True)

gitignore_content = "staging/\n"
(WORKSPACE / "studio" / ".gitignore").write_text(gitignore_content)

# ── Helper: create a file with a specific size and mtime ────────────────────
def make_file(path: Path, size_bytes: int, mtime_days_ago: float):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (b"AUDIODATA" * (size_bytes // 9 + 1))[:size_bytes]
    path.write_bytes(data)
    ts = time.time() - mtime_days_ago * 86400
    os.utime(path, (ts, ts))

# ── TARGET files: .wav, size 150KB–800KB, modified 2–7 days ago ─────────────
# These should appear in audit_report.txt (some are in gitignored staging dirs)

targets = [
    # visible (non-ignored) locations
    ("studio/projects/album_alpha/tracks/lead_guitar_v2.wav",         250_000, 3.0),
    ("studio/projects/album_beta/tracks/bass_line_final.wav",         520_000, 5.5),
    ("studio/projects/album_beta/stems/drums_overhead.wav",           180_000, 2.5),
    ("studio/assets/sfx/urban/city_ambience_long.wav",                750_000, 6.9),
    ("studio/assets/music/loops/groove_loop_120bpm.wav",              300_000, 4.0),
    # inside gitignored staging/ — must use -I flag to find these
    ("studio/staging/incoming/vocal_take_03.wav",                     400_000, 3.5),
    ("studio/staging/review/synth_pad_edit.wav",                      600_000, 6.0),
]

target_basenames = set()
for rel, size, days in targets:
    p = WORKSPACE / rel
    make_file(p, size, days)
    target_basenames.add(p.name)

# ── DISTRACTOR files: wrong extension, wrong size, wrong time, wrong depth ──

# Wrong extension (.mp3, .aiff, .txt) – correct size and time
make_file(WORKSPACE / "studio/projects/album_alpha/tracks/reference_mix.mp3",  300_000, 3.0)
make_file(WORKSPACE / "studio/projects/album_beta/fx/reverb_tail.aiff",        450_000, 4.5)
make_file(WORKSPACE / "studio/tools/configs/session_notes.txt",                200_000, 2.0)

# Correct extension but TOO SMALL (<150KB)
make_file(WORKSPACE / "studio/assets/sfx/nature/bird_chirp.wav",        50_000, 3.0)
make_file(WORKSPACE / "studio/assets/music/oneshots/kick_tight.wav",    80_000, 5.0)
make_file(WORKSPACE / "studio/exports/drafts/intro_sting_short.wav",   120_000, 4.0)

# Correct extension but TOO LARGE (>800KB)
make_file(WORKSPACE / "studio/projects/archive/2023/sessions/full_session_raw.wav", 2_000_000, 3.0)
make_file(WORKSPACE / "studio/exports/final/master_stereo.wav",                    1_500_000, 6.0)

# Correct extension + size but TOO RECENT (<2 days ago)
make_file(WORKSPACE / "studio/projects/album_beta/tracks/scratch_vocal.wav",  250_000, 0.5)
make_file(WORKSPACE / "studio/staging/incoming/hot_fix_mix.wav",               350_000, 1.0)

# Correct extension + size but TOO OLD (>7 days ago)
make_file(WORKSPACE / "studio/projects/archive/2022/sessions/old_master.wav",  400_000, 14.0)
make_file(WORKSPACE / "studio/assets/sfx/urban/rain_loop_archive.wav",         700_000, 30.0)

# Correct extension + size + time but TOO DEEP (depth > 4 from studio root)
deep_dir = WORKSPACE / "studio/projects/album_alpha/stems/sub/deep"
deep_dir.mkdir(parents=True, exist_ok=True)
make_file(deep_dir / "hidden_deep_track.wav", 300_000, 4.0)

# Correct .wav + size + time, but a DIRECTORY named .wav (edge case)
wav_dir = WORKSPACE / "studio/assets/music/loops/fake_audio.wav"
wav_dir.mkdir(parents=True, exist_ok=True)

# Miscellaneous distractors
make_file(WORKSPACE / "studio/tools/scripts/batch_export.sh",           1_000, 3.0)
make_file(WORKSPACE / "studio/tools/configs/render_preset.json",        5_000, 2.0)
make_file(WORKSPACE / "studio/projects/album_alpha/stems/dry_vox.aiff", 250_000, 3.5)

# ── Write the ground-truth list for evaluator (hidden from agent) ─────────────
truth_path = WORKSPACE / ".audit_ground_truth.txt"
truth_path.write_text("\n".join(sorted(target_basenames)) + "\n")
print("Ground truth basenames:")
for n in sorted(target_basenames):
    print(" ", n)
print("Workspace setup complete.")