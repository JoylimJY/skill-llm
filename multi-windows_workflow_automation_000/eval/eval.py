import json
import sys
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def evaluate(workspace_root: str):
    workspace = Path(workspace_root)
    tasks_dir = workspace / "memory" / "tasks"

    checks = []
    total_score = 0.0
    max_score = 0.0

    # ─────────────────────────────────────────────
    # CHECK 1: tasks.json exists and is valid JSON with windows indexed
    # ─────────────────────────────────────────────
    max_score += 1.0
    tasks_json_path = tasks_dir / "tasks.json"
    tasks_data, err = load_json_safe(tasks_json_path)
    if err:
        checks.append({"name": "tasks.json_exists_and_valid", "passed": False,
                        "detail": f"tasks.json missing or invalid JSON: {err}"})
    else:
        # It should contain some kind of list/array of window entries
        # We look for any key whose value is a list with at least 2 entries
        found_windows = None
        if isinstance(tasks_data, list) and len(tasks_data) >= 2:
            found_windows = tasks_data
        elif isinstance(tasks_data, dict):
            for v in tasks_data.values():
                if isinstance(v, list) and len(v) >= 2:
                    found_windows = v
                    break
        if found_windows is not None:
            checks.append({"name": "tasks.json_has_multiple_windows", "passed": True,
                            "detail": f"tasks.json contains a list with {len(found_windows)} entries"})
            total_score += 1.0
        else:
            checks.append({"name": "tasks.json_has_multiple_windows", "passed": False,
                            "detail": f"tasks.json does not contain a list of >=2 window entries. Content: {str(tasks_data)[:300]}"})

    # ─────────────────────────────────────────────
    # CHECK 2: current.json exists and references a valid window
    # ─────────────────────────────────────────────
    max_score += 1.0
    current_json_path = tasks_dir / "current.json"
    current_data, err = load_json_safe(current_json_path)
    if err:
        checks.append({"name": "current.json_exists_and_valid", "passed": False,
                        "detail": f"current.json missing or invalid: {err}"})
    else:
        # Should have some id/window reference
        has_id = False
        if isinstance(current_data, dict):
            for key in ["id", "window_id", "current", "name", "window"]:
                if key in current_data and current_data[key]:
                    has_id = True
                    break
        if has_id:
            checks.append({"name": "current.json_exists_and_valid", "passed": True,
                            "detail": f"current.json is valid and references a window: {current_data}"})
            total_score += 1.0
        else:
            checks.append({"name": "current.json_exists_and_valid", "passed": False,
                            "detail": f"current.json exists but has no identifiable window reference: {current_data}"})

    # ─────────────────────────────────────────────
    # CHECK 3: At least 2 window directories exist under memory/tasks/
    # with the proprietary {ID}{名称} naming pattern (e.g., 0314-1客户调研)
    # ─────────────────────────────────────────────
    max_score += 1.5
    import re
    # Pattern: starts with MMDD-N (4 digits, dash, digit(s)) followed by Chinese or alphanumeric name
    window_dir_pattern = re.compile(r'^\d{4}-\d+.+')
    window_dirs = [
        d for d in tasks_dir.iterdir()
        if d.is_dir() and window_dir_pattern.match(d.name)
    ]

    if len(window_dirs) >= 2:
        checks.append({"name": "window_dirs_with_correct_naming", "passed": True,
                        "detail": f"Found {len(window_dirs)} window dirs: {[d.name for d in window_dirs]}"})
        total_score += 1.5
    elif len(window_dirs) == 1:
        checks.append({"name": "window_dirs_with_correct_naming", "passed": False,
                        "detail": f"Only 1 window dir found (need >=2): {[d.name for d in window_dirs]}"})
        total_score += 0.5
    else:
        checks.append({"name": "window_dirs_with_correct_naming", "passed": False,
                        "detail": f"No window directories matching pattern MMDD-N<name> found under {tasks_dir}. Dirs: {[d.name for d in tasks_dir.iterdir() if d.is_dir()]}"})

    # ─────────────────────────────────────────────
    # CHECK 4: Each window directory has meta.json with required fields
    # ─────────────────────────────────────────────
    max_score += 1.5
    meta_ok_count = 0
    meta_details = []
    for wdir in window_dirs:
        meta_path = wdir / "meta.json"
        meta_data, err = load_json_safe(meta_path)
        if err:
            meta_details.append(f"{wdir.name}: meta.json missing/invalid ({err})")
        else:
            # meta.json should have some identifying fields (id, name, status, created_at or similar)
            required_fields_present = sum(1 for k in ["id", "name", "status", "created"] 
                                           if k in (meta_data or {}))
            if required_fields_present >= 2:
                meta_ok_count += 1
                meta_details.append(f"{wdir.name}: meta.json OK ({list(meta_data.keys())})")
            else:
                meta_details.append(f"{wdir.name}: meta.json too sparse: {meta_data}")

    if meta_ok_count >= 2:
        checks.append({"name": "window_meta_json_valid", "passed": True,
                        "detail": " | ".join(meta_details)})
        total_score += 1.5
    elif meta_ok_count == 1:
        checks.append({"name": "window_meta_json_valid", "passed": False,
                        "detail": f"Only {meta_ok_count}/2 windows have valid meta.json. " + " | ".join(meta_details)})
        total_score += 0.5
    else:
        checks.append({"name": "window_meta_json_valid", "passed": False,
                        "detail": "No windows have valid meta.json. " + " | ".join(meta_details)})

    # ─────────────────────────────────────────────
    # CHECK 5: Each window directory has output/transcript.jsonl
    # ─────────────────────────────────────────────
    max_score += 1.0
    transcript_ok = 0
    transcript_details = []
    for wdir in window_dirs:
        transcript_path = wdir / "output" / "transcript.jsonl"
        if transcript_path.exists():
            transcript_ok += 1
            transcript_details.append(f"{wdir.name}: transcript.jsonl exists")
        else:
            transcript_details.append(f"{wdir.name}: transcript.jsonl MISSING at {transcript_path}")

    if transcript_ok >= 2:
        checks.append({"name": "transcript_jsonl_exists", "passed": True,
                        "detail": " | ".join(transcript_details)})
        total_score += 1.0
    elif transcript_ok == 1:
        checks.append({"name": "transcript_jsonl_exists", "passed": False,
                        "detail": f"Only {transcript_ok}/2 have transcript.jsonl. " + " | ".join(transcript_details)})
        total_score += 0.4
    else:
        checks.append({"name": "transcript_jsonl_exists", "passed": False,
                        "detail": "No window has output/transcript.jsonl. " + " | ".join(transcript_details)})

    # ─────────────────────────────────────────────
    # CHECK 6: At least one window has a non-empty summary.md
    # ─────────────────────────────────────────────
    max_score += 1.0
    summary_found = False
    summary_details = []
    for wdir in window_dirs:
        summary_path = wdir / "summary.md"
        if summary_path.exists():
            content = summary_path.read_text(encoding="utf-8").strip()
            if len(content) > 10:
                summary_found = True
                summary_details.append(f"{wdir.name}/summary.md: '{content[:80]}'")
            else:
                summary_details.append(f"{wdir.name}/summary.md: exists but nearly empty ('{content}')")
        else:
            summary_details.append(f"{wdir.name}/summary.md: missing")

    if summary_found:
        checks.append({"name": "summary_md_with_content", "passed": True,
                        "detail": " | ".join(summary_details)})
        total_score += 1.0
    else:
        checks.append({"name": "summary_md_with_content", "passed": False,
                        "detail": "No window has a meaningful summary.md. " + " | ".join(summary_details)})

    # ─────────────────────────────────────────────
    # CHECK 7: At least one window is marked as completed/done in meta.json
    # ─────────────────────────────────────────────
    max_score += 1.5
    completed_window = None
    completed_details = []
    for wdir in window_dirs:
        meta_path = wdir / "meta.json"
        meta_data, err = load_json_safe(meta_path)
        if meta_data and isinstance(meta_data, dict):
            status = str(meta_data.get("status", "")).lower()
            if any(s in status for s in ["done", "complete", "finished", "closed", "completed"]):
                completed_window = wdir.name
                completed_details.append(f"{wdir.name}: status='{meta_data.get('status')}'")
            else:
                completed_details.append(f"{wdir.name}: status='{meta_data.get('status', 'N/A')}'")

    if completed_window:
        checks.append({"name": "one_window_marked_complete", "passed": True,
                        "detail": f"Window '{completed_window}' is marked complete. " + " | ".join(completed_details)})
        total_score += 1.5
    else:
        checks.append({"name": "one_window_marked_complete", "passed": False,
                        "detail": "No window has status=done/complete/finished. " + " | ".join(completed_details)})

    # ─────────────────────────────────────────────
    # CHECK 8: current.json points to the NON-completed window
    # (after completing one window, current should be the other active one)
    # ─────────────────────────────────────────────
    max_score += 1.0
    if current_data and completed_window and isinstance(current_data, dict):
        current_id_str = str(current_data)
        # The current window should NOT be the completed one
        if completed_window not in current_id_str:
            checks.append({"name": "current_is_active_not_completed", "passed": True,
                            "detail": f"current.json points to a different window than the completed '{completed_window}'"})
            total_score += 1.0
        else:
            checks.append({"name": "current_is_active_not_completed", "passed": False,
                            "detail": f"current.json still references the completed window '{completed_window}'. current.json: {current_data}"})
    else:
        checks.append({"name": "current_is_active_not_completed", "passed": False,
                        "detail": "Cannot verify: either current.json or completed window info is missing."})

    # ─────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)