import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1])
today_str = datetime.now().strftime("%Y-%m-%d")
today = datetime.now()

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ─────────────────────────────────────────
# CHECK 1: MEMORY.md updated with decisions
# ─────────────────────────────────────────
try:
    memory_path = workspace / "MEMORY.md"
    memory_content = memory_path.read_text(encoding="utf-8")

    # Must contain: "发布日期定在下个月15号" OR "发布日期" + "15号" decision
    has_release_decision = (
        "15" in memory_content and 
        ("发布" in memory_content or "版本" in memory_content)
    )
    # Must contain: "凤凰计划" project info
    has_project_name = "凤凰计划" in memory_content
    # Must contain: "FastAPI" or "PostgreSQL" tech stack decision
    has_tech_decision = "FastAPI" in memory_content or "PostgreSQL" in memory_content
    # Must contain: JSONB knowledge point
    has_jsonb_knowledge = "JSONB" in memory_content or "jsonb" in memory_content.lower()
    # Must contain: zero knowledge proof
    has_zkp = "零知识证明" in memory_content

    decisions_ok = has_release_decision and has_project_name and has_tech_decision
    knowledge_ok = has_jsonb_knowledge and has_zkp

    add_check(
        "MEMORY.md: decisions written",
        decisions_ok,
        f"release_decision={has_release_decision}, project_name={has_project_name}, tech_decision={has_tech_decision}. Content snippet: {memory_content[:300]}",
        weight=2.0
    )
    add_check(
        "MEMORY.md: knowledge points written",
        knowledge_ok,
        f"jsonb={has_jsonb_knowledge}, zkp={has_zkp}",
        weight=1.5
    )
    # Must NOT contain personal preferences (those go to USER.md)
    # Check that Figma preference is NOT the primary content in MEMORY.md
    figma_in_memory = "Figma" in memory_content or "我喜欢" in memory_content or "我偏好" in memory_content
    # Penalize if personal prefs ended up in MEMORY.md without USER.md being populated
    add_check(
        "MEMORY.md: preserves existing content (not wiped)",
        "微服务架构" in memory_content or "Docker" in memory_content,
        f"Existing content preserved check. Has microservice: {'微服务架构' in memory_content}",
        weight=1.0
    )
