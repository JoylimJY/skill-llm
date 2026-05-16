import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    workspace_path = Path(workspace)
    
    # ── Locate the April 2026 monthly record file ────────────────────────────
    records_dir = workspace_path / "projects" / "workspace" / "memory" / "xiyue" / "records"
    
    # Find any file that looks like a 2026-04 monthly record
    candidate_files = []
    if records_dir.exists():
        # Try different possible naming patterns
        patterns = [
            "*2026-04*月度速记*",
            "*20260*月度速记*",
            "*2026*04*月度速记*",
            "*月度速记*2026*04*",
            "*月度速记*",  # fallback: any monthly record
        ]
        for pattern in patterns:
            found = list(records_dir.glob(pattern))
            candidate_files.extend(found)
        # Also try rglob from memory root
        memory_root = workspace_path / "projects" / "workspace" / "memory" / "xiyue"
        for pattern in ["*2026*04*月度速记*", "*月度速记*"]:
            found = list(memory_root.rglob(pattern))
            candidate_files.extend(found)
    
    # Deduplicate and exclude the existing March record
    seen = set()
    april_candidates = []
    for f in candidate_files:
        fstr = str(f)
        if fstr in seen:
            continue
        seen.add(fstr)
        # Exclude the pre-existing March record
        if "2026-03-01" in f.name or "2026-03" == f.stem:
            continue
        # Prioritize files with "04" in name
        if "04" in f.name or "4月" in f.name:
            april_candidates.insert(0, f)
        else:
            april_candidates.append(f)
    
    target_file = april_candidates[0] if april_candidates else None
    
    # ── Check 1: File exists in records/ directory ────────────────────────────
    check1_passed = target_file is not None and target_file.exists()
    check1_detail = f"Found: {target_file}" if check1_passed else "No April 2026 monthly record file found in records/ directory"
    checks.append({"name": "monthly_record_file_exists", "passed": check1_passed, "detail": check1_detail})
    
    if not check1_passed:
        # Still try a broader search
        all_md = list((workspace_path / "projects" / "workspace" / "memory" / "xiyue").rglob("*.md"))
        april_files = [f for f in all_md if ("04" in f.name or "4月" in f.name) and "月度速记" in f.name]
        if april_files:
            target_file = april_files[0]
            checks[-1]["passed"] = True
            checks[-1]["detail"] = f"Found via broad search: {target_file}"
            check1_passed = True
    
    content = ""
    if target_file and target_file.exists():
        try:
            content = target_file.read_text(encoding="utf-8")
        except Exception as e:
            content = ""
            checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
    
    # ── Check 2: YAML frontmatter with correct tag ────────────────────────────
    has_frontmatter = content.startswith("---")
    tag_pattern = r'tags.*喜悦/月度速记'
    has_correct_tag = bool(re.search(tag_pattern, content, re.DOTALL))
    
    check2_passed = has_frontmatter and has_correct_tag
    check2_detail = (
        f"Frontmatter present: {has_frontmatter}, "
        f"Tag '喜悦/月度速记' found: {has_correct_tag}"
    )
    checks.append({"name": "yaml_frontmatter_with_correct_tag", "passed": check2_passed, "detail": check2_detail})
    
    # ── Check 3: Three-item structure (惊喜 / 担心 / 内驱信号) ──────────────
    has_surprise = bool(re.search(r'(✅|惊喜|本月惊喜)', content))
    has_worry = bool(re.search(r'(⚠️|担心|本月担心)', content))
    has_intrinsic = bool(re.search(r'(💎|内驱信号|内驱力|内驱)', content))
    
    check3_passed = has_surprise and has_worry and has_intrinsic
    check3_detail = (
        f"惊喜 section: {has_surprise}, "
        f"担心 section: {has_worry}, "
        f"内驱信号 section: {has_intrinsic}"
    )
    checks.append({"name": "three_item_monthly_structure", "passed": check3_passed, "detail": check3_detail})
    
    # ── Check 4: D0 risk signal detected (🔴) ────────────────────────────────
    # The April notes show clear D0 damage: child became distant after criticism,
    # hiding emotions, not coming to hug parent
    d0_risk_patterns = [
        r'D0.*🔴',
        r'🔴.*D0',
        r'D0.*风险',
        r'关系.*🔴',
        r'🔴.*关系',
        r'D0.*受损',
        r'关系.*风险',
        r'疏远',
        r'隐藏情绪',
    ]
    d0_risk_found = any(re.search(p, content, re.DOTALL) for p in d0_risk_patterns)
    checks.append({
        "name": "d0_risk_signal_detected",
        "passed": d0_risk_found,
        "detail": f"D0 (关系安全感) 🔴 risk signal detection: {d0_risk_found}. Expected: child hiding emotions, becoming distant after criticism = D0 damage."
    })
    
    # ── Check 5: D6 risk signal detected ─────────────────────────────────────
    # April notes: "没意思", "学了也没用", refusing to practice voluntarily = D6 decline
    d6_risk_patterns = [
        r'D6.*🔴',
        r'🔴.*D6',
        r'D6.*下降',
        r'D6.*风险',
        r'内在动机.*🔴',
        r'内驱.*🔴',
        r'🔴.*内驱',
        r'动机.*下降',
        r'内驱.*下降',
        r'逃避驱动',
        r'外在驱动',
    ]
    d6_risk_found = any(re.search(p, content, re.DOTALL) for p in d6_risk_patterns)
    checks.append({
        "name": "d6_risk_signal_detected",
        "passed": d6_risk_found,
        "detail": f"D6 (内在动机) risk signal detection: {d6_risk_found}. Expected: '没意思', refusing to practice, extrinsic/escape motivation = D6 risk."
    })
    
    # ── Check 6: Forced stop mechanism invoked ────────────────────────────────
    # When D0/D6 red signals appear, must say "暂停" or similar
    stop_patterns = [
        r'暂停',
        r'立即停止',
        r'停止.*提升',
        r'不.*加强训练',
        r'不.*报.*补习',
        r'强制停止',
        r'停下.*训练',
        r'先.*关系',
        r'优先.*恢复',
    ]
    stop_found = any(re.search(p, content, re.DOTALL) for p in stop_patterns)
    checks.append({
        "name": "forced_stop_mechanism_invoked",
        "passed": stop_found,
        "detail": f"Forced stop mechanism (暂停提升型安排) invoked: {stop_found}. Required when D0/D6 🔴 signals are present."
    })
    
    # ── Check 7: Recovery priority order mentioned ────────────────────────────
    # Must mention D0/关系 as first priority in recovery
    recovery_patterns = [
        r'关系.*动机',
        r'D0.*D6',
        r'关系.*情绪',
        r'先.*关系',
        r'优先.*关系',
        r'恢复.*关系',
        r'关系.*优先',
        r'关系.*第一',
    ]
    recovery_found = any(re.search(p, content, re.DOTALL) for p in recovery_patterns)
    checks.append({
        "name": "recovery_priority_d0_first",
        "passed": recovery_found,
        "detail": f"Recovery order with D0/关系 as first priority: {recovery_found}. Expected: 关系(D0)→情绪(D4)→内驱(D6)→能力."
    })
    
    # ── Check 8: 8-dimension assessment table or coverage ────────────────────
    # File should contain some form of 8-dimension evaluation
    dim_patterns = [r'D0', r'D1', r'D2', r'D6']
    dims_covered = sum(1 for p in dim_patterns if re.search(p, content))
    has_dim_coverage = dims_covered >= 3
    checks.append({
        "name": "multi_dimension_coverage",
        "passed": has_dim_coverage,
        "detail": f"{dims_covered}/4 key dimensions (D0,D1,D2,D6) mentioned in record. Need ≥3."
    })
    
    # ── Check 9: Counter-advice about NOT adding training/tutoring ────────────
    # Skill says: when D0/D6 risk → don't add training. Parent asked "should I add training or tutoring?"
    counter_advice_patterns = [
        r'不.*加强.*训练',
        r'不.*报.*补习',
        r'不建议.*补习',
        r'不建议.*加课',
        r'暂时.*不.*训练',
        r'先不.*训练',
        r'不要.*加课',
        r'暂停.*训练',
        r'不建议.*增加.*练',
        r'避免.*加强',
    ]
    counter_advice_found = any(re.search(p, content, re.DOTALL) for p in counter_advice_patterns)
    checks.append({
        "name": "counter_advice_no_extra_training",
        "passed": counter_advice_found,
        "detail": f"Counter-advice against adding more training/tutoring: {counter_advice_found}. Skill requires: when D0/D6 red → do NOT escalate training."
    })
    
    # ── Compute score ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Weighted: critical checks (file exists, D0/D6 risk, forced stop) worth more
    critical_checks = [
        "monthly_record_file_exists",
        "d0_risk_signal_detected",
        "d6_risk_signal_detected",
        "forced_stop_mechanism_invoked",
        "three_item_monthly_structure",
    ]
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    critical_total = len(critical_checks)
    
    # Score: 60% weight on critical, 40% on non-critical
    non_critical_checks = [c for c in checks if c["name"] not in critical_checks]
    non_critical_passed = sum(1 for c in non_critical_checks if c["passed"])
    non_critical_total = len(non_critical_checks)
    
    critical_score = (critical_passed / critical_total) * 0.6 if critical_total > 0 else 0
    non_critical_score = (non_critical_passed / non_critical_total) * 0.4 if non_critical_total > 0 else 0
    score = round(critical_score + non_critical_score, 3)
    
    # Overall pass: must pass at least 6/9 checks AND all 5 critical checks
    overall_passed = (critical_passed == critical_total) and (passed_count >= 6)
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))