import sys
import json
import re
import os
from pathlib import Path

def find_output_file(workspace):
    """Find the output JSON file."""
    # Check the specified output location first
    direct_path = Path(workspace) / "output" / "qingyuantang_proverbs.json"
    if direct_path.exists():
        return direct_path
    # Fallback: search entire workspace
    candidates = list(Path(workspace).rglob("qingyuantang_proverbs.json"))
    if candidates:
        return candidates[0]
    return None

def load_json_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return None, str(e)

def check_brand_name_in_proverb(text, brand_name="清远堂"):
    return brand_name in text

def check_no_adjectives(text):
    """Check that common adjectives are not present."""
    forbidden_adjectives = [
        "优质", "高效", "专业", "纯天然", "高品质", "卓越", "领先",
        "顶级", "一流", "完美", "精致", "纯正", "健康", "美味",
        "清凉", "神奇", "最好", "极品", "超级", "绝佳", "独特"
    ]
    found = [adj for adj in forbidden_adjectives if adj in text]
    return found

def check_char_length(text, brand_name="清远堂"):
    """Count Chinese characters in a proverb."""
    # Count only Chinese chars + common punctuation-excluded
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
    return len(chinese_chars)

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0
    
    # ---- Check 1: Output file exists ----
    output_file = find_output_file(workspace)
    file_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found at {output_file}" if file_exists else "qingyuantang_proverbs.json not found anywhere in workspace"
    })
    
    if not file_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return
    
    # ---- Load JSON ----
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        json_valid = True
        json_error = ""
    except Exception as e:
        json_valid = False
        json_error = str(e)
        data = {}
    
    checks.append({
        "name": "valid_json_format",
        "passed": json_valid,
        "detail": f"Valid JSON" if json_valid else f"JSON parse error: {json_error}"
    })
    
    if not json_valid:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ---- Check 2: Has top10 key ----
    has_top10 = "top10" in data
    checks.append({
        "name": "has_top10_key",
        "passed": has_top10,
        "detail": f"'top10' key present" if has_top10 else f"Missing 'top10' key. Keys found: {list(data.keys())}"
    })
    
    if not has_top10:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    top10 = data["top10"]
    
    # ---- Check 3: Top 10 has exactly 10 items ----
    has_ten_items = isinstance(top10, list) and len(top10) >= 10
    checks.append({
        "name": "top10_has_ten_entries",
        "passed": has_ten_items,
        "detail": f"Found {len(top10)} entries" if isinstance(top10, list) else "top10 is not a list"
    })

    if not has_ten_items:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    top10_entries = top10[:10]

    # ---- Check 4: All entries have required fields ----
    required_fields = ["rank", "line", "strategy", "rhetoric", "rhyme", "length", "score_total", "score_breakdown"]
    missing_fields_list = []
    for i, entry in enumerate(top10_entries):
        if not isinstance(entry, dict):
            missing_fields_list.append(f"Entry {i}: not a dict")
            continue
        for field in required_fields:
            if field not in entry:
                missing_fields_list.append(f"Entry {i} missing '{field}'")
    
    has_all_fields = len(missing_fields_list) == 0
    checks.append({
        "name": "all_entries_have_required_fields",
        "passed": has_all_fields,
        "detail": "All required fields present" if has_all_fields else f"Missing fields: {missing_fields_list[:5]}"
    })

    # ---- Check 5: All proverbs contain brand name "清远堂" ----
    brand_name = "清远堂"
    brand_name_violations = []
    for i, entry in enumerate(top10_entries):
        if isinstance(entry, dict) and "line" in entry:
            line = entry["line"]
            if not check_brand_name_in_proverb(line, brand_name):
                brand_name_violations.append(f"Entry {i} (rank {entry.get('rank','?')}): '{line}'")
    
    all_have_brand_name = len(brand_name_violations) == 0
    checks.append({
        "name": "all_proverbs_contain_brand_name",
        "passed": all_have_brand_name,
        "detail": "All proverbs contain '清远堂'" if all_have_brand_name else f"Missing brand name in: {brand_name_violations}"
    })

    # ---- Check 6: No adjectives in proverbs ----
    adjective_violations = []
    for i, entry in enumerate(top10_entries):
        if isinstance(entry, dict) and "line" in entry:
            line = entry["line"]
            found_adj = check_no_adjectives(line)
            if found_adj:
                adjective_violations.append(f"Entry {i}: '{line}' contains adjectives: {found_adj}")
    
    no_adjectives = len(adjective_violations) == 0
    checks.append({
        "name": "no_adjectives_in_proverbs",
        "passed": no_adjectives,
        "detail": "No forbidden adjectives found" if no_adjectives else f"Adjective violations: {adjective_violations[:3]}"
    })

    # ---- Check 7: Character length within 10 chars ----
    length_violations = []
    for i, entry in enumerate(top10_entries):
        if isinstance(entry, dict) and "line" in entry:
            line = entry["line"]
            char_count = check_char_length(line, brand_name)
            if char_count > 10:
                length_violations.append(f"Entry {i}: '{line}' has {char_count} Chinese chars (limit: 10)")
    
    length_ok = len(length_violations) == 0
    checks.append({
        "name": "proverbs_within_char_limit",
        "passed": length_ok,
        "detail": "All proverbs within 10-char limit" if length_ok else f"Length violations: {length_violations[:3]}"
    })

    # ---- Check 8: score_breakdown uses correct field names and sums to score_total ----
    required_breakdown_fields = ["brand_name", "brand_value", "rhetoric_fit", "culture_force",
                                  "brevity", "brand_drama", "pleasantness"]
    max_scores = {"brand_name": 20, "brand_value": 20, "rhetoric_fit": 20,
                  "culture_force": 10, "brevity": 10, "brand_drama": 10, "pleasantness": 10}
    
    breakdown_violations = []
    sum_violations = []
    max_violations = []
    
    for i, entry in enumerate(top10_entries):
        if not isinstance(entry, dict):
            continue
        breakdown = entry.get("score_breakdown", {})
        if not isinstance(breakdown, dict):
            breakdown_violations.append(f"Entry {i}: score_breakdown is not a dict")
            continue
        
        # Check required fields
        missing_bd_fields = [f for f in required_breakdown_fields if f not in breakdown]
        if missing_bd_fields:
            breakdown_violations.append(f"Entry {i} breakdown missing: {missing_bd_fields}")
        
        # Check sum
        try:
            computed_sum = sum(float(breakdown.get(f, 0)) for f in required_breakdown_fields)
            score_total = float(entry.get("score_total", 0))
            if abs(computed_sum - score_total) > 1.0:  # allow 1pt rounding
                sum_violations.append(
                    f"Entry {i}: breakdown sum={computed_sum:.0f} != score_total={score_total:.0f}"
                )
        except Exception as e:
            sum_violations.append(f"Entry {i}: computation error {e}")
        
        # Check no dimension exceeds max
        for field, max_val in max_scores.items():
            val = float(breakdown.get(field, 0))
            if val > max_val:
                max_violations.append(f"Entry {i}: {field}={val} exceeds max {max_val}")

    all_breakdown_ok = len(breakdown_violations) == 0 and len(sum_violations) == 0 and len(max_violations) == 0
    checks.append({
        "name": "score_breakdown_correct",
        "passed": all_breakdown_ok,
        "detail": "All score breakdowns valid" if all_breakdown_ok else 
                  f"Field issues: {breakdown_violations[:2]}, Sum issues: {sum_violations[:2]}, Max issues: {max_violations[:2]}"
    })

    # ---- Check 9: Entries are sorted by score_total descending ----
    try:
        scores = [float(e.get("score_total", 0)) for e in top10_entries if isinstance(e, dict)]
        is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
        checks.append({
            "name": "top10_sorted_by_score_descending",
            "passed": is_sorted,
            "detail": f"Scores in order: {scores}" if is_sorted else f"Not sorted: {scores}"
        })
    except Exception as e:
        checks.append({
            "name": "top10_sorted_by_score_descending",
            "passed": False,
            "detail": f"Error checking sort order: {e}"
        })

    # ---- Check 10: Mentions 7x7 or matrix structure (has at least 49 total proverbs documented) ----
    # Check if there's evidence of the 7x7 matrix (either in the JSON or as additional keys)
    has_matrix_evidence = False
    matrix_detail = ""
    
    # Option A: check for a matrix/proverbs_matrix key
    if "proverbs_matrix" in data or "matrix" in data or "all_proverbs" in data:
        has_matrix_evidence = True
        matrix_detail = "Found matrix/all_proverbs key in JSON"
    
    # Option B: count total unique proverbs across all sections
    elif "sections" in data:
        all_lines = []
        for section in data.get("sections", []):
            all_lines.extend(section.get("proverbs", []))
        if len(all_lines) >= 49:
            has_matrix_evidence = True
            matrix_detail = f"Found {len(all_lines)} proverbs in sections"
    
    # Option C: look for any list in data that has 49+ items
    else:
        for key, val in data.items():
            if key == "top10":
                continue
            if isinstance(val, list) and len(val) >= 49:
                has_matrix_evidence = True
                matrix_detail = f"Found 49+ proverbs in key '{key}'"
                break
            elif isinstance(val, dict):
                for subkey, subval in val.items():
                    if isinstance(subval, list) and len(subval) >= 49:
                        has_matrix_evidence = True
                        matrix_detail = f"Found 49+ proverbs in '{key}.{subkey}'"
                        break
    
    checks.append({
        "name": "evidence_of_7x7_matrix_49_proverbs",
        "passed": has_matrix_evidence,
        "detail": matrix_detail if has_matrix_evidence else "No evidence of 49-proverb 7x7 matrix found in JSON structure"
    })

    # ---- Check 11: Top 1 proverb score >= 75 (reasonable quality threshold) ----
    try:
        top1_score = float(top10_entries[0].get("score_total", 0))
        score_reasonable = top1_score >= 75
        checks.append({
            "name": "top1_score_at_least_75",
            "passed": score_reasonable,
            "detail": f"Top 1 score: {top1_score}" 
        })
    except Exception as e:
        checks.append({
            "name": "top1_score_at_least_75",
            "passed": False,
            "detail": f"Error reading top1 score: {e}"
        })

    # ---- Check 12: Rank field is correct (1-10) ----
    try:
        ranks = [int(e.get("rank", 0)) for e in top10_entries if isinstance(e, dict)]
        ranks_correct = sorted(ranks) == list(range(1, 11))
        checks.append({
            "name": "rank_fields_1_to_10",
            "passed": ranks_correct,
            "detail": f"Ranks found: {ranks}" if not ranks_correct else "Ranks 1-10 correct"
        })
    except Exception as e:
        checks.append({
            "name": "rank_fields_1_to_10",
            "passed": False,
            "detail": f"Error checking ranks: {e}"
        })

    # ---- Compute final score ----
    # Weight checks by importance
    weights = {
        "output_file_exists": 5,
        "valid_json_format": 5,
        "has_top10_key": 5,
        "top10_has_ten_entries": 10,
        "all_entries_have_required_fields": 10,
        "all_proverbs_contain_brand_name": 20,   # Critical proprietary rule
        "no_adjectives_in_proverbs": 10,
        "proverbs_within_char_limit": 10,
        "score_breakdown_correct": 10,
        "top10_sorted_by_score_descending": 5,
        "evidence_of_7x7_matrix_49_proverbs": 5,
        "top1_score_at_least_75": 3,
        "rank_fields_1_to_10": 2,
    }
    
    earned = 0
    total_weight = sum(weights.values())
    
    for check in checks:
        w = weights.get(check["name"], 0)
        if check["passed"]:
            earned += w
    
    final_score = round(earned / total_weight, 4)
    passed = final_score >= 0.70 and all_have_brand_name and no_adjectives and has_ten_items

    print(json.dumps({
        "passed": passed,
        "score": final_score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()