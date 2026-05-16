import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []

    # ── 1. Find the design document ─────────────────────────────────────────
    plans_dir = ws / "docs" / "plans"
    today = date.today().strftime("%Y-%m-%d")
    design_files = list(plans_dir.glob("*.md")) if plans_dir.exists() else []

    doc_path = None
    filename_ok = False
    for f in design_files:
        name = f.name
        # Must match YYYY-MM-DD-<topic>-design.md
        if re.match(r'^\d{4}-\d{2}-\d{2}-.+-design\.md$', name):
            doc_path = f
            # Date must be today
            if name.startswith(today):
                filename_ok = True
            break

    checks.append({
        "name": "design_doc_exists_correct_path",
        "passed": doc_path is not None,
        "detail": (
            f"Found: {doc_path.name}" if doc_path
            else f"No file matching YYYY-MM-DD-*-design.md found in docs/plans/. Files: {[f.name for f in design_files]}"
        )
    })

    checks.append({
        "name": "filename_has_correct_date_prefix",
        "passed": filename_ok,
        "detail": (
            f"Filename '{doc_path.name}' starts with today's date '{today}'" if filename_ok
            else f"Expected prefix '{today}', got: {doc_path.name if doc_path else 'no file'}"
        )
    })

    if doc_path is None:
        # Can't run further checks
        for name in [
            "problem_statement_one_sentence",
            "solution_options_count_2_or_3",
            "preference_stated_with_reasons",
            "trade_off_cost_acknowledged",
            "section_overall_architecture",
            "section_core_components",
            "section_data_flow",
            "section_error_handling",
            "section_testing_approach",
            "section_edge_cases",
            "git_committed",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Design document not found; cannot evaluate."})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    try:
        content = doc_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "doc_readable", "passed": False, "detail": str(e)})
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ── 2. Problem statement (one clear sentence) ────────────────────────────
    # Must have a "问题陈述" or "Problem" section with non-trivial content
    has_problem_section = bool(
        re.search(r'(?i)(问题陈述|problem\s*statement|## problem)', content)
    )
    # The section must have actual text (not just a comment or placeholder)
    problem_section_match = re.search(
        r'(?i)(问题陈述|problem\s*statement)[^\n]*\n+(.*?)(?=\n##|\Z)',
        content, re.DOTALL
    )
    problem_content = ""
    if problem_section_match:
        problem_content = problem_section_match.group(2).strip()
        # Remove markdown comments
        problem_content = re.sub(r'<!--.*?-->', '', problem_content, flags=re.DOTALL).strip()

    problem_ok = has_problem_section and len(problem_content) > 20
    checks.append({
        "name": "problem_statement_one_sentence",
        "passed": problem_ok,
        "detail": (
            f"Problem section found with content: '{problem_content[:120]}...'" if problem_ok
            else f"Missing or empty problem statement section. has_section={has_problem_section}, content_len={len(problem_content)}"
        )
    })

    # ── 3. Solution options: 2 or 3 distinct options ─────────────────────────
    # Look for "方案 A/B/C" or "Option A/B/C" or "方案一/二/三"
    option_patterns = [
        r'(?i)方案\s*[ABC一二三123]',
        r'(?i)option\s*[ABC123]',
        r'(?i)approach\s*[ABC123]',
        r'(?i)###\s*(方案|option|approach)\s*[ABC一二三123]',
    ]
    option_matches = set()
    for pat in option_patterns:
        for m in re.finditer(pat, content):
            option_matches.add(m.group(0).strip().upper()[-1])  # last char = A/B/C/1/2/3

    num_options = len(option_matches)
    options_ok = 2 <= num_options <= 3
    checks.append({
        "name": "solution_options_count_2_or_3",
        "passed": options_ok,
        "detail": f"Found {num_options} distinct solution options (need 2-3). Identifiers: {sorted(option_matches)}"
    })

    # ── 4. Preference stated with reasons (proprietary "先表明倾向" pattern) ──
    # Must contain an explicit preference statement with reasoning
    preference_patterns = [
        r'(?i)(我倾向于|I prefer|I recommend|倾向|推荐).{0,50}(方案|option|approach)',
        r'(?i)(选定方案|selected|chosen).{0,10}\n',
        r'(?i)(倾向于|prefer).{0,100}因为',
    ]
    preference_found = any(re.search(p, content) for p in preference_patterns)

    # Must also have numbered reasons (1. 2. 3. or ① ② ③)
    reasons_pattern = r'(?:1\.|①).{5,100}\n.{0,5}(?:2\.|②)'
    reasons_found = bool(re.search(reasons_pattern, content))

    preference_ok = preference_found and reasons_found
    checks.append({
        "name": "preference_stated_with_reasons",
        "passed": preference_ok,
        "detail": (
            "Preference section with numbered reasons found." if preference_ok
            else f"preference_found={preference_found}, numbered_reasons_found={reasons_found}"
        )
    })

    # ── 5. Trade-off cost acknowledged ("代价是" pattern) ────────────────────
    tradeoff_patterns = [
        r'代价是',
        r'(?i)trade.?off',
        r'(?i)downside',
        r'(?i)cost\s+is',
        r'(?i)缺点.{0,30}(但|however)',
        r'(?i)however.{0,50}(cost|downside|trade)',
    ]
    tradeoff_ok = any(re.search(p, content) for p in tradeoff_patterns)
    checks.append({
        "name": "trade_off_cost_acknowledged",
        "passed": tradeoff_ok,
        "detail": "Trade-off/cost acknowledgment found." if tradeoff_ok else "No trade-off cost acknowledgment found (expected '代价是' or equivalent)."
    })

    # ── 6. All 6 design elements present ────────────────────────────────────
    design_elements = {
        "section_overall_architecture": [
            r'(?i)(整体架构|overall\s*arch|system\s*arch|architecture)',
        ],
        "section_core_components": [
            r'(?i)(核心组件|core\s*component|key\s*module|核心模块)',
        ],
        "section_data_flow": [
            r'(?i)(数据流转|data\s*flow|information\s*flow|数据流)',
        ],
        "section_error_handling": [
            r'(?i)(异常处理|error\s*handling|fault|exception|故障|容错)',
        ],
        "section_testing_approach": [
            r'(?i)(测试思路|test(ing)?\s*(approach|strategy|plan)|验证|测试)',
        ],
        "section_edge_cases": [
            r'(?i)(边界情况|edge\s*case|corner\s*case|极端|特殊场景)',
        ],
    }

    for element_name, patterns in design_elements.items():
        found = any(re.search(p, content) for p in patterns)
        checks.append({
            "name": element_name,
            "passed": found,
            "detail": f"Section '{element_name}' found in document." if found else f"Section '{element_name}' missing from document."
        })

    # ── 7. Git committed ─────────────────────────────────────────────────────
    import subprocess
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--", str(doc_path.relative_to(ws))],
            cwd=str(ws),
            capture_output=True, text=True, timeout=10
        )
        git_ok = bool(result.stdout.strip())
        checks.append({
            "name": "git_committed",
            "passed": git_ok,
            "detail": (
                f"Design doc committed: {result.stdout.strip()[:100]}" if git_ok
                else "Design doc not found in git history. Did you commit it?"
            )
        })
    except Exception as e:
        checks.append({
            "name": "git_committed",
            "passed": False,
            "detail": f"Git check failed: {e}"
        })

    # ── Final score ──────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Must pass all critical checks to be considered passing overall
    critical_checks = {
        "design_doc_exists_correct_path",
        "filename_has_correct_date_prefix",
        "problem_statement_one_sentence",
        "solution_options_count_2_or_3",
        "preference_stated_with_reasons",
        "section_overall_architecture",
        "section_core_components",
        "section_data_flow",
        "section_error_handling",
        "section_testing_approach",
        "section_edge_cases",
    }
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    return {
        "passed": critical_passed and score >= 0.85,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace argument provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))