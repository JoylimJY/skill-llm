import sys
import json
import sqlite3
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    db_path = Path(workspace) / "gtm-system" / "data" / "gtm.db"

    def fail(name, detail):
        checks.append({"name": name, "passed": False, "detail": detail})

    def ok(name, detail):
        checks.append({"name": name, "passed": True, "detail": detail})

    if not db_path.exists():
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "db_exists", "passed": False, "detail": f"Database not found at {db_path}"}]
        }
        print(json.dumps(result))
        return

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "db_connect", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        return

    # ── CHECK 1: Contact "Jordan Mehta" exists ─────────────────────────────────
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE name LIKE '%Jordan Mehta%' OR name LIKE '%jordan%mehta%'"
        ).fetchone()
        if row:
            correct_company = (row["company"] or "").lower() == "vertex systems"
            correct_role = "infrastructure" in (row["role"] or "").lower()
            correct_email = "jordan.mehta@vertexsystems.io" in (row["email"] or "").lower()
            if correct_company and correct_role and correct_email:
                ok("contact_jordan_mehta", f"Found: id={row['id']} company='{row['company']}' role='{row['role']}' email='{row['email']}'")
            else:
                fail("contact_jordan_mehta",
                     f"Contact exists but fields wrong: company='{row['company']}' role='{row['role']}' email='{row['email']}'")
        else:
            fail("contact_jordan_mehta", "No contact found with name matching 'Jordan Mehta'")
    except Exception as e:
        fail("contact_jordan_mehta", f"Exception: {e}")

    # ── CHECK 2: Opportunity for Vertex Systems exists with priority 5 ──────────
    jordan_id = None
    vertex_opp_id = None
    try:
        row = conn.execute(
            "SELECT * FROM contacts WHERE name LIKE '%Jordan%' AND name LIKE '%Mehta%'"
        ).fetchone()
        if row:
            jordan_id = row["id"]

        opp_row = conn.execute(
            "SELECT * FROM opportunities WHERE company LIKE '%Vertex%' ORDER BY id"
        ).fetchone()
        if opp_row:
            vertex_opp_id = opp_row["id"]
            correct_priority = opp_row["priority"] == 5
            correct_contact = (opp_row["contact_id"] == jordan_id) if jordan_id else False
            desc_ok = "evaluat" in (opp_row["description"] or "").lower() or "batch" in (opp_row["description"] or "").lower()
            details = f"id={vertex_opp_id} priority={opp_row['priority']} contact_id={opp_row['contact_id']} desc_ok={desc_ok}"
            if correct_priority and correct_contact:
                ok("opportunity_vertex_systems", details)
            else:
                fail("opportunity_vertex_systems",
                     f"Opportunity exists but: priority={opp_row['priority']} (expected 5), "
                     f"contact_id={opp_row['contact_id']} (expected {jordan_id}). {details}")
        else:
            fail("opportunity_vertex_systems", "No opportunity found for 'Vertex Systems'")
    except Exception as e:
        fail("opportunity_vertex_systems", f"Exception: {e}")

    # ── CHECK 3: Stage is exactly "evaluation" ─────────────────────────────────
    try:
        if vertex_opp_id:
            opp_row = conn.execute(
                "SELECT stage FROM opportunities WHERE id=?", (vertex_opp_id,)
            ).fetchone()
            if opp_row:
                stage = opp_row["stage"]
                if stage == "evaluation":
                    ok("stage_evaluation", f"Stage correctly set to 'evaluation'")
                else:
                    fail("stage_evaluation",
                         f"Stage is '{stage}' but expected exactly 'evaluation' "
                         f"(valid stages: awareness/interest/evaluation/negotiation/closed_won/closed_lost)")
            else:
                fail("stage_evaluation", f"Could not fetch stage for opp_id={vertex_opp_id}")
        else:
            fail("stage_evaluation", "Cannot check stage — Vertex Systems opportunity not found")
    except Exception as e:
        fail("stage_evaluation", f"Exception: {e}")

    # ── CHECK 4: Interaction logged for Vertex opp ─────────────────────────────
    try:
        if vertex_opp_id:
            rows = conn.execute(
                "SELECT * FROM interactions WHERE opportunity_id=?", (vertex_opp_id,)
            ).fetchall()
            if rows:
                notes_combined = " ".join(r["notes"] or "" for r in rows).lower()
                has_trial = "trial" in notes_combined or "bacalhau" in notes_combined or "cluster" in notes_combined
                if has_trial:
                    ok("interaction_logged", f"Interaction logged with relevant content. notes_preview='{rows[0]['notes'][:80]}'")
                else:
                    fail("interaction_logged",
                         f"Interaction found but content doesn't mention trial/cluster/bacalhau. "
                         f"Got: '{rows[0]['notes'][:100]}'")
            else:
                fail("interaction_logged", f"No interactions found for opportunity_id={vertex_opp_id}")
        else:
            fail("interaction_logged", "Cannot check interaction — Vertex Systems opportunity not found")
    except Exception as e:
        fail("interaction_logged", f"Exception: {e}")

    # ── CHECK 5: Reminder set for Vertex opp with date 2024-03-01 ─────────────
    try:
        if vertex_opp_id:
            rows = conn.execute(
                "SELECT * FROM reminders WHERE opportunity_id=?", (vertex_opp_id,)
            ).fetchall()
            if rows:
                matching = [r for r in rows if "2024-03-01" in (r["due_date"] or "")]
                if matching:
                    r = matching[0]
                    desc_ok = "pric" in (r["description"] or "").lower() or "proposal" in (r["description"] or "").lower()
                    if desc_ok:
                        ok("reminder_set", f"Reminder with due=2024-03-01 and pricing content found.")
                    else:
                        fail("reminder_set",
                             f"Reminder with 2024-03-01 found but description missing 'pricing/proposal'. "
                             f"Got: '{r['description']}'")
                else:
                    dates = [r["due_date"] for r in rows]
                    fail("reminder_set", f"Reminder(s) exist for opp but none with due_date=2024-03-01. Found dates: {dates}")
            else:
                fail("reminder_set", f"No reminders found for opportunity_id={vertex_opp_id}")
        else:
            fail("reminder_set", "Cannot check reminder — Vertex Systems opportunity not found")
    except Exception as e:
        fail("reminder_set", f"Exception: {e}")

    # ── CHECK 6: Keyword "wasm-compute" with category=domain and weight=2.5 ────
    try:
        row = conn.execute(
            "SELECT * FROM keywords WHERE keyword = 'wasm-compute'"
        ).fetchone()
        if row:
            correct_category = (row["category"] or "").lower() == "domain"
            correct_weight = abs(float(row["weight"]) - 2.5) < 0.01
            if correct_category and correct_weight:
                ok("keyword_wasm_compute",
                   f"Keyword 'wasm-compute' found: category='{row['category']}' weight={row['weight']}")
            else:
                fail("keyword_wasm_compute",
                     f"Keyword exists but: category='{row['category']}' (expected 'domain'), "
                     f"weight={row['weight']} (expected 2.5)")
        else:
            # Check for close matches
            all_kw = [r["keyword"] for r in conn.execute("SELECT keyword FROM keywords").fetchall()]
            fail("keyword_wasm_compute",
                 f"Keyword 'wasm-compute' not found. Existing keywords: {all_kw}")
    except Exception as e:
        fail("keyword_wasm_compute", f"Exception: {e}")

    # ── CHECK 7: All signals processed ────────────────────────────────────────
    try:
        unprocessed = conn.execute(
            "SELECT COUNT(*) as cnt FROM signals WHERE processed=0"
        ).fetchone()["cnt"]
        total = conn.execute("SELECT COUNT(*) as cnt FROM signals").fetchone()["cnt"]
        processed = conn.execute(
            "SELECT COUNT(*) as cnt FROM signals WHERE processed=1"
        ).fetchone()["cnt"]
        if unprocessed == 0 and total > 0:
            ok("all_signals_processed",
               f"All {total} signals are processed (0 unprocessed). "
               f"Crawl must have run and all signals marked done.")
        elif total == 0:
            fail("all_signals_processed", "No signals in DB at all — crawl was never run.")
        else:
            fail("all_signals_processed",
                 f"{unprocessed} unprocessed signal(s) remain out of {total} total. "
                 f"Processed: {processed}. All signals must be marked processed.")
    except Exception as e:
        fail("all_signals_processed", f"Exception: {e}")

    conn.close()

    # ── Scoring ────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_count / total_checks, 4) if total_checks else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)