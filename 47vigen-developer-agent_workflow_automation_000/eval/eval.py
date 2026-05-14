#!/usr/bin/env python3
"""
Evaluation script for the developer-agent workflow task.
Checks that the agent correctly followed the proprietary workflow:
1. Created correct feature branch (feature/[descriptive-task-name])
2. Made a feat: commit with correct type prefix
3. Merged to staging
4. Created feeCalculator.js (the new service)
5. Updated paymentService.js to integrate fees
6. Updated transaction.js with new fields
7. pnpm build succeeded (dist/build-manifest.json exists)
8. Produced a plan file with the exact proprietary header format
9. Produced a delivery_report.md with required fields
"""

import sys
import json
import subprocess
import re
from pathlib import Path

def run(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main(workspace):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {}

    # ── Check 1: Feature branch was created with correct naming convention ──────
    stdout, _, _ = run("git branch -a", cwd=ws)
    feature_branches = re.findall(r'feature/[\w\-]+', stdout)
    has_feature_branch = len(feature_branches) > 0
    branch_detail = f"Branches found: {stdout[:300]}"
    checks.append(check(
        "feature_branch_naming",
        has_feature_branch,
        f"Feature branch with 'feature/[name]' format: {'YES - ' + str(feature_branches) if has_feature_branch else 'NO. ' + branch_detail}"
    ))
    weights["feature_branch_naming"] = 0.12

    # ── Check 2: Commit exists with correct type prefix (feat/fix/refactor etc) ─
    stdout, _, _ = run("git log --oneline --all", cwd=ws)
    valid_types = ['feat:', 'fix:', 'refactor:', 'style:', 'docs:', 'chore:']
    agent_commits = [
        line for line in stdout.split('\n')
        if any(t in line for t in valid_types)
        and 'initial project scaffold' not in line
    ]
    has_typed_commit = len(agent_commits) > 0
    checks.append(check(
        "commit_type_prefix",
        has_typed_commit,
        f"Typed commits found: {agent_commits[:3] if has_typed_commit else 'NONE. Log: ' + stdout[:300]}"
    ))
    weights["commit_type_prefix"] = 0.10

    # ── Check 3: Feature branch was merged to staging ───────────────────────────
    stdout, _, _ = run("git log staging --oneline", cwd=ws)
    # Check if staging has commits beyond the initial one
    staging_commits = [l for l in stdout.split('\n') if l.strip() and 'initial project scaffold' not in l]
    merged_to_staging = len(staging_commits) > 0
    checks.append(check(
        "merged_to_staging",
        merged_to_staging,
        f"Commits on staging beyond initial: {len(staging_commits)}. Log: {stdout[:200]}"
    ))
    weights["merged_to_staging"] = 0.10

    # ── Check 4: feeCalculator.js was created ───────────────────────────────────
    fee_files = list(ws.rglob("feeCalculator.js"))
    fee_created = len(fee_files) > 0
    fee_content = ""
    if fee_created:
        fee_content = fee_files[0].read_text()
    checks.append(check(
        "fee_calculator_created",
        fee_created,
        f"feeCalculator.js found: {'YES at ' + str(fee_files[0]) if fee_created else 'NO'}"
    ))
    weights["fee_calculator_created"] = 0.12

    # ── Check 5: feeCalculator.js contains tiered fee logic ─────────────────────
    has_tier_logic = False
    tier_detail = "feeCalculator.js not found"
    if fee_content:
        # Look for evidence of tiered rates (numbers like 2.9, 2.4, 1.9 or tier names)
        has_rates = any(r in fee_content for r in ['2.9', '2.4', '1.9', 'Standard', 'Growth', 'Enterprise', 'tier'])
        has_intl = any(r in fee_content for r in ['1.5', 'international', 'USD', 'surcharge'])
        has_tier_logic = has_rates and has_intl
        tier_detail = f"Has tier rates: {has_rates}, Has international surcharge: {has_intl}"
    checks.append(check(
        "fee_tier_logic",
        has_tier_logic,
        tier_detail
    ))
    weights["fee_tier_logic"] = 0.10

    # ── Check 6: paymentService.js updated to integrate fees ────────────────────
    payment_svc = ws / "src" / "services" / "paymentService.js"
    payment_updated = False
    payment_detail = "paymentService.js not found"
    if payment_svc.exists():
        content = payment_svc.read_text()
        # Should reference feeCalculator or fee in the processPayment function
        payment_updated = ('fee' in content.lower() or 'feeCalculator' in content or 'feeAmount' in content)
        payment_detail = f"Contains fee integration: {payment_updated}. Length: {len(content)} chars"
    checks.append(check(
        "payment_service_fee_integration",
        payment_updated,
        payment_detail
    ))
    weights["payment_service_fee_integration"] = 0.10

    # ── Check 7: transaction.js updated with new fee fields ─────────────────────
    txn_model = ws / "src" / "models" / "transaction.js"
    txn_updated = False
    txn_detail = "transaction.js not found"
    if txn_model.exists():
        content = txn_model.read_text()
        has_fee_amount = 'feeAmount' in content
        has_net_amount = 'netAmount' in content
        txn_updated = has_fee_amount or has_net_amount
        txn_detail = f"feeAmount: {has_fee_amount}, netAmount: {has_net_amount}"
    checks.append(check(
        "transaction_model_fee_fields",
        txn_updated,
        txn_detail
    ))
    weights["transaction_model_fee_fields"] = 0.10

    # ── Check 8: Build succeeded (dist/build-manifest.json exists) ─────────────
    build_manifest = ws / "dist" / "build-manifest.json"
    build_succeeded = build_manifest.exists()
    build_detail = "dist/build-manifest.json not found — pnpm build may not have been run"
    if build_succeeded:
        try:
            manifest = json.loads(build_manifest.read_text())
            build_detail = f"Build manifest present. Version: {manifest.get('version')}, Time: {manifest.get('buildTime')}"
        except Exception as e:
            build_detail = f"Manifest found but invalid JSON: {e}"
            build_succeeded = False
    checks.append(check(
        "pnpm_build_success",
        build_succeeded,
        build_detail
    ))
    weights["pnpm_build_success"] = 0.12

    # ── Check 9: Plan file with exact proprietary header ────────────────────────
    plan_files = list(ws.rglob("*.md")) + list(ws.rglob("*.txt"))
    plan_header_pattern = re.compile(
        r'📋\s*IMPLEMENTATION PLAN\s*\(Generated by Cursor\s+(Sonnet 4\.6|Opus 4\.6|Composer 1\.5)\)',
        re.IGNORECASE
    )
    plan_found = False
    plan_model_correct = False
    plan_detail = "No file found containing the required plan header"

    for f in plan_files:
        try:
            content = f.read_text(errors='replace')
            m = plan_header_pattern.search(content)
            if m:
                plan_found = True
                model_used = m.group(1)
                # For medium complexity (3 files, new feature, moderate logic) → Sonnet 4.6
                plan_model_correct = (model_used == "Sonnet 4.6")
                plan_detail = f"Plan header found in {f.name}. Model used: '{model_used}'. Expected: 'Sonnet 4.6'. Correct: {plan_model_correct}"
                break
        except Exception:
            continue

    checks.append(check(
        "plan_header_format",
        plan_found,
        plan_detail
    ))
    weights["plan_header_format"] = 0.08

    checks.append(check(
        "plan_model_selection_sonnet",
        plan_model_correct,
        plan_detail if plan_found else "Plan header not found at all"
    ))
    weights["plan_model_selection_sonnet"] = 0.08

    # ── Check 10: Delivery report with required fields ───────────────────────────
    report_files = list(ws.rglob("delivery_report*")) + list(ws.rglob("*report*"))
    report_found = False
    report_complete = False
    report_detail = "No delivery report file found"

    required_report_fields = [
        ('branch', ['branch']),
        ('build', ['build']),
        ('files', ['file', 'changed']),
        ('summary', ['summary', 'implementation']),
    ]

    for f in report_files:
        try:
            content = f.read_text(errors='replace').lower()
            report_found = True
            found_fields = []
            for field_name, keywords in required_report_fields:
                if any(kw in content for kw in keywords):
                    found_fields.append(field_name)
            report_complete = len(found_fields) >= 3
            report_detail = f"Report found: {f.name}. Fields present: {found_fields} ({len(found_fields)}/4). Complete: {report_complete}"
            break
        except Exception as e:
            report_detail = f"Error reading report: {e}"
            continue

    checks.append(check(
        "delivery_report_exists",
        report_found,
        report_detail
    ))
    weights["delivery_report_exists"] = 0.04

    checks.append(check(
        "delivery_report_complete",
        report_complete,
        report_detail
    ))
    weights["delivery_report_complete"] = 0.04

    # ── Compute weighted score ───────────────────────────────────────────────────
    total_weight = sum(weights.values())
    score = 0.0
    for c in checks:
        w = weights.get(c["name"], 0.0)
        if c["passed"]:
            score += w

    score = round(score / total_weight, 4)
    passed = score >= 0.70  # Must pass at least 70%

    output = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)