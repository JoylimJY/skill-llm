import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ── Locate the output file ─────────────────────────────────────────────
    candidates = list(workspace.rglob("complaint_draft.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "complaint_draft.md not found anywhere in workspace"}]
        }

    # Use the first match (prefer shallowest)
    candidates.sort(key=lambda p: len(p.parts))
    target = candidates[0]

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False,
                        "detail": f"Could not read file: {e}"}]
        }

    # ── Check 1: Title present ─────────────────────────────────────────────
    has_title = "民事起诉状" in content
    checks.append({
        "name": "has_title_民事起诉状",
        "passed": has_title,
        "detail": "Document contains title '民事起诉状'" if has_title
                  else "Missing required title '民事起诉状'"
    })

    # ── Check 2: Plaintiff as legal entity (法人格式) ─────────────────────
    # Must include: company name, registered address, legal rep name + title, contact
    plaintiff_section = ""
    m = re.search(r"原告[：:](.*?)(?=被告[：:]|诉讼请求)", content, re.DOTALL)
    if m:
        plaintiff_section = m.group(1)

    has_company_name = "宏远电子科技（深圳）有限公司" in plaintiff_section or \
                       "宏远电子科技(深圳)有限公司" in plaintiff_section or \
                       "宏远电子科技" in plaintiff_section
    has_registered_address = "南山区" in plaintiff_section or "科技园" in plaintiff_section or \
                              "高新南七道" in plaintiff_section
    has_legal_rep = ("陈建国" in plaintiff_section and
                     ("总经理" in plaintiff_section or "法定代表人" in plaintiff_section))
    has_contact = "0755" in plaintiff_section or "88776655" in plaintiff_section

    plaintiff_ok = has_company_name and has_registered_address and has_legal_rep
    checks.append({
        "name": "plaintiff_legal_entity_format",
        "passed": plaintiff_ok,
        "detail": (
            f"Plaintiff (法人) info check — company_name:{has_company_name}, "
            f"address:{has_registered_address}, legal_rep:{has_legal_rep}, "
            f"contact:{has_contact}"
        )
    })

    # ── Check 3: Defendant as legal entity ────────────────────────────────
    defendant_section = ""
    m2 = re.search(r"被告[：:](.*?)(?=诉讼请求|事实与理由)", content, re.DOTALL)
    if m2:
        defendant_section = m2.group(1)

    has_defendant_name = "上海顺达物流科技有限公司" in defendant_section or \
                         "顺达物流" in defendant_section
    has_defendant_addr = "浦东" in defendant_section or "张江" in defendant_section or \
                         "科苑路" in defendant_section or "上海" in defendant_section
    has_defendant_rep = "郭伟" in defendant_section

    defendant_ok = has_defendant_name and has_defendant_addr and has_defendant_rep
    checks.append({
        "name": "defendant_legal_entity_format",
        "passed": defendant_ok,
        "detail": (
            f"Defendant info — name:{has_defendant_name}, "
            f"address:{has_defendant_addr}, legal_rep(郭伟):{has_defendant_rep}"
        )
    })

    # ── Check 4: Claims use Chinese numeral ordering 一、二、三 ──────────
    has_yi = bool(re.search(r"一[、，,：:]", content))
    has_er = bool(re.search(r"二[、，,：:]", content))
    has_san = bool(re.search(r"三[、，,：:]", content))
    has_numeral_order = has_yi and has_er and has_san
    checks.append({
        "name": "claims_use_chinese_numeral_ordering",
        "passed": has_numeral_order,
        "detail": f"Chinese numeral ordering 一/二/三 present: {has_yi}/{has_er}/{has_san}"
    })

    # ── Check 5: Key claim amounts ─────────────────────────────────────────
    has_damage_amount = "252,000" in content or "252000" in content or "二十五万二千" in content
    has_penalty_amount = "2,136" in content or "2136" in content
    # LPR interest claim
    has_interest = ("利率" in content or "LPR" in content or "贷款市场报价" in content) and \
                   ("2024年1月5日" in content or "2024.1.5" in content)

    claims_ok = has_damage_amount and has_penalty_amount
    checks.append({
        "name": "claims_contain_correct_amounts",
        "passed": claims_ok,
        "detail": (
            f"Damage 252000:{has_damage_amount}, "
            f"penalty 2136:{has_penalty_amount}, "
            f"interest clause:{has_interest}"
        )
    })

    # ── Check 6: Litigation cost clause as last numbered item ─────────────
    has_litigation_cost = "诉讼费" in content and (
        "由被告承担" in content or "被告负担" in content
    )
    checks.append({
        "name": "litigation_cost_clause_present",
        "passed": has_litigation_cost,
        "detail": "Contains '诉讼费...由被告承担' clause" if has_litigation_cost
                  else "Missing '诉讼费用由被告承担' clause"
    })

    # ── Check 7: Facts section exists with key facts ──────────────────────
    has_facts_section = "事实与理由" in content
    # Key facts that must appear
    has_contract_date = "2023年11月" in content or "SHD-2023-1127" in content
    has_delivery_delay = ("2023年12月8" in content or "12月8号" in content or
                          "延误" in content or "逾期" in content)
    has_damage_cause = "装卸" in content or "货损" in content or "损坏" in content
    has_lawyer_letter = ("律师函" in content and
                         ("2024年1月5日" in content or "2024年3月10日" in content))

    facts_ok = has_facts_section and has_contract_date and has_delivery_delay
    checks.append({
        "name": "facts_section_complete",
        "passed": facts_ok,
        "detail": (
            f"facts_section:{has_facts_section}, contract_ref:{has_contract_date}, "
            f"delivery_delay:{has_delivery_delay}, damage_cause:{has_damage_cause}, "
            f"lawyer_letter:{has_lawyer_letter}"
        )
    })

    # ── Check 8: Evidence table with pipe-delimited format ─────────────────
    # Template requires: 序号 | 证据名称 | 证据来源 | 页数 | 证明目的
    has_evidence_table_header = bool(
        re.search(r"序号\s*[|｜]\s*证据名称\s*[|｜]\s*证据来源\s*[|｜]\s*页数\s*[|｜]\s*证明目的", content)
    )
    # Count evidence rows (lines with pipe separators containing content)
    evidence_rows = re.findall(r"^\s*\d+\s*[|｜].*[|｜].*[|｜].*[|｜]", content, re.MULTILINE)
    has_enough_evidence = len(evidence_rows) >= 5  # Chat log mentions 6 pieces of evidence

    # Key evidence items
    has_contract_evidence = "货运合同" in content or "运输合同" in content
    has_inspection_report = "鉴定报告" in content or "质量检测" in content
    has_bank_transfer = "转账" in content and ("银行" in content or "运费" in content)

    evidence_table_ok = has_evidence_table_header and has_enough_evidence
    checks.append({
        "name": "evidence_table_pipe_format_and_completeness",
        "passed": evidence_table_ok,
        "detail": (
            f"Pipe-delimited header:{has_evidence_table_header}, "
            f"row_count:{len(evidence_rows)} (need>=5), "
            f"contract:{has_contract_evidence}, inspection:{has_inspection_report}, "
            f"bank_transfer:{has_bank_transfer}"
        )
    })

    # ── Check 9: Court name correct (深圳市南山区人民法院) ─────────────────
    has_correct_court = "深圳市南山区人民法院" in content
    has_此致 = "此致" in content
    court_ok = has_correct_court and has_此致
    checks.append({
        "name": "correct_court_and_此致_closing",
        "passed": court_ok,
        "detail": (
            f"Court '深圳市南山区人民法院':{has_correct_court}, "
            f"'此致' present:{has_此致}"
        )
    })

    # ── Check 10: Closing — legal entity format (company + legal rep + 公章) ─
    # For a legal entity plaintiff, closing must name company as 具状人
    # and note legal representative signature + company seal
    closing_section = content[content.rfind("此致"):] if "此致" in content else content[-500:]

    has_guzhuren_company = (
        "宏远电子科技" in closing_section or "具状人" in closing_section
    )
    has_legal_rep_in_closing = "陈建国" in closing_section or "法定代表人" in closing_section
    # Check for seal/stamp notation
    has_seal_notation = "公章" in closing_section or "盖章" in closing_section or \
                        "（盖章）" in closing_section or "(盖章)" in closing_section

    closing_ok = has_guzhuren_company and has_legal_rep_in_closing
    checks.append({
        "name": "closing_legal_entity_format",
        "passed": closing_ok,
        "detail": (
            f"Company as 具状人:{has_guzhuren_company}, "
            f"legal_rep in closing:{has_legal_rep_in_closing}, "
            f"seal notation:{has_seal_notation}"
        )
    })

    # ── Compute overall score ──────────────────────────────────────────────
    weights = {
        "has_title_民事起诉状": 0.05,
        "plaintiff_legal_entity_format": 0.15,
        "defendant_legal_entity_format": 0.10,
        "claims_use_chinese_numeral_ordering": 0.08,
        "claims_contain_correct_amounts": 0.12,
        "litigation_cost_clause_present": 0.07,
        "facts_section_complete": 0.13,
        "evidence_table_pipe_format_and_completeness": 0.15,
        "correct_court_and_此致_closing": 0.08,
        "closing_legal_entity_format": 0.07,
    }

    score = sum(weights[c["name"]] for c in checks if c["passed"])
    passed = score >= 0.75  # Must pass at least 75% weighted score

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))