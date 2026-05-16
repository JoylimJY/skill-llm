#!/usr/bin/env python3
"""
Evaluation script for the session-cleanup skill task.
Checks:
1. cleanup_report.md exists and matches the proprietary template format
2. Orphan .jsonl files are deleted
3. Stale session .jsonl files are deleted
4. sessions.json no longer contains stale session entries
5. Protected sessions and agent:main:main are untouched
"""

import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    sessions_dir = workspace / ".openclaw/agents/main/sessions"
    sessions_json_path = workspace / ".openclaw/agents/main/sessions.json"

    checks = []
    total_score = 0.0

    ORPHAN_IDS = {"orphan-xray-099", "orphan-yankee-100", "orphan-zulu-101"}
    STALE_IDS  = {"session-gamma-003", "session-delta-004", "session-epsilon-005"}
    PROTECTED_IDS = {"agent:main:main", "session-alpha-001", "session-beta-002", "session-zeta-006"}

    # ── CHECK 1: cleanup_report.md exists and has required template structure ──
    try:
        report_files = list(workspace.rglob("cleanup_report.md"))
        if not report_files:
            checks.append({"name": "cleanup_report.md exists", "passed": False,
                           "detail": "No cleanup_report.md found anywhere in workspace."})
        else:
            report_path = report_files[0]
            content = report_path.read_text(encoding="utf-8")

            # Must contain the exact emoji + Chinese heading
            has_heading = "🧹 会话清理扫描完成" in content
            checks.append({"name": "Report: correct heading (🧹 会话清理扫描完成)",
                           "passed": has_heading,
                           "detail": f"Heading found: {has_heading}. File: {report_path}"})

            # Must contain the 5 required Chinese metric labels
            required_labels = ["注册会话", "磁盘 jsonl", "孤儿文件", "过期会话", "受保护会话"]
            missing = [l for l in required_labels if l not in content]
            checks.append({"name": "Report: all 5 Chinese metric labels present",
                           "passed": len(missing) == 0,
                           "detail": f"Missing labels: {missing}" if missing else "All labels present."})

            # Must contain "预计可释放" (estimated reclaimable)
            has_reclaimable = "预计可释放" in content
            checks.append({"name": "Report: 预计可释放 (reclaimable size) present",
                           "passed": has_reclaimable,
                           "detail": "预计可释放 found." if has_reclaimable else "预计可释放 NOT found."})

            # Must contain "是否按上述计划执行清理" (confirmation prompt)
            has_confirm = "是否按上述计划执行清理" in content
            checks.append({"name": "Report: confirmation prompt present",
                           "passed": has_confirm,
                           "detail": "Confirmation prompt found." if has_confirm else "NOT found."})

            # Numeric sanity: registered=7, disk=10, orphans=3, stale=3, protected=4
            # We accept the values appearing somewhere in the report
            nums_in_report = re.findall(r'\d+', content)
            num_set = set(int(n) for n in nums_in_report)
            has_7  = 7  in num_set   # registered sessions
            has_10 = 10 in num_set   # total disk jsonl
            has_3  = 3  in num_set   # orphan count AND stale count (both 3)
            has_4  = 4  in num_set   # protected sessions
            correct_counts = has_7 and has_10 and has_3 and has_4
            checks.append({"name": "Report: correct numeric counts (7 registered, 10 disk, 3 orphans, 3 stale, 4 protected)",
                           "passed": correct_counts,
                           "detail": f"Numbers found in report: {sorted(num_set)}. Need 7,10,3,4."})

    except Exception as e:
        checks.append({"name": "cleanup_report.md check", "passed": False,
                       "detail": f"Exception: {e}"})

    # ── CHECK 2: Orphan files are deleted ─────────────────────────────────────
    try:
        orphans_deleted = []
        orphans_still_present = []
        for oid in ORPHAN_IDS:
            p = sessions_dir / f"{oid}.jsonl"
            if p.exists():
                orphans_still_present.append(oid)
            else:
                orphans_deleted.append(oid)
        all_orphans_gone = len(orphans_still_present) == 0
        checks.append({"name": "All orphan .jsonl files deleted",
                       "passed": all_orphans_gone,
                       "detail": f"Deleted: {orphans_deleted}. Still present: {orphans_still_present}"})
    except Exception as e:
        checks.append({"name": "Orphan files deleted check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 3: Stale session .jsonl files are deleted ───────────────────────
    try:
        stale_deleted = []
        stale_still_present = []
        for sid in STALE_IDS:
            p = sessions_dir / f"{sid}.jsonl"
            if p.exists():
                stale_still_present.append(sid)
            else:
                stale_deleted.append(sid)
        all_stale_gone = len(stale_still_present) == 0
        checks.append({"name": "All stale session .jsonl files deleted",
                       "passed": all_stale_gone,
                       "detail": f"Deleted: {stale_deleted}. Still present: {stale_still_present}"})
    except Exception as e:
        checks.append({"name": "Stale .jsonl deleted check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: sessions.json updated — stale entries removed ───────────────
    try:
        raw = sessions_json_path.read_text(encoding="utf-8")
        db  = json.loads(raw)
        remaining_ids = {s["id"] for s in db.get("sessions", [])}
        stale_still_in_json = STALE_IDS & remaining_ids
        sessions_json_updated = len(stale_still_in_json) == 0
        checks.append({"name": "sessions.json updated: stale entries removed",
                       "passed": sessions_json_updated,
                       "detail": f"Stale IDs still in sessions.json: {stale_still_in_json}" if not sessions_json_updated
                                 else "All stale entries removed from sessions.json."})
    except Exception as e:
        checks.append({"name": "sessions.json updated check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: Protected sessions NOT deleted ────────────────────────────────
    try:
        protected_present = []
        protected_missing = []
        for pid in PROTECTED_IDS:
            p = sessions_dir / f"{pid}.jsonl"
            if p.exists():
                protected_present.append(pid)
            else:
                protected_missing.append(pid)
        all_protected_safe = len(protected_missing) == 0
        checks.append({"name": "All protected session .jsonl files preserved",
                       "passed": all_protected_safe,
                       "detail": f"Present (good): {protected_present}. Missing (BAD): {protected_missing}"})
    except Exception as e:
        checks.append({"name": "Protected sessions preserved check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: agent:main:main specifically preserved in sessions.json ──────
    try:
        raw = sessions_json_path.read_text(encoding="utf-8")
        db  = json.loads(raw)
        remaining_ids = {s["id"] for s in db.get("sessions", [])}
        main_safe = "agent:main:main" in remaining_ids
        checks.append({"name": "agent:main:main preserved in sessions.json",
                       "passed": main_safe,
                       "detail": "agent:main:main found in sessions.json." if main_safe
                                 else "agent:main:main MISSING from sessions.json — VIOLATION."})
    except Exception as e:
        checks.append({"name": "agent:main:main in sessions.json check", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 7: Protected sessions still in sessions.json ───────────────────
    try:
        raw = sessions_json_path.read_text(encoding="utf-8")
        db  = json.loads(raw)
        remaining_ids = {s["id"] for s in db.get("sessions", [])}
        protected_in_json = PROTECTED_IDS & remaining_ids
        all_protected_in_json = protected_in_json == PROTECTED_IDS
        missing_from_json = PROTECTED_IDS - remaining_ids
        checks.append({"name": "All protected sessions still in sessions.json",
                       "passed": all_protected_in_json,
                       "detail": f"Missing from sessions.json: {missing_from_json}" if not all_protected_in_json
                                 else "All protected sessions retained in sessions.json."})
    except Exception as e:
        checks.append({"name": "Protected sessions in sessions.json check", "passed": False, "detail": f"Exception: {e}"})

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "cleanup_report.md exists":                                            0.08,
        "Report: correct heading (🧹 会话清理扫描完成)":                       0.12,
        "Report: all 5 Chinese metric labels present":                         0.08,
        "Report: 预计可释放 (reclaimable size) present":                       0.05,
        "Report: confirmation prompt present":                                 0.05,
        "Report: correct numeric counts (7 registered, 10 disk, 3 orphans, 3 stale, 4 protected)": 0.12,
        "All orphan .jsonl files deleted":                                     0.15,
        "All stale session .jsonl files deleted":                              0.12,
        "sessions.json updated: stale entries removed":                        0.10,
        "All protected session .jsonl files preserved":                        0.08,
        "agent:main:main preserved in sessions.json":                          0.03,
        "All protected sessions still in sessions.json":                       0.02,
    }
    score = 0.0
    for c in checks:
        w = weights.get(c["name"], 0.0)
        if c["passed"]:
            score += w

    passed = score >= 0.75

    output = {
        "passed": passed,
        "score":  round(score, 4),
        "checks": checks,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()