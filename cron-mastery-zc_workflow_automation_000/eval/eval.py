import json
import sys
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0

def load_json(path):
    with open(path) as f:
        return json.load(f)

def check(name, condition, detail, weight=1.0):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return weight if condition else 0.0

# ── HELPER ───────────────────────────────────────────────────────────────────
STRICT_PREFIX = "DELIVER THIS EXACT MESSAGE TO THE USER WITHOUT MODIFICATION OR COMMENTARY:"

# ── 1. LEGACY JOB 1: legacy_job_med_reminder.json ────────────────────────────
med_path = Path(workspace) / "services/reminder/legacy_job_med_reminder.json"
try:
    med = load_json(med_path)

    # 1a. schedule.at (ISO 8601) replaces atMs
    has_at = med.get("schedule", {}).get("at") == "2026-02-06T01:30:00Z"
    total_score += check(
        "med_reminder: schedule.at is ISO 8601 (2026-02-06T01:30:00Z)",
        has_at,
        f"schedule={med.get('schedule')}"
    )

    # 1b. No atMs
    no_atms = "atMs" not in med.get("schedule", {})
    total_score += check(
        "med_reminder: legacy atMs removed",
        no_atms,
        f"schedule keys={list(med.get('schedule', {}).keys())}"
    )

    # 1c. payload.kind = agentTurn
    payload_kind_ok = med.get("payload", {}).get("kind") == "agentTurn"
    total_score += check(
        "med_reminder: payload.kind is agentTurn",
        payload_kind_ok,
        f"payload.kind={med.get('payload', {}).get('kind')}"
    )

    # 1d. No deliver:true in payload
    no_deliver = "deliver" not in med.get("payload", {})
    total_score += check(
        "med_reminder: legacy 'deliver' field removed from payload",
        no_deliver,
        f"payload keys={list(med.get('payload', {}).keys())}"
    )

    # 1e. Strict instruction prefix in message
    msg = med.get("payload", {}).get("message", "")
    has_strict = STRICT_PREFIX in msg
    total_score += check(
        "med_reminder: payload.message uses strict instruction prefix",
        has_strict,
        f"message starts with: {msg[:80]!r}"
    )

    # 1f. sessionTarget = isolated
    session_ok = med.get("sessionTarget") == "isolated"
    total_score += check(
        "med_reminder: sessionTarget is 'isolated' (not 'main')",
        session_ok,
        f"sessionTarget={med.get('sessionTarget')}"
    )

    # 1g. wakeMode = now
    wake_ok = med.get("wakeMode") == "now"
    total_score += check(
        "med_reminder: wakeMode is 'now'",
        wake_ok,
        f"wakeMode={med.get('wakeMode')}"
    )

    # 1h. deleteAfterRun = true
    dar_ok = med.get("deleteAfterRun") is True
    total_score += check(
        "med_reminder: deleteAfterRun is true",
        dar_ok,
        f"deleteAfterRun={med.get('deleteAfterRun')}"
    )

    # 1i. delivery block with announce + telegram + correct to
    delivery = med.get("delivery", {})
    delivery_ok = (
        delivery.get("mode") == "announce"
        and delivery.get("channel") == "telegram"
        and str(delivery.get("to")) == "1027899060"
    )
    total_score += check(
        "med_reminder: delivery block correct (announce/telegram/1027899060)",
        delivery_ok,
        f"delivery={delivery}"
    )

except Exception as e:
    for name in [
        "med_reminder: schedule.at is ISO 8601 (2026-02-06T01:30:00Z)",
        "med_reminder: legacy atMs removed",
        "med_reminder: payload.kind is agentTurn",
        "med_reminder: legacy 'deliver' field removed from payload",
        "med_reminder: payload.message uses strict instruction prefix",
        "med_reminder: sessionTarget is 'isolated' (not 'main')",
        "med_reminder: wakeMode is 'now'",
        "med_reminder: deleteAfterRun is true",
        "med_reminder: delivery block correct (announce/telegram/1027899060)",
    ]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})

