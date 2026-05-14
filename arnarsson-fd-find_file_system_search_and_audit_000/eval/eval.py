import sys
import json
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []

    # ── Load ground truth ────────────────────────────────────────────────────
    truth_file = ws / ".audit_ground_truth.txt"
    try:
        expected_basenames = set(truth_file.read_text().split())
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "ground_truth_load", "passed": False,
                        "detail": f"Could not load ground truth: {e}"}]
        }

    # ── Find audit_report.txt ────────────────────────────────────────────────
    candidates = list(ws.rglob("audit_report.txt"))

    check_exists = {
        "name": "audit_report_exists",
        "passed": len(candidates) >= 1,
        "detail": f"Found {len(candidates)} audit_report.txt file(s)."
    }
    checks.append(check_exists)

    if not check_exists["passed"]:
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]

    try:
        raw = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False,
                       "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Parse: one basename per non-empty line, strip whitespace
    reported_lines = [l.strip() for l in raw.splitlines() if l.strip()]
    reported_basenames = set(reported_lines)

    # ── Check 1: All target .wav files are present ───────────────────────────
    missing = expected_basenames - reported_basenames
    check_all_targets = {
        "name": "all_target_wavs_present",
        "passed": len(missing) == 0,
        "detail": (f"Missing targets: {sorted(missing)}" if missing
                   else "All 7 target .wav files found in report.")
    }
    checks.append(check_all_targets)

    # ── Check 2: Gitignored staging files ARE included ───────────────────────
    staging_targets = {"vocal_take_03.wav", "synth_pad_edit.wav"}
    found_staging = staging_targets & reported_basenames
    check_staging = {
        "name": "gitignored_staging_files_included",
        "passed": found_staging == staging_targets,
        "detail": (f"Staging files found: {sorted(found_staging)}; "
                   f"expected: {sorted(staging_targets)}")
    }
    checks.append(check_staging)

    # ── Check 3: No distractor files included ───────────────────────────────
    known_distractors = {
        "reference_mix.mp3",
        "reverb_tail.aiff",
        "session_notes.txt",
        "bird_chirp.wav",         # too small
        "kick_tight.wav",         # too small
        "intro_sting_short.wav",  # too small
        "full_session_raw.wav",   # too large
        "master_stereo.wav",      # too large
        "scratch_vocal.wav",      # too recent
        "hot_fix_mix.wav",        # too recent (also gitignored)
        "old_master.wav",         # too old
        "rain_loop_archive.wav",  # too old
        "hidden_deep_track.wav",  # too deep
        "batch_export.sh",
        "render_preset.json",
        "dry_vox.aiff",
    }
    false_positives = known_distractors & reported_basenames
    check_no_distractors = {
        "name": "no_distractor_files_included",
        "passed": len(false_positives) == 0,
        "detail": (f"False positives found: {sorted(false_positives)}"
                   if false_positives else "No distractor files in report.")
    }
    checks.append(check_no_distractors)

    # ── Check 4: Report contains only basenames (no path separators) ─────────
    lines_with_slash = [l for l in reported_lines if "/" in l or "\\" in l]
    check_basenames_only = {
        "name": "basenames_only_no_paths",
        "passed": len(lines_with_slash) == 0,
        "detail": (f"Lines containing path separators: {lines_with_slash[:5]}"
                   if lines_with_slash
                   else "All lines are bare filenames (no paths).")
    }
    checks.append(check_basenames_only)

    # ── Check 5: Correct count (exactly 7 entries) ───────────────────────────
    check_count = {
        "name": "correct_entry_count",
        "passed": len(reported_basenames) == len(expected_basenames),
        "detail": (f"Report has {len(reported_basenames)} unique entries; "
                   f"expected {len(expected_basenames)}.")
    }
    checks.append(check_count)

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall = all(c["passed"] for c in checks)

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))