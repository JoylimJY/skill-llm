import sys
import os
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─── CHECK 1: Directory structure follows SKILL.md spec ───────────────────────
try:
    cc_dir = Path(workspace) / "conflict-coordination"
    scripts_dir = cc_dir / "scripts"
    docs_dir = cc_dir / "docs"

    has_root = cc_dir.exists() and cc_dir.is_dir()
    has_scripts = scripts_dir.exists() and scripts_dir.is_dir()
    has_docs = docs_dir.exists() and docs_dir.is_dir()

    # Check for detect-conflicts.sh in scripts/
    detect_script = scripts_dir / "detect-conflicts.sh"
    has_detect = detect_script.exists()

    # Check docs subdirectory has at least some files
    docs_files = list(docs_dir.glob("*")) if has_docs else []
    has_doc_files = len(docs_files) >= 1

    structure_ok = has_root and has_scripts and has_docs
    total_score += check(
        "conflict-coordination directory structure",
        structure_ok,
        f"Root: {has_root}, scripts/: {has_scripts}, docs/: {has_docs}",
        weight=1.0
    )
    total_score += check(
        "detect-conflicts.sh present in scripts/",
        has_detect,
        f"scripts/detect-conflicts.sh exists: {has_detect}",
        weight=1.0
    )
    total_score += check(
        "docs/ directory has files",
        has_doc_files,
        f"docs/ files: {[f.name for f in docs_files]}",
        weight=0.5
    )
except Exception as e:
    total_score += check("conflict-coordination directory structure", False, f"Exception: {e}", weight=1.0)
    total_score += check("detect-conflicts.sh present in scripts/", False, f"Exception: {e}", weight=1.0)
    total_score += check("docs/ directory has files", False, f"Exception: {e}", weight=0.5)

# ─── CHECK 2: conflict-detection.cron - existence and correct schedule ────────
try:
    cron_files = list(Path(workspace).rglob("conflict-detection.cron"))
    if not cron_files:
        total_score += check("conflict-detection.cron exists", False, "File not found anywhere in workspace", weight=1.5)
        total_score += check("crontab schedule is exactly '0 22 * * 6'", False, "File not found", weight=2.0)
        total_score += check("crontab references detect-conflicts.sh", False, "File not found", weight=1.0)
    else:
        cron_path = cron_files[0]
        cron_content = cron_path.read_text()
        total_score += check("conflict-detection.cron exists", True, f"Found at: {cron_path}", weight=1.5)

        # Check EXACT schedule: must be "0 22 * * 6" - Saturday 22:00
        # Trap: Wrong answers include "0 22 * * 0" (Sunday), "@weekly", "0 22 * * 7", "30 22 * * 6"
        schedule_pattern = re.compile(r'\b0\s+22\s+\*\s+\*\s+6\b')
        has_correct_schedule = bool(schedule_pattern.search(cron_content))

        # Anti-trap: make sure wrong schedules are NOT present instead
        wrong_sunday = re.compile(r'\b0\s+22\s+\*\s+\*\s+0\b')
        wrong_7 = re.compile(r'\b0\s+22\s+\*\s+\*\s+7\b')
        has_wrong_schedule = bool(wrong_sunday.search(cron_content)) or bool(wrong_7.search(cron_content))

        schedule_ok = has_correct_schedule and not has_wrong_schedule
        total_score += check(
            "crontab schedule is exactly '0 22 * * 6'",
            schedule_ok,
            f"Correct schedule found: {has_correct_schedule}, Wrong schedule (Sunday/7) found: {has_wrong_schedule}. Content: {cron_content[:300]}",
            weight=2.0
        )

        # Check it references detect-conflicts.sh
        refs_script = "detect-conflicts.sh" in cron_content
        total_score += check(
            "crontab references detect-conflicts.sh",
            refs_script,
            f"detect-conflicts.sh in cron content: {refs_script}",
            weight=1.0
        )