# ── 2. LEGACY JOB 2: legacy_job_appt_reminder.json ───────────────────────────
appt_path = Path(workspace) / "services/reminder/legacy_job_appt_reminder.json"
try:
    appt = load_json(appt_path)

    has_at = appt.get("schedule", {}).get("at") == "2026-02-06T14:40:00Z"
    total_score += check(
        "appt_reminder: schedule.at is ISO 8601 (2026-02-06T14:40:00Z)",
        has_at,
        f"schedule={appt.get('schedule')}"
    )

    no_atms = "atMs" not in appt.get("schedule", {})
    total_score += check(
        "appt_reminder: legacy atMs removed",
        no_atms,
        f"schedule keys={list(appt.get('schedule', {}).keys())}"
    )

    payload_kind_ok = appt.get("payload", {}).get("kind") == "agentTurn"
    total_score += check(
        "appt_reminder: payload.kind is agentTurn",
        payload_kind_ok,
        f"payload.kind={appt.get('payload', {}).get('kind')}"
    )

    no_deliver = "deliver" not in appt.get("payload", {})
    total_score += check(
        "appt_reminder: legacy 'deliver' field removed from payload",
        no_deliver,
        f"payload keys={list(appt.get('payload', {}).keys())}"
    )

    msg = appt.get("payload", {}).get("message", "")
    has_strict = STRICT_PREFIX in msg
    total_score += check(
        "appt_reminder: payload.message uses strict instruction prefix",
        has_strict,
        f"message starts with: {msg[:80]!r}"
    )

    session_ok = appt.get("sessionTarget") == "isolated"
    total_score += check(
        "appt_reminder: sessionTarget is 'isolated' (not 'main')",
        session_ok,
        f"sessionTarget={appt.get('sessionTarget')}"
    )

    wake_ok = appt.get("wakeMode") == "now"
    total_score += check(
        "appt_reminder: wakeMode is 'now'",
        wake_ok,
        f"wakeMode={appt.get('wakeMode')}"
    )

    dar_ok = appt.get("deleteAfterRun") is True
    total_score += check(
        "appt_reminder: deleteAfterRun is true",
        dar_ok,
        f"deleteAfterRun={appt.get('deleteAfterRun')}"
    )

    delivery = appt.get("delivery", {})
    delivery_ok = (
        delivery.get("mode") == "announce"
        and delivery.get("channel") == "telegram"
        and str(delivery.get("to")) == "1027899060"
    )
    total_score += check(
        "appt_reminder: delivery block correct (announce/telegram/1027899060)",
        delivery_ok,
        f"delivery={delivery}"
    )

except Exception as e:
    for name in [
        "appt_reminder: schedule.at is ISO 8601 (2026-02-06T14:40:00Z)",
        "appt_reminder: legacy atMs removed",
        "appt_reminder: payload.kind is agentTurn",
        "appt_reminder: legacy 'deliver' field removed from payload",
        "appt_reminder: payload.message uses strict instruction prefix",
        "appt_reminder: sessionTarget is 'isolated' (not 'main')",
        "appt_reminder: wakeMode is 'now'",
        "appt_reminder: deleteAfterRun is true",
        "appt_reminder: delivery block correct (announce/telegram/1027899060)",
    ]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})

# ── 3. NEW FILE: new_hydration_reminder.json ─────────────────────────────────
hydration_candidates = list(Path(workspace).rglob("new_hydration_reminder.json"))
try:
    assert hydration_candidates, "File not found"
    hyd = load_json(hydration_candidates[0])

    # schedule: every 24h = 86400000ms
    sched = hyd.get("schedule", {})
    is_every = sched.get("kind") == "every" and sched.get("everyMs") == 86400000
    total_score += check(
        "new_hydration: schedule is every 24h (everyMs=86400000)",
        is_every,
        f"schedule={sched}"
    )

    # payload: agentTurn
    payload_kind_ok = hyd.get("payload", {}).get("kind") == "agentTurn"
    total_score += check(
        "new_hydration: payload.kind is agentTurn (push notification)",
        payload_kind_ok,
        f"payload.kind={hyd.get('payload', {}).get('kind')}"
    )

    # strict prefix in message
    msg = hyd.get("payload", {}).get("message", "")
    has_strict = STRICT_PREFIX in msg
    total_score += check(
        "new_hydration: payload.message uses strict instruction prefix",
        has_strict,
        f"message starts with: {msg[:100]!r}"
    )

    # verbatim message content after prefix
    verbatim_msg = "💧 Drink water, Momo! Stay hydrated for your treatment."
    has_verbatim = verbatim_msg in msg
    total_score += check(
        "new_hydration: verbatim message content present",
        has_verbatim,
        f"message={msg!r}"
    )

    # sessionTarget: isolated
    session_ok = hyd.get("sessionTarget") == "isolated"
    total_score += check(
        "new_hydration: sessionTarget is 'isolated'",
        session_ok,
        f"sessionTarget={hyd.get('sessionTarget')}"
    )

    # wakeMode: now
    wake_ok = hyd.get("wakeMode") == "now"
    total_score += check(
        "new_hydration: wakeMode is 'now'",
        wake_ok,
        f"wakeMode={hyd.get('wakeMode')}"
    )

    # delivery: announce + telegram + 1027899060
    delivery = hyd.get("delivery", {})
    delivery_ok = (
        delivery.get("mode") == "announce"
        and delivery.get("channel") == "telegram"
        and str(delivery.get("to")) == "1027899060"
    )
    total_score += check(
        "new_hydration: delivery block correct (announce/telegram/1027899060)",
        delivery_ok,
        f"delivery={delivery}"
    )

    # Schedule at 07:00 UTC (09:00 Cairo GMT+2)
    # For 'every' daily jobs, check if there's a time hint or just accept everyMs=86400000 with a start time
    # The spec says "Daily at 09:00 AM Cairo time = 07:00 UTC"
    # For a proper daily job, we can accept either:
    #   - kind: "every" with everyMs: 86400000 (daily recurring)
    #   - OR kind: "at" for one-shot. But spec says "Daily" -> every is correct.
    # We also accept an optional 'startAt' or 'at' hint for UTC 07:00
    # This check is lenient: if they used 'every' with 86400000, that's the key signal
    total_score += check(
        "new_hydration: recurring daily schedule (not one-shot)",
        sched.get("kind") == "every",
        f"schedule.kind={sched.get('kind')}"
    )

