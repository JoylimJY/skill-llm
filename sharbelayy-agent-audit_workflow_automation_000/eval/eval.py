import json
import re
import sys
from pathlib import Path

def load_history(workspace):
    """Load all cron run history and compute per-cron stats."""
    history_dir = Path(workspace) / ".openclaw/cron/history"
    stats = {}
    for f in history_dir.glob("*.json"):
        data = json.loads(f.read_text())
        cron_id = data["cron_id"]
        runs = data["runs"]
        if not runs:
            stats[cron_id] = {"run_count": 0}
            continue
        total = len(runs)
        success_count = sum(1 for r in runs if r.get("success", False))
        avg_output = sum(r["output_tokens"] for r in runs) / total
        avg_input = sum(r["input_tokens"] for r in runs) / total
        avg_runtime = sum(r["runtime_seconds"] for r in runs) / total
        avg_tools = sum(r.get("tool_calls", 0) for r in runs) / total
        error_rate = (total - success_count) / total
        stats[cron_id] = {
            "run_count": total,
            "avg_output": avg_output,
            "avg_input": avg_input,
            "avg_runtime": avg_runtime,
            "avg_tools": avg_tools,
            "error_rate": error_rate,
            "success_rate": success_count / total,
        }
    return stats

def find_report(workspace):
    """Find the generated markdown report."""
    ws = Path(workspace)
    # Look for any .md file that's not in references/ or docs/
    candidates = []
    for p in ws.rglob("*.md"):
        parts = p.parts
        skip_dirs = {"references", "docs", ".git"}
        if any(d in parts for d in skip_dirs):
            continue
        candidates.append(p)
    # Also check common names
    common_names = [
        "audit_report.md", "audit-report.md", "report.md", "cost_report.md",
        "cost-report.md", "agent_audit.md", "optimization_report.md",
        "audit.md", "savings_report.md",
    ]
    for name in common_names:
        p = ws / name
        if p.exists():
            return p
    if candidates:
        # Return newest
        return max(candidates, key=lambda p: p.stat().st_mtime)
    return None

