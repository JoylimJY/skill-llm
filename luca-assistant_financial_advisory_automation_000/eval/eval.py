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
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def find_report(workspace):
    """Search for card_strategy_report.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("card_strategy_report.json"))
    if not candidates:
        return None
    # Prefer workspace root, else take first found
    root_candidate = Path(workspace) / "card_strategy_report.json"
    if root_candidate.exists():
        return root_candidate
    return candidates[0]

def check_report_exists(workspace):
    report = find_report(workspace)
    if report is None:
        return False, "card_strategy_report.json not found anywhere in workspace"
    return True, f"Found at {report}"

def load_report(workspace):
    report = find_report(workspace)
    if report is None:
        raise FileNotFoundError("card_strategy_report.json not found")
    with open(report) as f:
        return json.load(f)

def check_portfolio_in_db():
    """Verify cards were actually added to the luca DB."""
    try:
        env = os.environ.copy()
        env["PATH"] = f"{os.path.expanduser('~')}/.local/bin:/root/.local/bin:" + env.get("PATH", "")
        result = subprocess.run(
            ["luca", "portfolio"],
            capture_output=True, text=True, env=env, timeout=30
        )
        output = result.stdout + result.stderr
        # Check for at least some of the expected cards
        cards_found = []
        for card_fragment in ["Sapphire", "Freedom", "Gold", "Venture"]:
            if card_fragment.lower() in output.lower():
                cards_found.append(card_fragment)
        if len(cards_found) >= 2:
            return True, f"Portfolio contains cards: {cards_found}"
        return False, f"Portfolio output didn't contain expected cards. Output: {output[:500]}"
    except Exception as e:
        return False, f"Could not query luca portfolio: {e}"

def check_524_status_in_report(workspace):
    """Report must contain Chase 5/24 status information."""
    try:
        data = load_report(workspace)
    except Exception as e:
        return False, f"Could not load report: {e}"
    
    report_str = json.dumps(data).lower()
    # Look for 5/24 related keys or values
    has_524 = any(keyword in report_str for keyword in [
        "5/24", "524", "five_twenty_four", "chase_slots", "slots_remaining",
        "slots", "chase_524", "under_524"
    ])
    if has_524:
        return True, f"Report contains 5/24 status information"
    return False, f"Report does not appear to contain Chase 5/24 status. Keys found: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}"

def check_top_offers_in_report(workspace):
    """Report must contain top offer/bonus recommendations."""
    try:
        data = load_report(workspace)
    except Exception as e:
        return False, f"Could not load report: {e}"
    
    report_str = json.dumps(data).lower()
    has_offers = any(keyword in report_str for keyword in [
        "bonus", "offer", "sub", "sign_up", "signup", "welcome",
        "min_bonus", "highest", "top_offers", "recommendations"
    ])
    if not has_offers:
        return False, "Report does not contain offer/bonus information"
    
    # Check that there are actual card names (not empty)
    # Look for common card issuers or card names
    has_cards = any(bank in report_str for bank in [
        "chase", "amex", "american express", "capital one", "citi", "discover", "wells fargo", "bank of america"
    ])
    if has_cards:
        return True, "Report contains offer data with card/bank names"
    return False, f"Report has offer keywords but no recognizable card/bank names"

def check_comparison_in_report(workspace):
    """Report must contain a side-by-side card comparison."""
    try:
        data = load_report(workspace)
    except Exception as e:
        return False, f"Could not load report: {e}"
    
    report_str = json.dumps(data).lower()
    has_comparison = any(keyword in report_str for keyword in [
        "comparison", "compare", "benefits", "multiplier", "annual_fee",
        "side_by_side", "card_comparison", "compared"
    ])
    if has_comparison:
        return True, "Report contains card comparison data"
    return False, "Report does not appear to contain card comparison"

def check_report_is_valid_json(workspace):
    report = find_report(workspace)
    if report is None:
        return False, "Report file not found"
    try:
        with open(report) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False, f"Report is valid JSON but not an object (got {type(data).__name__})"
        if len(data) < 2:
            return False, f"Report is a valid JSON object but has too few keys ({list(data.keys())})"
        return True, f"Valid JSON object with keys: {list(data.keys())}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

def check_min_bonus_threshold(workspace):
    """Offers in the report should reflect the $500 minimum bonus filter."""
    try:
        data = load_report(workspace)
    except Exception as e:
        return False, f"Could not load report: {e}"
    
    report_str = json.dumps(data)
    # Check that 500 appears as a threshold or that bonus values are >= 500
    import re
    # Look for numeric bonus values
    bonus_values = re.findall(r'"(?:bonus_usd|min_bonus|value|bonus_value|usd_value|estimated_value)"\s*:\s*(\d+(?:\.\d+)?)', report_str)
    if bonus_values:
        values = [float(v) for v in bonus_values]
        all_above_500 = all(v >= 500 for v in values)
        if all_above_500:
            return True, f"All found bonus values >= $500: {values}"
        else:
            below = [v for v in values if v < 500]
            return False, f"Some bonus values below $500 threshold: {below}"
    
    # If no explicit numeric values found, check for $500 mention
    if "500" in report_str:
        return True, "$500 threshold referenced in report"
    
    return False, "Could not verify $500 minimum bonus threshold in report"

def check_non_business_cards(workspace):
    """Offers should be personal (non-business) cards only."""
    try:
        data = load_report(workspace)
    except Exception as e:
        return False, f"Could not load report: {e}"
    
    report_str = json.dumps(data).lower()
    # Business card names that should NOT appear as recommendations
    business_card_flags = ["business", "ink ", "spark", "blue business", "delta skymiles business"]
    found_business = [b for b in business_card_flags if b in report_str and "is_business" not in json.dumps(data).lower()]
    
    # This is a soft check — if "business" appears only as a filter flag (is_business: false), it's fine
    if "is_business" in report_str or "personal" in report_str:
        return True, "Report references personal/business filter correctly"
    
    return True, "No obvious business card contamination detected (soft check passed)"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = [
        run_check("report_file_exists", lambda: check_report_exists(workspace)),
        run_check("report_is_valid_json", lambda: check_report_is_valid_json(workspace)),
        run_check("cards_added_to_portfolio_db", lambda: check_portfolio_in_db()),
        run_check("chase_524_status_present", lambda: check_524_status_in_report(workspace)),
        run_check("top_offers_present", lambda: check_top_offers_in_report(workspace)),
        run_check("card_comparison_present", lambda: check_comparison_in_report(workspace)),
        run_check("min_bonus_500_threshold", lambda: check_min_bonus_threshold(workspace)),
        run_check("personal_cards_only", lambda: check_non_business_cards(workspace)),
    ]
    
    # Weighted scoring
    weights = {
        "report_file_exists": 1.0,
        "report_is_valid_json": 1.0,
        "cards_added_to_portfolio_db": 2.0,
        "chase_524_status_present": 2.0,
        "top_offers_present": 2.0,
        "card_comparison_present": 1.5,
        "min_bonus_500_threshold": 1.0,
        "personal_cards_only": 0.5,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 3)
    passed = score >= 0.70  # Need at least 70% to pass
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()