except Exception as e:
    for name in [
        "new_hydration: schedule is every 24h (everyMs=86400000)",
        "new_hydration: payload.kind is agentTurn (push notification)",
        "new_hydration: payload.message uses strict instruction prefix",
        "new_hydration: verbatim message content present",
        "new_hydration: sessionTarget is 'isolated'",
        "new_hydration: wakeMode is 'now'",
        "new_hydration: delivery block correct (announce/telegram/1027899060)",
        "new_hydration: recurring daily schedule (not one-shot)",
    ]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})

# ── 4. NEW FILE: new_maintenance_job.json ────────────────────────────────────
maint_candidates = list(Path(workspace).rglob("new_maintenance_job.json"))
try:
    assert maint_candidates, "File not found"
    maint = load_json(maint_candidates[0])

    # schedule: every 24h
    sched = maint.get("schedule", {})
    is_every = sched.get("kind") == "every" and sched.get("everyMs") == 86400000
    total_score += check(
        "new_maintenance: schedule is every 24h (everyMs=86400000)",
        is_every,
        f"schedule={sched}"
    )

    # payload: systemEvent (NOT agentTurn — silent log)
    payload_kind_ok = maint.get("payload", {}).get("kind") == "systemEvent"
    total_score += check(
        "new_maintenance: payload.kind is systemEvent (silent, not agentTurn)",
        payload_kind_ok,
        f"payload.kind={maint.get('payload', {}).get('kind')}"
    )

    # text field contains required log message
    text = maint.get("payload", {}).get("text", "")
    has_text = "[MAINTENANCE] MedTrack gateway health check passed." in text
    total_score += check(
        "new_maintenance: payload.text contains required log message",
        has_text,
        f"text={text!r}"
    )

    # CRITICAL: sessionTarget = main (not isolated — janitor needs full tool access)
    session_ok = maint.get("sessionTarget") == "main"
    total_score += check(
        "new_maintenance: sessionTarget is 'main' (CRITICAL — janitor must use main session)",
        session_ok,
        f"sessionTarget={maint.get('sessionTarget')}"
    )

    # No delivery block (silent log — no announce)
    no_delivery = "delivery" not in maint
    total_score += check(
        "new_maintenance: no delivery block (silent job, no push notification)",
        no_delivery,
        f"keys={list(maint.keys())}"
    )

    # No agentTurn strict prefix (should be systemEvent, not agentTurn)
    no_strict_prefix = STRICT_PREFIX not in str(maint.get("payload", {}))
    total_score += check(
        "new_maintenance: no strict instruction prefix (systemEvent, not agentTurn)",
        no_strict_prefix,
        f"payload={maint.get('payload')}"
    )

except Exception as e:
    for name in [
        "new_maintenance: schedule is every 24h (everyMs=86400000)",
        "new_maintenance: payload.kind is systemEvent (silent, not agentTurn)",
        "new_maintenance: payload.text contains required log message",
        "new_maintenance: sessionTarget is 'main' (CRITICAL — janitor must use main session)",
        "new_maintenance: no delivery block (silent job, no push notification)",
        "new_maintenance: no strict instruction prefix (systemEvent, not agentTurn)",
    ]:
        checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})

# ── SCORE ─────────────────────────────────────────────────────────────────────
total_checks = len(checks)
passed_checks = sum(1 for c in checks if c["passed"])
score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
overall_passed = score >= 0.85

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))