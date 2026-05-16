import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    """Find the aight_entries output file anywhere in workspace."""
    candidates = list(Path(workspace).rglob("aight_entries.json"))
    if candidates:
        return candidates[0]
    return None

def check_id_format(item_id, expected_prefix):
    """Check that ID follows <type>-<slug>-<timestamp> with 2-4 word slug."""
    if not isinstance(item_id, str):
        return False, "ID is not a string"
    parts = item_id.split("-")
    if len(parts) < 3:
        return False, f"ID '{item_id}' has fewer than 3 dash-separated parts"
    # prefix must match expected type prefix
    if not item_id.startswith(expected_prefix + "-"):
        return False, f"ID '{item_id}' does not start with expected prefix '{expected_prefix}-'"
    # slug is middle part(s), last part is timestamp/hash
    # at least 2 slug words (so minimum parts: type + 2 slug words + timestamp = 4 parts)
    if len(parts) < 4:
        return False, f"ID '{item_id}' slug appears to have fewer than 2 words (parts: {parts})"
    return True, "OK"

def check_iso8601_timezone(dt_str):
    """Check that datetime has +08:00 timezone."""
    if not isinstance(dt_str, str):
        return False, "Not a string"
    # Must contain +08:00
    if "+08:00" not in dt_str:
        return False, f"Missing +08:00 timezone in '{dt_str}'"
    # Basic ISO 8601 pattern
    pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$'
    if not re.match(pattern, dt_str):
        return False, f"Does not match ISO 8601 format: '{dt_str}'"
    return True, "OK"

