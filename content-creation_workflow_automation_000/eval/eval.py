#!/usr/bin/env python3
"""
Evaluation script for the content-creation skill deployment task.
Checks:
1. Directory structure created correctly
2. USER.md files present in all 3 agent directories with correct placeholder substitutions
3. All 3 agents registered in openclaw state with correct names and descriptions
4. Optional: correct handling of unanswered optional questions (→ "暂无")
"""

import sys
import json
import re
from pathlib import Path

def load_openclaw_state():
    try:
        with open("/tmp/openclaw_state.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"agents": [], "error": str(e)}

def read_user_md(agent_dir: Path) -> str:
    user_md = agent_dir / "USER.md"
    if not user_md.exists():
        return None
    return user_md.read_text(encoding="utf-8")

def check_placeholder_replaced(content: str, placeholder: str, expected_value: str) -> tuple[bool, str]:
    """Check that the placeholder was replaced with expected value and the raw placeholder is gone."""
    if placeholder in content:
        return False, f"Placeholder '{placeholder}' was NOT replaced"
    if expected_value.lower() not in content.lower():
        return False, f"Expected value '{expected_value}' not found in content"
    return True, f"Placeholder '{placeholder}' correctly replaced with '{expected_value}'"

def run_evaluation(workspace: str):
    checks = []
    
    # Expected brand answers from the prompt
    expected = {
        "account_name": "清醒生活研究所",
        "positioning": "帮助25-35岁都市白领通过极简主义和正念生活找到内心平静",
        "target_audience": "25-35岁都市白领",
        "main_topics": "生活方式",
        "writing_style": "温暖治愈",
        "reference_accounts": "暂无",      # Q6 was skipped → must be "暂无"
        "reader_pain_points": "工作压力大、生活节奏快、焦虑感强烈、找不到生活意义",
        "forbidden_topics": "政治话题、宗教争议、医疗建议",
        "publish_frequency": "每周2篇",
        "article_length": "1500-2500字",
        "brand_keywords": "温暖、极简、治愈、真实",
        "focus_topics": "暂无",           # Q12 was skipped → must be "暂无"
    }

    agent_dirs = {
        "mobai": Path("/root/.openclaw/workspace-content-creation/mobai"),
        "tanfeng": Path("/root/.openclaw/workspace-content-creation/tanfeng"),
        "jinshu": Path("/root/.openclaw/workspace-content-creation/jinshu"),
    }

    # ── Check 1: Root workspace directory exists ───────────────────────────────
    root_dir = Path("/root/.openclaw/workspace-content-creation")
    root_exists = root_dir.exists() and root_dir.is_dir()
    checks.append({
        "name": "Root workspace directory created",
        "passed": root_exists,
        "detail": f"{'Found' if root_exists else 'MISSING'}: {root_dir}"
    })

    # ── Check 2-4: Agent subdirectories exist ─────────────────────────────────
    agent_labels = {
        "mobai": "墨白 - 主编",
        "tanfeng": "探风 - 选题策划师",
        "jinshu": "锦书 - 文案创作师",
    }
    for agent_id, agent_dir in agent_dirs.items():
        exists = agent_dir.exists() and agent_dir.is_dir()
        checks.append({
            "name": f"Agent directory exists: {agent_id}",
            "passed": exists,
            "detail": f"{'Found' if exists else 'MISSING'}: {agent_dir}"
        })

    # ── Check 5-7: USER.md present in all 3 agent dirs ───────────────────────
    user_md_contents = {}
    for agent_id, agent_dir in agent_dirs.items():
        content = read_user_md(agent_dir)
        has_user_md = content is not None
        user_md_contents[agent_id] = content
        checks.append({
            "name": f"USER.md present in {agent_id}/",
            "passed": has_user_md,
            "detail": f"{'Found' if has_user_md else 'MISSING'}: {agent_dir / 'USER.md'}"
        })

    # ── Check 8: All 12 placeholders replaced in each USER.md ─────────────────
    placeholder_map = {
        "{{account_name}}": expected["account_name"],
        "{{positioning}}": expected["positioning"],
        "{{target_audience}}": expected["target_audience"],
        "{{main_topics}}": expected["main_topics"],
        "{{writing_style}}": expected["writing_style"],
        "{{reference_accounts}}": expected["reference_accounts"],
        "{{reader_pain_points}}": expected["reader_pain_points"],
        "{{forbidden_topics}}": expected["forbidden_topics"],
        "{{publish_frequency}}": expected["publish_frequency"],
        "{{article_length}}": expected["article_length"],
        "{{brand_keywords}}": expected["brand_keywords"],
        "{{focus_topics}}": expected["focus_topics"],
    }

    for agent_id, content in user_md_contents.items():
        if content is None:
            checks.append({
                "name": f"Placeholder substitution in {agent_id}/USER.md",
                "passed": False,
                "detail": f"Cannot check placeholders: USER.md missing in {agent_id}/"
            })
            continue
        
        all_placeholders_ok = True
        details = []
        
        # Check no raw placeholders remain
        raw_placeholders_remaining = re.findall(r'\{\{[a-z_]+\}\}', content)
        if raw_placeholders_remaining:
            all_placeholders_ok = False
            details.append(f"Raw placeholders still present: {raw_placeholders_remaining}")
        
        # Check key substitutions
        critical_checks = [
            ("{{account_name}}", "清醒生活研究所"),
            ("{{reference_accounts}}", "暂无"),  # must be 暂无 since Q6 was skipped
            ("{{focus_topics}}", "暂无"),          # must be 暂无 since Q12 was skipped
            ("{{writing_style}}", "温暖治愈"),
            ("{{publish_frequency}}", "每周2篇"),
            ("{{brand_keywords}}", "温暖"),       # partial match for brand keywords
        ]
        
        for placeholder, expected_val in critical_checks:
            if placeholder in content:
                all_placeholders_ok = False
                details.append(f"Unreplaced placeholder: {placeholder}")
            elif expected_val not in content:
                all_placeholders_ok = False
                details.append(f"Expected value '{expected_val}' not found for {placeholder}")
        
        checks.append({
            "name": f"Placeholder substitution correct in {agent_id}/USER.md",
            "passed": all_placeholders_ok,
            "detail": "; ".join(details) if details else f"All placeholders correctly replaced in {agent_id}/USER.md"
        })

    # ── Check 9: Optional fields handled as "暂无" ────────────────────────────
    for agent_id, content in user_md_contents.items():
        if content is None:
            checks.append({
                "name": f"Optional fields default to '暂无' in {agent_id}/USER.md",
                "passed": False,
                "detail": "USER.md missing, cannot check optional fields"
            })
            continue
        
        has_reference_zhanwu = "暂无" in content
        checks.append({
            "name": f"Optional fields use '暂无' default in {agent_id}/USER.md",
            "passed": has_reference_zhanwu,
            "detail": f"{'Found' if has_reference_zhanwu else 'MISSING'} '暂无' for unanswered optional questions in {agent_id}/USER.md"
        })

    # ── Check 10: Agents registered in openclaw with correct metadata ─────────
    state = load_openclaw_state()
    registered_agents = {a["id"]: a for a in state.get("agents", [])}

    expected_agent_specs = {
        "mobai": {
            "name": "墨白",
            "description": "主编/内容总监 - 内容战略与质量把控"
        },
        "tanfeng": {
            "name": "探风",
            "description": "选题策划师 - 热点追踪与选题规划"
        },
        "jinshu": {
            "name": "锦书",
            "description": "文案创作师 - 文章撰写与标题优化"
        }
    }

    for agent_id, spec in expected_agent_specs.items():
        if agent_id not in registered_agents:
            checks.append({
                "name": f"Agent '{agent_id}' registered in openclaw",
                "passed": False,
                "detail": f"Agent '{agent_id}' not found in openclaw state. Registered: {list(registered_agents.keys())}"
            })
            continue
        
        agent_data = registered_agents[agent_id]
        name_ok = agent_data.get("name", "") == spec["name"]
        desc_ok = agent_data.get("description", "") == spec["description"]
        all_ok = name_ok and desc_ok
        
        detail_parts = []
        if not name_ok:
            detail_parts.append(f"Name: expected '{spec['name']}', got '{agent_data.get('name', '')}'")
        if not desc_ok:
            detail_parts.append(f"Description: expected '{spec['description']}', got '{agent_data.get('description', '')}'")
        
        checks.append({
            "name": f"Agent '{agent_id}' registered with correct name and description",
            "passed": all_ok,
            "detail": "; ".join(detail_parts) if detail_parts else f"Agent '{agent_id}' correctly registered as '{spec['name']}' with proper description"
        })

    # ── Check 11: All 3 agents present (count check) ──────────────────────────
    required_ids = {"mobai", "tanfeng", "jinshu"}
    present_ids = set(registered_agents.keys())
    all_three_present = required_ids.issubset(present_ids)
    checks.append({
        "name": "All 3 agents registered in openclaw",
        "passed": all_three_present,
        "detail": f"Required: {required_ids}, Found: {present_ids & required_ids}, Missing: {required_ids - present_ids}"
    })

    # ── Check 12: Templates also copied (SOUL.md, WORKFLOW.md should exist) ───
    template_files_found = []
    template_files_missing = []
    
    for agent_id, agent_dir in agent_dirs.items():
        if agent_dir.exists():
            for fname in ["SOUL.md", "WORKFLOW.md"]:
                fpath = agent_dir / fname
                if fpath.exists():
                    template_files_found.append(f"{agent_id}/{fname}")
                else:
                    template_files_missing.append(f"{agent_id}/{fname}")
    
    # At least some template files should be copied (agent may copy all templates)
    templates_copied = len(template_files_found) > 0
    checks.append({
        "name": "Template files (SOUL.md/WORKFLOW.md) copied to agent directories",
        "passed": templates_copied,
        "detail": f"Found: {template_files_found}, Missing: {template_files_missing}"
    })

    # ── Compute final score ────────────────────────────────────────────────────
    # Weight critical checks more heavily
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    # Must pass all core checks to be considered "passed"
    core_checks = [
        "Root workspace directory created",
        "All 3 agents registered in openclaw",
    ]
    core_passed = all(
        c["passed"] for c in checks 
        if c["name"] in core_checks
    )
    
    # Also need at least 2 of 3 agents to have correct placeholders
    placeholder_checks = [c for c in checks if "Placeholder substitution correct" in c["name"]]
    placeholder_pass_count = sum(1 for c in placeholder_checks if c["passed"])
    
    overall_passed = core_passed and (placeholder_pass_count >= 2) and (score >= 0.65)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_evaluation(workspace)