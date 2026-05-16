#!/usr/bin/env python3
"""
Evaluation script for the AI recipe brand domain availability task.

Checks:
1. available_domains.json exists somewhere in the workspace.
2. It is valid JSON containing a list/array.
3. Every entry in the list is a genuinely ✅ AVAILABLE domain per the script's DB.
4. No TAKEN / LIKELY TAKEN / UNKNOWN domains are included.
5. At least 15 distinct candidate domains were evaluated (inferred from result
   plausibility: the agent must have run the script on ≥15 domains to surface
   a meaningful shortlist — we verify this by checking that the JSON file was
   produced after running a reasonable batch, and that at least some domains
   are present).
"""

import sys
import json
import subprocess
from pathlib import Path

def main(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    overall_passed = True

    # ── Ground-truth: what the script actually marks AVAILABLE ─────────────
    TRULY_AVAILABLE = {
        "flavrai.com", "dishiq.com", "mealcraftai.com", "forkwise.com",
        "chompai.com", "savorly.ai", "forkwise.ai", "recipemind.ai",
        "pantrypal.ai", "mealcraft.ai", "dishiq.io", "chompai.io",
        "tastecraft.io", "flavrai.net", "dishiq.net", "mealcraftai.org",
    }

    NOT_AVAILABLE = {
        "savorly.com", "recipemind.com", "cookgenius.com", "pantrypal.com",
        "spoonful.com", "bitesize.com", "noshly.com", "plately.com",
        "cuisineiq.com", "tastecraft.com", "grubgenius.com", "mealbot.com",
        "culinaryai.com", "dishcraft.com", "flavr.ai", "dishiq.ai",
        "chompai.ai", "tastecraft.ai", "flavrai.io", "savorly.io",
        "forkwise.io", "recipemind.io", "pantrypal.io", "savorly.net",
        "flavrai.org",
        # LIKELY TAKEN (also not available)
        "cookgenius.ai", "mealcraft.io",
        # UNKNOWN (also not available)
        "grubgenius.io",
    }

    # ── Check 1: Find available_domains.json ──────────────────────────────
    found_files = list(workspace.rglob("available_domains.json"))
    if not found_files:
        checks.append({
            "name": "file_exists",
            "passed": False,
            "detail": "available_domains.json not found anywhere in the workspace."
        })
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    target_file = found_files[0]
    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found at {target_file.relative_to(workspace)}"
    })

    # ── Check 2: Valid JSON ───────────────────────────────────────────────
    try:
        raw = target_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        checks.append({
            "name": "valid_json",
            "passed": False,
            "detail": f"Could not parse JSON: {e}"
        })
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({
        "name": "valid_json",
        "passed": True,
        "detail": "File parses as valid JSON."
    })

    # ── Check 3: Is a list / array ────────────────────────────────────────
    # Accept either a plain list of domain strings, or a list of dicts with a "domain" key.
    domain_list = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                domain_list.append(item.strip().lower())
            elif isinstance(item, dict):
                # Accept {"domain": "x.com", ...} or {"name": "x.com", ...}
                for key in ("domain", "name", "url"):
                    if key in item:
                        domain_list.append(str(item[key]).strip().lower())
                        break
    elif isinstance(data, dict):
        # Maybe {"available": [...]}
        for key in ("available", "domains", "results"):
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    if isinstance(item, str):
                        domain_list.append(item.strip().lower())
                    elif isinstance(item, dict):
                        for k in ("domain", "name"):
                            if k in item:
                                domain_list.append(str(item[k]).strip().lower())
                                break
                break

    is_list_ok = len(domain_list) > 0
    checks.append({
        "name": "contains_domain_list",
        "passed": is_list_ok,
        "detail": (
            f"Extracted {len(domain_list)} domain entries from the JSON."
            if is_list_ok
            else "Could not extract any domain entries. Expected a JSON array of domain strings."
        )
    })
    if not is_list_ok:
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Check 4: No false positives (TAKEN/LIKELY_TAKEN/UNKNOWN included) ─
    false_positives = [d for d in domain_list if d in NOT_AVAILABLE]
    fp_passed = len(false_positives) == 0
    checks.append({
        "name": "no_false_positives",
        "passed": fp_passed,
        "detail": (
            "All listed domains are correctly identified as available — no TAKEN/LIKELY TAKEN/UNKNOWN domains included."
            if fp_passed
            else f"FAIL: These domains are NOT available but were listed: {false_positives}"
        )
    })
    if not fp_passed:
        overall_passed = False

    # ── Check 5: Only truly AVAILABLE domains listed ──────────────────────
    unrecognized = [d for d in domain_list if d not in TRULY_AVAILABLE and d not in NOT_AVAILABLE]
    unrecognized_pass = len(unrecognized) == 0
    checks.append({
        "name": "only_script_available_domains",
        "passed": unrecognized_pass,
        "detail": (
            "All entries match known AVAILABLE domains from the script."
            if unrecognized_pass
            else f"Unrecognized domains (not in script's domain DB): {unrecognized}. "
                 "Agent may have invented domains without running the script."
        )
    })
    if not unrecognized_pass:
        overall_passed = False

    # ── Check 6: At least 5 AVAILABLE domains identified ─────────────────
    # (The script has 16 AVAILABLE entries; a proper batch run should surface many)
    true_positives = [d for d in domain_list if d in TRULY_AVAILABLE]
    coverage_ok = len(true_positives) >= 5
    checks.append({
        "name": "minimum_available_domains_found",
        "passed": coverage_ok,
        "detail": (
            f"Found {len(true_positives)} correctly identified AVAILABLE domain(s). "
            + ("Meets the minimum threshold of 5."
               if coverage_ok
               else "Below minimum threshold of 5. Agent likely did not run a proper 15+ candidate batch.")
        )
    })
    if not coverage_ok:
        overall_passed = False

    # ── Check 7: Script was actually used (script exists and is executable) ─
    script_path = workspace / "scripts" / "check_domains.sh"
    script_ok = script_path.exists() and os.access(str(script_path), os.X_OK)
    checks.append({
        "name": "script_intact",
        "passed": script_ok,
        "detail": (
            "scripts/check_domains.sh exists and is executable."
            if script_ok
            else "scripts/check_domains.sh missing or not executable — agent may have removed/corrupted it."
        )
    })
    if not script_ok:
        overall_passed = False

    # ── Scoring ──────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))


import os
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided."}]}))
        sys.exit(1)
    main(sys.argv[1])