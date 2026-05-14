#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw Active Maintenance task.
Usage: python3 eval.py <workspace_dir>
"""
import json
import sys
import os
from pathlib import Path

def load_manifest(workspace: Path):
    p = workspace / "config" / ".eval_manifest.json"
    return json.loads(p.read_text())

def run_checks(workspace: Path):
    checks = []
    score_parts = []

    try:
        manifest = load_manifest(workspace)
    except Exception as e:
        return [{"name": "manifest_load", "passed": False, "detail": str(e)}], 0.0

    # ── CHECK 1: Old temp files were removed ─────────────────────────────────
    removed_all = True
    missing_removals = []
    for f in manifest["old_temp_files"]:
        if Path(f).exists():
            removed_all = False
            missing_removals.append(f)
    checks.append({
        "name": "old_temp_files_cleaned",
        "passed": removed_all,
        "detail": (
            "All old temp files successfully removed."
            if removed_all
            else f"Still present: {missing_removals}"
        ),
    })
    score_parts.append(0.25 if removed_all else 0.0)

    # ── CHECK 2: Recent temp files were NOT removed ───────────────────────────
    kept_all = True
    wrongly_deleted = []
    for f in manifest["recent_temp_files"]:
        if not Path(f).exists():
            kept_all = False
            wrongly_deleted.append(f)
    checks.append({
        "name": "recent_temp_files_preserved",
        "passed": kept_all,
        "detail": (
            "All recent temp files correctly preserved."
            if kept_all
            else f"Wrongly deleted: {wrongly_deleted}"
        ),
    })
    score_parts.append(0.15 if kept_all else 0.0)

    # ── CHECK 3: Duplicate memory fragments removed ───────────────────────────
    dups_removed = True
    surviving_dups = []
    for f in manifest["duplicate_fragments"]:
        if Path(f).exists():
            dups_removed = False
            surviving_dups.append(f)
    checks.append({
        "name": "duplicate_fragments_removed",
        "passed": dups_removed,
        "detail": (
            "All exact duplicate fragments removed."
            if dups_removed
            else f"Duplicates still present: {surviving_dups}"
        ),
    })
    score_parts.append(0.20 if dups_removed else 0.0)

    # ── CHECK 4: Original fragments preserved ────────────────────────────────
    originals_ok = True
    missing_originals = []
    for f in manifest["original_fragments"]:
        if not Path(f).exists():
            originals_ok = False
            missing_originals.append(f)
    checks.append({
        "name": "original_fragments_preserved",
        "passed": originals_ok,
        "detail": (
            "All original fragments intact."
            if originals_ok
            else f"Originals missing: {missing_originals}"
        ),
    })
    score_parts.append(0.10 if originals_ok else 0.0)

    # ── CHECK 5: Near-duplicate NOT removed ──────────────────────────────────
    near_dup_path = Path(manifest["near_dup_fragment"])
    near_dup_ok = near_dup_path.exists()
    checks.append({
        "name": "near_duplicate_preserved",
        "passed": near_dup_ok,
        "detail": (
            "Near-duplicate (non-exact) fragment correctly preserved."
            if near_dup_ok
            else "Near-duplicate was incorrectly deleted."
        ),
    })
    score_parts.append(0.05 if near_dup_ok else 0.0)

    # ── CHECK 6: Distilled notes created ─────────────────────────────────────
    notes_dir = workspace / "MEMORY" / "notes"
    distilled_files = list(notes_dir.glob("*_distilled.txt")) if notes_dir.exists() else []
    distill_ok = len(distilled_files) >= 2
    distill_detail = f"Found {len(distilled_files)} distilled note(s)."
    # Verify content quality: at least one signal-word line per distilled file
    content_ok = True
    for df in distilled_files:
        try:
            content = df.read_text()
            signal_words = ("Insight:", "Key", "Core", "key", "core",
                            "finding", "Finding", "Confirmed", "confirmed",
                            "validated", "Validated")
            has_signal = any(any(line.strip().startswith(sw) for sw in signal_words)
                             for line in content.splitlines())
            if not has_signal:
                content_ok = False
                distill_detail += f" {df.name} has no signal lines."
        except Exception as ex:
            content_ok = False
            distill_detail += f" Error reading {df.name}: {ex}"
    distill_passed = distill_ok and content_ok
    checks.append({
        "name": "notes_distilled",
        "passed": distill_passed,
        "detail": distill_detail,
    })
    score_parts.append(0.10 if distill_passed else 0.0)

    # ── CHECK 7: Decision log written to MEMORY/DECISIONS/ ───────────────────
    decisions_dir = workspace / "MEMORY" / "DECISIONS"
    decision_files = list(decisions_dir.glob("*.json")) if decisions_dir.exists() else []
    decision_written = False
    decision_detail = "No decision log found in MEMORY/DECISIONS/."
    for df in decision_files:
        try:
            record = json.loads(df.read_text())
            has_title   = "title" in record and isinstance(record["title"], str) and len(record["title"]) > 0
            has_summary = "summary" in record and isinstance(record["summary"], str)
            has_details = "details" in record and isinstance(record["details"], dict)
            has_ts      = "timestamp" in record
            if has_title and has_summary and has_details and has_ts:
                decision_written = True
                decision_detail = (
                    f"Valid decision log found: {df.name} | "
                    f"title='{record['title']}' | summary='{record['summary'][:80]}'"
                )
                break
        except Exception as ex:
            decision_detail += f" Parse error on {df.name}: {ex}"
    checks.append({
        "name": "decision_logged",
        "passed": decision_written,
        "detail": decision_detail,
    })
    score_parts.append(0.10 if decision_written else 0.0)

    # ── CHECK 8: Decision log references actual results ───────────────────────
    results_reflected = False
    results_detail = "Decision log does not reference cleaned/dedup/distilled counts."
    for df in decision_files:
        try:
            record = json.loads(df.read_text())
            details = record.get("details", {})
            cleaned   = details.get("cleaned_files", [])
            duped     = details.get("duplicates_removed", [])
            distilled = details.get("distilled_notes", [])
            if len(cleaned) >= 1 and len(duped) >= 1:
                results_reflected = True
                results_detail = (
                    f"Decision log correctly reflects: "
                    f"{len(cleaned)} cleaned, {len(duped)} deduped, {len(distilled)} distilled."
                )
                break
        except Exception:
            pass
    checks.append({
        "name": "decision_log_reflects_results",
        "passed": results_reflected,
        "detail": results_detail,
    })
    score_parts.append(0.05 if results_reflected else 0.0)

    # ── CHECK 9: TEMP_DIRS was actually configured (not left empty) ───────────
    optimizer_path = workspace / "scripts" / "nightly_optimizer.py"
    config_set = False
    config_detail = "Could not verify TEMP_DIRS configuration."
    try:
        src = optimizer_path.read_text()
        # Look for TEMP_DIRS being set to a non-empty list
        import re
        match = re.search(r'TEMP_DIRS\s*=\s*(\[.*?\])', src, re.DOTALL)
        if match:
            try:
                val = json.loads(match.group(1).replace("'", '"'))
                if isinstance(val, list) and len(val) > 0:
                    config_set = True
                    config_detail = f"TEMP_DIRS configured with {len(val)} director(y/ies): {val}"
                else:
                    config_detail = "TEMP_DIRS is still an empty list — not configured."
            except Exception:
                # Non-JSON list notation — check it's not just []
                raw = match.group(1).strip()
                if raw != "[]":
                    config_set = True
                    config_detail = f"TEMP_DIRS appears non-empty: {raw[:120]}"
                else:
                    config_detail = "TEMP_DIRS is still []."
    except Exception as ex:
        config_detail = f"Error reading optimizer: {ex}"
    checks.append({
        "name": "temp_dirs_configured",
        "passed": config_set,
        "detail": config_detail,
    })
    score_parts.append(0.0)   # informational — weight captured by check 1

    total_score = sum(score_parts)
    return checks, round(total_score, 4)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks, score = run_checks(workspace)
    passed = score >= 0.70  # must pass at least 70 % of weighted score

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()