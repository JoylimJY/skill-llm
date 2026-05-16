import sys
import json
import re
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Find the output file ─────────────────────────────────────────────────────
# Agent is asked to produce gougoubi_proposal.json

found_files = list(Path(workspace).rglob("gougoubi_proposal.json"))
if not found_files:
    add_check("output_file_exists", False, "gougoubi_proposal.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

output_path = found_files[0]
add_check("output_file_exists", True, f"Found at {output_path}")

try:
    with open(output_path, "r", encoding="utf-8") as f:
        raw = f.read()
    data = json.loads(raw)
except Exception as e:
    add_check("json_parseable", False, f"Cannot parse JSON: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

add_check("json_parseable", True, "Valid JSON")

# ── Check top-level structure ────────────────────────────────────────────────
has_ok = "ok" in data
add_check("has_ok_field", has_ok, f"ok={data.get('ok')}")

has_analysis = "analysis" in data and isinstance(data["analysis"], dict)
add_check("has_analysis_block", has_analysis, "analysis block present" if has_analysis else "missing analysis block")

has_payload = "gougoubiPayload" in data and isinstance(data["gougoubiPayload"], dict)
add_check("has_gougoubiPayload", has_payload, "gougoubiPayload present" if has_payload else "missing")

has_create_input = "createInput" in data and isinstance(data["createInput"], dict)
add_check("has_createInput", has_create_input, "createInput present" if has_create_input else "missing")

if not has_payload:
    result = {"passed": False, "score": 0.2, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

payload = data["gougoubiPayload"]

# ── CHECK: Correct candidate selected (C2, not C1/C3) ────────────────────────
market_name = payload.get("marketName", "")
# C1 is open narrative (no threshold), C3 is sentiment — both disqualified
# C2: "Will 02318 close above HK$52 on 2026-04-28?"
# C4 is also valid but recommended is C2

c1_rejected = "dominant force" not in market_name.lower() and "decade" not in market_name.lower()
c3_rejected = "sentiment" not in market_name.lower() and "positive this quarter" not in market_name.lower()
add_check("invalid_candidates_rejected", c1_rejected and c3_rejected,
          f"marketName='{market_name}' — C1/C3 must not be chosen")

# Valid candidate: must mention 02318, a price or metric, and a date
valid_market = bool(re.search(r'02318|2318', market_name, re.IGNORECASE))
add_check("market_name_references_02318", valid_market, f"marketName: '{market_name}'")

has_measurable = bool(re.search(r'HK\$\d+|profit|growth|above|below|outperform', market_name, re.IGNORECASE))
add_check("market_name_has_measurable_claim", has_measurable, f"Must have numeric/measurable threshold")

has_date_in_name = bool(re.search(r'20\d{2}-\d{2}-\d{2}', market_name))
add_check("market_name_has_date", has_date_in_name, "Market name must include a concrete date")

# ── CHECK: deadlineIsoUtc is valid UTC ISO string ─────────────────────────────
deadline = payload.get("deadlineIsoUtc", "")
is_utc_format = bool(re.match(r'20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', deadline))
add_check("deadline_is_utc_iso", is_utc_format, f"deadlineIsoUtc='{deadline}'")

# For C2 (close-price on 2026-04-28): HKT close 16:00 = 08:00 UTC
# deadlineIsoUtc should be 2026-04-28T08:00:00Z
# For C4 (earnings on 2026-04-28 with safety buffer to 2026-04-30): acceptable variants
# We check if deadline is on or after 2026-04-28 and not absurdly far
if is_utc_format:
    deadline_date = deadline[:10]
    deadline_ok = deadline_date >= "2026-04-28" and deadline_date <= "2026-05-05"
    add_check("deadline_in_reasonable_range", deadline_ok,
              f"Deadline date {deadline_date} should be 2026-04-28 to 2026-05-05")

    # For C2: check UTC hour conversion — 16:00 HKT = 08:00 UTC
    if "2026-04-28" in deadline:
        hour_str = deadline[11:13]
        try:
            hour = int(hour_str)
            # Accept 08:00 UTC (exact HK close) or small buffer (e.g., 08:30, 09:00)
            hour_correct = 0 <= hour <= 17
            add_check("deadline_utc_hour_hkt_converted",
                      hour_correct,
                      f"Hour={hour}; HK market close 16:00 HKT = 08:00 UTC; got {hour_str}:xx UTC")
        except Exception as e:
            add_check("deadline_utc_hour_hkt_converted", False, f"Could not parse hour: {e}")

# ── CHECK: rules field ────────────────────────────────────────────────────────
rules = payload.get("rules", "")
has_rules = isinstance(rules, str) and len(rules) > 50
add_check("rules_field_present_and_nonempty", has_rules, f"rules length={len(rules)}")

if has_rules:
    # Must have Primary source
    has_primary = "Primary" in rules or "primary" in rules
    add_check("rules_has_primary_source", has_primary, "rules must declare Primary resolution source")

    # Must have Fallback source
    has_fallback = "Fallback" in rules or "fallback" in rules
    add_check("rules_has_fallback_source", has_fallback, "rules must declare Fallback source")

    # Must have YES/NO resolution rule
    has_yes_no = "resolves YES" in rules and "resolves NO" in rules
    add_check("rules_has_yes_no_resolution", has_yes_no, "rules must have explicit YES and NO conditions")

    # Must mention Asia/Hong_Kong timezone
    has_timezone = "Asia/Hong_Kong" in rules
    add_check("rules_has_hk_timezone", has_timezone, "rules must specify Asia/Hong_Kong timezone")

    # Must have tie handling
    has_tie = "tie" in rules.lower() or "equal" in rules.lower() or "equality" in rules.lower()
    add_check("rules_has_tie_handling", has_tie, "rules must address tie/equality handling")

    # Tie handling: equality should resolve NO for a "close above" market
    # Look for the specific tie-handling logic
    if "above" in market_name.lower():
        tie_resolves_no = bool(re.search(r'equal.*resolves?\s+NO|tie.*resolves?\s+NO|equality.*NO', rules, re.IGNORECASE))
        add_check("rules_tie_resolves_no_for_above_market", tie_resolves_no,
                  "For 'close above' market, equality must resolve NO")

    # Must have Observation time or reporting event
    has_obs_time = "Observation time" in rules or "observation time" in rules or "reporting" in rules.lower()
    add_check("rules_has_observation_time", has_obs_time, "rules must specify observation time")

    # Must have Metric field
    has_metric = "Metric" in rules or "metric" in rules
    add_check("rules_has_metric_field", has_metric, "rules must specify metric")

# ── CHECK: tags ───────────────────────────────────────────────────────────────
tags = payload.get("tags", [])
is_list = isinstance(tags, list)
add_check("tags_is_list", is_list, f"tags type={type(tags).__name__}")

if is_list:
    tag_strings = [str(t).lower() for t in tags]
    has_hk_tag = "hong-kong-stocks" in tag_strings
    add_check("tags_has_hong_kong_stocks", has_hk_tag, f"tags={tags}")

    # One sector tag (finance, insurance, tech, internet, etc.)
    sector_tags = {"finance", "insurance", "tech", "internet", "fintech", "financial-services"}
    has_sector = any(t in sector_tags for t in tag_strings)
    add_check("tags_has_sector_tag", has_sector, f"Need one of {sector_tags}; got {tag_strings}")

    # One catalyst tag (earnings, event, results, catalyst, q1-results, etc.)
    catalyst_tags = {"earnings", "event", "results", "catalyst", "q1-results", "q1", "annual-results"}
    has_catalyst = any(t in catalyst_tags for t in tag_strings)
    add_check("tags_has_catalyst_tag", has_catalyst, f"Need one of {catalyst_tags}; got {tag_strings}")

    # One horizon tag (14d, 30d, 1m, short-term, near-term, etc.)
    horizon_tags = {"14d", "30d", "1m", "short-term", "near-term", "event"}
    has_horizon = any(t in horizon_tags for t in tag_strings)
    add_check("tags_has_horizon_tag", has_horizon, f"Need one of {horizon_tags}; got {tag_strings}")

    min_tags = len(tags) >= 4
    add_check("tags_minimum_four", min_tags, f"Got {len(tags)} tags, need at least 4")

# ── CHECK: analysis block has symbol and company ─────────────────────────────
if has_analysis:
    analysis = data["analysis"]
    has_symbol = "02318" in str(analysis.get("symbol", "")) or "02318" in str(analysis.get("companyName", ""))
    add_check("analysis_references_02318", has_symbol, f"analysis symbol/name should reference 02318")

# ── CHECK: createInput minimal fields ─────────────────────────────────────────
if has_create_input:
    ci = data["createInput"]
    has_ci_name = "marketName" in ci and ci["marketName"]
    has_ci_deadline = "deadlineIsoUtc" in ci and ci["deadlineIsoUtc"]
    add_check("createInput_has_marketName", has_ci_name, f"createInput.marketName='{ci.get('marketName','')}'")
    add_check("createInput_has_deadline", has_ci_deadline, f"createInput.deadlineIsoUtc='{ci.get('deadlineIsoUtc','')}'")

# ── CHECK: Markdown response file ────────────────────────────────────────────
md_files = list(Path(workspace).rglob("gougoubi_proposal.md"))
has_md = len(md_files) > 0
add_check("markdown_response_file_exists", has_md, f"gougoubi_proposal.md {'found' if has_md else 'not found'}")

if has_md:
    try:
        with open(md_files[0], "r", encoding="utf-8") as f:
            md_content = f.read()
        has_sections = all(kw in md_content for kw in ["标的", "预测题", "Gougoubi", "规则"])
        add_check("markdown_has_required_sections", has_sections,
                  "Markdown must include 标的结论, 选中的预测题, Gougoubi参数, 规则草案 sections")
    except Exception as e:
        add_check("markdown_readable", False, str(e))

# ── Score calculation ─────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
overall_passed = score >= 0.75

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))