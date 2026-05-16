#!/usr/bin/env python3
"""
Evaluation script for the outreach sequencer task.
Checks:
1. campaign_report.json exists and has correct analytics structure
2. Exactly the right leads were processed (5 due, not 7 or 8)
3. LinkedIn messages are under 300 chars
4. Email bodies are under 150 words
5. No generic openers ("I hope this finds you well", etc.)
6. Same-company leads (Marcus Webb + Priya Sharma) have different messages
7. C-suite vs IC tone distinction
8. DuckDB status correctly updated (Sequence Step advanced, Next Outreach set, Outreach Status = 'Sent')
9. Opted Out lead (id=8) was NOT touched
10. Future-due lead (id=7) was NOT processed
"""

import sys
import json
import re
from pathlib import Path
from datetime import date, timedelta

try:
    import duckdb
except ImportError:
    print(json.dumps({
        "passed": False, "score": 0.0,
        "checks": [{"name": "imports", "passed": False, "detail": "duckdb not installed"}]
    }))
    sys.exit(0)

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
today = date.today()

checks = []

def add_check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

# ── Load DuckDB state ──────────────────────────────────────────────────────
db_path = Path(workspace) / "crm" / "leads.db"
try:
    con = duckdb.connect(str(db_path))
    all_leads = con.execute("SELECT * FROM leads").fetchdf()
    con.close()
    db_ok = True
except Exception as e:
    db_ok = False
    add_check("db_readable", False, f"Could not read DuckDB: {e}")

if not db_ok:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

add_check("db_readable", True, "DuckDB loaded successfully")

# Helper: get lead row by id
def lead(lid):
    row = all_leads[all_leads['id'] == lid]
    if row.empty:
        return None
    return row.iloc[0]

# ── Check 1: campaign_report.json exists ──────────────────────────────────
report_files = list(Path(workspace).rglob("campaign_report.json"))
if not report_files:
    add_check("campaign_report_exists", False, "campaign_report.json not found anywhere in workspace")
    report = None
else:
    add_check("campaign_report_exists", True, f"Found at {report_files[0]}")
    try:
        report = json.loads(report_files[0].read_text())
    except Exception as e:
        add_check("campaign_report_parseable", False, f"JSON parse error: {e}")
        report = None

if report is not None:
    add_check("campaign_report_parseable", True, "Valid JSON")

# ── Check 2: Report contains analytics fields ──────────────────────────────
if report is not None:
    required_keys = {"total_processed", "sent_count"}
    has_keys = required_keys.issubset(set(k.lower().replace(" ", "_") for k in report.keys())) or \
               required_keys.issubset(set(report.keys()))
    # Be flexible — check for any analytics-like structure
    has_structure = (
        isinstance(report, dict) and
        any(k in str(report).lower() for k in ["sent", "processed", "total", "step"])
    )
    add_check("report_has_analytics_structure", has_structure,
              f"Keys found: {list(report.keys())[:10]}")

    # Check that 5 leads were processed (ids 1,2,3,4,5,6 — but id 7 not due, id 8 opted out)
    # We expect 5 due leads: 1,2,3,4,5,6 minus id7(future) minus id8(opted out) = 6 leads due
    # Actually: ids 1,2,3 (Queued, due today) + ids 4,5,6 (Sent, overdue) = 6 due leads
    count_in_report = None
    for k, v in report.items():
        if "processed" in k.lower() or "total" in k.lower() or "sent" in k.lower():
            try:
                n = int(v)
                if 4 <= n <= 6:
                    count_in_report = n
                    break
            except:
                pass
    add_check("report_correct_lead_count", count_in_report is not None,
              f"Expected ~6 leads processed, report suggests: {count_in_report}")

# ── Check 3: Opted Out lead (id=8) untouched ─────────────────────────────
l8 = lead(8)
if l8 is not None:
    opted_out_status = l8["Outreach Status"] == "Opted Out"
    opted_out_msg = l8["generated_message"] is None or str(l8["generated_message"]).strip() == ""
    add_check("opted_out_lead_not_contacted",
              opted_out_status and opted_out_msg,
              f"id=8 status='{l8['Outreach Status']}', generated_message='{l8['generated_message']}'")
else:
    add_check("opted_out_lead_not_contacted", False, "Lead id=8 missing from DB")

# ── Check 4: Future-due lead (id=7) not processed ─────────────────────────
l7 = lead(7)
if l7 is not None:
    future_untouched = (
        l7["Sequence Step"] == 1 and
        (l7["generated_message"] is None or str(l7["generated_message"]).strip() == "")
    )
    add_check("future_lead_not_processed", future_untouched,
              f"id=7 step={l7['Sequence Step']}, msg='{l7['generated_message']}'")
else:
    add_check("future_lead_not_processed", False, "Lead id=7 missing from DB")

