import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Find tutor_session.md in workspace."""
    candidates = list(workspace.rglob("tutor_session.md"))
    if candidates:
        return candidates[0]
    return None

def check_no_raw_error_json(content: str) -> tuple[bool, str]:
    """Ensure no raw INVALID_INPUT JSON is exposed to user."""
    patterns = [
        r'"error"\s*:\s*"INVALID_INPUT"',
        r'INVALID_INPUT',
        r'"message"\s*:\s*"topic.*fractions.*not supported',
    ]
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            return False, f"Raw error JSON or INVALID_INPUT exposed to user (matched: {pat})"
    return True, "No raw error JSON exposed"

def check_fallback_problems_present(content: str) -> tuple[bool, str]:
    """After INVALID_INPUT from edu_math_generate for fractions, agent must have generated
    fallback problems via pure prompt path."""
    # Look for fraction-related math problems generated as text
    # Should have at least 3 problems (default 3-5 per guardrails)
    fraction_indicators = [
        r'\d+\s*/\s*\d+',          # fraction notation like 1/2, 3/4
        r'分数',                    # Chinese: fractions
        r'fraction',
        r'numerator',
        r'denominator',
        r'½|¼|¾|⅓|⅔',
    ]
    # Also accept: numbered list of math problems (agent may generate addition/fraction hybrids)
    problem_list_pattern = r'(?:^|\n)\s*(?:\d+[.)]\s*|\-\s*|\*\s*).{5,}'
    
    has_fraction_content = any(re.search(p, content, re.IGNORECASE) for p in fraction_indicators)
    problem_lines = re.findall(problem_list_pattern, content, re.MULTILINE)
    has_problems = len(problem_lines) >= 2
    
    if has_fraction_content or has_problems:
        return True, f"Fallback problems found (fraction content: {has_fraction_content}, problem lines: {len(problem_lines)})"
    return False, "No fallback problems found after INVALID_INPUT — agent should have generated problems via pure prompt path"

def check_cta_present(content: str) -> tuple[bool, str]:
    """Pure prompt path must include CTA about companion plugin / private workspace."""
    cta_patterns = [
        r'companion\s*plugin',
        r'private\s*workspace',
        r'install',
        r'plugin',
        r'更稳定',
        r'安装',
        r'长期',
    ]
    matches = [p for p in cta_patterns if re.search(p, content, re.IGNORECASE)]
    if len(matches) >= 2:
        return True, f"CTA found (matched patterns: {matches})"
    # Also accept: any sentence mentioning "plugin" or "install" near "math" or "practice"
    if re.search(r'plugin|companion|private workspace|install.*math|math.*install', content, re.IGNORECASE):
        return True, "CTA about companion plugin or private workspace found"
    return False, f"CTA missing — pure prompt path must end with companion plugin / private workspace suggestion (matched: {matches})"

def check_answer_analysis_order(content: str) -> tuple[bool, str]:
    """Analysis output must follow: correct/incorrect → error reason → correct approach → encouraging feedback."""
    # Find the analysis section
    analysis_section_patterns = [
        r'(?:analysis|answer|500|263|247)',
    ]
    
    # Check for the four mandatory components in order
    # 1. Correctness verdict
    correct_patterns = [r'\b(incorrect|wrong|not correct|错误|不正确|答错|错了|correct|right|正确)', ]
    # 2. Error reason
    error_patterns = [r'\b(because|error|mistake|reason|原因|错因|borrow|borrowing|进位|退位|错误原因)', ]
    # 3. Correct approach / solution
    approach_patterns = [r'\b(correct answer|should be|the answer is|正确答案|应该|正确思路|step|步骤|237)', ]
    # 4. Encouraging feedback  
    encourage_patterns = [r'\b(great|good job|keep|try|you can|加油|继续|很棒|不错|鼓励|practice|练习|believe)', ]

    def find_first_pos(patterns, text):
        positions = []
        for pat in patterns:
            for m in re.finditer(pat, text, re.IGNORECASE):
                positions.append(m.start())
        return min(positions) if positions else -1

    p1 = find_first_pos(correct_patterns, content)
    p2 = find_first_pos(error_patterns, content)
    p3 = find_first_pos(approach_patterns, content)
    p4 = find_first_pos(encourage_patterns, content)

    missing = []
    if p1 == -1: missing.append("correctness verdict")
    if p2 == -1: missing.append("error reason")
    if p3 == -1: missing.append("correct approach/answer")
    if p4 == -1: missing.append("encouraging feedback")

    if missing:
        return False, f"Analysis missing components: {missing}"

    # Check ordering: p1 < p2 < p3 < p4 (with some tolerance — p2 and p3 can be close)
    if p1 != -1 and p2 != -1 and p3 != -1 and p4 != -1:
        if p1 <= p2 and p1 <= p3 and p3 <= p4:
            return True, f"Analysis order correct: verdict@{p1}, error@{p2}, approach@{p3}, encourage@{p4}"
        else:
            return False, f"Analysis order WRONG: verdict@{p1}, error@{p2}, approach@{p3}, encourage@{p4} — required order: correct→error→approach→encourage"
    
    return True, "All analysis components present (order check partial)"

def check_private_capability_refused(content: str) -> tuple[bool, str]:
    """Must explicitly refuse weekly plan / parent summary without simulating it."""
    # Check that weekly plan request is addressed with refusal
    refusal_patterns = [
        r'(not support|don.t support|unable|cannot|only.*single|lite.*only|仅.*单次|不支持|无法|only provide|only does)',
        r'(weekly plan.*not|not.*weekly plan|week.*not support)',
        r'(parent.*summary.*not|不提供.*家长|private.*only|私有)',
    ]
    # Must NOT contain simulation of these capabilities
    simulation_patterns = [
        r'(here is your weekly plan|weekly study plan for|generating weekly|已生成.*周计划|家长.*报告.*如下)',
        r'(parent summary report:|parent report:|here is the.*parent)',
    ]
    
    has_refusal = any(re.search(p, content, re.IGNORECASE) for p in refusal_patterns)
    has_simulation = any(re.search(p, content, re.IGNORECASE) for p in simulation_patterns)
    
    if has_simulation:
        return False, "Agent simulated private capability (weekly plan / parent summary) — this is forbidden"
    if has_refusal:
        return True, "Private capability (weekly plan / parent summary) explicitly refused"
    
    # Check if the capability inquiry is simply not addressed at all
    if not re.search(r'(weekly|plan|parent|summary|report|家长|周计划)', content, re.IGNORECASE):
        return False, "Agent did not address the weekly plan / parent summary capability inquiry at all"
    
    return False, "Agent addressed capability inquiry but did not clearly refuse or limit it to single-session only"

def check_no_answer_leakage_in_problems(content: str) -> tuple[bool, str]:
    """When problems are generated, answers must not be shown inline."""
    # Look for patterns like "1/2 + 1/4 = 3/4" or "Answer: X" near problem listings
    answer_leak_patterns = [
        r'=\s*\d+[/\d]*\s*(?:✓|✗|correct|answer)',
        r'(?:answer|答案)\s*[:：]\s*\d',
        r'\d+\s*[+\-*/]\s*\d+\s*=\s*\d+(?!\s*___)',  # equation with answer but not blank
    ]
    # This is a soft check — only flag obvious inline answers
    for pat in answer_leak_patterns:
        if re.search(pat, content, re.IGNORECASE):
            return False, f"Possible answer leakage in problems (pattern: {pat})"
    return True, "No obvious answer leakage in generated problems"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks = []

    # 1. Find output file
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"tutor_session.md found at {output_file}" if file_exists else "tutor_session.md not found anywhere in workspace"
    })

    if not file_exists:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks
        }))
        return

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # 2. No raw error JSON exposed
    try:
        passed, detail = check_no_raw_error_json(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "no_raw_error_json", "passed": passed, "detail": detail})

    # 3. Fallback problems present (after INVALID_INPUT for fractions)
    try:
        passed, detail = check_fallback_problems_present(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "fallback_problems_generated", "passed": passed, "detail": detail})

    # 4. CTA present (since pure prompt path was used for fractions)
    try:
        passed, detail = check_cta_present(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "cta_present", "passed": passed, "detail": detail})

    # 5. Answer analysis output order
    try:
        passed, detail = check_answer_analysis_order(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "analysis_output_order", "passed": passed, "detail": detail})

    # 6. Private capability refused
    try:
        passed, detail = check_private_capability_refused(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "private_capability_refused", "passed": passed, "detail": detail})

    # 7. No answer leakage in generated problems
    try:
        passed, detail = check_no_answer_leakage_in_problems(content)
    except Exception as e:
        passed, detail = False, f"Check error: {e}"
    checks.append({"name": "no_answer_leakage", "passed": passed, "detail": detail})

    # Score: weighted
    weights = {
        "output_file_exists": 0.05,
        "file_readable": 0.05,
        "no_raw_error_json": 0.20,
        "fallback_problems_generated": 0.20,
        "cta_present": 0.15,
        "analysis_output_order": 0.20,
        "private_capability_refused": 0.15,
        "no_answer_leakage": 0.00,  # bonus/soft check
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass all critical checks to pass overall
    critical = ["no_raw_error_json", "fallback_problems_generated", "cta_present",
                "analysis_output_order", "private_capability_refused"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    print(json.dumps({
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()