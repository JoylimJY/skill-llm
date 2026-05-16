import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: str) -> Path | None:
    """Search for the context pack output file."""
    ws = Path(workspace)
    # Look for the specific requested filename
    candidates = list(ws.rglob("creator_commerce_context_pack.md")) + \
                 list(ws.rglob("creator_commerce_context_pack.txt"))
    if candidates:
        return candidates[0]
    return None

def check_content(text: str) -> list[dict]:
    checks = []
    text_lower = text.lower()

    # ── SECTION CHECKS (all 7 required sections) ──────────────────────────
    section_patterns = [
        ("business_snapshot", ["business snapshot"]),
        ("product_offer_snapshot", ["product / offer snapshot", "product/offer snapshot", "product & offer", "product and offer snapshot"]),
        ("customer_creator_profile", ["customer and creator profile", "customer & creator profile", "creator profile"]),
        ("channel_campaign_objective", ["channel and campaign", "channel & campaign", "campaign objective"]),
        ("constraints_risks", ["constraints and risks", "constraints & risks", "constraints"]),
        ("missing_information", ["missing information", "missing info", "information gaps", "open questions"]),
        ("recommended_downstream", ["recommended downstream", "next skills", "next actions", "downstream next"]),
    ]

    for section_id, keywords in section_patterns:
        found = any(kw in text_lower for kw in keywords)
        checks.append({
            "name": f"section_present_{section_id}",
            "passed": found,
            "detail": f"Section '{keywords[0]}' {'found' if found else 'NOT found'} in output."
        })

    # ── FACTS VS ASSUMPTIONS DISTINCTION ──────────────────────────────────
    facts_assumption_markers = [
        "confirmed", "assumption", "assumed", "unconfirmed", "fact:", "assumed:", "[fact]", "[assumption]",
        "[confirmed]", "[assumed]", "✓", "?", "unknown", "tbd", "not confirmed"
    ]
    has_distinction = any(marker in text_lower for marker in facts_assumption_markers)
    checks.append({
        "name": "facts_vs_assumptions_distinction",
        "passed": has_distinction,
        "detail": "Output must clearly distinguish confirmed facts from assumptions/unknowns. " +
                  ("Distinction markers found." if has_distinction else "No distinction markers detected.")
    })

    # ── KEY FACTUAL CONTENT CHECKS ──────────────────────────────────────────

    # Product name
    has_product = "velvet glow" in text_lower
    checks.append({
        "name": "product_name_present",
        "passed": has_product,
        "detail": "'Velvet Glow' product name " + ("found." if has_product else "NOT found.")
    })

    # Correct price ($42, not $38 outdated price)
    has_correct_price = "$42" in text or "42.00" in text or "42 " in text
    has_wrong_price = "$38" in text  # outdated distractor
    checks.append({
        "name": "correct_price_not_outdated",
        "passed": has_correct_price and not has_wrong_price,
        "detail": f"Correct price $42 {'found' if has_correct_price else 'NOT found'}; " +
                  f"Outdated price $38 {'INCORRECTLY present' if has_wrong_price else 'correctly absent'}."
    })

    # Offer structure: $5 off (not percentage)
    has_correct_offer = "$5 off" in text_lower or "5 off" in text_lower or "5-off" in text_lower or "five dollars off" in text_lower
    checks.append({
        "name": "correct_offer_structure",
        "passed": has_correct_offer,
        "detail": "Launch offer '$5 off' (not percentage) " + ("found." if has_correct_offer else "NOT found.")
    })

    # Primary channel TikTok Shop
    has_tiktok_shop = "tiktok shop" in text_lower
    checks.append({
        "name": "tiktok_shop_channel",
        "passed": has_tiktok_shop,
        "detail": "TikTok Shop as primary channel " + ("present." if has_tiktok_shop else "NOT mentioned.")
    })

    # Campaign objective: conversion (not awareness)
    has_conversion = "conversion" in text_lower
    checks.append({
        "name": "campaign_objective_conversion",
        "passed": has_conversion,
        "detail": "Conversion-first objective " + ("stated." if has_conversion else "NOT stated.")
    })

    # Creator types mentioned (affiliate + live seller)
    has_affiliate = "affiliate" in text_lower
    has_live_seller = "live sell" in text_lower or "live seller" in text_lower
    checks.append({
        "name": "creator_types_present",
        "passed": has_affiliate and has_live_seller,
        "detail": f"Affiliate: {'yes' if has_affiliate else 'no'}, Live seller: {'yes' if has_live_seller else 'no'}."
    })

    # Budget
    has_budget = "18,000" in text or "18k" in text_lower or "$18" in text
    checks.append({
        "name": "budget_present",
        "passed": has_budget,
        "detail": "Total budget $18,000 " + ("found." if has_budget else "NOT found.")
    })

    # Timeline / deadline
    has_timeline = "september 30" in text_lower or "sept 30" in text_lower or "sep 30" in text_lower or "end of q3" in text_lower
    checks.append({
        "name": "timeline_deadline",
        "passed": has_timeline,
        "detail": "Q3/September 30 deadline " + ("found." if has_timeline else "NOT found.")
    })

    # Legal constraints: banned claims
    has_legal_claims = "anti-aging" in text_lower or "repair" in text_lower or "dermatologist" in text_lower
    checks.append({
        "name": "legal_constraints_claims",
        "passed": has_legal_claims,
        "detail": "Legal banned claims restriction " + ("mentioned." if has_legal_claims else "NOT mentioned.")
    })

    # Missing info: TikTok Shop listing not live
    has_missing_tts = "tiktok shop" in text_lower and (
        "not live" in text_lower or "not yet live" in text_lower or "in progress" in text_lower or
        "listing" in text_lower
    )
    checks.append({
        "name": "missing_tiktok_shop_listing",
        "passed": has_missing_tts,
        "detail": "TikTok Shop listing not yet live is " + ("noted." if has_missing_tts else "NOT noted.")
    })

    # Missing info: no signed contracts
    has_missing_contracts = "contract" in text_lower and (
        "not signed" in text_lower or "unsigned" in text_lower or "none signed" in text_lower or
        "no signed" in text_lower or "not yet" in text_lower or "open" in text_lower
    )
    checks.append({
        "name": "missing_creator_contracts",
        "passed": has_missing_contracts,
        "detail": "Missing signed creator contracts " + ("flagged." if has_missing_contracts else "NOT flagged.")
    })

    # Risk: FTC disclosure open
    has_ftc = "ftc" in text_lower or "disclosure" in text_lower
    checks.append({
        "name": "risk_ftc_disclosure",
        "passed": has_ftc,
        "detail": "FTC disclosure risk " + ("mentioned." if has_ftc else "NOT mentioned.")
    })

    # Geo constraint: US only
    has_geo = "us only" in text_lower or "united states only" in text_lower or "us-only" in text_lower or \
              ("geo" in text_lower and "us" in text_lower) or "no international" in text_lower or \
              ("us" in text_lower and "canada" in text_lower)
    checks.append({
        "name": "geo_constraint_us_only",
        "passed": has_geo,
        "detail": "US-only geo constraint " + ("present." if has_geo else "NOT found.")
    })

    # Anti-bloat: check it's not just a wall of text with no structure
    has_headers = text.count("#") >= 3 or text.count("**") >= 6 or text.count("\n\n") >= 10
    checks.append({
        "name": "structured_not_bloated",
        "passed": has_headers,
        "detail": "Output appears structured (headers/bold/sections) " + ("yes." if has_headers else "NO - appears unstructured.")
    })

    # No filler strategy language (basic check)
    filler_phrases = ["synergize", "leverage the power of", "best-in-class", "move the needle",
                      "360-degree", "paradigm shift", "holistic approach to brand"]
    filler_found = [p for p in filler_phrases if p in text_lower]
    checks.append({
        "name": "no_filler_strategy_language",
        "passed": len(filler_found) == 0,
        "detail": f"Filler phrases found: {filler_found}" if filler_found else "No filler strategy language detected."
    })

    # Recommended downstream actions present
    has_recommended = "script" in text_lower or "brief" in text_lower or "contract" in text_lower or \
                      "next" in text_lower or "offer" in text_lower
    # This is covered by section check, but verify it has real actionable content
    checks.append({
        "name": "recommended_actions_actionable",
        "passed": has_recommended,
        "detail": "Recommended next actions appear actionable " + ("yes." if has_recommended else "NO.")
    })

    return checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    all_checks = []
    output_file = None

    # Find output file
    try:
        output_file = find_output_file(workspace)
        file_found = output_file is not None
        all_checks.append({
            "name": "output_file_exists",
            "passed": file_found,
            "detail": f"Output file 'creator_commerce_context_pack.md' or '.txt' " +
                      (f"found at {output_file}" if file_found else "NOT FOUND anywhere in workspace.")
        })
    except Exception as e:
        all_checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": f"Error searching for output file: {e}"
        })
        file_found = False

    if not file_found:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, indent=2))
        return

    # Read file content
    try:
        content = output_file.read_text(encoding="utf-8")
        all_checks.append({
            "name": "output_file_readable",
            "passed": True,
            "detail": f"File read successfully, {len(content)} characters."
        })
    except Exception as e:
        all_checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks
        }
        print(json.dumps(result, indent=2))
        return

    # Run content checks
    content_checks = check_content(content)
    all_checks.extend(content_checks)

    # Calculate score
    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = round(passed_count / total, 3)

    # Determine overall pass: must pass output file check + at least 16/20 content checks
    critical_checks = ["output_file_exists", "output_file_readable",
                       "section_present_business_snapshot",
                       "section_present_missing_information",
                       "section_present_recommended_downstream",
                       "facts_vs_assumptions_distinction",
                       "correct_price_not_outdated",
                       "campaign_objective_conversion"]

    critical_passed = all(
        c["passed"] for c in all_checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()