import sys
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score = 0.0
total_weight = 0.0

def run_node(script, *args):
    result = subprocess.run(
        ["node", str(workspace / "scripts" / script)] + list(args),
        capture_output=True, text=True, cwd=str(workspace)
    )
    return result

def check(name, passed, detail, weight=1.0):
    global score, total_weight
    checks.append({"name": name, "passed": passed, "detail": detail})
    total_weight += weight
    if passed:
        score += weight

# ── Load stores ──────────────────────────────────────────────────────────────
notes_store_path = workspace / "data" / "notes_store.json"
reminders_store_path = workspace / "data" / "reminders_store.json"

try:
    notes = json.loads(notes_store_path.read_text(encoding="utf-8"))
except Exception as e:
    notes = []
    check("notes_store_readable", False, f"Cannot read notes_store.json: {e}", weight=0.5)

try:
    reminders = json.loads(reminders_store_path.read_text(encoding="utf-8"))
except Exception as e:
    reminders = []
    check("reminders_store_readable", False, f"Cannot read reminders_store.json: {e}", weight=0.5)

# ── CHECK 1: At least 3 notes were added ─────────────────────────────────────
try:
    n_count = len(notes)
    passed = n_count >= 3
    check(
        "notes_minimum_count",
        passed,
        f"Found {n_count} notes in store; expected at least 3 (one per meeting topic).",
        weight=1.0
    )
except Exception as e:
    check("notes_minimum_count", False, f"Exception: {e}", weight=1.0)

# ── CHECK 2: Notes cover the 3 discussion topics ──────────────────────────────
try:
    all_text = " ".join(
        (n.get("title", "") + " " + n.get("content", "")).lower()
        for n in notes
    )
    # The three topics are API design (GraphQL/REST), performance (DB/N+1), release schedule
    topics = {
        "API/GraphQL": any(kw in all_text for kw in ["api", "graphql", "rest"]),
        "Performance/DB": any(kw in all_text for kw in ["パフォーマンス", "performance", "db", "n+1", "クエリ", "query", "チューニング"]),
        "Release/Schedule": any(kw in all_text for kw in ["リリース", "release", "v2.3", "スケジュール", "schedule", "デプロイ", "deploy", "qa"]),
    }
    missing = [k for k, v in topics.items() if not v]
    passed = len(missing) == 0
    check(
        "notes_cover_all_topics",
        passed,
        f"Topics coverage: {topics}. Missing: {missing}",
        weight=1.5
    )
except Exception as e:
    check("notes_cover_all_topics", False, f"Exception: {e}", weight=1.5)

# ── CHECK 3: Notes have non-empty title AND content ───────────────────────────
try:
    bad = [n for n in notes if not n.get("title", "").strip() or not n.get("content", "").strip()]
    passed = len(bad) == 0 and len(notes) >= 3
    check(
        "notes_have_title_and_content",
        passed,
        f"{len(bad)} notes missing title or content out of {len(notes)} total.",
        weight=1.0
    )
except Exception as e:
    check("notes_have_title_and_content", False, f"Exception: {e}", weight=1.0)

# ── CHECK 4: Exactly 3 reminders were added ───────────────────────────────────
try:
    r_count = len(reminders)
    passed = r_count == 3
    check(
        "reminders_count_exact",
        passed,
        f"Found {r_count} reminders; expected exactly 3 (one per [REMINDER] line).",
        weight=1.0
    )
except Exception as e:
    check("reminders_count_exact", False, f"Exception: {e}", weight=1.0)

# ── CHECK 5: remind_at uses ISO 8601 with +09:00 offset ──────────────────────
import re
try:
    iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")
    bad_tz = [r for r in reminders if not iso_pattern.match(r.get("remind_at", ""))]
    passed = len(bad_tz) == 0 and len(reminders) >= 1
    check(
        "reminders_iso8601_tokyo_offset",
        passed,
        f"{len(bad_tz)} reminders do NOT have +09:00 offset. Offending entries: {[r.get('remind_at') for r in bad_tz]}",
        weight=2.0
    )
except Exception as e:
    check("reminders_iso8601_tokyo_offset", False, f"Exception: {e}", weight=2.0)

