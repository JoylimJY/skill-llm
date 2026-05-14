import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # --- Check 1: Find the output file ---
    result_files = list(ws.rglob("sched_poster_v3_scan_result.txt"))
    file_found = len(result_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(result_files)} file(s) named 'sched_poster_v3_scan_result.txt'" if file_found else "No file named 'sched_poster_v3_scan_result.txt' found anywhere in workspace"
    })

    if not file_found:
        return checks, False

    result_path = result_files[0]

    # --- Read output content ---
    try:
        content = result_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "output_file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return checks, False

    checks.append({"name": "output_file_readable", "passed": True, "detail": f"File readable, {len(content)} chars"})

    # --- Check 2: Scanner ran and produced output (not empty, has heartbeat scanner header) ---
    has_scanner_header = "Heartbeat Scanner" in content or "heartbeat" in content.lower()
    checks.append({
        "name": "scanner_output_present",
        "passed": has_scanner_header,
        "detail": "Scanner output header found" if has_scanner_header else "File does not appear to contain heartbeat scanner output"
    })

    # --- Check 3: SHACL validation passed ---
    shacl_passed = "SHACL validation passed" in content or "✅ SHACL validation passed" in content
    checks.append({
        "name": "shacl_validation_passed",
        "passed": shacl_passed,
        "detail": "SHACL validation passed message found" if shacl_passed else "No 'SHACL validation passed' message in output — profile may be structurally invalid"
    })

    # --- Check 4: Correct classification = CRON ---
    # CV = 0.081 < 0.12 → must be CRON regardless of agent_score
    cron_classified = bool(re.search(r'CLASSIFICATION\s*:\s*CRON', content, re.IGNORECASE)) or \
                      bool(re.search(r'⏰\s*CLASSIFICATION', content)) or \
                      bool(re.search(r'CLASSIFICATION.*CRON', content, re.IGNORECASE))
    checks.append({
        "name": "correct_classification_cron",
        "passed": cron_classified,
        "detail": "CRON classification found in output (CV=0.081 < 0.12 guard)" if cron_classified else f"CRON classification NOT found. CV=0.081 should trigger the CV<0.12 CRON guard. Content snippet: {content[:500]}"
    })

    # --- Check 5: No "INSUFFICIENT" or exit error ---
    not_insufficient = "INSUFFICIENT" not in content.upper() or "CANNOT CLASSIFY" not in content.upper()
    # More precisely: check scanner didn't exit with insufficient data
    has_insufficient = "INSUFFICIENT DATA" in content.upper()
    checks.append({
        "name": "data_quality_sufficient",
        "passed": not has_insufficient,
        "detail": "Data quality sufficient (postCount=25 >= 5, daysSpan=18.5 >= 2)" if not has_insufficient else "Scanner reported INSUFFICIENT DATA — profile may have wrong postCount or daysSpan"
    })

    # --- Check 6: Find the TTL profile created by agent ---
    ttl_files = list(ws.rglob("*.ttl"))
    # Exclude the example files and distractor files
    excluded_paths = {
        "shapes/examples/BatMann.ttl",
        "shapes/examples/Test_RoyMas.ttl",
        "shapes/examples/Test_SarahChen.ttl",
        "profiles/archived/broken_profile.ttl",
        "profiles/pending_review/incomplete_bot.ttl",
        "tools/legacy/old_profile_template.ttl",
    }
    agent_ttl_files = [
        f for f in ttl_files
        if not any(str(f).endswith(ep) for ep in excluded_paths)
    ]

    profile_found = len(agent_ttl_files) > 0
    checks.append({
        "name": "profile_ttl_created",
        "passed": profile_found,
        "detail": f"Found {len(agent_ttl_files)} agent-created TTL profile(s): {[str(f) for f in agent_ttl_files]}" if profile_found else "No new TTL profile created by agent"
    })

    if profile_found:
        # --- Check 7: Correct CV score in the profile ---
        profile_content = agent_ttl_files[0].read_text(encoding="utf-8")

        has_correct_cv = bool(re.search(r'hasCVScore\s+"0\.08[0-9]*"', profile_content)) or \
                         bool(re.search(r'hasCVScore\s+"0\.081"', profile_content)) or \
                         bool(re.search(r'hasCVScore\s+"\.081"', profile_content))
        checks.append({
            "name": "correct_cv_score_in_profile",
            "passed": has_correct_cv,
            "detail": "CV score 0.081 found in profile" if has_correct_cv else f"CV score 0.081 not found in TTL profile. Content: {profile_content[:600]}"
        })

        # --- Check 8: Correct agent score formula applied ---
        # agentScore = 0.3*0.081 + 0.5*0.18 + 0.2*0.10 = 0.0243 + 0.09 + 0.02 = 0.1343
        # Accept values in range [0.13, 0.14] for rounding tolerance
        score_match = re.search(r'hasAgentScore\s+"([0-9.]+)"', profile_content)
        if score_match:
            try:
                score_val = float(score_match.group(1))
                correct_score = 0.130 <= score_val <= 0.140
                checks.append({
                    "name": "correct_agent_score_formula",
                    "passed": correct_score,
                    "detail": f"hasAgentScore={score_val:.4f}, expected ~0.1343 (0.3*0.081 + 0.5*0.18 + 0.2*0.10). In range [0.13,0.14]: {correct_score}"
                })
            except ValueError:
                checks.append({
                    "name": "correct_agent_score_formula",
                    "passed": False,
                    "detail": f"Could not parse hasAgentScore value: {score_match.group(1)}"
                })
        else:
            checks.append({
                "name": "correct_agent_score_formula",
                "passed": False,
                "detail": "hasAgentScore predicate not found in profile"
            })

        # --- Check 9: Correct namespace usage ---
        correct_namespace = "http://moltbook.org/mimicry/ontology#" in profile_content
        checks.append({
            "name": "correct_mimicry_namespace",
            "passed": correct_namespace,
            "detail": "Correct mimicry namespace (http://moltbook.org/mimicry/ontology#) found in profile" if correct_namespace else "Correct mimicry namespace NOT found — agent may have used wrong/legacy namespace"
        })

        # --- Check 10: Correct postCount and daysSpan ---
        has_postcount = bool(re.search(r'postCount\s+"25"', profile_content))
        has_daysspan = bool(re.search(r'daysSpan\s+"18\.5"', profile_content)) or \
                      bool(re.search(r'daysSpan\s+"18\.50*"', profile_content))
        checks.append({
            "name": "correct_postcount_and_daysspan",
            "passed": has_postcount and has_daysspan,
            "detail": f"postCount=25: {has_postcount}, daysSpan=18.5: {has_daysspan}"
        })

    # Determine overall pass
    # Core required checks: file exists, scanner output, shacl passed, correct CRON classification, data sufficient
    critical = ["output_file_exists", "scanner_output_present", "shacl_validation_passed",
                "correct_classification_cron", "data_quality_sufficient"]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_pass = all(critical_results.get(n, False) for n in critical)

    return checks, all_critical_pass


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, overall_passed = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }
        print(json.dumps(result))
        return

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3) if total > 0 else 0.0

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()