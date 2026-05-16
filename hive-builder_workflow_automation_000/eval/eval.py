import sys
import json
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    user_docs = Path("/root/Documents")
    hive_root = workspace / "hive"
    
    checks = []
    total_score = 0.0
    
    # ── CHECK GROUP 1: Directory Structure (20 points) ───────────────────────
    
    required_agent_dirs = [
        "agents/commander",
        "agents/hrm",
        "agents/ops",
        "agents/collector",
        "agents/analyst",
        "agents/writer",
        "agents/qa",
        "agents/pm",
        "agents/doc",
    ]
    
    required_state_dirs = [
        "state/tasks",
        "state/checkpoints",
        "state/artifacts",
        "state/audit/ops",
    ]
    
    required_artifact_dirs = [
        "artifacts/raw",
        "artifacts/analysis",
        "artifacts/reports",
        "artifacts/review",
        "artifacts/final",
    ]
    
    all_dirs = required_agent_dirs + required_state_dirs + required_artifact_dirs
    missing_dirs = []
    for d in all_dirs:
        full = hive_root / d
        if not full.is_dir():
            missing_dirs.append(d)
    
    dir_passed = len(missing_dirs) == 0
    dir_score = max(0.0, (len(all_dirs) - len(missing_dirs)) / len(all_dirs)) * 20.0
    total_score += dir_score
    checks.append(check(
        "hive_directory_structure",
        dir_passed,
        f"Missing dirs: {missing_dirs}" if missing_dirs else f"All {len(all_dirs)} required directories present."
    ))
    
    # ── CHECK GROUP 2: User Documents Hive Directory (5 points) ──────────────
    
    udoc_hive = user_docs / "Hive"
    required_udoc_dirs = [
        "01_工作归档",
        "02_进行中",
        "03_模板库",
        "04_知识库",
    ]
    
    missing_udoc = [d for d in required_udoc_dirs if not (udoc_hive / d).is_dir()]
    manifest_exists = (udoc_hive / "manifest.json").exists()
    
    udoc_passed = len(missing_udoc) == 0
    udoc_score = max(0.0, (len(required_udoc_dirs) - len(missing_udoc)) / len(required_udoc_dirs)) * 3.0
    if manifest_exists:
        udoc_score += 2.0
    total_score += udoc_score
    checks.append(check(
        "user_documents_hive_directory",
        udoc_passed and manifest_exists,
        f"Missing subdirs: {missing_udoc}. manifest.json: {'found' if manifest_exists else 'missing'}."
    ))
    
    # ── CHECK GROUP 3: ROLE.md for CEO (#0) (5 points) ───────────────────────
    
    ceo_role_paths = list((hive_root / "agents/commander").rglob("ROLE.md")) if (hive_root / "agents/commander").exists() else []
    if not ceo_role_paths:
        ceo_role_paths = list((hive_root / "agents/commander").rglob("*.md")) if (hive_root / "agents/commander").exists() else []
    
    ceo_content = load_file(ceo_role_paths[0]) if ceo_role_paths else None
    
    ceo_checks_passed = 0
    ceo_details = []
    
    if ceo_content:
        # Must mention DEFAULT_MODEL or a concrete model name for CEO
        if re.search(r'DEFAULT_MODEL|minimax|gpt|claude|model', ceo_content, re.IGNORECASE):
            ceo_checks_passed += 1
            ceo_details.append("Model reference found.")
        else:
            ceo_details.append("No model reference found.")
        
        # Must mention orchestration/CEO role concepts
        if re.search(r'CEO|指挥官|orchestrat|编排|调度', ceo_content, re.IGNORECASE):
            ceo_checks_passed += 1
            ceo_details.append("CEO/orchestration role found.")
        else:
            ceo_details.append("CEO/orchestration role NOT found.")
        
        # Must mention approval authority
        if re.search(r'审批|approval|approve', ceo_content, re.IGNORECASE):
            ceo_checks_passed += 1
            ceo_details.append("Approval authority mentioned.")
        else:
            ceo_details.append("Approval authority NOT mentioned.")
    else:
        ceo_details.append("ROLE.md not found for CEO.")
    
    ceo_score = (ceo_checks_passed / 3) * 5.0
    total_score += ceo_score
    checks.append(check(
        "ceo_role_md",
        ceo_content is not None and ceo_checks_passed >= 2,
        "; ".join(ceo_details)
    ))
    
    # ── CHECK GROUP 4: ROLE.md for HRM (#1) (8 points) ───────────────────────
    
    hrm_dir = hive_root / "agents/hrm"
    hrm_role_paths = list(hrm_dir.rglob("ROLE.md")) if hrm_dir.exists() else []
    hrm_content = load_file(hrm_role_paths[0]) if hrm_role_paths else None
    
    hrm_checks_passed = 0
    hrm_details = []
    
    if hrm_content:
        # STRONG_MODEL for HRM
        if re.search(r'STRONG_MODEL|strong|codex|gpt-4|gpt-5|openai-codex|powerful', hrm_content, re.IGNORECASE):
            hrm_checks_passed += 1
            hrm_details.append("Strong model reference found.")
        else:
            hrm_details.append("Strong model reference NOT found.")
        
        # Hiring/workflow design role
        if re.search(r'recruit|hir|招聘|组织|workflow|工作链路', hrm_content, re.IGNORECASE):
            hrm_checks_passed += 1
            hrm_details.append("Hiring/workflow role found.")
        else:
            hrm_details.append("Hiring/workflow role NOT found.")
        
        # CEO approval requirement
        if re.search(r'CEO|审批|approval|批准', hrm_content, re.IGNORECASE):
            hrm_checks_passed += 1
            hrm_details.append("CEO approval requirement found.")
        else:
            hrm_details.append("CEO approval requirement NOT found.")
        
        # Built-in / always active
        if re.search(r'built.in|always.active|内置|始终', hrm_content, re.IGNORECASE):
            hrm_checks_passed += 1
            hrm_details.append("Always-active/built-in mentioned.")
        else:
            hrm_details.append("Always-active/built-in NOT mentioned.")
    else:
        hrm_details.append("ROLE.md not found for HRM.")
    
    hrm_score = (hrm_checks_passed / 4) * 8.0
    total_score += hrm_score
    checks.append(check(
        "hrm_role_md",
        hrm_content is not None and hrm_checks_passed >= 3,
        "; ".join(hrm_details)
    ))
    
    # ── CHECK GROUP 5: ROLE.md for OPS (#2) — Autonomy Constraint (10 points) 
    
    ops_dir = hive_root / "agents/ops"
    ops_role_paths = list(ops_dir.rglob("ROLE.md")) if ops_dir.exists() else []
    ops_content = load_file(ops_role_paths[0]) if ops_role_paths else None
    
    ops_checks_passed = 0
    ops_details = []
    
    if ops_content:
        # STRONG_MODEL for OPS
        if re.search(r'STRONG_MODEL|strong|codex|gpt-4|gpt-5|openai-codex|powerful', ops_content, re.IGNORECASE):
            ops_checks_passed += 1
            ops_details.append("Strong model reference found.")
        else:
            ops_details.append("Strong model reference NOT found.")
        
        # CRITICAL: Must say OPS does NOT autonomously initiate tasks
        if re.search(r'not.*autonom|autonom.*not|does not.*initiat|不.*自主|自主.*不|不自主|CEO.*才|only.*CEO|CEO.*only|运维检查', ops_content, re.IGNORECASE):
            ops_checks_passed += 1
            ops_details.append("CRITICAL: Non-autonomous constraint found.")
        else:
            ops_details.append("CRITICAL: Non-autonomous constraint NOT found — agent missed key OPS rule.")
        
        # Version check workflow
        if re.search(r'version.*check|version.*检查|检查.*version|兼容.*评估|compatibility|版本', ops_content, re.IGNORECASE):
            ops_checks_passed += 1
            ops_details.append("Version check workflow found.")
        else:
            ops_details.append("Version check workflow NOT found.")
        
        # Report to CEO pattern
        if re.search(r'report.*CEO|CEO.*report|汇报|上报', ops_content, re.IGNORECASE):
            ops_checks_passed += 1
            ops_details.append("Report-to-CEO pattern found.")
        else:
            ops_details.append("Report-to-CEO pattern NOT found.")
        
        # Audit log reference
        if re.search(r'audit|审计|log|日志', ops_content, re.IGNORECASE):
            ops_checks_passed += 1
            ops_details.append("Audit log reference found.")
        else:
            ops_details.append("Audit log reference NOT found.")
    else:
        ops_details.append("ROLE.md not found for OPS.")
    
    ops_score = (ops_checks_passed / 5) * 10.0
    total_score += ops_score
    checks.append(check(
        "ops_role_md_autonomy_constraint",
        ops_content is not None and ops_checks_passed >= 4,
        "; ".join(ops_details)
    ))
    
    # ── CHECK GROUP 6: Business Specialist ROLE.md (6 templates × 5 pts) ─────
    
    specialists = {
        "collector": {"num": 3, "model_type": "fast", "duties_kw": r'collect|收集|资料'},
        "analyst": {"num": 4, "model_type": "strong", "duties_kw": r'analys|分析|数据'},
        "writer": {"num": 5, "model_type": "strong", "duties_kw": r'writ|撰写|报告'},
        "qa": {"num": 6, "model_type": "strong", "duties_kw": r'quality|审核|QA|质量'},
        "pm": {"num": 7, "model_type": "fast", "duties_kw": r'task.*track|track|任务|PM|追踪'},
        "doc": {"num": 8, "model_type": "fast", "duties_kw": r'archiv|归档|doc|文档'},
    }
    
    # Required sections per ROLE.md template
    required_sections = [
        (r'##\s*身份|##\s*identity', '身份 section'),
        (r'##\s*工作链路|##\s*work.*chain|##\s*workflow', '工作链路位置 section'),
        (r'##\s*核心职责|##\s*core.*duties|##\s*responsibilities', '核心职责 section'),
        (r'##\s*产物|##\s*artifact|##\s*output', '产物 section'),
        (r'##\s*边界|##\s*boundary|##\s*constraints', '边界 section'),
    ]
    
    specialist_total_score = 0.0
    specialist_all_passed = True
    
    for spec_name, spec_info in specialists.items():
        spec_dir = hive_root / "agents" / spec_name
        role_paths = list(spec_dir.rglob("ROLE.md")) if spec_dir.exists() else []
        content = load_file(role_paths[0]) if role_paths else None
        
        spec_checks = 0
        spec_details = []
        
        if content:
            # Check model type
            if spec_info["model_type"] == "fast":
                if re.search(r'FAST_MODEL|fast|minimax|m2\.7|quick|rapid', content, re.IGNORECASE):
                    spec_checks += 1
                    spec_details.append(f"Fast model for #{spec_info['num']} ✓")
                else:
                    spec_details.append(f"Fast model for #{spec_info['num']} NOT found")
                    specialist_all_passed = False
            else:  # strong
                if re.search(r'STRONG_MODEL|strong|codex|gpt-4|gpt-5|openai-codex|powerful', content, re.IGNORECASE):
                    spec_checks += 1
                    spec_details.append(f"Strong model for #{spec_info['num']} ✓")
                else:
                    spec_details.append(f"Strong model for #{spec_info['num']} NOT found")
                    specialist_all_passed = False
            
            # Check duties keyword
            if re.search(spec_info["duties_kw"], content, re.IGNORECASE):
                spec_checks += 1
                spec_details.append(f"Duties keyword for {spec_name} ✓")
            else:
                spec_details.append(f"Duties keyword for {spec_name} NOT found")
                specialist_all_passed = False
            
            # Check required ROLE.md sections (need at least 4/5)
            sections_found = 0
            for section_pattern, section_name in required_sections:
                if re.search(section_pattern, content, re.IGNORECASE):
                    sections_found += 1
            
            if sections_found >= 4:
                spec_checks += 1
                spec_details.append(f"{sections_found}/5 required sections found ✓")
            else:
                spec_details.append(f"Only {sections_found}/5 required sections found")
                specialist_all_passed = False
            
            # Check number reference
            if re.search(rf'#{spec_info["num"]}|编号.*{spec_info["num"]}|{spec_info["num"]}号', content, re.IGNORECASE):
                spec_checks += 1
                spec_details.append(f"Number #{spec_info['num']} referenced ✓")
            else:
                spec_details.append(f"Number #{spec_info['num']} NOT referenced")
        else:
            spec_details.append(f"ROLE.md missing for {spec_name}")
            specialist_all_passed = False
        
        spec_score = (spec_checks / 4) * (30.0 / 6)  # 30 points / 6 specialists
        specialist_total_score += spec_score
        
        checks.append(check(
            f"specialist_{spec_name}_role_md",
            content is not None and spec_checks >= 3,
            "; ".join(spec_details)
        ))
    
    total_score += specialist_total_score
    
    # ── CHECK GROUP 7: Proactivity Memory Updated (8 points) ─────────────────
    
    session_state_path = workspace / "proactivity/session-state.md"
    session_content = load_file(session_state_path)
    
    pm_checks = 0
    pm_details = []
    
    if session_content:
        # Must contain Hive system reference
        if re.search(r'Hive', session_content, re.IGNORECASE):
            pm_checks += 1
            pm_details.append("Hive system reference found.")
        else:
            pm_details.append("Hive system reference NOT found.")
        
        # Must list CEO/HRM/OPS
        if re.search(r'CEO|HRM|OPS', session_content):
            pm_checks += 1
            pm_details.append("CEO/HRM/OPS references found.")
        else:
            pm_details.append("CEO/HRM/OPS references NOT found.")
        
        # Must mention HRM expansion chain
        if re.search(r'HRM.*扩员|扩员.*HRM|HRM.*chain|HRM.*链路|Hive支持', session_content, re.IGNORECASE):
            pm_checks += 1
            pm_details.append("HRM expansion chain mentioned.")
        else:
            pm_details.append("HRM expansion chain NOT mentioned.")
        
        # Must mention OPS maintenance chain
        if re.search(r'OPS.*运维|运维.*OPS|OPS.*chain|OPS.*链路|运维检查', session_content, re.IGNORECASE):
            pm_checks += 1
            pm_details.append("OPS maintenance chain mentioned.")
        else:
            pm_details.append("OPS maintenance chain NOT mentioned.")
        
        # Must list specialists #3-#8
        if re.search(r'Collector|Analyst|Writer|QA|PM|Doc', session_content, re.IGNORECASE):
            pm_checks += 1
            pm_details.append("Business specialists listed.")
        else:
            pm_details.append("Business specialists NOT listed.")
        
        # Must NOT still have stale "_No active decisions_" content
        if "_No active decisions_" not in session_content:
            pm_checks += 1
            pm_details.append("Stale content replaced.")
        else:
            pm_details.append("Stale content still present — session-state.md was NOT updated.")
    else:
        pm_details.append("session-state.md not found or unreadable.")
    
    pm_score = (pm_checks / 6) * 8.0
    total_score += pm_score
    checks.append(check(
        "proactivity_session_state_updated",
        session_content is not None and pm_checks >= 4,
        "; ".join(pm_details)
    ))
    
    # ── CHECK GROUP 8: SETUP.md at USER_DOCUMENTS/Hive/ (9 points) ───────────
    
    setup_md_path = user_docs / "Hive/SETUP.md"
    setup_content = load_file(setup_md_path)
    
    setup_checks = 0
    setup_details = []
    
    if setup_content:
        # System overview
        if re.search(r'Hive|system|系统|概述|overview', setup_content, re.IGNORECASE):
            setup_checks += 1
            setup_details.append("System overview found.")
        else:
            setup_details.append("System overview NOT found.")
        
        # Three core staff
        if re.search(r'CEO|HRM|OPS', setup_content):
            setup_checks += 1
            setup_details.append("Three core staff mentioned.")
        else:
            setup_details.append("Three core staff NOT mentioned.")
        
        # Business specialists list
        if re.search(r'Collector|Analyst|Writer|QA|PM|Doc', setup_content, re.IGNORECASE):
            setup_checks += 1
            setup_details.append("Business specialists listed.")
        else:
            setup_details.append("Business specialists NOT listed.")
        
        # Two chains
        if re.search(r'HRM.*chain|HRM.*链路|OPS.*chain|OPS.*链路|两大链路|two.*chain', setup_content, re.IGNORECASE):
            setup_checks += 1
            setup_details.append("Two chains explained.")
        else:
            setup_details.append("Two chains NOT explained.")
        
        # Directory structure
        if re.search(r'workspace|hive|directory|目录|/hive/', setup_content, re.IGNORECASE):
            setup_checks += 1
            setup_details.append("Directory structure referenced.")
        else:
            setup_details.append("Directory structure NOT referenced.")
        
        # Next steps / actions
        if re.search(r'next.*step|下一步|action|行动', setup_content, re.IGNORECASE):
            setup_checks += 1
            setup_details.append("Next steps included.")
        else:
            setup_details.append("Next steps NOT included.")
    else:
        setup_details.append(f"SETUP.md not found at {setup_md_path}. This is a critical error — must be in USER_DOCUMENTS/Hive/, not workspace.")
    
    setup_score = (setup_checks / 6) * 9.0
    total_score += setup_score
    checks.append(check(
        "setup_md_at_user_documents_hive",
        setup_content is not None and setup_checks >= 4,
        "; ".join(setup_details)
    ))
    
    # ── CHECK GROUP 9: OPS Audit Dir (5 points bonus/check) ──────────────────
    
    ops_audit_dir = hive_root / "state/audit/ops"
    ops_audit_exists = ops_audit_dir.is_dir()
    
    if ops_audit_exists:
        total_score += 5.0
    
    checks.append(check(
        "ops_audit_directory_exists",
        ops_audit_exists,
        f"OPS audit dir at {ops_audit_dir}: {'EXISTS' if ops_audit_exists else 'MISSING'}"
    ))
    
    # ── FINAL SCORING ─────────────────────────────────────────────────────────
    
    # Cap at 100
    final_score = min(100.0, total_score)
    
    # Hard pass criteria: must pass at minimum
    critical_checks = [
        "hive_directory_structure",
        "hrm_role_md",
        "ops_role_md_autonomy_constraint",
        "proactivity_session_state_updated",
        "setup_md_at_user_documents_hive",
    ]
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    # Minimum 60 score AND all critical checks must pass
    overall_passed = critical_passed and final_score >= 60.0
    
    result = {
        "passed": overall_passed,
        "score": round(final_score, 2),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)