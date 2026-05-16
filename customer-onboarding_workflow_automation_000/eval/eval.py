import sys
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []

    # =========================================================
    # FILE 1: onboarding_checklist.md (or .txt)
    # =========================================================
    checklist_file = find_file(workspace, "onboarding_checklist.md") or find_file(workspace, "onboarding_checklist.txt")
    
    if not checklist_file:
        checks.append(check("Checklist file exists", False, "onboarding_checklist.md/.txt not found anywhere in workspace"))
        checklist_content = ""
    else:
        try:
            checklist_content = checklist_file.read_text(encoding="utf-8")
            checks.append(check("Checklist file exists", True, f"Found at {checklist_file}"))
        except Exception as e:
            checks.append(check("Checklist file exists", False, f"Error reading file: {e}"))
            checklist_content = ""

    # Check checkbox format (must have - [ ] style)
    checkbox_pattern = re.findall(r'- \[[ xX]\]', checklist_content)
    checks.append(check(
        "Checklist uses checkbox format",
        len(checkbox_pattern) >= 10,
        f"Found {len(checkbox_pattern)} checkbox items (need >=10 '- [ ]' or '- [x]' entries)"
    ))

    # Check all 5 required phases present
    phases = {
        "Pre-onboarding": bool(re.search(r'pre.?onboard|before kick.?off|prep', checklist_content, re.IGNORECASE)),
        "Day 1": bool(re.search(r'day\s*1\b', checklist_content, re.IGNORECASE)),
        "Week 1": bool(re.search(r'week\s*1\b', checklist_content, re.IGNORECASE)),
        "Week 2-4": bool(re.search(r'week\s*[2-4]|week\s*2.*(through|to|-)\s*4', checklist_content, re.IGNORECASE)),
        "Day 30/60/90": bool(re.search(r'day\s*(30|sixty|ninety)|30.*day|60.*day|90.*day', checklist_content, re.IGNORECASE)),
    }
    for phase_name, present in phases.items():
        checks.append(check(
            f"Checklist phase: {phase_name}",
            present,
            f"Phase '{phase_name}' {'found' if present else 'NOT FOUND'} in checklist"
        ))

    # Check ownership field is present
    has_ownership = bool(re.search(r'owner|responsible|assigned|who:|csm|sarah|james|maria', checklist_content, re.IGNORECASE))
    checks.append(check(
        "Checklist includes ownership",
        has_ownership,
        "Ownership/responsible party mention found" if has_ownership else "No ownership info found in checklist"
    ))

    # Check deadlines present
    has_deadlines = bool(re.search(r'deadline|due|by day|within \d+|day \d+|week \d+', checklist_content, re.IGNORECASE))
    checks.append(check(
        "Checklist includes deadlines",
        has_deadlines,
        "Deadline/timing info found" if has_deadlines else "No deadline/timing info found in checklist"
    ))

    # Check client-specific content (Harrington & Associates / law firm context)
    has_client_context = bool(re.search(r'harrington|law firm|attorney|contractiq|legal|NDA|ms365|microsoft 365', checklist_content, re.IGNORECASE))
    checks.append(check(
        "Checklist is customized to Harrington/legal context",
        has_client_context,
        "Client-specific terms found" if has_client_context else "No client-specific customization found"
    ))

    # =========================================================
    # FILE 2: welcome_sequence.md (or .txt)
    # =========================================================
    welcome_file = find_file(workspace, "welcome_sequence.md") or find_file(workspace, "welcome_sequence.txt")

    if not welcome_file:
        checks.append(check("Welcome sequence file exists", False, "welcome_sequence.md/.txt not found anywhere in workspace"))
        welcome_content = ""
    else:
        try:
            welcome_content = welcome_file.read_text(encoding="utf-8")
            checks.append(check("Welcome sequence file exists", True, f"Found at {welcome_file}"))
        except Exception as e:
            checks.append(check("Welcome sequence file exists", False, f"Error reading: {e}"))
            welcome_content = ""

    # Must have all 6 emails
    email_triggers = {
        "Welcome (immediate/Day 0)": bool(re.search(r'welcome.*email|email\s*1|immediate|day\s*0', welcome_content, re.IGNORECASE)),
        "Getting started (Day 1)": bool(re.search(r'getting started|day\s*1|get started', welcome_content, re.IGNORECASE)),
        "Check-in (Day 3)": bool(re.search(r'day\s*3|check.?in', welcome_content, re.IGNORECASE)),
        "Tips (Day 7)": bool(re.search(r'day\s*7|tips|best practice', welcome_content, re.IGNORECASE)),
        "Milestone (Day 14)": bool(re.search(r'day\s*14|milestone|celebrat', welcome_content, re.IGNORECASE)),
        "Review/Feedback (Day 30)": bool(re.search(r'day\s*30|review|feedback|csat', welcome_content, re.IGNORECASE)),
    }
    for email_name, present in email_triggers.items():
        checks.append(check(
            f"Welcome sequence email: {email_name}",
            present,
            f"Email '{email_name}' {'found' if present else 'NOT FOUND'} in welcome sequence"
        ))

    # Emails must be ready-to-send (has subject line or greeting)
    has_email_structure = bool(re.search(r'subject:|dear|hi |hello |greetings', welcome_content, re.IGNORECASE))
    checks.append(check(
        "Welcome emails are ready-to-send (have structure)",
        has_email_structure,
        "Email structure (Subject/greeting) found" if has_email_structure else "Emails don't appear ready-to-send"
    ))

    # =========================================================
    # FILE 3: risk_report.md (or .txt)
    # =========================================================
    risk_file = find_file(workspace, "risk_report.md") or find_file(workspace, "risk_report.txt")

    if not risk_file:
        checks.append(check("Risk report file exists", False, "risk_report.md/.txt not found anywhere in workspace"))
        risk_content = ""
    else:
        try:
            risk_content = risk_file.read_text(encoding="utf-8")
            checks.append(check("Risk report file exists", True, f"Found at {risk_file}"))
        except Exception as e:
            checks.append(check("Risk report file exists", False, f"Error reading: {e}"))
            risk_content = ""

    # Must flag: missed milestones
    has_missed_milestones = bool(re.search(r'missed milestone|milestone.*missed|milestone.*not completed|overdue milestone', risk_content, re.IGNORECASE))
    checks.append(check(
        "Risk: Missed milestones flagged",
        has_missed_milestones,
        "Missed milestones risk found" if has_missed_milestones else "Missed milestones NOT flagged in risk report"
    ))

    # Must flag: low engagement / no logins
    has_low_engagement = bool(re.search(r'low engagement|no login|zero login|0 login|engagement.*low|inactive|no activity', risk_content, re.IGNORECASE))
    checks.append(check(
        "Risk: Low engagement signals flagged",
        has_low_engagement,
        "Low engagement risk found" if has_low_engagement else "Low engagement NOT flagged"
    ))

    # Must flag: delayed responses
    has_delayed_responses = bool(re.search(r'delayed response|slow response|response.*delay|unresponsive|no reply|voicemail', risk_content, re.IGNORECASE))
    checks.append(check(
        "Risk: Delayed responses flagged",
        has_delayed_responses,
        "Delayed response risk found" if has_delayed_responses else "Delayed responses NOT flagged"
    ))

    # Must flag: scope creep
    has_scope_creep = bool(re.search(r'scope creep|out of scope|scope.*expand|scope.*change|beyond.*scope|litigation hold|lease agreement.*not in scope', risk_content, re.IGNORECASE))
    checks.append(check(
        "Risk: Scope creep flagged",
        has_scope_creep,
        "Scope creep risk found" if has_scope_creep else "Scope creep NOT flagged"
    ))

    # Must flag: champion departure (Tom Yuen leaving)
    has_champion_departure = bool(re.search(r'champion.*depart|champion.*leav|champion.*exit|tom.*leav|leav.*tom|key.*contact.*leav|champion at risk', risk_content, re.IGNORECASE))
    checks.append(check(
        "Risk: Champion departure flagged",
        has_champion_departure,
        "Champion departure risk found" if has_champion_departure else "Champion departure (Tom Yuen) NOT flagged"
    ))

    # =========================================================
    # SCORING
    # =========================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.80

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))