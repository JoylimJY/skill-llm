import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

workspace = sys.argv[1]

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# --- Locate the output file ---
report_files = list(Path(workspace).rglob("campaign_readiness_report.json"))
if not report_files:
    print(json.dumps({
        "passed": False, "score": 0.0,
        "checks": [make_check("file_exists", False, "campaign_readiness_report.json not found anywhere in workspace")]
    }))
    sys.exit(0)

report_path = report_files[0]
checks.append(make_check("file_exists", True, f"Found at {report_path}"))

try:
    with open(report_path) as f:
        report = json.load(f)
except Exception as e:
    checks.append(make_check("valid_json", False, f"Failed to parse JSON: {e}"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

checks.append(make_check("valid_json", True, "JSON parsed successfully"))

# ========================================================================
# SECTION 1: List Health Audit
# ========================================================================
# Expected metrics from generated data:
# Total sent = 380+550+572+90+18+5+25 = 1640 who had emails_sent=1, plus 80 new with emails_sent=0
# Active emails sent: all rows with emails_sent=1
# emails_sent=1: engaged(380) + warm(550) + cold(572) + bounced(90) + unsub(18) + complaint(5) + VIP(25) = 1640
# Bounce rate: 90/1640 = 5.49% -> CRITICAL (>5%)
# Unsubscribe rate: 18/1640 = 1.10% -> CRITICAL (>1%)
# Spam complaint rate: 5/1640 = 0.305% -> CRITICAL (>0.3%)
# Open rate: 380 opened / 1640 sent = 23.17% -> HEALTHY (>20%)  [but VIP 25 also opened = 405/1640=24.7%]
# Actually VIP customers also opened (25 more), so opens = 380 engaged with opens + 25 VIP = but the 80 from engaged already include is_customer=true
# Let me recount: engaged_count=380 (of which 80 are customers), VIP=25 (additional customers who opened)
# Total openers from sent = 380 + 25 = 405 (those with last_opened_date within 30 days AND emails_sent=1)
# Open rate: 405/1640 = 24.7% -> HEALTHY
# Click rate: 36 (tagged clicked in engaged) + 25 VIP = 61/1640 = 3.72% -> HEALTHY
# 
# We accept some tolerance since agents parse the CSV themselves.
# Key assertions:
# - bounce rate classified as WARNING or CRITICAL (>2%)  — specifically CRITICAL since 90/1640 ≈ 5.49%
# - unsubscribe rate classified as WARNING or CRITICAL (>0.5%) — specifically CRITICAL since >1%
# - spam complaint rate classified as WARNING or CRITICAL (>0.1%) — specifically CRITICAL since >0.3%

health_section = None
for key in ["list_health", "health_audit", "campaign_health", "health", "metrics"]:
    if key in report:
        health_section = report[key]
        break
if health_section is None:
    # Try top-level keys
    for k, v in report.items():
        if isinstance(v, dict) and any(m in str(v).lower() for m in ["bounce", "open_rate", "unsubscribe"]):
            health_section = v
            break

if health_section is None:
    checks.append(make_check("health_section_present", False, "No list health / metrics section found in report"))
else:
    checks.append(make_check("health_section_present", True, f"Health section found under key"))

    # Check bounce rate status
    bounce_status_found = False
    bounce_correct = False
    report_str = json.dumps(health_section).lower()
    
    # Look for bounce rate value and status
    bounce_matches = re.findall(r'bounce[^"]*[:\s]+([0-9.]+)', report_str)
    if bounce_matches:
        for bm in bounce_matches:
            try:
                val = float(bm)
                if val > 2.0:  # Either as percentage >2 or as decimal >0.02
                    bounce_status_found = True
                    break
                elif val > 0.02:  # decimal form
                    bounce_status_found = True
                    break
            except:
                pass
    
    # Check for "critical" or "warning" label near bounce
    if "critical" in report_str and "bounce" in report_str:
        bounce_correct = True
    elif "warning" in report_str and "bounce" in report_str:
        bounce_correct = True  # warning is also acceptable — bounce is 5.49% which is CRITICAL
    
    # More precise: check that bounce is labeled critical (5.49% > 5%)
    bounce_critical = "critical" in report_str and "bounce" in report_str
    checks.append(make_check(
        "bounce_rate_critical",
        bounce_critical,
        f"Bounce rate ~5.49% should be CRITICAL (>5%). Report content: {report_str[:300]}"
    ))
    
    # Check spam complaint status — 0.305% is CRITICAL (>0.3%)
    spam_critical = ("critical" in report_str and "spam" in report_str)
    spam_warning = ("warning" in report_str and "spam" in report_str)
    checks.append(make_check(
        "spam_complaint_warning_or_critical",
        spam_critical or spam_warning,
        f"Spam complaint rate ~0.3% should be WARNING or CRITICAL. Found critical={spam_critical}, warning={spam_warning}"
    ))
    
    # Check unsubscribe status — 1.1% is CRITICAL (>1%)
    unsub_critical = ("critical" in report_str and ("unsub" in report_str or "unsubscribe" in report_str))
    unsub_warning = ("warning" in report_str and ("unsub" in report_str or "unsubscribe" in report_str))
    checks.append(make_check(
        "unsubscribe_rate_critical",
        unsub_critical or unsub_warning,
        f"Unsubscribe rate ~1.1% should be CRITICAL (>1%). Found critical={unsub_critical}, warning={unsub_warning}"
    ))

# ========================================================================
# SECTION 2: Segmentation
# ========================================================================
# Expected segments per SKILL.md minimum viable segments:
# - new_subscribers: subscribed within ~7 days, ~80 records
# - engaged: opened within 30 days, ~405 records  
# - unengaged (sunset candidates): last opened > 90 days, ~572 records
# - customers: is_customer=true (80+25=105 total, but ~105 active customers)
# - VIP: highest engagement (customers who opened recently)

segments_section = None
for key in ["segments", "segmentation", "subscriber_segments", "list_segments"]:
    if key in report:
        segments_section = report[key]
        break
if segments_section is None:
    for k, v in report.items():
        if isinstance(v, (dict, list)) and any(s in str(v).lower() for s in ["new_sub", "engaged", "vip", "unengaged", "customer"]):
            segments_section = v
            break

if segments_section is None:
    checks.append(make_check("segments_section_present", False, "No segmentation section found in report"))
else:
    checks.append(make_check("segments_section_present", True, "Segmentation section found"))
    
    seg_str = json.dumps(segments_section).lower()
    
    # Check for the 4 minimum viable segments from SKILL.md
    has_new = any(t in seg_str for t in ["new_sub", "new subscriber", "new sign", "new_signup", "new-sub"])
    has_engaged = "engaged" in seg_str
    has_unengaged = any(t in seg_str for t in ["unengaged", "un-engaged", "inactive", "sunset", "cold"])
    has_customers = "customer" in seg_str
    has_vip = "vip" in seg_str
    
    checks.append(make_check("segment_new_subscribers", has_new, f"'new subscribers' segment found: {has_new}"))
    checks.append(make_check("segment_engaged", has_engaged, f"'engaged' segment found: {has_engaged}"))
    checks.append(make_check("segment_unengaged_sunset", has_unengaged, f"'unengaged/sunset' segment found: {has_unengaged}"))
    checks.append(make_check("segment_customers", has_customers, f"'customers' segment found: {has_customers}"))
    checks.append(make_check("segment_vip", has_vip, f"'VIP' segment found: {has_vip}"))
    
    # Check segment counts are roughly correct
    # New subscribers: should be ~80 (±20)
    new_count_match = re.search(r'new[_\s-]sub[^"]*[^0-9]([6-9][0-9]|1[0-2][0-9])', seg_str)
    # Engaged: should be ~380-420
    engaged_count_match = re.search(r'engaged[^"]*[^0-9](3[5-9][0-9]|4[0-9][0-9])', seg_str)
    # Unengaged/sunset: should be ~550-600
    unengaged_count_match = re.search(r'(unengaged|sunset|cold|inactive)[^"]*[^0-9](5[0-9][0-9]|6[0-9][0-9])', seg_str)
    
    checks.append(make_check(
        "segment_new_count_reasonable",
        bool(new_count_match) or any(f'"{n}"' in seg_str or f': {n}' in seg_str for n in range(60, 105)),
        f"New subscriber count should be ~80. Match found: {bool(new_count_match)}"
    ))

# ========================================================================
# SECTION 3: Welcome Sequence Schedule
# ========================================================================
# Per SKILL.md: 5-7 emails over 2 weeks
# Day schedule: 0 (immediate), 1, 3, 5, 7, 10, 14
# Subject lines: 40-50 chars optimal, no spam triggers

sequence_section = None
for key in ["welcome_sequence", "sequence", "onboarding_sequence", "email_sequence", "welcome_schedule"]:
    if key in report:
        sequence_section = report[key]
        break
if sequence_section is None:
    for k, v in report.items():
        if isinstance(v, list) and len(v) >= 5:
            sequence_section = v
            break
        elif isinstance(v, dict) and any(s in str(v).lower() for s in ["day 0", "day 1", "day 3", "day 7", "day 14", "immediate"]):
            sequence_section = v
            break

if sequence_section is None:
    checks.append(make_check("welcome_sequence_present", False, "No welcome sequence section found"))
else:
    checks.append(make_check("welcome_sequence_present", True, "Welcome sequence section found"))
    
    seq_str = json.dumps(sequence_section).lower()
    
    # Check for correct number of emails: 5-7
    emails_in_seq = []
    if isinstance(sequence_section, list):
        emails_in_seq = sequence_section
    elif isinstance(sequence_section, dict):
        for v in sequence_section.values():
            if isinstance(v, list):
                emails_in_seq = v
                break
    
    seq_count = len(emails_in_seq) if emails_in_seq else seq_str.count('"day')
    email_count_ok = 5 <= seq_count <= 7
    checks.append(make_check(
        "sequence_email_count_5_to_7",
        email_count_ok,
        f"Welcome sequence should have 5-7 emails. Found ~{seq_count}"
    ))
    
    # Check for correct day schedule from SKILL.md: 0, 1, 3, 5, 7, 10, 14
    required_days = [0, 1, 3, 5, 7, 10, 14]
    days_found = []
    for day in required_days:
        pattern = rf'\bday[_\s:]*{day}\b|"day"[:\s]*{day}|\bday {day}\b|"send_day"[:\s]*{day}|"day_number"[:\s]*{day}'
        if re.search(pattern, seq_str):
            days_found.append(day)
    
    # Must have at least day 0 (or immediate), day 1, day 7, day 14
    critical_days = {0, 1, 7, 14}
    # Also check for "immediate" as day 0 alternative
    has_immediate = "immediate" in seq_str or "day 0" in seq_str or "day_0" in seq_str or '"day": 0' in seq_str
    
    days_found_set = set(days_found)
    if has_immediate and 0 not in days_found_set:
        days_found_set.add(0)
    
    critical_found = critical_days.intersection(days_found_set)
    checks.append(make_check(
        "sequence_day_0_immediate",
        has_immediate or 0 in days_found_set,
        f"First email should be immediate/day 0. Found: {has_immediate}"
    ))
    checks.append(make_check(
        "sequence_day_14_present",
        14 in days_found_set or "day 14" in seq_str or "day_14" in seq_str,
        f"Day 14 email required (clear CTA). Days found: {sorted(days_found_set)}"
    ))
    checks.append(make_check(
        "sequence_spacing_correct",
        len(days_found_set) >= 4,
        f"At least 4 of the SKILL.md days (0,1,3,5,7,10,14) should appear. Found: {sorted(days_found_set)}"
    ))
    
    # Check subject line lengths (40-50 chars)
    subjects = re.findall(r'"subject"[:\s]+"([^"]{10,80})"', json.dumps(sequence_section))
    if not subjects:
        subjects = re.findall(r'"subject_line"[:\s]+"([^"]{10,80})"', json.dumps(sequence_section))
    
    if subjects:
        valid_length_count = sum(1 for s in subjects if 40 <= len(s) <= 50)
        # At least half should be in the 40-50 range
        subject_length_ok = valid_length_count >= len(subjects) // 2
        checks.append(make_check(
            "subject_line_length_40_50_chars",
            subject_length_ok,
            f"Subject lines should be 40-50 chars. {valid_length_count}/{len(subjects)} within range. Subjects: {subjects}"
        ))
        
        # Check for spam trigger words
        spam_triggers = ["free", "act now", "!!!", "all caps subject"]
        spam_found = []
        for s in subjects:
            for trigger in spam_triggers:
                if trigger in s.lower():
                    spam_found.append((s, trigger))
            if s == s.upper() and len(s) > 5:  # ALL CAPS
                spam_found.append((s, "ALL CAPS"))
        
        checks.append(make_check(
            "subject_lines_no_spam_triggers",
            len(spam_found) == 0,
            f"Spam triggers found in subjects: {spam_found}" if spam_found else "No spam triggers detected"
        ))
    else:
        checks.append(make_check("subject_lines_present", False, "No subject lines found in sequence"))

# ========================================================================
# SCORING
# ========================================================================
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall_passed = score >= 0.70

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, indent=2))