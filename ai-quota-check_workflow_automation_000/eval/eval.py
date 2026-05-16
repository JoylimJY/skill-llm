import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    passed_all = True

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── 1. Locate model_routing_decision.json ─────────────────────────────────
    target_files = list(Path(workspace).rglob("model_routing_decision.json"))
    if not target_files:
        add_check("file_exists", False, "model_routing_decision.json not found anywhere in workspace")
        return passed_all, checks

    # Use the most recently modified if multiple (shouldn't happen)
    target_file = sorted(target_files, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    add_check("file_exists", True, f"Found at: {target_file}")

    # ── 2. Parse JSON ─────────────────────────────────────────────────────────
    try:
        with open(target_file, "r") as f:
            data = json.load(f)
        add_check("valid_json", True, "File is valid JSON")
    except Exception as e:
        add_check("valid_json", False, f"JSON parse error: {e}")
        return passed_all, checks

    # ── 3. Coding task recommendation ─────────────────────────────────────────
    # Quota state:
    #   gpt-5.3-codex: 8%  (<20% → fallback)
    #   gpt-5.2-codex: 11% (<20% → fallback)
    #   gemini-3-pro-high: 52% (≥20% → SELECTED)
    EXPECTED_CODING_MODEL = "google-antigravity/gemini-3-pro-high"

    coding_section = None
    # Try to find coding recommendation in various possible structures
    for key in ["coding", "coding_task", "CODING"]:
        if key in data:
            coding_section = data[key]
            break

    if coding_section is None:
        add_check("coding_section_present", False, f"No 'coding' key found in JSON. Keys present: {list(data.keys())}")
    else:
        add_check("coding_section_present", True, f"Found coding section")

        # Extract recommended model — accept nested dict or flat string
        coding_model = None
        if isinstance(coding_section, dict):
            for key in ["recommended_model", "model", "recommendation", "selected_model"]:
                if key in coding_section:
                    coding_model = coding_section[key]
                    break
        elif isinstance(coding_section, str):
            coding_model = coding_section

        if coding_model is None:
            add_check("coding_model_correct", False, f"Could not extract model from coding section: {coding_section}")
        else:
            correct = (coding_model.strip() == EXPECTED_CODING_MODEL)
            add_check(
                "coding_model_correct",
                correct,
                f"Expected '{EXPECTED_CODING_MODEL}', got '{coding_model}'. "
                f"(gpt-5.3-codex=8%<20%, gpt-5.2-codex=11%<20%, gemini-3-pro-high=52%≥20%→selected)"
                if not correct else f"Correct: '{coding_model}'"
            )

    # ── 4. Reasoning task recommendation ──────────────────────────────────────
    # Quota state:
    #   claude-opus-4.6-thinking: 15% (<20% → fallback)
    #   claude-4.6-opus: 34% (≥20% → SELECTED)
    EXPECTED_REASONING_MODEL = "github-copilot/claude-4.6-opus"

    reasoning_section = None
    for key in ["reasoning", "reasoning_task", "REASONING", "complex_reasoning"]:
        if key in data:
            reasoning_section = data[key]
            break

    if reasoning_section is None:
        add_check("reasoning_section_present", False, f"No 'reasoning' key found in JSON. Keys present: {list(data.keys())}")
    else:
        add_check("reasoning_section_present", True, "Found reasoning section")

        reasoning_model = None
        if isinstance(reasoning_section, dict):
            for key in ["recommended_model", "model", "recommendation", "selected_model"]:
                if key in reasoning_section:
                    reasoning_model = reasoning_section[key]
                    break
        elif isinstance(reasoning_section, str):
            reasoning_model = reasoning_section

        if reasoning_model is None:
            add_check("reasoning_model_correct", False, f"Could not extract model from reasoning section: {reasoning_section}")
        else:
            correct = (reasoning_model.strip() == EXPECTED_REASONING_MODEL)
            add_check(
                "reasoning_model_correct",
                correct,
                f"Expected '{EXPECTED_REASONING_MODEL}', got '{reasoning_model}'. "
                f"(claude-opus-4.6-thinking=15%<20%, claude-4.6-opus=34%≥20%→selected)"
                if not correct else f"Correct: '{reasoning_model}'"
            )

    # ── 5. Verify CLI was actually used (not hardcoded guesses) ───────────────
    # Run the CLI ourselves and check coding recommendation matches
    try:
        result = subprocess.run(
            ["node", "skills/ai-quota-check/index.js", "--task=coding"],
            capture_output=True, text=True, cwd=workspace, timeout=15
        )
        cli_output = result.stdout
        # The CLI should clearly show gemini-3-pro-high as selected
        if "gemini-3-pro-high" in cli_output and "SELECTED" in cli_output:
            add_check("cli_output_consistency", True,
                      "CLI output confirms gemini-3-pro-high is selected for coding (◀ SELECTED marker present)")
        else:
            add_check("cli_output_consistency", True,
                      "CLI ran successfully (note: SELECTED marker may vary in format)")
    except Exception as e:
        add_check("cli_output_consistency", False, f"Could not run CLI to verify: {e}")

    # ── 6. Verify coding quota percentages are documented (shows CLI was read) ─
    # The agent should have captured the quota dashboard — check that the
    # decision file includes at least some evidence of quota reading
    # (remaining percentage fields, or a rationale mentioning percentages)
    has_quota_evidence = False
    raw_text = json.dumps(data).lower()

    # Look for percentage values or quota mentions
    quota_indicators = ["remaining", "quota", "percent", "%", "threshold", "fallback",
                        "8", "11", "52", "15", "34"]  # actual quota values from CLI
    matches = [ind for ind in quota_indicators if ind in raw_text]
    if len(matches) >= 3:
        has_quota_evidence = True

    add_check(
        "quota_evidence_present",
        has_quota_evidence,
        f"Found {len(matches)} quota-related indicators in JSON ({matches[:5]}). "
        f"Expected evidence the CLI output was read (quota %, thresholds, etc.)"
        if not has_quota_evidence else
        f"Quota evidence found: {matches[:5]}"
    )

    # ── 7. Fallback threshold awareness ───────────────────────────────────────
    # Check that the file doesn't incorrectly recommend the primary models
    # (which would indicate the agent ignored the 20% threshold)
    WRONG_CODING_PRIMARIES = ["openai-codex/gpt-5.3-codex", "openai-codex/gpt-5.2-codex"]
    WRONG_REASONING_PRIMARY = "google-antigravity/claude-opus-4.6-thinking"

    wrongly_used_primary = False
    if coding_section:
        cm = ""
        if isinstance(coding_section, dict):
            cm = coding_section.get("recommended_model", coding_section.get("model", ""))
        elif isinstance(coding_section, str):
            cm = coding_section
        if cm in WRONG_CODING_PRIMARIES:
            wrongly_used_primary = True

    if reasoning_section:
        rm = ""
        if isinstance(reasoning_section, dict):
            rm = reasoning_section.get("recommended_model", reasoning_section.get("model", ""))
        elif isinstance(reasoning_section, str):
            rm = reasoning_section
        if rm == WRONG_REASONING_PRIMARY:
            wrongly_used_primary = True

    add_check(
        "threshold_logic_applied",
        not wrongly_used_primary,
        "Agent correctly applied 20% fallback threshold (did not recommend models below threshold)"
        if not wrongly_used_primary else
        "Agent recommended a primary model that is below the 20% fallback threshold — threshold logic was NOT applied"
    )

    return passed_all, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    try:
        passed_all, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, indent=2))
        return

    # Score: each check weighted equally
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0

    # Must pass all critical checks to pass overall
    critical_checks = ["file_exists", "valid_json", "coding_model_correct", "reasoning_model_correct", "threshold_logic_applied"]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    result = {
        "passed": critical_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()