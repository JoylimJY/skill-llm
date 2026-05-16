import json
import sys
import os
from pathlib import Path
from datetime import datetime

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_eval(workspace):
    workspace = Path(workspace)
    okr_dir = workspace / ".okr-work-manager"
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── CHECK 1: okr_config.json uses correct OKR ID format ──────────────────
    max_score += 20
    check_name = "okr_config: correct OKR ID format (q_2025-Q4_N)"
    try:
        config = load_json(okr_dir / "okr_config.json")
        objectives = config.get("objectives", [])
        if not objectives:
            checks.append({"name": check_name, "passed": False, "detail": "No objectives found in okr_config.json"})
        else:
            ids = [o.get("id", "") for o in objectives]
            # Must have at least 2 objectives with correct format q_2025-Q4_N
            correct_ids = [id_ for id_ in ids if id_.startswith("q_2025-Q4_")]
            old_format = [id_ for id_ in ids if "OKR-Q4" in id_ or ("Q4" in id_ and not id_.startswith("q_"))]
            if len(correct_ids) >= 2 and len(old_format) == 0:
                total_score += 20
                checks.append({"name": check_name, "passed": True, "detail": f"Found correct IDs: {correct_ids}"})
            elif len(correct_ids) >= 1:
                total_score += 10
                checks.append({"name": check_name, "passed": False, "detail": f"Only {len(correct_ids)} correct IDs found (need >=2): {ids}"})
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"No correctly formatted OKR IDs found. Got: {ids}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error reading okr_config.json: {e}"})

    # ── CHECK 2: okr_config.json has version 2.0 and KR IDs follow convention ─
    max_score += 10
    check_name = "okr_config: version 2.0 and KR IDs follow q_2025-Q4_N_krN pattern"
    try:
        config = load_json(okr_dir / "okr_config.json")
        version_ok = str(config.get("version", "")).startswith("2")
        all_krs = []
        for obj in config.get("objectives", []):
            for kr in obj.get("key_results", []):
                all_krs.append(kr.get("id", ""))
        kr_format_ok = all(
            (kr_id.startswith("q_2025-Q4_") and "_kr" in kr_id) 
            for kr_id in all_krs
        ) if all_krs else False
        
        if version_ok and kr_format_ok and len(all_krs) >= 2:
            total_score += 10
            checks.append({"name": check_name, "passed": True, "detail": f"Version: {config.get('version')}, KR IDs: {all_krs}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"version_ok={version_ok}, kr_format_ok={kr_format_ok}, kr_count={len(all_krs)}, KR IDs: {all_krs}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 3: December daily logs created from raw notes ───────────────────
    max_score += 15
    check_name = "December daily logs created (at least 4 dates in Dec 2025)"
    try:
        dec_logs = list((okr_dir / "daily").glob("2025-12-*.json"))
        if len(dec_logs) >= 4:
            total_score += 15
            checks.append({"name": check_name, "passed": True, "detail": f"Found {len(dec_logs)} December logs: {sorted(f.name for f in dec_logs)}"})
        elif len(dec_logs) >= 2:
            total_score += 7
            checks.append({"name": check_name, "passed": False, "detail": f"Only {len(dec_logs)} December logs (need >=4): {sorted(f.name for f in dec_logs)}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Only {len(dec_logs)} December logs found"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 4: December logs reference correct OKR IDs ─────────────────────
    max_score += 10
    check_name = "December daily logs reference q_2025-Q4_N OKR IDs"
    try:
        dec_logs = list((okr_dir / "daily").glob("2025-12-*.json"))
        logs_with_correct_okr = 0
        logs_with_wrong_okr = 0
        for log_path in dec_logs:
            log_data = load_json(log_path)
            for entry in log_data.get("entries", []):
                okr_id = entry.get("okr_id", "")
                if okr_id and okr_id.startswith("q_2025-Q4_"):
                    logs_with_correct_okr += 1
                elif okr_id and okr_id not in (None, "", "null"):
                    logs_with_wrong_okr += 1
        
        if logs_with_correct_okr >= 4 and logs_with_wrong_okr == 0:
            total_score += 10
            checks.append({"name": check_name, "passed": True, "detail": f"{logs_with_correct_okr} entries with correct OKR IDs"})
        elif logs_with_correct_okr >= 2:
            total_score += 5
            checks.append({"name": check_name, "passed": False, "detail": f"{logs_with_correct_okr} correct, {logs_with_wrong_okr} wrong OKR ID format in Dec logs"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Insufficient correct OKR IDs in December logs: {logs_with_correct_okr} correct, {logs_with_wrong_okr} wrong"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 5: okr_progress.json updated with cumulative Q4 hours ──────────
    max_score += 10
    check_name = "okr_progress.json updated with Q4 cumulative hours"
    try:
        progress = load_json(okr_dir / "okr_progress.json")
        objectives_progress = progress.get("objectives", {})
        has_correct_ids = any(k.startswith("q_2025-Q4_") for k in objectives_progress.keys())
        has_hours = any(
            v.get("logged_hours", 0) > 0 
            for v in objectives_progress.values() 
            if isinstance(v, dict)
        )
        last_updated_recent = progress.get("last_updated", "") >= "2025-12"
        
        if has_correct_ids and has_hours and last_updated_recent:
            total_score += 10
            checks.append({"name": check_name, "passed": True, "detail": f"Progress updated with IDs: {list(objectives_progress.keys())}"})
        elif has_correct_ids and has_hours:
            total_score += 7
            checks.append({"name": check_name, "passed": False, "detail": f"Progress has correct IDs and hours, but last_updated={progress.get('last_updated')} is not December or later"})
        elif has_correct_ids:
            total_score += 3
            checks.append({"name": check_name, "passed": False, "detail": f"Progress has correct IDs but no logged_hours > 0"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"okr_progress.json still has wrong format or old IDs: {list(objectives_progress.keys())}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error reading okr_progress.json: {e}"})

    # ── CHECK 6: December monthly report exists ───────────────────────────────
    max_score += 10
    check_name = "December monthly report: monthly/2025-12-report.json exists"
    try:
        dec_report_path = okr_dir / "monthly" / "2025-12-report.json"
        if dec_report_path.exists():
            dec_report = load_json(dec_report_path)
            if dec_report.get("period") == "2025-12":
                total_score += 10
                checks.append({"name": check_name, "passed": True, "detail": f"Found with period={dec_report.get('period')}, total_hours={dec_report.get('total_hours')}"})
            else:
                total_score += 5
                checks.append({"name": check_name, "passed": False, "detail": f"File exists but period field is wrong: {dec_report.get('period')}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "monthly/2025-12-report.json not found"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 7: December monthly report has OKR alignment with correct IDs ───
    max_score += 5
    check_name = "December monthly report references q_2025-Q4_N OKR IDs"
    try:
        dec_report_path = okr_dir / "monthly" / "2025-12-report.json"
        dec_report = load_json(dec_report_path)
        alignment = dec_report.get("okr_alignment", {})
        correct_keys = [k for k in alignment.keys() if k.startswith("q_2025-Q4_")]
        if len(correct_keys) >= 2:
            total_score += 5
            checks.append({"name": check_name, "passed": True, "detail": f"OKR alignment has correct IDs: {correct_keys}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"OKR alignment keys don't use correct format: {list(alignment.keys())}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 8: Q4 quarterly report exists with correct filename ─────────────
    max_score += 10
    check_name = "Q4 quarterly report: quarterly/2025-Q4-report.json exists"
    try:
        q4_report_path = okr_dir / "quarterly" / "2025-Q4-report.json"
        if q4_report_path.exists():
            q4_report = load_json(q4_report_path)
            if q4_report.get("period") == "2025-Q4":
                total_score += 10
                checks.append({"name": check_name, "passed": True, "detail": f"Found with correct period=2025-Q4"})
            else:
                total_score += 5
                checks.append({"name": check_name, "passed": False, "detail": f"File exists but period field wrong: {q4_report.get('period')}"})
        else:
            # Check for alternative wrong names
            alt_files = list((okr_dir / "quarterly").glob("*.json"))
            checks.append({"name": check_name, "passed": False, "detail": f"2025-Q4-report.json not found. Files in quarterly/: {[f.name for f in alt_files]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 9: Q4 quarterly report has okr_completion with KR-level progress ─
    max_score += 10
    check_name = "Q4 quarterly report has okr_completion with kr_progress entries"
    try:
        q4_report_path = okr_dir / "quarterly" / "2025-Q4-report.json"
        q4_report = load_json(q4_report_path)
        okr_completion = q4_report.get("okr_completion", {})
        
        # Check OKR IDs are correct format
        correct_okr_keys = [k for k in okr_completion.keys() if k.startswith("q_2025-Q4_")]
        
        # Check KR progress exists within at least one OKR
        has_kr_progress = any(
            isinstance(v, dict) and len(v.get("kr_progress", {})) > 0
            for v in okr_completion.values()
        )
        
        if len(correct_okr_keys) >= 2 and has_kr_progress:
            total_score += 10
            checks.append({"name": check_name, "passed": True, "detail": f"okr_completion has {len(correct_okr_keys)} OKRs with KR progress: {correct_okr_keys}"})
        elif len(correct_okr_keys) >= 1 and has_kr_progress:
            total_score += 6
            checks.append({"name": check_name, "passed": False, "detail": f"Only {len(correct_okr_keys)} correct OKR IDs with KR progress (need >=2)"})
        elif len(correct_okr_keys) >= 1:
            total_score += 3
            checks.append({"name": check_name, "passed": False, "detail": f"Has correct OKR IDs but no kr_progress entries found"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"okr_completion keys not in correct format: {list(okr_completion.keys())}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── CHECK 10: Q4 quarterly report has next_quarter_okr_suggestions ────────
    max_score += 10
    check_name = "Q4 quarterly report has next_quarter_okr_suggestions (non-empty list)"
    try:
        q4_report_path = okr_dir / "quarterly" / "2025-Q4-report.json"
        q4_report = load_json(q4_report_path)
        suggestions = q4_report.get("next_quarter_okr_suggestions", [])
        has_monthly_breakdown = bool(q4_report.get("monthly_breakdown", {}))
        
        if isinstance(suggestions, list) and len(suggestions) >= 1:
            # Each suggestion should have title and rationale
            valid_suggestions = [
                s for s in suggestions 
                if isinstance(s, dict) and s.get("title") and s.get("rationale")
            ]
            if len(valid_suggestions) >= 1 and has_monthly_breakdown:
                total_score += 10
                checks.append({"name": check_name, "passed": True, "detail": f"{len(valid_suggestions)} valid suggestions with title+rationale, monthly_breakdown present"})
            elif len(valid_suggestions) >= 1:
                total_score += 7
                checks.append({"name": check_name, "passed": False, "detail": f"{len(valid_suggestions)} valid suggestions but monthly_breakdown missing"})
            else:
                total_score += 4
                checks.append({"name": check_name, "passed": False, "detail": f"Suggestions exist but lack required fields (title/rationale): {suggestions}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"next_quarter_okr_suggestions missing or empty: {suggestions}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ── FINAL SCORE ───────────────────────────────────────────────────────────
    score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    passed = score >= 0.75 and all(
        c["passed"] for c in checks if c["name"] in [
            "okr_config: correct OKR ID format (q_2025-Q4_N)",
            "Q4 quarterly report: quarterly/2025-Q4-report.json exists",
            "Q4 quarterly report has okr_completion with kr_progress entries",
            "Q4 quarterly report has next_quarter_okr_suggestions (non-empty list)",
        ]
    )

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))