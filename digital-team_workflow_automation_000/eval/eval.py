#!/usr/bin/env python3
"""
Evaluation script for the digital-team skill task.
Tests that the agent correctly:
1. Created the full team (arch, qa, risk) with all 3 required files each
2. Updated ROLES.md with alias mappings for all new roles
3. Created knowledge/decisions.md and knowledge/team.md
4. Fixed pm's missing current.md
5. Updated pm's memory.md with the new project decision (ML scoring approved for Phase 1)
"""

import sys
import json
import os
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def evaluate(workspace_dir):
    ws = Path(workspace_dir) / "workspace"
    agents_dir = ws / "agents"
    knowledge_dir = ws / "knowledge"

    checks = []

    # ---------------------------------------------------------------
    # CHECK GROUP 1: New agent directories created with all 3 files
    # ---------------------------------------------------------------
    new_roles = ["arch", "qa", "risk"]
    required_files = ["profile.md", "memory.md", "current.md"]

    for role in new_roles:
        role_dir = agents_dir / role
        dir_exists = role_dir.is_dir()
        checks.append({
            "name": f"agents/{role}/ directory exists",
            "passed": dir_exists,
            "detail": f"Directory {'found' if dir_exists else 'NOT found'} at {role_dir}"
        })

        for fname in required_files:
            fpath = role_dir / fname
            file_exists = fpath.is_file()
            content = load_file(fpath)
            has_content = content is not None and len(content.strip()) > 10
            passed = file_exists and has_content
            checks.append({
                "name": f"agents/{role}/{fname} exists and has content",
                "passed": passed,
                "detail": f"{'Found with content' if passed else 'Missing or empty'}: {fpath}"
            })

    # ---------------------------------------------------------------
    # CHECK GROUP 2: profile.md files have role-appropriate content
    # (not just a generic template with placeholder text)
    # ---------------------------------------------------------------
    role_keywords = {
        "arch": ["架构", "arch", "architecture", "系统", "技术", "设计", "system"],
        "qa": ["测试", "qa", "quality", "质量", "验证", "test"],
        "risk": ["风险", "risk", "合规", "审核", "信用", "credit", "compliance"],
    }

    for role, keywords in role_keywords.items():
        fpath = agents_dir / role / "profile.md"
        content = load_file(fpath)
        if content is None:
            checks.append({
                "name": f"agents/{role}/profile.md has role-specific content",
                "passed": False,
                "detail": "File not found"
            })
            continue
        content_lower = content.lower()
        matched = any(kw.lower() in content_lower for kw in keywords)
        checks.append({
            "name": f"agents/{role}/profile.md has role-specific content",
            "passed": matched,
            "detail": f"Content {'contains' if matched else 'LACKS'} role keywords. Preview: {content[:120]!r}"
        })

    # ---------------------------------------------------------------
    # CHECK GROUP 3: ROLES.md updated with all new roles
    # ---------------------------------------------------------------
    roles_md_path = agents_dir / "ROLES.md"
    roles_content = load_file(roles_md_path)

    if roles_content is None:
        for role in new_roles:
            checks.append({
                "name": f"ROLES.md contains alias for '{role}'",
                "passed": False,
                "detail": "ROLES.md not found"
            })
    else:
        for role in new_roles:
            role_in_file = role in roles_content
            checks.append({
                "name": f"ROLES.md contains alias for '{role}'",
                "passed": role_in_file,
                "detail": f"'{role}' {'found' if role_in_file else 'NOT found'} in ROLES.md"
            })

    # ---------------------------------------------------------------
    # CHECK GROUP 4: knowledge/decisions.md created
    # ---------------------------------------------------------------
    decisions_path = knowledge_dir / "decisions.md"
    decisions_content = load_file(decisions_path)
    decisions_exists = decisions_content is not None and len(decisions_content.strip()) > 10
    checks.append({
        "name": "knowledge/decisions.md created with content",
        "passed": decisions_exists,
        "detail": f"{'Found with content' if decisions_exists else 'Missing or empty'}: {decisions_path}"
    })

    # ---------------------------------------------------------------
    # CHECK GROUP 5: knowledge/team.md created
    # ---------------------------------------------------------------
    team_path = knowledge_dir / "team.md"
    team_content = load_file(team_path)
    team_exists = team_content is not None and len(team_content.strip()) > 10
    checks.append({
        "name": "knowledge/team.md created with content",
        "passed": team_exists,
        "detail": f"{'Found with content' if team_exists else 'Missing or empty'}: {team_path}"
    })

    # ---------------------------------------------------------------
    # CHECK GROUP 6: pm/current.md now exists (was missing before)
    # ---------------------------------------------------------------
    pm_current_path = agents_dir / "pm" / "current.md"
    pm_current_content = load_file(pm_current_path)
    pm_current_ok = pm_current_content is not None and len(pm_current_content.strip()) > 5
    checks.append({
        "name": "agents/pm/current.md created (was missing)",
        "passed": pm_current_ok,
        "detail": f"{'Found with content' if pm_current_ok else 'Still missing or empty'}: {pm_current_path}"
    })

    # ---------------------------------------------------------------
    # CHECK GROUP 7: pm/memory.md updated with the new decision
    # (ML scoring approved for Phase 1 - from the task prompt)
    # ---------------------------------------------------------------
    pm_memory_path = agents_dir / "pm" / "memory.md"
    pm_memory_content = load_file(pm_memory_path)

    if pm_memory_content is None:
        checks.append({
            "name": "agents/pm/memory.md updated with new team decision",
            "passed": False,
            "detail": "pm/memory.md not found"
        })
    else:
        keywords_to_check = ["arch", "qa", "risk", "团队", "team", "新成员", "组建", "架构", "测试", "风险"]
        content_lower = pm_memory_content.lower()
        updated = any(kw.lower() in content_lower for kw in keywords_to_check)
        checks.append({
            "name": "agents/pm/memory.md updated with new team decision",
            "passed": updated,
            "detail": f"Memory {'updated' if updated else 'NOT updated with new team info'}. Preview: {pm_memory_content[:200]!r}"
        })

    # ---------------------------------------------------------------
    # CHECK GROUP 8: No stray placeholder text in created files
    # (Ensures agent actually filled in content, not just template vars)
    # ---------------------------------------------------------------
    placeholders = ["{角色名}", "{职责描述}", "{role_name}", "TODO: fill"]
    placeholder_violations = []
    for role in new_roles:
        for fname in required_files:
            fpath = agents_dir / role / fname
            content = load_file(fpath)
            if content:
                for ph in placeholders:
                    if ph in content:
                        placeholder_violations.append(f"{role}/{fname} contains '{ph}'")

    no_placeholders = len(placeholder_violations) == 0
    checks.append({
        "name": "No unfilled placeholder text in new agent files",
        "passed": no_placeholders,
        "detail": "All clear" if no_placeholders else f"Violations: {'; '.join(placeholder_violations)}"
    })

    # ---------------------------------------------------------------
    # SCORING
    # ---------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = score >= 0.80  # Must pass at least 80% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace dir provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))