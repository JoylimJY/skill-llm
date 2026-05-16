import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    """Search for the activation plan file."""
    candidates = list(Path(workspace).rglob("new_shopper_activation_plan.md"))
    if not candidates:
        # Try common alternate names as fallback for partial credit detection
        candidates = list(Path(workspace).rglob("*activation*plan*")) + \
                     list(Path(workspace).rglob("*cold*start*")) + \
                     list(Path(workspace).rglob("*first*order*offer*"))
    return candidates[0] if candidates else None

def check_section_a(content):
    """Check: Path → Segment table exists with correct columns and all 5 sessions mapped."""
    checks = []
    
    # Must have section A header
    has_section_a = bool(re.search(r'(?i)(section\s*a|path.*segment|a[\)\.:].*path)', content))
    checks.append(("section_a_present", has_section_a, "Section A (Path→Segment table) header found"))
    
    # Must have the required column headers
    has_observed_path = bool(re.search(r'(?i)observed.{0,10}path', content))
    has_preference_label = bool(re.search(r'(?i)preference.{0,10}label', content))
    has_rationale = bool(re.search(r'(?i)rationale', content))
    checks.append(("section_a_columns", has_observed_path and has_preference_label and has_rationale,
                   f"Section A columns: observed_path={has_observed_path}, preference_label={has_preference_label}, rationale={has_rationale}"))
    
    # Must map all 5 sessions (check for segment labels from playbook)
    segments_expected = ["Category Intent", "Price Sensitive", "Shipping Sensitive", "Single SKU Deep Dive", "Bouncer"]
    found_segments = []
    for seg in segments_expected:
        if re.search(re.escape(seg), content, re.IGNORECASE):
            found_segments.append(seg)
    checks.append(("section_a_all_segments", len(found_segments) >= 4,
                   f"Found {len(found_segments)}/5 expected segment labels: {found_segments}"))
    
    return checks

def check_section_b(content):
    """Check: Segment → First-order offer table with correct offers and guardrails from playbook."""
    checks = []
    
    has_section_b = bool(re.search(r'(?i)(section\s*b|segment.*offer|b[\)\.:].*segment)', content))
    checks.append(("section_b_present", has_section_b, "Section B (Segment→Offer table) header found"))
    
    # Check offer types match playbook (not generic)
    # Category Intent → 12% off, min $85
    has_cat_intent_discount = bool(re.search(r'12\s*%', content))
    checks.append(("category_intent_12pct", has_cat_intent_discount,
                   "Category Intent offer is 12% (playbook-specific, not generic)"))
    
    # Check min order $85 for Category Intent
    has_min_85 = bool(re.search(r'\$\s*85|85\s*dollar', content, re.IGNORECASE))
    checks.append(("category_intent_min_85", has_min_85,
                   "Category Intent min order $85 from playbook"))
    
    # Price Sensitive → $15 fixed off, min $60
    has_price_sensitive_15 = bool(re.search(r'\$\s*15\s*off|\$15', content))
    checks.append(("price_sensitive_15_off", has_price_sensitive_15,
                   "Price Sensitive offer is $15 off (playbook-specific fixed amount)"))
    
    # Shipping Sensitive → Free shipping, min $50
    has_free_ship = bool(re.search(r'free\s+ship', content, re.IGNORECASE))
    checks.append(("shipping_sensitive_free_ship", has_free_ship,
                   "Shipping Sensitive offer is free shipping"))
    
    # Single SKU Deep Dive → Gift with order, min $120
    has_gift = bool(re.search(r'gift\s*(with|w/)', content, re.IGNORECASE))
    has_min_120 = bool(re.search(r'\$\s*120', content))
    checks.append(("single_sku_gift_offer", has_gift and has_min_120,
                   f"Single SKU Deep Dive: gift offer={has_gift}, min $120={has_min_120}"))
    
    # Exclusion: full-price tents >$400 excluded from Category Intent
    has_tent_exclusion = bool(re.search(r'tent.{0,40}\$\s*400|400.{0,40}tent|exclud.{0,40}tent', content, re.IGNORECASE))
    checks.append(("category_intent_tent_exclusion", has_tent_exclusion,
                   "Category Intent excludes full-price tents >$400"))
    
    # Stack rule: cannot stack with WELCOME15/EARLYBIRD
    has_stack_rule = bool(re.search(r'WELCOME15|EARLYBIRD|stack|cannot\s+stack', content, re.IGNORECASE))
    checks.append(("stack_rule_mentioned", has_stack_rule,
                   "Stack rule (cannot combine with WELCOME15/EARLYBIRD) noted"))
    
    return checks

