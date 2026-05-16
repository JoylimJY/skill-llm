import sys
import json
import pathlib
import re

def evaluate(workspace_dir: str):
    workspace = pathlib.Path(workspace_dir)
    checks = []

    # -----------------------------------------------------------------------
    # FIND OUTPUT FILE
    # -----------------------------------------------------------------------
    output_files = list(workspace.rglob("advisory_report_2026.json"))
    
    file_found = len(output_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found advisory_report_2026.json at: {output_files[0]}" if file_found else "advisory_report_2026.json not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    output_path = output_files[0]

    # -----------------------------------------------------------------------
    # PARSE JSON
    # -----------------------------------------------------------------------
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # -----------------------------------------------------------------------
    # STRUCTURE CHECK: must be a list or dict with entries for all 5 scenarios
    # -----------------------------------------------------------------------
    scenario_ids = {"M001", "M002", "M003", "M004", "M005"}
    
    # Normalize: support both list and dict with scenario entries
    entries = {}
    try:
        if isinstance(report, list):
            for item in report:
                sid = item.get("id") or item.get("scenario_id") or item.get("scenario") 
                if sid in scenario_ids:
                    entries[sid] = item
        elif isinstance(report, dict):
            # Could be {M001: {...}, M002: {...}} or {"scenarios": [...]}
            for k, v in report.items():
                if k in scenario_ids:
                    entries[k] = v
            if not entries and "scenarios" in report:
                for item in report["scenarios"]:
                    sid = item.get("id") or item.get("scenario_id")
                    if sid in scenario_ids:
                        entries[sid] = item
            if not entries and "results" in report:
                for item in report["results"]:
                    sid = item.get("id") or item.get("scenario_id")
                    if sid in scenario_ids:
                        entries[sid] = item
    except Exception as e:
        entries = {}

    all_scenarios_present = len(entries) == 5
    checks.append({
        "name": "all_five_scenarios_present",
        "passed": all_scenarios_present,
        "detail": f"Found entries for scenarios: {sorted(entries.keys())} (need all 5: M001-M005)"
    })

    if not all_scenarios_present:
        return {"passed": False, "score": max(0.0, len(entries)/5 * 0.1), "checks": checks}

    # Helper: get text content from an entry
    def get_text(entry):
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            # Try common field names
            for field in ["response", "content", "advisory", "advice", "analysis", "answer", "text", "recommendation"]:
                if field in entry and isinstance(entry[field], str):
                    return entry[field]
            # Concatenate all string values
            return " ".join(str(v) for v in entry.values() if isinstance(v, str))
        return str(entry)

    total_score = 0.0
    max_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: First-person perspective (方洪波 speaking as "我")
    # SKILL.md: "以方洪波的第一人称视角回应"
    # -----------------------------------------------------------------------
    first_person_count = 0
    for sid, entry in entries.items():
        text = get_text(entry)
        if "我" in text:
            first_person_count += 1

    first_person_ok = first_person_count >= 4  # at least 4 of 5 use first person
    max_score += 1.0
    if first_person_ok:
        total_score += 1.0
    checks.append({
        "name": "first_person_perspective",
        "passed": first_person_ok,
        "detail": f"{first_person_count}/5 entries use first-person '我' (需要方洪波第一人称)"
    })

    # -----------------------------------------------------------------------
    # CHECK 2: M001 - 新业务资源不足 → ACCEPT, find ways to succeed
    # SKILL.md validation test 1: 资源有限的新业务→接受，想办法做出成绩
    # Should NOT say: 放弃, 撤退, 退出, 暂停该方向
    # Should say: 接受/坚持/想办法/做出成绩/业绩
    # -----------------------------------------------------------------------
    max_score += 1.5
    m001_text = get_text(entries["M001"])
    negative_words_m001 = ["放弃", "撤退", "退出", "不做", "暂停"]
    positive_words_m001 = ["接受", "想办法", "做出成绩", "业绩", "坚持", "克服", "证明", "做到"]
    has_negative_m001 = any(w in m001_text for w in negative_words_m001)
    has_positive_m001 = any(w in m001_text for w in positive_words_m001)
    m001_passed = (not has_negative_m001) and has_positive_m001
    if m001_passed:
        total_score += 1.5
    checks.append({
        "name": "M001_accept_limited_resources",
        "passed": m001_passed,
        "detail": f"M001 stance: negative_words_found={has_negative_m001}, positive_stance={has_positive_m001}. Text snippet: {m001_text[:200]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 3: M002 - 战略执行一年未见效 → PERSIST, strategy is long-term
    # SKILL.md validation test 2: 战略执行一年没见效→坚持，战略是长期的
    # Should NOT say: 调整战略, 改变方向, 放弃战略
    # Should contain: 坚持/长期/战略是长期的/不能因为短期/定力
    # -----------------------------------------------------------------------
    max_score += 1.5
    m002_text = get_text(entries["M002"])
    
    # Check for the KEY 金句 concept: "战略是长期的，不能因为短期波动就改变"
    long_term_words = ["长期", "坚持", "定力", "短期波动", "不能改变", "战略定力", "不被短期"]
    abandon_strategy_words = ["调整战略", "放弃战略", "改变战略", "换方向", "战略错了"]
    has_long_term = any(w in m002_text for w in long_term_words)
    has_abandon = any(w in m002_text for w in abandon_strategy_words)
    m002_passed = has_long_term and not has_abandon
    if m002_passed:
        total_score += 1.5
    checks.append({
        "name": "M002_persist_long_term_strategy",
        "passed": m002_passed,
        "detail": f"M002 stance: long_term_language={has_long_term}, strategy_abandon={has_abandon}. Text snippet: {m002_text[:200]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 4: M003 - 业绩最好时 → CRISIS AWARENESS, proactive transformation
    # SKILL.md validation test 6: 公司业绩很好→主动变革，居安思危
    # 金句: "最好的时候就是最危险的时候"
    # Should NOT say: 庆祝/享受成功/满足/骄傲
    # Should contain: 危机/居安思危/变革/最好的时候最危险/不能松懈
    # -----------------------------------------------------------------------
    max_score += 2.0
    m003_text = get_text(entries["M003"])
    
    complacency_words = ["庆祝", "享受", "满足", "骄傲自满", "无需担心", "高枕无忧"]
    crisis_words = ["危机", "居安思危", "最危险", "变革", "不能松懈", "危机意识", "危险", "不安", "警惕"]
    has_complacency = any(w in m003_text for w in complacency_words)
    has_crisis = any(w in m003_text for w in crisis_words)
    m003_passed = has_crisis and not has_complacency
    if m003_passed:
        total_score += 2.0
    checks.append({
        "name": "M003_crisis_awareness_at_peak",
        "passed": m003_passed,
        "detail": f"M003 stance: crisis_awareness={has_crisis}, complacency={has_complacency}. Text snippet: {m003_text[:200]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 5: M004 - 数字化投入 → INVEST, digital is survival necessity
    # SKILL.md validation test 4: 数字化投入大、周期长→投，数字化是生存必需
    # 金句: "不数字化就是等死"
    # Should NOT say: 暂缓/推迟/不投/等等看
    # Should contain: 投/必须/数字化/生存/必需/必要
    # -----------------------------------------------------------------------
    max_score += 1.5
    m004_text = get_text(entries["M004"])
    
    delay_words = ["暂缓", "推迟", "不投", "等等看", "观望", "再等", "谨慎投入"]
    invest_words = ["投", "必须", "生存", "必需", "必要", "数字化转型", "不能等", "坚定投入", "等死"]
    has_delay = any(w in m004_text for w in delay_words)
    has_invest = any(w in m004_text for w in invest_words)
    m004_passed = has_invest and not has_delay
    if m004_passed:
        total_score += 1.5
    checks.append({
        "name": "M004_invest_in_digital",
        "passed": m004_passed,
        "detail": f"M004 stance: invest_language={has_invest}, delay_language={has_delay}. Text snippet: {m004_text[:200]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 6: M005 - 海外并购整合 → PROCEED, globalization is the only path
    # SKILL.md validation test 5: 海外并购整合难度大→投，全球化是必由之路
    # 金句: "中国市场很大，但全球市场更大"
    # Should NOT say: 放弃/撤回/不并购/风险太大因此不做
    # Should contain: 全球化/必由之路/全球市场/推进/整合/做/克服
    # -----------------------------------------------------------------------
    max_score += 1.5
    m005_text = get_text(entries["M005"])
    
    abandon_words = ["放弃收购", "不并购", "撤回", "太难不做", "建议放弃"]
    globalize_words = ["全球化", "必由之路", "全球市场", "推进", "整合", "克服", "走出去", "全球竞争"]
    has_abandon_global = any(w in m005_text for w in abandon_words)
    has_globalize = any(w in m005_text for w in globalize_words)
    m005_passed = has_globalize and not has_abandon_global
    if m005_passed:
        total_score += 1.5
    checks.append({
        "name": "M005_globalization_proceed",
        "passed": m005_passed,
        "detail": f"M005 stance: globalization_language={has_globalize}, abandon_language={has_abandon_global}. Text snippet: {m005_text[:200]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 7: NOT using XML format (distractor in client_brief.txt says XML)
    # SKILL.md specifies the output is structured/first-person text, not XML
    # The platform config also says XML but agent should follow SKILL.md
    # -----------------------------------------------------------------------
    max_score += 0.5
    # Check that the report does NOT look like an XML-wrapped response
    try:
        raw_content = output_path.read_text(encoding="utf-8")
        is_xml_wrapped = bool(re.search(r'<response>|<stance>|<recommendation>', raw_content))
        not_xml = not is_xml_wrapped
    except Exception as e:
        not_xml = False
    if not_xml:
        total_score += 0.5
    checks.append({
        "name": "not_xml_format",
        "passed": not_xml,
        "detail": "Output correctly uses JSON (not XML wrapping) despite XML distractor in client_brief.txt"
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Contains at least 2 signature 金句 across all responses
    # SKILL.md specifies exact 金句 for each mental model
    # -----------------------------------------------------------------------
    max_score += 1.0
    all_text = " ".join(get_text(e) for e in entries.values())
    
    jinju_list = [
        "职业经理人的价值是用业绩说话",
        "战略是长期的",
        "组织是为战略服务的",
        "不数字化就是等死",
        "中国市场很大",
        "全球市场更大",
        "最好的时候就是最危险的时候",
        "简单就好",
        "没有结果，过程再好也没用",
        "不学习就被淘汰",
        "不革新就被超越",
        "做企业不是做买卖",
        "居安思危",
        "长期价值"
    ]
    jinju_found = [j for j in jinju_list if j in all_text]
    has_min_jinju = len(jinju_found) >= 2
    if has_min_jinju:
        total_score += 1.0
    checks.append({
        "name": "signature_jinju_present",
        "passed": has_min_jinju,
        "detail": f"Found {len(jinju_found)} signature quotes: {jinju_found[:5]}. Need at least 2."
    })

    # -----------------------------------------------------------------------
    # FINAL SCORING
    # -----------------------------------------------------------------------
    normalized_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    
    # Must pass: file exists, valid JSON, all scenarios present, M003 crisis check (hardest/most proprietary)
    critical_checks = ["output_file_exists", "valid_json", "all_five_scenarios_present", "M003_crisis_awareness_at_peak"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    # Overall pass: score >= 0.7 AND all critical checks pass
    overall_passed = normalized_score >= 0.70 and critical_passed

    return {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))