except Exception as e:
    total_score += check("conflict-detection.cron exists", False, f"Exception: {e}", weight=1.5)
    total_score += check("crontab schedule is exactly '0 22 * * 6'", False, f"Exception: {e}", weight=2.0)
    total_score += check("crontab references detect-conflicts.sh", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 3: coordination-report.md - existence and conflict categories ──────
try:
    report_files = list(Path(workspace).rglob("coordination-report.md"))
    if not report_files:
        total_score += check("coordination-report.md exists", False, "File not found anywhere in workspace", weight=1.0)
        total_score += check("Report covers all 5 detection categories", False, "File not found", weight=2.0)
        total_score += check("Report includes correct priority/coordination principles", False, "File not found", weight=2.0)
        total_score += check("Systemd > cron coordination principle present", False, "File not found", weight=1.0)
        total_score += check("trash > rm coordination principle present", False, "File not found", weight=1.0)
    else:
        report_path = report_files[0]
        report_content = report_files[0].read_text().lower()
        total_score += check("coordination-report.md exists", True, f"Found at: {report_path}", weight=1.0)

        # Check all 5 detection categories from SKILL.md table are addressed
        # crontab/cron conflict, systemd service conflict, script overlap, log path, doc consistency
        categories = {
            "crontab/cron conflicts": bool(re.search(r'crontab|cron\s+config', report_content)),
            "systemd service conflicts": bool(re.search(r'systemd', report_content)),
            "script functional overlap": bool(re.search(r'script.{0,30}(overlap|重叠|功能)|功能.{0,30}重叠|(overlap|redundan).{0,30}script', report_content)),
            "log path inconsistency": bool(re.search(r'log.{0,30}path|log.{0,30}(散|inconsist|分散)|路径', report_content)),
            "doc consistency": bool(re.search(r'doc.{0,30}(consist|miss|缺|一致)|文档', report_content)),
        }
        all_5_present = all(categories.values())
        missing = [k for k, v in categories.items() if not v]
        total_score += check(
            "Report covers all 5 detection categories",
            all_5_present,
            f"Categories found: {categories}. Missing: {missing}",
            weight=2.0
        )

        # Check coordination principles - inotifywait > cron (realtime priority)
        has_realtime = bool(re.search(r'inotifywait|实时.{0,20}(优先|cron)|realtime.{0,20}prior', report_content))
        # systemd > nohup
        has_systemd_priority = bool(re.search(r'systemd.{0,40}(nohup|优先|prior|>)|nohup.{0,40}systemd', report_content))
        # trash > rm
        has_trash = bool(re.search(r'trash.{0,20}(rm|>)|rm.{0,20}trash|trash\s*>\s*rm|可恢复', report_content))

        principles_count = sum([has_realtime, has_systemd_priority, has_trash])
        principles_ok = principles_count >= 2  # At least 2 of 3 proprietary principles
        total_score += check(
            "Report includes correct priority/coordination principles",
            principles_ok,
            f"inotifywait>cron: {has_realtime}, systemd>nohup: {has_systemd_priority}, trash>rm: {has_trash} (need >=2)",
            weight=2.0
        )

        # Cron vs Systemd → Systemd 优先 is the most important resolution principle
        total_score += check(
            "Systemd > cron coordination principle present",
            has_systemd_priority,
            f"systemd priority principle found: {has_systemd_priority}",
            weight=1.0
        )

        # trash > rm is the proprietary trap (recoverable operations)
        total_score += check(
            "trash > rm coordination principle present",
            has_trash,
            f"trash > rm principle found: {has_trash}",
            weight=1.0
        )

except Exception as e:
    total_score += check("coordination-report.md exists", False, f"Exception: {e}", weight=1.0)
    total_score += check("Report covers all 5 detection categories", False, f"Exception: {e}", weight=2.0)
    total_score += check("Report includes correct priority/coordination principles", False, f"Exception: {e}", weight=2.0)
    total_score += check("Systemd > cron coordination principle present", False, f"Exception: {e}", weight=1.0)
    total_score += check("trash > rm coordination principle present", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 4: platform.json conflict_detection updated ────────────────────────
try:
    platform_json_path = Path(workspace) / "ai-assistant" / "config" / "platform.json"
    if platform_json_path.exists():
        data = json.loads(platform_json_path.read_text())
        cd = data.get("conflict_detection", {})
        # Check that it's no longer disabled/UNCONFIGURED
        enabled_fixed = cd.get("enabled", False) is True
        schedule_fixed = cd.get("schedule", "UNCONFIGURED") != "UNCONFIGURED"
        script_fixed = cd.get("script", "UNCONFIGURED") != "UNCONFIGURED"
        updated = enabled_fixed or (schedule_fixed and script_fixed)
        total_score += check(
            "platform.json conflict_detection updated from UNCONFIGURED",
            updated,
            f"enabled: {cd.get('enabled')}, schedule: {cd.get('schedule')}, script: {cd.get('script')}",
            weight=0.5
        )
    else:
        # Not strictly required but nice to have
        total_score += check(
            "platform.json conflict_detection updated from UNCONFIGURED",
            False,
            "platform.json not found at expected path",
            weight=0.5
        )
except Exception as e:
    total_score += check("platform.json conflict_detection updated from UNCONFIGURED", False, f"Exception: {e}", weight=0.5)

# ─── SCORE NORMALIZATION ──────────────────────────────────────────────────────
max_score = 1.0 + 1.0 + 0.5 + 1.5 + 2.0 + 1.0 + 1.0 + 2.0 + 2.0 + 1.0 + 1.0 + 0.5
normalized = round(min(total_score / max_score, 1.0), 4)

result = {
    "passed": normalized >= 0.65,
    "score": normalized,
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))