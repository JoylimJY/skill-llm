import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # ---- Find the output file ----
    workspace = Path(workspace_dir)
    candidates = list(workspace.rglob("japan_itinerary_zhangwei.md"))
    
    file_found = len(candidates) > 0
    checks.append({
        "name": "Output file japan_itinerary_zhangwei.md exists",
        "passed": file_found,
        "detail": f"Found at: {candidates[0]}" if file_found else "File not found anywhere in workspace"
    })
    
    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    
    try:
        content = candidates[0].read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "File readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "File readable", "passed": True, "detail": f"File size: {len(content)} chars"})
    
    # ---- Check 1: Powered by flyai brand tag ----
    has_brand = bool(re.search(r'[Pp]owered\s+by\s+flyai', content, re.IGNORECASE))
    checks.append({
        "name": "Brand tag 'Powered by flyai' present",
        "passed": has_brand,
        "detail": "Found 'Powered by flyai'" if has_brand else "Missing required brand tag"
    })
    
    # ---- Check 2: Visa information present (from fliggy-fast-search) ----
    has_visa = bool(re.search(r'[Vv]isa|签证', content))
    checks.append({
        "name": "Visa information included",
        "passed": has_visa,
        "detail": "Visa section found" if has_visa else "No visa information found"
    })
    
    # ---- Check 3: Visa has a booking/detail link from CLI output ----
    visa_link = bool(re.search(r'fliggy\.com/visa.*ref=flyai_mock_001', content))
    checks.append({
        "name": "Visa info has CLI-sourced booking link",
        "passed": visa_link,
        "detail": "Found fliggy.com/visa link from CLI" if visa_link else "Missing CLI-sourced visa link (must use fliggy-fast-search output)"
    })
    
    # ---- Check 4: Outbound flight from CLI (Beijing → Tokyo) ----
    has_outbound_flight = bool(re.search(r'CA181|NH906', content))
    checks.append({
        "name": "Outbound flight from CLI (Beijing→Tokyo CA181 or NH906)",
        "passed": has_outbound_flight,
        "detail": "Found outbound flight from CLI" if has_outbound_flight else "Missing outbound flight — must run search-flight with origin=Beijing"
    })
    
    # ---- Check 5: Outbound flight has booking link ----
    has_outbound_link = bool(re.search(r'fliggy\.com/flight/(CA181|NH906)/PEK-NRT', content))
    checks.append({
        "name": "Outbound flight has CLI-sourced booking link",
        "passed": has_outbound_link,
        "detail": "Found flight booking link" if has_outbound_link else "Missing CLI-sourced flight booking link"
    })
    
    # ---- Check 6: Return flight from CLI (Osaka → Beijing) ----
    has_return_flight = bool(re.search(r'MU524|JL822', content))
    checks.append({
        "name": "Return flight from CLI (Osaka→Beijing MU524 or JL822)",
        "passed": has_return_flight,
        "detail": "Found return flight from CLI" if has_return_flight else "Missing return flight — must run search-flight with destination=Beijing"
    })
    
    # ---- Check 7: Return flight has booking link ----
    has_return_link = bool(re.search(r'fliggy\.com/flight/(MU524|JL822)/KIX-PEK', content))
    checks.append({
        "name": "Return flight has CLI-sourced booking link",
        "passed": has_return_link,
        "detail": "Found return flight booking link" if has_return_link else "Missing CLI-sourced return flight booking link"
    })
    
    # ---- Check 8: Tokyo hotel from CLI ----
    has_tokyo_hotel = bool(re.search(r'Shinjuku Grand Hotel|Akihabara Tech Inn', content, re.IGNORECASE))
    checks.append({
        "name": "Tokyo hotel from CLI output present",
        "passed": has_tokyo_hotel,
        "detail": "Found Tokyo hotel from CLI" if has_tokyo_hotel else "Missing Tokyo hotel — must run search-hotels --dest-name Tokyo"
    })
    
    # ---- Check 9: Tokyo hotel has booking link ----
    has_tokyo_hotel_link = bool(re.search(r'fliggy\.com/hotel/(shinjuku-grand-tokyo|akihabara-tech-inn)', content))
    checks.append({
        "name": "Tokyo hotel has CLI-sourced booking link",
        "passed": has_tokyo_hotel_link,
        "detail": "Found Tokyo hotel booking link" if has_tokyo_hotel_link else "Missing CLI-sourced hotel booking link for Tokyo"
    })
    
    # ---- Check 10: Osaka hotel from CLI ----
    has_osaka_hotel = bool(re.search(r'Namba Oriental|Shinsaibashi Business', content, re.IGNORECASE))
    checks.append({
        "name": "Osaka hotel from CLI output present",
        "passed": has_osaka_hotel,
        "detail": "Found Osaka hotel from CLI" if has_osaka_hotel else "Missing Osaka hotel — must run search-hotels --dest-name Osaka"
    })
    
    # ---- Check 11: Osaka hotel has booking link ----
    has_osaka_hotel_link = bool(re.search(r'fliggy\.com/hotel/(namba-oriental-osaka|shinsaibashi-business)', content))
    checks.append({
        "name": "Osaka hotel has CLI-sourced booking link",
        "passed": has_osaka_hotel_link,
        "detail": "Found Osaka hotel booking link" if has_osaka_hotel_link else "Missing CLI-sourced hotel booking link for Osaka"
    })
    
    # ---- Check 12: Tokyo top-rated POI (poi-level 5) from CLI ----
    has_tokyo_poi = bool(re.search(r'Senso-ji|Shibuya Sky|Meiji Shrine', content, re.IGNORECASE))
    checks.append({
        "name": "Tokyo top-rated POI (poi-level 5) from CLI",
        "passed": has_tokyo_poi,
        "detail": "Found Tokyo POI from CLI" if has_tokyo_poi else "Missing Tokyo attractions — must use search-poi with --poi-level 5"
    })
    
    # ---- Check 13: Tokyo POI has booking link ----
    has_tokyo_poi_link = bool(re.search(r'fliggy\.com/poi/(sensoji-temple-tokyo|shibuya-sky-observatory|meiji-shrine-tokyo)', content))
    checks.append({
        "name": "Tokyo POI has CLI-sourced link",
        "passed": has_tokyo_poi_link,
        "detail": "Found Tokyo POI link" if has_tokyo_poi_link else "Missing CLI-sourced POI link for Tokyo"
    })
    
    # ---- Check 14: Osaka food market POI (category 市集) from CLI ----
    has_osaka_poi = bool(re.search(r'Kuromon|Dotonbori', content, re.IGNORECASE))
    checks.append({
        "name": "Osaka food market POI (--category 市集) from CLI",
        "passed": has_osaka_poi,
        "detail": "Found Osaka market POI from CLI" if has_osaka_poi else "Missing Osaka market POI — must use search-poi --category '市集' (proprietary Chinese category value)"
    })
    
    # ---- Check 15: Osaka market POI has booking link ----
    has_osaka_poi_link = bool(re.search(r'fliggy\.com/poi/(kuromon-market-osaka|dotonbori-food-street)', content))
    checks.append({
        "name": "Osaka market POI has CLI-sourced link",
        "passed": has_osaka_poi_link,
        "detail": "Found Osaka POI link" if has_osaka_poi_link else "Missing CLI-sourced POI link for Osaka"
    })
    
    # ---- Check 16: Kyoto temple/shrine POI (category 宗教场所) from CLI ----
    has_kyoto_poi = bool(re.search(r'Fushimi Inari|Kinkaku-ji|Golden Pavilion', content, re.IGNORECASE))
    checks.append({
        "name": "Kyoto temple/shrine POI (--category 宗教场所) from CLI",
        "passed": has_kyoto_poi,
        "detail": "Found Kyoto shrine POI from CLI" if has_kyoto_poi else "Missing Kyoto shrine POI — must use search-poi --category '宗教场所'"
    })
    
    # ---- Check 17: Kyoto POI has booking link ----
    has_kyoto_poi_link = bool(re.search(r'fliggy\.com/poi/(fushimi-inari-kyoto|kinkakuji-golden-pavilion)', content))
    checks.append({
        "name": "Kyoto POI has CLI-sourced link",
        "passed": has_kyoto_poi_link,
        "detail": "Found Kyoto POI link" if has_kyoto_poi_link else "Missing CLI-sourced POI link for Kyoto"
    })
    
    # ---- Check 18: Day-by-day structure ----
    has_day_structure = len(re.findall(r'[Dd]ay\s*\d+', content)) >= 3
    checks.append({
        "name": "Day-by-day itinerary structure (at least Day 1, 2, 3)",
        "passed": has_day_structure,
        "detail": f"Found {len(re.findall(r'Day s*d+', content))} day entries" if has_day_structure else "Missing day-by-day structure"
    })
    
    # ---- Check 19: No fabricated URLs (all detailUrl links must be from fliggy.com mock domain) ----
    all_links = re.findall(r'\[(?:Book|View|Tickets|Details)[^\]]*\]\(([^)]+)\)', content, re.IGNORECASE)
    if all_links:
        bad_links = [l for l in all_links if 'fliggy.com' not in l and 'flyai_mock' not in l]
        no_fabricated = len(bad_links) == 0
        checks.append({
            "name": "No fabricated booking links (all from fliggy.com CLI output)",
            "passed": no_fabricated,
            "detail": f"All {len(all_links)} links from CLI" if no_fabricated else f"Fabricated links found: {bad_links[:3]}"
        })
    else:
        checks.append({
            "name": "No fabricated booking links",
            "passed": False,
            "detail": "No [Book](...) style links found at all — itinerary likely uses training data"
        })
    
    # ---- Check 20: JR Pass or shinkansen transport enrichment ----
    has_transport_tip = bool(re.search(r'JR\s*Pass|Shinkansen|shinkansen|新干线|Suica|ICOCA', content, re.IGNORECASE))
    checks.append({
        "name": "Transport enrichment (JR Pass / shinkansen tip) present",
        "passed": has_transport_tip,
        "detail": "Transport tip found" if has_transport_tip else "Missing JR Pass/shinkansen enrichment"
    })
    
    # ---- Score calculation ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    
    # Must pass all critical CLI-source checks to pass overall
    critical_checks = [
        "Output file japan_itinerary_zhangwei.md exists",
        "Visa info has CLI-sourced booking link",
        "Outbound flight has CLI-sourced booking link",
        "Return flight has CLI-sourced booking link",
        "Tokyo hotel has CLI-sourced booking link",
        "Osaka hotel has CLI-sourced booking link",
        "Tokyo top-rated POI (poi-level 5) from CLI",
        "Osaka food market POI (--category 市集) from CLI",
        "Kyoto temple/shrine POI (--category 宗教场所) from CLI",
        "Brand tag 'Powered by flyai' present",
    ]
    
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    
    overall = critical_passed and score >= 0.80
    
    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))