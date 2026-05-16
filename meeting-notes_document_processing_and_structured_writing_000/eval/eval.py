import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # Find the output file
    target_files = list(Path(workspace).rglob("meeting_notes_homesense_20250318.md"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "Could not find meeting_notes_homesense_20250318.md anywhere in workspace"}]
        }
    
    # Use the most recently modified one if multiple found
    output_file = sorted(target_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # -----------------------------------------------------------------------
    # CHECK 1: Header format - must have date 2025-03-18
    # -----------------------------------------------------------------------
    has_header_date = "2025-03-18" in content
    checks.append({
        "name": "header_contains_date",
        "passed": has_header_date,
        "detail": "Output must contain the meeting date 2025-03-18 in the header."
    })

    # -----------------------------------------------------------------------
    # CHECK 2: Participants listed correctly - 张敏, 陈浩, 林一帆 all present
    # -----------------------------------------------------------------------
    has_zhang = "张敏" in content
    has_chen = "陈浩" in content
    has_lin = "林一帆" in content
    participants_ok = has_zhang and has_chen and has_lin
    checks.append({
        "name": "participants_listed",
        "passed": participants_ok,
        "detail": f"All three participants (张敏, 陈浩, 林一帆) must appear. Found: 张敏={has_zhang}, 陈浩={has_chen}, 林一帆={has_lin}"
    })

    # -----------------------------------------------------------------------
    # CHECK 3: Greetings DELETED - "新年好" and "久等了"-style content removed
    # -----------------------------------------------------------------------
    has_greeting = "新年好" in content or "久等了" in content or "终于见面了" in content
    checks.append({
        "name": "greetings_deleted",
        "passed": not has_greeting,
        "detail": "Greetings like '新年好', '久等了', '终于见面了' must be deleted per skill rules."
    })

    # -----------------------------------------------------------------------
    # CHECK 4: Demo section DELETED - "能看到吗" and "Ok" confirmations removed
    # -----------------------------------------------------------------------
    has_demo_noise = "能看到吗" in content or "能看到能看到" in content
    checks.append({
        "name": "demo_noise_deleted",
        "passed": not has_demo_noise,
        "detail": "Technical demo confirmation phrases like '能看到吗' must be deleted."
    })

    # -----------------------------------------------------------------------
    # CHECK 5: Investor framing - NO 转述 sentences like "关注...", "试图厘清..."
    # -----------------------------------------------------------------------
    forbidden_framing_patterns = [
        r"关注.{0,10}问题",
        r"试图厘清",
        r"重点考察",
        r"表示关注",
        r"就.{0,15}进行了",
        r"对.{0,15}进行了追问",
    ]
    found_forbidden = []
    for pat in forbidden_framing_patterns:
        if re.search(pat, content):
            found_forbidden.append(pat)
    
    no_indirect_framing = len(found_forbidden) == 0
    checks.append({
        "name": "no_indirect_investor_framing",
        "passed": no_indirect_framing,
        "detail": f"Investor questions must NOT use 转述 framing patterns. Found violations: {found_forbidden}"
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Investor questions appear as direct questions (end with ？or contain question structure)
    # Must find at least 5 investor question blocks
    # -----------------------------------------------------------------------
    # Look for bold investor name followed by a question
    investor_question_blocks = re.findall(r'\*\*(张敏|陈浩)\*\*[:：].{5,200}[？?]', content)
    has_enough_investor_questions = len(investor_question_blocks) >= 5
    checks.append({
        "name": "investor_direct_questions",
        "passed": has_enough_investor_questions,
        "detail": f"Must have at least 5 investor question blocks in **Name**: format. Found: {len(investor_question_blocks)}"
    })

    # -----------------------------------------------------------------------
    # CHECK 7: Founder's key verbatim facts preserved - specific numbers must appear
    # These numbers only exist in the founder's original speech and must NOT be summarized away
    # -----------------------------------------------------------------------
    key_facts = [
        "4200",        # 付费用户数
        "61%",         # 复购率
        "899",         # 产品定价
        "35%",         # 毛利率 (35%到40%)
        "380",         # 早鸟付费用户
        "2500",        # 估值 2500万
        "500万",       # 融资金额
        "15000",       # 6个月用户目标
    ]
    missing_facts = [f for f in key_facts if f not in content]
    verbatim_facts_ok = len(missing_facts) <= 1  # allow at most 1 miss
    checks.append({
        "name": "founder_verbatim_facts_preserved",
        "passed": verbatim_facts_ok,
        "detail": f"Key founder facts (numbers) must be preserved verbatim. Missing: {missing_facts}"
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Speaker label correction - 
    # The transcript has 陈浩's JUDGMENT at 12:45 labeled as Speaker_C but he gives a judgment not a question.
    # That judgment must be attributed to 陈浩 (investor), not to 林一帆.
    # The content "2500万美金对于一个4200用户" is a judgment by 陈浩.
    # Check that "2500万" appears near "陈浩" within 300 chars
    # -----------------------------------------------------------------------
    idx_2500 = content.find("2500万")
    idx_chenghao_near = -1
    if idx_2500 >= 0:
        window = content[max(0, idx_2500-300):idx_2500+300]
        if "陈浩" in window:
            idx_chenghao_near = 1
    
    judgment_attribution_ok = idx_chenghao_near > 0
    checks.append({
        "name": "investor_judgment_correctly_attributed",
        "passed": judgment_attribution_ok,
        "detail": "陈浩's judgment about '2500万美金对于一个4200用户...估值有点超前' must be attributed to 陈浩 (investor), not the project side."
    })

    # -----------------------------------------------------------------------
    # CHECK 9: Theme ORDER matches meeting order
    # The meeting order is: 创始人背景/全职状态 → 创业动机 → 团队 → 产品 → 竞争/壁垒 → 商业模式 → 融资/估值 → 里程碑
    # We check that "团队" section appears BEFORE "估值" section,
    # and "产品" section appears BEFORE "融资" section
    # -----------------------------------------------------------------------
    try:
        # Find section headers
        section_matches = [(m.start(), m.group()) for m in re.finditer(r'##\s+[一二三四五六七八九十]+、.+', content)]
        section_texts = [(pos, content[pos:pos+200]) for pos, _ in section_matches]
        
        # Find positions of key content markers
        pos_team = next((pos for pos, txt in section_texts if any(k in txt for k in ["团队", "成员"])), None)
        pos_valuation = next((pos for pos, txt in section_texts if any(k in txt for k in ["估值", "融资"])), None)
        pos_product = next((pos for pos, txt in section_texts if any(k in txt for k in ["产品", "中枢"])), None)
        
        order_ok = True
        order_detail = []
        if pos_team is not None and pos_valuation is not None:
            if pos_team >= pos_valuation:
                order_ok = False
                order_detail.append("团队 section must come BEFORE 估值/融资 section")
        if pos_product is not None and pos_valuation is not None:
            if pos_product >= pos_valuation:
                order_ok = False
                order_detail.append("产品 section must come BEFORE 估值/融资 section")
        
        checks.append({
            "name": "theme_order_matches_meeting_order",
            "passed": order_ok,
            "detail": f"Themes must follow meeting chronological order. Issues: {order_detail if order_detail else 'none'}"
        })
    except Exception as e:
        checks.append({
            "name": "theme_order_matches_meeting_order",
            "passed": False,
            "detail": f"Error checking theme order: {e}"
        })

    # -----------------------------------------------------------------------
    # CHECK 10: Summary table present with required rows
    # Must have 关键信息摘要 table with at least 创始人, 阶段/Stage, 团队, 估值
    # -----------------------------------------------------------------------
    has_summary_table = "关键信息摘要" in content or "关键信息" in content
    has_table_syntax = "|" in content and "---" in content
    
    required_table_rows = ["创始人", "估值", "团队"]
    missing_rows = [r for r in required_table_rows if r not in content]
    
    summary_table_ok = has_summary_table and has_table_syntax and len(missing_rows) == 0
    checks.append({
        "name": "summary_table_present_and_complete",
        "passed": summary_table_ok,
        "detail": f"Must have 关键信息摘要 table with rows for 创始人, 估值, 团队. has_summary={has_summary_table}, has_table={has_table_syntax}, missing_rows={missing_rows}"
    })

    # -----------------------------------------------------------------------
    # CHECK 11: Investor judgment is framed as judgment, not question
    # 陈浩's line "2500万美金对于一个4200用户的早期项目，这个估值我是有保留的" 
    # must appear as a judgment/statement, not rephrased as a question
    # -----------------------------------------------------------------------
    judgment_keywords = ["保留", "超前", "有保留"]
    judgment_present = any(k in content for k in judgment_keywords)
    checks.append({
        "name": "investor_judgment_preserved_as_judgment",
        "passed": judgment_present,
        "detail": f"陈浩's valuation judgment ('估值我是有保留的' / '估值有点超前') must be preserved. Found keywords: {[k for k in judgment_keywords if k in content]}"
    })

    # -----------------------------------------------------------------------
    # CHECK 12: Founder verbatim answer length check - 
    # Project side answers must NOT be compressed into 1-2 line summaries.
    # Check that the longest 项目方 answer block is at least 80 characters
    # (indicating verbatim preservation, not summary)
    # -----------------------------------------------------------------------
    project_answer_blocks = re.findall(r'\*\*(?:林一帆|项目方)\*\*[:：]\s*(.+?)(?=\n\n|\n##|\Z)', content, re.DOTALL)
    if project_answer_blocks:
        longest_answer = max(len(block.strip()) for block in project_answer_blocks)
        answer_verbatim_ok = longest_answer >= 80
    else:
        longest_answer = 0
        answer_verbatim_ok = False
    
    checks.append({
        "name": "founder_answers_not_compressed",
        "passed": answer_verbatim_ok,
        "detail": f"Founder/project answers must be preserved verbatim (not compressed to short summaries). Longest answer block: {longest_answer} chars (need ≥80)."
    })

    # -----------------------------------------------------------------------
    # SCORING
    # -----------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    overall_passed = score >= 0.75  # Must pass at least 9/12 checks

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))