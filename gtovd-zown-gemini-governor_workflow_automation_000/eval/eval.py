import sys
import json
import re
from pathlib import Path

def count_tokens_approx(text: str) -> int:
    """Approximate token count: split on whitespace and punctuation, ~1 token per word."""
    # Use a simple whitespace split as a conservative approximation
    # tiktoken is available but we want deterministic behavior
    words = re.findall(r'\S+', text)
    return len(words)

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # -------------------------------------------------------------------------
    # CHECK 1: SOUL.md has been compacted to under 500 tokens
    # -------------------------------------------------------------------------
    max_score += 20.0
    check_name = "SOUL.md compacted to under 500 tokens"
    soul_path = workspace / "agents" / "identity" / "SOUL.md"
    try:
        soul_text = soul_path.read_text(encoding="utf-8")
        token_count = count_tokens_approx(soul_text)
        passed = token_count < 500
        detail = f"SOUL.md token count (approx): {token_count}. Limit: 500."
        if passed:
            total_score += 20.0
        checks.append({"name": check_name, "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error reading SOUL.md: {e}"})

    # -------------------------------------------------------------------------
    # CHECK 2: IDENTITY.md has been compacted to under 500 tokens
    # -------------------------------------------------------------------------
    max_score += 20.0
    check_name = "IDENTITY.md compacted to under 500 tokens"
    identity_path = workspace / "agents" / "identity" / "IDENTITY.md"
    try:
        identity_text = identity_path.read_text(encoding="utf-8")
        token_count = count_tokens_approx(identity_text)
        passed = token_count < 500
        detail = f"IDENTITY.md token count (approx): {token_count}. Limit: 500."
        if passed:
            total_score += 20.0
        checks.append({"name": check_name, "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error reading IDENTITY.md: {e}"})

    # -------------------------------------------------------------------------
    # CHECK 3: MEMORY.md exists and contains substantive content (history summary)
    # -------------------------------------------------------------------------
    max_score += 20.0
    check_name = "MEMORY.md created with substantive history summary"
    memory_candidates = list(workspace.rglob("MEMORY.md"))
    try:
        if not memory_candidates:
            raise FileNotFoundError("MEMORY.md not found anywhere in workspace.")
        memory_path = memory_candidates[0]
        memory_text = memory_path.read_text(encoding="utf-8")
        # Must have at least 50 tokens (non-trivial content)
        token_count = count_tokens_approx(memory_text)
        # Must reference key concepts: memory, history, session, or step
        has_content = token_count >= 50
        has_relevant_terms = any(
            term in memory_text.lower()
            for term in ["identity", "soul", "session", "step", "task", "pipeline", "compact", "memory", "history", "prune"]
        )
        passed = has_content and has_relevant_terms
        detail = (
            f"MEMORY.md found at {memory_path}. "
            f"Token count: {token_count}. "
            f"Has relevant terms: {has_relevant_terms}. "
            f"Content preview: {memory_text[:200]!r}"
        )
        if passed:
            total_score += 20.0
        checks.append({"name": check_name, "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # -------------------------------------------------------------------------
    # CHECK 4: cooldown.py was invoked with argument 60
    # (verified by the existence and content of cooldown.log)
    # -------------------------------------------------------------------------
    max_score += 20.0
    check_name = "cooldown.py invoked with 60-second duration (50% rule enforcement)"
    cooldown_log_path = workspace / "sessions" / "active" / "cooldown.log"
    try:
        log_text = cooldown_log_path.read_text(encoding="utf-8")
        log_data = json.loads(log_text)
        triggered = log_data.get("cooldown_triggered") is True
        duration_ok = log_data.get("duration_seconds") == 60
        passed = triggered and duration_ok
        detail = (
            f"cooldown.log content: {log_data}. "
            f"triggered={triggered}, duration_seconds={log_data.get('duration_seconds')} (expected 60)."
        )
        if passed:
            total_score += 20.0
        checks.append({"name": check_name, "passed": passed, "detail": detail})
    except FileNotFoundError:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": "cooldown.log not found. The agent did not invoke scripts/cooldown.py 60."
        })
    except json.JSONDecodeError as e:
        checks.append({
            "name": check_name,
            "passed": False,
            "detail": f"cooldown.log exists but is not valid JSON: {e}"
        })
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Unexpected error: {e}"})

    # -------------------------------------------------------------------------
    # CHECK 5: Atomic pipeline manifest created for the engineering task
    # Must be a file that breaks the task into atomic (individual) steps,
    # each described separately — not combined Plan+Execute.
    # We look for any file in workspace that contains pipeline/stage breakdown.
    # -------------------------------------------------------------------------
    max_score += 20.0
    check_name = "Atomic pipeline manifest created with individual verifiable steps"
    # Search for any .md or .json or .txt file that the agent produced as a pipeline plan
    # Exclude the original task_brief.md and log files
    candidate_files = []
    for pattern in ["*.md", "*.json", "*.txt", "*.yaml", "*.yml"]:
        for f in workspace.rglob(pattern):
            name_lower = f.name.lower()
            # Exclude known input files and logs
            if name_lower in {"soul.md", "identity.md", "skill.md", "memory.md",
                               "task_brief.md", "system_overview.md", "onboarding.txt",
                               "rate_limit_policy.txt", "run_20240101.log", "run_20240102.log",
                               "cooldown.log"}:
                continue
            if name_lower.startswith("stage") and f.suffix == ".json":
                continue
            if name_lower in {"metrics.json", "session_20240601.json", "session_current.json"}:
                continue
            try:
                text = f.read_text(encoding="utf-8")
                candidate_files.append((f, text))
            except Exception:
                pass

    try:
        found_pipeline = False
        pipeline_file = None
        pipeline_detail = "No pipeline manifest file found."

        for f, text in candidate_files:
            text_lower = text.lower()
            # Must mention atomic steps, stages, or numbered step breakdown
            # Look for at least 3 distinct step markers
            step_patterns = [
                r'step\s*\d+',
                r'stage\s*\d+',
                r'^\s*\d+\.\s+\w',
                r'^\s*-\s+step',
                r'atomic',
            ]
            step_matches = 0
            for pattern in step_patterns:
                matches = re.findall(pattern, text_lower, re.MULTILINE)
                step_matches += len(matches)

            has_pipeline_terms = any(
                term in text_lower
                for term in ["atomic", "pipeline", "stage", "step", "verifiable", "encrypt"]
            )

            if step_matches >= 3 and has_pipeline_terms:
                found_pipeline = True
                pipeline_file = f
                pipeline_detail = (
                    f"Pipeline manifest found at {f}. "
                    f"Step-like patterns found: {step_matches}. "
                    f"Content preview: {text[:300]!r}"
                )
                break

        if found_pipeline:
            total_score += 20.0
        else:
            pipeline_detail = (
                f"No file with ≥3 atomic step markers and pipeline/encryption terms found. "
                f"Candidates examined: {[str(f) for f, _ in candidate_files[:5]]}"
            )
        checks.append({"name": check_name, "passed": found_pipeline, "detail": pipeline_detail})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Unexpected error during pipeline check: {e}"})

    # -------------------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------------------
    all_passed = all(c["passed"] for c in checks)
    final_score = total_score / max_score if max_score > 0 else 0.0

    result = {
        "passed": all_passed,
        "score": round(final_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument_check", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])