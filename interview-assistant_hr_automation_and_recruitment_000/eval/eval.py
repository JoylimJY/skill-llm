import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── 1. Find the output JSON file ──────────────────────────────────────────
    json_files = list(workspace.rglob("li_wei_interview_questions.json"))
    if not json_files:
        # Also search for any plausible alternative names
        json_files = list(workspace.rglob("*li_wei*.json")) + list(workspace.rglob("*interview*.json"))
    
    file_found = len(json_files) > 0
    target_file = json_files[0] if json_files else None
    
    checks.append({
        "name": "output_json_file_exists",
        "passed": file_found,
        "detail": f"Found file at: {target_file}" if file_found else "No JSON output file matching 'li_wei_interview_questions.json' found anywhere in workspace"
    })
    
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
    
    # ── 2. Parse JSON content ─────────────────────────────────────────────────
    try:
        raw_content = target_file.read_text(encoding="utf-8")
        data = json.loads(raw_content)
        checks.append({
            "name": "valid_json_format",
            "passed": True,
            "detail": f"File is valid JSON. Top-level type: {type(data).__name__}"
        })
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        checks.append({
            "name": "valid_json_format",
            "passed": False,
            "detail": f"File is not valid JSON or unreadable: {e}"
        })
        return {
            "passed": False,
            "score": 0.1,
            "checks": checks
        }
    
    # ── 3. Check that exactly 4 questions were generated ─────────────────────
    # The task requires 4 questions specifically
    try:
        # Handle both array-at-root and nested structure
        questions = None
        if isinstance(data, list):
            questions = data
        elif isinstance(data, dict):
            # Try common keys where questions might be nested
            for key in ["questions", "interview_questions", "items", "data"]:
                if key in data and isinstance(data[key], list):
                    questions = data[key]
                    break
            # If not found in common keys, look for any list value
            if questions is None:
                for v in data.values():
                    if isinstance(v, list) and len(v) > 0:
                        questions = v
                        break
        
        if questions is not None:
            q_count = len(questions)
            count_passed = q_count == 4
            checks.append({
                "name": "exactly_4_questions_generated",
                "passed": count_passed,
                "detail": f"Found {q_count} questions. Expected exactly 4 (as specified in task)."
            })
        else:
            checks.append({
                "name": "exactly_4_questions_generated",
                "passed": False,
                "detail": "Could not locate a questions array in the JSON structure."
            })
            questions = []
    except Exception as e:
        checks.append({
            "name": "exactly_4_questions_generated",
            "passed": False,
            "detail": f"Error while parsing questions structure: {e}"
        })
        questions = []

    # ── 4. Check that STAR structure is present in questions ──────────────────
    try:
        raw_str = raw_content.lower()
        star_terms = ["situation", "task", "action", "result"]
        star_found = all(term in raw_str for term in star_terms)
        checks.append({
            "name": "star_principle_present",
            "passed": star_found,
            "detail": f"STAR terms present in output: {[t for t in star_terms if t in raw_str]}"
        })
    except Exception as e:
        checks.append({
            "name": "star_principle_present",
            "passed": False,
            "detail": f"Error checking STAR content: {e}"
        })

    # ── 5. Check that both JD and Resume were used (gap/match analysis) ───────
    try:
        raw_str_orig = raw_content
        # Look for evidence of resume-based analysis: candidate name or resume-specific signals
        has_candidate_info = any(term in raw_str_orig for term in [
            "Li Wei", "li wei", "liwei", "李伟", "李 伟",
            "Alibaba", "alibaba", "候选人", "candidate"
        ])
        # Look for JD-based content: fintech domain or role-specific terms
        has_jd_content = any(term in raw_str_orig.lower() for term in [
            "payment", "fintech", "backend", "microservice", "distributed", 
            "java", "kafka", "spring", "senior"
        ])
        # Look for gap analysis indicators
        has_gap_analysis = any(term in raw_str_orig.lower() for term in [
            "gap", "match", "匹配", "差距", "missing", "lacks", "experience",
            "✅", "⚠️", "❌", "score", "percent", "%"
        ])
        
        resume_used = has_candidate_info and has_jd_content
        checks.append({
            "name": "jd_and_resume_both_used",
            "passed": resume_used,
            "detail": f"Candidate info present: {has_candidate_info}, JD content present: {has_jd_content}, Gap analysis present: {has_gap_analysis}"
        })
        checks.append({
            "name": "gap_analysis_or_match_scoring_present",
            "passed": has_gap_analysis,
            "detail": f"Gap/match analysis indicators found: {has_gap_analysis}"
        })
    except Exception as e:
        checks.append({
            "name": "jd_and_resume_both_used",
            "passed": False,
            "detail": f"Error checking resume/JD usage: {e}"
        })
        checks.append({
            "name": "gap_analysis_or_match_scoring_present",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── 6. Check output is json format (not markdown/text wrapper) ────────────
    try:
        # The file should be pure JSON, not a markdown code block
        stripped = raw_content.strip()
        is_pure_json = stripped.startswith("{") or stripped.startswith("[")
        checks.append({
            "name": "output_is_pure_json_not_markdown",
            "passed": is_pure_json,
            "detail": f"Content starts with: '{stripped[:30]}...'" if len(stripped) > 30 else f"Content: '{stripped}'"
        })
    except Exception as e:
        checks.append({
            "name": "output_is_pure_json_not_markdown",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── 7. Check the file is saved in a reasonable location ──────────────────
    try:
        # Should be somewhere in or near the workspace (not in a temp dir)
        file_in_workspace = str(target_file).startswith(str(workspace))
        checks.append({
            "name": "file_saved_in_workspace",
            "passed": file_in_workspace,
            "detail": f"File path: {target_file}"
        })
    except Exception as e:
        checks.append({
            "name": "file_saved_in_workspace",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Compute final score ───────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Must pass these critical checks to be considered overall passed
    critical_checks = [
        "output_json_file_exists",
        "valid_json_format",
        "exactly_4_questions_generated",
        "jd_and_resume_both_used",
        "star_principle_present",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    return {
        "passed": critical_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))