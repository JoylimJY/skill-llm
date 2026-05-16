import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # Find the output file
    candidates = list(workspace.rglob("competitive_briefing.md"))
    file_found = len(candidates) > 0

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named competitive_briefing.md" if file_found else "competitive_briefing.md not found anywhere in workspace"
    })

    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = candidates[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # ── CHECK 1: 结论摘要 section exists ──
    jieLun_match = re.search(r'##\s*结论摘要', content)
    checks.append({
        "name": "section_结论摘要_exists",
        "passed": bool(jieLun_match),
        "detail": "Found '## 结论摘要' section" if jieLun_match else "Missing '## 结论摘要' section"
    })

    # ── CHECK 2: 结论摘要 ≤ 120 Chinese characters ──
    jl_passed = False
    jl_detail = "Could not extract 结论摘要 content"
    if jieLun_match:
        try:
            after_header = content[jieLun_match.end():]
            # Extract text until the next ## section
            next_section = re.search(r'\n##\s', after_header)
            jl_text = after_header[:next_section.start()].strip() if next_section else after_header.strip()
            # Count Chinese characters (CJK Unified Ideographs range)
            chinese_chars = re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', jl_text)
            count = len(chinese_chars)
            jl_passed = count <= 120 and count > 0
            jl_detail = f"结论摘要 contains {count} Chinese characters (limit: 120)"
        except Exception as e:
            jl_detail = f"Error counting chars: {e}"
    checks.append({
        "name": "结论摘要_le_120_chars",
        "passed": jl_passed,
        "detail": jl_detail
    })

    # ── CHECK 3: 关键要点 section exists with bullets ──
    yaoD_match = re.search(r'##\s*关键要点', content)
    yaoD_passed = False
    yaoD_detail = "Missing '## 关键要点' section"
    if yaoD_match:
        after_yd = content[yaoD_match.end():]
        next_s = re.search(r'\n##\s', after_yd)
        yd_block = after_yd[:next_s.start()].strip() if next_s else after_yd.strip()
        bullets = re.findall(r'^\s*[-*]\s+.+', yd_block, re.MULTILINE)
        yaoD_passed = len(bullets) >= 3
        yaoD_detail = f"Found {len(bullets)} bullet(s) in 关键要点 (need ≥3)"
    checks.append({
        "name": "section_关键要点_with_bullets",
        "passed": yaoD_passed,
        "detail": yaoD_detail
    })

    # ── CHECK 4: Every bullet in 关键要点 has at least one markdown link ──
    md_links_in_bullets = False
    md_links_detail = "Could not check markdown links in 关键要点"
    if yaoD_match:
        try:
            after_yd = content[yaoD_match.end():]
            next_s = re.search(r'\n##\s', after_yd)
            yd_block = after_yd[:next_s.start()].strip() if next_s else after_yd.strip()
            bullets = re.findall(r'^\s*[-*]\s+.+', yd_block, re.MULTILINE)
            bullets_with_links = [b for b in bullets if re.search(r'\[.+?\]\(https?://[^\)]+\)', b)]
            # Allow bare URLs as fallback only if NO markdown links anywhere (fail case)
            bare_urls_in_bullets = [b for b in bullets if re.search(r'https?://\S+', b) and not re.search(r'\[.+?\]\(https?://[^\)]+\)', b)]
            all_have_md_links = len(bullets_with_links) == len(bullets) and len(bullets) > 0
            md_links_in_bullets = all_have_md_links
            md_links_detail = (
                f"{len(bullets_with_links)}/{len(bullets)} bullets have markdown links; "
                f"{len(bare_urls_in_bullets)} have bare URLs only"
            )
        except Exception as e:
            md_links_detail = f"Error: {e}"
    checks.append({
        "name": "关键要点_bullets_have_markdown_links",
        "passed": md_links_in_bullets,
        "detail": md_links_detail
    })

    # ── CHECK 5: No bare URLs (https://... not inside a markdown link) in the whole document ──
    bare_url_pattern = r'(?<!\()(https?://[^\s\)\]]+)(?!\))'
    bare_urls = re.findall(bare_url_pattern, content)
    no_bare_urls = len(bare_urls) == 0
    checks.append({
        "name": "no_bare_urls",
        "passed": no_bare_urls,
        "detail": f"Found {len(bare_urls)} bare URL(s)" + (f": {bare_urls[:3]}" if bare_urls else "")
    })

    # ── CHECK 6: 详情 section exists ──
    details_match = re.search(r'##\s*详情', content)
    checks.append({
        "name": "section_详情_exists",
        "passed": bool(details_match),
        "detail": "Found '## 详情' section" if details_match else "Missing '## 详情' section"
    })

    # ── CHECK 7: 来源清单 section exists with ≥3 entries ──
    sources_match = re.search(r'##\s*来源清单', content)
    sources_passed = False
    sources_detail = "Missing '## 来源清单' section"
    if sources_match:
        after_src = content[sources_match.end():]
        next_s = re.search(r'\n##\s', after_src)
        src_block = after_src[:next_s.start()].strip() if next_s else after_src.strip()
        # Look for numbered list entries
        src_entries = re.findall(r'^\s*\d+\.\s+.+', src_block, re.MULTILINE)
        sources_passed = len(src_entries) >= 3
        sources_detail = f"Found {len(src_entries)} source entry/entries in 来源清单 (need ≥3)"
    checks.append({
        "name": "section_来源清单_with_entries",
        "passed": sources_passed,
        "detail": sources_detail
    })

    # ── CHECK 8: 来源清单 entries include YYYY-MM-DD date format ──
    date_in_sources = False
    date_detail = "Could not verify dates in 来源清单"
    if sources_match:
        try:
            after_src = content[sources_match.end():]
            next_s = re.search(r'\n##\s', after_src)
            src_block = after_src[:next_s.start()].strip() if next_s else after_src.strip()
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', src_block)
            date_in_sources = len(dates) >= 2
            date_detail = f"Found {len(dates)} YYYY-MM-DD date(s) in 来源清单"
        except Exception as e:
            date_detail = f"Error: {e}"
    checks.append({
        "name": "来源清单_has_dates",
        "passed": date_in_sources,
        "detail": date_detail
    })

    # ── CHECK 9: 检索说明 section with 3–8 keywords listed ──
    search_match = re.search(r'##\s*检索说明', content)
    search_passed = False
    search_detail = "Missing '## 检索说明' section"
    if search_match:
        after_s = content[search_match.end():]
        next_s = re.search(r'\n##\s', after_s)
        s_block = after_s[:next_s.start()].strip() if next_s else after_s.strip()
        # Look for 检索关键词 line
        kw_match = re.search(r'检索关键词[：:]\s*(.+)', s_block)
        if kw_match:
            kw_line = kw_match.group(1)
            # Count comma/slash/semicolon-separated terms or bullet sub-items
            # Also accept multi-line keyword listings
            # Count items separated by common delimiters
            kw_items = re.split(r'[,，；;/\n•\-]+', kw_line)
            kw_items = [k.strip() for k in kw_items if k.strip() and len(k.strip()) >= 2]
            # Also count bullets after the keyword header line
            bullets_kw = re.findall(r'^\s*[-•]\s+\S.+', s_block, re.MULTILINE)
            total_kw = max(len(kw_items), len(bullets_kw))
            search_passed = 3 <= total_kw <= 8
            search_detail = f"Found ~{total_kw} keyword(s) in 检索关键词 (need 3–8)"
        else:
            search_detail = "检索说明 found but 检索关键词 sub-field missing"
    checks.append({
        "name": "检索说明_has_3_to_8_keywords",
        "passed": search_passed,
        "detail": search_detail
    })

    # ── CHECK 10: 影响评估 or 分析/判断/推测 labeling present ──
    speculation_label = bool(re.search(r'(分析|判断|推测|推演)', content))
    checks.append({
        "name": "analysis_labeled_as_judgment",
        "passed": speculation_label,
        "detail": "Found speculation/judgment label (分析/判断/推测)" if speculation_label else "No 分析/判断/推测 labels found — analysis not properly flagged"
    })

    # ── CHECK 11: Content covers both China and EU (dual-region scope) ──
    has_china = bool(re.search(r'(中国|工信部|MIIT|国内|北京|上海|自动驾驶.*中|中.*自动驾驶)', content))
    has_eu = bool(re.search(r'(欧盟|EU|European|Europe|欧洲|委员会|Commission)', content))
    dual_region = has_china and has_eu
    checks.append({
        "name": "dual_region_coverage_china_and_eu",
        "passed": dual_region,
        "detail": f"China coverage: {has_china}, EU coverage: {has_eu}"
    })

    # ── CHECK 12: Single-source claims labeled if present (heuristic: 单一来源 appears if needed) ──
    # We check: if there is any claim mentioning only one source, it uses 单一来源 label
    # This is a soft check: just verify the agent is aware of the concept
    single_source_label = bool(re.search(r'单一来源|single.source|仅见.*来源|只有.*来源|仅一.*来源', content, re.IGNORECASE))
    # This check is optional/bonus — we don't fail for its absence but reward its presence
    checks.append({
        "name": "single_source_labeling_awareness",
        "passed": True,  # Not a hard fail, but noted
        "detail": f"单一来源 label present: {single_source_label} (bonus check, not required to fail)"
    })

    # ── Scoring ──
    hard_checks = [
        "output_file_exists",
        "file_readable",
        "section_结论摘要_exists",
        "结论摘要_le_120_chars",
        "section_关键要点_with_bullets",
        "关键要点_bullets_have_markdown_links",
        "no_bare_urls",
        "section_详情_exists",
        "section_来源清单_with_entries",
        "来源清单_has_dates",
        "检索说明_has_3_to_8_keywords",
        "analysis_labeled_as_judgment",
        "dual_region_coverage_china_and_eu",
    ]
    
    hard_results = {c["name"]: c["passed"] for c in checks}
    hard_passed_count = sum(1 for name in hard_checks if hard_results.get(name, False))
    score = round(hard_passed_count / len(hard_checks), 4)
    overall_passed = hard_passed_count >= 11  # Must pass at least 11/13 hard checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))