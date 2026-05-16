import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        return bool(condition)

    # -----------------------------------------------------------------------
    # CHECK 1: Correct knowledge base root directory exists
    # -----------------------------------------------------------------------
    kb_root = workspace / "Obsidian" / "Docs" / "OpenClaw"
    c1 = check(
        "KB root directory exists",
        kb_root.is_dir(),
        f"Expected directory: {kb_root}"
    )

    # -----------------------------------------------------------------------
    # CHECK 2: docs/ and tips/ subdirectories exist under KB root
    # -----------------------------------------------------------------------
    docs_dir = kb_root / "docs"
    tips_dir = kb_root / "tips"
    c2a = check(
        "KB docs/ subdirectory exists",
        docs_dir.is_dir(),
        f"Expected: {docs_dir}"
    )
    c2b = check(
        "KB tips/ subdirectory exists",
        tips_dir.is_dir(),
        f"Expected: {tips_dir}"
    )

    # -----------------------------------------------------------------------
    # CHECK 3: At least 2 tip articles under tips/ with correct template structure
    # Required sections (in Chinese): 简介, 使用场景, 详细步骤, 示例, 注意事项
    # -----------------------------------------------------------------------
    required_sections = ["简介", "使用场景", "详细步骤", "示例", "注意事项"]
    tip_files = list(tips_dir.glob("*.md")) if tips_dir.is_dir() else []
    
    valid_tips = []
    tip_detail_parts = []
    for tf in tip_files:
        try:
            content = tf.read_text(encoding="utf-8")
            # Each section must appear as a ## heading
            missing = [s for s in required_sections if f"## {s}" not in content]
            if not missing:
                valid_tips.append(tf.name)
                tip_detail_parts.append(f"{tf.name}: OK")
            else:
                tip_detail_parts.append(f"{tf.name}: missing sections {missing}")
        except Exception as e:
            tip_detail_parts.append(f"{tf.name}: read error {e}")

    c3 = check(
        "At least 2 valid tip articles with all 5 required sections",
        len(valid_tips) >= 2,
        f"Valid tips: {valid_tips}. Details: {'; '.join(tip_detail_parts)}"
    )

    # Also check tip articles have a code block (示例 section should have ```)
    tip_with_code = []
    for tf in tip_files:
        try:
            content = tf.read_text(encoding="utf-8")
            if "```" in content and "## 示例" in content:
                tip_with_code.append(tf.name)
        except:
            pass
    c3b = check(
        "At least 1 tip article has a code example block",
        len(tip_with_code) >= 1,
        f"Tips with code blocks: {tip_with_code}"
    )

    # -----------------------------------------------------------------------
    # CHECK 4: daily-tips.json at the correct location (kb_root, NOT Obsidian root)
    # -----------------------------------------------------------------------
    dtj_path = kb_root / "daily-tips.json"
    dtj_wrong_path = workspace / "Obsidian" / "daily-tips.json"
    
    dtj_exists = dtj_path.exists()
    c4a = check(
        "daily-tips.json exists at correct KB root location",
        dtj_exists,
        f"Expected at: {dtj_path}, wrong location would be: {dtj_wrong_path}"
    )

    # Validate daily-tips.json structure: must be valid JSON and not be the wrong placeholder
    dtj_valid = False
    dtj_detail = "file missing"
    if dtj_exists:
        try:
            dtj_content = json.loads(dtj_path.read_text(encoding="utf-8"))
            # Must be a dict (not the wrong_key placeholder) and have meaningful content
            if isinstance(dtj_content, dict) and "wrong_key" not in dtj_content:
                dtj_valid = True
                dtj_detail = f"Valid JSON dict with keys: {list(dtj_content.keys())}"
            else:
                dtj_detail = f"JSON content appears to be placeholder or wrong format: {dtj_content}"
        except Exception as e:
            dtj_detail = f"JSON parse error: {e}"
    c4b = check(
        "daily-tips.json has valid non-placeholder JSON structure",
        dtj_valid,
        dtj_detail
    )

    # -----------------------------------------------------------------------
    # CHECK 5: Cron schedule with EXACT times: 03:21, 07:21, 21:05
    # Agent must create a crontab or cron config file somewhere in workspace
    # -----------------------------------------------------------------------
    # Search for any file that looks like a crontab (crontab.txt, .crontab, cron.txt, etc.)
    cron_candidates = list(workspace.rglob("crontab*")) + \
                      list(workspace.rglob("*.crontab")) + \
                      list(workspace.rglob("cron*.txt")) + \
                      list(workspace.rglob("cron.txt")) + \
                      list(workspace.rglob("schedule*.txt")) + \
                      list(workspace.rglob("schedule*.conf"))
    
    # Filter out old distractor
    cron_candidates = [f for f in cron_candidates 
                       if "legacy" not in str(f) and "deprecated" not in str(f)]

    EXACT_TIMES = {
        "sync": ("21", "3", "scripts/sync-docs.sh"),      # 03:21 → minute=21, hour=3
        "pick": ("5", "21", "scripts/pick-daily-tip.sh"),  # 21:05 → minute=5, hour=21
        "send": ("21", "7", "scripts/send-daily-tip.sh"),  # 07:21 → minute=21, hour=7
    }

    found_cron_file = None
    cron_content = ""
    for cf in cron_candidates:
        try:
            content = cf.read_text(encoding="utf-8")
            # Quick check: must have at least 2 of 3 script names
            hits = sum(1 for _, _, script in EXACT_TIMES.values() if script in content)
            if hits >= 2:
                found_cron_file = cf
                cron_content = content
                break
        except:
            pass

    c5a = check(
        "Cron/schedule file found with script references",
        found_cron_file is not None,
        f"Searched {len(cron_candidates)} candidate files. Found: {found_cron_file}"
    )

    # Check exact cron times
    time_checks = {}
    if cron_content:
        lines = cron_content.strip().splitlines()
        for line in lines:
            parts = line.split()
            if len(parts) < 5:
                continue
            minute, hour = parts[0], parts[1]
            line_str = line
            # sync-docs at 03:21
            if "sync-docs.sh" in line_str:
                time_checks["sync"] = (minute == "21" and hour == "3", f"minute={minute} hour={hour}")
            # pick-daily-tip at 21:05
            if "pick-daily-tip.sh" in line_str:
                time_checks["pick"] = (minute == "5" and hour == "21", f"minute={minute} hour={hour}")
            # send-daily-tip at 07:21
            if "send-daily-tip.sh" in line_str:
                time_checks["send"] = (minute == "21" and hour == "7", f"minute={minute} hour={hour}")

    c5b = check(
        "sync-docs.sh scheduled at exactly 03:21",
        time_checks.get("sync", (False, "not found"))[0],
        f"sync-docs.sh time: {time_checks.get('sync', (False, 'not found in cron file'))[1]}"
    )
    c5c = check(
        "pick-daily-tip.sh scheduled at exactly 21:05",
        time_checks.get("pick", (False, "not found"))[0],
        f"pick-daily-tip.sh time: {time_checks.get('pick', (False, 'not found in cron file'))[1]}"
    )
    c5d = check(
        "send-daily-tip.sh scheduled at exactly 07:21",
        time_checks.get("send", (False, "not found"))[0],
        f"send-daily-tip.sh time: {time_checks.get('send', (False, 'not found in cron file'))[1]}"
    )

    # -----------------------------------------------------------------------
    # CHECK 6: tips-log.md exists at correct KB root location
    # -----------------------------------------------------------------------
    log_path = kb_root / "tips-log.md"
    log_exists = log_path.exists()
    c6a = check(
        "tips-log.md exists at KB root",
        log_exists,
        f"Expected: {log_path}"
    )
    log_has_content = False
    if log_exists:
        try:
            log_content = log_path.read_text(encoding="utf-8").strip()
            log_has_content = len(log_content) > 20
        except:
            pass
    c6b = check(
        "tips-log.md has meaningful log content",
        log_has_content,
        f"Log file length > 20 chars: {log_has_content}"
    )

    # -----------------------------------------------------------------------
    # CHECK 7: latest-version.txt exists at KB root
    # -----------------------------------------------------------------------
    ver_path = kb_root / "latest-version.txt"
    ver_exists = ver_path.exists()
    c7 = check(
        "latest-version.txt exists at KB root",
        ver_exists,
        f"Expected: {ver_path}"
    )
    ver_has_version = False
    if ver_exists:
        try:
            ver_content = ver_path.read_text(encoding="utf-8").strip()
            # Must look like a version (e.g., v1.0.0, 1.2.3, etc.)
            ver_has_version = bool(re.search(r'\d+\.\d+', ver_content))
        except:
            pass
    c7b = check(
        "latest-version.txt contains a version string",
        ver_has_version,
        f"Content: {ver_path.read_text().strip() if ver_exists else 'FILE MISSING'}"
    )

    # -----------------------------------------------------------------------
    # CHECK 8: docs/ directory has at least one markdown file
    # -----------------------------------------------------------------------
    doc_files = list(docs_dir.glob("*.md")) if docs_dir.is_dir() else []
    c8 = check(
        "docs/ directory contains at least one markdown doc file",
        len(doc_files) >= 1,
        f"Found doc files: {[f.name for f in doc_files]}"
    )

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    all_checks = checks
    passed_count = sum(1 for c in all_checks if c["passed"])
    total = len(all_checks)
    score = round(passed_count / total, 4)

    # Must pass critical checks to be considered passing overall
    critical = [c1, c2a, c2b, c3, c4a, c5b, c5c, c5d]
    overall_passed = all(critical) and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)