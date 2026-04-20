import json
import os
import re
from pathlib import Path


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def fuzzy_contains(text, phrase):
    return norm(phrase) in norm(text)


def safe_read(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None, str(e)


def main(workspace):
    checks = []
    ws = Path(workspace)

    try:
        p = ws / "revenue_model_plan.txt"
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="replace")
            checks.append({"name": "output_exists", "passed": True, "detail": "revenue_model_plan.txt exists"})
        else:
            text = ""
            checks.append({"name": "output_exists", "passed": False, "detail": "revenue_model_plan.txt is missing"})
    except Exception as e:
        text = ""
        checks.append({"name": "output_exists", "passed": False, "detail": f"Could not inspect output file: {e}"})

    try:
        ok = fuzzy_contains(text, "primary revenue stream") or fuzzy_contains(text, "primary stream")
        checks.append({"name": "primary_stream_present", "passed": ok, "detail": "Found a primary stream section" if ok else "Primary stream not clearly described"})
    except Exception as e:
        checks.append({"name": "primary_stream_present", "passed": False, "detail": f"Error checking primary stream: {e}"})

    try:
        sec = fuzzy_contains(text, "secondary revenue stream") or fuzzy_contains(text, "secondary stream")
        opp = fuzzy_contains(text, "opportunistic stream") or fuzzy_contains(text, "opportunistic")
        checks.append({"name": "secondary_and_opportunistic", "passed": sec and opp, "detail": f"secondary={sec}, opportunistic={opp}"})
    except Exception as e:
        checks.append({"name": "secondary_and_opportunistic", "passed": False, "detail": f"Error checking supporting streams: {e}"})

    try:
        cadence_ok = any(fuzzy_contains(text, x) for x in ["monthly", "annual", "one time", "one-time", "quarterly"])
        payment_ok = any(fuzzy_contains(text, x) for x in ["stripe", "invoice", "billing", "checkout", "payment flow"])
        checks.append({"name": "cadence_and_payment_flow", "passed": cadence_ok and payment_ok, "detail": f"cadence={cadence_ok}, payment={payment_ok}"})
    except Exception as e:
        checks.append({"name": "cadence_and_payment_flow", "passed": False, "detail": f"Error checking cadence/payment: {e}"})

    try:
        proj_ok = fuzzy_contains(text, "12 month") or fuzzy_contains(text, "12-month") or fuzzy_contains(text, "month 12")
        checks.append({"name": "projection_summary", "passed": proj_ok, "detail": "12-month projection summary present" if proj_ok else "No clear 12-month projection summary"})
    except Exception as e:
        checks.append({"name": "projection_summary", "passed": False, "detail": f"Error checking projection: {e}"})

    total = len(checks)
    passed = sum(1 for c in checks if c.get("passed"))
    score = (passed / total) if total else 0.0
    result = {"passed": passed == total and total > 0, "score": score, "checks": checks}
    print(json.dumps(result))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
