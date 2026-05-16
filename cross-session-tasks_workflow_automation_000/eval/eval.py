import sys
import json
import re
from pathlib import Path

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_root: str):
    ws = Path(workspace_root)
    openclaw_ws = ws / ".openclaw" / "workspace"
    projects_dir = openclaw_ws / "projects"
    archive_dir = projects_dir / "_archive"

    checks = []

    # ══════════════════════════════════════════════════
    # PART A: NEW TASK — data-pipeline-migration/progress.md
    # ══════════════════════════════════════════════════

    # A1: progress.md exists for data-pipeline-migration
    new_progress_candidates = list(projects_dir.rglob("progress.md"))
    dpm_progress_path = None
    for p in new_progress_candidates:
        if "data-pipeline-migration" in str(p) and "_archive" not in str(p):
            dpm_progress_path = p
            break

    if dpm_progress_path is None:
        checks.append(check("A1_dpm_progress_exists", False,
            "No progress.md found under projects/data-pipeline-migration/"))
    else:
        checks.append(check("A1_dpm_progress_exists", True,
            f"Found at {dpm_progress_path}"))

    dpm_content = ""
    if dpm_progress_path and dpm_progress_path.exists():
        try:
            dpm_content = dpm_progress_path.read_text(encoding="utf-8")
        except Exception as e:
            checks.append(check("A1_dpm_progress_readable", False, str(e)))

    # A2: Section 1 — 基本信息 present
    has_basic_info = bool(re.search(r'基本信息', dpm_content))
    checks.append(check("A2_section_basic_info", has_basic_info,
        "Missing '基本信息' section in progress.md" if not has_basic_info else "Present"))

    # A3: Section 2 — 进度检查清单 with checkboxes
    has_checklist = bool(re.search(r'进度检查清单', dpm_content))
    has_checkboxes = bool(re.search(r'- \[[ xX]\]', dpm_content))
    checks.append(check("A3_section_checklist", has_checklist and has_checkboxes,
        "Missing '进度检查清单' section or no checkboxes" if not (has_checklist and has_checkboxes) else "Present"))

    # A4: Section 3 — 关键决策与规则 present
    has_decisions = bool(re.search(r'关键决策', dpm_content))
    checks.append(check("A4_section_decisions", has_decisions,
        "Missing '关键决策' section" if not has_decisions else "Present"))

    # A5: Section 4 — 文件位置 present
    has_file_locations = bool(re.search(r'文件位置', dpm_content))
    checks.append(check("A5_section_file_locations", has_file_locations,
        "Missing '文件位置' section" if not has_file_locations else "Present"))

    # A6: Section 5 — 下次开始时需要知道的 with 3-5 bullet points
    has_next_memo = bool(re.search(r'下次开始时需要知道的', dpm_content))
    # Count bullet points in that section
    memo_section_match = re.search(
        r'下次开始时需要知道的.*?(?=##|\Z)', dpm_content, re.DOTALL)
    bullet_count = 0
    if memo_section_match:
        section_text = memo_section_match.group(0)
        bullets = re.findall(r'^\s*[-*]\s+.+', section_text, re.MULTILINE)
        bullet_count = len(bullets)
    has_3_to_5_bullets = 3 <= bullet_count <= 5
    checks.append(check("A6_section_memo_3_to_5_bullets",
        has_next_memo and has_3_to_5_bullets,
        f"'下次开始时需要知道的' present={has_next_memo}, bullet_count={bullet_count} (need 3-5)"
        if not (has_next_memo and has_3_to_5_bullets) else f"Present with {bullet_count} bullets"))

    # A7: progress.md contains project-specific content (PROJ-045 or bob or pipeline or Airflow)
    has_relevant_content = bool(re.search(
        r'(PROJ-045|data.pipeline|Airflow|airflow|DAG|dag|migration|Migration)', dpm_content, re.IGNORECASE))
    checks.append(check("A7_dpm_progress_relevant_content", has_relevant_content,
        "progress.md appears generic — lacks project-specific details (PROJ-045, Airflow, DAGs, etc.)"
        if not has_relevant_content else "Contains project-relevant content"))

    # A8: data-pipeline-migration row added to ACTIVE-TASKS.md
    active_tasks_path = openclaw_ws / "ACTIVE-TASKS.md"
    active_content = ""
    try:
        active_content = active_tasks_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("A8_active_tasks_readable", False, str(e)))

    dpm_in_active = bool(re.search(r'data-pipeline-migration', active_content))
    checks.append(check("A8_dpm_in_active_tasks", dpm_in_active,
        "data-pipeline-migration not found in ACTIVE-TASKS.md" if not dpm_in_active
        else "Found in ACTIVE-TASKS.md"))

    # ══════════════════════════════════════════════════
    # PART B: ARCHIVAL — api-redesign task
    # ══════════════════════════════════════════════════

    # B1: api-redesign folder moved to _archive
    archived_path = archive_dir / "api-redesign"
    b1_archived = archived_path.exists() and archived_path.is_dir()
    checks.append(check("B1_api_redesign_archived", b1_archived,
        f"Expected {archived_path} to exist as directory" if not b1_archived else "Correctly archived"))

    # B2: archived progress.md still present inside _archive/api-redesign
    archived_progress = archived_path / "progress.md"
    b2_progress_in_archive = archived_progress.exists()
    checks.append(check("B2_archived_progress_preserved", b2_progress_in_archive,
        f"progress.md missing from archive: {archived_progress}" if not b2_progress_in_archive
        else "progress.md preserved in archive"))

    # B3: api-redesign REMOVED from ACTIVE-TASKS.md
    api_still_in_active = bool(re.search(r'api-redesign', active_content))
    checks.append(check("B3_api_removed_from_active", not api_still_in_active,
        "api-redesign still present in ACTIVE-TASKS.md — should be removed after archival"
        if api_still_in_active else "Correctly removed from ACTIVE-TASKS.md"))

    # B4: api-redesign added to CLOSED-TASKS.md
    closed_tasks_path = openclaw_ws / "CLOSED-TASKS.md"
    closed_content = ""
    try:
        closed_content = closed_tasks_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("B4_closed_tasks_readable", False, str(e)))

    api_in_closed = bool(re.search(r'api-redesign', closed_content))
    checks.append(check("B4_api_in_closed_tasks", api_in_closed,
        "api-redesign not found in CLOSED-TASKS.md" if not api_in_closed
        else "Correctly added to CLOSED-TASKS.md"))

    # B5: Original api-redesign folder no longer exists at projects/ (non-archive)
    original_api_path = projects_dir / "api-redesign"
    original_still_exists = original_api_path.exists()
    checks.append(check("B5_original_api_folder_removed", not original_still_exists,
        f"{original_api_path} still exists — should have been moved, not copied"
        if original_still_exists else "Original folder correctly removed"))

    # ══════════════════════════════════════════════════
    # PART C: INTEGRITY — infra-monitoring-setup untouched
    # ══════════════════════════════════════════════════

    infra_progress = projects_dir / "infra-monitoring-setup" / "progress.md"
    c1_infra_intact = infra_progress.exists()
    checks.append(check("C1_infra_monitoring_untouched", c1_infra_intact,
        "infra-monitoring-setup/progress.md was deleted or moved — should remain unchanged"
        if not c1_infra_intact else "infra-monitoring-setup correctly untouched"))

    infra_still_in_active = bool(re.search(r'infra-monitoring-setup', active_content))
    checks.append(check("C2_infra_still_in_active_tasks", infra_still_in_active,
        "infra-monitoring-setup removed from ACTIVE-TASKS.md — it should remain active"
        if not infra_still_in_active else "infra-monitoring-setup still in ACTIVE-TASKS.md"))

    # ══════════════════════════════════════════════════
    # Scoring
    # ══════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.85

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))