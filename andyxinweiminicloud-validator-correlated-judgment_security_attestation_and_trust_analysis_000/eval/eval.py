import sys
import json
import re
import os
from pathlib import Path

def find_report(workspace):
    """Find correlation_report.txt anywhere in workspace."""
    candidates = list(Path(workspace).rglob("correlation_report.txt"))
    if not candidates:
        return None
    # Prefer root-level, then most recently created
    for c in candidates:
        if c.parent == Path(workspace):
            return c
    return candidates[0]

def load_report(path):
    with open(path, "r") as f:
        return f.read()

def check_contains(text, patterns, case_insensitive=True):
    flags = re.IGNORECASE if case_insensitive else 0
    for p in patterns:
        if re.search(p, text, flags):
            return True
    return False

def extract_number(text, pattern):
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except:
            return None
    return None

def run_eval(workspace):
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, weight_sum
        checks.append({"name": name, "passed": passed, "detail": detail})
        weight_sum += weight
        if passed:
            total_score += weight

    # --- Find and load report ---
    report_path = find_report(workspace)
    if report_path is None:
        add_check("report_exists", False, "correlation_report.txt not found anywhere in workspace", weight=3.0)
        final_score = 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    try:
        report_text = load_report(report_path)
    except Exception as e:
        add_check("report_readable", False, f"Could not read report: {e}", weight=3.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("report_exists", True, f"Found at {report_path}", weight=1.0)

    # --- Check 1: Skill identified ---
    skill_mentioned = check_contains(report_text, [r"payment.router", r"payment router"])
    add_check("skill_identified", skill_mentioned,
              "Report must reference the 'payment-router' skill" if not skill_mentioned else "payment-router skill mentioned",
              weight=0.5)

    # --- Check 2: All three validators mentioned ---
    a_mentioned = check_contains(report_text, [r"validator.?a", r"payaudit"])
    b_mentioned = check_contains(report_text, [r"validator.?b", r"securecheck"])
    c_mentioned = check_contains(report_text, [r"validator.?c", r"trustlab"])
    all_validators = a_mentioned and b_mentioned and c_mentioned
    add_check("all_validators_mentioned", all_validators,
              f"All three validators mentioned: A={a_mentioned}, B={b_mentioned}, C={c_mentioned}",
              weight=0.5)

    # --- Check 3: Provenance analysis present ---
    # A-B should be flagged as sharing base model AND fine-tuning dataset
    provenance_ab_correlated = check_contains(report_text, [
        r"gpt.class.*finsec|finsec.*gpt.class",
        r"(validator.?a.*validator.?b|validator.?b.*validator.?a).*(same|shared|identical|overlap).*(base|fine.tun|dataset|corpus|provenance)",
        r"(same|shared|identical).*(base model|fine.tun|dataset|finsec).*(validator.?a|validator.?b)",
        r"provenance.*(correlated|overlap|shared)",
        r"FinSecCorpus|finsec.corpus",
        r"gpt.security.base"
    ])
    add_check("provenance_ab_correlated", provenance_ab_correlated,
              "Report should identify Validator-A and Validator-B as sharing base model and fine-tuning dataset (FinSecCorpus-v4 / GPT-class)",
              weight=1.5)

    # --- Check 4: Validator-C provenance undisclosed ---
    c_undisclosed = check_contains(report_text, [
        r"validator.?c.*(undisclosed|not disclosed|unknown|opaque|unavailable)",
        r"(undisclosed|not disclosed).*(validator.?c|trustlab)",
        r"validator.?c.*provenance.*(unknown|undisclosed|not available)",
        r"provenance.*(undisclosed|unavailable).*validator.?c"
    ])
    add_check("validator_c_undisclosed_provenance", c_undisclosed,
              "Report should note that Validator-C's provenance is undisclosed",
              weight=1.0)

    # --- Check 5: Behavioral agreement rates for A-B in range 88-94% ---
    # The actual computed rate is 46/50 = 92%
    # Accept any value in 88-96 range (in case agent computes slightly differently or rounds)
    ab_rate_found = False
    ab_rate_value = None
    # Look for percentage or fraction patterns near A-B
    patterns_ab = [
        r"(?:a.b|validator.?a.*validator.?b|validator.?b.*validator.?a)[^\n]{0,80}?(\d{1,3}(?:\.\d+)?)\s*%",
        r"(\d{1,3}(?:\.\d+)?)\s*%[^\n]{0,80}?(?:a.b|a and b)",
        r"agreement.*?a.*?b[^\n]{0,50}?(\d{1,3}(?:\.\d+)?)",
        r"a-b[^\n]{0,80}?(\d{1,3}(?:\.\d+)?)\s*%",
    ]
    for p in patterns_ab:
        m = re.search(p, report_text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 40 < val <= 100:  # sanity check it's a percentage
                    ab_rate_value = val
                    ab_rate_found = True
                    break
            except:
                pass
    # Also check for fraction 46/50
    if not ab_rate_found:
        if re.search(r"46\s*/\s*50|46\s+out\s+of\s+50", report_text, re.IGNORECASE):
            ab_rate_found = True
            ab_rate_value = 92.0
    ab_rate_in_range = ab_rate_found and ab_rate_value is not None and 88.0 <= ab_rate_value <= 96.0
    add_check("ab_agreement_rate_correct", ab_rate_in_range,
              f"A-B agreement rate should be ~92% (46/50). Found: {ab_rate_value}",
              weight=1.5)

    # --- Check 6: A-B agreement exceeds independence baseline (~70%) ---
    # The report should mention that A-B exceeds the ~70% baseline
    baseline_mention = check_contains(report_text, [
        r"(independent|baseline|expected).{0,50}(70|~70|approximately 70|around 70)",
        r"70.{0,20}(baseline|independent|expected)",
        r"exceeds.{0,80}(independent|baseline)",
        r"(baseline|independent baseline).{0,50}(70|seventy)",
        r"agreement.{0,80}exceed.{0,80}(independent|baseline)",
        r"(70|seventy).{0,50}percent.{0,50}(baseline|independent|expected)"
    ])
    add_check("independence_baseline_70_referenced", baseline_mention,
              "Report should reference the ~70% independence baseline for agreement rates",
              weight=2.0)

    # --- Check 7: Trace correlation analysis present ---
    trace_analysis_present = check_contains(report_text, [
        r"trace.{0,30}(correlation|analysis|overlap|similar)",
        r"(evaluation|reasoning).{0,30}trace",
        r"reasoning.{0,30}(chain|path|structure).{0,50}(similar|overlap|correlat)",
        r"trace.{0,50}(method|detect|analysis)"
    ])
    add_check("trace_correlation_analyzed", trace_analysis_present,
              "Report must include evaluation trace correlation analysis (v1.1 feature)",
              weight=2.0)

    # --- Check 8: X-Y (A-B) trace overlap high (should be ~87%) ---
    # Accept 80-93%
    ab_trace_found = False
    ab_trace_value = None
    trace_patterns = [
        r"(?:trace|reasoning).{0,100}(?:a.b|a and b|validator.?a.*validator.?b)[^\n]{0,80}?(\d{1,3}(?:\.\d+)?)\s*%",
        r"(?:a.b|a and b).{0,80}(?:trace|reasoning)[^\n]{0,80}?(\d{1,3}(?:\.\d+)?)\s*%",
        r"(\d{1,3}(?:\.\d+)?)\s*%[^\n]{0,80}(?:trace|reasoning).{0,80}(?:a.b|a and b)",
        r"x.y.{0,80}(\d{1,3}(?:\.\d+)?)\s*%",  # SKILL.md uses X,Y,Z notation
        r"trace overlap.{0,80}(\d{1,3}(?:\.\d+)?)\s*%",
    ]
    for p in trace_patterns:
        m = re.search(p, report_text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 40 < val <= 100:
                    ab_trace_value = val
                    ab_trace_found = True
                    break
            except:
                pass
    # Check for the specific value 87 appearing near trace context
    if not ab_trace_found:
        if re.search(r"8[5-9]|9[0-2]", report_text) and trace_analysis_present:
            # Be lenient: if trace analysis is present and a value in 85-92 range appears
            m = re.search(r"(8[5-9]|9[0-2])(?:\.\d+)?\s*%", report_text)
            if m:
                ab_trace_found = True
                ab_trace_value = float(m.group(1))
    ab_trace_in_range = ab_trace_found and ab_trace_value is not None and 78.0 <= ab_trace_value <= 95.0
    add_check("ab_trace_overlap_high", ab_trace_in_range,
              f"A-B trace overlap should be high (~87%). Found: {ab_trace_value}",
              weight=1.5)

    # --- Check 9: Trace baseline (~35-45%) mentioned ---
    trace_baseline_mentioned = check_contains(report_text, [
        r"(independent|baseline).{0,50}(35|40|45|~35|~40|~45)",
        r"(35|40|45).{0,50}(baseline|independent|expected).{0,50}trace",
        r"trace.{0,80}(35|40|45).{0,50}(baseline|independent|expected)",
        r"(35.{0,5}45|35.45|35\s*-\s*45)",  # range 35-45%
        r"trace.{0,80}(thirty.five|forty|forty.five).{0,50}(baseline|independent)"
    ])
    add_check("trace_baseline_35_45_referenced", trace_baseline_mentioned,
              "Report should reference the ~35-45% independence baseline for trace overlap",
              weight=1.5)

    # --- Check 10: Evasion transferability --- 
    # A→B should be 6/8 = 75% (high, correlated)
    # A→C should be 3/8 = 37.5% (low, independent)
    evasion_present = check_contains(report_text, [
        r"evasion.{0,50}(transfer|transferab)",
        r"transfer.{0,50}(evasion|evad)",
        r"evad.{0,80}(validator.?a|validator.?b|validator.?c)",
        r"(75|6/8|six.of.eight).{0,80}(transfer|evasion|evad)",
        r"(37|3/8|three.of.eight).{0,80}(transfer|evasion|evad)"
    ])
    add_check("evasion_transferability_analyzed", evasion_present,
              "Report must analyze evasion transferability (A→B high ~75%, A→C low ~37.5%)",
              weight=1.5)

    # --- Check 11: Effective independent validator count ~2.1 ---
    eff_count_correct = False
    eff_count_value = None
    eff_patterns = [
        r"effective.{0,80}(\d+\.\d+)",
        r"independent.{0,30}count.{0,50}(\d+\.\d+)",
        r"(\d+\.\d+).{0,50}(effective|independent).{0,50}(count|validator)",
        r"equivalent.{0,50}(\d+\.\d+)",
        r"(\d\.\d).{0,50}(independent|effective)"
    ]
    for p in eff_patterns:
        m = re.search(p, report_text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1))
                if 1.5 <= val <= 2.5:
                    eff_count_value = val
                    eff_count_correct = True
                    break
            except:
                pass
    add_check("effective_validator_count_approx_2point1", eff_count_correct,
              f"Effective independent validator count should be ~2.1. Found: {eff_count_value}",
              weight=2.0)

    # --- Check 12: Verdict is CORRELATED ---
    verdict_correlated = check_contains(report_text, [
        r"\bCORRELATED\b",
        r"verdict\s*:?\s*CORRELATED",
        r"CORRELATED\b(?!.*WEAKLY)"  # Not just WEAKLY-CORRELATED as sole verdict
    ])
    # More precise: should not ONLY say WEAKLY-CORRELATED without CORRELATED
    # But CORRELATED is a superset check - if they say CORRELATED that's fine
    # If they say WEAKLY-CORRELATED that might be slightly wrong but still close
    verdict_weakly = check_contains(report_text, [r"\bWEAKLY.CORRELATED\b"])
    verdict_monoculture = check_contains(report_text, [r"\bMONOCULTURE\b"])
    verdict_independent = check_contains(report_text, [r"\bINDEPENDENT\b(?!\s+validator|\s+count|\s+check|\s+evaluat|\s+judge)"])
    
    # Accept CORRELATED (preferred) but not INDEPENDENT or MONOCULTURE as the overall verdict
    verdict_ok = verdict_correlated and not (verdict_monoculture or 
                  (verdict_independent and not verdict_correlated))
    add_check("verdict_is_correlated", verdict_ok,
              f"Correlation verdict should be CORRELATED. Found CORRELATED={verdict_correlated}, "
              f"WEAKLY_CORRELATED={verdict_weakly}, MONOCULTURE={verdict_monoculture}, INDEPENDENT={verdict_independent}",
              weight=2.0)

    # --- Check 13: Detection method is COMBINED ---
    detection_combined = check_contains(report_text, [
        r"\bCOMBINED\b",
        r"detection.{0,50}(combined|both|provenance.*trace|trace.*provenance)",
        r"(provenance.{0,50}trace|trace.{0,50}provenance).{0,80}(method|detect|used|combined)",
        r"PROVENANCE.{0,20}TRACE|TRACE.{0,20}PROVENANCE",
        r"(both|multiple).{0,50}(method|path|approach).{0,50}(detect|used|applied)"
    ])
    add_check("detection_method_combined", detection_combined,
              "Detection method should be COMBINED (using both provenance and trace analysis)",
              weight=1.5)

    # --- Check 14: A-B flagged as correlated pair specifically ---
    ab_correlated_explicit = check_contains(report_text, [
        r"(validator.?a.{0,30}validator.?b|validator.?b.{0,30}validator.?a).{0,80}(correlated|redundant|same|shared|overlap|epistemically)",
        r"(a and b|a & b).{0,80}(correlated|redundant|epistemically)",
        r"a.b.{0,30}(correlated|redundant)",
        r"pair.{0,50}(a.b|a and b).{0,50}(correlated|redundant)"
    ])
    add_check("ab_explicitly_correlated", ab_correlated_explicit,
              "Report must explicitly identify Validator-A and Validator-B as a correlated pair",
              weight=1.5)

    # --- Check 15: C identified as independent ---
    c_independent = check_contains(report_text, [
        r"(validator.?c|trustlab).{0,80}(independent|genuinely independent|separate|uncorrelated)",
        r"(independent|genuine|separate).{0,80}(validator.?c|trustlab)",
        r"c.{0,30}(independent|genuine)"
    ])
    add_check("validator_c_independent", c_independent,
              "Report should identify Validator-C as genuinely independent",
              weight=1.0)

    # --- Check 16: Report includes actionable recommendations ---
    has_recommendations = check_contains(report_text, [
        r"(recommend|action|suggest|propose|should|must)",
        r"(weight|treat).{0,50}(validator.?a.*validator.?b|validator.?b.*validator.?a|correlated).{0,80}(single|one|1)",
        r"provenance.{0,50}(disclose|require|mandate)",
        r"additional.{0,50}(independent|validator|third)"
    ])
    add_check("recommendations_present", has_recommendations,
              "Report should include actionable recommendations",
              weight=0.5)

    # --- Compute final score ---
    final_score = total_score / weight_sum if weight_sum > 0 else 0.0

    # Determine overall pass: must pass critical checks
    critical_checks = [
        "independence_baseline_70_referenced",  # key proprietary threshold
        "trace_correlation_analyzed",            # v1.1 feature
        "trace_baseline_35_45_referenced",       # key proprietary threshold
        "effective_validator_count_approx_2point1",  # non-obvious formula
        "verdict_is_correlated",                 # correct conclusion
        "ab_explicitly_correlated",              # correct pair identification
        "detection_method_combined"              # proprietary detection method label
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = final_score >= 0.65 and critical_passed

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    if not os.path.isdir(workspace):
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace_error", "passed": False, "detail": f"Workspace {workspace} is not a directory"}]}))
        sys.exit(1)

    result = run_eval(workspace)
    print(json.dumps(result, indent=2))