#!/usr/bin/env python3
"""
Evaluation script for BracketsBot Coded workflow task.
Checks:
1. Policy module file exists with correct chooseWinner export
2. model-bracket-output.json exists with 63 valid seed picks (1..64)
3. validate command was effectively run (validation output captured or bracket is valid)
4. share-link was generated using --predictions-file flag (not default walk path)
"""
import sys
import json
import os
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Unexpected error: {e}"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "setup", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []

    # ---------------------------------------------------------------
    # CHECK 1: A JS policy module exists somewhere in the workspace
    # and it contains 'chooseWinner'
    # ---------------------------------------------------------------
    def check_policy_module():
        # Search for any .js file (excluding distractors in archived/)
        js_files = list(Path(workspace).rglob("*.js"))
        # Exclude known distractors
        candidate_files = [
            f for f in js_files
            if "archived" not in str(f)
            and "legacy" not in str(f)
            and "seed_lookup" not in str(f)
            and "wrong_policy" not in str(f)
        ]
        
        if not candidate_files:
            return False, "No JS policy module found (excluding known distractor files). Expected a module with 'chooseWinner' export."
        
        for f in candidate_files:
            try:
                content = f.read_text()
                if "chooseWinner" in content:
                    # Also check it's a proper export
                    if "module.exports" in content or "exports.chooseWinner" in content or "export" in content:
                        return True, f"Found valid policy module with chooseWinner export at: {f}"
                    else:
                        # Has chooseWinner but check if it's defined at all
                        if "function chooseWinner" in content or "chooseWinner" in content:
                            return True, f"Found policy module with chooseWinner at: {f}"
            except Exception as e:
                continue
        
        # Check all candidates for chooseWinner even without export
        for f in candidate_files:
            try:
                content = f.read_text()
                if "chooseWinner" in content:
                    return True, f"Found policy module referencing chooseWinner at: {f}"
            except:
                continue
        
        return False, f"Found {len(candidate_files)} JS file(s) but none export 'chooseWinner'. Distractor files use wrong name 'pickWinner' or 'selectWinner'."

    checks.append(run_check("policy_module_has_chooseWinner", check_policy_module))

    # ---------------------------------------------------------------
    # CHECK 2: model-bracket-output.json exists in ./out/ and has
    # exactly 63 valid picks (all seeds 1..64)
    # ---------------------------------------------------------------
    def check_bracket_output():
        bracket_file = os.path.join(workspace, "out", "model-bracket-output.json")
        
        if not os.path.exists(bracket_file):
            # Also search broadly
            found = list(Path(workspace).rglob("model-bracket-output.json"))
            if not found:
                return False, "model-bracket-output.json not found in ./out/ directory. The Coded workflow (walk-run-policy) should write to this file."
            bracket_file = str(found[0])
        
        try:
            with open(bracket_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return False, f"model-bracket-output.json exists but is invalid JSON: {e}"
        
        predictions = data.get("predictions", [])
        
        if len(predictions) != 63:
            return False, f"Expected exactly 63 picks in predictions array, got {len(predictions)}. Incomplete bracket."
        
        invalid_picks = []
        for i, pick in enumerate(predictions):
            if not isinstance(pick, int) or pick < 1 or pick > 64:
                invalid_picks.append(f"index {i}: {pick}")
        
        if invalid_picks:
            return False, f"Invalid picks found (must be seed integers 1..64): {invalid_picks[:5]}"
        
        success_flag = data.get("success", data.get("complete", False))
        if not success_flag:
            return False, f"Bracket output exists with {len(predictions)} valid picks but 'success' flag is False/missing."
        
        return True, f"model-bracket-output.json has exactly 63 valid seed picks (all in 1..64 range), success=True."

    checks.append(run_check("bracket_output_63_valid_picks", check_bracket_output))

    # ---------------------------------------------------------------
    # CHECK 3: Bracket passes validation (run validate ourselves
    # to confirm the output file is genuinely valid, simulating
    # what the agent should have done)
    # ---------------------------------------------------------------
    def check_validation():
        bracket_file = os.path.join(workspace, "out", "model-bracket-output.json")
        
        if not os.path.exists(bracket_file):
            return False, "Cannot validate: model-bracket-output.json not found."
        
        # Run bracketsbot validate --json ourselves to check
        try:
            result = subprocess.run(
                ["bracketsbot", "validate", "--predictions-file", bracket_file, "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=workspace
            )
            
            if result.returncode != 0:
                return False, f"Validation failed with exit code {result.returncode}. stderr: {result.stderr[:200]}"
            
            try:
                val_output = json.loads(result.stdout)
            except json.JSONDecodeError:
                return False, f"Validation produced non-JSON output: {result.stdout[:200]}"
            
            if val_output.get("valid") or val_output.get("success"):
                return True, f"Bracket validates successfully: {val_output.get('message', 'valid=True')}"
            else:
                errors = val_output.get("errors", [])
                return False, f"Validation found errors: {errors}"
        
        except subprocess.TimeoutExpired:
            return False, "Validation command timed out."
        except FileNotFoundError:
            # bracketsbot not on PATH, check if the bracket file itself is valid
            try:
                with open(bracket_file) as f:
                    data = json.load(f)
                picks = data.get("predictions", [])
                if len(picks) == 63 and all(isinstance(p, int) and 1 <= p <= 64 for p in picks):
                    return True, "Bracket file is structurally valid (63 picks, seeds 1..64). CLI not available for full validation."
                else:
                    return False, "Bracket file has structural issues."
            except Exception as e:
                return False, f"Could not validate bracket: {e}"

    checks.append(run_check("bracket_validates_successfully", check_validation))

    # ---------------------------------------------------------------
    # CHECK 4: share-link was generated using --predictions-file flag
    # pointing to model-bracket-output.json (not default walk path).
    # We check for evidence: a saved share URL or shell history.
    # We also independently run share-link to confirm it works.
    # ---------------------------------------------------------------
    def check_share_link():
        bracket_file = os.path.join(workspace, "out", "model-bracket-output.json")
        
        if not os.path.exists(bracket_file):
            return False, "Cannot check share-link: model-bracket-output.json not found."
        
        # Check for any file the agent may have written containing a share URL
        share_url_found_in_file = False
        share_url_value = None
        
        # Search all text files for a bracketsbot share URL
        for ext in ["*.txt", "*.json", "*.md", "*.log", "*.out"]:
            for f in Path(workspace).rglob(ext):
                if "model-bracket-output" in str(f):
                    continue
                try:
                    content = f.read_text(errors="ignore")
                    if "bracketsbot.xyz/bracket" in content or "shareUrl" in content:
                        share_url_found_in_file = True
                        # Extract URL
                        import re
                        urls = re.findall(r'https://bracketsbot\.xyz/bracket\?[^\s\'"]+', content)
                        if urls:
                            share_url_value = urls[0]
                        break
                except:
                    continue
            if share_url_found_in_file:
                break
        
        # Also check bash history or any output files
        history_files = [
            os.path.expanduser("~/.bash_history"),
            os.path.join(workspace, ".bash_history"),
            "/root/.bash_history"
        ]
        
        share_link_cmd_found = False
        for hf in history_files:
            if os.path.exists(hf):
                try:
                    content = open(hf).read()
                    # Must have used --predictions-file with model-bracket-output.json
                    if "share-link" in content and "model-bracket-output" in content:
                        share_link_cmd_found = True
                        break
                    # Also accept if share-link was run (even without checking file)
                    if "share-link" in content and "--predictions-file" in content:
                        share_link_cmd_found = True
                        break
                except:
                    pass
        
        # Independently verify: run share-link with the correct file
        try:
            result = subprocess.run(
                ["bracketsbot", "share-link", "--predictions-file", bracket_file, "--json"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=workspace
            )
            if result.returncode == 0:
                try:
                    sl_output = json.loads(result.stdout)
                    if sl_output.get("success") and sl_output.get("shareUrl"):
                        expected_url = sl_output["shareUrl"]
                        # Now we know what the correct URL should look like
                        if share_url_found_in_file or share_link_cmd_found:
                            return True, f"share-link executed with --predictions-file. URL generated: {expected_url}. Evidence found in workspace."
                        else:
                            # The agent ran it but may not have saved output - check if bracket output itself references it
                            # Check stdout capture files
                            for f in Path(workspace).rglob("*.json"):
                                try:
                                    data = json.loads(f.read_text())
                                    if data.get("shareUrl"):
                                        return True, f"Share URL found in {f}: {data['shareUrl']}"
                                except:
                                    continue
                            
                            # Last check: was the bracket output complete? If so, partial credit
                            return False, f"Bracket is valid and share-link would work (URL: {expected_url}), but no evidence found that agent ran share-link with --predictions-file flag. For Coded workflow, must use: bracketsbot share-link --predictions-file ./out/model-bracket-output.json --json"
                except:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        if share_url_found_in_file:
            return True, f"Share URL found in workspace files: {share_url_value}"
        if share_link_cmd_found:
            return True, "Evidence found that share-link was run with --predictions-file flag pointing to model-bracket-output.json."
        
        return False, "No evidence that 'bracketsbot share-link --predictions-file ./out/model-bracket-output.json' was run. For Coded/Instructed workflows, the default share-link reads walk picks; --predictions-file must be specified explicitly."

    checks.append(run_check("share_link_with_predictions_file", check_share_link))

    # ---------------------------------------------------------------
    # CHECK 5: Policy module was actually used with walk-run-policy
    # (not semantic-run or manual JSON construction)
    # ---------------------------------------------------------------
    def check_coded_workflow_used():
        bracket_file = os.path.join(workspace, "out", "model-bracket-output.json")
        
        if not os.path.exists(bracket_file):
            return False, "model-bracket-output.json not found."
        
        try:
            with open(bracket_file) as f:
                data = json.load(f)
        except:
            return False, "Could not read model-bracket-output.json"
        
        # Check if policyModule field is present (walk-run-policy sets this)
        policy_module_field = data.get("policyModule")
        
        # Check bash history for walk-run-policy usage
        history_files = [
            "/root/.bash_history",
            os.path.expanduser("~/.bash_history"),
        ]
        
        walk_run_policy_used = False
        for hf in history_files:
            if os.path.exists(hf):
                try:
                    content = open(hf).read()
                    if "walk-run-policy" in content and "--policy-module" in content:
                        walk_run_policy_used = True
                        break
                except:
                    pass
        
        if policy_module_field:
            return True, f"model-bracket-output.json contains 'policyModule' field: '{policy_module_field}', confirming walk-run-policy was used with --policy-module flag."
        
        if walk_run_policy_used:
            return True, "Bash history confirms walk-run-policy --policy-module was executed."
        
        # Check if the bracket has the structure from walk-run-policy (has success and complete)
        if data.get("success") and data.get("complete") and len(data.get("predictions", [])) == 63:
            # Weaker signal but acceptable
            return True, "model-bracket-output.json has correct structure (success+complete+63 picks) consistent with walk-run-policy execution."
        
        return False, "No evidence that walk-run-policy --policy-module was used. The Coded workflow requires running the policy module through bracketsbot, not constructing JSON manually."

    checks.append(run_check("coded_workflow_walk_run_policy_used", check_coded_workflow_used))

    # ---------------------------------------------------------------
    # SCORING
    # ---------------------------------------------------------------
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Must pass checks 1, 2, 3 to be considered passing overall
    # (policy module + bracket output + validation are critical)
    critical_checks = ["policy_module_has_chooseWinner", "bracket_output_63_valid_picks", "bracket_validates_successfully"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.6

    result = {
        "passed": overall_passed,
        "score": round(score, 2),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()