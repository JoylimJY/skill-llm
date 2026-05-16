import json
import math
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

workspace = Path(sys.argv[1])
db_path = workspace / "memory_db.json"
archive_path = workspace / "MEMORY.md"

checks = []
score_weights = []

def check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_weights.append((passed, weight))

# ── Load DB ───────────────────────────────────────────────────────────────────
try:
    with open(db_path) as f:
        db = json.load(f)
    memories = db["memories"]
except Exception as e:
    check("db_readable", False, f"Could not read memory_db.json: {e}", 2.0)
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

check("db_readable", True, "memory_db.json is valid JSON", 0.5)

# Helper
def find_memory(mid):
    for m in memories:
        if m["id"] == mid:
            return m
    return None

def compute_strength(last_reviewed_iso: str, stability: float) -> float:
    last = datetime.fromisoformat(last_reviewed_iso)
    now  = datetime.now(timezone.utc)
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    days = (now - last).total_seconds() / 86400
    return math.exp(-days / stability)

# ── CHECK 1: Item #1 (CPD-417) must have been REVIEWED ────────────────────────
# After review: strength=1.0, stability=1.5 (was 1.0), review_count >= 1
try:
    m1 = find_memory(1)
    if m1 is None:
        check("item1_reviewed_exists", False, "Item #1 not found in DB", 2.0)
    else:
        status_ok = m1.get("status", "active") == "active"
        # Stability must be 1.5 (was 1.0, reviewed once => ×1.5)
        stability_ok = abs(m1.get("stability", 0) - 1.5) < 0.01
        # strength should be ~1.0 (freshly reviewed) or close (time may have elapsed slightly)
        current_strength = compute_strength(m1["last_reviewed"], m1["stability"])
        strength_ok = current_strength >= 0.9  # recently reviewed
        review_count_ok = m1.get("review_count", 0) >= 1

        all_ok = status_ok and stability_ok and strength_ok and review_count_ok
        detail = (f"status={m1.get('status')}, stability={m1.get('stability'):.4f} (expect 1.5), "
                  f"current_strength={current_strength:.4f} (expect >=0.9), "
                  f"review_count={m1.get('review_count')}")
        check("item1_reviewed_correctly", all_ok, detail, 2.0)
except Exception as e:
    check("item1_reviewed_correctly", False, f"Exception: {e}", 2.0)

# ── CHECK 2: Item #2 or #3 must have been ARCHIVED ────────────────────────────
# The task says archive one fading item. Acceptable: #2 or #3 archived.
# We check that at least one of them has status="archived" AND appears in MEMORY.md
try:
    m2 = find_memory(2)
    m3 = find_memory(3)
    archived_ids = []
    if m2 and m2.get("status") == "archived":
        archived_ids.append(2)
    if m3 and m3.get("status") == "archived":
        archived_ids.append(3)

    at_least_one_archived_in_db = len(archived_ids) > 0

    # Check MEMORY.md exists and contains the archived item's content
    archive_ok = False
    archive_detail = "MEMORY.md not found"
    if archive_path.exists():
        archive_content = archive_path.read_text()
        for aid in archived_ids:
            m = find_memory(aid)
            if m and m["content"][:30] in archive_content:
                archive_ok = True
                archive_detail = f"Item #{aid} found in MEMORY.md"
                break
        if not archive_ok and archived_ids:
            archive_detail = f"Items {archived_ids} archived in DB but content not in MEMORY.md"
    else:
        if at_least_one_archived_in_db:
            archive_detail = "Status archived in DB but MEMORY.md missing"

    db_check = at_least_one_archived_in_db
    detail = f"archived_in_db={archived_ids}, archive_file_ok={archive_ok}. {archive_detail}"
    check("fading_item_archived_in_db", db_check, detail, 1.5)
    check("fading_item_archived_in_file", archive_ok, archive_detail, 1.5)
except Exception as e:
    check("fading_item_archived", False, f"Exception: {e}", 3.0)

# ── CHECK 3: One fading item must have been DELETED (forgotten) ───────────────
# Among items #1, #2, #3 — one should be completely gone from DB
# (Already checked #1 is reviewed, so we look for #2 or #3 deleted)
try:
    # Which fading items are completely absent from DB?
    deleted_ids = []
    for mid in [2, 3]:
        if find_memory(mid) is None:
            deleted_ids.append(mid)

    # Also check: could be that one of 2/3 is archived and the other is deleted
    # Acceptable: exactly one of {2,3} archived, other deleted OR one deleted
    all_fading_ids = {2, 3}
    archived_set = set(archived_ids) if 'archived_ids' in dir() else set()
    deleted_set = set(deleted_ids)

    # At minimum, one item from {2,3} must be deleted
    one_deleted = len(deleted_set) >= 1
    detail = f"Deleted IDs from fading set {{2,3}}: {deleted_ids}"
    check("fading_item_forgotten", one_deleted, detail, 2.0)
