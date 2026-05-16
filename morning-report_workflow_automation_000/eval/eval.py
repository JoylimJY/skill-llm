import sys
import json
import re
from pathlib import Path

def load_report(workspace: Path):
    candidates = list(workspace.rglob("morning_report.md"))
    if not candidates:
        return None, "morning_report.md not found anywhere in workspace"
    # Prefer root-level
    root_candidate = workspace / "morning_report.md"
    if root_candidate.exists():
        return root_candidate.read_text(encoding="utf-8"), str(root_candidate)
    return candidates[0].read_text(encoding="utf-8"), str(candidates[0])


def run_checks(content: str, workspace: Path):
    checks = []

    # ── CHECK 1: File header format ─────────────────────────────────────────
    try:
        header_pattern = r'📰\s+\*\*每日晨报\*\*\s*\|\s*2025-07-14\s+星期一'
        passed = bool(re.search(header_pattern, content))
        checks.append({
            "name": "header_format",
            "passed": passed,
            "detail": "Header must match: 📰 **每日晨报** | 2025-07-14 星期一" if not passed
                      else "Header format correct"
        })
    except Exception as e:
        checks.append({"name": "header_format", "passed": False, "detail": str(e)})

    # ── CHECK 2: All 6 sections present ─────────────────────────────────────
    try:
        required_sections = [
            "一、AI与游戏行业前沿资讯",
            "二、竞品监控",
            "三、竞品舆情",
            "四、SLG新品测试",
            "五、STEAM新游与新玩法",
            "六、参考数据",
        ]
        missing = [s for s in required_sections if s not in content]
        passed = len(missing) == 0
        checks.append({
            "name": "all_six_sections_present",
            "passed": passed,
            "detail": f"Missing sections: {missing}" if missing else "All 6 sections found"
        })
    except Exception as e:
        checks.append({"name": "all_six_sections_present", "passed": False, "detail": str(e)})

    # ── CHECK 3: No forbidden HTML tags ─────────────────────────────────────
    try:
        html_pattern = r'<(br|b|i|strong|em|p|div|span|html|body)[^>]*>'
        matches = re.findall(html_pattern, content, re.IGNORECASE)
        passed = len(matches) == 0
        checks.append({
            "name": "no_html_tags",
            "passed": passed,
            "detail": f"Found forbidden HTML tags: {matches}" if matches else "No forbidden HTML tags"
        })
    except Exception as e:
        checks.append({"name": "no_html_tags", "passed": False, "detail": str(e)})

    # ── CHECK 4: No strikethrough syntax ────────────────────────────────────
    try:
        strikethrough = re.findall(r'~~[^~]+~~', content)
        passed = len(strikethrough) == 0
        checks.append({
            "name": "no_strikethrough",
            "passed": passed,
            "detail": f"Found strikethrough: {strikethrough}" if strikethrough else "No strikethrough syntax"
        })
    except Exception as e:
        checks.append({"name": "no_strikethrough", "passed": False, "detail": str(e)})

    # ── CHECK 5: No task list syntax ────────────────────────────────────────
    try:
        task_list = re.findall(r'- \[[ xX]\]', content)
        passed = len(task_list) == 0
        checks.append({
            "name": "no_task_list_syntax",
            "passed": passed,
            "detail": f"Found task list syntax: {task_list}" if task_list else "No task list syntax"
        })
    except Exception as e:
        checks.append({"name": "no_task_list_syntax", "passed": False, "detail": str(e)})

    # ── CHECK 6: No footnotes ────────────────────────────────────────────────
    try:
        footnotes = re.findall(r'\[\^[^\]]+\]', content)
        passed = len(footnotes) == 0
        checks.append({
            "name": "no_footnotes",
            "passed": passed,
            "detail": f"Found footnotes: {footnotes}" if footnotes else "No footnote syntax"
        })
    except Exception as e:
        checks.append({"name": "no_footnotes", "passed": False, "detail": str(e)})

    # ── CHECK 7: Tables have blank lines before and after ────────────────────
    try:
        # Find all table blocks: lines starting with |
        lines = content.split('\n')
        table_violations = []
        i = 0
        in_table = False
        table_start = -1
        for i, line in enumerate(lines):
            is_table_line = line.strip().startswith('|')
            if is_table_line and not in_table:
                in_table = True
                table_start = i
                # Check line before: must be blank (or beginning of file)
                if table_start > 0 and lines[table_start - 1].strip() != '':
                    table_violations.append(f"Table at line {table_start+1} missing blank line before it (prev: '{lines[table_start-1]}')")
            elif not is_table_line and in_table:
                # Table just ended at i-1
                table_end = i - 1
                in_table = False
                # Check line after: must be blank (or end of file)
                if i < len(lines) and lines[i].strip() != '':
                    table_violations.append(f"Table ending at line {table_end+1} missing blank line after it (next: '{lines[i]}')")
        # Handle table at end of file
        if in_table:
            pass  # end of file is acceptable

        passed = len(table_violations) == 0
        checks.append({
            "name": "tables_surrounded_by_blank_lines",
            "passed": passed,
            "detail": "; ".join(table_violations) if table_violations else "All tables properly surrounded by blank lines"
        })
    except Exception as e:
        checks.append({"name": "tables_surrounded_by_blank_lines", "passed": False, "detail": str(e)})

    # ── CHECK 8: All 4 competitor products in section 2 ─────────────────────
    try:
        required_products = [
            "Last War: Survival",
            "Whiteout Survival",
            "Kingshot",
            "Last Z: Shooter",
        ]
        # Find section 2 content
        sec2_match = re.search(r'二、竞品监控(.*?)(?=三、竞品舆情|$)', content, re.DOTALL)
        if sec2_match:
            sec2_content = sec2_match.group(1)
            missing_products = [p for p in required_products if p not in sec2_content]
        else:
            missing_products = required_products

        passed = len(missing_products) == 0
        checks.append({
            "name": "all_4_competitors_in_section2",
            "passed": passed,
            "detail": f"Missing in section 2: {missing_products}" if missing_products
                      else "All 4 competitors listed in section 2"
        })
    except Exception as e:
        checks.append({"name": "all_4_competitors_in_section2", "passed": False, "detail": str(e)})

    # ── CHECK 9: Kingshot and Last Z marked as no updates in section 2 ───────
    try:
        sec2_match = re.search(r'二、竞品监控(.*?)(?=三、竞品舆情|$)', content, re.DOTALL)
        if sec2_match:
            sec2_content = sec2_match.group(1)
            # Check Kingshot
            kingshot_section = re.search(r'Kingshot(.*?)(?=\*\*Last Z|\*\*Whiteout|\*\*Last War|$)', sec2_content, re.DOTALL)
            lastZ_section = re.search(r'Last Z: Shooter(.*?)(?=\|产品|\| 产品|$)', sec2_content, re.DOTALL)
            
            no_update_phrase = '近期无明显变动'
            kingshot_ok = False
            if kingshot_section:
                kingshot_ok = no_update_phrase in kingshot_section.group(1)
            lastZ_ok = False
            if lastZ_section:
                lastZ_ok = no_update_phrase in lastZ_section.group(1)

            passed = kingshot_ok and lastZ_ok
            checks.append({
                "name": "no_update_products_marked_correctly",
                "passed": passed,
                "detail": f"Kingshot has '近期无明显变动': {kingshot_ok}, Last Z has '近期无明显变动': {lastZ_ok}"
            })
        else:
            checks.append({
                "name": "no_update_products_marked_correctly",
                "passed": False,
                "detail": "Could not locate section 2 content"
            })
    except Exception as e:
        checks.append({"name": "no_update_products_marked_correctly", "passed": False, "detail": str(e)})

    # ── CHECK 10: Ranking table present in section 2 ─────────────────────────
    try:
        sec2_match = re.search(r'二、竞品监控(.*?)(?=三、竞品舆情|$)', content, re.DOTALL)
        if sec2_match:
            sec2_content = sec2_match.group(1)
            has_table = '| 产品' in sec2_content or '|产品' in sec2_content or ('Last War' in sec2_content and '|' in sec2_content and 'iOS' in sec2_content)
            passed = has_table
        else:
            passed = False
        checks.append({
            "name": "ranking_table_in_section2",
            "passed": passed,
            "detail": "Ranking summary table found in section 2" if passed
                      else "No ranking table found in section 2"
        })
    except Exception as e:
        checks.append({"name": "ranking_table_in_section2", "passed": False, "detail": str(e)})

    # ── CHECK 11: Section 3 has 🌟 and ⚠️ markers ────────────────────────────
    try:
        sec3_match = re.search(r'三、竞品舆情(.*?)(?=四、SLG新品测试|$)', content, re.DOTALL)
        if sec3_match:
            sec3_content = sec3_match.group(1)
            has_star = '🌟' in sec3_content
            has_warning = '⚠️' in sec3_content
            passed = has_star and has_warning
        else:
            passed = False
        checks.append({
            "name": "sentiment_emoji_markers",
            "passed": passed,
            "detail": f"🌟 found: {has_star if sec3_match else 'N/A'}, ⚠️ found: {has_warning if sec3_match else 'N/A'}"
        })
    except Exception as e:
        checks.append({"name": "sentiment_emoji_markers", "passed": False, "detail": str(e)})

    # ── CHECK 12: Source links use [name](url) format ────────────────────────
    try:
        # There should be at least 3 proper markdown links in the document
        link_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
        links = re.findall(link_pattern, content)
        passed = len(links) >= 3
        checks.append({
            "name": "source_links_markdown_format",
            "passed": passed,
            "detail": f"Found {len(links)} proper [name](url) links (need ≥3)"
        })
    except Exception as e:
        checks.append({"name": "source_links_markdown_format", "passed": False, "detail": str(e)})

    # ── CHECK 13: Section 5 (Steam) uses fallback text ───────────────────────
    try:
        sec5_match = re.search(r'五、STEAM新游与新玩法(.*?)(?=六、参考数据|$)', content, re.DOTALL)
        if sec5_match:
            sec5_content = sec5_match.group(1)
            passed = '今日暂无相关更新' in sec5_content
        else:
            passed = False
        checks.append({
            "name": "empty_section5_uses_correct_fallback",
            "passed": passed,
            "detail": "Section 5 correctly uses '今日暂无相关更新'" if passed
                      else "Section 5 should contain '今日暂无相关更新' since no Steam data was available"
        })
    except Exception as e:
        checks.append({"name": "empty_section5_uses_correct_fallback", "passed": False, "detail": str(e)})

    # ── CHECK 14: Section 6 ad data uses "数据暂不可用" ──────────────────────
    try:
        sec6_match = re.search(r'六、参考数据(.*?)$', content, re.DOTALL)
        if sec6_match:
            sec6_content = sec6_match.group(1)
            passed = '数据暂不可用' in sec6_content
        else:
            passed = False
        checks.append({
            "name": "missing_ad_data_uses_correct_marker",
            "passed": passed,
            "detail": "Section 6 correctly uses '数据暂不可用' for unavailable ad data" if passed
                      else "Section 6 should use '数据暂不可用' for missing CPI/CPM data"
        })
    except Exception as e:
        checks.append({"name": "missing_ad_data_uses_correct_marker", "passed": False, "detail": str(e)})

    # ── CHECK 15: Message tool call block present ─────────────────────────────
    try:
        # Must contain the message tool call with correct channel and target
        has_tool_call = (
            'tool: message' in content or
            'tool:message' in content or
            'action: send' in content
        )
        has_dingtalk = 'dingtalk' in content
        has_target = '2735046220840628' in content
        passed = has_tool_call and has_dingtalk and has_target
        checks.append({
            "name": "message_tool_call_present",
            "passed": passed,
            "detail": f"tool:message={has_tool_call}, channel=dingtalk:{has_dingtalk}, target={has_target}"
        })
    except Exception as e:
        checks.append({"name": "message_tool_call_present", "passed": False, "detail": str(e)})

    # ── CHECK 16: No opening pleasantries (no 您好/你好/亲爱的/Hi/Hello at start) ──
    try:
        first_200 = content[:200]
        pleasantries = ['您好', '你好', '亲爱的', 'Hi,', 'Hello,', '早上好', 'Good morning']
        found = [p for p in pleasantries if p in first_200]
        passed = len(found) == 0
        checks.append({
            "name": "no_opening_pleasantries",
            "passed": passed,
            "detail": f"Found pleasantries: {found}" if found else "No opening pleasantries found"
        })
    except Exception as e:
        checks.append({"name": "no_opening_pleasantries", "passed": False, "detail": str(e)})

    # ── CHECK 17: Section 4 SLG content includes Iron Throne data ────────────
    try:
        sec4_match = re.search(r'四、SLG新品测试(.*?)(?=五、STEAM|$)', content, re.DOTALL)
        if sec4_match:
            sec4_content = sec4_match.group(1)
            has_iron_throne = 'Iron Throne' in sec4_content
            passed = has_iron_throne
        else:
            passed = False
        checks.append({
            "name": "section4_contains_iron_throne",
            "passed": passed,
            "detail": "Iron Throne CBT entry found in section 4" if passed
                      else "Section 4 should include Iron Throne: Rise of Kingdoms CBT from raw data"
        })
    except Exception as e:
        checks.append({"name": "section4_contains_iron_throne", "passed": False, "detail": str(e)})

    return checks


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(0)

    workspace = Path(sys.argv[1])
    content, location = load_report(workspace)

    if content is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": location}]
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    checks = [{"name": "file_exists", "passed": True, "detail": f"Found at: {location}"}]
    checks += run_checks(content, workspace)

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = score >= 0.80  # Need 80%+ to pass

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()