def run_checks(workspace):
    checks = []
    score_parts = []

    # --- Locate output file ---
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists (aight_entries.json)",
        "passed": file_exists,
        "detail": str(output_file) if file_exists else "aight_entries.json not found anywhere in workspace"
    })
    if not file_exists:
        # All remaining checks fail
        for name in [
            "valid_json_array",
            "all_7_entries_present",
            "reminder_accountant_is_trigger",
            "reminder_accountant_scheduledFor_correct",
            "reminder_accountant_id_format",
            "reminder_accountant_labels",
            "pr_review_openclaw_451_is_item",
            "pr_review_has_url",
            "pr_review_id_format",
            "pr_review_labels",
            "deadline_ssl_is_trigger",
            "deadline_ssl_scheduledFor_april15",
            "deadline_ssl_timezone",
            "deadline_ssl_id_format",
            "deadline_ssl_labels_finance_or_urgent",
            "task_investor_email_is_item",
            "task_investor_email_labels",
            "reminder_call_mom_is_trigger",
            "reminder_call_mom_scheduledFor",
            "reminder_call_mom_timezone",
            "deadline_vercel_billing_is_trigger",
            "deadline_vercel_billing_nextfriday",
            "deadline_vercel_billing_timezone",
            "track_issue_88_is_item",
            "track_issue_88_has_url",
            "track_issue_88_labels",
            "no_forbidden_status_on_new_items",
        ]:
            checks.append({"name": name, "passed": False, "detail": "File not found"})
        score = 1.0 / (len(checks))
        return checks, score

    # --- Load JSON ---
    try:
        with open(output_file) as f:
            data = json.load(f)
        valid_json = isinstance(data, list)
        checks.append({"name": "valid_json_array", "passed": valid_json, "detail": f"Parsed OK, is list: {valid_json}"})
    except Exception as e:
        checks.append({"name": "valid_json_array", "passed": False, "detail": f"JSON parse error: {e}"})
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return checks, score

    if not valid_json:
        score = sum(1 for c in checks if c["passed"]) / max(len(checks), 1)
        return checks, score

    entries = data

    # --- Check count ---
    count_ok = len(entries) >= 7
    checks.append({
        "name": "all_7_entries_present",
        "passed": count_ok,
        "detail": f"Found {len(entries)} entries, expected at least 7"
    })

    # Helper: find entry by matching text keywords
    def find_entry(keywords, entries):
        keywords_lower = [k.lower() for k in keywords]
        for e in entries:
            text = str(e.get("text", "") + " " + str(e.get("id", ""))).lower()
            if all(k in text for k in keywords_lower):
                return e
        return None

    # =====================================================================
    # 1. Reminder: ping accountant about Q1 tax — "end of day tomorrow"
    #    = 2026-03-23T23:59:59+08:00 (tomorrow from 2026-03-22)
    # =====================================================================
    acc = find_entry(["accountant"], entries) or find_entry(["tax"], entries) or find_entry(["q1"], entries)
    if acc is None:
        # try relaxed
        for e in entries:
            txt = str(e).lower()
            if "account" in txt or ("tax" in txt and "ssl" not in txt and "vercel" not in txt):
                acc = e
                break

    acc_is_trigger = acc is not None and acc.get("type") == "trigger"
    checks.append({
        "name": "reminder_accountant_is_trigger",
        "passed": acc_is_trigger,
        "detail": f"Entry: {acc}" if acc else "Entry not found"
    })

    acc_scheduled_ok = False
    acc_scheduled_detail = "Entry not found or missing scheduledFor"
    if acc and "scheduledFor" in acc:
        sf = acc["scheduledFor"]
        # end of day tomorrow = 2026-03-23T23:59:59+08:00
        acc_scheduled_ok = "2026-03-23" in sf and "+08:00" in sf
        acc_scheduled_detail = f"scheduledFor={sf}"
    checks.append({
        "name": "reminder_accountant_scheduledFor_correct",
        "passed": acc_scheduled_ok,
        "detail": acc_scheduled_detail
    })

    acc_id_ok, acc_id_detail = (False, "No entry") if acc is None else check_id_format(acc.get("id", ""), "remind")
    checks.append({"name": "reminder_accountant_id_format", "passed": acc_id_ok, "detail": acc_id_detail})

    acc_labels_ok = False
    acc_labels_detail = "No entry or no labels"
    if acc and "labels" in acc:
        lbls = acc["labels"]
        # finance or work labels expected
        acc_labels_ok = any(l in lbls for l in ["finance", "work", "tax"])
        acc_labels_detail = f"labels={lbls}"
    checks.append({"name": "reminder_accountant_labels", "passed": acc_labels_ok, "detail": acc_labels_detail})

    # =====================================================================
    # 2. Task: review OpenClaw PR #451 — should be item with url
    # =====================================================================
    pr = find_entry(["451"], entries) or find_entry(["openclaw", "pr"], entries)
    if pr is None:
        for e in entries:
            if "451" in str(e) or ("openclaw" in str(e).lower() and "pull" in str(e).lower()):
                pr = e
                break

    pr_is_item = pr is not None and pr.get("type") == "item"
    checks.append({
        "name": "pr_review_openclaw_451_is_item",
        "passed": pr_is_item,
        "detail": f"Entry: {pr}" if pr else "Entry not found"
    })

    pr_has_url = pr is not None and "url" in pr and "451" in str(pr.get("url", ""))
    checks.append({
        "name": "pr_review_has_url",
        "passed": pr_has_url,
        "detail": f"url={pr.get('url') if pr else 'N/A'}"
    })

    pr_id_ok, pr_id_detail = (False, "No entry") if pr is None else check_id_format(pr.get("id", ""), "pr")
    checks.append({"name": "pr_review_id_format", "passed": pr_id_ok, "detail": pr_id_detail})

    pr_labels_ok = pr is not None and "labels" in pr and "code-review" in pr.get("labels", [])
    checks.append({
        "name": "pr_review_labels",
        "passed": pr_labels_ok,
        "detail": f"labels={pr.get('labels') if pr else 'N/A'}"
    })

    # =====================================================================
    # 3. Deadline: SSL certificate renewal — April 15 23:59 +08:00 → trigger
    # =====================================================================
    ssl = find_entry(["ssl"], entries)
    if ssl is None:
        for e in entries:
            if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                ssl = e
                break

    ssl_is_trigger = ssl is not None and ssl.get("type") == "trigger"
    checks.append({
        "name": "deadline_ssl_is_trigger",
        "passed": ssl_is_trigger,
        "detail": f"Entry: {ssl}" if ssl else "Entry not found"
    })

    ssl_april15 = False
    ssl_april15_detail = "No entry or missing scheduledFor"
    if ssl and "scheduledFor" in ssl:
        sf = ssl["scheduledFor"]
        ssl_april15 = "2026-04-15" in sf and "23:59" in sf
        ssl_april15_detail = f"scheduledFor={sf}"
    checks.append({"name": "deadline_ssl_scheduledFor_april15", "passed": ssl_april15, "detail": ssl_april15_detail})

    ssl_tz_ok = False
    ssl_tz_detail = "No scheduledFor"
    if ssl and "scheduledFor" in ssl:
        ssl_tz_ok, ssl_tz_detail = check_iso8601_timezone(ssl["scheduledFor"])
    checks.append({"name": "deadline_ssl_timezone", "passed": ssl_tz_ok, "detail": ssl_tz_detail})

    ssl_id_ok, ssl_id_detail = (False, "No entry") if ssl is None else check_id_format(ssl.get("id", ""), "deadline")
    checks.append({"name": "deadline_ssl_id_format", "passed": ssl_id_ok, "detail": ssl_id_detail})

    ssl_labels_ok = ssl is not None and "labels" in ssl and any(
        l in ssl.get("labels", []) for l in ["finance", "urgent", "high-priority", "work"]
    )
    checks.append({
        "name": "deadline_ssl_labels_finance_or_urgent",
        "passed": ssl_labels_ok,
        "detail": f"labels={ssl.get('labels') if ssl else 'N/A'}"
    })

    # =====================================================================
    # 4. Task: write Q2 investor update email — item with work/fundraising labels
    # =====================================================================
    inv = find_entry(["investor"], entries) or find_entry(["q2", "email"], entries)
    if inv is None:
        for e in entries:
            if "investor" in str(e).lower() or ("q2" in str(e).lower() and "email" in str(e).lower()):
                inv = e
                break

    inv_is_item = inv is not None and inv.get("type") == "item"
    checks.append({
        "name": "task_investor_email_is_item",
        "passed": inv_is_item,
        "detail": f"Entry: {inv}" if inv else "Entry not found"
    })

    inv_labels_ok = inv is not None and "labels" in inv and any(
        l in inv.get("labels", []) for l in ["work", "fundraising", "meeting"]
    )
    checks.append({
        "name": "task_investor_email_labels",
        "passed": inv_labels_ok,
        "detail": f"labels={inv.get('labels') if inv else 'N/A'}"
    })

    # =====================================================================
    # 5. Reminder: call mom — Sunday morning 10am
    #    Next Sunday from 2026-03-22 (Sunday) = 2026-03-29T10:00:00+08:00
    #    OR same-day 2026-03-22T10:00:00+08:00 (today is Sunday)
    #    Accept either 2026-03-22 or 2026-03-29
    # =====================================================================
    mom = find_entry(["mom"], entries)
    if mom is None:
        for e in entries:
            if "mom" in str(e).lower() or "mother" in str(e).lower():
                mom = e
                break

    mom_is_trigger = mom is not None and mom.get("type") == "trigger"
    checks.append({
        "name": "reminder_call_mom_is_trigger",
        "passed": mom_is_trigger,
        "detail": f"Entry: {mom}" if mom else "Entry not found"
    })

    mom_scheduled_ok = False
    mom_scheduled_detail = "No entry or missing scheduledFor"
    if mom and "scheduledFor" in mom:
        sf = mom["scheduledFor"]
        # Sunday 10am: accept 2026-03-22 or 2026-03-29, must have T10:00
        mom_scheduled_ok = ("T10:00" in sf) and (("2026-03-22" in sf) or ("2026-03-29" in sf))
        mom_scheduled_detail = f"scheduledFor={sf}"
    checks.append({"name": "reminder_call_mom_scheduledFor", "passed": mom_scheduled_ok, "detail": mom_scheduled_detail})

    mom_tz_ok = False
    mom_tz_detail = "No scheduledFor"
    if mom and "scheduledFor" in mom:
        mom_tz_ok, mom_tz_detail = check_iso8601_timezone(mom["scheduledFor"])
    checks.append({"name": "reminder_call_mom_timezone", "passed": mom_tz_ok, "detail": mom_tz_detail})

    # =====================================================================
    # 6. Deadline: Vercel annual billing — next Friday end of day
    #    Next Friday from 2026-03-22 = 2026-03-27T23:59:59+08:00
    # =====================================================================
    vercel = find_entry(["vercel"], entries)
    if vercel is None:
        for e in entries:
            if "vercel" in str(e).lower() or ("billing" in str(e).lower() and "vercel" in str(e).lower()):
                vercel = e
                break

    vercel_is_trigger = vercel is not None and vercel.get("type") == "trigger"
    checks.append({
        "name": "deadline_vercel_billing_is_trigger",
        "passed": vercel_is_trigger,
        "detail": f"Entry: {vercel}" if vercel else "Entry not found"
    })

    vercel_date_ok = False
    vercel_date_detail = "No entry or missing scheduledFor"
    if vercel and "scheduledFor" in vercel:
        sf = vercel["scheduledFor"]
        # next Friday = 2026-03-27, end of day = 23:59
        vercel_date_ok = "2026-03-27" in sf and "23:59" in sf
        vercel_date_detail = f"scheduledFor={sf}"
    checks.append({
        "name": "deadline_vercel_billing_nextfriday",
        "passed": vercel_date_ok,
        "detail": vercel_date_detail
    })

    vercel_tz_ok = False
    vercel_tz_detail = "No scheduledFor"
    if vercel and "scheduledFor" in vercel:
        vercel_tz_ok, vercel_tz_detail = check_iso8601_timezone(vercel["scheduledFor"])
    checks.append({"name": "deadline_vercel_billing_timezone", "passed": vercel_tz_ok, "detail": vercel_tz_detail})

    # =====================================================================
    # 7. Track issue #88 — item with url
    # =====================================================================
    iss88 = find_entry(["88"], entries)
    if iss88 is None:
        for e in entries:
            if "issue" in str(e).lower() and "88" in str(e):
                iss88 = e
                break

    iss88_is_item = iss88 is not None and iss88.get("type") == "item"
    checks.append({
        "name": "track_issue_88_is_item",
        "passed": iss88_is_item,
        "detail": f"Entry: {iss88}" if iss88 else "Entry not found"
    })

    iss88_has_url = iss88 is not None and "url" in iss88 and "88" in str(iss88.get("url", ""))
    checks.append({
        "name": "track_issue_88_has_url",
        "passed": iss88_has_url,
        "detail": f"url={iss88.get('url') if iss88 else 'N/A'}"
    })

    iss88_labels_ok = iss88 is not None and "labels" in iss88 and any(
        l in iss88.get("labels", []) for l in ["code-review", "work"]
    )
    checks.append({
        "name": "track_issue_88_labels",
        "passed": iss88_labels_ok,
        "detail": f"labels={iss88.get('labels') if iss88 else 'N/A'}"
    })

    # =====================================================================
    # Bonus: no forbidden explicit "active" status set where not needed
    # Actually the skill says "default status is active, don't set unless changing"
    # However, the example DOES set status: "active" on tasks, so we'll be lenient here
    # and just check that triggers don't have a status field set (triggers are fire-once)
    # =====================================================================
    trigger_entries = [e for e in entries if e.get("type") == "trigger"]
    triggers_no_status = all("status" not in e for e in trigger_entries)
    checks.append({
        "name": "no_forbidden_status_on_new_items",
        "passed": triggers_no_status,
        "detail": f"Checked {len(trigger_entries)} trigger entries for unexpected 'status' field"
    })

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.75  # pass threshold: 75% of checks

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()