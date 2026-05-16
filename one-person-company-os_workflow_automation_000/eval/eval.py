#!/usr/bin/env python3
"""
Evaluation script for the one-person-company-os task.

Checks:
1. Workspace for 律智科技 exists under /app/workspace (or discoverable via rglob)
2. 00-经营总盘.md exists and contains correct company/product/stage data
3. 04-产品与上线状态.md contains demo state and v0.1 version label
4. 09-本周唯一主目标.md contains the correct arena (sales) and goal about first clients
5. 03-机会与成交管道.md contains pipeline snapshot with talking>=2 and proposal>=1
6. 07-资产与自动化.md contains a recorded asset of kind 'templates' for client onboarding
7. All 13 canonical workspace files exist
"""

import sys
import json
import re
from pathlib import Path

def find_company_workspace(base: Path, company_name: str):
    """Find the company workspace directory."""
    candidates = list(base.rglob(company_name))
    # Prefer the one under 'workspace/' if multiple found
    for c in candidates:
        if c.is_dir() and 'archive' not in str(c) and 'wrong_workspace' not in str(c):
            return c
    for c in candidates:
        if c.is_dir():
            return c
    return None

def run_checks(workspace_arg: str):
    checks = []
    score_weights = []

    base = Path(workspace_arg) if workspace_arg else Path("/app")

    # ── Check 0: Find the company workspace ──────────────────────────────────
    company_ws = find_company_workspace(base, "律智科技")
    if company_ws is None:
        # Also search all of /app
        company_ws = find_company_workspace(Path("/app"), "律智科技")

    checks.append({
        "name": "company_workspace_exists",
        "passed": company_ws is not None and company_ws.is_dir(),
        "detail": f"Found workspace at: {company_ws}" if company_ws else "No directory named '律智科技' found anywhere under /app"
    })
    score_weights.append(1.0)

    if company_ws is None:
        # Can't proceed without workspace
        for name in [
            "all_13_canonical_files_present",
            "overview_has_correct_metadata",
            "product_state_is_demo",
            "product_has_version_label",
            "focus_arena_is_sales",
            "focus_goal_mentions_clients",
            "pipeline_has_talking_prospects",
            "pipeline_has_proposal",
            "asset_kind_is_templates",
            "asset_mentions_onboarding",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Workspace not found; cannot check."})
            score_weights.append(1.0)

        total = sum(w for w in score_weights)
        passed_score = sum(w for c, w in zip(checks, score_weights) if c["passed"])
        return {
            "passed": False,
            "score": round(passed_score / total, 3),
            "checks": checks
        }

    # ── Check 1: All 13 canonical files present ───────────────────────────────
    CANONICAL_FILES = [
        "00-经营总盘.md",
        "01-创始人约束.md",
        "02-价值承诺与报价.md",
        "03-机会与成交管道.md",
        "04-产品与上线状态.md",
        "05-客户交付与回款.md",
        "06-现金流与经营健康.md",
        "07-资产与自动化.md",
        "08-风险与关键决策.md",
        "09-本周唯一主目标.md",
        "10-今日最短动作.md",
        "11-协作记忆.md",
        "12-会话交接.md",
    ]
    missing_files = []
    for fname in CANONICAL_FILES:
        if not (company_ws / fname).exists():
            missing_files.append(fname)

    checks.append({
        "name": "all_13_canonical_files_present",
        "passed": len(missing_files) == 0,
        "detail": f"Missing: {missing_files}" if missing_files else "All 13 canonical files present"
    })
    score_weights.append(2.0)

    # ── Check 2: 00-经营总盘.md has correct metadata ─────────────────────────
    try:
        overview = (company_ws / "00-经营总盘.md").read_text(encoding="utf-8")
        has_company = "律智科技" in overview
        has_product = "律智审阅" in overview
        has_stage = "构建期" in overview
        checks.append({
            "name": "overview_has_correct_metadata",
            "passed": has_company and has_product and has_stage,
            "detail": f"company={has_company}, product={has_product}, stage=构建期:{has_stage}"
        })
    except Exception as e:
        checks.append({"name": "overview_has_correct_metadata", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Check 3: 04-产品与上线状态.md has state=demo ──────────────────────────
    try:
        product_content = (company_ws / "04-产品与上线状态.md").read_text(encoding="utf-8")
        has_demo = "demo" in product_content.lower()
        checks.append({
            "name": "product_state_is_demo",
            "passed": has_demo,
            "detail": f"'demo' found in product file: {has_demo}. Snippet: {product_content[:300]}"
        })
    except Exception as e:
        checks.append({"name": "product_state_is_demo", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Check 4: 04-产品与上线状态.md has a version label (v0.x format) ───────
    try:
        product_content = (company_ws / "04-产品与上线状态.md").read_text(encoding="utf-8")
        # Accept any version string like v0.1, v0.1 hero, v1.0, etc.
        has_version = bool(re.search(r'v\d+\.\d+', product_content, re.IGNORECASE))
        checks.append({
            "name": "product_has_version_label",
            "passed": has_version,
            "detail": f"Version pattern found: {has_version}. Snippet: {product_content[:300]}"
        })
    except Exception as e:
        checks.append({"name": "product_has_version_label", "passed": False, "detail": str(e)})
    score_weights.append(1.0)

    # ── Check 5: 09-本周唯一主目标.md has arena=sales ─────────────────────────
    try:
        goal_content = (company_ws / "09-本周唯一主目标.md").read_text(encoding="utf-8")
        has_sales_arena = "sales" in goal_content.lower()
        checks.append({
            "name": "focus_arena_is_sales",
            "passed": has_sales_arena,
            "detail": f"'sales' arena found: {has_sales_arena}. Content: {goal_content[:300]}"
        })
    except Exception as e:
        checks.append({"name": "focus_arena_is_sales", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Check 6: 09-本周唯一主目标.md mentions client/customer/first ─────────
    try:
        goal_content = (company_ws / "09-本周唯一主目标.md").read_text(encoding="utf-8")
        # Accept Chinese or English references to clients/customers
        has_client_ref = bool(re.search(
            r'(客户|client|customer|对话|paying|首|第一|first)',
            goal_content, re.IGNORECASE
        ))
        checks.append({
            "name": "focus_goal_mentions_clients",
            "passed": has_client_ref,
            "detail": f"Client/customer reference found: {has_client_ref}. Content: {goal_content[:400]}"
        })
    except Exception as e:
        checks.append({"name": "focus_goal_mentions_clients", "passed": False, "detail": str(e)})
    score_weights.append(1.0)

    # ── Check 7: 03-机会与成交管道.md has talking prospects (>=2) ────────────
    try:
        pipeline_content = (company_ws / "03-机会与成交管道.md").read_text(encoding="utf-8")
        # Look for 对话中: N  (N >= 2)
        talking_matches = re.findall(r'对话[中]?[：:]\s*(\d+)', pipeline_content)
        has_talking = False
        talking_val = 0
        for m in talking_matches:
            val = int(m)
            if val >= 2:
                has_talking = True
                talking_val = val
                break
        checks.append({
            "name": "pipeline_has_talking_prospects",
            "passed": has_talking,
            "detail": f"Found talking value(s): {talking_matches}. Needs >=2. Got: {talking_val}"
        })
    except Exception as e:
        checks.append({"name": "pipeline_has_talking_prospects", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Check 8: 03-机会与成交管道.md has proposals (>=1) ────────────────────
    try:
        pipeline_content = (company_ws / "03-机会与成交管道.md").read_text(encoding="utf-8")
        proposal_matches = re.findall(r'已发提案[：:]\s*(\d+)', pipeline_content)
        has_proposal = False
        for m in proposal_matches:
            if int(m) >= 1:
                has_proposal = True
                break
        checks.append({
            "name": "pipeline_has_proposal",
            "passed": has_proposal,
            "detail": f"Found proposal value(s): {proposal_matches}. Needs >=1."
        })
    except Exception as e:
        checks.append({"name": "pipeline_has_proposal", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Check 9: 07-资产与自动化.md has a 'templates' asset ──────────────────
    try:
        asset_content = (company_ws / "07-资产与自动化.md").read_text(encoding="utf-8")
        has_templates = "[templates]" in asset_content
        checks.append({
            "name": "asset_kind_is_templates",
            "passed": has_templates,
            "detail": f"'[templates]' found in asset file: {has_templates}. Content: {asset_content[:400]}"
        })
    except Exception as e:
        checks.append({"name": "asset_kind_is_templates", "passed": False, "detail": str(e)})
    score_weights.append(2.0)

    # ── Check 10: 07-资产与自动化.md mentions onboarding ─────────────────────
    try:
        asset_content = (company_ws / "07-资产与自动化.md").read_text(encoding="utf-8")
        has_onboarding = bool(re.search(r'(onboarding|话术|入门|引导|接入)', asset_content, re.IGNORECASE))
        checks.append({
            "name": "asset_mentions_onboarding",
            "passed": has_onboarding,
            "detail": f"Onboarding reference found: {has_onboarding}. Content: {asset_content[:400]}"
        })
    except Exception as e:
        checks.append({"name": "asset_mentions_onboarding", "passed": False, "detail": str(e)})
    score_weights.append(1.5)

    # ── Final scoring ─────────────────────────────────────────────────────────
    total_weight = sum(score_weights)
    passed_weight = sum(w for c, w in zip(checks, score_weights) if c["passed"])
    score = round(passed_weight / total_weight, 3)

    # Must pass all critical checks (workspace exists + all files + product state + arena + asset kind)
    critical_checks = {
        "company_workspace_exists",
        "all_13_canonical_files_present",
        "product_state_is_demo",
        "focus_arena_is_sales",
        "asset_kind_is_templates",
        "pipeline_has_talking_prospects",
        "pipeline_has_proposal",
    }
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    return {
        "passed": critical_passed and score >= 0.80,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/app"
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))