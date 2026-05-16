#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def main(workspace_dir):
    checks = []
    queue_dir = Path("/root/.openclaw/workspace/skills/lel-mail/queue")

    # -----------------------------------------------------------------------
    # Check 1: The stale "TEST - ignore this" email has been deleted
    # -----------------------------------------------------------------------
    stale_id = "a3f9b1c2"
    stale_deleted = True
    stale_detail = ""
    try:
        stale_file = queue_dir / f"{stale_id}.json"
        # Check by filename
        if stale_file.exists():
            stale_deleted = False
            stale_detail = f"Stale email file {stale_id}.json still exists in queue."
        else:
            # Also double-check by scanning all files for subject
            for f in queue_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    if data.get("subject", "").strip().upper() == "TEST - IGNORE THIS":
                        stale_deleted = False
                        stale_detail = f"Stale email still found in queue under file {f.name}."
                        break
                except Exception:
                    pass
            if stale_deleted:
                stale_detail = "Stale 'TEST - ignore this' email correctly removed from queue."
    except Exception as e:
        stale_deleted = False
        stale_detail = f"Exception checking stale email: {e}"

    checks.append({
        "name": "stale_email_deleted",
        "passed": stale_deleted,
        "detail": stale_detail
    })

    # -----------------------------------------------------------------------
    # Check 2: The legitimate "Monthly Ops Review" email is still in queue
    # -----------------------------------------------------------------------
    legit_id = "d7e2a0f4"
    legit_present = False
    legit_detail = ""
    try:
        legit_file = queue_dir / f"{legit_id}.json"
        if legit_file.exists():
            legit_present = True
            legit_detail = "Legitimate 'Monthly Ops Review' email correctly preserved in queue."
        else:
            # Search by subject as fallback
            for f in queue_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text())
                    if "Monthly Ops Review" in data.get("subject", ""):
                        legit_present = True
                        legit_detail = "Legitimate 'Monthly Ops Review' email found (under different filename) in queue."
                        break
                except Exception:
                    pass
            if not legit_present:
                legit_detail = "Legitimate 'Monthly Ops Review' email was incorrectly removed from queue."
    except Exception as e:
        legit_present = False
        legit_detail = f"Exception checking legit email: {e}"

    checks.append({
        "name": "legitimate_email_preserved",
        "passed": legit_present,
        "detail": legit_detail
    })

    # -----------------------------------------------------------------------
    # Check 3: New regulatory notification email was queued
    # -----------------------------------------------------------------------
    new_email_found = False
    new_email_detail = ""
    new_email_data = None
    try:
        for f in queue_dir.glob("*.json"):
            if f.stem in (stale_id, legit_id):
                continue
            try:
                data = json.loads(f.read_text())
                subj = data.get("subject", "")
                recipient = data.get("recipient", "")
                sender = data.get("sender", "")
                if (
                    "Q4 2024 Regulatory Compliance Notification" in subj and
                    "regulators@finra.org" in recipient and
                    "compliance@fincorp.com" in sender
                ):
                    new_email_found = True
                    new_email_data = data
                    new_email_detail = f"New regulatory email queued with ID {data.get('id','?')}."
                    break
            except Exception:
                pass
        if not new_email_found:
            # Looser search
            for f in queue_dir.glob("*.json"):
                if f.stem in (stale_id, legit_id):
                    continue
                try:
                    data = json.loads(f.read_text())
                    subj = data.get("subject", "").lower()
                    if "regulatory" in subj or "q4" in subj or "compliance notification" in subj:
                        new_email_found = True
                        new_email_data = data
                        new_email_detail = f"New regulatory-like email queued (subject: {data.get('subject','?')}) — partial match."
                        break
                except Exception:
                    pass
        if not new_email_found:
            new_email_detail = "No new regulatory notification email found in queue."
    except Exception as e:
        new_email_found = False
        new_email_detail = f"Exception scanning for new email: {e}"

    checks.append({
        "name": "new_regulatory_email_queued",
        "passed": new_email_found,
        "detail": new_email_detail
    })

    # -----------------------------------------------------------------------
    # Check 4: BCC field contains BOTH legal@fincorp.com and audit@fincorp.com
    # (comma-separated, as required by SKILL.md)
    # -----------------------------------------------------------------------
    bcc_correct = False
    bcc_detail = ""
    if new_email_data:
        try:
            bcc_raw = new_email_data.get("bcc", "")
            # Normalize: split by comma, strip whitespace
            bcc_entries = [x.strip().lower() for x in bcc_raw.split(",") if x.strip()]
            has_legal = "legal@fincorp.com" in bcc_entries
            has_audit = "audit@fincorp.com" in bcc_entries
            if has_legal and has_audit:
                bcc_correct = True
                bcc_detail = f"BCC correctly contains both legal@fincorp.com and audit@fincorp.com as comma-separated list. Raw value: '{bcc_raw}'"
            else:
                missing = []
                if not has_legal:
                    missing.append("legal@fincorp.com")
                if not has_audit:
                    missing.append("audit@fincorp.com")
                bcc_detail = f"BCC field missing: {missing}. Raw BCC value was: '{bcc_raw}'"
        except Exception as e:
            bcc_correct = False
            bcc_detail = f"Exception checking BCC: {e}"
    else:
        bcc_detail = "Cannot check BCC — new email not found."

    checks.append({
        "name": "bcc_comma_separated_correct",
        "passed": bcc_correct,
        "detail": bcc_detail
    })

    # -----------------------------------------------------------------------
    # Check 5: Body of new email is substantively correct
    # -----------------------------------------------------------------------
    body_correct = False
    body_detail = ""
    if new_email_data:
        try:
            body = new_email_data.get("body", "")
            # Check for key phrases
            if (
                "Q4 2024" in body or "q4 2024" in body.lower()
            ) and (
                "compliance" in body.lower()
            ):
                body_correct = True
                body_detail = f"Email body contains expected content references."
            else:
                body_detail = f"Email body does not appear to contain required Q4 2024 compliance content. Body: '{body[:200]}'"
        except Exception as e:
            body_correct = False
            body_detail = f"Exception checking body: {e}"
    else:
        body_detail = "Cannot check body — new email not found."

    checks.append({
        "name": "email_body_correct",
        "passed": body_correct,
        "detail": body_detail
    })

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------
    # Weights: delete stale (25%), preserve legit (20%), new email queued (25%), 
    #          bcc format (20%), body correct (10%)
    weights = [0.25, 0.20, 0.25, 0.20, 0.10]
    score = sum(w for w, c in zip(weights, checks) if c["passed"])
    passed = score >= 0.85  # Must pass all major checks

    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/root/workspace"
    main(workspace)