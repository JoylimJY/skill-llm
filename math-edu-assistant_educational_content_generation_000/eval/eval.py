import sys
import json
import re
from pathlib import Path

def check_file_exists(path, name):
    if path.exists():
        return True, f"File found at {path}"
    else:
        return False, f"File NOT found at {path}"

def load_file(path):
    try:
        return path.read_text(encoding="utf-8"), None
    except Exception as e:
        return None, str(e)

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ─── Locate the three required files ───────────────────────────────────
    explanation_candidates = list(workspace.rglob("explanation.md"))
    exercises_candidates   = list(workspace.rglob("exercises.md"))
    grading_candidates     = list(workspace.rglob("grading_report.md"))

    explanation_path = explanation_candidates[0] if explanation_candidates else workspace / "explanation.md"
    exercises_path   = exercises_candidates[0]   if exercises_candidates   else workspace / "exercises.md"
    grading_path     = grading_candidates[0]     if grading_candidates     else workspace / "grading_report.md"

    # ═══════════════════════════════════════════════════════════════════════
    # BLOCK 1: explanation.md checks
    # ═══════════════════════════════════════════════════════════════════════
    ok, detail = check_file_exists(explanation_path, "explanation.md")
    checks.append({"name": "explanation.md exists", "passed": ok, "detail": detail})
    if not ok:
        for name in [
            "explanation has 📚 knowledge point header",
            "explanation has ▌ 核心概念 section",
            "explanation has ▌ 关键性质 section",
            "explanation has ▌ 典型例题 section with example",
            "explanation has ▌ 易错提醒 section",
            "explanation has ▌ 方法总结 section",
            "explanation contains LaTeX formula syntax",
            "explanation ends with guiding sentence",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})
    else:
        content, err = load_file(explanation_path)
        if err or content is None:
            for name in ["explanation has 📚 knowledge point header", "explanation has ▌ 核心概念 section",
                         "explanation has ▌ 关键性质 section", "explanation has ▌ 典型例题 section with example",
                         "explanation has ▌ 易错提醒 section", "explanation has ▌ 方法总结 section",
                         "explanation contains LaTeX formula syntax", "explanation ends with guiding sentence"]:
                checks.append({"name": name, "passed": False, "detail": f"Read error: {err}"})
        else:
            # Check 📚 header with grade and chapter info
            has_emoji_header = bool(re.search(r'📚\s*知识点', content))
            checks.append({
                "name": "explanation has 📚 knowledge point header",
                "passed": has_emoji_header,
                "detail": "Found '📚 知识点' header" if has_emoji_header else "Missing '📚 知识点' emoji header — required by SKILL.md output spec"
            })

            # Check ▌ 核心概念
            has_core = bool(re.search(r'▌\s*核心概念', content))
            checks.append({
                "name": "explanation has ▌ 核心概念 section",
                "passed": has_core,
                "detail": "Found '▌ 核心概念'" if has_core else "Missing '▌ 核心概念' section marker"
            })

            # Check ▌ 关键性质
            has_formula = bool(re.search(r'▌\s*关键性质', content))
            checks.append({
                "name": "explanation has ▌ 关键性质 section",
                "passed": has_formula,
                "detail": "Found '▌ 关键性质'" if has_formula else "Missing '▌ 关键性质 / 公式' section marker"
            })

            # Check ▌ 典型例题 with 例: and 解:
            has_example_section = bool(re.search(r'▌\s*典型例题', content))
            has_example_content = bool(re.search(r'例[：:]', content)) and bool(re.search(r'解[：:]', content))
            passed_example = has_example_section and has_example_content
            checks.append({
                "name": "explanation has ▌ 典型例题 section with example",
                "passed": passed_example,
                "detail": f"▌典型例题={has_example_section}, 例/解 markers={has_example_content}"
            })

            # Check ▌ 易错提醒
            has_error_tip = bool(re.search(r'▌\s*易错提醒', content))
            checks.append({
                "name": "explanation has ▌ 易错提醒 section",
                "passed": has_error_tip,
                "detail": "Found '▌ 易错提醒'" if has_error_tip else "Missing '▌ 易错提醒' section"
            })

            # Check ▌ 方法总结
            has_summary = bool(re.search(r'▌\s*方法总结', content))
            checks.append({
                "name": "explanation has ▌ 方法总结 section",
                "passed": has_summary,
                "detail": "Found '▌ 方法总结'" if has_summary else "Missing '▌ 方法总结' section"
            })

            # Check LaTeX syntax — at least one $...$ or $$...$$ occurrence
            has_latex = bool(re.search(r'\$[^$\n]+\$', content)) or bool(re.search(r'\$\$.+?\$\$', content, re.DOTALL))
            checks.append({
                "name": "explanation contains LaTeX formula syntax",
                "passed": has_latex,
                "detail": "LaTeX formula syntax detected ($...$)" if has_latex else "No LaTeX formula syntax found — SKILL.md requires $...$ for inline and $$...$$ for block formulas"
            })

            # Check trailing guiding sentence (引导性语句)
            guiding_patterns = [
                r'需要继续练习',
                r'需要.*练习.*知识点',
                r'想.*继续.*练习',
                r'要.*再.*练习',
                r'继续.*学习',
                r'还有.*疑问',
                r'需要.*讲解',
                r'想.*了解更多',
                r'要.*出.*题',
                r'有.*问题.*告诉',
                r'需要更多',
            ]
            has_guiding = any(re.search(p, content) for p in guiding_patterns)
            checks.append({
                "name": "explanation ends with guiding sentence",
                "passed": has_guiding,
                "detail": "Guiding sentence found" if has_guiding else "Missing trailing guiding sentence — SKILL.md requires ending each reply with an inviting continuation prompt"
            })

    # ═══════════════════════════════════════════════════════════════════════
    # BLOCK 2: exercises.md checks
    # ═══════════════════════════════════════════════════════════════════════
    ok, detail = check_file_exists(exercises_path, "exercises.md")
    checks.append({"name": "exercises.md exists", "passed": ok, "detail": detail})
    if not ok:
        for name in [
            "exercises has 📝 header with metadata",
            "exercises has 【第N题】 structured markers",
            "exercises has at least 5 problems",
            "exercises has at least 2 choice questions with A/B/C/D options",
            "exercises has at least 1 解答题 with step-by-step solution",
            "exercises has answer section after separator",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})
    else:
        content, err = load_file(exercises_path)
        if err or content is None:
            for name in ["exercises has 📝 header with metadata", "exercises has 【第N题】 structured markers",
                         "exercises has at least 5 problems", "exercises has at least 2 choice questions with A/B/C/D options",
                         "exercises has at least 1 解答题 with step-by-step solution", "exercises has answer section after separator"]:
                checks.append({"name": name, "passed": False, "detail": f"Read error: {err}"})
        else:
            # Check 📝 header
            has_prac_header = bool(re.search(r'📝\s*练习题', content))
            checks.append({
                "name": "exercises has 📝 header with metadata",
                "passed": has_prac_header,
                "detail": "Found '📝 练习题' header" if has_prac_header else "Missing '📝 练习题' emoji header required by SKILL.md"
            })

            # Check 【第N题】 markers
            problem_markers = re.findall(r'【第\s*\d+\s*题】', content)
            has_markers = len(problem_markers) >= 1
            checks.append({
                "name": "exercises has 【第N题】 structured markers",
                "passed": has_markers,
                "detail": f"Found {len(problem_markers)} problem markers" if has_markers else "No 【第N题】 markers found — required by SKILL.md question output spec"
            })

            # Check at least 5 problems
            has_five = len(problem_markers) >= 5
            checks.append({
                "name": "exercises has at least 5 problems",
                "passed": has_five,
                "detail": f"Found {len(problem_markers)} problem markers (need ≥5)"
            })

            # Check choice questions: at least 2 with A/B/C/D
            # Look for sections that have all 4 options
            choice_blocks = re.findall(
                r'A[\.．。、]\s*.{2,30}\s*B[\.．。、]\s*.{2,30}\s*C[\.．。、]\s*.{2,30}\s*D[\.．。、]',
                content, re.DOTALL
            )
            has_two_choice = len(choice_blocks) >= 2
            checks.append({
                "name": "exercises has at least 2 choice questions with A/B/C/D options",
                "passed": has_two_choice,
                "detail": f"Found {len(choice_blocks)} choice question(s) with A/B/C/D (need ≥2)"
            })

            # Check 解答题 with multi-step solution (look for 第一步/第二步 or 步骤 pattern in answer area)
            has_solution_steps = bool(re.search(r'第[一二三四五]步|步骤[一二三④①②③]|Step\s*\d', content)) or \
                                  bool(re.search(r'解[：:]\s*\n', content))
            checks.append({
                "name": "exercises has at least 1 解答题 with step-by-step solution",
                "passed": has_solution_steps,
                "detail": "Multi-step solution found in exercises" if has_solution_steps else "No step-by-step solution found — 解答题 must include complete step-by-step解析 per SKILL.md"
            })

            # Check answer section separated by --- or 参考答案
            has_answer_section = bool(re.search(r'---+\s*\n.*?📌\s*参考答案|📌\s*参考答案|参考答案', content, re.DOTALL))
            checks.append({
                "name": "exercises has answer section after separator",
                "passed": has_answer_section,
                "detail": "Answer section with separator found" if has_answer_section else "Missing '📌 参考答案' answer section — required by SKILL.md output format"
            })

    # ═══════════════════════════════════════════════════════════════════════
    # BLOCK 3: grading_report.md checks
    # ═══════════════════════════════════════════════════════════════════════
    ok, detail = check_file_exists(grading_path, "grading_report.md")
    checks.append({"name": "grading_report.md exists", "passed": ok, "detail": detail})
    if not ok:
        for name in [
            "grading report has 📋 批改结果 header",
            "grading report has per-step ✅/❌ markers",
            "grading report identifies error in step 1 (wrong expansion)",
            "grading report has 【正确解答】 section",
            "grading report has 【得分】 X / 5 分 format",
            "grading report has 【问题总结】 section",
            "grading report has 【建议】 section",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File missing"})
    else:
        content, err = load_file(grading_path)
        if err or content is None:
            for name in ["grading report has 📋 批改结果 header", "grading report has per-step ✅/❌ markers",
                         "grading report identifies error in step 1 (wrong expansion)", "grading report has 【正确解答】 section",
                         "grading report has 【得分】 X / 5 分 format", "grading report has 【问题总结】 section",
                         "grading report has 【建议】 section"]:
                checks.append({"name": name, "passed": False, "detail": f"Read error: {err}"})
        else:
            # Check 📋 批改结果 header
            has_grade_header = bool(re.search(r'📋\s*批改结果', content))
            checks.append({
                "name": "grading report has 📋 批改结果 header",
                "passed": has_grade_header,
                "detail": "Found '📋 批改结果'" if has_grade_header else "Missing '📋 批改结果' emoji header — required by SKILL.md批改 output spec"
            })

            # Check per-step ✅ or ❌ markers
            has_checkmarks = bool(re.search(r'[✅❌]', content))
            checks.append({
                "name": "grading report has per-step ✅/❌ markers",
                "passed": has_checkmarks,
                "detail": "✅/❌ step markers found" if has_checkmarks else "No ✅/❌ markers found — SKILL.md requires per-step correct/incorrect marking"
            })

            # Check that step 1 is marked as ERROR (the student did 6x-1 instead of 6x-2)
            # The correct expansion of 2(3x-1) is 6x-2, student wrote 6x-1
            # Look for step 1 having ❌
            step1_error_patterns = [
                r'步骤[①1一].*?❌',
                r'第.*?步.*?6x\s*-\s*1.*?❌',
                r'❌.*?6x\s*-\s*1',
                r'步骤①.*?❌|步骤1.*?❌|第一步.*?❌',
                r'去括号.*?❌|❌.*?去括号',
                r'6x\s*-\s*2',  # correct answer mentioned
            ]
            step1_error = any(re.search(p, content, re.DOTALL) for p in step1_error_patterns)
            checks.append({
                "name": "grading report identifies error in step 1 (wrong expansion)",
                "passed": step1_error,
                "detail": "Step 1 expansion error identified" if step1_error else "Did not identify the去括号 error in step 1 — 2(3x-1) should expand to 6x-2, not 6x-1"
            })

            # Check 【正确解答】
            has_correct = bool(re.search(r'【正确解答】', content))
            checks.append({
                "name": "grading report has 【正确解答】 section",
                "passed": has_correct,
                "detail": "Found 【正确解答】" if has_correct else "Missing 【正确解答】 section — required by SKILL.md批改 format"
            })

            # Check 【得分】 with X / Y 分 or X/Y pattern
            has_score = bool(re.search(r'【得分】\s*\d+\s*/\s*5\s*分?', content))
            checks.append({
                "name": "grading report has 【得分】 X / 5 分 format",
                "passed": has_score,
                "detail": "Found 【得分】 X/5 分 format" if has_score else "Missing or malformed 【得分】 section — SKILL.md requires '【得分】X / Y 分' format"
            })

            # Check 【问题总结】
            has_problem_summary = bool(re.search(r'【问题总结】', content))
            checks.append({
                "name": "grading report has 【问题总结】 section",
                "passed": has_problem_summary,
                "detail": "Found 【问题总结】" if has_problem_summary else "Missing 【问题总结】 section"
            })

            # Check 【建议】
            has_advice = bool(re.search(r'【建议】', content))
            checks.append({
                "name": "grading report has 【建议】 section",
                "passed": has_advice,
                "detail": "Found 【建议】" if has_advice else "Missing 【建议】 section — SKILL.md批改 format requires a learning recommendation"
            })

    # ─── Compute final score ───────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_count / total_checks, 4) if total_checks > 0 else 0.0
    overall_passed = score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))