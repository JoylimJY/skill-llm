import sys
import json
import re
from pathlib import Path

def find_schedule_file(workspace: Path):
    candidates = list(workspace.rglob("watch_schedule.md"))
    if not candidates:
        return None
    return candidates[0]

def parse_sections(text: str):
    sections = {}
    # Status
    m = re.search(r'(?m)^Status:\s*(.+)$', text)
    sections['status_line'] = m.group(1).strip() if m else None

    # 24h Plan
    m = re.search(r'(?ms)^24h Plan:\s*\n(.*?)(?=\n[A-Z][^\n]*:|\Z)', text)
    sections['plan_block'] = m.group(1).strip() if m else None

    # Non-negotiables
    m = re.search(r'(?ms)^Non-negotiables:\s*\n(.*?)(?=\n[A-Z][^\n]*:|\Z)', text)
    sections['nonneg_block'] = m.group(1).strip() if m else None

    # Traffic budget
    m = re.search(r'(?ms)^Traffic budget:\s*\n(.*?)(?=\n[A-Z][^\n]*:|\Z)', text)
    sections['traffic_block'] = m.group(1).strip() if m else None

    return sections

def count_bullets(block: str) -> int:
    if not block:
        return 0
    lines = [l.strip() for l in block.splitlines() if l.strip()]
    return sum(1 for l in lines if l.startswith('-') or l.startswith('*') or re.match(r'^\d+\.', l))

def check_plan_bullets(block: str):
    """Returns list of (start, end, action) tuples for HH:MM–HH:MM lines."""
    if not block:
        return []
    pattern = re.compile(r'(\d{2}:\d{2})[–\-—](\d{2}:\d{2})\s*[—\-–]?\s*(.+)')
    return pattern.findall(block)

