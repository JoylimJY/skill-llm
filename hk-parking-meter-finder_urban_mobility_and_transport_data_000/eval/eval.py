import json
import sys
import os
from pathlib import Path

def main(workspace):
    workspace = Path(workspace)
    checks = []
    total_score = 0.0

    # ── 1. Find parking_results.json ─────────────────────────────────────────
    result_files = list(workspace.rglob("parking_results.json"))
    file_found = len(result_files) > 0
    checks.append({
        "name": "parking_results.json exists",
        "passed": file_found,
        "detail": f"Found at {result_files[0]}" if file_found else "File not found anywhere in workspace."
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    result_path = result_files[0]

    # ── 2. Valid JSON ─────────────────────────────────────────────────────────
    try:
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        valid_json = True
        checks.append({"name": "parking_results.json is valid JSON", "passed": True, "detail": "Parsed successfully."})
        total_score += 0.15
    except Exception as e:
        checks.append({"name": "parking_results.json is valid JSON", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── 3. Query contains 火炭 keywords ───────────────────────────────────────
    try:
        query = data.get("query", [])
        query_str = " ".join(query) if isinstance(query, list) else str(query)
        has_fotan_kw = any(kw in query_str for kw in ["火炭", "Fo Tan", "fo tan", "火炭站"])
        checks.append({
            "name": "Query includes 火炭/Fo Tan keyword",
            "passed": has_fotan_kw,
            "detail": f"query field: {query_str}"
        })
        if has_fotan_kw:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "Query includes 火炭/Fo Tan keyword", "passed": False, "detail": str(e)})

    # ── 4. matched == True ────────────────────────────────────────────────────
    try:
        matched = data.get("matched", False)
        checks.append({
            "name": "Results contain matched=True (spaces found)",
            "passed": bool(matched),
            "detail": f"matched={matched}"
        })
        if matched:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "Results contain matched=True", "passed": False, "detail": str(e)})

    # ── 5. Clusters present ───────────────────────────────────────────────────
    try:
        clusters = data.get("clusters", [])
        has_clusters = isinstance(clusters, list) and len(clusters) > 0
        checks.append({
            "name": "clusters array is non-empty",
            "passed": has_clusters,
            "detail": f"{len(clusters)} cluster(s) found."
        })
        if has_clusters:
            total_score += 0.10
    except Exception as e:
        clusters = []
        checks.append({"name": "clusters array is non-empty", "passed": False, "detail": str(e)})

    # ── 6. All clusters have vacant > 0 (--vacant-only was used) ─────────────
    try:
        if clusters:
            all_vacant = all(c.get("vacant", 0) > 0 for c in clusters)
            checks.append({
                "name": "All clusters have vacant > 0 (--vacant-only flag was applied)",
                "passed": all_vacant,
                "detail": f"Vacant values: {[c.get('vacant', 0) for c in clusters]}"
            })
            if all_vacant:
                total_score += 0.20
        else:
            checks.append({
                "name": "All clusters have vacant > 0 (--vacant-only flag was applied)",
                "passed": False,
                "detail": "No clusters to check."
            })
    except Exception as e:
        checks.append({"name": "All clusters have vacant > 0", "passed": False, "detail": str(e)})

    # ── 7. Clusters are from 火炭/Fo Tan area ─────────────────────────────────
    try:
        fo_tan_clusters = [
            c for c in clusters
            if "火炭" in str(c.get("subdistrict_zh", "")) or
               "Fo Tan" in str(c.get("subdistrict_en", "")) or
               "火炭" in str(c.get("street_zh", ""))
        ]
        correct_area = len(fo_tan_clusters) > 0
        checks.append({
            "name": "Clusters reference 火炭/Fo Tan area",
            "passed": correct_area,
            "detail": f"{len(fo_tan_clusters)} Fo Tan cluster(s) among {len(clusters)} total."
        })
        if correct_area:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "Clusters reference 火炭/Fo Tan area", "passed": False, "detail": str(e)})

    # ── 8. Clusters contain required fields (street_en, street_zh, maps_link, vehicle_type) ──
    try:
        required_fields = ["street_en", "street_zh", "maps_link", "vehicle_type", "total_spaces", "occupied", "vacant"]
        if clusters:
            first = clusters[0]
            missing = [f for f in required_fields if f not in first]
            has_all_fields = len(missing) == 0
            checks.append({
                "name": "Cluster objects have required fields (street_en, street_zh, maps_link, etc.)",
                "passed": has_all_fields,
                "detail": f"Missing: {missing}" if missing else "All required fields present."
            })
            if has_all_fields:
                total_score += 0.10
        else:
            checks.append({"name": "Cluster objects have required fields", "passed": False, "detail": "No clusters."})
    except Exception as e:
        checks.append({"name": "Cluster objects have required fields", "passed": False, "detail": str(e)})

    # ── 9. maps_link contains google.com/maps ─────────────────────────────────
    try:
        if clusters:
            maps_links_ok = all("google.com/maps" in str(c.get("maps_link", "")) for c in clusters)
            checks.append({
                "name": "maps_link fields contain valid Google Maps URL",
                "passed": maps_links_ok,
                "detail": f"Sample: {clusters[0].get('maps_link', 'N/A')}"
            })
            if maps_links_ok:
                total_score += 0.10
        else:
            checks.append({"name": "maps_link fields contain valid Google Maps URL", "passed": False, "detail": "No clusters."})
    except Exception as e:
        checks.append({"name": "maps_link fields valid", "passed": False, "detail": str(e)})

    # ── Final pass/fail ───────────────────────────────────────────────────────
    score = round(min(total_score, 1.0), 3)
    passed = score >= 0.70

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace arg", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    main(sys.argv[1])