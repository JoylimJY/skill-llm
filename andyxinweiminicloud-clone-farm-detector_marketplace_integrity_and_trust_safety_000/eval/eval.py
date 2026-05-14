import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def find_report(workspace):
    """Search for audit_report.json anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("audit_report.json"))
    return candidates[0] if candidates else None

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def run_eval(workspace):
    checks = []

    # ── Find the report ────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if not report_path:
        checks.append(check("report_exists", False, "audit_report.json not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("report_exists", True, f"Found at {report_path}"))

    try:
        report = load_json_file(report_path)
    except Exception as e:
        checks.append(check("report_parseable", False, f"JSON parse error: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_parseable", True, "Valid JSON"))

    # ── Check top-level risk rating ────────────────────────────────────────────
    # Must use FARMING (not HIGH, not FLAGGED, not CRITICAL)
    risk = None
    for key in ["risk_rating", "risk", "overall_risk", "rating", "status"]:
        if key in report:
            risk = str(report[key]).upper()
            break
    # Also search nested
    if risk is None and isinstance(report, dict):
        for v in report.values():
            if isinstance(v, str) and v.upper() in ("FARMING", "SUSPECT", "CLEAN"):
                risk = v.upper()
                break

    farming_detected = risk == "FARMING"
    checks.append(check(
        "risk_rating_is_FARMING",
        farming_detected,
        f"Top-level risk_rating = '{risk}' (expected 'FARMING')"
    ))

    # ── Check clusters are present ─────────────────────────────────────────────
    clusters = None
    for key in ["clusters", "cluster_groups", "clone_clusters", "groups"]:
        if key in report and isinstance(report[key], list):
            clusters = report[key]
            break

    has_clusters = clusters is not None and len(clusters) >= 2
    checks.append(check(
        "at_least_2_clusters",
        has_clusters,
        f"Found {len(clusters) if clusters else 0} cluster(s), need ≥ 2"
    ))

    # ── Cluster A: 4 JSON formatter skills from same node ─────────────────────
    cluster_a_names = {"json-formatter-pro", "json-beautifier-plus", "format-json-fast", "json-style-fixer"}
    cluster_a_found = False
    cluster_a_size_ok = False
    cluster_a_similarity_ok = False
    cluster_a_publisher_ok = False
    cluster_a_technique_ok = False
    cluster_a_id_washing_ok = False

    if clusters:
        for cluster in clusters:
            # Collect skill names in this cluster
            names_in_cluster = set()
            for key in ["skills", "members", "skill_names", "items"]:
                if key in cluster and isinstance(cluster[key], list):
                    for item in cluster[key]:
                        if isinstance(item, str):
                            names_in_cluster.add(item)
                        elif isinstance(item, dict):
                            for nk in ["name", "skill_name", "id"]:
                                if nk in item:
                                    names_in_cluster.add(item[nk])
            
            overlap = cluster_a_names & names_in_cluster
            if len(overlap) >= 3:
                cluster_a_found = True
                cluster_a_size_ok = len(names_in_cluster) >= 3

                # Similarity score >= 0.75
                for sk in ["similarity", "avg_similarity", "average_similarity", "similarity_score"]:
                    if sk in cluster:
                        try:
                            sim = float(cluster[sk])
                            if sim >= 0.75:
                                cluster_a_similarity_ok = True
                        except:
                            pass
                # Also accept percentage form
                if not cluster_a_similarity_ok:
                    for sk in ["similarity", "avg_similarity", "average_similarity", "similarity_score"]:
                        if sk in cluster:
                            try:
                                sim = float(str(cluster[sk]).replace('%',''))
                                if sim >= 75:
                                    cluster_a_similarity_ok = True
                            except:
                                pass

                # Publisher node
                for pk in ["publisher", "publisher_node", "node_id", "publisher_id"]:
                    if pk in cluster and "node_c4f9a1b2e3d0" in str(cluster[pk]):
                        cluster_a_publisher_ok = True

                # Technique: variable rename / comment injection
                technique_str = ""
                for tk in ["technique", "techniques", "method", "detection_method", "evidence"]:
                    if tk in cluster:
                        technique_str += str(cluster[tk]).lower()
                if any(t in technique_str for t in ["variable", "rename", "comment", "inject"]):
                    cluster_a_technique_ok = True

                # ID washing: different hashes, same functional code
                for ik in ["id_washing", "hash_washing", "id_wash", "washing"]:
                    if ik in cluster:
                        val = str(cluster[ik]).lower()
                        if any(x in val for x in ["true", "yes", "detected", "unique hash"]):
                            cluster_a_id_washing_ok = True
                # Also check evidence/notes field
                for ek in ["evidence", "notes", "detail", "details"]:
                    if ek in cluster:
                        ev = str(cluster[ek]).lower()
                        if any(x in ev for x in ["unique hash", "different hash", "id wash", "functional"]):
                            cluster_a_id_washing_ok = True
                break

    checks.append(check("cluster_A_identified", cluster_a_found, f"Cluster with ≥3 JSON-formatter skills found: {cluster_a_found}"))
    checks.append(check("cluster_A_size_correct", cluster_a_size_ok, "Cluster A has ≥3 member skills"))
    checks.append(check("cluster_A_similarity_score", cluster_a_similarity_ok, "Cluster A avg similarity ≥ 0.75"))
    checks.append(check("cluster_A_publisher_node", cluster_a_publisher_ok, "Cluster A publisher identified as node_c4f9a1b2e3d0"))
    checks.append(check("cluster_A_technique_noted", cluster_a_technique_ok, "Technique includes variable rename or comment injection"))
    checks.append(check("cluster_A_id_washing_flagged", cluster_a_id_washing_ok, "ID washing (different SHA-256, same functional code) detected for Cluster A"))

    # ── Cluster B: 3 YAML validator skills with cross-citation rings ──────────
    cluster_b_names = {"yaml-validator-core", "yaml-lint-helper", "yaml-check-tool"}
    cluster_b_found = False
    cluster_b_cross_citation_ok = False
    cluster_b_whitespace_ok = False
    cluster_b_similarity_ok = False

    if clusters:
        for cluster in clusters:
            names_in_cluster = set()
            for key in ["skills", "members", "skill_names", "items"]:
                if key in cluster and isinstance(cluster[key], list):
                    for item in cluster[key]:
                        if isinstance(item, str):
                            names_in_cluster.add(item)
                        elif isinstance(item, dict):
                            for nk in ["name", "skill_name", "id"]:
                                if nk in item:
                                    names_in_cluster.add(item[nk])
            
            overlap = cluster_b_names & names_in_cluster
            if len(overlap) >= 2:
                cluster_b_found = True

                # Cross-citation
                for ck in ["cross_citation", "cross_cites", "citation_ring", "citation", "dependencies"]:
                    if ck in cluster:
                        val = str(cluster[ck]).lower()
                        if any(x in val for x in ["true", "yes", "detected", "ring", "circular", "chain"]):
                            cluster_b_cross_citation_ok = True

                # Also check evidence/notes
                for ek in ["evidence", "notes", "detail", "details", "technique", "techniques"]:
                    if ek in cluster:
                        ev = str(cluster[ek]).lower()
                        if any(x in ev for x in ["cross-cit", "citation ring", "depend", "ring", "circular"]):
                            cluster_b_cross_citation_ok = True
                        if any(x in ev for x in ["whitespace", "blank line", "empty line", "space inject"]):
                            cluster_b_whitespace_ok = True

                # Similarity
                for sk in ["similarity", "avg_similarity", "average_similarity", "similarity_score"]:
                    if sk in cluster:
                        try:
                            sim = float(str(cluster[sk]).replace('%',''))
                            if sim >= 0.75 or (sim >= 75):
                                cluster_b_similarity_ok = True
                        except:
                            pass
                break

    checks.append(check("cluster_B_identified", cluster_b_found, f"Cluster with ≥2 YAML-validator skills found: {cluster_b_found}"))
    checks.append(check("cluster_B_cross_citation_flagged", cluster_b_cross_citation_ok, "Cross-citation ring detected for Cluster B"))
    checks.append(check("cluster_B_whitespace_injection_noted", cluster_b_whitespace_ok, "Whitespace injection technique noted for Cluster B"))
    checks.append(check("cluster_B_similarity_score", cluster_b_similarity_ok, "Cluster B similarity score reported"))

    # ── Suspect skills: csv-row-parser / csv-line-reader ──────────────────────
    suspect_names = {"csv-row-parser", "csv-line-reader"}
    suspect_found = False
    suspect_risk_ok = False

    # Check all clusters for suspect
    if clusters:
        for cluster in clusters:
            names_in_cluster = set()
            for key in ["skills", "members", "skill_names", "items"]:
                if key in cluster and isinstance(cluster[key], list):
                    for item in cluster[key]:
                        if isinstance(item, str):
                            names_in_cluster.add(item)
                        elif isinstance(item, dict):
                            for nk in ["name", "skill_name", "id"]:
                                if nk in item:
                                    names_in_cluster.add(item[nk])
            
            if suspect_names & names_in_cluster:
                suspect_found = True
                for rk in ["risk", "risk_rating", "rating"]:
                    if rk in cluster:
                        if str(cluster[rk]).upper() in ("SUSPECT", "FARMING"):
                            suspect_risk_ok = True
                break

    # Also check a separate "suspect_skills" or "flagged" section
    if not suspect_found:
        for key in ["suspect_skills", "flagged_skills", "suspect", "flagged"]:
            if key in report and isinstance(report[key], list):
                for item in report[key]:
                    item_str = str(item).lower()
                    if "csv" in item_str:
                        suspect_found = True
                        suspect_risk_ok = True
                        break

    checks.append(check("suspect_skills_flagged", suspect_found, "CSV skills identified as suspect/cluster"))
    checks.append(check("suspect_risk_rating_correct", suspect_risk_ok, "CSV skills rated SUSPECT or FARMING"))

    # ── Genuine skills count ───────────────────────────────────────────────────
    genuine_count = None
    for key in ["genuine_skills", "clean_skills", "genuine_count", "clean_count", "genuine"]:
        if key in report:
            try:
                genuine_count = int(report[key])
            except:
                if isinstance(report[key], list):
                    genuine_count = len(report[key])
            break
    
    # Also look for it in a summary section
    if genuine_count is None and "summary" in report and isinstance(report["summary"], dict):
        for key in ["genuine_skills", "clean_skills", "genuine_count", "clean_count", "genuine"]:
            if key in report["summary"]:
                try:
                    genuine_count = int(report["summary"][key])
                except:
                    pass

    genuine_ok = genuine_count == 3
    checks.append(check(
        "genuine_skills_count_correct",
        genuine_ok,
        f"Genuine skills count = {genuine_count} (expected 3: shell-executor, metrics-aggregator, url-extractor)"
    ))

    # ── Batch publish pattern detection ───────────────────────────────────────
    batch_detected = False
    batch_str = json.dumps(report).lower()
    if any(x in batch_str for x in ["batch publish", "batch_publish", "rapid publish", "short time window", 
                                      "same publisher", "time window", "coordinated", "09:0", "11:0", "14:0"]):
        batch_detected = True
    checks.append(check(
        "batch_publish_pattern_noted",
        batch_detected,
        "Report mentions batch publishing pattern (same node, short time window)"
    ))

    # ── Recommendation present ─────────────────────────────────────────────────
    recommendation_present = False
    for key in ["recommendation", "recommendations", "action", "actions"]:
        if key in report and report[key]:
            recommendation_present = True
            break
    if not recommendation_present and "recommendation" in batch_str:
        recommendation_present = True
    checks.append(check(
        "recommendation_present",
        recommendation_present,
        "Report includes a recommendation field"
    ))

    # ── Scoring ────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = round(len(passed_checks) / total_checks, 3)

    # Must pass core checks to overall pass
    critical = [
        "report_exists",
        "risk_rating_is_FARMING",
        "at_least_2_clusters",
        "cluster_A_identified",
        "cluster_B_identified",
        "cluster_B_cross_citation_flagged",
        "cluster_A_id_washing_flagged",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    overall_passed = critical_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))