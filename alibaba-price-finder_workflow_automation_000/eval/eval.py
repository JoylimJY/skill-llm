import sys
import json
import csv
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def find_output_file(workspace):
    candidates = list(Path(workspace).rglob("sourcing_urls.json"))
    return candidates[0] if candidates else None

def evaluate(workspace):
    checks = []
    
    # --- Locate output file ---
    output_path = find_output_file(workspace)
    if not output_path:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "sourcing_urls.json not found anywhere in workspace"}]
        }
    checks.append({"name": "output_file_exists", "passed": True, "detail": str(output_path)})

    # --- Parse JSON ---
    try:
        with open(output_path) as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.05,
            "checks": checks + [{"name": "json_parseable", "passed": False, "detail": str(e)}]
        }
    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})

    # Expected requirements and their rules:
    # REQ-001: Wireless Earbuds, priceMin=2, priceMax=15, moqMax=500, sort=cheapest first (orderBy=9999)
    # REQ-002: LED Strip Lights, no price filter, sort=most expensive first (orderBy=9998)
    # REQ-003: phone case, priceMin=1, priceMax=5, moqMax=100, no sort
    # REQ-004: Bamboo Cutting Board, priceMin=3, priceMax=20, no moq, sort=cheapest first (orderBy=9999)
    # REQ-005: USB C Cable, priceMin=0.5, priceMax=8, moqMax=200, no sort
    # REQ-006: Portable Bluetooth Speaker, no price filter, no moq, sort=cheapest first (orderBy=9999)
    # REQ-007: Silicone Watch Band, priceMin=1, priceMax=10, moqMax=50, sort=most expensive first (orderBy=9998)

    # The output must be a dict keyed by req_id, each with a 'url' field (or similar structure)
    # We'll be flexible on the top-level structure but strict on URL contents.

    def extract_urls(data):
        """Try to extract a dict of req_id -> url from various possible structures."""
        if isinstance(data, dict):
            # Could be {req_id: url_string} or {req_id: {url: ...}} or {results: [...]}
            result = {}
            for k, v in data.items():
                if isinstance(v, str) and v.startswith("http"):
                    result[k] = v
                elif isinstance(v, dict):
                    for subk, subv in v.items():
                        if isinstance(subv, str) and subv.startswith("http"):
                            result[k] = subv
                            break
            if result:
                return result
            # Try list-of-dicts under a key
            for k, v in data.items():
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict):
                            req_id = item.get("req_id") or item.get("id")
                            url = item.get("url") or item.get("search_url") or item.get("link")
                            if req_id and url:
                                result[req_id] = url
                    if result:
                        return result
        elif isinstance(data, list):
            result = {}
            for item in data:
                if isinstance(item, dict):
                    req_id = item.get("req_id") or item.get("id")
                    url = item.get("url") or item.get("search_url") or item.get("link")
                    if req_id and url:
                        result[req_id] = url
            return result
        return {}

    url_map = extract_urls(data)
    if not url_map:
        checks.append({"name": "urls_extractable", "passed": False, "detail": f"Could not extract req_id->url mapping from JSON structure: {str(data)[:300]}"})
        return {"passed": False, "score": 0.1, "checks": checks}
    checks.append({"name": "urls_extractable", "passed": True, "detail": f"Found {len(url_map)} URLs"})

    def parse_url_params(url):
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            # parse_qs returns lists; flatten single values
            return {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        except Exception:
            return {}

    def check_url(req_id, url, checks_local):
        params = parse_url_params(url)
        passed_all = True

        # 1. Must contain traffic_type=ags_llm
        has_tracking = params.get("traffic_type") == "ags_llm"
        checks_local.append({
            "name": f"{req_id}_has_traffic_type_ags_llm",
            "passed": has_tracking,
            "detail": f"traffic_type={params.get('traffic_type', 'MISSING')} | URL: {url}"
        })
        if not has_tracking:
            passed_all = False

        # 2. Must be alibaba.com search URL
        is_alibaba = "alibaba.com" in url and "trade/search" in url
        checks_local.append({
            "name": f"{req_id}_is_alibaba_search_url",
            "passed": is_alibaba,
            "detail": url
        })
        if not is_alibaba:
            passed_all = False

        # 3. SearchText must be present and reflect the product
        has_searchtext = "SearchText" in params
        checks_local.append({
            "name": f"{req_id}_has_SearchText",
            "passed": has_searchtext,
            "detail": f"SearchText={params.get('SearchText', 'MISSING')}"
        })
        if not has_searchtext:
            passed_all = False

        return passed_all

    # Per-requirement checks
    req_rules = {
        "REQ-001": {
            "product_keywords": ["wireless", "earbuds"],
            "priceMin": "2", "priceMax": "15",
            "moqMax": "500",
            "orderBy": "9999",  # cheapest first = low to high
        },
        "REQ-002": {
            "product_keywords": ["led", "strip"],
            "priceMin": None, "priceMax": None,
            "moqMax": None,
            "orderBy": "9998",  # most expensive first = high to low
        },
        "REQ-003": {
            "product_keywords": ["phone", "case"],
            "priceMin": "1", "priceMax": "5",
            "moqMax": "100",
            "orderBy": None,  # no sort preference
        },
        "REQ-004": {
            "product_keywords": ["bamboo", "cutting"],
            "priceMin": "3", "priceMax": "20",
            "moqMax": None,
            "orderBy": "9999",  # cheapest first
        },
        "REQ-005": {
            "product_keywords": ["usb", "cable"],
            "priceMin": "0.5", "priceMax": "8",
            "moqMax": "200",
            "orderBy": None,
        },
        "REQ-006": {
            "product_keywords": ["bluetooth", "speaker"],
            "priceMin": None, "priceMax": None,
            "moqMax": None,
            "orderBy": "9999",  # cheapest first
        },
        "REQ-007": {
            "product_keywords": ["silicone", "watch"],
            "priceMin": "1", "priceMax": "10",
            "moqMax": "50",
            "orderBy": "9998",  # most expensive first
        },
    }

    req_scores = []

    for req_id, rules in req_rules.items():
        url = url_map.get(req_id)
        if not url:
            checks.append({"name": f"{req_id}_url_present", "passed": False, "detail": f"No URL found for {req_id} in output"})
            req_scores.append(0.0)
            continue

        checks.append({"name": f"{req_id}_url_present", "passed": True, "detail": url})
        params = parse_url_params(url)
        req_pass_count = 0
        req_total = 0

        # Base URL checks
        base_ok = check_url(req_id, url, checks)

        # SearchText contains product keywords
        search_text = params.get("SearchText", "").lower().replace("+", " ").replace("%20", " ")
        keywords_found = all(kw in search_text for kw in rules["product_keywords"])
        checks.append({
            "name": f"{req_id}_searchtext_keywords",
            "passed": keywords_found,
            "detail": f"SearchText='{search_text}', expected keywords: {rules['product_keywords']}"
        })

        # priceMin check
        req_total += 1
        if rules["priceMin"] is not None:
            actual = params.get("priceMin")
            ok = actual == rules["priceMin"]
            checks.append({"name": f"{req_id}_priceMin", "passed": ok, "detail": f"priceMin={actual}, expected={rules['priceMin']}"})
            if ok: req_pass_count += 1
        else:
            ok = "priceMin" not in params
            checks.append({"name": f"{req_id}_no_priceMin", "passed": ok, "detail": f"priceMin should be absent, got: {params.get('priceMin', 'ABSENT')}"})
            if ok: req_pass_count += 1

        # priceMax check
        req_total += 1
        if rules["priceMax"] is not None:
            actual = params.get("priceMax")
            ok = actual == rules["priceMax"]
            checks.append({"name": f"{req_id}_priceMax", "passed": ok, "detail": f"priceMax={actual}, expected={rules['priceMax']}"})
            if ok: req_pass_count += 1
        else:
            ok = "priceMax" not in params
            checks.append({"name": f"{req_id}_no_priceMax", "passed": ok, "detail": f"priceMax should be absent, got: {params.get('priceMax', 'ABSENT')}"})
            if ok: req_pass_count += 1

        # moqMax check
        req_total += 1
        if rules["moqMax"] is not None:
            actual = params.get("moqMax")
            ok = actual == rules["moqMax"]
            checks.append({"name": f"{req_id}_moqMax", "passed": ok, "detail": f"moqMax={actual}, expected={rules['moqMax']}"})
            if ok: req_pass_count += 1
        else:
            ok = "moqMax" not in params
            checks.append({"name": f"{req_id}_no_moqMax", "passed": ok, "detail": f"moqMax should be absent, got: {params.get('moqMax', 'ABSENT')}"})
            if ok: req_pass_count += 1

        # orderBy check (this is the key proprietary trap: 9999 vs 9998)
        req_total += 1
        if rules["orderBy"] is not None:
            actual = params.get("orderBy")
            ok = actual == rules["orderBy"]
            checks.append({
                "name": f"{req_id}_orderBy",
                "passed": ok,
                "detail": f"orderBy={actual}, expected={rules['orderBy']} ({'cheapest first' if rules['orderBy']=='9999' else 'most expensive first'})"
            })
            if ok: req_pass_count += 1
        else:
            ok = "orderBy" not in params
            checks.append({"name": f"{req_id}_no_orderBy", "passed": ok, "detail": f"orderBy should be absent, got: {params.get('orderBy', 'ABSENT')}"})
            if ok: req_pass_count += 1

        # traffic_type check counts toward score
        req_total += 1
        tt_ok = params.get("traffic_type") == "ags_llm"
        if tt_ok: req_pass_count += 1

        # Keywords count toward score
        req_total += 1
        if keywords_found: req_pass_count += 1

        req_score = req_pass_count / req_total if req_total > 0 else 0.0
        req_scores.append(req_score)

    # Overall scoring
    total_score = sum(req_scores) / len(req_scores) if req_scores else 0.0

    # Must pass: all traffic_type checks (proprietary trap), all orderBy checks
    critical_checks = [c for c in checks if "traffic_type" in c["name"] or "orderBy" in c["name"]]
    critical_passed = all(c["passed"] for c in critical_checks)
    # Also require at least 70% overall
    overall_passed = total_score >= 0.70 and critical_passed

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))