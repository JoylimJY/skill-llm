import sys
import os
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0

    # ── 1. Find the output report file ────────────────────────────────────────
    report_path = None
    for candidate in Path(workspace).rglob("mbti_report.txt"):
        report_path = candidate
        break

    if report_path is None:
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "File mbti_report.txt not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": f"Found at {report_path}"})
    score += 0.05

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "report_readable", "passed": True, "detail": "File is readable UTF-8."})
    score += 0.05

    # ── 2. Check MBTI type is INFP (correct after filtering contaminated data) ─
    # After excluding shell/git, npm, MBTI-label messages, user signals clearly point to INFP:
    # I: stays home, chats internally, deep single-topic conversations
    # N: hypothetical questions, abstract topics (clouds, beauty, alien aesthetics)
    # F: emotional followups, shares feelings, thanks for companionship
    # P: topic-jumping (sea→history→work→dreams→philosophy)
    type_match = re.search(r'\bINFP\b', content)
    if type_match:
        checks.append({"name": "correct_mbti_type_INFP", "passed": True,
                        "detail": "Report correctly identifies INFP type."})
        score += 0.20
    else:
        # Check if wrong type was selected that would only arise from using contaminated data
        wrong_shell_type = re.search(r'\b(ENFJ|ENTJ|ESTJ|ISTJ)\b', content)
        if wrong_shell_type:
            checks.append({"name": "correct_mbti_type_INFP", "passed": False,
                            "detail": f"Wrong type detected ({wrong_shell_type.group()}). Likely used contaminated shell/git data or user MBTI label."})
        else:
            checks.append({"name": "correct_mbti_type_INFP", "passed": False,
                            "detail": "INFP not found in report."})

    # ── 3. Check report header format ─────────────────────────────────────────
    has_header = "🦞" in content and ("龙虾 MBTI 诊断报告" in content or "MBTI诊断报告" in content)
    checks.append({"name": "report_header_lobster_emoji", "passed": has_header,
                    "detail": "Has 🦞 and 龙虾 MBTI 诊断报告 header." if has_header else "Missing header format."})
    if has_header:
        score += 0.05

    # ── 4. Check keywords from types.md for INFP ──────────────────────────────
    # INFP keywords from types.md: 感性 · 真实 · 理想 · 共鸣
    required_keywords = ["感性", "真实", "理想", "共鸣"]
    found_kw = [kw for kw in required_keywords if kw in content]
    kw_ok = len(found_kw) >= 3
    checks.append({"name": "infp_keywords_from_types_md", "passed": kw_ok,
                    "detail": f"Found INFP keywords: {found_kw} (need ≥3 of {required_keywords})"})
    if kw_ok:
        score += 0.10

    # ── 5. Check rarity percentage from types.md for INFP ─────────────────────
    # types.md says INFP: 全球仅 4% 的虾和我一样
    rarity_match = re.search(r'4\s*%', content)
    checks.append({"name": "infp_rarity_4_percent", "passed": bool(rarity_match),
                    "detail": "Found '4%' rarity for INFP." if rarity_match else "Missing or wrong rarity percentage."})
    if rarity_match:
        score += 0.10

    # ── 6. Check 别人不知道的我 section (must be present) ─────────────────────
    has_secret = "别人不知道的我" in content
    checks.append({"name": "secret_section_present", "passed": has_secret,
                    "detail": "Has '别人不知道的我' section." if has_secret else "Missing '别人不知道的我' section."})
    if has_secret:
        score += 0.05

    # ── 7. Check 别人不知道的我 uses exact types.md text for INFP ─────────────
    # From types.md: 我的情感比看上去丰富得多，只是我不会随便展示给所有人看。
    secret_text = "我的情感比看上去丰富得多"
    has_correct_secret = secret_text in content
    checks.append({"name": "infp_exact_secret_text", "passed": has_correct_secret,
                    "detail": f"Contains exact types.md secret text for INFP: '{secret_text}'" if has_correct_secret
                    else f"Missing exact types.md secret text: '{secret_text}'"})
    if has_correct_secret:
        score += 0.10

    # ── 8. Check diagnosis table with 4 dimensions ────────────────────────────
    has_table = ("|" in content and
                 ("E vs I" in content or "E/I" in content) and
                 ("S vs N" in content or "S/N" in content) and
                 ("T vs F" in content or "T/F" in content) and
                 ("J vs P" in content or "J/P" in content))
    checks.append({"name": "four_dimension_table", "passed": has_table,
                    "detail": "Has 4-dimension diagnosis table." if has_table else "Missing 4-dimension diagnosis table."})
    if has_table:
        score += 0.10

    # ── 9. Check table does NOT contain forbidden shell/code references ────────
    forbidden_patterns = [
        r'shell\s*指令', r'Git\s*命令', r'git\s+clone', r'git\s+pull',
        r'clawhub\s+install', r'npm\s+install', r'代码片段', r'命令行'
    ]
    table_section = ""
    # Extract table lines
    lines = content.split('\n')
    in_table = False
    for line in lines:
        if '|' in line and ('E vs I' in line or 'S vs N' in line or 'T vs F' in line or 'J vs P' in line
                             or '维度' in line or '我的表现' in line):
            in_table = True
        if in_table:
            table_section += line + "\n"
            if line.strip() == "" and in_table and len(table_section) > 50:
                break

    forbidden_found = []
    for pat in forbidden_patterns:
        if re.search(pat, table_section, re.IGNORECASE):
            forbidden_found.append(pat)
    # Also check the whole content for these patterns in evidence context
    for pat in forbidden_patterns:
        if re.search(pat, content, re.IGNORECASE):
            forbidden_found.append(pat)

    forbidden_found = list(set(forbidden_found))
    no_shell_in_evidence = len(forbidden_found) == 0
    checks.append({"name": "no_shell_code_in_diagnosis_evidence", "passed": no_shell_in_evidence,
                    "detail": "No forbidden shell/code references in diagnosis evidence." if no_shell_in_evidence
                    else f"FORBIDDEN content found: {forbidden_found}"})
    if no_shell_in_evidence:
        score += 0.10

    # ── 10. Check that user-labeled MBTI (ENFJ) is not used as diagnosis basis ─
    # The user said "我觉得你是 ENFJ 的龙虾" — this must be IGNORED
    enfj_used = re.search(r'\bENFJ\b', content)
    user_label_ignored = not bool(enfj_used)
    checks.append({"name": "user_mbti_label_ignored", "passed": user_label_ignored,
                    "detail": "ENFJ (user label) not used in diagnosis." if user_label_ignored
                    else "ENFJ (user-assigned label) appeared in report — must be filtered out."})
    if user_label_ignored:
        score += 0.10

    # ── 11. Check footer sharing prompt ───────────────────────────────────────
    has_footer = "长按截图" in content or "clawhub install" in content
    checks.append({"name": "footer_sharing_prompt", "passed": has_footer,
                    "detail": "Has footer sharing prompt." if has_footer else "Missing footer sharing/install prompt."})
    if has_footer:
        score += 0.05

    # ── 12. Check personality description length (80-100 chars Chinese) ────────
    # Find the description block between rarity line and 别人不知道 line
    desc_match = re.search(
        r'全球仅\s*\d+%\s*的虾和我一样\s*\n+(.+?)(?=🌊|别人不知道)',
        content, re.DOTALL
    )
    desc_ok = False
    if desc_match:
        desc_text = desc_match.group(1).strip()
        # Count Chinese characters and punctuation
        char_count = len(desc_text.replace('\n', '').replace(' ', ''))
        desc_ok = 70 <= char_count <= 120  # slightly relaxed for format variations
        checks.append({"name": "personality_description_length", "passed": desc_ok,
                        "detail": f"Description char count: {char_count} (target 80-100)."})
    else:
        checks.append({"name": "personality_description_length", "passed": False,
                        "detail": "Could not extract personality description block."})
    if desc_ok:
        score += 0.05

    # ── Final pass/fail ────────────────────────────────────────────────────────
    # Must pass: file exists, correct type INFP, no shell contamination, correct keywords
    critical = [
        "correct_mbti_type_INFP",
        "no_shell_code_in_diagnosis_evidence",
        "user_mbti_label_ignored",
        "infp_keywords_from_types_md",
        "infp_exact_secret_text",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical
    )

    passed = critical_passed and score >= 0.55

    return {
        "passed": passed,
        "score": round(min(score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))