# ── Check 5: Status advancement for due leads ─────────────────────────────
# id=1,2,3 were Queued Step 0 → should now be Sent, Step 1
step1_advances = []
for lid in [1, 2, 3]:
    l = lead(lid)
    if l is not None:
        advanced = (
            str(l["Outreach Status"]) == "Sent" and
            int(l["Sequence Step"]) == 1
        )
        step1_advances.append(advanced)
        add_check(f"lead_{lid}_advanced_to_step1",
                  advanced,
                  f"Status={l['Outreach Status']}, Step={l['Sequence Step']}")
    else:
        add_check(f"lead_{lid}_advanced_to_step1", False, f"Lead {lid} not found")

# id=4 was Step 1 → should be Step 2
l4 = lead(4)
if l4 is not None:
    l4_ok = int(l4["Sequence Step"]) == 2
    add_check("lead_4_advanced_to_step2", l4_ok,
              f"Step={l4['Sequence Step']}")
else:
    add_check("lead_4_advanced_to_step2", False, "Lead 4 not found")

# id=5 was Step 2 → should be Step 3
l5 = lead(5)
if l5 is not None:
    l5_ok = int(l5["Sequence Step"]) == 3
    add_check("lead_5_advanced_to_step3", l5_ok,
              f"Step={l5['Sequence Step']}")
else:
    add_check("lead_5_advanced_to_step3", False, "Lead 5 not found")

# id=6 was Step 3 → should be Step 4
l6 = lead(6)
if l6 is not None:
    l6_ok = int(l6["Sequence Step"]) == 4
    add_check("lead_6_advanced_to_step4", l6_ok,
              f"Step={l6['Sequence Step']}")
else:
    add_check("lead_6_advanced_to_step4", False, "Lead 6 not found")

# ── Check 6: Next Outreach dates correctly set per template ───────────────
# Template 2 (Cold Email): Day 0→3→7→14; after step1 set next=today+3, step2→today+4(=7-3), etc.
# More precisely: step1 sent today → next = today+3
# step2 sent today → next = today+4 (day7-day3=4 days later)
# step3 sent today → next = today+7 (day14-day7=7 days later)
# Check id=4 (just did step2 follow-up, was at step1): next should be today+4
l4 = lead(4)
if l4 is not None and l4["Next Outreach"] is not None:
    try:
        next_date = l4["Next Outreach"]
        if hasattr(next_date, 'date'):
            next_date = next_date.date()
        elif isinstance(next_date, str):
            from datetime import datetime
            next_date = datetime.strptime(next_date, "%Y-%m-%d").date()
        # Accept today+3 to today+5 as valid (Day 7 - Day 3 = 4, but today+3 is minimum)
        days_ahead = (next_date - today).days
        date_ok = 3 <= days_ahead <= 5
        add_check("lead_4_next_outreach_date_correct",
                  date_ok,
                  f"Next Outreach: {next_date}, days ahead: {days_ahead} (expected 3-5)")
    except Exception as e:
        add_check("lead_4_next_outreach_date_correct", False, f"Date parse error: {e}")
else:
    add_check("lead_4_next_outreach_date_correct", False,
              f"id=4 Next Outreach not set: {l4['Next Outreach'] if l4 is not None else 'lead missing'}")

# ── Check 7: Messages generated and stored ────────────────────────────────
messages_generated = []
for lid in [1, 2, 3, 4, 5, 6]:
    l = lead(lid)
    if l is not None:
        has_msg = (l["generated_message"] is not None and
                   len(str(l["generated_message"]).strip()) > 10)
        messages_generated.append((lid, has_msg, str(l.get("generated_message", ""))))

gen_count = sum(1 for _, ok, _ in messages_generated if ok)
add_check("messages_generated_in_db",
          gen_count >= 5,
          f"{gen_count}/6 due leads have generated_message in DB")

# ── Check 8: LinkedIn messages under 300 chars ───────────────────────────
GENERIC_OPENERS = [
    "i hope this finds you well",
    "hope this email finds you",
    "i hope you are doing well",
    "hope you're doing well",
    "i wanted to reach out",
    "just wanted to follow up",
]

linkedin_leads = [1, 2]  # Marcus and Priya use LinkedIn channel
linkedin_violations = []
for lid in linkedin_leads:
    l = lead(lid)
    if l is not None and l["generated_message"]:
        msg = str(l["generated_message"])
        if len(msg) > 300:
            linkedin_violations.append(f"id={lid}: {len(msg)} chars")

add_check("linkedin_messages_under_300_chars",
          len(linkedin_violations) == 0,
          f"Violations: {linkedin_violations}" if linkedin_violations else "All LinkedIn msgs ≤300 chars")

# ── Check 9: Email bodies under 150 words ─────────────────────────────────
email_leads = [3, 4, 5, 6]  # Email channel leads
email_violations = []
for lid in email_leads:
    l = lead(lid)
    if l is not None and l["generated_message"]:
        msg = str(l["generated_message"])
        word_count = len(msg.split())
        if word_count > 150:
            email_violations.append(f"id={lid}: {word_count} words")

