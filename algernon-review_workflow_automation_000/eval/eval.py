#!/usr/bin/env python3
"""
Evaluation script for the algernon-review FSRS task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import sqlite3
import math
import os
from pathlib import Path
from datetime import date, datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
ALGERNON_HOME = workspace / "algernon_home"
DB_PATH = ALGERNON_HOME / "data" / "study.db"
TODAY = date.today().isoformat()

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

def approx_equal(a, b, tol=0.05):
    """Allow 5% relative tolerance for floating-point FSRS calculations."""
    if b == 0:
        return abs(a) < tol
    return abs(a - b) / abs(b) < tol

# ── Connect to DB ─────────────────────────────────────────────────────────────
try:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
except Exception as e:
    add_check("database_connection", False, f"Could not connect to DB: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 1: Card 1 FSRS update (review+Good, elapsed≈5, S=4.0, D=0.35)
# Expected:
#   R = EXP(LN(0.9)*5/4) ≈ 0.87673
#   new_S = 4.0 * EXP(0.9*(1-0.87673)) ≈ 4.4693
#   new_D = MAX(0.1, 0.35-0.05) = 0.30
#   state = 'review', interval = MAX(1, ROUND(4.4693)) = 4
#   lapses unchanged = 0
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT stability, difficulty, state, lapses, reps, due_date
        FROM card_state WHERE card_id = 1
    """)
    row = cur.fetchone()
    if row is None:
        add_check("card1_state_update", False, "card_state row for card_id=1 not found")
    else:
        expected_s = 4.0 * math.exp(0.9 * (1 - math.exp(math.log(0.9) * 5.0 / 4.0)))
        expected_d = 0.30
        expected_interval = max(1, round(expected_s))  # = 4
        expected_due = (datetime.strptime(TODAY, "%Y-%m-%d") + 
                       __import__('datetime').timedelta(days=expected_interval)).strftime("%Y-%m-%d")

        s_ok = approx_equal(row["stability"], expected_s, tol=0.05)
        d_ok = approx_equal(row["difficulty"], expected_d, tol=0.02)
        state_ok = row["state"] == "review"
        lapses_ok = row["lapses"] == 0
        reps_ok = row["reps"] >= 4  # incremented from 3

        passed = s_ok and d_ok and state_ok and lapses_ok and reps_ok
        detail = (f"stability={row['stability']:.4f}(exp≈{expected_s:.4f}) "
                  f"difficulty={row['difficulty']:.4f}(exp=0.30) "
                  f"state={row['state']}(exp=review) "
                  f"lapses={row['lapses']}(exp=0) reps={row['reps']}")
        add_check("card1_fsrs_review_good", passed, detail)
