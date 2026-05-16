import sys
import json
import re
from pathlib import Path

def check_file(path: Path, label: str):
    """Return (content, error_detail)"""
    try:
        if not path.exists():
            return None, f"File not found: {path}"
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return None, f"File is empty: {path}"
        return content, None
    except Exception as e:
        return None, f"Error reading {path}: {e}"

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    reviewed_dir = workspace / "hr_system" / "candidates" / "2025" / "reviewed"

    # =========================================================
    # FILE 1: Polished Resume
    # =========================================================
    resume_path = reviewed_dir / "polished_resume_chensiyuan.txt"
    resume_content, resume_err = check_file(resume_path, "Resume")

    # Check 1: Resume file exists
    checks.append({
        "name": "resume_file_exists",
        "passed": resume_content is not None,
        "detail": resume_err if resume_content is None else f"Found at {resume_path}"
    })

    if resume_content:
        # Check 2: Resume has the required 4-section emoji format
        has_original_section = "📝" in resume_content and ("原文" in resume_content)
        has_polished_section = "✨" in resume_content and ("润色后" in resume_content)
        has_changes_section = "🔧" in resume_content and ("主要修改" in resume_content)
        has_explanation_section = "💡" in resume_content and ("改进说明" in resume_content)
        has_full_format = has_original_section and has_polished_section and has_changes_section and has_explanation_section
        checks.append({
            "name": "resume_has_four_section_emoji_format",
            "passed": has_full_format,
            "detail": f"📝原文:{has_original_section}, ✨润色后:{has_polished_section}, 🔧主要修改:{has_changes_section}, 💡改进说明:{has_explanation_section}"
        })

        # Check 3: Resume polished section contains verb-first bullet points
        # Extract polished section content between ✨ and 🔧
        polished_section = ""
        try:
            match = re.search(r'✨.*?润色后[：:]\s*(.*?)(?=🔧|$)', resume_content, re.DOTALL)
            if match:
                polished_section = match.group(1)
        except Exception:
            polished_section = resume_content

        # Check for action verbs at start of bullet lines (common Chinese action verbs)
        action_verbs = ['负责', '主导', '策划', '执行', '管理', '提升', '优化', '撰写', '统筹', '推动',
                        '完成', '建立', '开发', '运营', '维护', '协调', '带领', '制定', '拓展', '实现',
                        '增长', '达成', '搭建', '设计', '参与', '推进']
        bullet_lines = [l.strip() for l in polished_section.split('\n') if l.strip().startswith('-') or l.strip().startswith('•') or l.strip().startswith('·')]
        verb_first_count = 0
        for line in bullet_lines:
            line_content = re.sub(r'^[-•·\s]+', '', line).strip()
            if any(line_content.startswith(v) for v in action_verbs):
                verb_first_count += 1
        verb_first_ratio = verb_first_count / len(bullet_lines) if bullet_lines else 0
        has_verb_first = verb_first_ratio >= 0.5 or verb_first_count >= 3
        checks.append({
            "name": "resume_verb_first_bullet_points",
            "passed": has_verb_first,
            "detail": f"Found {verb_first_count}/{len(bullet_lines)} verb-first bullet lines (ratio: {verb_first_ratio:.2f}). Need >= 50% or >= 3 verb-first lines."
        })

        # Check 4: Resume polished section contains quantified metrics
        has_quantification = bool(re.search(r'\d+[%％]|\d+倍|\d+万|\d+个|\d+人|\d+篇|\d+次|\d+年', polished_section if polished_section else resume_content))
        checks.append({
            "name": "resume_has_quantified_metrics",
            "passed": has_quantification,
            "detail": f"Polished resume must include quantified metrics (e.g., 15%, 3倍, 10万). Found: {has_quantification}"
        })

        # Check 5: Resume polished content is under 1000 Chinese characters
        # Count only the polished section
        chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', polished_section)) if polished_section else 0
        # If we couldn't extract polished section, use full content minus headers
        if chinese_char_count == 0:
            chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', resume_content))
        under_limit = chinese_char_count <= 1000
        checks.append({
            "name": "resume_polished_under_1000_chars",
            "passed": under_limit,
            "detail": f"Polished resume section has ~{chinese_char_count} Chinese characters. Must be <= 1000."
        })

    else:
        # File missing - add placeholder failures
        for name in ["resume_has_four_section_emoji_format", "resume_verb_first_bullet_points",
                     "resume_has_quantified_metrics", "resume_polished_under_1000_chars"]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})

    # =========================================================
    # FILE 2: Polished Email
    # =========================================================
    email_path = reviewed_dir / "polished_email_cooperation.txt"
    email_content, email_err = check_file(email_path, "Email")

    checks.append({
        "name": "email_file_exists",
        "passed": email_content is not None,
        "detail": email_err if email_content is None else f"Found at {email_path}"
    })

    if email_content:
        # Check 6: Email has the required 4-section emoji format
        has_email_format = (
            "📝" in email_content and "原文" in email_content and
            "✨" in email_content and "润色后" in email_content and
            "🔧" in email_content and "主要修改" in email_content and
            "💡" in email_content and "改进说明" in email_content
        )
        checks.append({
            "name": "email_has_four_section_emoji_format",
            "passed": has_email_format,
            "detail": f"Email must have 📝原文 / ✨润色后 / 🔧主要修改 / 💡改进说明 sections. Found: {has_email_format}"
        })

        # Check 7: Email polished section has explicit action request (结尾明确行动要求)
        polished_email_section = ""
        try:
            match = re.search(r'✨.*?润色后[：:]\s*(.*?)(?=🔧|$)', email_content, re.DOTALL)
            if match:
                polished_email_section = match.group(1)
        except Exception:
            polished_email_section = email_content

        action_request_patterns = [
            r'期待.*?回复', r'请.*?联系', r'请.*?回复', r'烦请.*?告知', r'敬请.*?回复',
            r'期待您的.*?回', r'如有.*?请.*?联系', r'请您.*?告知', r'麻烦.*?回复',
            r'请问.*?方便', r'希望.*?尽快', r'期盼.*?回音', r'请.*?安排',
            r'如.*?方便.*?请', r'欢迎.*?进一步', r'敬请.*?指示'
        ]
        section_to_check = polished_email_section if polished_email_section else email_content
        has_action_request = any(re.search(p, section_to_check) for p in action_request_patterns)
        checks.append({
            "name": "email_has_explicit_action_request",
            "passed": has_action_request,
            "detail": f"Email must end with an explicit action request (e.g., 期待回复, 请联系, 烦请告知). Found: {has_action_request}"
        })

        # Check 8: Email polished section has proper greeting and sign-off
        has_greeting = bool(re.search(r'尊敬的|您好|敬启者', section_to_check))
        has_signoff = bool(re.search(r'此致|敬上|顺颂|谢谢|谨上|祝好', section_to_check))
        has_proper_structure = has_greeting and has_signoff
        checks.append({
            "name": "email_has_proper_greeting_and_signoff",
            "passed": has_proper_structure,
            "detail": f"Email must have polite greeting (尊敬的/您好) and sign-off (此致/敬上/谢谢等). Greeting:{has_greeting}, Signoff:{has_signoff}"
        })

    else:
        for name in ["email_has_four_section_emoji_format", "email_has_explicit_action_request",
                     "email_has_proper_greeting_and_signoff"]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})

    # =========================================================
    # FILE 3: Polished Article
    # =========================================================
    article_path = reviewed_dir / "polished_article_digital_transformation.txt"
    article_content, article_err = check_file(article_path, "Article")

    checks.append({
        "name": "article_file_exists",
        "passed": article_content is not None,
        "detail": article_err if article_content is None else f"Found at {article_path}"
    })

    if article_content:
        # Check 9: Article has 4-section emoji format
        has_article_format = (
            "📝" in article_content and "原文" in article_content and
            "✨" in article_content and "润色后" in article_content and
            "🔧" in article_content and "主要修改" in article_content and
            "💡" in article_content and "改进说明" in article_content
        )
        checks.append({
            "name": "article_has_four_section_emoji_format",
            "passed": has_article_format,
            "detail": f"Article must have 📝原文 / ✨润色后 / 🔧主要修改 / 💡改进说明 sections. Found: {has_article_format}"
        })

        # Check 10: Article polished section removes redundant expressions
        polished_article_section = ""
        try:
            match = re.search(r'✨.*?润色后[：:]\s*(.*?)(?=🔧|$)', article_content, re.DOTALL)
            if match:
                polished_article_section = match.group(1)
        except Exception:
            polished_article_section = article_content

        section_to_check = polished_article_section if polished_article_section else article_content
        # Check that specific redundant patterns from the original are removed or greatly reduced
        redundant_patterns = [
            r'非常非常的',
            r'一些(.{0,3})问题和困难',
            r'各种各样的',
            r'很复杂的系统性',  # This phrase itself might be ok, but over-use
        ]
        # Check that verbose connectors are reduced
        verbose_connectors = ['然后我', '然后是', '最后是']
        connector_count = sum(section_to_check.count(vc) for vc in verbose_connectors)
        reduced_verbosity = connector_count <= 1

        # Also check "非常非常" (double intensifier) is removed
        no_double_intensifier = '非常非常' not in section_to_check
        
        article_improved = reduced_verbosity or no_double_intensifier
        checks.append({
            "name": "article_removes_redundant_expressions",
            "passed": article_improved,
            "detail": f"Article must remove redundant expressions like '非常非常的', verbose connectors. Double-intensifier removed:{no_double_intensifier}, Reduced verbose connectors (count={connector_count}):{reduced_verbosity}"
        })

        # Check 11: Article has changes explanation (修改说明 lists specific changes)
        changes_section = ""
        try:
            match = re.search(r'🔧.*?主要修改[：:]\s*(.*?)(?=💡|$)', article_content, re.DOTALL)
            if match:
                changes_section = match.group(1)
        except Exception:
            changes_section = article_content

        # Changes section should have at least 2 bullet points
        change_bullets = [l for l in changes_section.split('\n') if l.strip().startswith('-') or l.strip().startswith('•') or re.match(r'^\d+[.、]', l.strip())]
        has_sufficient_changes = len(change_bullets) >= 2
        checks.append({
            "name": "article_changes_section_has_specific_bullets",
            "passed": has_sufficient_changes,
            "detail": f"Changes section must list >= 2 specific modification points. Found {len(change_bullets)} bullet points."
        })

    else:
        for name in ["article_has_four_section_emoji_format", "article_removes_redundant_expressions",
                     "article_changes_section_has_specific_bullets"]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})

    # =========================================================
    # SCORING
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)