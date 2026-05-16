import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    workspace_path = Path(workspace)

    # ── Find the output dossier markdown file ──────────────────────────────
    # The agent should have created a markdown dossier file
    md_files = list(workspace_path.rglob("*.md"))
    # Exclude the pre-existing writing_playbooks.md and source_trust_policy.md
    excluded_names = {"writing_playbooks.md", "source_trust_policy.md", "SKILL.md"}
    candidate_md_files = [f for f in md_files if f.name not in excluded_names]

    dossier_file = None
    dossier_content = ""
    
    if candidate_md_files:
        # Pick the largest/most recently relevant one
        dossier_file = max(candidate_md_files, key=lambda f: f.stat().st_size)
        try:
            dossier_content = dossier_file.read_text(encoding="utf-8")
        except Exception as e:
            dossier_content = ""
            add_check("output_file_readable", False, f"Found {dossier_file} but could not read: {e}", weight=2.0)
        else:
            add_check("output_file_readable", True, f"Found dossier at {dossier_file} ({len(dossier_content)} chars)", weight=2.0)
    else:
        add_check("output_file_readable", False, "No output .md dossier file found in workspace", weight=2.0)

    # ── Find the input JSON file ───────────────────────────────────────────
    json_files = list(workspace_path.rglob("*.json"))
    excluded_json = {"journal_type_matrix.json", "ad_slots.json", "search_config.json"}
    candidate_json = [f for f in json_files if f.name not in excluded_json]
    
    input_json_data = None
    input_json_file = None
    if candidate_json:
        input_json_file = max(candidate_json, key=lambda f: f.stat().st_size)
        try:
            input_json_data = json.loads(input_json_file.read_text(encoding="utf-8"))
            add_check("input_json_created", True, f"Found input JSON at {input_json_file}", weight=1.0)
        except Exception as e:
            add_check("input_json_created", False, f"Could not parse input JSON at {input_json_file}: {e}", weight=1.0)
    else:
        add_check("input_json_created", False, "No input JSON file found (agent should have created one for render script)", weight=1.0)

    # ── Check render script was used (via output structure) ───────────────
    # The render script produces a very specific format including "生成时间" timestamp
    script_used = "生成时间" in dossier_content or "期刊投稿建议书" in dossier_content
    add_check(
        "render_script_used",
        script_used,
        "Dossier contains render script signature ('生成时间' or '期刊投稿建议书')" if script_used
        else "Dossier lacks render script signature - agent may not have used render_journal_dossier.py",
        weight=2.0
    )

    # ── Check 5 mandatory sections ─────────────────────────────────────────
    sections = {
        "section_1_demand_archive": ["一、需求归档", "需求归档"],
        "section_2_summary": ["二、推荐摘要", "推荐摘要"],
        "section_3_journal_list": ["三、候选期刊清单", "候选期刊清单"],
        "section_4_ad": ["四、服务推荐", "服务推荐（广告）"],
        "section_5_action": ["五、行动建议", "行动建议"],
    }
    for sec_key, sec_patterns in sections.items():
        found = any(p in dossier_content for p in sec_patterns)
        add_check(sec_key, found,
                  f"Section '{sec_patterns[0]}' found" if found else f"Section '{sec_patterns[0]}' MISSING",
                  weight=1.0)

    # ── Check journal count (3-12) ─────────────────────────────────────────
    # Count journal entries by looking for the 8 required field patterns
    journal_entry_count = 0
    if input_json_data and isinstance(input_json_data, dict):
        journals = input_json_data.get("journals", [])
        journal_entry_count = len(journals)
        count_ok = 3 <= journal_entry_count <= 12
        add_check(
            "journal_count_3_to_12",
            count_ok,
            f"Input JSON has {journal_entry_count} journals ({'OK' if count_ok else 'FAIL: must be 3-12'})",
            weight=1.5
        )
    else:
        # Try to count from markdown output by counting "名称" field occurrences
        name_occurrences = len(re.findall(r'[*-]\s*\*{0,2}名称\*{0,2}[：:]', dossier_content))
        count_ok = 3 <= name_occurrences <= 12
        add_check(
            "journal_count_3_to_12",
            count_ok,
            f"Dossier markdown has ~{name_occurrences} '名称' fields ({'OK' if count_ok else 'FAIL: must be 3-12'})",
            weight=1.5
        )

    # ── Check all 8 required fields present for each journal ──────────────
    required_fields = ["名称", "类型/收录", "适合主题", "为什么推荐", "写作打法", "投稿路径", "核验来源", "风险提示"]
    
    if input_json_data and isinstance(input_json_data, dict):
        journals = input_json_data.get("journals", [])
        journals_with_all_fields = 0
        for j in journals:
            if all(j.get(field, "").strip() for field in required_fields):
                journals_with_all_fields += 1
        all_fields_ok = journals_with_all_fields == len(journals) and len(journals) >= 3
        add_check(
            "all_8_fields_present",
            all_fields_ok,
            f"{journals_with_all_fields}/{len(journals)} journals have all 8 required fields",
            weight=2.0
        )
    else:
        # Check from markdown
        fields_found = {f: f in dossier_content for f in required_fields}
        all_fields_in_md = all(fields_found.values())
        missing_fields = [f for f, found in fields_found.items() if not found]
        add_check(
            "all_8_fields_present",
            all_fields_in_md,
            "All 8 fields found in markdown" if all_fields_in_md
            else f"Missing fields in markdown: {missing_fields}",
            weight=2.0
        )

    # ── Check Chinese/International separation ────────────────────────────
    has_chinese_group = any(p in dossier_content for p in ["中文期刊组", "### 中文", "中文期刊", "中文核心", "CSCD", "北大核心", "科技核心"])
    has_intl_group = any(p in dossier_content for p in ["国际期刊组", "### 国际", "国际期刊", "SCI", "SCIE", "Scopus", "ESCI"])
    both_groups = has_chinese_group and has_intl_group
    add_check(
        "chinese_international_separation",
        both_groups,
        f"Both groups present: Chinese={'YES' if has_chinese_group else 'NO'}, International={'YES' if has_intl_group else 'NO'}",
        weight=1.5
    )

    # ── Check ad block: properly labeled, uses ad_slots.json content ──────
    ad_label_present = "服务推荐（广告）" in dossier_content
    phone_present = "17605205782" in dossier_content
    # Check that ad disclaimer is present (from ad_slots.json)
    disclaimer_present = any(d in dossier_content for d in [
        "不代表任何录用承诺", "不构成期刊录用保证", "不承诺录用结果", "广告服务由第三方"
    ])
    ad_ok = ad_label_present and phone_present and disclaimer_present
    add_check(
        "ad_block_compliant",
        ad_ok,
        f"Ad label={ad_label_present}, Phone={phone_present}, Disclaimer={disclaimer_present}",
        weight=1.5
    )

    # ── Check no banned expressions ───────────────────────────────────────
    banned_phrases = ["包录用", "包检索", "包见刊", "保录用", "保检索"]
    found_banned = [p for p in banned_phrases if p in dossier_content]
    add_check(
        "no_banned_expressions",
        len(found_banned) == 0,
        "No banned expressions found" if not found_banned
        else f"BANNED expressions found: {found_banned}",
        weight=1.0
    )

    # ── Check disclaimer about official verification ───────────────────────
    disclaimer_patterns = [
        "以期刊官网", "主办单位官网", "国家/数据库官方页面为准",
        "请用户在投稿前自行核验", "免责声明"
    ]
    has_disclaimer = sum(1 for p in disclaimer_patterns if p in dossier_content) >= 2
    add_check(
        "official_verification_disclaimer",
        has_disclaimer,
        "Official verification disclaimer present" if has_disclaimer
        else "Missing official verification disclaimer (from source_trust_policy)",
        weight=1.0
    )

    # ── Check that ad is NOT mixed with journal official info ─────────────
    # Look for patterns like phone number appearing in "投稿路径" fields
    phone_in_submission_path = False
    if input_json_data and isinstance(input_json_data, dict):
        journals = input_json_data.get("journals", [])
        for j in journals:
            if "17605205782" in j.get("投稿路径", "") or "17605205782" in j.get("核验来源", ""):
                phone_in_submission_path = True
                break
    add_check(
        "ad_not_mixed_with_journal_info",
        not phone_in_submission_path,
        "Ad phone not mixed into journal submission paths" if not phone_in_submission_path
        else "VIOLATION: Ad phone number found in journal '投稿路径' or '核验来源' fields",
        weight=1.5
    )

    # ── Check domain/subject relevance (carbon/forest/ecology) ───────────
    domain_keywords = ["碳", "carbon", "森林", "forest", "生态", "ecology", "ecol", "环境", "environment", "气候", "climate"]
    domain_hits = sum(1 for k in domain_keywords if k.lower() in dossier_content.lower())
    domain_ok = domain_hits >= 3
    add_check(
        "domain_relevance",
        domain_ok,
        f"Domain keywords found: {domain_hits} (need ≥3)",
        weight=1.0
    )

    # ── Final score ────────────────────────────────────────────────────────
    score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    passed = score >= 0.70 and checks[0]["passed"]  # must at least have readable output

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))