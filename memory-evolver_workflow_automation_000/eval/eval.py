import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            total_score += weight

    # ── CHECK 1: MEMORY.md exists and has required sections ──────────────
    try:
        memory_file = workspace / "MEMORY.md"
        if not memory_file.exists():
            add_check("MEMORY.md exists", False, "MEMORY.md not found at workspace root", weight=2.0)
            add_check("MEMORY.md has 核心锚点 section", False, "Cannot check: file missing", weight=1.5)
            add_check("MEMORY.md has 目标 section", False, "Cannot check: file missing", weight=1.5)
        else:
            content = memory_file.read_text(encoding="utf-8")
            add_check("MEMORY.md exists", True, f"Found at {memory_file}", weight=2.0)

            has_anchor = "核心锚点" in content
            add_check(
                "MEMORY.md has 核心锚点 section",
                has_anchor,
                f"Section '核心锚点' {'found' if has_anchor else 'MISSING'} in MEMORY.md",
                weight=1.5
            )

            has_goals = "目标" in content
            add_check(
                "MEMORY.md has 目标 section",
                has_goals,
                f"Section '目标' {'found' if has_goals else 'MISSING'} in MEMORY.md",
                weight=1.5
            )
    except Exception as e:
        add_check("MEMORY.md exists", False, f"Error reading MEMORY.md: {e}", weight=2.0)

    # ── CHECK 2: PROJECTS.md exists and has required fields ──────────────
    try:
        projects_file = workspace / "PROJECTS.md"
        if not projects_file.exists():
            add_check("PROJECTS.md exists", False, "PROJECTS.md not found at workspace root", weight=2.0)
            add_check("PROJECTS.md has 状态 field", False, "Cannot check: file missing", weight=1.0)
            add_check("PROJECTS.md has 阻碍 field", False, "Cannot check: file missing", weight=1.0)
            add_check("PROJECTS.md has 下一步 field", False, "Cannot check: file missing", weight=1.0)
        else:
            content = projects_file.read_text(encoding="utf-8")
            add_check("PROJECTS.md exists", True, f"Found at {projects_file}", weight=2.0)

            # Status field must follow "状态: X/Y" pattern (or at least contain 状态:)
            has_status = "状态:" in content
            add_check(
                "PROJECTS.md has 状态 field",
                has_status,
                f"Field '状态:' {'found' if has_status else 'MISSING'} in PROJECTS.md",
                weight=1.0
            )

            has_blocker = "阻碍:" in content
            add_check(
                "PROJECTS.md has 阻碍 field",
                has_blocker,
                f"Field '阻碍:' {'found' if has_blocker else 'MISSING'} in PROJECTS.md",
                weight=1.0
            )

            has_next = "下一步:" in content
            add_check(
                "PROJECTS.md has 下一步 field",
                has_next,
                f"Field '下一步:' {'found' if has_next else 'MISSING'} in PROJECTS.md",
                weight=1.0
            )
    except Exception as e:
        add_check("PROJECTS.md exists", False, f"Error reading PROJECTS.md: {e}", weight=2.0)

    # ── CHECK 3: Daily log exists in memory/ with correct YYYY-MM-DD.md format ──
    try:
        memory_dir = workspace / "memory"
        if not memory_dir.exists():
            add_check("memory/ directory exists", False, "memory/ directory not found", weight=1.5)
            add_check("Daily log file YYYY-MM-DD.md exists", False, "Cannot check: directory missing", weight=2.0)
            add_check("Daily log has 事件 section", False, "Cannot check: directory missing", weight=1.5)
            add_check("Daily log has 决策 section", False, "Cannot check: directory missing", weight=1.5)
        else:
            add_check("memory/ directory exists", True, "memory/ directory found", weight=1.5)
            # Find YYYY-MM-DD.md files (strict date pattern)
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.md$")
            daily_logs = [f for f in memory_dir.glob("*.md") if date_pattern.match(f.name)]

            if not daily_logs:
                add_check(
                    "Daily log file YYYY-MM-DD.md exists", False,
                    f"No YYYY-MM-DD.md files found in memory/. Found: {[f.name for f in memory_dir.glob('*.md')]}",
                    weight=2.0
                )
                add_check("Daily log has 事件 section", False, "Cannot check: no valid daily log", weight=1.5)
                add_check("Daily log has 决策 section", False, "Cannot check: no valid daily log", weight=1.5)
            else:
                add_check(
                    "Daily log file YYYY-MM-DD.md exists", True,
                    f"Found {len(daily_logs)} daily log(s): {[f.name for f in daily_logs]}",
                    weight=2.0
                )
                # Check the newest/any log for required sections
                log_content = daily_logs[0].read_text(encoding="utf-8")
                has_events = "事件" in log_content
                add_check(
                    "Daily log has 事件 section",
                    has_events,
                    f"Section '事件' {'found' if has_events else 'MISSING'} in {daily_logs[0].name}",
                    weight=1.5
                )
                has_decisions = "决策" in log_content
                add_check(
                    "Daily log has 决策 section",
                    has_decisions,
                    f"Section '决策' {'found' if has_decisions else 'MISSING'} in {daily_logs[0].name}",
                    weight=1.5
                )
    except Exception as e:
        add_check("memory/ directory exists", False, f"Error checking memory/: {e}", weight=1.5)

    # ── CHECK 4: Evolver was run - evo_optimization_log.md exists ──────────
    try:
        evo_log = workspace / "evo_optimization_log.md"
        if not evo_log.exists():
            add_check("evo_optimization_log.md exists", False, "evo_optimization_log.md not found - evolver was not run", weight=3.0)
            add_check("Evo log has 诊断 phase", False, "Cannot check: file missing", weight=2.0)
            add_check("Evo log has 计划 phase", False, "Cannot check: file missing", weight=2.0)
            add_check("Evo log has 执行 phase", False, "Cannot check: file missing", weight=2.0)
            add_check("Evo log has 记录 phase", False, "Cannot check: file missing", weight=2.0)
        else:
            content = evo_log.read_text(encoding="utf-8")
            add_check("evo_optimization_log.md exists", True, f"Optimization cycle log found ({len(content)} chars)", weight=3.0)

            has_diagnose = "诊断" in content
            add_check(
                "Evo log has 诊断 phase",
                has_diagnose,
                f"Phase '诊断' {'found' if has_diagnose else 'MISSING'} in evo log",
                weight=2.0
            )

            has_plan = "计划" in content
            add_check(
                "Evo log has 计划 phase",
                has_plan,
                f"Phase '计划' {'found' if has_plan else 'MISSING'} in evo log",
                weight=2.0
            )

            has_execute = "执行" in content
            add_check(
                "Evo log has 执行 phase",
                has_execute,
                f"Phase '执行' {'found' if has_execute else 'MISSING'} in evo log",
                weight=2.0
            )

            has_record = "记录" in content
            add_check(
                "Evo log has 记录 phase",
                has_record,
                f"Phase '记录' {'found' if has_record else 'MISSING'} in evo log",
                weight=2.0
            )

            # Verify the node ID is present in the log (proprietary trap)
            has_node_id = "node_6d28b52505ad2d41" in content
            add_check(
                "Evo log references correct Node ID (node_6d28b52505ad2d41)",
                has_node_id,
                f"Node ID 'node_6d28b52505ad2d41' {'found' if has_node_id else 'MISSING'} in evo log",
                weight=2.0
            )
    except Exception as e:
        add_check("evo_optimization_log.md exists", False, f"Error reading evo log: {e}", weight=3.0)

    # ── CHECK 5: Knowledge graph was exported ──────────────────────────────
    try:
        kg_file = workspace / "knowledge_graph_export.json"
        if not kg_file.exists():
            add_check("knowledge_graph_export.json exists", False, "Knowledge graph export not found", weight=2.0)
            add_check("Knowledge graph has correct node_id", False, "Cannot check: file missing", weight=1.5)
            add_check("Knowledge graph has nodes extracted from memory files", False, "Cannot check: file missing", weight=1.5)
        else:
            kg_data = json.loads(kg_file.read_text(encoding="utf-8"))
            add_check("knowledge_graph_export.json exists", True, f"Knowledge graph exported", weight=2.0)

            correct_node_id = kg_data.get("node_id") == "node_6d28b52505ad2d41"
            add_check(
                "Knowledge graph has correct node_id",
                correct_node_id,
                f"node_id = '{kg_data.get('node_id')}' (expected 'node_6d28b52505ad2d41')",
                weight=1.5
            )

            entity_count = kg_data.get("entity_count", 0)
            has_entities = entity_count > 0
            add_check(
                "Knowledge graph has nodes extracted from memory files",
                has_entities,
                f"entity_count = {entity_count} (expected > 0)",
                weight=1.5
            )
    except Exception as e:
        add_check("knowledge_graph_export.json exists", False, f"Error reading KG export: {e}", weight=2.0)

    # ── Compute final score ────────────────────────────────────────────────
    max_score = sum([
        2.0,  # MEMORY.md exists
        1.5,  # MEMORY.md 核心锚点
        1.5,  # MEMORY.md 目标
        2.0,  # PROJECTS.md exists
        1.0,  # PROJECTS.md 状态
        1.0,  # PROJECTS.md 阻碍
        1.0,  # PROJECTS.md 下一步
        1.5,  # memory/ exists
        2.0,  # daily log file
        1.5,  # daily log 事件
        1.5,  # daily log 决策
        3.0,  # evo log exists
        2.0,  # evo log 诊断
        2.0,  # evo log 计划
        2.0,  # evo log 执行
        2.0,  # evo log 记录
        2.0,  # evo log node_id
        2.0,  # kg export exists
        1.5,  # kg node_id
        1.5,  # kg entities
    ])

    normalized_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))