def check_section_c(content):
    """Check: Trigger spec with exit intent as PRIMARY and two backups."""
    checks = []
    
    has_section_c = bool(re.search(r'(?i)(section\s*c|trigger\s*spec|c[\)\.:].*trigger)', content))
    checks.append(("section_c_present", has_section_c, "Section C (Trigger Spec) header found"))
    
    # Exit intent must be present and labeled primary/first
    has_exit_intent = bool(re.search(r'exit\s*intent', content, re.IGNORECASE))
    checks.append(("exit_intent_present", has_exit_intent, "Exit intent trigger present"))
    
    # Exit intent primary (must appear before backups)
    exit_pos = content.lower().find("exit intent")
    backup1_pos = content.lower().find("backup 1")
    backup2_pos = content.lower().find("backup 2")
    exit_is_primary = (exit_pos != -1) and (backup1_pos == -1 or exit_pos < backup1_pos)
    checks.append(("exit_intent_is_primary", exit_is_primary,
                   f"Exit intent is primary (pos={exit_pos} before backup1 pos={backup1_pos})"))
    
    # Backup 1: 25 seconds on PDP
    has_25s_backup = bool(re.search(r'25\s*(s|sec|second)', content, re.IGNORECASE))
    checks.append(("backup1_25s_pdp", has_25s_backup,
                   "Backup 1 is 25s dwell on PDP (playbook-specific)"))
    
    # Backup 2: second category/collection view
    has_second_category = bool(re.search(r'second\s*(category|collection)', content, re.IGNORECASE))
    checks.append(("backup2_second_category", has_second_category,
                   "Backup 2 is second category/collection view"))
    
    # Trigger table columns
    has_trigger_col = bool(re.search(r'(?i)\|\s*trigger\s*\|', content))
    has_when_col = bool(re.search(r'(?i)\|\s*when\s*\|', content))
    has_copy_role_col = bool(re.search(r'(?i)\|\s*copy\s*role\s*\|', content))
    checks.append(("trigger_table_columns", has_trigger_col and has_when_col and has_copy_role_col,
                   f"Trigger table has Trigger/When/Copy Role columns: {has_trigger_col}/{has_when_col}/{has_copy_role_col}"))
    
    return checks

def check_modal_copy(content):
    """Check: At least one modal headline + subline + CTA per primary segment."""
    checks = []
    
    # Must have modal copy section
    has_modal = bool(re.search(r'(?i)(modal|popup|headline|subline|CTA)', content))
    checks.append(("modal_copy_present", has_modal, "Modal copy section present"))
    
    # Headline
    has_headline = bool(re.search(r'(?i)headline', content))
    checks.append(("modal_headline", has_headline, "Modal headline present"))
    
    # Subline
    has_subline = bool(re.search(r'(?i)subline|sub.?line|sub.?headline', content))
    checks.append(("modal_subline", has_subline, "Modal subline present"))
    
    # CTA
    has_cta = bool(re.search(r'(?i)\bCTA\b|call.to.action', content))
    checks.append(("modal_cta", has_cta, "Modal CTA present"))
    
    return checks

def check_not_loyalty_winback(content):
    """Negative check: agent must not apply loyalty win-back rules."""
    checks = []
    # Should not reference lapsed customers or 90-day lapse (from distractor file)
    is_loyalty_only = bool(re.search(r'90.day\s*lapse|lapsed\s*buyer|loyalty\s*win.back', content, re.IGNORECASE))
    checks.append(("no_loyalty_winback_confusion", not is_loyalty_only,
                   "Output does not confuse cold-start with loyalty win-back"))
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    all_checks = []
    
    # Find the output file
    output_file = None
    try:
        output_file = find_output_file(workspace)
    except Exception as e:
        all_checks.append({"name": "output_file_found", "passed": False, "detail": f"Error searching: {e}"})
    
    if not output_file:
        all_checks.append({"name": "output_file_found", "passed": False,
                            "detail": "new_shopper_activation_plan.md not found anywhere in workspace"})
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result))
        return
    
    all_checks.append({"name": "output_file_found", "passed": True, "detail": f"Found at {output_file}"})
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        all_checks.append({"name": "output_file_readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": all_checks}
        print(json.dumps(result))
        return
    
    all_checks.append({"name": "output_file_readable", "passed": True, "detail": f"File length: {len(content)} chars"})
    
    # Run all check groups
    check_groups = [
        check_section_a(content),
        check_section_b(content),
        check_section_c(content),
        check_modal_copy(content),
        check_not_loyalty_winback(content),
    ]
    
    for group in check_groups:
        for name, passed, detail in group:
            all_checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Score calculation
    passed_count = sum(1 for c in all_checks if c["passed"])
    total = len(all_checks)
    score = round(passed_count / total, 3)
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "output_file_found",
        "section_a_present",
        "section_b_present", 
        "section_c_present",
        "exit_intent_is_primary",
        "category_intent_12pct",
        "backup1_25s_pdp",
        "single_sku_gift_offer",
    ]
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in all_checks)
        for cc in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.72
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()