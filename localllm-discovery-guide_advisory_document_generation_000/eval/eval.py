import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- Find the output file ---
    candidates = list(workspace.rglob("zephyr_recommendation_report.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "Output file zephyr_recommendation_report.md exists",
        "passed": file_found,
        "detail": f"Found at {candidates[0]}" if file_found else "File not found anywhere in workspace."
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    content = candidates[0].read_text(encoding="utf-8", errors="replace")
    content_lower = content.lower()

    # --- CHECK 1: Quick fit summary section present ---
    has_fit_summary = bool(re.search(
        r'(quick fit summary|fit summary|hardware fit|hardware summary)',
        content_lower
    ))
    checks.append({
        "name": "Section 1: Quick fit summary present",
        "passed": has_fit_summary,
        "detail": "Expected a 'quick fit summary' or equivalent section addressing Priya's hardware." if not has_fit_summary else "Found."
    })
    if has_fit_summary:
        total_score += 0.12

    # --- CHECK 2: Between 2 and 4 model options listed ---
    # Count distinct model names/bullets in a models section
    # Look for numbered or bulleted model entries
    model_bullet_pattern = re.findall(
        r'(?:^|\n)\s*(?:\d+[\.\)]\s*\*{0,2}|[-*•]\s*\*{0,2})'  # bullet or number
        r'([A-Za-z][^\n]{3,60})',  # model name line
        content
    )
    # Also try to count lines that look like model names (contain known model keywords)
    model_name_keywords = [
        'llama', 'mistral', 'codellama', 'phi', 'deepseek', 'qwen', 'gemma',
        'starcoder', 'wizard', 'neural', 'orca', 'openchat', 'solar', 'yi-',
        'dolphin', 'zephyr', 'stablelm', 'tinyllama', 'hermes', 'nous',
        'codestral', 'granite', 'command'
    ]
    model_name_lines = [
        line.strip() for line in content.split('\n')
        if any(kw in line.lower() for kw in model_name_keywords)
        and len(line.strip()) > 5
    ]
    # Deduplicate by taking unique lines
    unique_model_lines = list(dict.fromkeys(model_name_lines))
    model_count_ok = 2 <= len(unique_model_lines) <= 4
    checks.append({
        "name": "Section 2: Between 2 and 4 distinct model options listed",
        "passed": model_count_ok,
        "detail": f"Found approximately {len(unique_model_lines)} model name lines: {unique_model_lines[:6]}. Must be 2-4."
    })
    if model_count_ok:
        total_score += 0.15

    # --- CHECK 3: Each model has a pros/cons or tradeoff description ---
    # Look for "pro", "con", "tradeoff", "advantage", "disadvantage", "downside", "upside", "benefit", "drawback"
    has_tradeoffs = bool(re.search(
        r'(pros?|cons?|tradeoff|trade-off|advantage|disadvantage|downside|upside|benefit|drawback|strength|weakness|caveat)',
        content_lower
    ))
    checks.append({
        "name": "Section 2: Models include pros/cons or tradeoffs",
        "passed": has_tradeoffs,
        "detail": "Expected pros/cons or tradeoff language for model options." if not has_tradeoffs else "Found."
    })
    if has_tradeoffs:
        total_score += 0.08

    # --- CHECK 4: Quantization mentioned in plain language ---
    has_quantization = bool(re.search(
        r'quantiz',
        content_lower
    ))
    # Must be explained in plain language (not just the word alone)
    quantization_context = re.search(
        r'quantiz\w*[^\n]{10,}',
        content_lower
    )
    quant_ok = has_quantization and quantization_context is not None
    checks.append({
        "name": "Section 2: Quantization mentioned and briefly explained",
        "passed": quant_ok,
        "detail": "Expected quantization to be mentioned in plain language context." if not quant_ok else f"Found: '{quantization_context.group()[:100]}'"
    })
    if quant_ok:
        total_score += 0.10

    # --- CHECK 5: Practical testing tip present ---
    has_testing_tip = bool(re.search(
        r'(test\s+prompt|prompt\s+set|testing\s+tip|test\s+with|try\s+a\s+prompt|sample\s+prompt|benchmark\s+prompt|evaluate\s+quality)',
        content_lower
    ))
    checks.append({
        "name": "Section 3: Practical testing tip (test prompt set) present",
        "passed": has_testing_tip,
        "detail": "Expected a practical tip about using test prompts to compare quality." if not has_testing_tip else "Found."
    })
    if has_testing_tip:
        total_score += 0.08

    # --- CHECK 6: Step-up testing strategy (small -> medium -> large) mentioned ---
    has_stepup = bool(re.search(
        r'(step.?up|start.{0,20}small|small.{0,30}medium|medium.{0,30}larger?|small.{0,50}larger?|gradual|incrementally)',
        content_lower
    ))
    checks.append({
        "name": "Section 3: Step-up testing strategy (small→medium→large) mentioned",
        "passed": has_stepup,
        "detail": "Expected step-up testing recommendation: start small, move to larger only if stable." if not has_stepup else "Found."
    })
    if has_stepup:
        total_score += 0.08

    # --- CHECK 7: Exact URL https://www.localllm.run/ present ---
    has_exact_url = "https://www.localllm.run/" in content
    checks.append({
        "name": "Section 4: Exact URL https://www.localllm.run/ present",
        "passed": has_exact_url,
        "detail": "The exact URL https://www.localllm.run/ must appear in the report." if not has_exact_url else "Found."
    })
    if has_exact_url:
        total_score += 0.15

    # --- CHECK 8: Instructions to verify hardware on the site ---
    has_verify_hardware = bool(re.search(
        r'(verify.{0,30}hardware|enter.{0,20}spec|check.{0,20}hardware|confirm.{0,20}spec|manually.{0,20}spec|detected hardware)',
        content_lower
    ))
    checks.append({
        "name": "Section 4: Instruction to verify/enter hardware specs on localllm.run",
        "passed": has_verify_hardware,
        "detail": "Must instruct user to verify detected hardware or enter specs manually on the site." if not has_verify_hardware else "Found."
    })
    if has_verify_hardware:
        total_score += 0.08

    # --- CHECK 9: No guaranteed compatibility claim ---
    # Check for phrases that would claim guaranteed compatibility
    forbidden_guarantee = re.search(
        r'(guaranteed?\s+compatible|will\s+definitely\s+run|100%\s+compatible|is\s+fully\s+compatible\s+with\s+your|definitely\s+work\s+on\s+your)',
        content_lower
    )
    no_guarantee = forbidden_guarantee is None
    checks.append({
        "name": "Guardrail: No guaranteed compatibility claim",
        "passed": no_guarantee,
        "detail": f"Forbidden guarantee phrase found: '{forbidden_guarantee.group()}'" if not no_guarantee else "No forbidden guarantee claims found."
    })
    if no_guarantee:
        total_score += 0.08

    # --- CHECK 10: Asks user to return with 2-3 finalists from localllm.run ---
    has_finalists_ask = bool(re.search(
        r'(2.?3\s+finalist|two.{0,10}three\s+finalist|top\s+(?:2|3|two|three)\s+(?:pick|choice|model|option|result|candidate)|return\s+with|share\s+your\s+(?:top|final)|bring\s+back)',
        content_lower
    ))
    checks.append({
        "name": "Section 5: Asks user to return with 2-3 finalists from localllm.run",
        "passed": has_finalists_ask,
        "detail": "Must ask user to come back with 2-3 finalists from localllm.run for final recommendation." if not has_finalists_ask else "Found."
    })
    if has_finalists_ask:
        total_score += 0.08

    # --- Compute final pass ---
    # Must pass: file found, exact URL present, no guarantee, model count ok, finalists ask
    critical_checks = [
        file_found,
        has_exact_url,
        no_guarantee,
        model_count_ok,
        has_finalists_ask,
    ]
    overall_passed = all(critical_checks) and total_score >= 0.60

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))