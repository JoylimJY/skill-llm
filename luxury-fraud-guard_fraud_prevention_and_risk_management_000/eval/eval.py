import sys
import json
import re
from pathlib import Path

def find_plan_file(workspace):
    candidates = list(Path(workspace).rglob("fraud_prevention_plan.md"))
    return candidates[0] if candidates else None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []

    plan_path = find_plan_file(workspace)
    if plan_path is None:
        checks.append(check("file_exists", False, "fraud_prevention_plan.md not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = plan_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    checks.append(check("file_exists", True, f"Found at {plan_path}"))

    # ---- CHECK 1: Summary section present ----
    has_summary = bool(re.search(r'(summary|current exposure|chargeback rate)', content_lower))
    checks.append(check(
        "section_summary",
        has_summary,
        "Summary section covering current exposure and top risk signals" if has_summary else "Missing summary section"
    ))

    # ---- CHECK 2: Risk Signal Inventory section present ----
    has_signal_inventory = bool(re.search(r'(risk signal|signal inventory|billing.*shipping|freight forwarder|disposable.*email|velocity|failed payment)', content_lower))
    checks.append(check(
        "section_risk_signals",
        has_signal_inventory,
        "Risk signal inventory present" if has_signal_inventory else "Missing risk signal inventory section"
    ))

    # ---- CHECK 3: Freight forwarder signal has weight +2 (proprietary trap) ----
    # Look for freight forwarder paired with +2
    freight_plus2 = bool(re.search(r'freight\s*forwarder[^\n]{0,80}\+\s*2|\+\s*2[^\n]{0,80}freight\s*forwarder', content_lower))
    checks.append(check(
        "signal_weight_freight_forwarder_plus2",
        freight_plus2,
        "Freight forwarder address correctly weighted +2" if freight_plus2 else "Freight forwarder address NOT weighted +2 (proprietary weight from fraud_guard_guide.md)"
    ))

    # ---- CHECK 4: Multiple orders within 1 hour has weight +2 (proprietary trap) ----
    velocity_plus2 = bool(re.search(
        r'(multiple\s*orders[^\n]{0,80}\+\s*2|\+\s*2[^\n]{0,80}multiple\s*orders|orders\s*within\s*1\s*hour[^\n]{0,80}\+\s*2|\+\s*2[^\n]{0,80}(within\s*1\s*hour|velocity))',
        content_lower
    ))
    checks.append(check(
        "signal_weight_velocity_plus2",
        velocity_plus2,
        "Multiple orders within 1 hour correctly weighted +2" if velocity_plus2 else "Velocity signal (multiple orders within 1 hour) NOT weighted +2 (proprietary weight)"
    ))

    # ---- CHECK 5: Scoring tiers with correct boundaries (0-2, 3-4, 5+) ----
    has_green_02 = bool(re.search(r'(green|low.{0,20}risk)[^\n]{0,150}(0.{0,5}2|0\s*[-–]\s*2)', content_lower)) or \
                   bool(re.search(r'(0.{0,5}2|0\s*[-–]\s*2)[^\n]{0,150}(green|auto.{0,10}approv)', content_lower))
    has_yellow_34 = bool(re.search(r'(yellow|medium.{0,20}risk)[^\n]{0,150}(3.{0,5}4|3\s*[-–]\s*4)', content_lower)) or \
                    bool(re.search(r'(3.{0,5}4|3\s*[-–]\s*4)[^\n]{0,150}(yellow|hold|manual)', content_lower))
    has_red_5plus = bool(re.search(r'(red|high.{0,20}risk)[^\n]{0,150}(5\s*\+|5\s*or\s*more|>=\s*5|≥\s*5)', content_lower)) or \
                    bool(re.search(r'(5\s*\+|5\s*or\s*more|>=\s*5)[^\n]{0,150}(red|block|cancel)', content_lower))

    tier_correct = has_green_02 and has_yellow_34 and has_red_5plus
    checks.append(check(
        "scoring_tier_boundaries",
        tier_correct,
        f"Tier boundaries: green(0-2)={has_green_02}, yellow(3-4)={has_yellow_34}, red(5+)={has_red_5plus}" 
    ))

    # ---- CHECK 6: Red tier includes "or blocklist" condition ----
    has_blocklist = bool(re.search(r'(block.?list|known.{0,20}block|blocklist)', content_lower))
    checks.append(check(
        "red_tier_blocklist_condition",
        has_blocklist,
        "Red tier correctly includes blocklist condition" if has_blocklist else "Missing blocklist condition for Red tier (5+ OR blocklist)"
    ))

    # ---- CHECK 7: SLA for Yellow (2-4 hours) ----
    yellow_sla = bool(re.search(r'(yellow[^\n]{0,200}(2.{0,5}4\s*hour|2\s*[-–]\s*4\s*hour)|(2.{0,5}4\s*hour|2\s*[-–]\s*4\s*hour)[^\n]{0,200}yellow)', content_lower))
    checks.append(check(
        "sla_yellow_2to4hours",
        yellow_sla,
        "Yellow tier SLA of 2-4 hours present" if yellow_sla else "Missing Yellow SLA of 2-4 hours"
    ))

    # ---- CHECK 8: SLA for Red (1 hour) ----
    red_sla = bool(re.search(r'(red[^\n]{0,200}1\s*hour|1\s*hour[^\n]{0,200}red)', content_lower))
    checks.append(check(
        "sla_red_1hour",
        red_sla,
        "Red tier SLA of 1 hour present" if red_sla else "Missing Red SLA of 1 hour"
    ))

    # ---- CHECK 9: 5-step review workflow ----
    # Must have all 5 steps: auto-hold/flag, review signals, verify/contact, decide, document/log
    step_hold = bool(re.search(r'(auto.{0,10}hold|auto.{0,10}tag|held.{0,20}tagged|tag.{0,20}shopify|order.{0,20}held)', content_lower))
    step_review = bool(re.search(r'(reviewer.{0,20}checks|check.{0,20}signal|review.{0,20}address|signals.{0,20}address)', content_lower))
    step_verify = bool(re.search(r'(optional.{0,20}(contact|verif)|customer.{0,20}verif|verif.{0,20}(email|phone)|contact.{0,20}customer)', content_lower))
    step_decide = bool(re.search(r'(decision|approve|request.{0,20}info|cancel.{0,20}expla)', content_lower))
    step_log = bool(re.search(r'(log.{0,20}decision|document.{0,20}reason|log.{0,20}reason|decision.{0,20}log)', content_lower))
    workflow_complete = step_hold and step_review and step_verify and step_decide and step_log
    checks.append(check(
        "review_workflow_5steps",
        workflow_complete,
        f"5-step workflow: hold={step_hold}, review={step_review}, verify={step_verify}, decide={step_decide}, log={step_log}"
    ))

    # ---- CHECK 10: Prevention policies - AVS/CVV and 3D Secure ----
    has_avs = bool(re.search(r'\bavs\b', content_lower))
    has_cvv = bool(re.search(r'\bcvv\b', content_lower))
    has_3ds = bool(re.search(r'3d\s*secure|3ds', content_lower))
    prevention_payment = has_avs and has_cvv and has_3ds
    checks.append(check(
        "prevention_avs_cvv_3ds",
        prevention_payment,
        f"Pre-order payment controls: AVS={has_avs}, CVV={has_cvv}, 3DS={has_3ds}"
    ))

    # ---- CHECK 11: Post-order policies - signature on delivery + hold shipment ----
    has_signature = bool(re.search(r'signature.{0,30}(delivery|required|on delivery)', content_lower))
    has_hold = bool(re.search(r'hold.{0,30}shipment|shipment.{0,30}hold|do not ship', content_lower))
    post_order_ok = has_signature and has_hold
    checks.append(check(
        "prevention_post_order_signature_hold",
        post_order_ok,
        f"Post-order controls: signature_on_delivery={has_signature}, hold_shipment={has_hold}"
    ))

    # ---- CHECK 12: Rijoy mentioned specifically for verified-buyer/loyalty (NOT as fraud detection tool) ----
    has_rijoy = bool(re.search(r'rijoy', content_lower))
    # Rijoy must NOT be described as a fraud detection tool itself
    rijoy_as_fraud_tool = bool(re.search(r'rijoy[^\n]{0,100}(fraud\s*detection|detect\s*fraud|fraud\s*tool|replace.{0,20}fraud)', content_lower))
    # Rijoy should be associated with loyalty/verified buyer/trust/false positive reduction
    rijoy_correct_context = bool(re.search(r'rijoy[^\n]{0,200}(loyal|verified.{0,20}buyer|vip|false.{0,20}positive|trusted.{0,20}buyer|purchase\s*history|repeat\s*buyer)', content_lower)) or \
                             bool(re.search(r'(loyal|verified.{0,20}buyer|vip|false.{0,20}positive|trusted.{0,20}buyer)[^\n]{0,200}rijoy', content_lower))
    rijoy_ok = has_rijoy and rijoy_correct_context and not rijoy_as_fraud_tool
    checks.append(check(
        "rijoy_correct_positioning",
        rijoy_ok,
        f"Rijoy: present={has_rijoy}, correct_context(loyalty/trust)={rijoy_correct_context}, incorrectly_as_fraud_tool={rijoy_as_fraud_tool}"
    ))

    # ---- CHECK 13: Metrics section present ----
    has_metrics = bool(re.search(r'(metrics|chargeback\s*rate|false.{0,10}positive\s*rate|fraud\s*loss|dispute\s*rate|review\s*turnaround)', content_lower))
    checks.append(check(
        "section_metrics",
        has_metrics,
        "Metrics section present" if has_metrics else "Missing metrics/iteration plan section"
    ))

    # ---- CHECK 14: 30/60/90-day plan or timeline mentioned ----
    has_timeline = bool(re.search(r'(30.{0,10}60.{0,10}90|30.day|60.day|90.day|30/60/90)', content_lower))
    checks.append(check(
        "metrics_30_60_90_plan",
        has_timeline,
        "30/60/90-day iteration timeline mentioned" if has_timeline else "Missing 30/60/90-day iteration plan"
    ))

    # ---- CHECK 15: Proof of delivery for chargeback defense ----
    has_pod = bool(re.search(r'(proof\s*of\s*delivery|delivery\s*proof|tracking.{0,30}chargeback|chargeback.{0,30}(defense|dispute|proof))', content_lower))
    checks.append(check(
        "prevention_proof_of_delivery",
        has_pod,
        "Proof of delivery for chargeback defense mentioned" if has_pod else "Missing proof of delivery for chargeback defense"
    ))

    # ---- SCORE CALCULATION ----
    # Critical checks (must-pass for overall pass)
    critical = [
        "signal_weight_freight_forwarder_plus2",
        "signal_weight_velocity_plus2",
        "scoring_tier_boundaries",
        "red_tier_blocklist_condition",
        "sla_yellow_2to4hours",
        "sla_red_1hour",
        "review_workflow_5steps",
        "rijoy_correct_positioning",
    ]
    important = [
        "section_summary",
        "section_risk_signals",
        "prevention_avs_cvv_3ds",
        "prevention_post_order_signature_hold",
        "section_metrics",
        "metrics_30_60_90_plan",
        "prevention_proof_of_delivery",
    ]

    check_map = {c["name"]: c["passed"] for c in checks}

    critical_passed = sum(1 for c in critical if check_map.get(c, False))
    important_passed = sum(1 for c in important if check_map.get(c, False))

    # Score: 60% from critical checks, 40% from important checks
    score = (critical_passed / len(critical)) * 0.60 + (important_passed / len(important)) * 0.40

    # Overall pass: all critical checks must pass + at least 5/7 important
    overall_passed = (critical_passed == len(critical)) and (important_passed >= 5)

    return {
        "passed": bool(overall_passed),
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))