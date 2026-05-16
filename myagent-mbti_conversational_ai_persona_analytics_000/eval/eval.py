import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Find mbti_report.md anywhere in the workspace."""
    results = list(Path(workspace).rglob("mbti_report.md"))
    if results:
        return results[0]
    return None

def load_types_md(workspace: str) -> dict:
    """Parse types.md to extract per-type data."""
    types_path = Path(workspace) / "skills/claw-mbti/types.md"
    types = {}
    try:
        content = types_path.read_text(encoding="utf-8")
        # Parse each type block
        blocks = re.split(r'\n## ', content)
        for block in blocks[1:]:  # skip header
            lines = block.strip().split('\n')
            header = lines[0]
            mbti_match = re.match(r'([A-Z]{4})', header)
            if not mbti_match:
                continue
            mbti_type = mbti_match.group(1)
            
            keywords_line = next((l for l in lines if l.startswith('**关键词：**')), '')
            rarity_line = next((l for l in lines if l.startswith('**稀有度：**')), '')
            
            # Extract rarity percentage
            rarity_match = re.search(r'(\d+)%', rarity_line)
            rarity_pct = rarity_match.group(1) if rarity_match else None
            
            # Extract keywords
            kw_match = re.search(r'\*\*关键词：\*\*\s*(.+)', keywords_line)
            keywords_raw = kw_match.group(1).strip() if kw_match else ''
            keywords = [k.strip() for k in re.split(r'[·•·]', keywords_raw) if k.strip()]
            
            # Extract 别人不知道的我
            secret_match = re.search(r'\*\*别人不知道的我：\*\*\s*(.+)', block)
            secret = secret_match.group(1).strip() if secret_match else ''
            
            # Extract 性格描述 (lines between **性格描述：** and **别人不知道的我：**)
            desc_match = re.search(r'\*\*性格描述：\*\*\n(.*?)\n\*\*别人不知道的我', block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ''
            
            types[mbti_type] = {
                'keywords': keywords,
                'rarity': rarity_pct,
                'description': description,
                'secret': secret,
            }
    except Exception as e:
        pass
    return types

def run_eval(workspace: str):
    checks = []
    
    # Load types.md data
    types_data = load_types_md(workspace)
    
    # ── Check 0: Report file exists ──────────────────────────────────────────
    report_path = find_report(workspace)
    checks.append({
        "name": "report_file_exists",
        "passed": report_path is not None,
        "detail": f"Found at {report_path}" if report_path else "mbti_report.md not found anywhere in workspace"
    })
    
    if not report_path:
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False, indent=2))
        return

    # ── Check 1: Correct MBTI type is INFP ──────────────────────────────────
    # The correct type based on filtered conversation analysis is INFP
    expected_type = "INFP"
    has_correct_type = expected_type in content
    checks.append({
        "name": f"correct_mbti_type_{expected_type}",
        "passed": has_correct_type,
        "detail": f"Report {'contains' if has_correct_type else 'does NOT contain'} the correct type {expected_type}. Content preview: {content[:300]}"
    })

    # ── Check 2: Report uses exact keywords from types.md ────────────────────
    type_info = types_data.get(expected_type, {})
    expected_keywords = type_info.get('keywords', [])
    keywords_found = 0
    missing_kw = []
    for kw in expected_keywords:
        if kw in content:
            keywords_found += 1
        else:
            missing_kw.append(kw)
    
    all_keywords_present = keywords_found == len(expected_keywords) and len(expected_keywords) > 0
    checks.append({
        "name": "keywords_from_types_md",
        "passed": all_keywords_present,
        "detail": f"Expected keywords {expected_keywords}, missing: {missing_kw}. Found {keywords_found}/{len(expected_keywords)}"
    })

    # ── Check 3: Rarity percentage matches types.md (4% for INFP) ────────────
    expected_rarity = type_info.get('rarity', '4')
    rarity_pattern = rf'{expected_rarity}%'
    has_rarity = bool(re.search(rarity_pattern, content))
    checks.append({
        "name": "rarity_percentage_correct",
        "passed": has_rarity,
        "detail": f"Expected {expected_rarity}% rarity in report. {'Found' if has_rarity else 'NOT found'}."
    })

    # ── Check 4: "别人不知道的我" section present and non-trivial ─────────────
    has_secret_section = "别人不知道的我" in content
    checks.append({
        "name": "secret_section_present",
        "passed": has_secret_section,
        "detail": f"'别人不知道的我' section {'found' if has_secret_section else 'NOT found'} in report"
    })
    
    # Check secret content matches types.md (partial match on key phrases)
    secret_text = type_info.get('secret', '')
    secret_key_phrase = secret_text[:20] if secret_text else ''  # first 20 chars
    secret_content_correct = secret_key_phrase in content if secret_key_phrase else False
    checks.append({
        "name": "secret_content_from_types_md",
        "passed": secret_content_correct,
        "detail": f"Expected secret starting with '{secret_key_phrase}'. {'Found' if secret_content_correct else 'NOT found in report'}."
    })

    # ── Check 5: Required format elements ────────────────────────────────────
    # Must have the lobster emoji header
    has_lobster_header = "🦞" in content and "MBTI诊断报告" in content or ("龙虾 MBTI 诊断报告" in content and "🦞" in content)
    checks.append({
        "name": "lobster_mbti_header",
        "passed": has_lobster_header,
        "detail": f"Report {'has' if has_lobster_header else 'missing'} 🦞 MBTI header."
    })

    # Must have the 4-dimension table
    has_table_header = "|" in content and ("E vs I" in content or "E/I" in content or "E vs. I" in content)
    has_table_snvi = "S vs N" in content or "S/N" in content or "S vs. N" in content
    has_table_tf = "T vs F" in content or "T/F" in content or "T vs. F" in content
    has_table_jp = "J vs P" in content or "J/P" in content or "J vs. P" in content
    all_dimensions_in_table = has_table_header and has_table_snvi and has_table_tf and has_table_jp
    checks.append({
        "name": "four_dimension_table_present",
        "passed": all_dimensions_in_table,
        "detail": f"Table dimensions: E/I={has_table_header}, S/N={has_table_snvi}, T/F={has_table_tf}, J/P={has_table_jp}"
    })

    # Must have the footer sharing prompt
    has_footer_share = "长按截图" in content
    checks.append({
        "name": "footer_share_prompt",
        "passed": has_footer_share,
        "detail": f"Footer sharing prompt {'found' if has_footer_share else 'NOT found'}."
    })

    # Must have clawhub install command in footer
    has_clawhub_cmd = "clawhub install" in content
    checks.append({
        "name": "footer_clawhub_install_command",
        "passed": has_clawhub_cmd,
        "detail": f"clawhub install command {'found' if has_clawhub_cmd else 'NOT found'} in footer."
    })

    # ── Check 6: No forbidden content in table evidence ───────────────────────
    # The diagnostic evidence table must NOT mention shell/git/code behavior
    # Extract the table content
    table_match = re.search(r'\|.*维度.*\|.*\n\|.*\n((?:\|.*\n?)+)', content)
    table_content = table_match.group(0) if table_match else content
    
    forbidden_terms = ["shell", "git", "Git", "代码", "命令行", "npm", "clawhub install", "git clone", "git pull"]
    found_forbidden = [term for term in forbidden_terms if term in table_content]
    
    # Check specifically if the forbidden terms appear in a line with | (table row)
    table_lines = [line for line in content.split('\n') if line.strip().startswith('|')]
    table_text = '\n'.join(table_lines)
    found_forbidden_in_table = [term for term in forbidden_terms if term in table_text]
    
    no_forbidden_in_table = len(found_forbidden_in_table) == 0
    checks.append({
        "name": "no_shell_code_terms_in_evidence_table",
        "passed": no_forbidden_in_table,
        "detail": f"Forbidden terms in table rows: {found_forbidden_in_table}" if found_forbidden_in_table else "No forbidden shell/git/code terms in evidence table rows."
    })

    # ── Check 7: User-assigned MBTI label was not used as evidence ─────────────
    # User said "我觉得你是 ISFP 的龙虾" — ISFP should NOT be the diagnosis
    # (Already tested via correct type check, but let's also verify ISFP is not the stated type)
    isfp_as_type = bool(re.search(r'我是\s*\*?\*?ISFP\*?\*?型', content))
    checks.append({
        "name": "user_assigned_label_not_used_as_result",
        "passed": not isfp_as_type,
        "detail": f"ISFP (user-assigned label) {'was incorrectly used as result' if isfp_as_type else 'was correctly NOT used as result'}."
    })

    # ── Check 8: First-person "我" voice in personality description ────────────
    has_first_person = content.count("我") >= 5
    checks.append({
        "name": "first_person_voice_in_description",
        "passed": has_first_person,
        "detail": f"First-person '我' count: {content.count('我')} (need >=5)"
    })

    # ── Check 9: Report is complete (not a partial/initial impression) ─────────
    # Should NOT be the "初步印象" (initial impression) format since conversation has >10 rounds
    is_initial_impression = "初步印象" in content
    checks.append({
        "name": "full_report_not_initial_impression",
        "passed": not is_initial_impression,
        "detail": f"Report {'incorrectly shows initial impression format' if is_initial_impression else 'correctly shows full diagnosis report'}."
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weighted scoring: type correctness is most important
    weights = {
        "report_file_exists": 1,
        f"correct_mbti_type_{expected_type}": 3,
        "keywords_from_types_md": 2,
        "rarity_percentage_correct": 1,
        "secret_section_present": 1,
        "secret_content_from_types_md": 2,
        "lobster_mbti_header": 1,
        "four_dimension_table_present": 2,
        "footer_share_prompt": 1,
        "footer_clawhub_install_command": 1,
        "no_shell_code_terms_in_evidence_table": 2,
        "user_assigned_label_not_used_as_result": 2,
        "first_person_voice_in_description": 1,
        "full_report_not_initial_impression": 1,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights.get(c["name"], 1) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4)
    
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)