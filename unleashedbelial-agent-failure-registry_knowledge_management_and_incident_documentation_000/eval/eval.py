import sys
import os
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Find the submission file ──
    submissions_dir = Path("/tmp/agent-failure-registry/submissions")
    
    # Also search workspace in case agent placed it there
    candidate_files = list(submissions_dir.rglob("*.yaml")) + list(submissions_dir.rglob("*.yml"))
    # Exclude the pre-existing redis file
    candidate_files = [f for f in candidate_files if "redis-connection-pool" not in f.name]
    
    # Also check workspace submissions path
    ws_submissions = Path(workspace) / "submissions"
    if ws_submissions.exists():
        candidate_files += [f for f in ws_submissions.rglob("*.yaml") if "redis-connection-pool" not in f.name]
        candidate_files += [f for f in ws_submissions.rglob("*.yml") if "redis-connection-pool" not in f.name]

    # Also check if agent placed it in workspace root or any subdirectory
    # The prompt asks for a specific filename, so search broadly
    all_yaml = list(Path(workspace).rglob("*.yaml")) + list(Path(workspace).rglob("*.yml"))
    # Exclude distractor config files we know about
    known_distractors = {
        "production.yaml", "staging.yaml", "log_config.yaml", 
        "pipeline-deployment.yaml"
    }
    new_yamls = [f for f in all_yaml if f.name not in known_distractors]
    
    candidate_files = list(set(candidate_files + new_yamls))

    if not candidate_files:
        add_check("submission_file_exists", False, 
                  "No new YAML submission file found in submissions/ or workspace.")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # Try to find the most likely candidate (non-distractor, agent-created)
    # Prefer files in submissions/ directory
    submission_file = None
    for f in candidate_files:
        if "submissions" in str(f) and "redis-connection-pool" not in f.name:
            submission_file = f
            break
    
    if submission_file is None:
        # Fall back to any new yaml
        submission_file = candidate_files[0]

    add_check("submission_file_exists", True, 
              f"Found submission file: {submission_file}")

    # ── Parse YAML ──
    try:
        import yaml
        with open(submission_file) as f:
            doc = yaml.safe_load(f)
        add_check("yaml_parseable", True, "File is valid YAML.")
    except Exception as e:
        add_check("yaml_parseable", False, f"YAML parse error: {e}")
        score = 0.05
        return {"passed": False, "score": score, "checks": checks}

    if not isinstance(doc, dict):
        add_check("yaml_is_dict", False, "YAML root is not a mapping/dict.")
        return {"passed": False, "score": 0.05, "checks": checks}
    add_check("yaml_is_dict", True, "YAML root is a dict.")

    # ── CHECK: Required fields present ──
    required_fields = ["title", "category", "tags", "summary", 
                        "root_cause", "fix", "prevention", 
                        "lessons_learned", "confidence"]
    missing = [f for f in required_fields if f not in doc]
    if missing:
        add_check("required_fields_present", False, 
                  f"Missing required fields: {missing}")
    else:
        add_check("required_fields_present", True, 
                  "All required fields present.")

    # ── CHECK: category is valid enum value ──
    valid_categories = {
        "api_failure", "auth_expiry", "rate_limit", "silent_failure",
        "data_corruption", "timeout", "logic_error", "dependency_break",
        "permission_denied", "other"
    }
    category = doc.get("category", "")
    if category in valid_categories:
        add_check("category_valid_enum", True, 
                  f"Category '{category}' is a valid enum value.")
    else:
        add_check("category_valid_enum", False, 
                  f"Category '{category}' is not a valid enum. Must be one of: {sorted(valid_categories)}")

    # ── CHECK: category is semantically appropriate for an OpenAI rate limit incident ──
    # The scenario involves rate limiting — should be rate_limit or api_failure or silent_failure
    # We'll accept rate_limit (primary), api_failure, or silent_failure
    appropriate_categories = {"rate_limit", "api_failure", "silent_failure"}
    if category in appropriate_categories:
        add_check("category_semantically_appropriate", True, 
                  f"Category '{category}' is semantically appropriate for a rate-limit/silent-failure incident.")
    else:
        add_check("category_semantically_appropriate", False, 
                  f"Category '{category}' is not appropriate for the described incident. Expected one of: {sorted(appropriate_categories)}")

    # ── CHECK: tags is a list with at least 1 item ──
    tags = doc.get("tags", [])
    if isinstance(tags, list) and len(tags) >= 1:
        add_check("tags_valid_list", True, f"Tags: {tags}")
    else:
        add_check("tags_valid_list", False, 
                  f"'tags' must be a non-empty list. Got: {tags}")

    # ── CHECK: tags reference relevant technologies (openai or llm or rate-limit related) ──
    tags_lower = [str(t).lower() for t in (tags if isinstance(tags, list) else [])]
    relevant_tag_keywords = ["openai", "llm", "gpt", "rate", "batch", "pipeline", "api"]
    relevant_tags_found = any(any(kw in t for kw in relevant_tag_keywords) for t in tags_lower)
    if relevant_tags_found:
        add_check("tags_reference_relevant_tech", True, 
                  f"Tags reference relevant technology: {tags}")
    else:
        add_check("tags_reference_relevant_tech", False, 
                  f"Tags don't reference relevant technologies (openai, llm, gpt, rate, etc.). Got: {tags}")

    # ── CHECK: summary is string with min length 20 ──
    summary = str(doc.get("summary", "")).strip()
    if len(summary) >= 20:
        add_check("summary_min_length", True, 
                  f"Summary length: {len(summary)} chars.")
    else:
        add_check("summary_min_length", False, 
                  f"Summary too short ({len(summary)} chars, min 20). Got: '{summary}'")

    # ── CHECK: root_cause min length 10 ──
    root_cause = str(doc.get("root_cause", "")).strip()
    if len(root_cause) >= 10:
        add_check("root_cause_min_length", True, 
                  f"root_cause length: {len(root_cause)} chars.")
    else:
        add_check("root_cause_min_length", False, 
                  f"root_cause too short ({len(root_cause)} chars, min 10).")

    # ── CHECK: fix min length 10 ──
    fix = str(doc.get("fix", "")).strip()
    if len(fix) >= 10:
        add_check("fix_min_length", True, f"fix length: {len(fix)} chars.")
    else:
        add_check("fix_min_length", False, 
                  f"fix too short ({len(fix)} chars, min 10).")

    # ── CHECK: prevention is a list with at least 1 item ──
    prevention = doc.get("prevention", [])
    if isinstance(prevention, list) and len(prevention) >= 1:
        add_check("prevention_valid_list", True, 
                  f"prevention has {len(prevention)} items.")
    else:
        add_check("prevention_valid_list", False, 
                  f"'prevention' must be a non-empty list. Got: {prevention}")

    # ── CHECK: lessons_learned min length 10 ──
    lessons = str(doc.get("lessons_learned", "")).strip()
    if len(lessons) >= 10:
        add_check("lessons_learned_min_length", True, 
                  f"lessons_learned length: {len(lessons)} chars.")
    else:
        add_check("lessons_learned_min_length", False, 
                  f"lessons_learned too short ({len(lessons)} chars, min 10).")

    # ── CHECK: confidence is integer 1-5 ──
    confidence = doc.get("confidence")
    if isinstance(confidence, int) and 1 <= confidence <= 5:
        add_check("confidence_valid_range", True, 
                  f"confidence={confidence} (valid integer 1-5).")
    else:
        add_check("confidence_valid_range", False, 
                  f"confidence must be integer 1-5. Got: {confidence!r} (type: {type(confidence).__name__})")

    # ── CHECK: content references insights from the registry search ──
    # The agent should reference things found in the registry like:
    # tenacity, exponential backoff, TPM, token counter, output completeness, 
    # RateLimitError, silent failure, cardinality, etc.
    all_text = " ".join([
        summary, root_cause, fix, lessons,
        " ".join(str(p) for p in (prevention if isinstance(prevention, list) else []))
    ]).lower()
    
    registry_insights = [
        ("backoff", "exponential backoff mentioned"),
        ("retry", "retry logic mentioned"),
        ("silent", "silent failure concept mentioned"),
        ("tpm", "TPM (tokens per minute) referenced"),
        ("ratelimit", "RateLimitError or rate limit referenced"),
    ]
    # Need at least 2 of these to show the agent actually used search results
    insights_found = [(kw, desc) for kw, desc in registry_insights if kw in all_text.replace(" ", "").replace("-", "")]
    
    # Also check for variations
    extra_checks = [
        ("tenacity", "tenacity library referenced"),
        ("complete", "completeness validation referenced"),
        ("cardinality", "cardinality assertion referenced"),
        ("quota", "quota mentioned"),
    ]
    for kw, desc in extra_checks:
        if kw in all_text:
            insights_found.append((kw, desc))

    if len(insights_found) >= 2:
        add_check("content_derived_from_search", True, 
                  f"Content references {len(insights_found)} registry insights: {[d for _, d in insights_found[:5]]}")
    else:
        add_check("content_derived_from_search", False, 
                  f"Content does not appear to be informed by registry search results. "
                  f"Expected references to: backoff, retry, silent failure, TPM, RateLimitError, etc. "
                  f"Found only: {[d for _, d in insights_found]}")

    # ── CHECK: file is in submissions/ directory (or was intended to be) ──
    if "submissions" in str(submission_file):
        add_check("file_in_submissions_dir", True, 
                  f"File correctly placed in submissions/ directory: {submission_file}")
    else:
        add_check("file_in_submissions_dir", False, 
                  f"File not in submissions/ directory. Found at: {submission_file}. "
                  f"Expected under /tmp/agent-failure-registry/submissions/")

    # ── Compute score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = all(c["passed"] for c in checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))