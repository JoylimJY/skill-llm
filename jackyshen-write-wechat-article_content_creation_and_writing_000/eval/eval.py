import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    workspace = Path(workspace_dir)
    
    # --- FIND THE ARTICLE ---
    article_files = list(workspace.rglob("remote_team_article.md"))
    
    if not article_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "remote_team_article.md not found anywhere in workspace"}]
        }
    
    article_path = article_files[0]
    
    try:
        content = article_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # CHECK 1: File exists and is readable
    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found article at {article_path}"
    })

    # CHECK 2: Word count in Standard range (1200-2000 words)
    # Count both English and CJK characters/words
    try:
        # Count English words
        english_words = len(re.findall(r'[a-zA-Z]+', content))
        # Count CJK characters (each character ≈ 1 word in Chinese)
        cjk_chars = len(re.findall(r'[\u4e00-\u9fff\u3400-\u4dbf]', content))
        # Rough total word equivalent
        total_word_equiv = english_words + cjk_chars
        
        in_range = 1200 <= total_word_equiv <= 2000
        checks.append({
            "name": "word_count_standard_range",
            "passed": in_range,
            "detail": f"Estimated word count: {total_word_equiv} (English words: {english_words}, CJK chars: {cjk_chars}). Expected: 1200-2000"
        })
    except Exception as e:
        checks.append({
            "name": "word_count_standard_range",
            "passed": False,
            "detail": f"Word count check failed: {e}"
        })

    # CHECK 3: No Markdown tables (no | col | col | patterns — WeChat cannot parse them)
    try:
        # Detect MD table rows: lines with multiple pipe characters forming table structure
        lines = content.split('\n')
        table_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            # A markdown table row typically has | at start and end or multiple pipes
            if re.match(r'^\|.+\|', stripped) and '|' in stripped[1:]:
                table_lines.append((i+1, stripped[:80]))
        
        no_md_tables = len(table_lines) == 0
        checks.append({
            "name": "no_markdown_tables",
            "passed": no_md_tables,
            "detail": f"No Markdown tables found" if no_md_tables else f"Found {len(table_lines)} Markdown table line(s). Example: Line {table_lines[0][0]}: '{table_lines[0][1]}'"
        })
    except Exception as e:
        checks.append({
            "name": "no_markdown_tables",
            "passed": False,
            "detail": f"Table check failed: {e}"
        })

    # CHECK 4: Has proper H1 title matching one of the 6 title formulas
    # Formulas: Numbered List, How-to, Contrast, Question, Story, Curiosity
    try:
        h1_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        has_h1 = h1_match is not None
        title_text = h1_match.group(1) if h1_match else ""
        
        # Check if title follows one of the formula patterns
        formula_indicators = [
            # Numbered list: contains a digit + tip/ways/methods
            bool(re.search(r'\d+\s*(个|步|条|招|种|tips?|ways?|method)', title_text, re.IGNORECASE)),
            # How-to: starts with 如何/怎么/how to
            bool(re.search(r'^(如何|怎么|怎样|how\s+to)', title_text, re.IGNORECASE)),
            # Contrast: contains 却/但|but|however or destructive words
            bool(re.search(r'(却|反而|正在|毁掉|destroying|killing|hurting)', title_text, re.IGNORECASE)),
            # Question: ends with ? or ？
            bool(re.search(r'[?？]', title_text)),
            # Story: contains narrative numbers/progression (from X to Y)
            bool(re.search(r'(从|到|：|:).*(秘密|武器|秘诀|secret|weapon)', title_text, re.IGNORECASE)),
            # Curiosity: contains "never/从不/不会告诉你" or expert patterns
            bool(re.search(r'(从不|不会告诉|never tell|专家|高手|expert)', title_text, re.IGNORECASE)),
            # General: has a clear number pattern (listicle) - broader check
            bool(re.search(r'\d', title_text)),
        ]
        
        title_uses_formula = any(formula_indicators)
        checks.append({
            "name": "title_uses_formula",
            "passed": has_h1 and title_uses_formula,
            "detail": f"Title: '{title_text}'. Uses recognized formula: {title_uses_formula}"
        })
    except Exception as e:
        checks.append({
            "name": "title_uses_formula",
            "passed": False,
            "detail": f"Title check failed: {e}"
        })

    # CHECK 5: Has Opening section
    try:
        has_opening = bool(re.search(r'^## (Opening|开篇|引言|开场)', content, re.MULTILINE | re.IGNORECASE))
        checks.append({
            "name": "has_opening_section",
            "passed": has_opening,
            "detail": f"Opening section {'found' if has_opening else 'NOT found'}. Expected '## Opening' or similar H2 heading."
        })
    except Exception as e:
        checks.append({
            "name": "has_opening_section",
            "passed": False,
            "detail": f"Opening check failed: {e}"
        })

    # CHECK 6: Has Body section with at least 3 H3 subheadings
    try:
        h3_headings = re.findall(r'^### (.+)$', content, re.MULTILINE)
        has_three_points = len(h3_headings) >= 3
        checks.append({
            "name": "body_has_three_h3_points",
            "passed": has_three_points,
            "detail": f"Found {len(h3_headings)} H3 subheadings: {h3_headings[:5]}"
        })
    except Exception as e:
        checks.append({
            "name": "body_has_three_h3_points",
            "passed": False,
            "detail": f"H3 check failed: {e}"
        })

    # CHECK 7: Has 💡 Actionable Tip markers (proprietary skill format)
    try:
        actionable_tips = re.findall(r'💡\s*\*\*Actionable Tip', content)
        # Also accept Chinese variant
        actionable_tips_cn = re.findall(r'💡\s*\*\*(行动|可执行|实操|操作)', content)
        tip_emoji_generic = re.findall(r'💡', content)
        
        total_tip_markers = len(actionable_tips) + len(actionable_tips_cn)
        # At least check for 💡 emoji used in tip context (3+ times)
        has_tips = total_tip_markers >= 3 or len(tip_emoji_generic) >= 3
        checks.append({
            "name": "has_actionable_tip_markers",
            "passed": has_tips,
            "detail": f"Found {len(tip_emoji_generic)} 💡 emoji usage(s). English 'Actionable Tip' markers: {len(actionable_tips)}, Chinese variants: {len(actionable_tips_cn)}"
        })
    except Exception as e:
        checks.append({
            "name": "has_actionable_tip_markers",
            "passed": False,
            "detail": f"Actionable tip check failed: {e}"
        })

    # CHECK 8: Has Closing section
    try:
        has_closing = bool(re.search(r'^## (Closing|结尾|结语|总结|写在最后)', content, re.MULTILINE | re.IGNORECASE))
        checks.append({
            "name": "has_closing_section",
            "passed": has_closing,
            "detail": f"Closing section {'found' if has_closing else 'NOT found'}."
        })
    except Exception as e:
        checks.append({
            "name": "has_closing_section",
            "passed": False,
            "detail": f"Closing check failed: {e}"
        })

    # CHECK 9: Has Discussion/CTA block (💬 Discussion with question)
    try:
        has_discussion_emoji = bool(re.search(r'💬', content))
        has_discussion_section = bool(re.search(r'\*\*💬\s*(Discussion|讨论|互动|留言)', content, re.IGNORECASE))
        has_discussion = has_discussion_emoji and (has_discussion_section or bool(re.search(r'💬', content)))
        checks.append({
            "name": "has_discussion_block",
            "passed": has_discussion,
            "detail": f"💬 emoji found: {has_discussion_emoji}. Discussion section heading: {has_discussion_section}"
        })
    except Exception as e:
        checks.append({
            "name": "has_discussion_block",
            "passed": False,
            "detail": f"Discussion check failed: {e}"
        })

    # CHECK 10: Has Author/Source footer
    try:
        has_author = bool(re.search(r'\*Author.*\*|\*作者.*\*|Author:|作者：', content, re.IGNORECASE))
        has_source = bool(re.search(r'\*(Source|来源|账号|Account).*\*|(Source|来源):', content, re.IGNORECASE))
        has_footer = has_author or has_source
        # Check for the HR divider before footer
        has_hr = bool(re.search(r'^---\s*$', content, re.MULTILINE))
        checks.append({
            "name": "has_author_source_footer",
            "passed": has_footer,
            "detail": f"Author field: {has_author}, Source field: {has_source}, HR divider: {has_hr}"
        })
    except Exception as e:
        checks.append({
            "name": "has_author_source_footer",
            "passed": False,
            "detail": f"Footer check failed: {e}"
        })

    # CHECK 11: Pyramid Principle — main conclusion/insight appears early (in first 20% of body)
    try:
        lines = content.split('\n')
        total_lines = len(lines)
        first_20_pct = '\n'.join(lines[:max(1, int(total_lines * 0.20))])
        
        # Main conclusion should be stated early (presence of bold/key claim in opening)
        has_early_bold = bool(re.search(r'\*\*.+\*\*', first_20_pct))
        # Should address "you" (reader-focused)
        has_you_address = bool(re.search(r'你|您|your|you', first_20_pct, re.IGNORECASE))
        
        pyramid_ok = has_early_bold and has_you_address
        checks.append({
            "name": "pyramid_principle_early_conclusion",
            "passed": pyramid_ok,
            "detail": f"First 20% has bold claim: {has_early_bold}, addresses reader 'you/你': {has_you_address}"
        })
    except Exception as e:
        checks.append({
            "name": "pyramid_principle_early_conclusion",
            "passed": False,
            "detail": f"Pyramid check failed: {e}"
        })

    # CHECK 12: Content is relevant to remote team collaboration
    try:
        remote_keywords = ['远程', 'remote', '协作', 'collaborat', '团队', 'team', '沟通', 'communicat', '异步', 'async', '会议', 'meeting']
        found_keywords = [kw for kw in remote_keywords if kw.lower() in content.lower()]
        relevant = len(found_keywords) >= 4
        checks.append({
            "name": "content_relevance_remote_collaboration",
            "passed": relevant,
            "detail": f"Found {len(found_keywords)}/12 remote collaboration keywords: {found_keywords}"
        })
    except Exception as e:
        checks.append({
            "name": "content_relevance_remote_collaboration",
            "passed": False,
            "detail": f"Relevance check failed: {e}"
        })

    # --- SCORING ---
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    
    # Weight critical checks more heavily
    critical_checks = ["no_markdown_tables", "word_count_standard_range", "has_actionable_tip_markers", "body_has_three_h3_points"]
    critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
    critical_total = len(critical_checks)
    
    # Score: 60% from critical checks, 40% from all checks
    if total_checks > 0:
        base_score = (passed_checks / total_checks) * 0.4
        critical_score = (critical_passed / critical_total) * 0.6
        score = round(base_score + critical_score, 3)
    else:
        score = 0.0

    overall_passed = score >= 0.75 and critical_passed >= 3

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))