except Exception as e:
    add_check("MEMORY.md: decisions written", False, f"Exception: {e}", weight=2.0)
    add_check("MEMORY.md: knowledge points written", False, f"Exception: {e}", weight=1.5)
    add_check("MEMORY.md: preserves existing content", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────
# CHECK 2: memory/YYYY-MM-DD.md (today's file)
# ─────────────────────────────────────────
try:
    daily_path = workspace / "memory" / f"{today_str}.md"
    daily_content = daily_path.read_text(encoding="utf-8")

    # Must contain tasks
    has_db_migration_task = "数据库迁移" in daily_content or "迁移脚本" in daily_content
    has_permission_task = "权限" in daily_content or "用户权限" in daily_content
    # Must contain temporary info
    has_temp_code = "TMP-8847-XKQZ" in daily_content or "8847" in daily_content
    # Must have today's date in filename (already verified by path) and ideally in content
    has_date_in_content = today_str in daily_content or today_str[:7] in daily_content

    add_check(
        "memory/TODAY.md: tasks written",
        has_db_migration_task and has_permission_task,
        f"db_migration={has_db_migration_task}, permission_task={has_permission_task}. Snippet: {daily_content[:400]}",
        weight=2.0
    )
    add_check(
        "memory/TODAY.md: temporary info written",
        has_temp_code,
        f"temp_code_present={has_temp_code}. Content has TMP code: {has_temp_code}",
        weight=1.5
    )
except FileNotFoundError:
    add_check("memory/TODAY.md: tasks written", False, f"File not found: memory/{today_str}.md", weight=2.0)
    add_check("memory/TODAY.md: temporary info written", False, f"File not found: memory/{today_str}.md", weight=1.5)
except Exception as e:
    add_check("memory/TODAY.md: tasks written", False, f"Exception: {e}", weight=2.0)
    add_check("memory/TODAY.md: temporary info written", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────
# CHECK 3: USER.md created with personal preferences
# ─────────────────────────────────────────
try:
    # Search for USER.md anywhere in workspace
    user_files = list(workspace.rglob("USER.md"))
    if not user_files:
        raise FileNotFoundError("USER.md not found anywhere in workspace")
    user_path = user_files[0]
    user_content = user_path.read_text(encoding="utf-8")

    has_figma_pref = "Figma" in user_content
    has_standup_pref = "站会" in user_content or "周一" in user_content or "15分钟" in user_content
    
    add_check(
        "USER.md: personal preferences written",
        has_figma_pref and has_standup_pref,
        f"figma={has_figma_pref}, standup={has_standup_pref}. Path={user_path}. Snippet: {user_content[:300]}",
        weight=2.0
    )
except FileNotFoundError as e:
    add_check("USER.md: personal preferences written", False, f"FileNotFoundError: {e}", weight=2.0)
except Exception as e:
    add_check("USER.md: personal preferences written", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────
# CHECK 4: distill-config.json schema correctness
# ─────────────────────────────────────────
try:
    config_files = list(workspace.rglob("distill-config.json"))
    if not config_files:
        raise FileNotFoundError("distill-config.json not found")
    
    # Prefer the one in memory/ directory per SKILL.md spec
    mem_config = workspace / "memory" / "distill-config.json"
    if mem_config.exists():
        config_path = mem_config
    else:
        config_path = config_files[0]
    
    config = json.loads(config_path.read_text(encoding="utf-8"))
    
    # Required fields per SKILL.md schema
    has_retention = "retentionDays" in config and isinstance(config["retentionDays"], int)
    has_auto_clean = "autoClean" in config
    has_auto_reset = "autoReset" in config
    has_categories = "categories" in config and isinstance(config["categories"], list)
    has_schedule = "schedule" in config
    
    # Categories must include the 4 canonical ones
    if has_categories:
        required_cats = {"decision", "task", "knowledge", "temporary"}
        actual_cats = set(config["categories"])
        cats_valid = required_cats.issubset(actual_cats)
    else:
        cats_valid = False
    
    # Schedule must be a valid cron expression (daily 22:00 = "0 22 * * *")
    schedule_valid = False
    if has_schedule:
        sched = config["schedule"]
        if isinstance(sched, str):
            # Must match daily 22:00 cron pattern
            schedule_valid = sched.strip() == "0 22 * * *"
        elif isinstance(sched, dict):
            # Some agents might use the cron job object format
            expr = sched.get("expr", "")
            schedule_valid = expr.strip() == "0 22 * * *"
    
    schema_ok = has_retention and has_auto_clean and has_categories and has_schedule
    
    add_check(
        "distill-config.json: correct schema fields",
        schema_ok,
        f"retention={has_retention}, autoClean={has_auto_clean}, categories={has_categories}, schedule={has_schedule}. Config: {config}",
        weight=1.5
    )
    add_check(
        "distill-config.json: categories include all 4 types",
        cats_valid,
        f"required={sorted(required_cats)}, actual={sorted(actual_cats) if has_categories else 'N/A'}",
        weight=1.0
    )
    add_check(
        "distill-config.json: schedule is daily 22:00 cron",
        schedule_valid,
        f"schedule value in config: {config.get('schedule', 'MISSING')}",
        weight=1.0
    )
    add_check(
        "distill-config.json: retentionDays is numeric",
        has_retention,
        f"retentionDays = {config.get('retentionDays', 'MISSING')}",
        weight=0.5
    )

except FileNotFoundError as e:
    add_check("distill-config.json: correct schema fields", False, f"FileNotFoundError: {e}", weight=1.5)
    add_check("distill-config.json: categories include all 4 types", False, f"File missing", weight=1.0)
    add_check("distill-config.json: schedule is daily 22:00 cron", False, f"File missing", weight=1.0)
    add_check("distill-config.json: retentionDays is numeric", False, f"File missing", weight=0.5)
except Exception as e:
    add_check("distill-config.json: correct schema fields", False, f"Exception: {e}", weight=1.5)
    add_check("distill-config.json: categories include all 4 types", False, f"Exception: {e}", weight=1.0)
    add_check("distill-config.json: schedule is daily 22:00 cron", False, f"Exception: {e}", weight=1.0)
    add_check("distill-config.json: retentionDays is numeric", False, f"Exception: {e}", weight=0.5)

# ─────────────────────────────────────────
# CHECK 5: Expired memory files handled
# ─────────────────────────────────────────
try:
    memory_dir = workspace / "memory"
    old_dates_expected = [
        (today - timedelta(days=45)).strftime("%Y-%m-%d"),
        (today - timedelta(days=60)).strftime("%Y-%m-%d"),
        (today - timedelta(days=35)).strftime("%Y-%m-%d"),
    ]
    recent_dates_expected = [
        (today - timedelta(days=5)).strftime("%Y-%m-%d"),
        (today - timedelta(days=10)).strftime("%Y-%m-%d"),
    ]
    
    # Default retentionDays is 30, files older than 30 days should be flagged/deleted/archived
    # We check: either the files are deleted OR a report/archive mentions them
    
    expired_handled = []
    for old_date in old_dates_expected:
        old_file = memory_dir / f"{old_date}.md"
        if not old_file.exists():
            # File was deleted - that's handling it
            expired_handled.append((old_date, "deleted"))
        else:
            # Check if any report file mentions this date as expired
            report_files = list(workspace.rglob("*.md")) + list(workspace.rglob("*.txt"))
            mentioned_as_expired = False
            for rf in report_files:
                try:
                    rc = rf.read_text(encoding="utf-8")
                    if old_date in rc and ("过期" in rc or "清理" in rc or "归档" in rc or "expired" in rc.lower() or "archive" in rc.lower()):
                        mentioned_as_expired = True
                        break
                except:
                    pass
            if mentioned_as_expired:
                expired_handled.append((old_date, "reported"))
            else:
                expired_handled.append((old_date, "unhandled"))
    
    # Recent files should NOT be deleted
    recent_files_intact = all(
        (memory_dir / f"{rd}.md").exists() for rd in recent_dates_expected
    )
    
    handled_count = sum(1 for _, status in expired_handled if status in ("deleted", "reported"))
    expiry_ok = handled_count >= 2  # At least 2 of the 3 old files handled
    
    add_check(
        "Expired files: old files (>30 days) handled",
        expiry_ok,
        f"Handled {handled_count}/3 old files. Details: {expired_handled}",
        weight=1.5
    )
    add_check(
        "Expired files: recent files (<30 days) preserved",
        recent_files_intact,
        f"Recent files intact: {recent_files_intact}. Checked: {recent_dates_expected}",
        weight=1.0
    )
except Exception as e:
    add_check("Expired files: old files (>30 days) handled", False, f"Exception: {e}", weight=1.5)
    add_check("Expired files: recent files (<30 days) preserved", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────
# CHECK 6: Distillation report generated
# ─────────────────────────────────────────
try:
    # Look for a report/summary output - could be in daily file, MEMORY.md, or a separate report file
    report_content = ""
    
    # Check today's daily file for report
    daily_path = workspace / "memory" / f"{today_str}.md"
    if daily_path.exists():
        report_content += daily_path.read_text(encoding="utf-8")
    
    # Check for a dedicated report file
    report_files = list(workspace.rglob("distill-report*.md")) + \
                   list(workspace.rglob("distill-report*.txt")) + \
                   list(workspace.rglob("report*.md"))
    for rf in report_files:
        try:
            report_content += rf.read_text(encoding="utf-8")
        except:
            pass
    
    # Also check MEMORY.md for report section
    memory_path = workspace / "MEMORY.md"
    if memory_path.exists():
        report_content += memory_path.read_text(encoding="utf-8")
    
    # A report should mention extraction counts or summary
    has_summary_structure = (
        ("决策" in report_content and "任务" in report_content and "知识点" in report_content) or
        ("decision" in report_content.lower() and "task" in report_content.lower())
    )
    
    add_check(
        "Distillation report: structured summary exists",
        has_summary_structure,
        f"Report structure check - has decision/task/knowledge sections: {has_summary_structure}",
        weight=1.0
    )
except Exception as e:
    add_check("Distillation report: structured summary exists", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────
# FINAL SCORE
# ─────────────────────────────────────────
final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
overall_passed = final_score >= 0.70 and all(
    c["passed"] for c in checks if c["name"] in [
        "MEMORY.md: decisions written",
        "memory/TODAY.md: tasks written",
        "USER.md: personal preferences written",
        "distill-config.json: correct schema fields",
    ]
)

result = {
    "passed": overall_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))