def check_watch_model_44(entries):
    """
    Check that on-watch blocks alternate correctly for 4/4 model.
    Each watch block should be ~240 minutes.
    """
    on_watch = []
    for start, end, action in entries:
        if 'watch' in action.lower() and 'hand' not in action.lower():
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            dur = (eh * 60 + em) - (sh * 60 + sm)
            if dur < 0:
                dur += 1440
            on_watch.append(dur)
    return on_watch

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # ── 1. File exists ───────────────────────────────────────────────────────
    schedule_file = find_schedule_file(workspace)
    file_exists = schedule_file is not None
    checks.append({
        "name": "watch_schedule.md exists",
        "passed": file_exists,
        "detail": str(schedule_file) if file_exists else "File 'watch_schedule.md' not found anywhere in workspace."
    })
    if not file_exists:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    try:
        text = schedule_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    sections = parse_sections(text)

    # ── 2. All 4 required sections present ──────────────────────────────────
    required = ['status_line', 'plan_block', 'nonneg_block', 'traffic_block']
    labels   = ['Status:', '24h Plan:', 'Non-negotiables:', 'Traffic budget:']
    all_sections_present = True
    for key, label in zip(required, labels):
        present = sections.get(key) is not None
        if not present:
            all_sections_present = False
        checks.append({
            "name": f"Section '{label}' present",
            "passed": present,
            "detail": f"Found: {bool(sections.get(key))}"
        })

    # ── 3. Non-negotiables ≤ 5 bullets ──────────────────────────────────────
    nonneg_count = count_bullets(sections.get('nonneg_block', ''))
    nonneg_ok = 1 <= nonneg_count <= 5
    checks.append({
        "name": "Non-negotiables: 1–5 bullets",
        "passed": nonneg_ok,
        "detail": f"Bullet count: {nonneg_count}"
    })

    # ── 4. 24h Plan has HH:MM–HH:MM format entries ──────────────────────────
    plan_entries = check_plan_bullets(sections.get('plan_block', ''))
    plan_format_ok = len(plan_entries) >= 6
    checks.append({
        "name": "24h Plan has ≥6 timed entries (HH:MM–HH:MM format)",
        "passed": plan_format_ok,
        "detail": f"Found {len(plan_entries)} timed entries."
    })

    # ── 5. Correct watch start: 06:00 (not 08:00 from old template) ─────────
    plan_block = sections.get('plan_block', '') or ''
    has_0600_start = bool(re.search(r'06:00', plan_block))
    checks.append({
        "name": "First watch starts at 06:00 (not legacy 08:00)",
        "passed": has_0600_start,
        "detail": "06:00 found in 24h Plan block." if has_0600_start else "06:00 NOT found; agent may have used legacy 08:00 start."
    })

    # ── 6. Correct watch model: 4/4 (not 6/6 from old template) ────────────
    full_text_lower = text.lower()
    has_44 = bool(re.search(r'4[/\\]4|4-on.*4-off|four.on.*four.off', full_text_lower))
    not_66 = not bool(re.search(r'\b6[/\\]6\b', text))
    watch_model_ok = has_44
    checks.append({
        "name": "4/4 watch model referenced (not 6/6)",
        "passed": watch_model_ok,
        "detail": f"4/4 found: {has_44}. 6/6 found: {not not_66}."
    })

    # ── 7. Internet budget: uses 3 GB/week (not old 4 GB) ───────────────────
    traffic_block = sections.get('traffic_block', '') or ''
    # Correct daily_mb for 3 GB/week: int((3 * 1024) / 7) = 438
    correct_mb = int((3 * 1024) / 7)  # = 438
    wrong_mb   = int((4 * 1024) / 7)  # = 585 (from old contract)
    has_correct_mb = bool(re.search(r'438', traffic_block + text))
    has_wrong_mb   = bool(re.search(r'585', traffic_block))
    budget_correct = has_correct_mb and not has_wrong_mb
    checks.append({
        "name": f"Traffic budget uses 3 GB/week → {correct_mb} MB/day (not 585 from old 4 GB plan)",
        "passed": budget_correct,
        "detail": (
            f"438 MB/day found: {has_correct_mb}. "
            f"585 MB/day (wrong, old plan) found in traffic block: {has_wrong_mb}."
        )
    })

    # ── 8. Low-traffic day mentioned ────────────────────────────────────────
    has_low_traffic_day = bool(re.search(
        r'low.traffic.day|low traffic day|one day.*50\s*mb|50\s*mb.*day',
        full_text_lower
    ))
    checks.append({
        "name": "Low-traffic day (50 MB cap) mentioned in Traffic budget",
        "passed": has_low_traffic_day,
        "detail": "Found 'low-traffic day' / '50 MB' reference." if has_low_traffic_day else "Missing low-traffic day policy."
    })

    # ── 9. Offline-first policy mentioned ────────────────────────────────────
    has_offline_first = bool(re.search(
        r'offline.first|disable autoplay|no cloud sync|no auto.?play',
        full_text_lower
    ))
    checks.append({
        "name": "Offline-first policy mentioned (disable autoplay / no cloud sync)",
        "passed": has_offline_first,
        "detail": "Found offline-first language." if has_offline_first else "Missing offline-first policy."
    })

    # ── 10. Safety anchors: handover checklist mentioned ─────────────────────
    has_handover = bool(re.search(
        r'handover|hand.over|watch transfer|watch handover',
        full_text_lower
    ))
    checks.append({
        "name": "Safety anchor: start-of-watch handover checklist referenced",
        "passed": has_handover,
        "detail": "Handover checklist found." if has_handover else "No handover checklist reference."
    })

    # ── 11. Safety scans (2–4/day) mentioned ─────────────────────────────────
    has_safety_scan = bool(re.search(
        r'safety scan|safety check|horizon sweep|instrument check',
        full_text_lower
    ))
    checks.append({
        "name": "Safety scans mentioned in plan",
        "passed": has_safety_scan,
        "detail": "Safety scan language found." if has_safety_scan else "Safety scans not mentioned."
    })

    # ── 12. EOD log mentioned ─────────────────────────────────────────────────
    has_eod = bool(re.search(
        r'eod log|end.of.day log|daily log|log line|log entry',
        full_text_lower
    ))
    checks.append({
        "name": "End-of-day log line mentioned",
        "passed": has_eod,
        "detail": "EOD log found." if has_eod else "EOD log not found."
    })

    # ── 13. Sleep protection: no heavy tasks after fragmented sleep ───────────
    has_sleep_protection = bool(re.search(
        r'no.*cogni|avoid.*heavy.*after.*sleep|fragmented sleep|heavy task.*after.*sleep|cognitively.*after|no.*heavy.*after.*broken',
        full_text_lower
    ))
    checks.append({
        "name": "Sleep protection rule: no heavy cognitive tasks after fragmented sleep",
        "passed": has_sleep_protection,
        "detail": "Sleep protection language found." if has_sleep_protection else "Missing sleep/cognitive protection rule."
    })

    # ── 14. Timezone: America/Los_Angeles referenced ──────────────────────────
    has_tz = bool(re.search(
        r'america/los_angeles|los_angeles|pacific.*time|PDT|PST|pacific standard|pacific daylight',
        text,
        re.IGNORECASE
    ))
    checks.append({
        "name": "Correct timezone (America/Los_Angeles / Pacific) referenced",
        "passed": has_tz,
        "detail": "Pacific timezone found." if has_tz else "Timezone America/Los_Angeles not found — agent may have used Europe/Vilnius default or Europe/London legacy."
    })

    # ── 15. Sleep block ≥ 6h total present in plan ───────────────────────────
    sleep_minutes = 0
    for start, end, action in plan_entries:
        if re.search(r'sleep|rest|off.watch', action, re.IGNORECASE):
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            dur = (eh * 60 + em) - (sh * 60 + sm)
            if dur < 0:
                dur += 1440
            sleep_minutes += dur
    sleep_ok = sleep_minutes >= 360
    checks.append({
        "name": "≥6h sleep/rest in 24h plan",
        "passed": sleep_ok,
        "detail": f"Total sleep/rest minutes found: {sleep_minutes} (need ≥360)."
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)

    # Hard gates: file must exist, all 4 sections present, correct MB, correct start time
    hard_gates = [
        "watch_schedule.md exists",
        f"Traffic budget uses 3 GB/week → {correct_mb} MB/day (not 585 from old 4 GB plan)",
        "First watch starts at 06:00 (not legacy 08:00)",
        "4/4 watch model referenced (not 6/6)",
    ]
    hard_gate_passed = all(
        any(c["name"] == g and c["passed"] for c in checks)
        for g in hard_gates
    )

    overall_passed = hard_gate_passed and score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()