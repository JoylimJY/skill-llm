import sys
import os
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── CHECK 1: daily-log file exists at correct path ────────────────────────
    # Must be memory/2024-12-03.md (exact date from scenario)
    daily_log_path = workspace / "memory" / "2024-12-03.md"
    try:
        if daily_log_path.exists():
            content = daily_log_path.read_text()
            total_score += add_check(
                "daily-log: file exists at memory/2024-12-03.md",
                True,
                f"Found daily log at correct path. Size: {len(content)} chars."
            )
        else:
            # Check for wrong-date or wrong-path variants
            wrong_paths = list(workspace.rglob("2024-12-03.md"))
            if wrong_paths:
                total_score += add_check(
                    "daily-log: file exists at memory/2024-12-03.md",
                    False,
                    f"File found but at WRONG path: {wrong_paths[0]} (must be under memory/)"
                )
            else:
                total_score += add_check(
                    "daily-log: file exists at memory/2024-12-03.md",
                    False,
                    "No daily log file found at memory/2024-12-03.md"
                )
            content = ""
    except Exception as e:
        content = ""
        total_score += add_check("daily-log: file exists at memory/2024-12-03.md", False, f"Error: {e}")

    # ── CHECK 2: daily-log contains dated event evidence ──────────────────────
    try:
        has_backup_evidence = (
            "2024-12-03" in content or "december" in content.lower() or "dec" in content.lower()
        ) and (
            "backup" in content.lower() or "pg_dump" in content.lower() or "2.1" in content or "4m" in content.lower()
        )
        total_score += add_check(
            "daily-log: contains dated backup event evidence",
            has_backup_evidence,
            "Daily log should reference the 2024-12-03 backup run and its outcome (size, duration, etc.)"
            if not has_backup_evidence else "Contains dated evidence."
        )
    except Exception as e:
        total_score += add_check("daily-log: contains dated backup event evidence", False, f"Error: {e}")

    # ── CHECK 3: experience entry exists in correct directory ─────────────────
    exp_dir = workspace / "memory" / "experience-bank" / "entries"
    try:
        exp_files = list(exp_dir.glob("*.md"))
        has_exp = len(exp_files) > 0
        total_score += add_check(
            "experience: entry exists in memory/experience-bank/entries/",
            has_exp,
            f"Found {len(exp_files)} entry file(s): {[f.name for f in exp_files]}" if has_exp
            else "No .md files found in memory/experience-bank/entries/"
        )
        exp_content = "\n".join(f.read_text() for f in exp_files) if exp_files else ""
    except Exception as e:
        exp_content = ""
        total_score += add_check("experience: entry exists in memory/experience-bank/entries/", False, f"Error: {e}")

    # ── CHECK 4: experience entry has required structural fields ──────────────
    try:
        has_trigger = bool(re.search(r"trigger\s*:", exp_content, re.IGNORECASE))
        has_action = bool(re.search(r"action\s*:", exp_content, re.IGNORECASE))
        has_failure = bool(re.search(r"failure[_\s-]?mode\s*:", exp_content, re.IGNORECASE))
        has_tags = bool(re.search(r"tags\s*:", exp_content, re.IGNORECASE))
        all_fields = has_trigger and has_action and has_failure and has_tags
        detail = (
            f"trigger:{has_trigger} action:{has_action} failure_mode:{has_failure} tags:{has_tags}"
        )
        total_score += add_check(
            "experience: entry has trigger/action/failure_mode/tags fields",
            all_fields,
            detail
        )
    except Exception as e:
        total_score += add_check("experience: entry has trigger/action/failure_mode/tags fields", False, f"Error: {e}")

    # ── CHECK 5: experience entry captures pg_dump/pg_restore gotcha ──────────
    try:
        pg_gotcha = (
            "pg_restore" in exp_content.lower() or "-fc" in exp_content.lower() or
            "format" in exp_content.lower()
        ) and (
            "psql" in exp_content.lower() or "restore" in exp_content.lower()
        )
        total_score += add_check(
            "experience: captures pg_dump -Fc format / pg_restore lesson",
            pg_gotcha,
            "Experience entry should capture the -Fc format gotcha (pg_restore required, not psql)"
            if not pg_gotcha else "Captures the pg_dump/pg_restore lesson."
        )
    except Exception as e:
        total_score += add_check("experience: captures pg_dump -Fc format / pg_restore lesson", False, f"Error: {e}")

    # ── CHECK 6: playbook exists in playbooks/ directory ─────────────────────
    playbook_dir = workspace / "playbooks"
    try:
        # Exclude the archived distractor
        playbook_files = [
            f for f in playbook_dir.glob("*.md")
            if f.name != "old-backup-v1.md"
        ]
        has_playbook = len(playbook_files) > 0
        pb_content = "\n".join(f.read_text() for f in playbook_files) if playbook_files else ""
        total_score += add_check(
            "playbook: new file exists in playbooks/",
            has_playbook,
            f"Found playbook(s): {[f.name for f in playbook_files]}" if has_playbook
            else "No new playbook found in playbooks/ (excluding archived distractor)"
        )
    except Exception as e:
        pb_content = ""
        total_score += add_check("playbook: new file exists in playbooks/", False, f"Error: {e}")

    # ── CHECK 7: playbook has required structural sections ────────────────────
    try:
        has_prereqs = bool(re.search(r"##?\s*prerequisites", pb_content, re.IGNORECASE))
        has_steps = bool(re.search(r"##?\s*steps", pb_content, re.IGNORECASE))
        has_done = bool(re.search(r"##?\s*done.condition", pb_content, re.IGNORECASE))
        all_sections = has_prereqs and has_steps and has_done
        detail = f"prerequisites:{has_prereqs} steps:{has_steps} done-condition:{has_done}"
        total_score += add_check(
            "playbook: has Prerequisites / Steps / Done-condition sections",
            all_sections,
            detail
        )
    except Exception as e:
        total_score += add_check("playbook: has Prerequisites / Steps / Done-condition sections", False, f"Error: {e}")

    # ── CHECK 8: playbook content is about the backup workflow ────────────────
    try:
        pb_relevant = (
            "pg_dump" in pb_content.lower() or "backup" in pb_content.lower()
        ) and (
            "cron" in pb_content.lower() or "retention" in pb_content.lower() or "rotation" in pb_content.lower()
        )
        total_score += add_check(
            "playbook: contains pg_dump backup + cron/rotation workflow content",
            pb_relevant,
            "Playbook should include pg_dump command and cron/retention steps"
            if not pb_relevant else "Playbook contains relevant backup workflow content."
        )
    except Exception as e:
        total_score += add_check("playbook: contains pg_dump backup + cron/rotation workflow content", False, f"Error: {e}")

    # ── CHECK 9: NO skill created (not justified — single cross-project hint only, scenario says "next quarter") ──
    # According to decision rules: require actual cross-project reuse evidence, not just stated intent
    # The scenario says it "will be reused" but hasn't been yet — borderline case.
    # We check that if a skill was created, it doesn't simply duplicate the playbook content verbatim.
    skill_dir = workspace / "skills"
    try:
        new_skills = [
            f for f in skill_dir.rglob("*.md")
            if "postgres-tuning" not in f.name and "k8s-rolling-deploy" not in f.name
        ]
        # Skill creation is acceptable ONLY IF agent explicitly justifies cross-project reuse
        # We do NOT penalize for a skill if it exists AND is distinct from playbook
        # But we DO penalize if the agent put playbook content ONLY in skills/ and skipped playbooks/
        playbook_files_final = [
            f for f in (workspace / "playbooks").glob("*.md")
            if f.name != "old-backup-v1.md"
        ]
        playbook_skipped_for_skill = len(playbook_files_final) == 0 and len(new_skills) > 0
        total_score += add_check(
            "routing: did NOT place canonical workflow solely inside skills/ (bypassing playbooks/)",
            not playbook_skipped_for_skill,
            "Agent correctly used playbooks/ for the canonical workflow." if not playbook_skipped_for_skill
            else "Agent incorrectly routed the canonical workflow to skills/ only, skipping playbooks/."
        )
    except Exception as e:
        total_score += add_check("routing: did NOT place canonical workflow solely inside skills/", False, f"Error: {e}")

    # ── CHECK 10: no raw noise dumped as a single monolithic file ─────────────
    # Checks that the agent didn't just copy the scenario briefing verbatim into one file
    try:
        all_new_files = []
        for p in workspace.rglob("*.md"):
            if "scratch" in str(p) or "references" in str(p) or str(p).name in [
                "architecture.md", "README.md", "postgres-tuning.md",
                "k8s-rolling-deploy.md", "old-backup-v1.md", "task-briefing.md"
            ]:
                continue
            all_new_files.append(p)

        raw_dump_detected = False
        for f in all_new_files:
            try:
                c = f.read_text()
                # If any single new file contains the entire scenario verbatim (>80% overlap)
                scenario_markers = [
                    "pg_backup.sh", "backup_user", "22:00:03", "find /backups -mtime"
                ]
                hits = sum(1 for m in scenario_markers if m in c)
                if hits >= 4:
                    raw_dump_detected = True
                    break
            except Exception:
                pass

        total_score += add_check(
            "quality: no raw scenario dump stored as long-term knowledge",
            not raw_dump_detected,
            "No raw scenario copy detected in knowledge files." if not raw_dump_detected
            else "A knowledge file appears to be a verbatim copy of the scenario briefing — raw noise stored."
        )
    except Exception as e:
        total_score += add_check("quality: no raw scenario dump stored as long-term knowledge", False, f"Error: {e}")

    # ── Final score ───────────────────────────────────────────────────────────
    num_checks = len(checks)
    final_score = round(total_score / num_checks, 3) if num_checks > 0 else 0.0
    passed = final_score >= 0.75

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))