except Exception as e:
    add_check("card1_fsrs_review_good", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 2: Card 1 review record inserted
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("SELECT grade, scheduled_days, elapsed_days FROM reviews WHERE card_id=1")
    rows = cur.fetchall()
    if not rows:
        add_check("card1_review_record", False, "No review record found for card_id=1")
    else:
        row = rows[-1]  # most recent
        grade_ok = row["grade"] == 3
        sched_ok = row["scheduled_days"] == max(1, round(
            4.0 * math.exp(0.9 * (1 - math.exp(math.log(0.9) * 5.0 / 4.0)))))
        detail = f"grade={row['grade']}(exp=3) scheduled_days={row['scheduled_days']}(exp=4)"
        add_check("card1_review_record", grade_ok and sched_ok, detail)
except Exception as e:
    add_check("card1_review_record", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 3: Card 2 FSRS update (new+Again)
# Expected: new_S=0.1, new_D=0.4, state=learning, interval=1, lapses=0
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT stability, difficulty, state, lapses, reps, due_date
        FROM card_state WHERE card_id = 2
    """)
    row = cur.fetchone()
    if row is None:
        add_check("card2_fsrs_new_again", False, "card_state row for card_id=2 not found")
    else:
        s_ok = approx_equal(row["stability"], 0.1, tol=0.02)
        d_ok = approx_equal(row["difficulty"], 0.4, tol=0.02)
        state_ok = row["state"] == "learning"
        lapses_ok = row["lapses"] == 0  # lapses only increment on review+Again
        reps_ok = row["reps"] >= 1
        # interval=1, due_date=tomorrow
        from datetime import timedelta
        expected_due = (datetime.strptime(TODAY, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        due_ok = row["due_date"] == expected_due

        passed = s_ok and d_ok and state_ok and lapses_ok and reps_ok and due_ok
        detail = (f"stability={row['stability']:.4f}(exp=0.1) "
                  f"difficulty={row['difficulty']:.4f}(exp=0.4) "
                  f"state={row['state']}(exp=learning) "
                  f"lapses={row['lapses']}(exp=0) "
                  f"due_date={row['due_date']}(exp={expected_due})")
        add_check("card2_fsrs_new_again", passed, detail)
except Exception as e:
    add_check("card2_fsrs_new_again", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 4: Correction card created for card 2's misconception
# Expected: type='flashcard', tags contains '[correction]' AND '[N1]',
#           due_date=today, deck_id matches card 2's deck (deck_id=2)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT c.id, c.deck_id, c.type, c.front, c.back, c.tags, cs.due_date
        FROM cards c
        JOIN card_state cs ON cs.card_id = c.id
        WHERE c.tags LIKE '%[correction]%'
        AND c.id > 5
    """)
    correction_rows = cur.fetchall()
    if not correction_rows:
        add_check("correction_card_created", False,
                  "No correction card found (expected a card with '[correction]' in tags)")
    else:
        row = correction_rows[0]
        tags_str = row["tags"]
        has_correction = "[correction]" in tags_str
        has_n1 = "[N1]" in tags_str
        type_ok = row["type"] == "flashcard"
        due_ok = row["due_date"] == TODAY
        deck_ok = row["deck_id"] == 2  # card 2 is in deck 2
        front_nonempty = len(str(row["front"]).strip()) > 0
        back_nonempty = len(str(row["back"]).strip()) > 0

        passed = has_correction and has_n1 and type_ok and due_ok and deck_ok and front_nonempty and back_nonempty
        detail = (f"tags={tags_str} type={row['type']} due_date={row['due_date']}(exp={TODAY}) "
                  f"deck_id={row['deck_id']}(exp=2) front_ok={front_nonempty} back_ok={back_nonempty}")
        add_check("correction_card_created", passed, detail)
except Exception as e:
    add_check("correction_card_created", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 5: Card 3 FSRS update (learning+Good, S=0.3, D=0.35)
# Expected: new_S=0.45, new_D=0.30, state=review, interval=MAX(1,ROUND(0.45))=1
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT stability, difficulty, state, lapses, reps, due_date
        FROM card_state WHERE card_id = 3
    """)
    row = cur.fetchone()
    if row is None:
        add_check("card3_fsrs_learning_good", False, "card_state row for card_id=3 not found")
    else:
        expected_s = 0.3 * 1.5  # = 0.45
        expected_d = max(0.1, 0.35 - 0.05)  # = 0.30
        expected_interval = max(1, round(expected_s))  # ROUND(0.45)=0 in most impls, MAX(1,0)=1
        # Note: Python round(0.45)=0 (banker's rounding), but some impls get 1.
        # We allow interval of 1 either way.

        s_ok = approx_equal(row["stability"], expected_s, tol=0.02)
        d_ok = approx_equal(row["difficulty"], expected_d, tol=0.02)
        state_ok = row["state"] == "review"
        lapses_ok = row["lapses"] == 0
        reps_ok = row["reps"] >= 3

        from datetime import timedelta
        expected_due_1 = (datetime.strptime(TODAY, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        due_ok = row["due_date"] == expected_due_1

        passed = s_ok and d_ok and state_ok and lapses_ok and reps_ok and due_ok
        detail = (f"stability={row['stability']:.4f}(exp=0.45) "
                  f"difficulty={row['difficulty']:.4f}(exp=0.30) "
                  f"state={row['state']}(exp=review) "
                  f"due={row['due_date']}(exp={expected_due_1})")
        add_check("card3_fsrs_learning_good", passed, detail)
except Exception as e:
    add_check("card3_fsrs_learning_good", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 6: Card 4 FSRS update (review+Good, elapsed≈9, S=10.0, D=0.20)
# Expected:
#   R = EXP(LN(0.9)*9/10) ≈ 0.90953
#   new_S = 10.0 * EXP(0.9*(1-0.90953)) ≈ 10.848
#   new_D = MAX(0.1, 0.20-0.05) = 0.15
#   state=review, interval=MAX(1,ROUND(10.848))=11
#   lapses unchanged = 1 (not changed on Good)
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT stability, difficulty, state, lapses, reps, due_date
        FROM card_state WHERE card_id = 4
    """)
    row = cur.fetchone()
    if row is None:
        add_check("card4_fsrs_review_good", False, "card_state row for card_id=4 not found")
    else:
        elapsed = 9.0
        R = math.exp(math.log(0.9) * elapsed / 10.0)
        expected_s = 10.0 * math.exp(0.9 * (1 - R))
        expected_d = max(0.1, 0.20 - 0.05)  # = 0.15
        expected_interval = max(1, round(expected_s))  # = 11

        s_ok = approx_equal(row["stability"], expected_s, tol=0.05)
        d_ok = approx_equal(row["difficulty"], expected_d, tol=0.02)
        state_ok = row["state"] == "review"
        lapses_ok = row["lapses"] == 1  # unchanged from original
        reps_ok = row["reps"] >= 6  # incremented from 5

        from datetime import timedelta
        expected_due = (datetime.strptime(TODAY, "%Y-%m-%d") + 
                       timedelta(days=expected_interval)).strftime("%Y-%m-%d")
        due_ok = row["due_date"] == expected_due

        passed = s_ok and d_ok and state_ok and lapses_ok and reps_ok and due_ok
        detail = (f"stability={row['stability']:.4f}(exp≈{expected_s:.4f}) "
                  f"difficulty={row['difficulty']:.4f}(exp=0.15) "
                  f"state={row['state']}(exp=review) "
                  f"lapses={row['lapses']}(exp=1) reps={row['reps']}(exp>=6) "
                  f"due={row['due_date']}(exp={expected_due})")
        add_check("card4_fsrs_review_good", passed, detail)
except Exception as e:
    add_check("card4_fsrs_review_good", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 7: N2 promotion card created for Card 4 (deck_id=2, reps>=5, [N1], retention>=0.9)
# Expected: new card in deck 2, type='flashcard', tags contain '[N2]', due_date=today
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT c.id, c.deck_id, c.type, c.front, c.back, c.tags, cs.due_date
        FROM cards c
        JOIN card_state cs ON cs.card_id = c.id
        WHERE c.tags LIKE '%[N2]%'
        AND c.deck_id = 2
        AND c.id > 5
    """)
    n2_rows = cur.fetchall()
    if not n2_rows:
        add_check("n2_promotion_card_created", False,
                  "No N2 promotion card found in deck 2 (expected card with '[N2]' tag due today)")
    else:
        row = n2_rows[0]
        has_n2 = "[N2]" in row["tags"]
        due_ok = row["due_date"] == TODAY
        deck_ok = row["deck_id"] == 2
        front_nonempty = len(str(row["front"]).strip()) > 10
        back_nonempty = len(str(row["back"]).strip()) > 10

        passed = has_n2 and due_ok and deck_ok and front_nonempty and back_nonempty
        detail = (f"tags={row['tags']} due_date={row['due_date']}(exp={TODAY}) "
                  f"deck_id={row['deck_id']}(exp=2) "
                  f"front_len={len(str(row['front']))} back_len={len(str(row['back']))}")
        add_check("n2_promotion_card_created", passed, detail)
except Exception as e:
    add_check("n2_promotion_card_created", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 8: reviews table has entries for all 4 reviewed cards
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("""
        SELECT card_id, grade FROM reviews 
        WHERE card_id IN (1,2,3,4) 
        AND reviewed_at >= date('now')
    """)
    review_rows = cur.fetchall()
    reviewed_cards = {r["card_id"] for r in review_rows}
    grades_by_card = {r["card_id"]: r["grade"] for r in review_rows}

    # We need at least cards 1,2,3,4 to have review records today
    # Some may have been pre-seeded; check that grades match expected
    cur.execute("""
        SELECT card_id, grade, COUNT(*) as cnt FROM reviews 
        WHERE card_id IN (1,2,3,4)
        GROUP BY card_id
    """)
    all_reviews = {r["card_id"]: r["grade"] for r in cur.fetchall()}

    missing = {1, 2, 3, 4} - set(all_reviews.keys())
    grade_ok = (all_reviews.get(1) == 3 and 
                all_reviews.get(2) == 1 and
                all_reviews.get(3) == 3 and
                all_reviews.get(4) == 3)

    passed = len(missing) == 0 and grade_ok
    detail = f"reviewed_cards={set(all_reviews.keys())} grades={all_reviews} missing={missing}"
    add_check("reviews_table_populated", passed, detail)
except Exception as e:
    add_check("reviews_table_populated", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 9: Session summary log appended to conversations/YYYY-MM-DD.md
# ═══════════════════════════════════════════════════════════════════════════════
try:
    conv_dir = ALGERNON_HOME / "memory" / "conversations"
    log_file = conv_dir / f"{TODAY}.md"
    if not log_file.exists():
        # Also check if agent wrote to a different date file
        all_logs = list(conv_dir.glob("*.md"))
        if all_logs:
            add_check("session_log_appended", False,
                      f"Log file {log_file} not found. Found: {[f.name for f in all_logs]}")
        else:
            add_check("session_log_appended", False,
                      f"No conversation log files found in {conv_dir}")
    else:
        content = log_file.read_text()
        # Check for key session summary fields: "review session", cards reviewed, retention
        has_review = "review" in content.lower()
        has_cards = "card" in content.lower() or any(str(n) in content for n in range(1,10))
        has_retention = "%" in content or "retention" in content.lower()

        passed = has_review and has_cards
        detail = (f"File found: {log_file.name} | "
                  f"has_review={has_review} has_cards={has_cards} has_retention={has_retention} | "
                  f"content_preview={content[:200].strip()!r}")
        add_check("session_log_appended", passed, detail)
except Exception as e:
    add_check("session_log_appended", False, f"Exception: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# CHECK 10: Card 4 lapses NOT incremented (review+Good should NOT increase lapses)
# This is a TRAP: agents might increment lapses on any grade
# ═══════════════════════════════════════════════════════════════════════════════
try:
    cur.execute("SELECT lapses FROM card_state WHERE card_id=4")
    row = cur.fetchone()
    if row is None:
        add_check("card4_lapses_unchanged", False, "card_state row for card_id=4 not found")
    else:
        passed = row["lapses"] == 1  # started at 1, should NOT change on Good
        detail = f"lapses={row['lapses']}(exp=1, must not increment on review+Good)"
        add_check("card4_lapses_unchanged", passed, detail)
except Exception as e:
    add_check("card4_lapses_unchanged", False, f"Exception: {e}")

conn.close()

# ── Final scoring ─────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / total if total > 0 else 0.0
overall_passed = score >= 0.75  # Need at least 75% of checks to pass

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))