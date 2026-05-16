import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    home = Path.home()

    # ------------------------------------------------------------------ #
    # CHECK 1: Config file exists at the correct path                      #
    # ------------------------------------------------------------------ #
    config_path = home / ".config/lel-mail/config.json"
    config_ok = False
    config_data = None
    try:
        assert config_path.exists(), "Config file not found at ~/.config/lel-mail/config.json"
        with open(config_path) as f:
            config_data = json.load(f)
        assert isinstance(config_data, list), "Config must be a JSON array"
        assert len(config_data) >= 1, "Config array must have at least one entry"
        entry = config_data[0]
        assert "provider" in entry, "Missing 'provider' field"
        assert "auth" in entry, "Missing 'auth' field"
        assert "can_send" in entry, "Missing 'can_send' field"
        assert "can_read" in entry, "Missing 'can_read' field"
        assert entry["can_send"] is True, "'can_send' must be true"
        assert entry["can_read"] is True, "'can_read' must be true"
        auth = entry["auth"]
        assert "user" in auth, "Missing auth.user"
        assert "password" in auth, "Missing auth.password"
        # Verify the correct email account is used
        assert "risk-alerts@tradingdesk.com" in auth.get("user", ""), \
            f"auth.user should be risk-alerts@tradingdesk.com, got: {auth.get('user','')}"
        config_ok = True
        checks.append({
            "name": "config_file_valid",
            "passed": True,
            "detail": f"Config file exists at {config_path} with correct structure and email account."
        })
    except Exception as e:
        checks.append({
            "name": "config_file_valid",
            "passed": False,
            "detail": f"Config validation failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 2: Config has correct smtp/imap structure                       #
    # ------------------------------------------------------------------ #
    try:
        assert config_data is not None, "No config data loaded"
        entry = config_data[0]
        assert "config" in entry, "Missing 'config' field in entry"
        cfg = entry["config"]
        assert "smtp" in cfg, "Missing smtp section"
        assert "imap" in cfg, "Missing imap section"
        smtp = cfg["smtp"]
        imap = cfg["imap"]
        assert "server" in smtp and "port" in smtp, "SMTP needs server and port"
        assert "server" in imap and "port" in imap, "IMAP needs server and port"
        checks.append({
            "name": "config_smtp_imap_structure",
            "passed": True,
            "detail": f"smtp={smtp}, imap={imap}"
        })
    except Exception as e:
        checks.append({
            "name": "config_smtp_imap_structure",
            "passed": False,
            "detail": f"smtp/imap structure check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 3: The erroneous draft (QM-20240415-001) was deleted           #
    # ------------------------------------------------------------------ #
    queue_dir = home / ".openclaw/workspace/skills/lel-mail/queue"
    draft_id = "QM-20240415-001"
    try:
        draft_files = list(queue_dir.glob("*.json"))
        draft_ids = []
        for f in draft_files:
            with open(f) as fh:
                d = json.load(fh)
            draft_ids.append(d.get("id", ""))
        
        assert draft_id not in draft_ids, \
            f"Erroneous draft {draft_id} was NOT deleted. Still in queue: {draft_ids}"
        checks.append({
            "name": "erroneous_draft_deleted",
            "passed": True,
            "detail": f"Draft email {draft_id} (DO NOT SEND) was successfully deleted from queue."
        })
    except Exception as e:
        checks.append({
            "name": "erroneous_draft_deleted",
            "passed": False,
            "detail": f"Draft deletion check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 4: The legitimate queued email (QM-20240415-002) still exists  #
    # ------------------------------------------------------------------ #
    try:
        draft_files = list(queue_dir.glob("*.json"))
        all_ids = []
        for f in draft_files:
            with open(f) as fh:
                d = json.load(fh)
            all_ids.append(d.get("id", ""))
        assert "QM-20240415-002" in all_ids, \
            f"Legitimate email QM-20240415-002 was incorrectly deleted. Remaining IDs: {all_ids}"
        checks.append({
            "name": "legitimate_email_preserved",
            "passed": True,
            "detail": "Legitimate queued email QM-20240415-002 was correctly preserved."
        })
    except Exception as e:
        checks.append({
            "name": "legitimate_email_preserved",
            "passed": False,
            "detail": f"Legitimate email preservation check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 5: New VaR alert email was queued                              #
    # ------------------------------------------------------------------ #
    new_alert_found = False
    new_alert_detail = ""
    try:
        draft_files = list(queue_dir.glob("*.json"))
        candidate = None
        for f in draft_files:
            with open(f) as fh:
                d = json.load(fh)
            mid = d.get("id", "")
            # Must NOT be the two pre-existing emails
            if mid in ("QM-20240415-001", "QM-20240415-002"):
                continue
            # Must be from the risk-alerts account
            sender = d.get("sender", "")
            recipient = d.get("recipient", "")
            if "risk-alerts@tradingdesk.com" not in sender:
                continue
            candidate = d
            break
        
        assert candidate is not None, \
            "No new alert email found in queue from risk-alerts@tradingdesk.com"
        
        # Verify recipient is the CRO
        assert "cro@tradingdesk.com" in candidate.get("recipient", ""), \
            f"Alert must be sent to cro@tradingdesk.com, got: {candidate.get('recipient','')}"
        
        new_alert_found = True
        new_alert_detail = f"New alert queued: id={candidate.get('id')}, to={candidate.get('recipient')}, cc={candidate.get('cc')}"
        checks.append({
            "name": "new_alert_email_queued",
            "passed": True,
            "detail": new_alert_detail
        })
    except Exception as e:
        checks.append({
            "name": "new_alert_email_queued",
            "passed": False,
            "detail": f"New alert email check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 6: CC contains both required stakeholders (comma-separated)    #
    # ------------------------------------------------------------------ #
    try:
        assert new_alert_found, "New alert not found, cannot check CC"
        cc_field = candidate.get("cc", "")
        assert cc_field, "CC field is empty - should include quantlead and compliance"
        cc_list = [x.strip() for x in cc_field.split(",")]
        
        assert any("quantlead@tradingdesk.com" in c for c in cc_list), \
            f"quantlead@tradingdesk.com missing from CC. Got: {cc_list}"
        assert any("compliance@tradingdesk.com" in c for c in cc_list), \
            f"compliance@tradingdesk.com missing from CC. Got: {cc_list}"
        
        checks.append({
            "name": "cc_comma_separated_stakeholders",
            "passed": True,
            "detail": f"CC field correctly includes quantlead and compliance: {cc_list}"
        })
    except Exception as e:
        checks.append({
            "name": "cc_comma_separated_stakeholders",
            "passed": False,
            "detail": f"CC check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # CHECK 7: Alert email has a non-empty subject and body                #
    # ------------------------------------------------------------------ #
    try:
        assert new_alert_found, "New alert not found, cannot check subject/body"
        subj = candidate.get("subject", "").strip()
        body = candidate.get("body", "").strip()
        assert subj, "Subject is empty"
        assert body, "Body is empty"
        # Subject should relate to VaR or risk (contextually appropriate)
        subj_lower = subj.lower()
        body_lower = body.lower()
        relevant = any(kw in subj_lower or kw in body_lower 
                       for kw in ["var", "risk", "breach", "limit", "alert", "value at risk"])
        assert relevant, f"Subject/body don't seem related to VaR alert. Subject='{subj}', Body snippet='{body[:80]}'"
        checks.append({
            "name": "alert_subject_body_relevant",
            "passed": True,
            "detail": f"Subject='{subj}', body is non-empty and contextually relevant."
        })
    except Exception as e:
        checks.append({
            "name": "alert_subject_body_relevant",
            "passed": False,
            "detail": f"Subject/body check failed: {e}"
        })

    # ------------------------------------------------------------------ #
    # Scoring                                                               #
    # ------------------------------------------------------------------ #
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3) if total > 0 else 0.0
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))