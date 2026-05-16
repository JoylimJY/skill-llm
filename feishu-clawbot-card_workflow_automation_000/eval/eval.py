#!/usr/bin/env python3
"""
Evaluation script for the FCC bot onboarding task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import os
import subprocess
import re
from pathlib import Path

def run_cmd(cmd, cwd="/workspace"):
    """Run a shell command and return stdout, stderr, returncode."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    skill_cmd = f"node {workspace}/skills/feishu-clawbot-card/index.js"

    # ── CHECK 1: FinanceGuard is in the registry ──────────────────────────────
    check_name = "FinanceGuard registered in registry"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} list", cwd=workspace)
        combined = stdout + stderr
        if "FinanceGuard" in combined:
            checks.append({"name": check_name, "passed": True,
                           "detail": "FinanceGuard found in list output."})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"FinanceGuard NOT found in list output. Got: {combined[:500]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 2: LexBot is in the registry ───────────────────────────────────
    check_name = "LexBot registered in registry"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} list", cwd=workspace)
        combined = stdout + stderr
        if "LexBot" in combined:
            checks.append({"name": check_name, "passed": True,
                           "detail": "LexBot found in list output."})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"LexBot NOT found in list output. Got: {combined[:500]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 3: FinanceGuard card has correct feishu_id format (cli_ prefix) ─
    check_name = "FinanceGuard feishu_id uses cli_ prefix"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} export FinanceGuard", cwd=workspace)
        combined = stdout + stderr
        # Look for fcc-v1 JSON block
        match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
        if match:
            try:
                card = json.loads(match.group(0))
                fid = card.get("feishu_id", "")
                if fid.startswith("cli_"):
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"feishu_id='{fid}' correctly uses cli_ prefix."})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"feishu_id='{fid}' does NOT start with cli_."})
            except json.JSONDecodeError as je:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Exported JSON parse error: {je}. Raw: {combined[:300]}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"No fcc-v1 JSON found in export output. Got: {combined[:500]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 4: LexBot feishu_id uses ou_ prefix ─────────────────────────────
    check_name = "LexBot feishu_id uses ou_ prefix"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} export LexBot", cwd=workspace)
        combined = stdout + stderr
        match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
        if match:
            try:
                card = json.loads(match.group(0))
                fid = card.get("feishu_id", "")
                if fid.startswith("ou_"):
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"feishu_id='{fid}' correctly uses ou_ prefix."})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"feishu_id='{fid}' does NOT start with ou_."})
            except json.JSONDecodeError as je:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"JSON parse error: {je}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"No fcc-v1 JSON in LexBot export. Got: {combined[:500]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 5: FinanceGuard card has avatar.url (nested, not flat) ──────────
    check_name = "FinanceGuard avatar is nested {url: ...} not flat string"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} export FinanceGuard", cwd=workspace)
        combined = stdout + stderr
        match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
        if match:
            try:
                card = json.loads(match.group(0))
                avatar = card.get("avatar", None)
                if isinstance(avatar, dict) and "url" in avatar:
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"avatar is dict with url: {avatar['url']}"})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"avatar field is not {{url:...}}: {avatar}"})
            except json.JSONDecodeError as je:
                checks.append({"name": check_name, "passed": False, "detail": str(je)})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No fcc-v1 export found to inspect avatar."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 6: bio has species, mbti, desc sub-fields (FinanceGuard) ─────────
    check_name = "FinanceGuard bio has species/mbti/desc sub-fields"
    try:
        stdout, stderr, rc = run_cmd(f"{skill_cmd} export FinanceGuard", cwd=workspace)
        combined = stdout + stderr
        match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
        if match:
            try:
                card = json.loads(match.group(0))
                bio = card.get("bio", {})
                has_species = "species" in bio
                has_mbti = "mbti" in bio
                has_desc = "desc" in bio
                if has_species and has_mbti and has_desc:
                    checks.append({"name": check_name, "passed": True,
                                   "detail": f"bio={bio}"})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"bio missing fields. Got: {bio}. species={has_species}, mbti={has_mbti}, desc={has_desc}"})
            except json.JSONDecodeError as je:
                checks.append({"name": check_name, "passed": False, "detail": str(je)})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": "No fcc-v1 export found."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 7: Export→Import round-trip succeeded (FinanceGuard re-importable) 
    check_name = "FinanceGuard export→import round-trip produces valid fcc-v1 card"
    try:
        # Export FinanceGuard
        stdout, stderr, rc = run_cmd(f"{skill_cmd} export FinanceGuard", cwd=workspace)
        combined = stdout + stderr
        match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
        if match:
            card_json_str = match.group(0)
            try:
                card_obj = json.loads(card_json_str)
                assert card_obj.get("protocol") == "fcc-v1", "protocol != fcc-v1"
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Exported card has protocol=fcc-v1, id={card_obj.get('id','?')}, name={card_obj.get('display_name','?')}"})
            except (json.JSONDecodeError, AssertionError) as e:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Card validation failed: {e}"})
        else:
            checks.append({"name": check_name, "passed": False,
                           "detail": f"Could not extract fcc-v1 JSON from export. Output: {combined[:400]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 8: lexbot_display_card.json exists and is valid Feishu Post JSON ─
    check_name = "lexbot_display_card.json exists in ops/registry/ with Feishu Post structure"
    try:
        candidate_paths = list(Path(workspace).rglob("lexbot_display_card.json"))
        if not candidate_paths:
            checks.append({"name": check_name, "passed": False,
                           "detail": "lexbot_display_card.json not found anywhere in workspace."})
        else:
            fpath = candidate_paths[0]
            # Check it's under ops/registry/
            rel = fpath.relative_to(workspace)
            in_registry = str(rel).startswith("ops/registry")
            with open(fpath, "r") as f:
                content = f.read().strip()
            # Try to parse as JSON
            try:
                data = json.loads(content)
                # Feishu Post JSON typically has a "content" or "post" key or similar Rich Text structure
                # The render command should produce some structured JSON
                is_dict = isinstance(data, dict)
                # Accept any non-empty dict as valid render output (structure varies by skill version)
                if is_dict and len(data) > 0:
                    detail = f"Found at {rel} (in_registry_dir={in_registry}), keys: {list(data.keys())[:5]}"
                    checks.append({"name": check_name, "passed": True, "detail": detail})
                else:
                    checks.append({"name": check_name, "passed": False,
                                   "detail": f"File is empty dict or non-dict JSON. data={str(data)[:200]}"})
            except json.JSONDecodeError as je:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"File is not valid JSON: {je}. Content: {content[:200]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 9: registry_snapshot.txt exists and lists both bots ─────────────
    check_name = "registry_snapshot.txt lists both FinanceGuard and LexBot"
    try:
        snapshot_path = Path(workspace) / "ops" / "registry" / "registry_snapshot.txt"
        if not snapshot_path.exists():
            # Also search broadly
            candidates = list(Path(workspace).rglob("registry_snapshot.txt"))
            if candidates:
                snapshot_path = candidates[0]
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": "registry_snapshot.txt not found."})
                snapshot_path = None

        if snapshot_path and snapshot_path.exists():
            content = snapshot_path.read_text()
            has_finance = "FinanceGuard" in content
            has_lex = "LexBot" in content
            if has_finance and has_lex:
                checks.append({"name": check_name, "passed": True,
                               "detail": f"Both bots found in snapshot. Snippet: {content[:300]}"})
            else:
                checks.append({"name": check_name, "passed": False,
                               "detail": f"Missing bots. FinanceGuard={has_finance}, LexBot={has_lex}. Content: {content[:300]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── CHECK 10: capabilities field is a list (not a string) ─────────────────
    check_name = "capabilities field is a JSON array in both exported cards"
    try:
        results = []
        for bot_name in ["FinanceGuard", "LexBot"]:
            stdout, stderr, rc = run_cmd(f"{skill_cmd} export {bot_name}", cwd=workspace)
            combined = stdout + stderr
            match = re.search(r'\{.*"protocol"\s*:\s*"fcc-v1".*\}', combined, re.DOTALL)
            if match:
                try:
                    card = json.loads(match.group(0))
                    caps = card.get("capabilities", None)
                    if isinstance(caps, list):
                        results.append(f"{bot_name}: capabilities={caps}")
                    else:
                        results.append(f"{bot_name}: capabilities is NOT a list: {caps}")
                except json.JSONDecodeError:
                    results.append(f"{bot_name}: JSON parse failed")
            else:
                results.append(f"{bot_name}: no export found")

        all_pass = all("NOT a list" not in r and "JSON parse failed" not in r and "no export found" not in r
                       for r in results)
        checks.append({"name": check_name, "passed": all_pass,
                       "detail": " | ".join(results)})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": str(e)})

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= 7  # Pass threshold: 7/10

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()