except Exception as e:
    check("fading_item_forgotten", False, f"Exception: {e}", 2.0)

# ── CHECK 4: Item #4 (🟡 Decaying, FDA meeting) must remain UNTOUCHED ─────────
# It was decaying, not fading — should still be active and NOT reviewed/deleted
try:
    m4 = find_memory(4)
    if m4 is None:
        check("item4_untouched", False, "Item #4 was deleted — should not have been touched (was 🟡 Decaying)", 1.0)
    else:
        still_active = m4.get("status", "active") == "active"
        # stability should remain 2.0 (not reviewed again) — allow small tolerance
        stability_unchanged = abs(m4.get("stability", 0) - 2.0) < 0.01
        # review_count should remain 2
        review_count_unchanged = m4.get("review_count", 0) == 2
        all_ok = still_active and stability_unchanged and review_count_unchanged
        detail = (f"status={m4.get('status')}, stability={m4.get('stability')} (expect 2.0), "
                  f"review_count={m4.get('review_count')} (expect 2)")
        check("item4_untouched", all_ok, detail, 1.0)
except Exception as e:
    check("item4_untouched", False, f"Exception: {e}", 1.0)

# ── CHECK 5: Item #5 (🟢 Active) must remain untouched ───────────────────────
try:
    m5 = find_memory(5)
    if m5 is None:
        check("item5_untouched", False, "Item #5 was deleted — should not have been touched (was 🟢 Active)", 1.0)
    else:
        still_active = m5.get("status", "active") == "active"
        stability_ok = abs(m5.get("stability", 0) - 1.0) < 0.01
        detail = f"status={m5.get('status')}, stability={m5.get('stability')} (expect 1.0)"
        check("item5_untouched", still_active and stability_ok, detail, 1.0)
except Exception as e:
    check("item5_untouched", False, f"Exception: {e}", 1.0)

# ── CHECK 6: Heartbeat output should be HEARTBEAT_OK ─────────────────────────
# After cleanup: #1 reviewed (🟢), #4 decaying (🟡), #5 active (🟢)
# If no 🔴 items remain and at least #4 is 🟡, heartbeat should NOT print HEARTBEAT_OK
# Actually per spec: "Only 🟡 items → log silently, no interruption" — heartbeat still doesn't print HEARTBEAT_OK
# "All 🟢 → output HEARTBEAT_OK"
# So if #4 is still 🟡 decaying, we get SILENT output (not HEARTBEAT_OK).
# If agent also reviewed #4, then all remaining are 🟢 and HEARTBEAT_OK is printed.
# The task says clean up FADING items, so 🟡 items are fine to keep.
# We test: no 🔴 fading alerts in heartbeat output.
try:
    result = subprocess.run(
        ["python3", "scripts/ebbinghaus.py", "heartbeat"],
        capture_output=True, text=True, cwd=str(workspace), timeout=15
    )
    output = result.stdout.strip()
    # Must NOT contain fading alert (no 🔴 items should remain active)
    no_fading_alert = "ATTENTION REQUIRED" not in output and "🔴" not in output
    heartbeat_clean = no_fading_alert
    detail = f"heartbeat output: {repr(output[:200])}"
    check("heartbeat_no_fading_alerts", heartbeat_clean, detail, 2.0)
    # Bonus: HEARTBEAT_OK if all remaining are 🟢
    heartbeat_ok = "HEARTBEAT_OK" in output
    check("heartbeat_ok_bonus", heartbeat_ok, f"HEARTBEAT_OK present: {heartbeat_ok} | output={repr(output[:100])}", 0.5)
except Exception as e:
    check("heartbeat_no_fading_alerts", False, f"Exception running heartbeat: {e}", 2.0)

# ── CHECK 7: A new memory item was added (the task includes "add a finding") ──
# The prompt asks to also log a new research note. next_id should be > 6.
try:
    new_items = [m for m in memories if m["id"] >= 6 and m.get("status", "active") == "active"]
    added_new = len(new_items) >= 1
    detail = f"New items added (id>=6): {[m['id'] for m in new_items]}"
    check("new_memory_item_added", added_new, detail, 1.5)
    if added_new:
        # Check it has a proper category
        has_category = any(m.get("category", "general") in ["project","tech","person","event","general"] for m in new_items)
        check("new_item_has_valid_category", has_category,
              f"Categories: {[m.get('category') for m in new_items]}", 0.5)
except Exception as e:
    check("new_memory_item_added", False, f"Exception: {e}", 1.5)

# ── Score Calculation ─────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_weights)
earned_weight = sum(w for passed, w in score_weights if passed)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
passed_overall = score >= 0.75 and checks[1]["passed"]  # must get item1 reviewed correctly

print(json.dumps({
    "passed": passed_overall,
    "score": score,
    "checks": checks
}, indent=2))