#!/usr/bin/env python3
"""
Evaluation script for skill-factory task.
Checks that the agent correctly:
1. Ran the builder stage (skill/SKILL.md exists with content)
2. Fixed the name field to ≤32 characters
3. Ran the auditor stage (audit.md exists with OVERALL: PASS)
4. Ran the pricer stage (pricing.md exists with USD price + positioning)
5. Did NOT run the docs stage in the wrong way (docs_review.md absent OR correctly skipped)
6. .pipeline_state contains entries for builder, auditor, and pricer
"""

import sys
import json
import re
from pathlib import Path

def read_file_safe(path):
    try:
        p = Path(path)
        if p.exists():
            return p.read_text(), None
        return None, f"File not found: {path}"
    except Exception as e:
        return None, str(e)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/tmp/sf-csv-tool"
    ws = Path(workspace)

    checks = []
    total_score = 0.0
    max_score = 0.0

    # ── Check 1: skill/SKILL.md exists and is non-empty ──────────────────
    max_score += 1.0
    skill_md_path = ws / "skill" / "SKILL.md"
    content, err = read_file_safe(skill_md_path)
    if err or not content or not content.strip():
        checks.append({
            "name": "skill/SKILL.md exists and non-empty",
            "passed": False,
            "detail": f"Builder stage gate failed: {err or 'file is empty'}. Agent must run builder stage."
        })
    else:
        checks.append({
            "name": "skill/SKILL.md exists and non-empty",
            "passed": True,
            "detail": f"Builder stage ran successfully. skill/SKILL.md found ({len(content)} chars)."
        })
        total_score += 1.0

    # ── Check 2: skill/SKILL.md name field ≤32 characters ────────────────
    max_score += 2.0
    if content and content.strip():
        try:
            name_match = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
            if not name_match:
                checks.append({
                    "name": "SKILL.md name field ≤32 characters",
                    "passed": False,
                    "detail": "No 'name:' field found in SKILL.md frontmatter."
                })
            else:
                raw_name = name_match.group(1).strip()
                name = raw_name.strip('"\'')
                name_len = len(name)
                if name_len > 32:
                    checks.append({
                        "name": "SKILL.md name field ≤32 characters",
                        "passed": False,
                        "detail": f"Name '{name}' is {name_len} chars (exceeds 32-char limit). Agent must fix this before re-running auditor."
                    })
                elif name_len == 0:
                    checks.append({
                        "name": "SKILL.md name field ≤32 characters",
                        "passed": False,
                        "detail": "Name field is empty."
                    })
                else:
                    # Also check it's hyphen-case (lowercase + hyphens only)
                    is_hyphen_case = bool(re.match(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$', name))
                    checks.append({
                        "name": "SKILL.md name field ≤32 characters",
                        "passed": True,
                        "detail": f"Name '{name}' is {name_len} chars ({'hyphen-case valid' if is_hyphen_case else 'note: not strict hyphen-case but length OK'})."
                    })
                    total_score += 2.0
        except Exception as e:
            checks.append({
                "name": "SKILL.md name field ≤32 characters",
                "passed": False,
                "detail": f"Exception while parsing SKILL.md: {e}"
            })
    else:
        checks.append({
            "name": "SKILL.md name field ≤32 characters",
            "passed": False,
            "detail": "Cannot check name field — SKILL.md missing or empty."
        })

    # ── Check 3: audit.md exists and contains OVERALL: PASS ──────────────
    max_score += 2.0
    audit_content, audit_err = read_file_safe(ws / "audit.md")
    if audit_err or not audit_content or not audit_content.strip():
        checks.append({
            "name": "audit.md exists with OVERALL: PASS",
            "passed": False,
            "detail": f"Auditor stage failed: {audit_err or 'audit.md is empty'}. Agent must run auditor after fixing name."
        })
    elif "OVERALL: PASS" in audit_content:
        checks.append({
            "name": "audit.md exists with OVERALL: PASS",
            "passed": True,
            "detail": "audit.md present and contains 'OVERALL: PASS'. Auditor approved the skill."
        })
        total_score += 2.0
    elif "OVERALL: FAIL" in audit_content:
        # Extract the fail reason
        fail_context = ""
        for line in audit_content.splitlines():
            if "CRITICAL" in line or "FAIL" in line:
                fail_context += line.strip() + " | "
        checks.append({
            "name": "audit.md exists with OVERALL: PASS",
            "passed": False,
            "detail": f"audit.md contains OVERALL: FAIL — name fix was not applied before re-running auditor. Issues: {fail_context[:200]}"
        })
    else:
        checks.append({
            "name": "audit.md exists with OVERALL: PASS",
            "passed": False,
            "detail": f"audit.md exists but does not contain 'OVERALL: PASS' or 'OVERALL: FAIL'. Content preview: {audit_content[:100]}"
        })

    # ── Check 4: pricing.md exists with USD price and positioning ─────────
    max_score += 2.0
    pricing_content, pricing_err = read_file_safe(ws / "pricing.md")
    if pricing_err or not pricing_content or not pricing_content.strip():
        checks.append({
            "name": "pricing.md exists with USD price and positioning",
            "passed": False,
            "detail": f"Pricer stage not run: {pricing_err or 'pricing.md is empty'}."
        })
    else:
        # Check for USD price (e.g., $29 USD, $29, USD 29, etc.)
        has_usd = bool(re.search(r'\$\s*\d+', pricing_content)) or bool(re.search(r'\d+\s*USD', pricing_content))
        # Check for positioning statement (must contain "positioning" or multi-sentence paragraph about the skill)
        has_positioning = bool(re.search(r'positioning\s*statement', pricing_content, re.IGNORECASE)) or \
                          bool(re.search(r'positioning', pricing_content, re.IGNORECASE))
        
        if has_usd and has_positioning:
            checks.append({
                "name": "pricing.md exists with USD price and positioning",
                "passed": True,
                "detail": "pricing.md present with USD price and positioning statement."
            })
            total_score += 2.0
        elif not has_usd:
            checks.append({
                "name": "pricing.md exists with USD price and positioning",
                "passed": False,
                "detail": f"pricing.md exists but no USD price found. Content preview: {pricing_content[:150]}"
            })
        else:
            checks.append({
                "name": "pricing.md exists with USD price and positioning",
                "passed": False,
                "detail": f"pricing.md has USD price but no positioning statement. Content preview: {pricing_content[:150]}"
            })

    # ── Check 5: docs stage handling ──────────────────────────────────────
    # The task asks to skip docs — docs_review.md should NOT exist,
    # OR if it exists, it must contain BLOCKED (meaning audit failed first time).
    # Key: The final state should have a PASSING audit → if docs_review.md exists 
    # after the final run, it should reflect the passing state (not BLOCKED).
    max_score += 1.0
    docs_content, docs_err = read_file_safe(ws / "docs_review.md")
    if docs_err or not docs_content:
        # docs_review.md doesn't exist — agent correctly skipped docs stage
        checks.append({
            "name": "docs stage correctly skipped",
            "passed": True,
            "detail": "docs_review.md absent — agent correctly ran only builder, auditor, and pricer without the docs stage."
        })
        total_score += 1.0
    elif "BLOCKED" in docs_content:
        # docs was run but audit was FAIL at that time — this is the wrong final state
        # The agent should have fixed audit first, then skipped docs
        checks.append({
            "name": "docs stage correctly skipped",
            "passed": False,
            "detail": "docs_review.md contains BLOCKED — agent ran docs after a failed audit. The task requires running pricer after a passing audit, without docs."
        })
    else:
        # docs was run and produced non-BLOCKED content — agent ran docs when it shouldn't have
        # This is acceptable if the agent ran the full pipeline; let's be lenient but note it
        checks.append({
            "name": "docs stage correctly skipped",
            "passed": True,
            "detail": "docs_review.md present with non-BLOCKED content — agent ran docs stage (acceptable). Ideally should have been skipped per task spec."
        })
        total_score += 0.5  # Partial credit

    # ── Check 6: .pipeline_state contains builder, auditor, pricer ────────
    max_score += 2.0
    state_content, state_err = read_file_safe(ws / ".pipeline_state")
    if state_err or not state_content:
        checks.append({
            "name": ".pipeline_state records builder, auditor, pricer",
            "passed": False,
            "detail": f".pipeline_state not found or unreadable: {state_err}"
        })
    else:
        has_builder = "builder:" in state_content
        has_auditor = "auditor:" in state_content
        has_pricer = "pricer:" in state_content
        
        missing = []
        if not has_builder: missing.append("builder")
        if not has_auditor: missing.append("auditor")
        if not has_pricer: missing.append("pricer")
        
        if not missing:
            checks.append({
                "name": ".pipeline_state records builder, auditor, pricer",
                "passed": True,
                "detail": f"All three stages recorded in .pipeline_state."
            })
            total_score += 2.0
        else:
            checks.append({
                "name": ".pipeline_state records builder, auditor, pricer",
                "passed": False,
                "detail": f"Missing stage records in .pipeline_state: {missing}. Found content: {state_content[:200]}"
            })

    # ── Check 7: skill/ directory has correct structure ───────────────────
    max_score += 1.0
    skill_dir = ws / "skill"
    expected_files = [
        "skill/SKILL.md",
        "skill/scripts/transform.py",
        "skill/scripts/validate.py",
        "skill/references/transforms.md",
        "skill/references/examples.md",
    ]
    missing_files = []
    for ef in expected_files:
        if not (ws / ef).exists():
            missing_files.append(ef)
    
    if not missing_files:
        checks.append({
            "name": "skill/ directory has complete structure",
            "passed": True,
            "detail": f"All expected files present in skill/: {[f.split('/')[-1] for f in expected_files]}"
        })
        total_score += 1.0
    else:
        checks.append({
            "name": "skill/ directory has complete structure",
            "passed": False,
            "detail": f"Missing files in skill/: {missing_files}"
        })

    # ── Compute final result ──────────────────────────────────────────────
    final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)
    
    # Require at minimum: name fixed + audit passes + pricing exists
    critical_passed = (
        checks[1]["passed"] and  # name ≤32 chars
        checks[2]["passed"] and  # audit OVERALL: PASS
        checks[3]["passed"]      # pricing.md with USD + positioning
    )

    result = {
        "passed": critical_passed and final_score >= 0.7,
        "score": final_score,
        "checks": checks
    }

    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    main()