#!/usr/bin/env python3
import sys
import os
import json
import re
import subprocess
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    log_path = Path("/workspace/ralph_invocations.log")
    call_count_path = Path("/workspace/ralph_call_count")
    
    # ---- Find the fix_loop script ----
    fix_script = None
    for pattern in ["fix_loop.sh", "run_fix_loop.sh", "fix.sh", "loop.sh", "autofix.sh"]:
        found = list(Path(workspace).rglob(pattern))
        if found:
            fix_script = found[0]
            break
    
    # Also check if agent ran it directly (invocation log exists and has content)
    log_content = ""
    try:
        log_content = log_path.read_text()
    except Exception as e:
        log_content = ""

    # ---- CHECK 1: Ralph was actually invoked (at least 3 times for fallback) ----
    try:
        call_count = 0
        if call_count_path.exists():
            call_count = int(call_count_path.read_text().strip())
        
        passed = call_count >= 3
        checks.append({
            "name": "ralph_invoked_with_fallback",
            "passed": passed,
            "detail": f"ralph was called {call_count} times (need ≥3 for fallback chain: kimi→minimax→glm)"
        })
    except Exception as e:
        checks.append({
            "name": "ralph_invoked_with_fallback",
            "passed": False,
            "detail": f"Error reading call count: {e}"
        })

    # ---- CHECK 2: First attempt used kimi-k2.5-free ----
    try:
        first_model_correct = False
        first_call_section = ""
        if log_content:
            # Find CALL_1 section
            match = re.search(r'CALL_1:.*?(?=CALL_2:|$)', log_content, re.DOTALL)
            if match:
                first_call_section = match.group(0)
                if "kimi-k2.5-free" in first_call_section or "kimi" in first_call_section:
                    first_model_correct = True
            # Also check DETECTED_MODEL for call 1
            dm_match = re.search(r'DETECTED_MODEL: (opencode/kimi-k2\.5-free|opencode/kimi\S*)', log_content)
            if dm_match:
                first_model_correct = True
        
        checks.append({
            "name": "first_attempt_uses_kimi",
            "passed": first_model_correct,
            "detail": f"First ralph call must use opencode/kimi-k2.5-free. Log excerpt: {first_call_section[:200]}"
        })
    except Exception as e:
        checks.append({
            "name": "first_attempt_uses_kimi",
            "passed": False,
            "detail": f"Error checking first model: {e}"
        })

    # ---- CHECK 3: Second fallback used minimax-m2.1-free ----
    try:
        second_model_correct = False
        if log_content:
            # Find CALL_2 section
            dm_matches = re.findall(r'DETECTED_MODEL: (\S+)', log_content)
            if len(dm_matches) >= 2:
                model2 = dm_matches[1]
                if "minimax" in model2:
                    second_model_correct = True
        
        checks.append({
            "name": "second_fallback_uses_minimax",
            "passed": second_model_correct,
            "detail": f"Second ralph call must use opencode/minimax-m2.1-free. Models detected: {re.findall(r'DETECTED_MODEL: (\\S+)', log_content)}"
        })
    except Exception as e:
        checks.append({
            "name": "second_fallback_uses_minimax",
            "passed": False,
            "detail": f"Error checking second model: {e}"
        })

    # ---- CHECK 4: Third fallback used glm-4.7-free ----
    try:
        third_model_correct = False
        if log_content:
            dm_matches = re.findall(r'DETECTED_MODEL: (\S+)', log_content)
            if len(dm_matches) >= 3:
                model3 = dm_matches[2]
                if "glm" in model3:
                    third_model_correct = True
        
        checks.append({
            "name": "third_fallback_uses_glm",
            "passed": third_model_correct,
            "detail": f"Third ralph call must use opencode/glm-4.7-free. Models detected: {re.findall(r'DETECTED_MODEL: (\\S+)', log_content)}"
        })
    except Exception as e:
        checks.append({
            "name": "third_fallback_uses_glm",
            "passed": False,
            "detail": f"Error checking third model: {e}"
        })

    # ---- CHECK 5: --agent opencode flag present in all calls ----
    try:
        agent_flag_count = len(re.findall(r'ARG: --agent', log_content))
        opencode_agent_count = 0
        # Check that --agent is followed by opencode
        lines = log_content.split('\n')
        for i, line in enumerate(lines):
            if '--agent' in line and 'ARG:' in line:
                # Next arg line should have opencode
                if i + 1 < len(lines) and 'opencode' in lines[i + 1]:
                    opencode_agent_count += 1
        
        # Alternative: check full argv strings
        agent_opencode_in_calls = len(re.findall(r'--agent opencode|ARG: opencode\b', log_content))
        
        # At least 3 calls should have --agent opencode
        passed = agent_flag_count >= 3 or opencode_agent_count >= 3 or agent_opencode_in_calls >= 3
        
        # Also check individual calls contain both
        call_sections = re.findall(r'CALL_\d+:.*?(?=CALL_\d+:|$)', log_content, re.DOTALL)
        calls_with_agent = sum(1 for s in call_sections if '--agent' in s and 'opencode' in s)
        
        passed = passed or calls_with_agent >= 3
        
        checks.append({
            "name": "agent_opencode_flag_present",
            "passed": passed,
            "detail": f"--agent opencode must appear in all fallback calls. agent_flag_count={agent_flag_count}, calls_with_agent={calls_with_agent}"
        })
    except Exception as e:
        checks.append({
            "name": "agent_opencode_flag_present",
            "passed": False,
            "detail": f"Error checking --agent flag: {e}"
        })

    # ---- CHECK 6: --completion-promise "COMPLETE" flag present ----
    try:
        completion_promise_count = len(re.findall(r'--completion-promise', log_content))
        complete_value_count = len(re.findall(r'ARG: COMPLETE\b|--completion-promise[= ]COMPLETE', log_content))
        
        # Check per call
        call_sections = re.findall(r'CALL_\d+:.*?(?=CALL_\d+:|$)', log_content, re.DOTALL)
        calls_with_promise = sum(1 for s in call_sections if '--completion-promise' in s and 'COMPLETE' in s)
        
        passed = completion_promise_count >= 3 and calls_with_promise >= 3
        
        checks.append({
            "name": "completion_promise_flag_present",
            "passed": passed,
            "detail": f"--completion-promise COMPLETE must appear in all calls. count={completion_promise_count}, calls_with_both={calls_with_promise}"
        })
    except Exception as e:
        checks.append({
            "name": "completion_promise_flag_present",
            "passed": False,
            "detail": f"Error checking --completion-promise: {e}"
        })

    # ---- CHECK 7: Prompt contains <promise>COMPLETE</promise> XML tag ----
    try:
        # Look in the script file for the promise tag
        promise_in_script = False
        script_content = ""
        if fix_script and fix_script.exists():
            script_content = fix_script.read_text()
            if '<promise>COMPLETE</promise>' in script_content:
                promise_in_script = True
        
        # Also check log for the XML tag in the CALL args
        promise_in_log = '<promise>COMPLETE</promise>' in log_content
        
        passed = promise_in_script or promise_in_log
        
        checks.append({
            "name": "prompt_contains_xml_promise_tag",
            "passed": passed,
            "detail": f"Prompt must embed <promise>COMPLETE</promise> XML tag. in_script={promise_in_script}, in_log={promise_in_log}"
        })
    except Exception as e:
        checks.append({
            "name": "prompt_contains_xml_promise_tag",
            "passed": False,
            "detail": f"Error checking XML promise tag: {e}"
        })

    # ---- CHECK 8: --max-iterations set and <= 20 ----
    try:
        iter_values = re.findall(r'--max-iterations[= ]*(\d+)', log_content)
        # Also check ARG pattern
        lines = log_content.split('\n')
        iter_from_args = []
        for i, line in enumerate(lines):
            if '--max-iterations' in line:
                # Value might be inline or next arg
                inline = re.search(r'--max-iterations[= ](\d+)', line)
                if inline:
                    iter_from_args.append(int(inline.group(1)))
                elif i + 1 < len(lines):
                    nm = re.search(r'ARG: (\d+)', lines[i+1])
                    if nm:
                        iter_from_args.append(int(nm.group(1)))
        
        all_iters = [int(v) for v in iter_values] + iter_from_args
        
        passed = len(all_iters) >= 1 and all(v <= 20 for v in all_iters)
        
        checks.append({
            "name": "max_iterations_set_correctly",
            "passed": passed,
            "detail": f"--max-iterations must be ≤ 20. Found values: {all_iters}"
        })
    except Exception as e:
        checks.append({
            "name": "max_iterations_set_correctly",
            "passed": False,
            "detail": f"Error checking max-iterations: {e}"
        })

    # ---- CHECK 9: Ran inside a git repository (the backtester project) ----
    try:
        # Check if script changes directory to or references the git repo
        script_content = ""
        if fix_script and fix_script.exists():
            script_content = fix_script.read_text()
        
        git_repo_referenced = (
            "trading-backtester" in script_content or
            "git" in script_content.lower()
        )
        
        # Also verify: the workspace IS a git repo
        result = subprocess.run(
            ["git", "-C", "/workspace/trading-backtester", "status"],
            capture_output=True, text=True
        )
        git_repo_valid = result.returncode == 0
        
        # Check if ralph was invoked from within git repo context
        # (The log should show calls happened when git repo existed)
        passed = git_repo_valid and (git_repo_referenced or call_count_path.exists())
        
        checks.append({
            "name": "ran_inside_git_repository",
            "passed": passed,
            "detail": f"Must run ralph inside git repo. git_repo_valid={git_repo_valid}, git_referenced_in_script={git_repo_referenced}"
        })
    except Exception as e:
        checks.append({
            "name": "ran_inside_git_repository",
            "passed": False,
            "detail": f"Error checking git repo: {e}"
        })

    # ---- CHECK 10: Script file exists and is executable / well-formed ----
    try:
        script_exists = fix_script is not None and fix_script.exists()
        script_content = ""
        if script_exists:
            script_content = fix_script.read_text()
        
        has_ralph_calls = script_content.count("ralph ") >= 1
        has_multiple_models = sum(1 for m in ["kimi", "minimax", "glm"] if m in script_content)
        
        passed = script_exists and has_ralph_calls and has_multiple_models >= 3
        
        checks.append({
            "name": "fix_loop_script_complete",
            "passed": passed,
            "detail": f"fix_loop.sh must exist and contain ralph calls with ≥3 models. exists={script_exists}, ralph_calls={'yes' if has_ralph_calls else 'no'}, models_found={has_multiple_models}"
        })
    except Exception as e:
        checks.append({
            "name": "fix_loop_script_complete",
            "passed": False,
            "detail": f"Error checking script: {e}"
        })

    # ---- Score calculation ----
    # Weighted: fallback chain correctness is most critical
    weights = {
        "ralph_invoked_with_fallback": 2.0,
        "first_attempt_uses_kimi": 1.5,
        "second_fallback_uses_minimax": 1.5,
        "third_fallback_uses_glm": 1.5,
        "agent_opencode_flag_present": 1.0,
        "completion_promise_flag_present": 1.0,
        "prompt_contains_xml_promise_tag": 1.0,
        "max_iterations_set_correctly": 0.75,
        "ran_inside_git_repository": 0.5,
        "fix_loop_script_complete": 0.75,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned_weight / total_weight, 4)
    
    all_critical = all(
        c["passed"] for c in checks 
        if c["name"] in ["ralph_invoked_with_fallback", "first_attempt_uses_kimi", 
                          "second_fallback_uses_minimax", "third_fallback_uses_glm",
                          "completion_promise_flag_present"]
    )
    
    passed_overall = all_critical and score >= 0.7
    
    return {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))