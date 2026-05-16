#!/usr/bin/env python3
"""
Evaluation script for the memory health-score task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ── Locate health-score.json ─────────────────────────────────────────────
    candidates = list(workspace.rglob("health-score.json"))
    if not candidates:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "health-score.json not found anywhere in workspace"}]
        }))
        return

    # Use the most recently modified one if multiple exist
    hsfile = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

    # ── Parse JSON ───────────────────────────────────────────────────────────
    try:
        data = json.loads(hsfile.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "json_parseable", "passed": False,
                        "detail": f"Cannot parse health-score.json: {e}"}]
        }))
        return

    # ── CHECK 1: Top-level structure ─────────────────────────────────────────
    required_keys = {"timestamp", "totalScore", "grade", "dimensions", "recommendations"}
    missing = required_keys - set(data.keys())
    c1_pass = len(missing) == 0
    checks.append({
        "name": "top_level_structure",
        "passed": c1_pass,
        "detail": f"Missing keys: {missing}" if missing else "All top-level keys present"
    })
    if c1_pass:
        total_score += 5

    # ── CHECK 2: totalScore == 60 ────────────────────────────────────────────
    try:
        ts = int(data["totalScore"])
        c2_pass = ts == 60
        checks.append({
            "name": "total_score_correct",
            "passed": c2_pass,
            "detail": f"totalScore={ts}, expected 60"
        })
        if c2_pass:
            total_score += 30
    except Exception as e:
        checks.append({"name": "total_score_correct", "passed": False,
                       "detail": f"Cannot read totalScore: {e}"})

    # ── CHECK 3: grade == "警告" ─────────────────────────────────────────────
    try:
        grade = data["grade"]
        c3_pass = grade == "警告"
        checks.append({
            "name": "grade_correct",
            "passed": c3_pass,
            "detail": f"grade='{grade}', expected '警告' (50-69 band)"
        })
        if c3_pass:
            total_score += 15
    except Exception as e:
        checks.append({"name": "grade_correct", "passed": False,
                       "detail": f"Cannot read grade: {e}"})

    # ── CHECK 4: dimensions present and correctly structured ─────────────────
    expected_dims = {"completeness", "freshness", "structure", "density", "consistency"}
    try:
        dims = data["dimensions"]
        dim_keys = set(dims.keys())
        missing_dims = expected_dims - dim_keys
        c4_pass = len(missing_dims) == 0
        checks.append({
            "name": "dimensions_structure",
            "passed": c4_pass,
            "detail": f"Missing dimensions: {missing_dims}" if missing_dims else
                      "All 5 dimensions present"
        })
        if c4_pass:
            total_score += 5
    except Exception as e:
        dims = {}
        checks.append({"name": "dimensions_structure", "passed": False,
                       "detail": f"Cannot read dimensions: {e}"})

    # ── CHECK 5: completeness score == 25, max == 30 ─────────────────────────
    try:
        comp = dims.get("completeness", {})
        cs = int(comp.get("score", -1))
        cm = int(comp.get("max", -1))
        c5_pass = cs == 25 and cm == 30
        checks.append({
            "name": "completeness_score",
            "passed": c5_pass,
            "detail": f"completeness score={cs}/max={cm}, expected 25/30 "
                      "(MEMORY.md✓10 + INDEX✓5 + 7-day logs✓10 + P0 usage✗0)"
        })
        if c5_pass:
            total_score += 8
    except Exception as e:
        checks.append({"name": "completeness_score", "passed": False,
                       "detail": f"Cannot read completeness: {e}"})

    # ── CHECK 6: freshness score == 10, max == 25 ───────────────────────────
    try:
        fresh = dims.get("freshness", {})
        fs = int(fresh.get("score", -1))
        fm = int(fresh.get("max", -1))
        c6_pass = fs == 10 and fm == 25
        checks.append({
            "name": "freshness_score",
            "passed": c6_pass,
            "detail": f"freshness score={fs}/max={fm}, expected 10/25 "
                      "(today log✗0 + MEMORY 7-day✓10 + INDEX 3-day✗0)"
        })
        if c6_pass:
            total_score += 8
    except Exception as e:
        checks.append({"name": "freshness_score", "passed": False,
                       "detail": f"Cannot read freshness: {e}"})

    # ── CHECK 7: structure score == 15, max == 20 ────────────────────────────
    try:
        struct = dims.get("structure", {})
        ss = int(struct.get("score", -1))
        sm = int(struct.get("max", -1))
        c7_pass = ss == 15 and sm == 20
        checks.append({
            "name": "structure_score",
            "passed": c7_pass,
            "detail": f"structure score={ss}/max={sm}, expected 15/20 "
                      "(.issues exists✓10 + open issues✗0 + heartbeat✓5)"
        })
        if c7_pass:
            total_score += 8
    except Exception as e:
        checks.append({"name": "structure_score", "passed": False,
                       "detail": f"Cannot read structure: {e}"})

    # ── CHECK 8: density score == 10, max == 15 ──────────────────────────────
    try:
        dens = dims.get("density", {})
        ds = int(dens.get("score", -1))
        dm = int(dens.get("max", -1))
        c8_pass = ds == 10 and dm == 15
        checks.append({
            "name": "density_score",
            "passed": c8_pass,
            "detail": f"density score={ds}/max={dm}, expected 10/15 "
                      "(MEMORY.md 480 lines in 50-500✓10 + log avg <20 lines✗0)"
        })
        if c8_pass:
            total_score += 8
    except Exception as e:
        checks.append({"name": "density_score", "passed": False,
                       "detail": f"Cannot read density: {e}"})

    # ── CHECK 9: consistency score == 0, max == 10 ───────────────────────────
    try:
        cons = dims.get("consistency", {})
        ccs = int(cons.get("score", -1))
        ccm = int(cons.get("max", -1))
        c9_pass = ccs == 0 and ccm == 10
        checks.append({
            "name": "consistency_score",
            "passed": c9_pass,
            "detail": f"consistency score={ccs}/max={ccm}, expected 0/10 "
                      "(INDEX↔MEMORY mismatch✗0 + issue-099 missing✗0)"
        })
        if c9_pass:
            total_score += 8
    except Exception as e:
        checks.append({"name": "consistency_score", "passed": False,
                       "detail": f"Cannot read consistency: {e}"})

    # ── CHECK 10: each dimension has "issues" list ───────────────────────────
    try:
        all_have_issues = all(
            isinstance(dims.get(d, {}).get("issues"), list)
            for d in expected_dims
        )
        checks.append({
            "name": "dimension_issues_lists",
            "passed": all_have_issues,
            "detail": "All dimensions have 'issues' lists" if all_have_issues else
                      "Some dimensions missing 'issues' key or it's not a list"
        })
        if all_have_issues:
            total_score += 3
    except Exception as e:
        checks.append({"name": "dimension_issues_lists", "passed": False,
                       "detail": f"Error checking issues lists: {e}"})

    # ── CHECK 11: recommendations is a non-empty list ────────────────────────
    try:
        recs = data.get("recommendations", [])
        c11_pass = isinstance(recs, list) and len(recs) >= 1
        checks.append({
            "name": "recommendations_present",
            "passed": c11_pass,
            "detail": f"recommendations has {len(recs)} items" if isinstance(recs, list)
                      else "recommendations is not a list"
        })
        if c11_pass:
            total_score += 2
    except Exception as e:
        checks.append({"name": "recommendations_present", "passed": False,
                       "detail": f"Error reading recommendations: {e}"})

    # ── CHECK 12: timestamp field exists and looks like ISO-8601 ─────────────
    try:
        ts_val = data.get("timestamp", "")
        # Accept any ISO-8601-ish string with date portion
        c12_pass = bool(re.match(r'\d{4}-\d{2}-\d{2}', str(ts_val)))
        checks.append({
            "name": "timestamp_format",
            "passed": c12_pass,
            "detail": f"timestamp='{ts_val}'" + ("" if c12_pass else " — expected ISO-8601 format")
        })
        if c12_pass:
            total_score += 2
    except Exception as e:
        checks.append({"name": "timestamp_format", "passed": False,
                       "detail": f"Error reading timestamp: {e}"})

    # ── CHECK 13: completeness issues mention P0 ─────────────────────────────
    try:
        comp_issues = dims.get("completeness", {}).get("issues", [])
        mentions_p0 = any("P0" in str(i) or "p0" in str(i).lower() for i in comp_issues)
        checks.append({
            "name": "completeness_issues_mention_p0",
            "passed": mentions_p0,
            "detail": f"completeness.issues={comp_issues}; expected mention of P0 shortage"
        })
        if mentions_p0:
            total_score += 2
    except Exception as e:
        checks.append({"name": "completeness_issues_mention_p0", "passed": False,
                       "detail": f"Error: {e}"})

    # ── CHECK 14: freshness issues mention both today-log AND INDEX.md ───────
    try:
        fresh_issues = dims.get("freshness", {}).get("issues", [])
        fresh_text = " ".join(str(i).lower() for i in fresh_issues)
        mentions_today = any(
            kw in fresh_text for kw in ["今日", "today", "log", "日志"]
        )
        mentions_index = any(
            kw in fresh_text for kw in ["index", "索引"]
        )
        c14_pass = mentions_today and mentions_index
        checks.append({
            "name": "freshness_issues_complete",
            "passed": c14_pass,
            "detail": f"freshness.issues={fresh_issues}; "
                      f"mentions today-log={mentions_today}, mentions INDEX={mentions_index}"
        })
        if c14_pass:
            total_score += 2
    except Exception as e:
        checks.append({"name": "freshness_issues_complete", "passed": False,
                       "detail": f"Error: {e}"})

    # ── Normalise total_score to 0-100 ───────────────────────────────────────
    max_possible = 5+30+15+5+8+8+8+8+8+3+2+2+2+2
    normalised = round((total_score / max_possible) * 100, 1)

    # Passing threshold: must get totalScore right AND grade right AND
    # at least 4 of the 5 dimension scores correct
    critical_pass = (
        any(c["name"] == "total_score_correct" and c["passed"] for c in checks) and
        any(c["name"] == "grade_correct" and c["passed"] for c in checks)
    )
    dim_score_checks = [
        c for c in checks
        if c["name"] in {"completeness_score", "freshness_score", "structure_score",
                         "density_score", "consistency_score"}
    ]
    dims_passed = sum(1 for c in dim_score_checks if c["passed"])

    passed = critical_pass and dims_passed >= 4

    print(json.dumps({
        "passed": passed,
        "score": normalised,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()