import sys
import json
import sqlite3
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Locate required output files ──────────────────────────────────────────
    db_path = ws / "projects" / "constellation" / "memory.db"
    report_path = ws / "projects" / "constellation" / "onboarding_report.json"

    # CHECK 1: DB exists at the correct custom path
    db_exists = db_path.exists()
    total_score += add(
        "memory.db at correct custom path",
        db_exists,
        f"Expected {db_path} — {'found' if db_exists else 'NOT FOUND'}",
        weight=1.0
    )

    # CHECK 2: Report JSON exists
    report_exists = report_path.exists()
    total_score += add(
        "onboarding_report.json exists",
        report_exists,
        f"Expected {report_path} — {'found' if report_exists else 'NOT FOUND'}",
        weight=0.5
    )

    report = {}
    if report_exists:
        try:
            report = json.loads(report_path.read_text())
        except Exception as e:
            add("onboarding_report.json is valid JSON", False, str(e), weight=0.5)

    # ── DB-level checks ───────────────────────────────────────────────────────
    if not db_exists:
        # Add failing placeholders for remaining checks
        for name in [
            "entities table has ≥10 rows",
            "persons tracked with correct entity_type",
            "clients tracked with correct entity_type",
            "vendors tracked with correct entity_type",
            "lessons table has 6 rows (all incidents)",
            "negative outcomes stored as 'negative' (not 'FAILED'/'failure')",
            "positive outcomes stored as 'positive' (not 'SUCCESS'/'success')",
            "data_pipeline context lessons present",
            "client_management context lessons present",
        ]:
            checks.append({"name": name, "passed": False, "detail": "DB not found"})
        total_score += 0
    else:
        try:
            conn = sqlite3.connect(str(db_path))

            # CHECK 3: entities count ≥ 10
            entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            total_score += add(
                "entities table has ≥10 rows",
                entity_count >= 10,
                f"Found {entity_count} entities (need ≥10: 6 persons + 2 clients + 2 vendors)",
                weight=1.5
            )

            # CHECK 4: persons tracked
            persons = conn.execute(
                "SELECT name FROM entities WHERE entity_type = 'person'"
            ).fetchall()
            person_names = [r[0] for r in persons]
            expected_persons = ["Amara Osei-Bonsu", "Marcus Delgado", "Priya Nair",
                                 "Lena Krawczyk", "Tom Ridgeway", "Fatima Al-Hassan"]
            # flexible match: check at least 5 of 6 key names appear (partial match ok)
            matched_persons = sum(
                1 for ep in expected_persons
                if any(ep.split()[-1].lower() in pn.lower() for pn in person_names)
            )
            total_score += add(
                "persons tracked with correct entity_type",
                matched_persons >= 5,
                f"Matched {matched_persons}/6 expected persons in entity_type='person'. Found: {person_names}",
                weight=1.5
            )

            # CHECK 5: clients tracked
            clients = conn.execute(
                "SELECT name FROM entities WHERE entity_type = 'client'"
            ).fetchall()
            client_names = [r[0] for r in clients]
            client_ok = (
                any("novatech" in n.lower() for n in client_names) and
                any("meridian" in n.lower() for n in client_names)
            )
            total_score += add(
                "clients tracked with correct entity_type",
                client_ok,
                f"Found client entities: {client_names}",
                weight=1.0
            )

            # CHECK 6: vendors tracked
            vendors = conn.execute(
                "SELECT name FROM entities WHERE entity_type = 'vendor'"
            ).fetchall()
            vendor_names = [r[0] for r in vendors]
            vendor_ok = (
                any("cloudbridge" in n.lower() for n in vendor_names) and
                any("datasense" in n.lower() for n in vendor_names)
            )
            total_score += add(
                "vendors tracked with correct entity_type",
                vendor_ok,
                f"Found vendor entities: {vendor_names}",
                weight=1.0
            )

            # CHECK 7: lessons count == 6
            lesson_count = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
            total_score += add(
                "lessons table has 6 rows (all incidents)",
                lesson_count == 6,
                f"Found {lesson_count} lessons (expected 6)",
                weight=1.5
            )

            # CHECK 8: negative outcomes stored as 'negative' (proprietary trap)
            neg_rows = conn.execute(
                "SELECT outcome FROM lessons WHERE outcome = 'negative'"
            ).fetchall()
            bad_neg = conn.execute(
                "SELECT COUNT(*) FROM lessons WHERE outcome IN ('FAILED','failed','failure','negative_outcome')"
            ).fetchone()[0]
            total_score += add(
                "negative outcomes stored as 'negative' (not 'FAILED'/'failure')",
                len(neg_rows) == 3 and bad_neg == 0,
                f"Rows with outcome='negative': {len(neg_rows)} (expected 3). "
                f"Rows with wrong outcome values: {bad_neg}",
                weight=2.0
            )

            # CHECK 9: positive outcomes stored as 'positive' (proprietary trap)
            pos_rows = conn.execute(
                "SELECT outcome FROM lessons WHERE outcome = 'positive'"
            ).fetchall()
            bad_pos = conn.execute(
                "SELECT COUNT(*) FROM lessons WHERE outcome IN ('SUCCESS','success','positive_outcome')"
            ).fetchone()[0]
            total_score += add(
                "positive outcomes stored as 'positive' (not 'SUCCESS'/'success')",
                len(pos_rows) == 3 and bad_pos == 0,
                f"Rows with outcome='positive': {len(pos_rows)} (expected 3). "
                f"Rows with wrong outcome values: {bad_pos}",
                weight=2.0
            )

            # CHECK 10: data_pipeline context present
            dp_lessons = conn.execute(
                "SELECT COUNT(*) FROM lessons WHERE context = 'data_pipeline'"
            ).fetchone()[0]
            total_score += add(
                "data_pipeline context lessons present",
                dp_lessons >= 3,
                f"Found {dp_lessons} lessons with context='data_pipeline' (expected 3)",
                weight=1.0
            )

            # CHECK 11: client_management context present
            cm_lessons = conn.execute(
                "SELECT COUNT(*) FROM lessons WHERE context = 'client_management'"
            ).fetchone()[0]
            total_score += add(
                "client_management context lessons present",
                cm_lessons >= 2,
                f"Found {cm_lessons} lessons with context='client_management' (expected 2)",
                weight=1.0
            )

            conn.close()

        except Exception as e:
            checks.append({"name": "DB query error", "passed": False, "detail": str(e)})

    # ── Report content checks ─────────────────────────────────────────────────
    if report:
        # CHECK 12: entities_loaded correct
        ent_loaded = report.get("entities_loaded", -1)
        total_score += add(
            "report.entities_loaded ≥ 10",
            isinstance(ent_loaded, int) and ent_loaded >= 10,
            f"report.entities_loaded = {ent_loaded}",
            weight=0.5
        )

        # CHECK 13: lessons_loaded == 6
        les_loaded = report.get("lessons_loaded", -1)
        total_score += add(
            "report.lessons_loaded == 6",
            isinstance(les_loaded, int) and les_loaded == 6,
            f"report.lessons_loaded = {les_loaded}",
            weight=0.5
        )

        # CHECK 14: pipeline_lessons key present with correct data
        pl = report.get("pipeline_lessons", None)
        pl_ok = isinstance(pl, list) and len(pl) >= 3
        total_score += add(
            "report.pipeline_lessons is list of ≥3 items",
            pl_ok,
            f"pipeline_lessons type={type(pl).__name__}, len={len(pl) if isinstance(pl, list) else 'N/A'}",
            weight=0.5
        )

        # CHECK 15: client_mgmt_lessons key present
        cl = report.get("client_mgmt_lessons", None)
        cl_ok = isinstance(cl, list) and len(cl) >= 2
        total_score += add(
            "report.client_mgmt_lessons is list of ≥2 items",
            cl_ok,
            f"client_mgmt_lessons type={type(cl).__name__}, len={len(cl) if isinstance(cl, list) else 'N/A'}",
            weight=0.5
        )
    else:
        for name in [
            "report.entities_loaded ≥ 10",
            "report.lessons_loaded == 6",
            "report.pipeline_lessons is list of ≥3 items",
            "report.client_mgmt_lessons is list of ≥2 items",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Report missing or invalid JSON"})

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_score = 1.0 + 0.5 + 1.5 + 1.5 + 1.0 + 1.0 + 1.5 + 2.0 + 2.0 + 1.0 + 1.0 + 0.5 + 0.5 + 0.5 + 0.5
    # max_score = 16.0
    normalized = round(total_score / max_score, 4)
    passed = normalized >= 0.75

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))