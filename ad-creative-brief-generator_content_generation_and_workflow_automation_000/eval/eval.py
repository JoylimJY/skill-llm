import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # --- Find the output brief file ---
    brief_files = list(workspace_path.rglob("clarity_plus_creative_brief.md"))
    
    file_found = len(brief_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(brief_files)} file(s) named 'clarity_plus_creative_brief.md'" if file_found else "File 'clarity_plus_creative_brief.md' not found anywhere in workspace."
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    brief_path = brief_files[0]
    try:
        content = brief_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # --- CHECK 1: Section 1 - Campaign Objective Summary ---
    has_objective_section = bool(re.search(
        r'(campaign\s+objective|objective\s+summary|campaign\s+goal)',
        content_lower
    ))
    # Must mention first purchase / conversion, Meta, and Sept/August deadline
    has_first_purchase = bool(re.search(r'(first.{0,20}purchase|first.{0,20}order|purchase\s+conversion|first.time\s+buyer)', content_lower))
    has_meta_channel = bool(re.search(r'(meta|reels|instagram|facebook)', content_lower))
    
    checks.append({
        "name": "section1_campaign_objective_present",
        "passed": has_objective_section,
        "detail": "Campaign Objective Summary section found." if has_objective_section else "Missing Campaign Objective Summary section."
    })
    checks.append({
        "name": "section1_first_purchase_goal",
        "passed": has_first_purchase,
        "detail": "First purchase / conversion goal correctly extracted." if has_first_purchase else "Missing first purchase/conversion goal from campaign notes."
    })
    checks.append({
        "name": "section1_channel_meta",
        "passed": has_meta_channel,
        "detail": "Meta/Reels channel correctly identified." if has_meta_channel else "Missing Meta/Reels channel specification."
    })

    # --- CHECK 2: Section 2 - Core Angle & Message Hierarchy ---
    has_angle_section = bool(re.search(
        r'(core\s+angle|message\s+hierarchy|angle\s+&|angle\s+and)',
        content_lower
    ))
    # Must include specific angle (not just "better focus") - check for specificity signals
    # Non-stimulant angle is a key differentiator from inputs
    has_non_stimulant = bool(re.search(r'(non.stimulant|not.{0,10}caffeine|without\s+caffeine|stimulant.free|caffeine.free)', content_lower))
    # Must mention the target audience specificity (28-42 professionals, optimizer archetype)
    has_audience_specificity = bool(re.search(r'(28.{0,5}42|professional|deep\s+work|afternoon|optimizer|2\s*pm|2pm)', content_lower))
    # Message hierarchy must have multiple ordered points (not just one line)
    has_hierarchy = bool(re.search(r'(first|second|third|primary|1\.|2\.|3\.|\bprimary\b.*\bsecondary\b)', content_lower))
    
    checks.append({
        "name": "section2_angle_hierarchy_present",
        "passed": has_angle_section,
        "detail": "Core Angle & Message Hierarchy section found." if has_angle_section else "Missing Core Angle & Message Hierarchy section."
    })
    checks.append({
        "name": "section2_non_stimulant_angle",
        "passed": has_non_stimulant,
        "detail": "Non-stimulant differentiator correctly surfaced as angle." if has_non_stimulant else "Missing non-stimulant differentiator - a key commercial angle from the input data."
    })
    checks.append({
        "name": "section2_audience_specificity",
        "passed": has_audience_specificity,
        "detail": "Target audience specificity (28-42, professionals, deep work, afternoon slump) present." if has_audience_specificity else "Audience too vague - missing specific signals from input notes."
    })
    checks.append({
        "name": "section2_message_hierarchy_structure",
        "passed": has_hierarchy,
        "detail": "Message hierarchy shows ordered priority." if has_hierarchy else "No message hierarchy ordering found - brief reads as a flat list, not a hierarchy."
    })

    # --- CHECK 3: Section 3 - Hook / Scene / Proof Guidance ---
    has_hook_section = bool(re.search(
        r'(hook\s*/|hook\s+/|hook\s+and|hook.*scene|scene.*proof|proof\s+guidance|opening\s+hook)',
        content_lower
    ))
    # Must include NSF certification as proof point (explicitly in inputs, creators asked for it)
    has_nsf = bool(re.search(r'(nsf|third.party\s+test|third.party\s+certif|independently\s+tested)', content_lower))
    # Must include specific ingredients as proof (Lion's Mane, Bacopa, or L-Theanine)
    has_ingredients = bool(re.search(r"(lion.s\s+mane|bacopa|l.theanine|lionsm|ksh.66|bacosides)", content_lower))
    # Must have hook direction (not just say "write a hook")
    has_hook_content = bool(re.search(r'(hook\s*[:|\-]|opening\s*[:|\-]|first\s+[35]\s+sec|5\s+second|3\s+second|pattern\s+interrupt|relatable\s+moment)', content_lower))
    
    checks.append({
        "name": "section3_hook_proof_present",
        "passed": has_hook_section,
        "detail": "Hook / Scene / Proof section found." if has_hook_section else "Missing Hook / Scene / Proof Guidance section."
    })
    checks.append({
        "name": "section3_nsf_proof_point",
        "passed": has_nsf,
        "detail": "NSF certification correctly included as proof point." if has_nsf else "NSF certification missing from proof points - stakeholder feedback explicitly requested this."
    })
    checks.append({
        "name": "section3_specific_ingredients",
        "passed": has_ingredients,
        "detail": "Specific ingredient(s) included as proof direction." if has_ingredients else "Missing specific ingredients - brief is too generic without product-specific proof."
    })
    checks.append({
        "name": "section3_hook_direction",
        "passed": has_hook_content,
        "detail": "Concrete hook direction present." if has_hook_content else "Hook guidance is too vague - missing specific direction."
    })

    # --- CHECK 4: Section 4 - CTA & Offer Note ---
    has_cta_section = bool(re.search(
        r'(cta\s+&|cta\s+and|call\s+to\s+action|offer\s+note)',
        content_lower
    ))
    # Must include the specific promo code CLARITY20
    has_promo_code = bool(re.search(r'clarity20', content_lower))
    # Must mention the 20% discount
    has_discount = bool(re.search(r'(20\s*%\s*off|20\s*percent\s*off|twenty\s*percent)', content_lower))
    # Must mention expiry or urgency (Sept 30 or expires)
    has_urgency = bool(re.search(r'(sept(ember)?\s*(30|30th)|expires?\s*(sept|sep)|september\s+30)', content_lower))
    
    checks.append({
        "name": "section4_cta_offer_present",
        "passed": has_cta_section,
        "detail": "CTA & Offer Note section found." if has_cta_section else "Missing CTA & Offer Note section."
    })
    checks.append({
        "name": "section4_promo_code",
        "passed": has_promo_code,
        "detail": "Promo code CLARITY20 included." if has_promo_code else "Missing promo code CLARITY20 - critical offer detail omitted."
    })
    checks.append({
        "name": "section4_discount_amount",
        "passed": has_discount,
        "detail": "20% discount clearly stated." if has_discount else "Missing 20% discount detail."
    })
    checks.append({
        "name": "section4_expiry_urgency",
        "passed": has_urgency,
        "detail": "Offer expiry / Sept 30 urgency noted." if has_urgency else "Missing offer expiry date (Sept 30) - urgency signal omitted."
    })

    # --- CHECK 5: Section 5 - Guardrails & Risk Notes ---
    has_guardrails_section = bool(re.search(
        r'(guardrail|risk\s+note|compliance|forbidden|do\s+not\s+use|banned\s+claim)',
        content_lower
    ))
    # Must explicitly forbid FDA approved language
    has_fda_forbidden = bool(re.search(r'(fda.approved|fda.cleared|not.{0,20}fda)', content_lower))
    # Must include the FDA disclaimer asterisk language (or reference to it)
    has_fda_disclaimer = bool(re.search(r'(not\s+intended\s+to\s+diagnose|not\s+evaluated\s+by\s+the\s+fda|\*these\s+statements|fda\s+disclaimer|supplement\s+disclaimer)', content_lower))
    # Must mention individual results may vary (testimonial rule)
    has_results_vary = bool(re.search(r'(individual\s+results|results\s+(may|not)\s+(vary|typical))', content_lower))
    # Must explicitly call out the "clinically proven" ban OR quantified improvement ban
    has_clinically_proven_ban = bool(re.search(r'(clinically\s+proven|guaranteed|50%|quantified\s+improvement|specific.*percentage|before.{0,10}after)', content_lower))
    # The guardrails section should be substantive (more than 2 lines)
    guardrail_match = re.search(
        r'(guardrail|risk\s+note|compliance|forbidden)(.*?)(?=##|\Z)',
        content_lower,
        re.DOTALL
    )
    guardrail_substantive = False
    if guardrail_match:
        guardrail_text = guardrail_match.group(2)
        guardrail_lines = [l.strip() for l in guardrail_text.split('\n') if l.strip()]
        guardrail_substantive = len(guardrail_lines) >= 4

    checks.append({
        "name": "section5_guardrails_present",
        "passed": has_guardrails_section,
        "detail": "Guardrails & Risk Notes section found." if has_guardrails_section else "Missing Guardrails & Risk Notes section - critical omission for sensitive health supplement."
    })
    checks.append({
        "name": "section5_fda_approved_forbidden",
        "passed": has_fda_forbidden,
        "detail": "FDA approved/cleared language explicitly forbidden in guardrails." if has_fda_forbidden else "Missing explicit ban on 'FDA approved' language."
    })
    checks.append({
        "name": "section5_fda_footnote_required",
        "passed": has_fda_disclaimer,
        "detail": "Required FDA disclaimer footnote language included." if has_fda_disclaimer else "Missing required FDA supplement disclaimer language (*These statements have not been evaluated...)."
    })
    checks.append({
        "name": "section5_results_vary_required",
        "passed": has_results_vary,
        "detail": "'Individual results may vary' testimonial requirement present." if has_results_vary else "Missing 'Individual results may vary' requirement for testimonials."
    })
    checks.append({
        "name": "section5_banned_quantified_claims",
        "passed": has_clinically_proven_ban,
        "detail": "Ban on 'clinically proven' / guaranteed / quantified improvement claims included." if has_clinically_proven_ban else "Missing ban on clinically proven or quantified outcome claims."
    })
    checks.append({
        "name": "section5_guardrails_substantive",
        "passed": guardrail_substantive,
        "detail": "Guardrails section is substantive (4+ distinct items)." if guardrail_substantive else "Guardrails section too thin - not actionable for creator teams."
    })

    # --- CHECK 6: Overall Brief Quality ---
    # Must not be excessively short (< 400 words is likely too thin)
    word_count = len(content.split())
    is_substantive = word_count >= 400
    checks.append({
        "name": "overall_minimum_substance",
        "passed": is_substantive,
        "detail": f"Brief has {word_count} words (minimum 400 required for executable direction)." if is_substantive else f"Brief too short at {word_count} words - not enough substance for a creative team to execute from."
    })

    # Must have all 5 sections present (re-check via section headers)
    section_headers = re.findall(r'##\s+\d\.', content)
    has_five_sections = len(section_headers) >= 5
    checks.append({
        "name": "overall_five_sections_present",
        "passed": has_five_sections,
        "detail": f"Found {len(section_headers)} numbered sections (## 1., ## 2., etc.). Need 5." if has_five_sections else f"Only found {len(section_headers)} numbered section headers. All 5 required sections must be present."
    })

    # Must NOT contain the archived Q1 2023 SleepWave content (not mixing up products)
    has_wrong_product = bool(re.search(r'(sleepwave|sleep\s+wave\s+gummies)', content_lower))
    checks.append({
        "name": "overall_correct_product",
        "passed": not has_wrong_product,
        "detail": "Brief correctly targets Clarity Plus, not SleepWave." if not has_wrong_product else "Brief contains SleepWave content - agent incorrectly mixed archived product data."
    })

    # --- Scoring ---
    # Weight distribution: sections are scored, critical compliance checks get extra weight
    critical_checks = [
        "output_file_exists",
        "section1_campaign_objective_present",
        "section1_first_purchase_goal",
        "section2_angle_hierarchy_present",
        "section2_non_stimulant_angle",
        "section3_hook_proof_present",
        "section3_nsf_proof_point",
        "section4_cta_offer_present",
        "section4_promo_code",
        "section5_guardrails_present",
        "section5_fda_approved_forbidden",
        "section5_fda_footnote_required",
        "section5_results_vary_required",
        "overall_five_sections_present",
        "overall_correct_product",
    ]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    critical_passed = sum(1 for c in checks if c["passed"] and c["name"] in critical_checks)
    critical_total = len(critical_checks)

    # Score: 60% from critical checks, 40% from all checks
    score = 0.6 * (critical_passed / critical_total) + 0.4 * (passed_count / total)
    score = round(min(score, 1.0), 4)

    passed_overall = (
        score >= 0.75 and
        # Must pass all 5 section presence checks
        all(c["passed"] for c in checks if c["name"] in [
            "section1_campaign_objective_present",
            "section2_angle_hierarchy_present",
            "section3_hook_proof_present",
            "section4_cta_offer_present",
            "section5_guardrails_present",
        ]) and
        # Must pass critical compliance checks
        all(c["passed"] for c in checks if c["name"] in [
            "section5_fda_approved_forbidden",
            "section5_fda_footnote_required",
            "section4_promo_code",
            "overall_correct_product",
        ])
    )

    return {
        "passed": passed_overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))