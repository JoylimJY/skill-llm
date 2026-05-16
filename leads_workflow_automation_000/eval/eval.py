import json
import sys
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace_path = Path(workspace)
    leads_file = Path.home() / ".leads" / "leads.json"

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # --- Load leads.json ---
    leads = []
    try:
        with open(leads_file) as f:
            leads = json.load(f)
        add_check("leads_db_exists", True, f"Found {len(leads)} leads in {leads_file}")
    except Exception as e:
        add_check("leads_db_exists", False, f"Could not read {leads_file}: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # Expected prospects (from raw_prospects.csv)
    expected_prospects = [
        {"name": "Alice Nguyen",  "email": "alice@shieldcorp.io",       "company": "ShieldCorp",     "source": "LinkedIn",   "priority_score": 87},
        {"name": "Bob Tran",      "email": "bob.tran@fortifytech.com",   "company": "FortifyTech",    "source": "conference", "priority_score": 92},
        {"name": "Carol Mehta",   "email": "carol@nexusdefense.net",     "company": "NexusDefense",   "source": "referral",   "priority_score": 55},
        {"name": "David Park",    "email": "d.park@sentinelwave.com",    "company": "SentinelWave",   "source": "webinar",    "priority_score": 78},
        {"name": "Eve Okonkwo",   "email": "eve.o@cyberfortress.biz",    "company": "CyberFortress",  "source": "direct",     "priority_score": 95},
        {"name": "Frank Lee",     "email": "frank@infraguard.co",        "company": "InfraGuard",     "source": "direct",     "priority_score": 40},
    ]

    # CHECK 1: All 6 leads added
    lead_names_in_db = [l["name"] for l in leads]
    missing = [p["name"] for p in expected_prospects if p["name"] not in lead_names_in_db]
    if not missing:
        add_check("all_6_leads_added", True, "All 6 prospects found in leads DB")
    else:
        add_check("all_6_leads_added", False, f"Missing leads: {missing}")

    def find_lead(name):
        for l in leads:
            if l["name"] == name:
                return l
        return None

    # CHECK 2: Sources are correct (from 'channel' column)
    source_checks_passed = True
    source_details = []
    for p in expected_prospects:
        lead = find_lead(p["name"])
        if lead is None:
            source_checks_passed = False
            source_details.append(f"{p['name']}: not found")
            continue
        expected_source = p["source"]
        actual_source = lead.get("source", "")
        # Case-insensitive check
        if actual_source.lower() == expected_source.lower():
            source_details.append(f"{p['name']}: OK ({actual_source})")
        else:
            source_checks_passed = False
            source_details.append(f"{p['name']}: expected source='{expected_source}' got='{actual_source}'")
    add_check("sources_from_channel_field", source_checks_passed, "; ".join(source_details))

    # CHECK 3: Scores are correctly applied (additive, capped at 100)
    # Eve(95 -> capped to 100 since starts at 0+95=95, Bob 0+92=92)
    # But score is ADDITIVE: starting at 0, adding priority_score
    # Alice: 0+87=87, Bob: 0+92=92, Carol: 0+55=55, David: 0+78=78, Eve: 0+95=95, Frank: 0+40=40
    score_checks_passed = True
    score_details = []
    for p in expected_prospects:
        lead = find_lead(p["name"])
        if lead is None:
            score_checks_passed = False
            score_details.append(f"{p['name']}: not found")
            continue
        expected_score = min(100, p["priority_score"])  # capped at 100
        actual_score = lead.get("score", -1)
        if actual_score == expected_score:
            score_details.append(f"{p['name']}: score={actual_score} OK")
        else:
            score_checks_passed = False
            score_details.append(f"{p['name']}: expected={expected_score} got={actual_score}")
    add_check("scores_correctly_applied", score_checks_passed, "; ".join(score_details))

    # CHECK 4: Follow-ups set (check at least 4 of 6 have follow_up set)
    fu_set = [l for l in leads if l.get("follow_up") and l["follow_up"] != "null" and l["follow_up"] is not None]
    fu_names = [l["name"] for l in fu_set]
    if len(fu_set) >= 4:
        add_check("followups_set", True, f"{len(fu_set)} leads have follow-up dates: {fu_names}")
    else:
        add_check("followups_set", False, f"Only {len(fu_set)} leads have follow-up dates set (need >=4): {fu_names}")

    # CHECK 5: Follow-ups have notes (non-empty)
    fu_with_notes = [l for l in fu_set if l.get("follow_up_note") and str(l["follow_up_note"]).strip() != ""]
    if len(fu_with_notes) >= 4:
        add_check("followup_notes_present", True, f"{len(fu_with_notes)} follow-ups have notes")
    else:
        add_check("followup_notes_present", False, f"Only {len(fu_with_notes)} follow-ups have non-empty notes (need >=4)")

    # CHECK 6: Eve Okonkwo converted with deal_value=200000
    eve = find_lead("Eve Okonkwo")
    if eve is None:
        add_check("eve_converted", False, "Eve Okonkwo not found in DB")
    else:
        eve_status = eve.get("status") == "converted"
        eve_value = eve.get("deal_value")
        # Accept int or float 200000
        eve_value_ok = False
        try:
            eve_value_ok = abs(float(eve_value) - 200000.0) < 0.01
        except (TypeError, ValueError):
            pass
        if eve_status and eve_value_ok:
            add_check("eve_converted", True, f"Eve: status=converted, deal_value={eve_value}")
        else:
            add_check("eve_converted", False, f"Eve: status={eve.get('status')}, deal_value={eve_value} (expected converted + 200000)")

    # CHECK 7: Bob Tran converted with deal_value=120000
    bob = find_lead("Bob Tran")
    if bob is None:
        add_check("bob_converted", False, "Bob Tran not found in DB")
    else:
        bob_status = bob.get("status") == "converted"
        bob_value = bob.get("deal_value")
        bob_value_ok = False
        try:
            bob_value_ok = abs(float(bob_value) - 120000.0) < 0.01
        except (TypeError, ValueError):
            pass
        if bob_status and bob_value_ok:
            add_check("bob_converted", True, f"Bob: status=converted, deal_value={bob_value}")
        else:
            add_check("bob_converted", False, f"Bob: status={bob.get('status')}, deal_value={bob_value} (expected converted + 120000)")

    # CHECK 8: pipeline_report.txt exists and contains expected content
    report_files = list(workspace_path.rglob("pipeline_report.txt"))
    if not report_files:
        add_check("pipeline_report_exists", False, "pipeline_report.txt not found anywhere in workspace")
        add_check("pipeline_report_content", False, "Cannot check content — file missing")
    else:
        report_file = report_files[0]
        add_check("pipeline_report_exists", True, f"Found pipeline_report.txt at {report_file}")
        try:
            content = report_file.read_text()
            # Must contain "Pipeline Report" and current month
            import datetime
            current_month = datetime.datetime.now().strftime("%Y-%m")
            has_header = "Pipeline Report" in content or "pipeline" in content.lower()
            has_month = current_month in content
            has_converted = "converted" in content.lower()
            has_total = "total" in content.lower() or "Total" in content
            has_value = "320000" in content or "320000.00" in content  # Bob(120k) + Eve(200k)

            content_ok = has_header and has_month and has_converted and has_total
            detail = (f"has_header={has_header}, has_month={has_month}, "
                      f"has_converted={has_converted}, has_total={has_total}, "
                      f"has_deal_value={has_value}; content[:300]={content[:300]!r}")
            add_check("pipeline_report_content", content_ok, detail)

            # Bonus: deal value correctness
            add_check("pipeline_report_deal_value", has_value,
                      f"Total deal value 320000 (Bob+Eve) present: {has_value}")
        except Exception as e:
            add_check("pipeline_report_content", False, f"Error reading pipeline_report.txt: {e}")
            add_check("pipeline_report_deal_value", False, "Could not read file")

    # --- Scoring ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall = score >= 0.80

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))