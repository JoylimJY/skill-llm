import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    score = 0.0

    # ── Find the report file ────────────────────────────────────────────────────
    report_files = list(ws.rglob("daily_report.md"))
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "daily_report.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False,
                        "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": f"Found at {report_path}"})
    score += 0.05

    # ── CHECK 1: Proprietary header format ──────────────────────────────────────
    has_border = "═══" in content
    has_emoji_title = "📋" in content and ("每日智能盘点报告" in content or "每日" in content)
    header_ok = has_border and has_emoji_title
    checks.append({
        "name": "proprietary_header_format",
        "passed": header_ok,
        "detail": f"═══ border: {has_border}, 📋 emoji+title: {has_emoji_title}"
    })
    if header_ok:
        score += 0.10

    # ── CHECK 2: 概览 section present with correct structure ───────────────────
    has_overview = "【概览】" in content
    has_scan_range = "最近24小时" in content or "24小时" in content
    overview_ok = has_overview and has_scan_range
    checks.append({
        "name": "overview_section",
        "passed": overview_ok,
        "detail": f"【概览】present: {has_overview}, scan range '24小时': {has_scan_range}"
    })
    if overview_ok:
        score += 0.08

    # ── CHECK 3: 分类统计 section with all 6 categories ────────────────────────
    classification_section = "【分类统计】" in content
    categories = {
        "客户沟通": "客户沟通" in content,
        "内部会议": "内部会议" in content,
        "渠道合作": "渠道合作" in content,
        "投资决策": "投资决策" in content,
        "灵感/想法": "灵感" in content or "灵感/想法" in content,
        "内容创作": "内容创作" in content,
    }
    all_categories = all(categories.values())
    checks.append({
        "name": "classification_section_all_6_categories",
        "passed": classification_section and all_categories,
        "detail": f"Section present: {classification_section}, categories found: {categories}"
    })
    if classification_section and all_categories:
        score += 0.12

    # ── CHECK 4: Client 客户沟通 — 2 entries correctly identified ───────────────
    has_xinda = "鑫达" in content or "北京鑫达" in content
    has_mingtu = "明途" in content or "上海明途" in content
    clients_ok = has_xinda and has_mingtu
    checks.append({
        "name": "client_communication_both_clients",
        "passed": clients_ok,
        "detail": f"北京鑫达 found: {has_xinda}, 上海明途 found: {has_mingtu}"
    })
    if clients_ok:
        score += 0.10

    # ── CHECK 5: 客户沟通 action label contains proprietary text ────────────────
    # Expected: "已诊断" and "已更新CRM" (from SKILL.md's auto-processing table)
    has_diagnosed = "已诊断" in content
    has_crm_updated = "已更新CRM" in content or "更新CRM" in content
    client_action_ok = has_diagnosed and has_crm_updated
    checks.append({
        "name": "client_action_labels_proprietary",
        "passed": client_action_ok,
        "detail": f"'已诊断' found: {has_diagnosed}, 'CRM更新' found: {has_crm_updated}"
    })
    if client_action_ok:
        score += 0.10

    # ── CHECK 6: 内部会议 — todos extracted ────────────────────────────────────
    has_todos_section = "【待办事项】" in content
    has_liming = "李明" in content
    has_chenm = "陈梅" in content
    has_todo_format = bool(re.search(r"\[ \]|\[x\]|\[X\]", content))
    todos_ok = has_todos_section and has_liming and has_chenm
    checks.append({
        "name": "internal_meeting_todos_extracted",
        "passed": todos_ok,
        "detail": f"待办事项 section: {has_todos_section}, 李明: {has_liming}, 陈梅: {has_chenm}"
    })
    if todos_ok:
        score += 0.10

    # ── CHECK 7: 渠道合作 — channel partner identified ─────────────────────────
    has_channel = "成都智联" in content or "智联教育" in content or "赵总" in content
    has_channel_action = "已更新渠道表" in content or "渠道表" in content or "渠道档案" in content
    channel_ok = has_channel and has_channel_action
    checks.append({
        "name": "channel_cooperation_identified",
        "passed": channel_ok,
        "detail": f"成都智联/赵总 found: {has_channel}, 渠道表 action: {has_channel_action}"
    })
    if channel_ok:
        score += 0.08

    # ── CHECK 8: 投资决策 — correctly classified and report generated ───────────
    has_investment = "投资" in content and ("BP" in content or "融资" in content or "估值" in content)
    has_investment_action = "投资分析报告" in content or "已生成报告" in content or "投资报告" in content
    investment_ok = has_investment and has_investment_action
    checks.append({
        "name": "investment_decision_classified",
        "passed": investment_ok,
        "detail": f"Investment content found: {has_investment}, action label: {has_investment_action}"
    })
    if investment_ok:
        score += 0.08

    # ── CHECK 9: 灵感/想法 — stored in 素材库/选题 ────────────────────────────
    has_inspiration = "灵感" in content
    has_inspiration_action = "素材库" in content or "已存素材库" in content or "选题" in content
    inspiration_ok = has_inspiration and has_inspiration_action
    checks.append({
        "name": "inspiration_classified_and_stored",
        "passed": inspiration_ok,
        "detail": f"灵感 found: {has_inspiration}, 素材库/选题 action: {has_inspiration_action}"
    })
    if inspiration_ok:
        score += 0.06

    # ── CHECK 10: 内容创作 — stored in 选题库 ──────────────────────────────────
    has_content = "内容创作" in content or "短视频" in content
    has_content_action = "选题库" in content or "已存选题库" in content or "内容大纲" in content
    content_ok = has_content and has_content_action
    checks.append({
        "name": "content_creation_classified",
        "passed": content_ok,
        "detail": f"内容创作/短视频 found: {has_content}, 选题库 action: {has_content_action}"
    })
    if content_ok:
        score += 0.06

    # ── CHECK 11: Low-value note skipped / not counted as valuable ──────────────
    # The "无内容备忘" note should NOT be counted as valuable
    # The report should show at least 1 note skipped OR the 有价值 count < total count
    valuable_match = re.search(r"有价值录音[：:]\s*(\d+)", content)
    total_match = re.search(r"新增录音[：:]\s*(\d+)", content)
    skip_ok = False
    skip_detail = "Could not parse counts from 概览 section"
    if valuable_match and total_match:
        valuable = int(valuable_match.group(1))
        total = int(total_match.group(1))
        # Total should be at least 7 (6 valid + 1 low-value), valuable < total
        # OR the lowvalue note must be mentioned as skipped
        skip_ok = (total >= 7 and valuable < total) or (total >= 6 and valuable <= 6)
        skip_detail = f"Total: {total}, Valuable: {valuable}, skip_ok: {skip_ok}"
    else:
        # Alternative: look for explicit skip mention
        skip_ok = "跳过" in content or "无价值" in content or "低价值" in content
        skip_detail = f"Count parsing failed; explicit skip mention: {skip_ok}"
    checks.append({
        "name": "low_value_note_skipped",
        "passed": skip_ok,
        "detail": skip_detail
    })
    if skip_ok:
        score += 0.07

    # ── CHECK 12: Tree drawing characters used in classification section ─────────
    has_tree_chars = "├─" in content or "└─" in content
    checks.append({
        "name": "tree_drawing_characters_used",
        "passed": has_tree_chars,
        "detail": f"├─ or └─ present in report: {has_tree_chars}"
    })
    if has_tree_chars:
        score += 0.05

    # ── CHECK 13: CRM update detail section ─────────────────────────────────────
    has_crm_section = "【CRM更新详情】" in content
    checks.append({
        "name": "crm_update_detail_section",
        "passed": has_crm_section,
        "detail": f"【CRM更新详情】 section present: {has_crm_section}"
    })
    if has_crm_section:
        score += 0.05

    # ── CHECK 14: 今日小结 section present ──────────────────────────────────────
    has_summary = "【今日小结】" in content
    checks.append({
        "name": "daily_summary_section",
        "passed": has_summary,
        "detail": f"【今日小结】 present: {has_summary}"
    })
    if has_summary:
        score += 0.05

    # ── CHECK 15: Old files (>24h) NOT counted as new recordings ────────────────
    # The "already-processed-客户ABC" was 72h ago and "old-灵感" was 48.5h ago
    # They must NOT appear in the valued items
    old_note_erroneously_included = False
    # If "already-processed" content appears in the classification stats it's a bug
    if re.search(r"客户ABC", content):
        old_note_erroneously_included = True
    if re.search(r"old-灵感|20231201", content):
        old_note_erroneously_included = True
    checks.append({
        "name": "old_files_excluded_from_24h_scan",
        "passed": not old_note_erroneously_included,
        "detail": f"Old files (>24h) erroneously included: {old_note_erroneously_included}"
    })
    if not old_note_erroneously_included:
        score += 0.05

    # ── Final verdict ────────────────────────────────────────────────────────────
    score = round(min(score, 1.0), 4)
    passed = score >= 0.60 and checks[0]["passed"]

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))