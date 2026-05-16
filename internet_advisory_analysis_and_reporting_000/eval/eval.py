import sys
import json
import re
from pathlib import Path

def find_output_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def load_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ─── LOCATE OUTPUT FILES ────────────────────────────────────────────────
    comparison_path = find_output_file(workspace, "provider_comparison.json")
    incident_log_path = find_output_file(workspace, "incident_log.json")
    diagnostics_path = find_output_file(workspace, "diagnostics_report.json")

    # ════════════════════════════════════════════════════════════════════════
    # SECTION A: Provider Comparison (provider_comparison.json)
    # ════════════════════════════════════════════════════════════════════════

    # CHECK A1: File exists
    a1_passed = comparison_path is not None
    checks.append({"name": "A1_provider_comparison_file_exists", "passed": a1_passed,
                   "detail": f"Found at {comparison_path}" if a1_passed else "provider_comparison.json not found anywhere in workspace"})

    comparison_data = None
    if a1_passed:
        try:
            comparison_data = load_json_file(comparison_path)
        except Exception as e:
            checks.append({"name": "A1_parse", "passed": False, "detail": f"JSON parse error: {e}"})
            comparison_data = None

    # CHECK A2: 24-month total cost calculated for each provider (not just monthly)
    # Expected values (with tolerance ±5):
    # FiberNow 500:     12*39.99 + 12*(74.99+9.99) = 479.88 + 1019.88 = 1499.76  (ETF=180 not added unless switching mid-contract)
    # CableZone:        6*49.99  + 6*(49.99+12) + 12*(89.99+12) = wait...
    # Let's recalculate carefully:
    # FiberNow 500: months 1-12: $39.99/mo, months 13-24: $74.99 + $9.99(equipment) = $84.98/mo
    #   Total = 12*39.99 + 12*84.98 = 479.88 + 1019.76 = 1499.64
    # CableZone:    months 1-6: $49.99+$12=$61.99, months 7-24 (18 months): $89.99+$12=$101.99
    #   Total = 6*61.99 + 18*101.99 = 371.94 + 1835.82 = 2207.76
    # DSL-Direct:   12 months: $34.99, then month-to-month (assume 12 more): $34.99 (no promo)
    #   Total = 24*34.99 = 839.76
    # FiberNow Premium: months 1-12: $59.99, months 13-24: $99.99/mo (equipment included)
    #   Total = 12*59.99 + 12*99.99 = 719.88 + 1199.88 = 1919.76

    EXPECTED_24MO = {
        "fibernow": (1450, 1560),       # FiberNow 500 range
        "cablezone": (2150, 2280),      # CableZone range
        "dsl": (800, 880),              # DSL-Direct range (month-to-month after 12)
        "fibernow_premium": (1870, 1980),  # FiberNow Premium range
    }

    a2_passed = False
    a2_detail = "comparison_data not loaded"
    if comparison_data is not None:
        try:
            providers_list = comparison_data if isinstance(comparison_data, list) else comparison_data.get("providers", [])
            found_24mo_costs = []
            for p in providers_list:
                cost_key = None
                for k in p.keys():
                    if "24" in k.lower() or "total" in k.lower() or "cost" in k.lower():
                        cost_key = k
                        break
                if cost_key:
                    try:
                        cost_val = float(str(p[cost_key]).replace("$", "").replace(",", ""))
                        found_24mo_costs.append((p.get("name", p.get("provider", "unknown")), cost_val))
                    except:
                        pass

            if len(found_24mo_costs) >= 3:
                # Check at least some are in realistic 24-month range (> $500 and < $3000)
                valid_costs = [(n, c) for n, c in found_24mo_costs if 500 < c < 3000]
                if len(valid_costs) >= 3:
                    a2_passed = True
                    a2_detail = f"Found 24-month costs: {found_24mo_costs}"
                else:
                    a2_detail = f"Costs seem to be monthly, not 24-month totals: {found_24mo_costs}"
            else:
                a2_detail = f"Only found {len(found_24mo_costs)} 24-month cost entries, need at least 3. Keys found: {[list(p.keys()) for p in providers_list[:2]] if providers_list else 'no providers'}"
        except Exception as e:
            a2_detail = f"Error checking 24-month costs: {e}"

    checks.append({"name": "A2_24month_total_cost_calculated", "passed": a2_passed, "detail": a2_detail})

    # CHECK A3: Post-promotional price shown (not just promo rate)
    # FiberNow promo is $39.99 but real is $74.99 — must show the higher number
    a3_passed = False
    a3_detail = "comparison_data not loaded"
    if comparison_data is not None:
        try:
            raw_text = json.dumps(comparison_data).lower()
            # Must contain post-promo values: 74.99, 84.98 or 84.99, 89.99, 99.99
            found_post_promo = []
            for val in ["74.99", "84.98", "84.99", "89.99", "99.99"]:
                if val in raw_text:
                    found_post_promo.append(val)
            if len(found_post_promo) >= 2:
                a3_passed = True
                a3_detail = f"Post-promo prices found: {found_post_promo}"
            else:
                a3_detail = f"Post-promo prices largely missing. Only found: {found_post_promo}. Need at least 74.99 and 89.99 or 99.99"
        except Exception as e:
            a3_detail = f"Error: {e}"
    checks.append({"name": "A3_post_promo_prices_shown", "passed": a3_passed, "detail": a3_detail})

    # CHECK A4: ETF (early termination fees) included
    a4_passed = False
    a4_detail = "comparison_data not loaded"
    if comparison_data is not None:
        try:
            raw_text = json.dumps(comparison_data).lower()
            etf_present = any(kw in raw_text for kw in ["termination", "etf", "early_termination", "early termination", "penalty"])
            etf_values = any(v in raw_text for v in ["180", "240", "50"])
            if etf_present and etf_values:
                a4_passed = True
                a4_detail = "ETF information found with numeric values"
            elif etf_present:
                a4_detail = "ETF keyword found but specific values (180, 240, 50) missing"
            else:
                a4_detail = "No ETF / early termination information found in comparison"
        except Exception as e:
            a4_detail = f"Error: {e}"
    checks.append({"name": "A4_etf_included", "passed": a4_passed, "detail": a4_detail})

    # CHECK A5: Technology type noted (fiber vs cable vs DSL)
    a5_passed = False
    a5_detail = "comparison_data not loaded"
    if comparison_data is not None:
        try:
            raw_text = json.dumps(comparison_data).lower()
            tech_types = [t for t in ["fiber", "cable", "dsl"] if t in raw_text]
            if len(tech_types) >= 2:
                a5_passed = True
                a5_detail = f"Technology types noted: {tech_types}"
            else:
                a5_detail = f"Only found technology types: {tech_types}, need at least fiber+cable or dsl"
        except Exception as e:
            a5_detail = f"Error: {e}"
    checks.append({"name": "A5_technology_type_noted", "passed": a5_passed, "detail": a5_detail})

    # ════════════════════════════════════════════════════════════════════════
    # SECTION B: Diagnostics Report (diagnostics_report.json)
    # ════════════════════════════════════════════════════════════════════════

    b1_passed = diagnostics_path is not None
    checks.append({"name": "B1_diagnostics_report_file_exists", "passed": b1_passed,
                   "detail": f"Found at {diagnostics_path}" if b1_passed else "diagnostics_report.json not found"})

    diagnostics_data = None
    if b1_passed:
        try:
            diagnostics_data = load_json_file(diagnostics_path)
        except Exception as e:
            checks.append({"name": "B1_parse", "passed": False, "detail": f"JSON parse error: {e}"})

    # CHECK B2: Readings flagged that are <70% of 500 Mbps contracted = < 350 Mbps
    # Readings < 350 Mbps: 102.4, 98.7, 55.2, 48.9, 51.1, 188.4, 312.5, 340.2
    # Readings >= 350 Mbps: 487.3, 450.1, 489.2, 501.3
    FLAGGED_DATES = {"2024-03-05", "2024-03-12", "2024-03-18", "2024-03-22", "2024-04-02"}
    # Minimum: the severe ones must be flagged (Mar 5 x2, Mar 18 x3)
    MUST_FLAG_DATES = {"2024-03-05", "2024-03-18"}

    b2_passed = False
    b2_detail = "diagnostics_data not loaded"
    if diagnostics_data is not None:
        try:
            raw_text = json.dumps(diagnostics_data).lower()
            # Look for flagged entries: check if 2024-03-05 and 2024-03-18 are marked as flagged/below_threshold
            flag_keywords = ["flag", "below", "threshold", "below_threshold", "degraded", "issue", "warning", "fail"]
            has_flag_keyword = any(kw in raw_text for kw in flag_keywords)
            # Check for the specific dates
            has_mar5 = "2024-03-05" in raw_text or "march 5" in raw_text or "03-05" in raw_text
            has_mar18 = "2024-03-18" in raw_text or "march 18" in raw_text or "03-18" in raw_text
            # Check 70% threshold referenced
            has_threshold = "70" in raw_text or "350" in raw_text or "0.7" in raw_text

            if has_flag_keyword and has_mar5 and has_mar18:
                b2_passed = True
                b2_detail = f"Flagging logic present. Threshold ref: {has_threshold}. Mar5: {has_mar5}, Mar18: {has_mar18}"
            else:
                b2_detail = f"Missing elements. flag_keyword={has_flag_keyword}, mar5={has_mar5}, mar18={has_mar18}, threshold={has_threshold}"
        except Exception as e:
            b2_detail = f"Error: {e}"
    checks.append({"name": "B2_below_70pct_readings_flagged", "passed": b2_passed, "detail": b2_detail})

    # CHECK B3: Packet loss flagged (>0% readings identified)
    b3_passed = False
    b3_detail = "diagnostics_data not loaded"
    if diagnostics_data is not None:
        try:
            raw_text = json.dumps(diagnostics_data).lower()
            has_packet_loss = "packet" in raw_text and ("loss" in raw_text or "packet_loss" in raw_text)
            # High packet loss events: 3.2%, 4.1%, 11.5%, 13.2%, 12.8%
            high_loss_present = any(v in raw_text for v in ["11.5", "13.2", "12.8", "3.2", "4.1"])
            if has_packet_loss and high_loss_present:
                b3_passed = True
                b3_detail = "Packet loss data captured including high-loss events"
            else:
                b3_detail = f"packet_loss keyword={has_packet_loss}, high_loss_values={high_loss_present}"
        except Exception as e:
            b3_detail = f"Error: {e}"
    checks.append({"name": "B3_packet_loss_flagged", "passed": b3_passed, "detail": b3_detail})

    # CHECK B4: Issue classification present (local / ISP / destination)
    b4_passed = False
    b4_detail = "diagnostics_data not loaded"
    if diagnostics_data is not None:
        try:
            raw_text = json.dumps(diagnostics_data).lower()
            classification_keywords = ["isp", "local", "destination", "classification", "source", "cause"]
            found_classifications = [kw for kw in classification_keywords if kw in raw_text]
            if len(found_classifications) >= 2:
                b4_passed = True
                b4_detail = f"Classification keywords found: {found_classifications}"
            else:
                b4_detail = f"Insufficient classification. Found: {found_classifications}"
        except Exception as e:
            b4_detail = f"Error: {e}"
    checks.append({"name": "B4_issue_classification_present", "passed": b4_passed, "detail": b4_detail})

    # ════════════════════════════════════════════════════════════════════════
    # SECTION C: Incident Log (incident_log.json)
    # ════════════════════════════════════════════════════════════════════════

    c1_passed = incident_log_path is not None
    checks.append({"name": "C1_incident_log_file_exists", "passed": c1_passed,
                   "detail": f"Found at {incident_log_path}" if c1_passed else "incident_log.json not found"})

    incident_data = None
    if c1_passed:
        try:
            incident_data = load_json_file(incident_log_path)
        except Exception as e:
            checks.append({"name": "C1_parse", "passed": False, "detail": f"JSON parse error: {e}"})

    # CHECK C2: At least 2 incidents parsed (March 5 + March 18; April 2 optional)
    c2_passed = False
    c2_detail = "incident_data not loaded"
    if incident_data is not None:
        try:
            incidents = incident_data if isinstance(incident_data, list) else incident_data.get("incidents", [])
            if len(incidents) >= 2:
                c2_passed = True
                c2_detail = f"Found {len(incidents)} incidents"
            else:
                c2_detail = f"Only {len(incidents)} incidents found, need at least 2"
        except Exception as e:
            c2_detail = f"Error: {e}"
    checks.append({"name": "C2_minimum_two_incidents_parsed", "passed": c2_passed, "detail": c2_detail})

    # CHECK C3: Each incident has date, time, duration, speedtest_results, steps_attempted
    # These are the SKILL.md required fields for ISP dispute escalation
    REQUIRED_INCIDENT_FIELDS_OPTIONS = [
        ["date", "time", "duration", "speedtest", "steps"],
        ["date", "time", "duration", "speed", "attempted"],
        ["timestamp", "duration", "speedtest", "steps"],
    ]

    c3_passed = False
    c3_detail = "incident_data not loaded"
    if incident_data is not None:
        try:
            incidents = incident_data if isinstance(incident_data, list) else incident_data.get("incidents", [])
            if incidents:
                # Check first incident for required fields
                raw_incident = json.dumps(incidents[0]).lower()
                field_checks = {
                    "date_or_timestamp": any(kw in raw_incident for kw in ["date", "timestamp", "time"]),
                    "duration": "duration" in raw_incident,
                    "speedtest_results": any(kw in raw_incident for kw in ["speedtest", "speed_test", "speed", "mbps", "download", "down"]),
                    "steps_attempted": any(kw in raw_incident for kw in ["step", "attempted", "action", "tried", "remediation"]),
                }
                all_present = all(field_checks.values())
                missing = [k for k, v in field_checks.items() if not v]
                if all_present:
                    c3_passed = True
                    c3_detail = "All required incident fields present"
                else:
                    c3_detail = f"Missing fields in incident record: {missing}. Field checks: {field_checks}"
            else:
                c3_detail = "No incidents to check fields on"
        except Exception as e:
            c3_detail = f"Error: {e}"
    checks.append({"name": "C3_required_incident_fields_present", "passed": c3_passed, "detail": c3_detail})

    # CHECK C4: March 18 incident captures ~7.5 hour duration + multiple speedtest readings
    c4_passed = False
    c4_detail = "incident_data not loaded"
    if incident_data is not None:
        try:
            incidents = incident_data if isinstance(incident_data, list) else incident_data.get("incidents", [])
            raw_all = json.dumps(incidents).lower()
            # March 18 must be present
            has_mar18 = "2024-03-18" in raw_all or "march 18" in raw_all or "03-18" in raw_all or "mar 18" in raw_all
            # Duration around 7-8 hours
            has_duration = any(d in raw_all for d in ["7.5", "7 hour", "7.5 hour", "450 min", "7h", "8 hour", "7 hours", "8 hours"])
            # Multiple speed readings captured
            has_multiple_readings = raw_all.count("mbps") >= 3 or raw_all.count("48.9") >= 1 or raw_all.count("55.2") >= 1
            if has_mar18 and (has_duration or has_multiple_readings):
                c4_passed = True
                c4_detail = f"Mar18 incident: present={has_mar18}, duration={has_duration}, multiple_readings={has_multiple_readings}"
            else:
                c4_detail = f"Mar18 incident incomplete: present={has_mar18}, duration={has_duration}, multiple_readings={has_multiple_readings}"
        except Exception as e:
            c4_detail = f"Error: {e}"
    checks.append({"name": "C4_major_outage_march18_documented", "passed": c4_passed, "detail": c4_detail})

    # CHECK C5: ISP dispute context present (e.g., ISP claimed no outage but evidence contradicts)
    c5_passed = False
    c5_detail = "incident_data not loaded"
    if incident_data is not None:
        try:
            raw_all = json.dumps(incident_data).lower()
            isp_dispute_keywords = ["isp", "dispute", "escalat", "no outage", "claimed", "denied", "contradict", "evidence", "hold"]
            found = [kw for kw in isp_dispute_keywords if kw in raw_all]
            if len(found) >= 2:
                c5_passed = True
                c5_detail = f"ISP dispute context keywords found: {found}"
            else:
                c5_detail = f"Insufficient ISP dispute context. Only found: {found}"
        except Exception as e:
            c5_detail = f"Error: {e}"
    checks.append({"name": "C5_isp_dispute_context_documented", "passed": c5_passed, "detail": c5_detail})

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════
    # Weights:
    # A1: 0.04, A2: 0.12, A3: 0.10, A4: 0.08, A5: 0.06
    # B1: 0.04, B2: 0.12, B3: 0.08, B4: 0.06
    # C1: 0.04, C2: 0.08, C3: 0.10, C4: 0.08, C5: 0.06

    weights = {
        "A1_provider_comparison_file_exists": 0.04,
        "A2_24month_total_cost_calculated": 0.12,
        "A3_post_promo_prices_shown": 0.10,
        "A4_etf_included": 0.08,
        "A5_technology_type_noted": 0.06,
        "B1_diagnostics_report_file_exists": 0.04,
        "B2_below_70pct_readings_flagged": 0.12,
        "B3_packet_loss_flagged": 0.08,
        "B4_issue_classification_present": 0.06,
        "C1_incident_log_file_exists": 0.04,
        "C2_minimum_two_incidents_parsed": 0.08,
        "C3_required_incident_fields_present": 0.10,
        "C4_major_outage_march18_documented": 0.08,
        "C5_isp_dispute_context_documented": 0.06,
    }

    total_score = sum(weights.get(c["name"], 0) * (1.0 if c["passed"] else 0.0) for c in checks)
    # Round to avoid float noise
    total_score = round(total_score, 4)

    all_passed = total_score >= 0.75

    result = {
        "passed": all_passed,
        "score": total_score,
        "checks": checks
    }

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)