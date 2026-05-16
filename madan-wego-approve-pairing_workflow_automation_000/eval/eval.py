import sys
import json
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text())

def run_checks(workspace):
    checks = []
    creds_dir = Path.home() / ".openclaw" / "credentials"

    # ── CHECK 1: telegram allowFrom file exists with correct name ─────────────
    tg_allow_path = creds_dir / "telegram-acc-7821-allowFrom.json"
    try:
        tg_allow = load_json(tg_allow_path)
        checks.append({
            "name": "telegram allowFrom file exists",
            "passed": True,
            "detail": f"Found {tg_allow_path}"
        })
    except Exception as e:
        checks.append({
            "name": "telegram allowFrom file exists",
            "passed": False,
            "detail": f"Missing or unreadable: {tg_allow_path} — {e}"
        })
        tg_allow = None

    # ── CHECK 2: telegram allowFrom has correct version ──────────────────────
    if tg_allow is not None:
        ver_ok = tg_allow.get("version") == 1
        checks.append({
            "name": "telegram allowFrom version == 1",
            "passed": ver_ok,
            "detail": f"Got version={tg_allow.get('version')}"
        })
    else:
        checks.append({"name": "telegram allowFrom version == 1", "passed": False,
                        "detail": "File missing"})

    # ── CHECK 3: telegram sender ID present in allowFrom ─────────────────────
    if tg_allow is not None:
        present = "tg_user_553912" in tg_allow.get("allowFrom", [])
        checks.append({
            "name": "telegram sender tg_user_553912 in allowFrom",
            "passed": present,
            "detail": f"allowFrom={tg_allow.get('allowFrom')}"
        })
    else:
        checks.append({"name": "telegram sender tg_user_553912 in allowFrom",
                        "passed": False, "detail": "File missing"})

    # ── CHECK 4: telegram pairing code ALPHA77X removed from pairing file ────
    tg_pairing_path = creds_dir / "telegram-pairing.json"
    try:
        tg_pairing = load_json(tg_pairing_path)
        codes = [r.get("code") for r in tg_pairing.get("requests", [])]
        removed = "ALPHA77X" not in codes
        checks.append({
            "name": "telegram ALPHA77X removed from pairing file",
            "passed": removed,
            "detail": f"Remaining codes in pairing file: {codes}"
        })
    except Exception as e:
        checks.append({
            "name": "telegram ALPHA77X removed from pairing file",
            "passed": False,
            "detail": f"Could not read pairing file: {e}"
        })

    # ── CHECK 5: slack allowFrom file uses 'default' (not empty string) ───────
    slack_allow_path_default = creds_dir / "slack-default-allowFrom.json"
    slack_allow_path_empty   = creds_dir / "slack--allowFrom.json"  # wrong path

    if slack_allow_path_empty.exists():
        checks.append({
            "name": "slack allowFrom file NOT named with empty accountId",
            "passed": False,
            "detail": f"Found wrongly-named file slack--allowFrom.json. Should be slack-default-allowFrom.json"
        })
        sl_allow = None
    else:
        checks.append({
            "name": "slack allowFrom file NOT named with empty accountId",
            "passed": True,
            "detail": "slack--allowFrom.json does not exist (correct)"
        })

        try:
            sl_allow = load_json(slack_allow_path_default)
            checks.append({
                "name": "slack-default-allowFrom.json exists",
                "passed": True,
                "detail": f"Found {slack_allow_path_default}"
            })
        except Exception as e:
            checks.append({
                "name": "slack-default-allowFrom.json exists",
                "passed": False,
                "detail": f"Missing or unreadable: {slack_allow_path_default} — {e}"
            })
            sl_allow = None

    # ── CHECK 6: slack allowFrom has correct version ──────────────────────────
    if sl_allow is not None:
        ver_ok = sl_allow.get("version") == 1
        checks.append({
            "name": "slack allowFrom version == 1",
            "passed": ver_ok,
            "detail": f"Got version={sl_allow.get('version')}"
        })
    else:
        checks.append({"name": "slack allowFrom version == 1", "passed": False,
                        "detail": "File missing"})

    # ── CHECK 7: slack sender ID present in allowFrom ─────────────────────────
    if sl_allow is not None:
        present = "slack_uid_U04NZPQ88" in sl_allow.get("allowFrom", [])
        checks.append({
            "name": "slack sender slack_uid_U04NZPQ88 in allowFrom",
            "passed": present,
            "detail": f"allowFrom={sl_allow.get('allowFrom')}"
        })
    else:
        checks.append({"name": "slack sender slack_uid_U04NZPQ88 in allowFrom",
                        "passed": False, "detail": "File missing"})

    # ── CHECK 8: slack pairing code BETA99Z removed from pairing file ─────────
    slack_pairing_path = creds_dir / "slack-pairing.json"
    try:
        sk_pairing = load_json(slack_pairing_path)
        codes = [r.get("code") for r in sk_pairing.get("requests", [])]
        removed = "BETA99Z" not in codes
        checks.append({
            "name": "slack BETA99Z removed from pairing file",
            "passed": removed,
            "detail": f"Remaining codes in pairing file: {codes}"
        })
    except Exception as e:
        checks.append({
            "name": "slack BETA99Z removed from pairing file",
            "passed": False,
            "detail": f"Could not read pairing file: {e}"
        })

    # ── CHECK 9: whatsapp distractor file untouched ───────────────────────────
    wa_path = creds_dir / "whatsapp-default-allowFrom.json"
    try:
        wa = load_json(wa_path)
        intact = wa.get("allowFrom") == ["wa_user_99887766"]
        checks.append({
            "name": "whatsapp distractor file untouched",
            "passed": intact,
            "detail": f"whatsapp allowFrom={wa.get('allowFrom')}"
        })
    except Exception as e:
        checks.append({
            "name": "whatsapp distractor file untouched",
            "passed": False,
            "detail": f"File missing or corrupted: {e}"
        })

    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = run_checks(workspace)
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count == total
    result = {
        "passed": overall,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()