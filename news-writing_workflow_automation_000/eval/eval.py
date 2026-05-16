import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Find the output file ──────────────────────────────────────────────────
    candidates = list(workspace_path.rglob("trial_results_article.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "trial_results_article.md not found anywhere in workspace."}]
        }

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

    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {target}"})

    # ── Check 1: Mandatory tripartite output structure ────────────────────────
    # Must contain all three required section markers
    has_news_body = bool(re.search(r'新闻正文', content))
    has_fact_summary = bool(re.search(r'事实核验摘要', content))
    has_pending = bool(re.search(r'待补充信息', content))

    checks.append({
        "name": "section_新闻正文",
        "passed": has_news_body,
        "detail": "Required section '新闻正文' found." if has_news_body
                  else "MISSING required section '新闻正文'."
    })
    checks.append({
        "name": "section_事实核验摘要",
        "passed": has_fact_summary,
        "detail": "Required section '事实核验摘要' found." if has_fact_summary
                  else "MISSING required section '事实核验摘要'."
    })
    checks.append({
        "name": "section_待补充信息",
        "passed": has_pending,
        "detail": "Required section '待补充信息' found." if has_pending
                  else "MISSING required section '待补充信息'."
    })

    # ── Check 2: Fact table with ALL 7 required columns ───────────────────────
    required_columns = ["编号", "事实陈述", "来源链接/出处", "时间", "地点", "可核实状态", "备注"]
    # Look for a markdown table row containing all these headers
    table_line = None
    for line in content.splitlines():
        if "|" in line and "编号" in line:
            table_line = line
            break

    if table_line is None:
        checks.append({
            "name": "fact_table_exists",
            "passed": False,
            "detail": "No Markdown table with '编号' header found. Fact table is missing."
        })
        checks.append({
            "name": "fact_table_all_7_columns",
            "passed": False,
            "detail": "Cannot check columns because table is missing."
        })
    else:
        checks.append({
            "name": "fact_table_exists",
            "passed": True,
            "detail": f"Fact table found: {table_line[:80]}"
        })
        missing_cols = [col for col in required_columns if col not in table_line]
        all_cols_present = len(missing_cols) == 0
        checks.append({
            "name": "fact_table_all_7_columns",
            "passed": all_cols_present,
            "detail": (f"All 7 required columns present." if all_cols_present
                       else f"Missing columns: {missing_cols}. Table header: {table_line[:120]}")
        })

    # ── Check 3: 标题 exists and is result-oriented (no piled adjectives) ─────
    # Title should be a heading (# or ## level) containing SAB-2201 or SOLAR-3 or key facts
    title_match = re.search(r'^#{1,2}\s+(.+)', content, re.MULTILINE)
    has_title = title_match is not None
    checks.append({
        "name": "title_exists",
        "passed": has_title,
        "detail": (f"Title found: '{title_match.group(1)[:80]}'" if has_title
                   else "No H1/H2 title found in content.")
    })

    # Check title doesn't pile empty adjectives (common patterns)
    if has_title:
        title_text = title_match.group(1)
        bad_adj_patterns = [r'卓越', r'辉煌', r'伟大', r'震撼', r'惊人', r'完美', r'无与伦比', r'史无前例的成功']
        bad_found = [p for p in bad_adj_patterns if re.search(p, title_text)]
        title_clean = len(bad_found) == 0
        checks.append({
            "name": "title_no_piled_adjectives",
            "passed": title_clean,
            "detail": (f"Title is result-oriented, no banned adjectives." if title_clean
                       else f"Title contains banned adjective patterns: {bad_found}")
        })
    else:
        checks.append({
            "name": "title_no_piled_adjectives",
            "passed": False,
            "detail": "Cannot check adjectives, title not found."
        })

    # ── Check 4: 导语 covers 5W elements ─────────────────────────────────────
    # The lede should contain: who (星弧/StarArc/李明远/CEO), when (2024年11月/11月14日),
    # what (SAB-2201/三期/临床/SOLAR), where (上海/中国/美国 or 多中心), impact/effect word
    # Strategy: find the paragraph immediately after the title (or after a 导语 label)
    
    # Extract lede: look for 导语 label or first paragraph of news body section
    lede_text = ""
    # Try to find labeled lede
    lede_match = re.search(r'导语[：:]\s*(.+?)(?:\n|$)', content)
    if lede_match:
        lede_text = lede_match.group(1)
    else:
        # Try first non-heading paragraph after title
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and not p.strip().startswith('#')]
        if paragraphs:
            lede_text = paragraphs[0]

    # Check 5W presence
    who_present = bool(re.search(r'星弧|StarArc|李明远|王刚|SAB-2201|SOLAR', lede_text))
    when_present = bool(re.search(r'2024|11月|今日|近日', lede_text))
    what_present = bool(re.search(r'三期|临床|试验|SOLAR|终点|PFS|ORR', lede_text))
    impact_present = bool(re.search(r'突破|达到|宣布|公布|成功|申请|降低|改善|上市', lede_text))

    fivew_score = sum([who_present, when_present, what_present, impact_present])
    lede_ok = fivew_score >= 3  # at least 3 of 4 required elements

    checks.append({
        "name": "lede_5W_coverage",
        "passed": lede_ok,
        "detail": (f"Lede covers required elements (who={who_present}, when={when_present}, "
                   f"what={what_present}, impact={impact_present}). Score: {fivew_score}/4. "
                   f"Lede text (first 150 chars): '{lede_text[:150]}'")
    })

    # ── Check 5: Key verified facts present in body ───────────────────────────
    # PFS data (11.3 months vs 5.6 months) should appear - from press release & registry
    pfs_present = bool(re.search(r'11\.3|5\.6', content))
    # HR value
    hr_present = bool(re.search(r'0\.48|HR\s*=\s*0\.48|HR为0\.48', content))
    # ORR 43.7%
    orr_present = bool(re.search(r'43\.7|43\.7%', content))
    # 847 patients
    patients_present = bool(re.search(r'847', content))

    key_facts_count = sum([pfs_present, hr_present, orr_present, patients_present])
    key_facts_ok = key_facts_count >= 3

    checks.append({
        "name": "key_verified_facts_in_body",
        "passed": key_facts_ok,
        "detail": (f"Key verified facts: PFS={pfs_present}, HR={hr_present}, "
                   f"ORR43.7%={orr_present}, 847patients={patients_present}. "
                   f"Score: {key_facts_count}/4 (need ≥3).")
    })

    # ── Check 6: Unverified claims MUST NOT appear in main body without caveat ─
    # "ORR超过50%" from social media / meeting notes informal rumor — must not appear uncaveated
    # "FDA快速通道已确定" — unverified
    # "PharmaNova PN-4400已经凉了" — unverified (only rumor)
    # "股价" financial claims from unconfirmed sources

    # Check that "50%" ORR claim is either absent or clearly marked as unverified
    orr_50_raw = bool(re.search(r'50\+?%|超过50|ORR.*50|50.*ORR', content))
    # If it appears, it must be accompanied by an "unverified" caveat nearby
    orr_50_violation = False
    if orr_50_raw:
        # Check if it's in a "待确认" section or has caveat near it
        # Find the context around the 50% mention
        match = re.search(r'.{0,100}50\+?%.{0,100}', content)
        if match:
            context = match.group()
            # Must have caveat language
            has_caveat = bool(re.search(r'待确认|未核实|尚无|传言|不能|未经证实|无法证实|存疑|匿名', context))
            orr_50_violation = not has_caveat

    checks.append({
        "name": "unverified_orr50_not_in_body_uncaveated",
        "passed": not orr_50_violation,
        "detail": ("Unverified ORR >50% claim is correctly excluded or properly caveated."
                   if not orr_50_violation
                   else "VIOLATION: Unverified ORR >50% claim appears in body without caveat (from informal meeting note / social media).")
    })

    # "FDA快速通道已确定" must not appear as confirmed fact
    fda_confirmed_violation = bool(re.search(r'FDA.*绿色通道.*确定|绿色通道.*已.*确定|FDA快速通道.*确定', content))
    checks.append({
        "name": "unverified_fda_fasttrack_not_confirmed",
        "passed": not fda_confirmed_violation,
        "detail": ("Unverified FDA fast-track claim correctly excluded."
                   if not fda_confirmed_violation
                   else "VIOLATION: Unverified 'FDA fast-track confirmed' claim presented as fact (source: anonymous social media post).")
    })

    # ── Check 7: 待确认列表 or equivalent for unverified items ─────────────────
    # The document should have some form of unconfirmed items section
    has_pending_list = bool(re.search(r'待确认|尚无独立证实|未核实|未经证实', content))
    checks.append({
        "name": "has_unverified_items_list",
        "passed": has_pending_list,
        "detail": ("Document contains explicit unverified/pending items notation." if has_pending_list
                   else "MISSING: No '待确认' or unverified items notation found. Unverified claims must be explicitly labeled.")
    })

    # ── Check 8: 事实核验摘要 section has actual content ────────────────────────
    # Find content after 事实核验摘要 heading
    fact_summary_match = re.search(r'事实核验摘要(.+?)(?=##|$)', content, re.DOTALL)
    if fact_summary_match:
        summary_content = fact_summary_match.group(1).strip()
        summary_has_content = len(summary_content) > 30
    else:
        summary_has_content = False

    checks.append({
        "name": "fact_summary_has_content",
        "passed": summary_has_content,
        "detail": ("事实核验摘要 section has substantive content." if summary_has_content
                   else "事实核验摘要 section is empty or missing content (needs source citations and unconfirmed items).")
    })

    # ── Check 9: Inverted pyramid structure — body sections exist ─────────────
    has_background_or_context = bool(re.search(r'背景|历史|此前|此次|该公司|成立|管线', content))
    has_followup_or_cta = bool(re.search(r'后续|将于|计划|申请|公布|下一步|ASCO|2025|未来', content))

    inv_pyramid_ok = has_background_or_context and has_followup_or_cta
    checks.append({
        "name": "inverted_pyramid_structure",
        "passed": inv_pyramid_ok,
        "detail": (f"Article has background context ({has_background_or_context}) "
                   f"and follow-up/CTA section ({has_followup_or_cta}).")
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Must pass all critical checks to overall pass
    critical_checks = [
        "fact_table_exists",
        "fact_table_all_7_columns",
        "section_新闻正文",
        "section_事实核验摘要",
        "section_待补充信息",
        "lede_5W_coverage",
        "unverified_orr50_not_in_body_uncaveated",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))