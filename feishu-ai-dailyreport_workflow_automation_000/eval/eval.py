import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))
today_beijing = datetime.now(BEIJING_TZ).date()
expected_date_str = today_beijing.strftime("%Y-%m-%d")
expected_filename = f"daily-report-{expected_date_str}.md"

# Expected agent configuration from SKILL.md
AGENTS = [
    ("main",      "芮芮",  "总助理",         "📋"),
    ("architect", "小明",  "系统架构师",      "🏗️"),
    ("ops",       "小王",  "运维工程师",      "🔧"),
    ("stock",     "小钱",  "股票助手",        "💰"),
    ("xiaolan",   "小蓝",  "浏览器操作助手",  "🌐"),
    ("content",   "小圆",  "内容写手",        "📝"),
    ("aigf",      "aigf",  "临时项目开发",    "💕"),
    ("xiaotian",  "小天",  "灵感记录",        "✨"),
]

# Expected deduplicated messages from TODAY's sessions
EXPECTED_WORK = {
    "main": [
        "帮我整理一下今天的会议纪要",
        "查询一下本周的团队进度",
        "发送日报给所有成员",
    ],
    "architect": [
        "设计微服务拆分方案",
        "评审API接口文档",
        "数据库schema优化建议",
    ],
    "ops": [
        "检查服务器CPU使用率",
        "更新Docker镜像到最新版本",
        "配置监控告警规则",
    ],
    "stock": [
        "分析今日A股大盘走势",
        "查询贵州茅台最新股价",
    ],
    "xiaolan": [
        "帮我打开淘宝搜索耳机",
        "截图当前页面",
    ],
    "content": [
        "写一篇关于AI发展的文章",
        "优化产品介绍文案",
        "生成5条社交媒体推文",
    ],
    "aigf": [],
    "xiaotian": [
        "记录一个关于量子计算的灵感",
        "整理本周的创意想法",
    ],
}

def find_report(workspace):
    """Find the daily report file."""
    # Check the canonical path first
    canonical = Path("/root/.openclaw/workspace") / expected_filename
    if canonical.exists():
        return canonical
    # Fallback: search in workspace arg
    for p in Path(workspace).rglob(expected_filename):
        return p
    return None