def eval_report(workspace):
    checks = []

    # ── Locate report ─────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False,
                        "detail": "No markdown report file found anywhere in workspace."}]
        }

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_readable", "passed": False,
                        "detail": f"Could not read report: {e}"}]
        }

    content_lower = content.lower()
    stats = load_history(workspace)

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Report is a markdown file with an overview section
    # ─────────────────────────────────────────────────────────────────────────
    has_overview = bool(re.search(r'#.*overview|#.*summary|#.*agent audit|total.*agent|total.*cron', content_lower))
    checks.append({
        "name": "report_has_overview",
        "passed": has_overview,
        "detail": f"Report at {report_path} {'has' if has_overview else 'missing'} an overview/summary section."
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: cron-001 (Trade Price Alert) IS recommended for downgrade
    #   - Simple signals: systemEvent, <150 tokens output avg, <10s runtime, 0 tool calls, 100% success
    #   - Current: claude-opus-4. Should recommend: claude-haiku-3
    # ─────────────────────────────────────────────────────────────────────────
    # Check that Trade Price Alert downgrade is recommended
    trade_alert_patterns = [
        r'trade price alert',
        r'trade.*alert',
        r'cron-001',
    ]
    mentions_trade_alert = any(re.search(p, content_lower) for p in trade_alert_patterns)
    
    # Should mention downgrade to haiku
    downgrade_to_haiku_patterns = [
        r'trade price alert.*haiku',
        r'haiku.*trade price alert',
        r'cron-001.*haiku',
        r'downgrade.*trade.*alert',
        r'trade.*alert.*downgrade',
        r'trade.*alert.*haiku',
    ]
    # More flexible: check for haiku recommendation near trade alert content
    # Split into blocks and check proximity
    blocks = re.split(r'\n#{1,3} ', content_lower)
    trade_block_has_haiku = False
    for block in blocks:
        if 'trade' in block and 'alert' in block:
            if 'haiku' in block or 'downgrade' in block:
                trade_block_has_haiku = True
                break
    
    downgrade_cron001 = (mentions_trade_alert and trade_block_has_haiku) or \
                         any(re.search(p, content_lower) for p in downgrade_to_haiku_patterns)
    
    checks.append({
        "name": "cron001_downgrade_recommended",
        "passed": downgrade_cron001,
        "detail": (
            "cron-001 (Trade Price Alert) SHOULD be recommended for downgrade to haiku-3. "
            f"Report mentions trade alert: {mentions_trade_alert}. "
            f"Downgrade to haiku found: {trade_block_has_haiku}. "
            "It's a systemEvent, <150 token output, 0 tool calls, 100% success rate — clearly Simple tier."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: cron-002 (Compliance Audit Scan) is NOT recommended for downgrade
    #   Override rules: security task + thinking=True → NEVER downgrade
    # ─────────────────────────────────────────────────────────────────────────
    compliance_mentioned = bool(re.search(r'compliance|cron-002', content_lower))
    
    # Should NOT recommend downgrading compliance
    compliance_downgrade_patterns = [
        r'downgrade.*compliance',
        r'compliance.*downgrade',
        r'compliance.*haiku',
        r'compliance.*sonnet',
        r'compliance.*gpt-4o-mini',
        r'compliance.*grok-3-mini',
    ]
    compliance_downgrade_suggested = any(re.search(p, content_lower) for p in compliance_downgrade_patterns)
    
    # Check: compliance should be mentioned (in breakdown) but NOT downgraded
    compliance_check_passed = compliance_mentioned and not compliance_downgrade_suggested
    checks.append({
        "name": "cron002_no_downgrade_security_thinking",
        "passed": compliance_check_passed,
        "detail": (
            f"cron-002 (Compliance Audit Scan) must NOT be recommended for downgrade "
            f"(security task + thinking=True). "
            f"Mentioned: {compliance_mentioned}. "
            f"Incorrectly suggested downgrade: {compliance_downgrade_suggested}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: cron-004 (PR Code Review) is NOT recommended for downgrade
    #   Override rule: CODING TASK → NEVER downgrade
    # ─────────────────────────────────────────────────────────────────────────
    code_review_mentioned = bool(re.search(r'pr code review|code review|cron-004', content_lower))
    
    code_review_downgrade_patterns = [
        r'downgrade.*code review',
        r'code review.*downgrade',
        r'pr.*review.*downgrade',
        r'code review.*haiku',
        r'code review.*sonnet',
        r'pr.*code.*haiku',
        r'cron-004.*downgrade',
        r'cron-004.*haiku',
        r'cron-004.*sonnet',
    ]
    code_review_downgrade_suggested = any(re.search(p, content_lower) for p in code_review_downgrade_patterns)
    
    code_review_check_passed = not code_review_downgrade_suggested
    checks.append({
        "name": "cron004_no_downgrade_coding_task",
        "passed": code_review_check_passed,
        "detail": (
            f"cron-004 (PR Code Review) must NOT be recommended for downgrade "
            f"(coding task override rule). "
            f"Mentioned: {code_review_mentioned}. "
            f"Incorrectly suggested downgrade: {code_review_downgrade_suggested}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: cron-005 (Microservice Health Ping) is NOT recommended for downgrade
    #   Despite being simple by output/name, error rate is ~15% > 10% → NO downgrade
    # ─────────────────────────────────────────────────────────────────────────
    ping_mentioned = bool(re.search(r'microservice health|health ping|ping watcher|cron-005', content_lower))
    
    ping_downgrade_patterns = [
        r'downgrade.*health ping',
        r'health ping.*downgrade',
        r'microservice.*downgrade',
        r'ping.*downgrade',
        r'ping watcher.*haiku',
        r'health ping.*haiku',
        r'cron-005.*downgrade',
        r'cron-005.*haiku',
    ]
    ping_downgrade_suggested = any(re.search(p, content_lower) for p in ping_downgrade_patterns)
    
    ping_check_passed = not ping_downgrade_suggested
    
    # Compute actual error rate for detail
    cron005_stats = stats.get("cron-005", {})
    actual_error_rate = cron005_stats.get("error_rate", -1)
    
    checks.append({
        "name": "cron005_no_downgrade_high_error_rate",
        "passed": ping_check_passed,
        "detail": (
            f"cron-005 (Microservice Health Ping) must NOT be recommended for downgrade. "
            f"Error rate is ~{actual_error_rate:.1%} which exceeds the 10% threshold. "
            f"Ping mentioned: {ping_mentioned}. "
            f"Incorrectly suggested downgrade: {ping_downgrade_suggested}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: cron-006 (Regulatory Weekly Brief) marked as insufficient data
    #   Only 3 runs < 5 run threshold → must NOT make recommendations
    # ─────────────────────────────────────────────────────────────────────────
    cron006_stats = stats.get("cron-006", {})
    actual_run_count = cron006_stats.get("run_count", -1)
    
    regulatory_mentioned = bool(re.search(r'regulatory|weekly brief|cron-006', content_lower))
    
    insufficient_data_patterns = [
        r'insufficient data.*regulatory',
        r'regulatory.*insufficient data',
        r'insufficient data.*cron-006',
        r'cron-006.*insufficient',
        r'regulatory.*insufficient',
        r'insufficient.*brief',
        r'not enough.*regulatory',
        r'regulatory.*not enough',
        r'too few.*runs.*regulatory',
        r'regulatory.*too few',
        r'fewer than 5',
        r'less than 5.*runs',
        r'only.*3.*runs',
        r'3.*runs.*insufficient',
    ]
    
    regulatory_downgrade_patterns = [
        r'downgrade.*regulatory',
        r'regulatory.*downgrade',
        r'regulatory.*grok-3-mini',
        r'regulatory.*grok.*mini',
        r'cron-006.*downgrade',
        r'brief.*downgrade.*grok',
    ]
    
    insufficient_flagged = any(re.search(p, content_lower) for p in insufficient_data_patterns)
    regulatory_downgrade_suggested = any(re.search(p, content_lower) for p in regulatory_downgrade_patterns)
    
    # Pass if: insufficient data mentioned OR downgrade NOT suggested
    # (Agent might just silently exclude it, which is also acceptable)
    cron006_check_passed = insufficient_flagged or not regulatory_downgrade_suggested
    
    checks.append({
        "name": "cron006_insufficient_data_no_recommendation",
        "passed": cron006_check_passed,
        "detail": (
            f"cron-006 (Regulatory Weekly Brief) has only {actual_run_count} runs (<5 threshold). "
            f"Should be marked 'insufficient data' or excluded from recommendations. "
            f"Insufficient data flagged: {insufficient_flagged}. "
            f"Incorrectly suggested downgrade: {regulatory_downgrade_suggested}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Monthly cost calculation for cron-001 using correct pricing formula
    #   cron-001: avg_input ~310, avg_output ~120 tokens, 96 runs/day
    #   claude-opus-4: $15/M input, $75/M output
    #   cost_per_run = (310/1M * 15) + (120/1M * 75) = 0.004650 + 0.009000 = $0.013650
    #   monthly = 0.013650 * 96 * 30 = $39.31 (approx)
    #   Tolerance: $25 to $60 range for monthly cost of cron-001
    # ─────────────────────────────────────────────────────────────────────────
    
    # Look for dollar amounts in the report near trade alert / cron-001
    dollar_amounts = re.findall(r'\$\s*(\d+(?:\.\d+)?)', content)
    float_amounts = [float(a) for a in dollar_amounts]
    
    # Check if any amount falls in expected range for cron-001 monthly cost (~$39)
    # or the total monthly cost (which would be much larger)
    cron001_cost_reasonable = any(25 <= v <= 60 for v in float_amounts)
    
    # Alternative: check savings estimate is present for cron-001 recommendation
    savings_mentioned = bool(re.search(r'saving|estimated.*\$|per.*month|\$/month|monthly.*cost', content_lower))
    
    cost_check_passed = cron001_cost_reasonable or savings_mentioned
    checks.append({
        "name": "cost_calculations_present",
        "passed": cost_check_passed,
        "detail": (
            f"Report should include cost calculations using the pricing formula. "
            f"Dollar amounts found: {sorted(set(float_amounts))}. "
            f"Amount in cron-001 expected range ($25-$60): {cron001_cost_reasonable}. "
            f"Savings/cost language present: {savings_mentioned}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: cron-003 (Market Research Digest) — gpt-4o is correct tier (Medium)
    #   Should NOT recommend downgrading (already at correct tier)
    #   OR if recommending change, it should NOT be to a Simple tier model
    # ─────────────────────────────────────────────────────────────────────────
    digest_downgrade_patterns = [
        r'downgrade.*market research',
        r'market research.*downgrade.*gpt-4o-mini',
        r'digest.*gpt-4o-mini',
        r'market.*digest.*downgrade.*mini',
        r'cron-003.*gpt-4o-mini',
        r'cron-003.*downgrade',
    ]
    digest_inappropriate_downgrade = any(re.search(p, content_lower) for p in digest_downgrade_patterns)
    
    checks.append({
        "name": "cron003_no_inappropriate_downgrade",
        "passed": not digest_inappropriate_downgrade,
        "detail": (
            f"cron-003 (Market Research Digest) uses gpt-4o (Medium tier) which matches its "
            f"Medium classification. Should NOT be downgraded to Simple tier (gpt-4o-mini). "
            f"Inappropriate downgrade suggested: {digest_inappropriate_downgrade}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: Recommendations sorted by savings potential
    #   cron-001 (96 runs/day) should appear as TOP savings opportunity
    # ─────────────────────────────────────────────────────────────────────────
    rec_section_match = re.search(
        r'recommendation[s]?(.*?)(?=\n#{1,2} |$)', 
        content_lower, 
        re.DOTALL
    )
    
    if rec_section_match:
        rec_text = rec_section_match.group(1)
        # In recommendations section, trade alert / cron-001 should appear
        trade_in_rec = bool(re.search(r'trade.*alert|cron-001', rec_text))
    else:
        # Check if recommendations exist anywhere and trade alert is in them
        trade_in_rec = bool(re.search(r'recommend.*trade|trade.*recommend', content_lower))
    
    checks.append({
        "name": "recommendations_include_cron001",
        "passed": trade_in_rec or downgrade_cron001,
        "detail": (
            f"Recommendations section should prominently feature cron-001 (Trade Price Alert) "
            f"as the top savings opportunity. "
            f"Trade alert in recommendations: {trade_in_rec}. "
            f"Downgrade recommended: {downgrade_cron001}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 10: Risk/confidence levels present in recommendations
    # ─────────────────────────────────────────────────────────────────────────
    risk_patterns = [
        r'\brisk\b.*\b(low|medium|high)\b',
        r'\b(low|medium|high)\b.*\brisk\b',
        r'confidence.*\b(low|medium|high)\b',
        r'\b(low|medium|high)\b.*confidence',
    ]
    has_risk_confidence = any(re.search(p, content_lower) for p in risk_patterns)
    
    checks.append({
        "name": "risk_confidence_levels_present",
        "passed": has_risk_confidence,
        "detail": (
            f"Report must include risk levels (LOW/MEDIUM/HIGH) and confidence scores "
            f"for each recommendation. Found: {has_risk_confidence}."
        )
    })

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────────
    weights = {
        "report_has_overview": 0.05,
        "cron001_downgrade_recommended": 0.20,       # Core positive recommendation
        "cron002_no_downgrade_security_thinking": 0.15,  # Override rule: security+thinking
        "cron004_no_downgrade_coding_task": 0.15,    # Override rule: coding
        "cron005_no_downgrade_high_error_rate": 0.15,  # Override rule: error rate >10%
        "cron006_insufficient_data_no_recommendation": 0.10,  # Edge case: <5 runs
        "cost_calculations_present": 0.07,
        "cron003_no_inappropriate_downgrade": 0.05,
        "recommendations_include_cron001": 0.04,
        "risk_confidence_levels_present": 0.04,
    }

    total_weight = sum(weights.values())
    score = sum(
        weights.get(c["name"], 0) * (1 if c["passed"] else 0)
        for c in checks
    ) / total_weight

    passed = score >= 0.70

    return {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = eval_report(workspace)
    print(json.dumps(result, indent=2))