add_check("email_messages_under_150_words",
          len(email_violations) == 0,
          f"Violations: {email_violations}" if email_violations else "All email msgs ≤150 words")

# ── Check 10: No generic openers ─────────────────────────────────────────
generic_violations = []
for lid in [1, 2, 3, 4, 5, 6]:
    l = lead(lid)
    if l is not None and l["generated_message"]:
        msg = str(l["generated_message"]).lower()
        for opener in GENERIC_OPENERS:
            if opener in msg:
                generic_violations.append(f"id={lid}: contains '{opener}'")
                break

add_check("no_generic_openers",
          len(generic_violations) == 0,
          f"Violations: {generic_violations}" if generic_violations else "No generic openers found")

# ── Check 11: Same-company leads have different messages ──────────────────
l1 = lead(1)
l2 = lead(2)
if l1 is not None and l2 is not None and l1["generated_message"] and l2["generated_message"]:
    msg1 = str(l1["generated_message"]).strip().lower()
    msg2 = str(l2["generated_message"]).strip().lower()

    # Check messages are not identical
    not_identical = msg1 != msg2

    # Check they have meaningful differences (Jaccard similarity < 0.7)
    def word_set(text):
        return set(re.findall(r'\b\w+\b', text.lower()))
    ws1, ws2 = word_set(msg1), word_set(msg2)
    union = ws1 | ws2
    intersection = ws1 & ws2
    jaccard = len(intersection) / len(union) if union else 1.0

    different_enough = jaccard < 0.7

    add_check("same_company_leads_have_different_messages",
              not_identical and different_enough,
              f"Messages identical: {not_identical==False}, Jaccard similarity: {jaccard:.2f} (must be <0.70)")
else:
    add_check("same_company_leads_have_different_messages", False,
              f"Could not compare: l1_msg={l1['generated_message'] if l1 else 'missing'}, l2_msg={l2['generated_message'] if l2 else 'missing'}")

# ── Check 12: C-suite vs IC tone (strategic vs technical language) ─────────
# Marcus (CTO, id=1) and Nathaniel (CEO, id=5) vs Priya (Staff Eng, id=2) and Sofia (Sr SWE, id=4)
STRATEGIC_WORDS = {"scale", "scaling", "revenue", "growth", "roi", "business", "strategic",
                   "leadership", "org", "team", "velocity", "roadmap", "invest", "competitive",
                   "efficiency", "cost", "results", "outcomes", "portfolio", "budget"}
TECHNICAL_WORDS = {"deploy", "stack", "integration", "api", "pipeline", "debug", "latency",
                   "kubernetes", "k8s", "rust", "microservice", "profil", "observab",
                   "toolchain", "open-source", "distributed", "performance", "engineer"}

tone_checks_passed = 0
tone_total = 0

for lid, seniority in [(1, "csuite"), (5, "csuite"), (2, "ic"), (4, "ic")]:
    l = lead(lid)
    if l is not None and l["generated_message"]:
        msg_words = set(re.findall(r'\b\w+\b', str(l["generated_message"]).lower()))
        if seniority == "csuite":
            # C-suite: should have more strategic than technical markers
            strat_count = len(msg_words & STRATEGIC_WORDS)
            tech_count = sum(1 for tw in TECHNICAL_WORDS if tw in str(l["generated_message"]).lower())
            # Relaxed: just verify at least one strategic word present
            tone_ok = strat_count >= 1
        else:
            # IC: should have at least one technical marker
            tech_count = sum(1 for tw in TECHNICAL_WORDS if tw in str(l["generated_message"]).lower())
            tone_ok = tech_count >= 1
        if tone_ok:
            tone_checks_passed += 1
        tone_total += 1

add_check("tone_matches_seniority",
          tone_total > 0 and tone_checks_passed >= (tone_total // 2 + 1),
          f"{tone_checks_passed}/{tone_total} leads have appropriate seniority tone")

# ── Check 13: Personalization hooks referenced in messages ────────────────
personalization_checks = 0
for lid, hook_field in [(1, "trigger"), (2, "trigger"), (3, "mutual"), (4, "mutual"), (5, "trigger"), (6, "trigger")]:
    l = lead(lid)
    if l is not None and l["generated_message"] and l.get(hook_field):
        hook_value = str(l[hook_field]).lower()
        # Check if any significant word from the hook appears in the message
        hook_words = [w for w in hook_value.split() if len(w) > 4]
        msg_lower = str(l["generated_message"]).lower()
        if any(w in msg_lower for w in hook_words):
            personalization_checks += 1

add_check("messages_reference_personalization_hooks",
          personalization_checks >= 3,
          f"{personalization_checks}/6 messages reference their personalization hook")

# ── Scoring ────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
overall_passed = score >= 0.75

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, indent=2))