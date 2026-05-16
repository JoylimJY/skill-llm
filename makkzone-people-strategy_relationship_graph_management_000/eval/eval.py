#!/usr/bin/env python3
"""
Evaluation script for the People-Strategy consulting team task.
Checks:
1. All 6 people inserted with correct field mappings (role stripped, character, notes)
2. Correct number of unique edges (8, not 9 — duplicate suppressed)
3. Correct relationship directions (reports_to: subordinate→manager)
4. Mentorship edge exists (Carlos→Jordan, type=mentors)
5. works_with edges exist in both directions (Priya↔Sam)
6. network_report.json exists and has correct structure/counts for Carlos Reyes
"""

import sys
import json
import sqlite3
import os
from pathlib import Path

def find_db(workspace: str) -> str | None:
    for p in Path(workspace).rglob("people.db"):
        return str(p)
    return None

def find_report(workspace: str) -> str | None:
    for p in Path(workspace).rglob("network_report.json"):
        return str(p)
    return None

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    weights = {
        "db_exists": 0.05,
        "six_people": 0.10,
        "field_mapping_role": 0.10,
        "field_mapping_character": 0.10,
        "field_mapping_notes": 0.05,
        "edge_count": 0.15,
        "reports_to_direction": 0.10,
        "mentors_edge": 0.10,
        "works_with_bidirectional": 0.10,
        "report_exists": 0.05,
        "report_carlos_connections": 0.10,
    }

    # ── locate DB ────────────────────────────────────────────────────────────
    db_path = find_db(workspace)
    db_ok = db_path is not None
    checks.append({
        "name": "db_exists",
        "passed": db_ok,
        "detail": f"people.db found at: {db_path}" if db_ok else "people.db not found anywhere in workspace"
    })
    if db_ok:
        total_score += weights["db_exists"]

    conn = None
    if db_ok:
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        except Exception as e:
            checks.append({"name": "db_connect", "passed": False, "detail": str(e)})
            conn = None

    # ── 6 people ─────────────────────────────────────────────────────────────
    try:
        if conn:
            rows = conn.execute("SELECT * FROM people ORDER BY id").fetchall()
            people = [dict(r) for r in rows]
            expected_names = {"Diana Osei", "Carlos Reyes", "Priya Nambiar",
                              "Sam Okafor", "Lin Wei", "Jordan Blake"}
            found_names = {p["name"] for p in people}
            ok = expected_names == found_names
            checks.append({
                "name": "six_people",
                "passed": ok,
                "detail": f"Found names: {sorted(found_names)}; expected: {sorted(expected_names)}"
            })
            if ok:
                total_score += weights["six_people"]
        else:
            checks.append({"name": "six_people", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "six_people", "passed": False, "detail": str(e)})

    # ── field mapping: role (whitespace stripped) ─────────────────────────────
    try:
        if conn:
            diana = conn.execute("SELECT * FROM people WHERE name='Diana Osei'").fetchone()
            carlos = conn.execute("SELECT * FROM people WHERE name='Carlos Reyes'").fetchone()
            ok_diana = diana and diana["role"] and diana["role"].strip() == diana["role"] and "Managing Partner" in diana["role"]
            ok_carlos = carlos and carlos["role"] == "Senior Consultant"
            ok = bool(ok_diana and ok_carlos)
            checks.append({
                "name": "field_mapping_role",
                "passed": ok,
                "detail": f"Diana role='{diana['role'] if diana else None}', Carlos role='{carlos['role'] if carlos else None}'"
            })
            if ok:
                total_score += weights["field_mapping_role"]
        else:
            checks.append({"name": "field_mapping_role", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "field_mapping_role", "passed": False, "detail": str(e)})

    # ── field mapping: character (CSV "personality" → DB "character") ─────────
    try:
        if conn:
            diana = conn.execute("SELECT * FROM people WHERE name='Diana Osei'").fetchone()
            ok = diana and diana["character"] and "big-picture" in diana["character"].lower()
            checks.append({
                "name": "field_mapping_character",
                "passed": bool(ok),
                "detail": f"Diana character='{diana['character'] if diana else None}'"
            })
            if ok:
                total_score += weights["field_mapping_character"]
        else:
            checks.append({"name": "field_mapping_character", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "field_mapping_character", "passed": False, "detail": str(e)})

    # ── field mapping: notes (CSV "memo" → DB "notes") ────────────────────────
    try:
        if conn:
            carlos = conn.execute("SELECT * FROM people WHERE name='Carlos Reyes'").fetchone()
            ok = carlos and carlos["notes"] and "mentor" in carlos["notes"].lower()
            checks.append({
                "name": "field_mapping_notes",
                "passed": bool(ok),
                "detail": f"Carlos notes='{carlos['notes'] if carlos else None}'"
            })
            if ok:
                total_score += weights["field_mapping_notes"]
        else:
            checks.append({"name": "field_mapping_notes", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "field_mapping_notes", "passed": False, "detail": str(e)})

    # ── edge count: must be exactly 8 (duplicate suppressed) ─────────────────
    try:
        if conn:
            edge_count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            ok = edge_count == 8
            checks.append({
                "name": "edge_count",
                "passed": ok,
                "detail": f"Found {edge_count} edges; expected 8 (1 duplicate Carlos→Jordan mentors must be suppressed)"
            })
            if ok:
                total_score += weights["edge_count"]
        else:
            checks.append({"name": "edge_count", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "edge_count", "passed": False, "detail": str(e)})

    # ── reports_to direction: Carlos→Diana, Priya→Carlos, Sam→Carlos, Lin→Priya, Jordan→Carlos ──
    try:
        if conn:
            people_map = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM people").fetchall()}
            expected_reports_to = [
                ("Carlos Reyes", "Diana Osei"),
                ("Priya Nambiar", "Carlos Reyes"),
                ("Sam Okafor", "Carlos Reyes"),
                ("Lin Wei", "Priya Nambiar"),
                ("Jordan Blake", "Carlos Reyes"),
            ]
            all_ok = True
            details = []
            for subordinate, manager in expected_reports_to:
                sub_id = people_map.get(subordinate)
                mgr_id = people_map.get(manager)
                if not sub_id or not mgr_id:
                    all_ok = False
                    details.append(f"Missing person: {subordinate} or {manager}")
                    continue
                edge = conn.execute(
                    "SELECT id FROM edges WHERE from_person_id=? AND to_person_id=? AND relationship_type='reports_to'",
                    (sub_id, mgr_id)
                ).fetchone()
                if not edge:
                    all_ok = False
                    details.append(f"Missing reports_to: {subordinate}→{manager}")
                else:
                    details.append(f"OK: {subordinate}→{manager}")
            checks.append({
                "name": "reports_to_direction",
                "passed": all_ok,
                "detail": "; ".join(details)
            })
            if all_ok:
                total_score += weights["reports_to_direction"]
        else:
            checks.append({"name": "reports_to_direction", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "reports_to_direction", "passed": False, "detail": str(e)})

    # ── mentors edge: Carlos→Jordan ───────────────────────────────────────────
    try:
        if conn:
            people_map = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM people").fetchall()}
            carlos_id = people_map.get("Carlos Reyes")
            jordan_id = people_map.get("Jordan Blake")
            edge = conn.execute(
                "SELECT id FROM edges WHERE from_person_id=? AND to_person_id=? AND relationship_type='mentors'",
                (carlos_id, jordan_id)
            ).fetchone() if carlos_id and jordan_id else None
            ok = edge is not None
            checks.append({
                "name": "mentors_edge",
                "passed": ok,
                "detail": f"Carlos→Jordan mentors edge {'found' if ok else 'NOT found'}"
            })
            if ok:
                total_score += weights["mentors_edge"]
        else:
            checks.append({"name": "mentors_edge", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "mentors_edge", "passed": False, "detail": str(e)})

    # ── works_with bidirectional: Priya↔Sam ───────────────────────────────────
    try:
        if conn:
            people_map = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM people").fetchall()}
            priya_id = people_map.get("Priya Nambiar")
            sam_id = people_map.get("Sam Okafor")
            e1 = conn.execute(
                "SELECT id FROM edges WHERE from_person_id=? AND to_person_id=? AND relationship_type='works_with'",
                (priya_id, sam_id)
            ).fetchone() if priya_id and sam_id else None
            e2 = conn.execute(
                "SELECT id FROM edges WHERE from_person_id=? AND to_person_id=? AND relationship_type='works_with'",
                (sam_id, priya_id)
            ).fetchone() if priya_id and sam_id else None
            ok = e1 is not None and e2 is not None
            checks.append({
                "name": "works_with_bidirectional",
                "passed": ok,
                "detail": f"Priya→Sam works_with: {'found' if e1 else 'missing'}; Sam→Priya works_with: {'found' if e2 else 'missing'}"
            })
            if ok:
                total_score += weights["works_with_bidirectional"]
        else:
            checks.append({"name": "works_with_bidirectional", "passed": False, "detail": "No DB connection"})
    except Exception as e:
        checks.append({"name": "works_with_bidirectional", "passed": False, "detail": str(e)})

    # ── network_report.json exists ────────────────────────────────────────────
    report_path = find_report(workspace)
    report_ok = report_path is not None
    checks.append({
        "name": "report_exists",
        "passed": report_ok,
        "detail": f"network_report.json found at: {report_path}" if report_ok else "network_report.json not found"
    })
    if report_ok:
        total_score += weights["report_exists"]

    # ── report: Carlos's network connections count ────────────────────────────
    try:
        if report_ok:
            with open(report_path) as f:
                report = json.load(f)
            # Carlos is connected to: Diana(out), Jordan(out,mentors), Priya(in), Sam(in), Jordan(in from reports_to)
            # Unique connected people: Diana, Jordan, Priya, Sam = 4
            # Accept report["carlos_reyes"] or report["Carlos Reyes"] or top-level connections_count
            carlos_section = None
            for key in report:
                if "carlos" in key.lower():
                    carlos_section = report[key]
                    break
            if carlos_section is None and "person" in report:
                # maybe report IS the network for Carlos
                if report.get("person", {}).get("name", "").lower().startswith("carlos"):
                    carlos_section = report

            connections_count = None
            if carlos_section:
                connections_count = carlos_section.get("connections_count")

            ok = connections_count == 4
            checks.append({
                "name": "report_carlos_connections",
                "passed": ok,
                "detail": f"Carlos connections_count={connections_count}; expected 4 (Diana, Jordan, Priya, Sam)"
            })
            if ok:
                total_score += weights["report_carlos_connections"]
        else:
            checks.append({
                "name": "report_carlos_connections",
                "passed": False,
                "detail": "network_report.json not found"
            })
    except Exception as e:
        checks.append({"name": "report_carlos_connections", "passed": False, "detail": str(e)})

    if conn:
        conn.close()

    passed = total_score >= 0.75
    print(json.dumps({
        "passed": passed,
        "score": round(total_score, 3),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)