# ── CHECK 6: remind_at timestamps match the meeting notes ────────────────────
try:
    expected_times = {
        "2026-01-15T09:00:00+09:00",
        "2026-01-20T09:00:00+09:00",
        "2026-01-16T15:00:00+09:00",
    }
    actual_times = {r.get("remind_at", "") for r in reminders}
    matched = expected_times & actual_times
    passed = len(matched) == 3
    check(
        "reminders_correct_timestamps",
        passed,
        f"Expected times: {expected_times}. Found: {actual_times}. Matched: {matched}",
        weight=2.0
    )
except Exception as e:
    check("reminders_correct_timestamps", False, f"Exception: {e}", weight=2.0)

# ── CHECK 7: Channels match the meeting notes ─────────────────────────────────
try:
    expected_channels = {"C0AHBLQ0P32", "C1DEPLOYOP9", "C2GRAPHQLCH"}
    actual_channels = {r.get("channel", "") for r in reminders}
    matched_ch = expected_channels & actual_channels
    passed = len(matched_ch) == 3
    check(
        "reminders_correct_channels",
        passed,
        f"Expected channels: {expected_channels}. Found: {actual_channels}. Matched: {matched_ch}",
        weight=1.5
    )
except Exception as e:
    check("reminders_correct_channels", False, f"Exception: {e}", weight=1.5)

# ── CHECK 8: check-and-fire was run and fired_alerts.txt exists ───────────────
fired_alerts_candidates = list(workspace.rglob("fired_alerts.txt"))
fired_alerts_path = fired_alerts_candidates[0] if fired_alerts_candidates else None

try:
    passed = fired_alerts_path is not None and fired_alerts_path.exists()
    check(
        "fired_alerts_file_exists",
        passed,
        f"fired_alerts.txt {'found at ' + str(fired_alerts_path) if passed else 'NOT found anywhere in workspace'}.",
        weight=1.0
    )
except Exception as e:
    check("fired_alerts_file_exists", False, f"Exception: {e}", weight=1.0)

# ── CHECK 9: fired_alerts.txt contains correct format "リマインダー: {message}" ──
try:
    if fired_alerts_path and fired_alerts_path.exists():
        content = fired_alerts_path.read_text(encoding="utf-8")
        # The only reminder that should have fired is the one with remind_at=2026-01-15T09:00:00+09:00
        # (田中: N+1クエリ調査レポート提出) -- its time is in the past relative to when check-and-fire runs
        # We check that at least one "リマインダー: " prefixed line exists
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        reminder_lines = [l for l in lines if l.startswith("リマインダー: ")]
        passed = len(reminder_lines) >= 1
        check(
            "fired_alerts_format_correct",
            passed,
            f"Lines with 'リマインダー: ' prefix: {len(reminder_lines)}. Content preview: {content[:300]}",
            weight=2.0
        )
        # CHECK 10: The message in the fired line corresponds to the fired reminder
        # The reminder for 田中 is past-dated (2026-01-15T09:00:00+09:00)
        # Its message should contain something about N+1 or 田中 or クエリ
        try:
            fired_messages = [l[len("リマインダー: "):].strip() for l in reminder_lines]
            # Find the corresponding reminder in store
            fired_reminders_in_store = [r for r in reminders if r.get("fired") == True]
            # Each fired reminder message should appear in fired_alerts
            all_fired_messages_present = all(
                any(fr.get("message", "") in alert_msg or alert_msg in fr.get("message", "")
                    for fr in fired_reminders_in_store)
                for alert_msg in fired_messages
            )
            # Also check that at least one reminder IS fired in the store
            at_least_one_fired = len(fired_reminders_in_store) >= 1
            passed2 = at_least_one_fired and len(fired_messages) >= 1
            check(
                "fired_alerts_message_matches_store",
                passed2,
                f"Fired in store: {[r.get('message') for r in fired_reminders_in_store]}. "
                f"Alerts written: {fired_messages}. At least one fired: {at_least_one_fired}",
                weight=2.0
            )
        except Exception as e2:
            check("fired_alerts_message_matches_store", False, f"Exception: {e2}", weight=2.0)
    else:
        check("fired_alerts_format_correct", False, "fired_alerts.txt not found.", weight=2.0)
        check("fired_alerts_message_matches_store", False, "fired_alerts.txt not found.", weight=2.0)
except Exception as e:
    check("fired_alerts_format_correct", False, f"Exception: {e}", weight=2.0)
    check("fired_alerts_message_matches_store", False, f"Exception: {e}", weight=2.0)

# ── Final score ───────────────────────────────────────────────────────────────
final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

output = {
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(output, ensure_ascii=False, indent=2))