def evaluate(workspace):
    checks = []
    
    # ---- CHECK 1: File exists with correct name ----
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_exists,
        "detail": f"Expected file '{expected_filename}' at /root/.openclaw/workspace/. Found: {report_path}"
    })
    
    if not file_exists:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    lines = content.split("\n")
    
    # ---- CHECK 2: First line format ----
    expected_line1 = f"📅 AI助手工作日报（{expected_date_str}）"
    line1_ok = len(lines) > 0 and lines[0].strip() == expected_line1
    checks.append({
        "name": "first_line_format",
        "passed": line1_ok,
        "detail": f"Expected: '{expected_line1}', Got: '{lines[0].strip() if lines else ''}'"
    })
    
    # ---- CHECK 3: Second line is generation time ----
    line2_ok = False
    line2_detail = "Line 2 missing or malformed"
    if len(lines) > 1:
        m = re.match(r"^生成时间：(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})$", lines[1].strip())
        if m:
            date_part = m.group(1)
            line2_ok = date_part == expected_date_str
            line2_detail = f"Date in generation time: {date_part} (expected {expected_date_str})"
        else:
            line2_detail = f"Format mismatch. Got: '{lines[1].strip()}'"
    checks.append({
        "name": "second_line_generation_time",
        "passed": line2_ok,
        "detail": line2_detail
    })
    
    # ---- CHECK 4: Contains overview section header ----
    has_overview = "📊 团队工作总览" in content
    checks.append({
        "name": "has_overview_section",
        "passed": has_overview,
        "detail": "'📊 团队工作总览' section header present" if has_overview else "Missing '📊 团队工作总览'"
    })
    
    # ---- CHECK 5: Contains detail section header ----
    has_detail = "📝 详细工作内容" in content
    checks.append({
        "name": "has_detail_section",
        "passed": has_detail,
        "detail": "'📝 详细工作内容' section header present" if has_detail else "Missing '📝 详细工作内容'"
    })
    
    # ---- CHECK 6: All 8 team members present in overview with correct emoji and Chinese parentheses ----
    overview_checks_passed = 0
    overview_details = []
    for agent_id, name, role, emoji in AGENTS:
        # Must use Chinese parentheses （）
        pattern = rf"- {re.escape(emoji)} {re.escape(name)}（{re.escape(role)}）："
        found = bool(re.search(pattern, content))
        if found:
            overview_checks_passed += 1
        overview_details.append(f"{name}: {'✓' if found else '✗'}")
    
    all_members_overview = overview_checks_passed == len(AGENTS)
    checks.append({
        "name": "all_members_in_overview",
        "passed": all_members_overview,
        "detail": f"{overview_checks_passed}/{len(AGENTS)} members correctly formatted in overview. " + ", ".join(overview_details)
    })
    
    # ---- CHECK 7: Detail section member headers use correct format ----
    detail_header_passed = 0
    detail_header_details = []
    for agent_id, name, role, emoji in AGENTS:
        # Must match: emoji name（role） as a standalone line
        pattern = rf"^{re.escape(emoji)} {re.escape(name)}（{re.escape(role)}）\s*$"
        found = bool(re.search(pattern, content, re.MULTILINE))
        if found:
            detail_header_passed += 1
        detail_header_details.append(f"{name}: {'✓' if found else '✗'}")
    
    all_detail_headers = detail_header_passed == len(AGENTS)
    checks.append({
        "name": "all_member_headers_in_detail",
        "passed": all_detail_headers,
        "detail": f"{detail_header_passed}/{len(AGENTS)} member headers correct. " + ", ".join(detail_header_details)
    })
    
    # ---- CHECK 8: aigf has "今日无工作内容" (no work today) ----
    aigf_no_work = "今日无工作内容" in content
    checks.append({
        "name": "aigf_no_work_content",
        "passed": aigf_no_work,
        "detail": "'今日无工作内容' present for aigf (no messages today)" if aigf_no_work else "Missing '今日无工作内容' for aigf"
    })
    
    # ---- CHECK 9: Footer format ----
    has_separator = "---" in content
    has_footer = "*日报由芮芮自动生成*" in content
    footer_ok = has_separator and has_footer
    checks.append({
        "name": "footer_format",
        "passed": footer_ok,
        "detail": f"Separator '---': {has_separator}, Footer '*日报由芮芮自动生成*': {has_footer}"
    })
    
    # ---- CHECK 10: DM prefix stripped - actual work content present (not raw DM strings) ----
    # The report should NOT contain "DM from ou_" raw strings
    raw_dm_present = "DM from ou_" in content
    checks.append({
        "name": "dm_prefix_stripped",
        "passed": not raw_dm_present,
        "detail": "Raw 'DM from ou_' prefixes correctly stripped" if not raw_dm_present else "ERROR: Raw 'DM from ou_' strings found in report - prefix not stripped"
    })
    
    # ---- CHECK 11: Yesterday's content NOT included ----
    yesterday_content = ["昨天的工作内容", "昨天设计了数据库", "昨天重启了服务器"]
    yesterday_leaked = any(yc in content for yc in yesterday_content)
    checks.append({
        "name": "no_yesterday_content",
        "passed": not yesterday_leaked,
        "detail": "Yesterday's session data correctly excluded" if not yesterday_leaked else "ERROR: Yesterday's content leaked into report"
    })
    
    # ---- CHECK 12: Non-DM system messages not extracted ----
    system_msg_leaked = "系统消息：请更新状态" in content
    checks.append({
        "name": "no_non_dm_messages",
        "passed": not system_msg_leaked,
        "detail": "Non-DM system messages correctly excluded" if not system_msg_leaked else "ERROR: Non-DM system messages included in report"
    })
    
    # ---- CHECK 13: Key work items present (deduplicated) ----
    # Spot-check some known expected items
    spot_checks = [
        ("帮我整理一下今天的会议纪要", "main work item 1"),
        ("设计微服务拆分方案", "architect work item 1"),
        ("检查服务器CPU使用率", "ops work item 1"),
        ("分析今日A股大盘走势", "stock work item"),
        ("帮我打开淘宝搜索耳机", "xiaolan work item"),
        ("写一篇关于AI发展的文章", "content work item"),
        ("记录一个关于量子计算的灵感", "xiaotian work item"),
    ]
    spot_passed = 0
    spot_details = []
    for item, label in spot_checks:
        found = item in content
        if found:
            spot_passed += 1
        spot_details.append(f"{label}: {'✓' if found else '✗'}")
    
    spot_ok = spot_passed >= 5  # At least 5/7 spot checks pass
    checks.append({
        "name": "key_work_items_present",
        "passed": spot_ok,
        "detail": f"{spot_passed}/{len(spot_checks)} key work items found. " + ", ".join(spot_details)
    })
    
    # ---- CHECK 14: Numbered list format for work items ----
    # Should have "1. " formatted items
    has_numbered = bool(re.search(r"^1\. ", content, re.MULTILINE))
    checks.append({
        "name": "numbered_list_format",
        "passed": has_numbered,
        "detail": "Numbered list format (1. ) present" if has_numbered else "Missing numbered list format"
    })
    
    # ---- CHECK 15: Deduplication check - "帮我整理一下今天的会议纪要" appears only once ----
    dedup_count = content.count("帮我整理一下今天的会议纪要")
    dedup_ok = dedup_count == 1
    checks.append({
        "name": "deduplication_applied",
        "passed": dedup_ok,
        "detail": f"Duplicate message appears {dedup_count} time(s), expected 1 (deduplication check)"
    })
    
    # ---- Score calculation ----
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "report_file_exists",
        "first_line_format",
        "all_members_in_overview",
        "footer_format",
        "dm_prefix_stripped",
        "no_yesterday_content",
        "deduplication_applied",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))