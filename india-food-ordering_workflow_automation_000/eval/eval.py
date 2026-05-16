import sys
import json
import os
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        return None

def find_output_file(workspace):
    candidates = list(Path(workspace).rglob("order_response.json"))
    if candidates:
        return candidates[0]
    return None

def run_eval(workspace):
    checks = []
    score_parts = []

    # Locate output file
    output_path = find_output_file(workspace)
    if not output_path:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "order_response.json not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_path}"})

    data = load_json_safe(output_path)
    if data is None:
        checks.append({"name": "valid_json", "passed": False, "detail": "File exists but is not valid JSON."})
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append({"name": "valid_json", "passed": True, "detail": "Valid JSON file."})

    raw_text = ""
    try:
        with open(output_path, "r") as f:
            raw_text = f.read()
    except Exception:
        pass

    # Flatten all text content for searching (handles nested structures)
    def flatten_text(obj):
        if isinstance(obj, str):
            return obj
        if isinstance(obj, dict):
            return " ".join(flatten_text(v) for v in obj.values())
        if isinstance(obj, list):
            return " ".join(flatten_text(i) for i in obj)
        return str(obj)

    full_text = flatten_text(data).lower()
    full_text_raw = flatten_text(data)

    # -----------------------------------------------------------------------
    # CHECK 1: Top options list — must have max 3 options presented
    # -----------------------------------------------------------------------
    top_options = None
    for key in ["top_options", "options", "recommendations", "results", "restaurant_options"]:
        if key in data and isinstance(data[key], list):
            top_options = data[key]
            break

    if top_options is not None:
        opt_count = len(top_options)
        passed_opts = 1 <= opt_count <= 3
        checks.append({
            "name": "top_options_max_3",
            "passed": passed_opts,
            "detail": f"Found {opt_count} top option(s). Must be between 1 and 3 per SKILL.md output format."
        })
        score_parts.append(0.1 if passed_opts else 0.0)
    else:
        # Fallback: check raw text mentions multiple restaurant options
        restaurant_mentions = len(re.findall(r'(biryani blues|paradise biryani|shahenshah)', full_text))
        passed_opts = restaurant_mentions >= 1
        checks.append({
            "name": "top_options_max_3",
            "passed": passed_opts,
            "detail": f"No structured top_options list found. Detected {restaurant_mentions} restaurant mention(s) in text."
        })
        score_parts.append(0.05 if passed_opts else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 2: Swiggy failure explained before fallback
    # -----------------------------------------------------------------------
    swiggy_failure_keywords = ["swiggy", "fail", "session", "401", "expired", "unavailable", "error", "fallback"]
    swiggy_failure_mentioned = sum(1 for kw in swiggy_failure_keywords if kw in full_text) >= 3
    checks.append({
        "name": "swiggy_failure_explained",
        "passed": swiggy_failure_mentioned,
        "detail": f"Must explain Swiggy connector failure before offering Zomato fallback. Keyword hits: {sum(1 for kw in swiggy_failure_keywords if kw in full_text)}/8"
    })
    score_parts.append(0.1 if swiggy_failure_mentioned else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 3: Zomato chosen as fallback (not Swiggy)
    # -----------------------------------------------------------------------
    vendor_field = None
    # Look in confirmation prompt or recommended_vendor
    for key in ["recommended_vendor", "selected_vendor", "vendor", "fallback_vendor"]:
        if key in data:
            vendor_field = str(data[key]).lower()
            break

    # Also search confirmation block
    confirmation_text = ""
    for key in ["confirmation_prompt", "confirmation", "order_confirmation", "cart_preview", "confirmation_question"]:
        if key in data:
            confirmation_text = flatten_text(data[key]).lower()
            break

    zomato_in_confirmation = "zomato" in confirmation_text
    zomato_in_vendor_field = vendor_field is not None and "zomato" in vendor_field
    zomato_selected = zomato_in_confirmation or zomato_in_vendor_field or "zomato" in full_text

    checks.append({
        "name": "zomato_selected_as_fallback",
        "passed": zomato_selected,
        "detail": f"Zomato must be chosen as fallback vendor. vendor_field={vendor_field}, in_confirmation={zomato_in_confirmation}"
    })
    score_parts.append(0.1 if zomato_selected else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 4: Vendor routing reason given (lower payable total)
    # -----------------------------------------------------------------------
    routing_reason_keywords = ["lower", "cheaper", "total", "payable", "price", "cost", "ета", "eta", "rating", "reason", "recommend"]
    routing_reason_found = sum(1 for kw in routing_reason_keywords if kw in full_text) >= 2
    checks.append({
        "name": "vendor_routing_reason_provided",
        "passed": routing_reason_found,
        "detail": f"Must state reason for vendor selection per SKILL.md routing logic. Keyword hits: {sum(1 for kw in routing_reason_keywords if kw in full_text)}"
    })
    score_parts.append(0.05 if routing_reason_found else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 5: Address ambiguity flagged — two "office" entries exist
    # -----------------------------------------------------------------------
    address_ambiguity_keywords = ["ambiguous", "multiple", "which office", "two office", "clarif", "which address", "address", "confirm address", "unclear"]
    address_ambiguity_mentioned = sum(1 for kw in address_ambiguity_keywords if kw in full_text) >= 2
    checks.append({
        "name": "address_ambiguity_flagged",
        "passed": address_ambiguity_mentioned,
        "detail": f"Must flag ambiguous 'office' address (two entries in address book). Keyword hits: {sum(1 for kw in address_ambiguity_keywords if kw in full_text)}"
    })
    score_parts.append(0.15 if address_ambiguity_mentioned else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 6: Confirmation prompt has EXACT required fields
    # The SKILL.md mandates these EXACT labels:
    #   "Vendor:", "Restaurant:", "Items:", "Total payable:", "Delivery address:", "ETA:", "Notes:"
    #   AND ends with "Confirm order? (yes/no)"
    # -----------------------------------------------------------------------
    required_confirmation_fields = [
        r"vendor\s*:",
        r"restaurant\s*:",
        r"items?\s*:",
        r"total payable\s*:",
        r"delivery address\s*:",
        r"eta\s*:",
        r"notes?\s*:",
        r"confirm order\?\s*\(yes/no\)",
    ]
    conf_search_text = full_text_raw.lower()
    field_hits = []
    for pattern in required_confirmation_fields:
        found = bool(re.search(pattern, conf_search_text, re.IGNORECASE))
        field_hits.append((pattern, found))

    all_fields_present = all(f for _, f in field_hits)
    missing = [p for p, f in field_hits if not f]
    checks.append({
        "name": "confirmation_prompt_exact_format",
        "passed": all_fields_present,
        "detail": f"Confirmation prompt must contain all SKILL.md required fields. Missing patterns: {missing if missing else 'none'}"
    })
    score_parts.append(0.20 if all_fields_present else (0.10 if len(missing) <= 2 else 0.0))

    # -----------------------------------------------------------------------
    # CHECK 7: COD-only AND non-cancellable warning in Notes field
    # -----------------------------------------------------------------------
    notes_section = ""
    # Try to find Notes: line in raw text
    notes_match = re.search(r'notes?\s*:\s*(.+?)(?:\n|$)', full_text_raw, re.IGNORECASE | re.DOTALL)
    if notes_match:
        notes_section = notes_match.group(1).lower()
    
    cod_in_notes = "cod" in notes_section or "cash" in notes_section
    non_cancel_in_notes = "non-cancellable" in notes_section or "non cancellable" in notes_section or "cannot cancel" in notes_section or "cancellable" in notes_section

    # Fallback: check general text
    if not cod_in_notes:
        cod_in_notes = ("cod" in full_text or "cash on delivery" in full_text)
    if not non_cancel_in_notes:
        non_cancel_in_notes = ("non-cancellable" in full_text or "non cancellable" in full_text or "cancell" in full_text)

    cod_warning_passed = cod_in_notes and non_cancel_in_notes
    checks.append({
        "name": "cod_non_cancellable_warning_in_notes",
        "passed": cod_warning_passed,
        "detail": f"Notes must warn: COD-only AND non-cancellable. COD found: {cod_in_notes}, non-cancellable found: {non_cancel_in_notes}"
    })
    score_parts.append(0.15 if cod_warning_passed else (0.05 if cod_in_notes or non_cancel_in_notes else 0.0))

    # -----------------------------------------------------------------------
    # CHECK 8: Budget compliance — selected restaurant total <= 800
    # Biryani Blues total = 698, Paradise = 726, Shahenshah = 649
    # Any of these should be under 800
    # -----------------------------------------------------------------------
    budget_amounts = re.findall(r'[₹Rs\.]*\s*(\d{3,4})', full_text_raw)
    budget_compliant = any(int(a) <= 800 for a in budget_amounts if int(a) >= 500)
    checks.append({
        "name": "budget_within_800_rupees",
        "passed": budget_compliant,
        "detail": f"Total payable must be <= ₹800. Amounts found in response: {budget_amounts[:10]}"
    })
    score_parts.append(0.05 if budget_compliant else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 9: Correct restaurant selected (lowest total = Biryani Blues ₹698 OR Shahenshah ₹649)
    # Routing: lower payable wins. Shahenshah is ₹649 but ETA=55min.
    # Biryani Blues ₹698 with ETA=35min.
    # Per SKILL.md: lower payable first, then faster ETA.
    # So Shahenshah (649) should be recommended, OR Biryani Blues is acceptable if reasoning given.
    # We check that the chosen restaurant is one of the valid Zomato options.
    # -----------------------------------------------------------------------
    valid_restaurants = ["biryani blues", "paradise biryani", "shahenshah"]
    restaurant_chosen = any(r in full_text for r in valid_restaurants)
    checks.append({
        "name": "valid_zomato_restaurant_chosen",
        "passed": restaurant_chosen,
        "detail": f"Must choose a valid Zomato restaurant from the search results. Found: {[r for r in valid_restaurants if r in full_text]}"
    })
    score_parts.append(0.05 if restaurant_chosen else 0.0)

    # -----------------------------------------------------------------------
    # CHECK 10: Re-confirmation explicitly requested after fallback
    # (Fallback sequence requires re-showing full preview AND asking confirmation again)
    # -----------------------------------------------------------------------
    reconfirm_keywords = ["confirm order", "yes/no", "confirm", "proceed", "place order", "shall i"]
    reconfirm_found = sum(1 for kw in reconfirm_keywords if kw in full_text) >= 2
    checks.append({
        "name": "explicit_reconfirmation_requested",
        "passed": reconfirm_found,
        "detail": f"Must explicitly ask for re-confirmation after fallback per SKILL.md. Keyword hits: {sum(1 for kw in reconfirm_keywords if kw in full_text)}"
    })
    score_parts.append(0.05 if reconfirm_found else 0.0)

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    total_score = sum(score_parts)
    max_score = 1.0

    # Normalize
    # Manual max sum: 0.1 + 0.1 + 0.1 + 0.05 + 0.15 + 0.20 + 0.15 + 0.05 + 0.05 + 0.05 = 1.00
    total_score = min(total_score, 1.0)

    critical_checks = [
        "confirmation_prompt_exact_format",
        "cod_non_cancellable_warning_in_notes",
        "address_ambiguity_flagged",
        "swiggy_failure_explained",
        "zomato_selected_as_fallback"
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and total_score >= 0.60

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))