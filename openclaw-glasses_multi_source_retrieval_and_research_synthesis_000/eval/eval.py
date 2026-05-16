import sys
import json
import re
from pathlib import Path

def load_jsonl(path):
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── CHECK 1: research_report.json exists ──────────────────────────────────
    report_candidates = list(workspace.rglob("research_report.json"))
    if not report_candidates:
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "research_report.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = report_candidates[0]
    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": f"Found at {report_path.relative_to(workspace)}"})
    total_score += 0.05

    # ── CHECK 2: report is valid JSON ─────────────────────────────────────────
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        checks.append({"name": "report_valid_json", "passed": True, "detail": "Valid JSON"})
        total_score += 0.05
    except Exception as e:
        checks.append({"name": "report_valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    # ── CHECK 3: search.py was invoked (invocation log exists) ───────────────
    inv_log = workspace / "logs" / "search_invocations.jsonl"
    if not inv_log.exists():
        checks.append({"name": "search_script_invoked", "passed": False,
                        "detail": "No invocation log found; search.py was never called"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    try:
        invocations = load_jsonl(inv_log)
    except Exception as e:
        checks.append({"name": "search_script_invoked", "passed": False,
                        "detail": f"Could not parse invocation log: {e}"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    if not invocations:
        checks.append({"name": "search_script_invoked", "passed": False,
                        "detail": "Invocation log is empty"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    checks.append({"name": "search_script_invoked", "passed": True,
                    "detail": f"{len(invocations)} invocation(s) recorded"})
    total_score += 0.10

    # ── CHECK 4: Multi-query form used for comparison part ───────────────────
    # At least one invocation must use --queries (multi-query) for comparison
    multi_query_invocations = [inv for inv in invocations if inv.get("queries") is not None and len(inv.get("queries", [])) >= 2]
    if multi_query_invocations:
        mq = multi_query_invocations[0]
        checks.append({"name": "multi_query_used_for_comparison", "passed": True,
                        "detail": f"--queries with {len(mq['queries'])} sub-queries found: {mq['queries']}"})
        total_score += 0.15
    else:
        checks.append({"name": "multi_query_used_for_comparison", "passed": False,
                        "detail": "No invocation found using --queries with 2+ sub-queries for comparison. "
                                  "SKILL.md requires --queries for comparison intents."})

    # ── CHECK 5: comparison invocations use --mode deep ───────────────────────
    comparison_invocations = [inv for inv in invocations if inv.get("intent") == "comparison"]
    if comparison_invocations:
        all_deep = all(inv.get("mode") == "deep" for inv in comparison_invocations)
        if all_deep:
            checks.append({"name": "comparison_uses_mode_deep", "passed": True,
                            "detail": f"{len(comparison_invocations)} comparison invocation(s), all use --mode deep"})
            total_score += 0.10
        else:
            bad = [inv for inv in comparison_invocations if inv.get("mode") != "deep"]
            checks.append({"name": "comparison_uses_mode_deep", "passed": False,
                            "detail": f"{len(bad)} comparison invocation(s) do NOT use --mode deep. "
                                      f"SKILL.md: comparison → deep mode. Modes found: {[inv['mode'] for inv in bad]}"})
    else:
        checks.append({"name": "comparison_uses_mode_deep", "passed": False,
                        "detail": "No invocation found with --intent comparison"})

    # ── CHECK 6: Finance/status invocation uses correct source list ───────────
    # Must include alpha-vantage AND binance in --source for the ETH price query
    finance_invocations = [
        inv for inv in invocations
        if inv.get("intent") == "status" and inv.get("source") is not None
        and "binance" in inv.get("source", "")
        and "alpha-vantage" in inv.get("source", "")
    ]
    if finance_invocations:
        fin = finance_invocations[0]
        checks.append({"name": "finance_source_list_correct", "passed": True,
                        "detail": f"Finance invocation found with source='{fin['source']}'"})
        total_score += 0.15
    else:
        # Also accept: source has binance without alpha-vantage (partial credit if at least binance present)
        binance_only = [inv for inv in invocations if inv.get("intent") == "status"
                        and inv.get("source") and "binance" in inv.get("source", "")]
        if binance_only:
            checks.append({"name": "finance_source_list_correct", "passed": False,
                            "detail": "binance found in status invocation but alpha-vantage missing from --source. "
                                      "SKILL.md requires both for ETH price with broader context."})
            total_score += 0.05  # partial
        else:
            checks.append({"name": "finance_source_list_correct", "passed": False,
                            "detail": "No status invocation with binance in --source found. "
                                      "Finance-aware path requires --source alpha-vantage,binance,... for crypto+tradfi."})

    # ── CHECK 7: Finance invocation uses mode=deep (quote+context) ─────────
    # SKILL.md: "deep when combining quote + broader context"
    finance_deep_invocations = [
        inv for inv in invocations
        if inv.get("intent") == "status"
        and inv.get("source") and "binance" in inv.get("source", "")
        and inv.get("mode") in ("deep", "fast")
    ]
    if finance_deep_invocations:
        modes_used = list(set(inv["mode"] for inv in finance_deep_invocations))
        # Accept 'deep' or 'fast' — both are valid per SKILL.md depending on use case
        checks.append({"name": "finance_invocation_mode_valid", "passed": True,
                        "detail": f"Finance invocation mode(s): {modes_used} — valid per SKILL.md"})
        total_score += 0.05
    else:
        checks.append({"name": "finance_invocation_mode_valid", "passed": False,
                        "detail": "No status invocation with binance found at all"})

    # ── CHECK 8: Report contains comparison section (themed, not per-provider) ─
    report_text = report_path.read_text(encoding="utf-8").lower()

    # Look for comparison-themed keys or sections
    has_comparison_section = any(
        k in report_text for k in [
            "comparison", "solana", "ethereum", "tps", "throughput",
            "performance", "ecosystem", "defi", "vs"
        ]
    )
    if has_comparison_section:
        checks.append({"name": "report_has_comparison_content", "passed": True,
                        "detail": "Report contains comparison-themed content (Solana/Ethereum comparison)"})
        total_score += 0.10
    else:
        checks.append({"name": "report_has_comparison_content", "passed": False,
                        "detail": "Report lacks any comparison content about the blockchain platforms"})

    # ── CHECK 9: Report contains finance/price section ─────────────────────────
    has_finance_section = any(
        k in report_text for k in [
            "eth", "ethereum price", "price", "realtime", "real-time",
            "binance", "alpha-vantage", "3,41", "3412", "quote", "usdt"
        ]
    )
    if has_finance_section:
        checks.append({"name": "report_has_finance_content", "passed": True,
                        "detail": "Report contains finance/price content (ETH realtime data)"})
        total_score += 0.10
    else:
        checks.append({"name": "report_has_finance_content", "passed": False,
                        "detail": "Report lacks ETH price/realtime content"})

    # ── CHECK 10: Report is structured by theme (not just provider list) ───────
    # The SKILL.md says "Group by themes or findings", "Answer first, then cite"
    # We check that the JSON has structured sections/keys rather than a flat provider dump

    report_is_object = isinstance(report, dict)
    if report_is_object:
        keys = list(report.keys())
        # Must have more than just "results" or provider names — expect thematic sections
        provider_only_keys = {"exa", "tavily", "binance", "alpha-vantage", "gemini", "kimi", "grok"}
        non_provider_keys = [k for k in keys if k.lower() not in provider_only_keys]
        if len(non_provider_keys) >= 2:
            checks.append({"name": "report_structured_by_theme", "passed": True,
                            "detail": f"Report has thematic structure with keys: {keys[:8]}"})
            total_score += 0.10
        else:
            checks.append({"name": "report_structured_by_theme", "passed": False,
                            "detail": f"Report appears to be organized by provider, not by theme. Keys: {keys}. "
                                      "SKILL.md: synthesize by topic, not by provider."})
    else:
        # Array is okay if elements have non-provider theme keys
        checks.append({"name": "report_structured_by_theme", "passed": False,
                        "detail": "Report is not a JSON object; expected thematic dict structure"})

    # ── CHECK 11: Report includes conflict callout ─────────────────────────────
    conflict_keywords = ["conflict", "contradict", "discrepan", "disagree", "differs", 
                         "inconsistent", "conflicting", "vary", "single-source", "caution",
                         "note:", "however", "whereas", "but according"]
    has_conflict = any(kw in report_text for kw in conflict_keywords)
    if has_conflict:
        checks.append({"name": "report_calls_out_conflicts", "passed": True,
                        "detail": "Report explicitly calls out conflicting/uncertain claims"})
        total_score += 0.10
    else:
        checks.append({"name": "report_calls_out_conflicts", "passed": False,
                        "detail": "Report does not call out conflicting claims or source caveats. "
                                  "SKILL.md: 'Call out conflicts explicitly'."})

    # ── CHECK 12: Finance data includes timestamp or source attribution ────────
    has_timestamp = any(kw in report_text for kw in [
        "timestamp", "as of", "2024", "09:5", "09:4", "t09", "realtime", "real-time",
        "binance", "alpha-vantage", "market open"
    ])
    if has_timestamp:
        checks.append({"name": "finance_data_has_timestamp_or_source", "passed": True,
                        "detail": "Finance data includes timestamp or source attribution"})
        total_score += 0.05
    else:
        checks.append({"name": "finance_data_has_timestamp_or_source", "passed": False,
                        "detail": "Finance realtime data lacks timestamp/source. "
                                  "SKILL.md: 'always note the timestamp and source' for finance realtime data."})

    # ── Final scoring ──────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    overall_passed = (total_score >= 0.60) and all(
        c["passed"] for c in checks if c["name"] in [
            "report_file_exists",
            "report_valid_json",
            "search_script_invoked",
            "multi_query_used_for_comparison",
            "finance_source_list_correct",
            "report_has_comparison_content",
            "report_has_finance_content",
        ]
    )

    print(json.dumps({
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])