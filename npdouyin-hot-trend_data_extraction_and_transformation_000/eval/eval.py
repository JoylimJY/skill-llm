import sys
import json
import re
from pathlib import Path

def main(workspace):
    results = []
    overall_passed = True

    def check(name, passed, detail):
        results.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # --- Find the output file ---
    target_file = None
    candidates = list(Path(workspace).rglob("trending_report.json"))
    
    file_found = len(candidates) > 0
    if not check("output_file_exists", file_found, 
                 f"Found at: {candidates[0]}" if file_found else "trending_report.json not found anywhere in workspace"):
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    target_file = candidates[0]

    # --- Parse JSON ---
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        check("json_parseable", False, f"Failed to parse JSON: {e}")
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    check("json_parseable", True, "File parsed successfully as JSON")

    # --- Must be a list/array ---
    is_list = isinstance(data, list)
    if not check("is_array", is_list, f"Expected JSON array, got {type(data).__name__}"):
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    # --- Must have exactly 15 items ---
    count_ok = len(data) == 15
    if not check("exactly_15_items", count_ok, f"Expected 15 items, got {len(data)}"):
        overall_passed = False

    if len(data) == 0:
        print(json.dumps({"passed": False, "score": 0.0, "checks": results}))
        return

    # --- Check required fields exist in all items ---
    required_fields = {"rank", "title", "popularity", "link", "cover", "label", "type"}
    missing_fields_items = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            missing_fields_items.append(f"item[{i}] is not a dict")
            continue
        missing = required_fields - set(item.keys())
        if missing:
            missing_fields_items.append(f"item[{i}] missing: {missing}")

    all_fields_present = len(missing_fields_items) == 0
    check("all_required_fields_present", all_fields_present,
          "All items have required fields" if all_fields_present else "; ".join(missing_fields_items[:5]))
    if not all_fields_present:
        overall_passed = False

    # --- Check rank is integer starting from 1, sequential ---
    rank_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        r = item.get("rank")
        if not isinstance(r, int):
            rank_errors.append(f"item[{i}] rank is {type(r).__name__} (expected int)")
        elif r != i + 1:
            rank_errors.append(f"item[{i}] rank={r}, expected {i+1}")
    rank_ok = len(rank_errors) == 0
    check("rank_field_correct", rank_ok,
          "Ranks are integers starting from 1" if rank_ok else "; ".join(rank_errors[:5]))
    if not rank_ok:
        overall_passed = False

    # --- Check popularity is NUMBER (not string), >= 0 ---
    pop_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        p = item.get("popularity")
        if not isinstance(p, (int, float)):
            pop_errors.append(f"item[{i}] popularity={repr(p)} is {type(p).__name__} (must be number)")
        elif p < 0:
            pop_errors.append(f"item[{i}] popularity={p} is negative")
    pop_ok = len(pop_errors) == 0
    check("popularity_is_number", pop_ok,
          "All popularity values are numbers" if pop_ok else "; ".join(pop_errors[:5]))
    if not pop_ok:
        overall_passed = False

    # --- Check cover field: must be string or null, NOT missing, NOT empty string for present covers ---
    cover_errors = []
    cover_null_count = 0
    cover_url_count = 0
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        c = item.get("cover", "__MISSING__")
        if c == "__MISSING__":
            cover_errors.append(f"item[{i}] cover field is completely absent (must be string or null)")
        elif c is None:
            cover_null_count += 1
        elif isinstance(c, str):
            if c.strip() == "":
                cover_errors.append(f"item[{i}] cover is empty string (should be null when absent)")
            else:
                cover_url_count += 1
        else:
            cover_errors.append(f"item[{i}] cover={repr(c)} is {type(c).__name__} (must be string or null)")

    cover_field_ok = len(cover_errors) == 0
    check("cover_field_valid_types", cover_field_ok,
          f"Cover field valid: {cover_url_count} URLs, {cover_null_count} nulls" if cover_field_ok
          else "; ".join(cover_errors[:5]))
    if not cover_field_ok:
        overall_passed = False

    # There should be at least some nulls and some URLs (per mock data: every 3rd item has null cover)
    has_mixed_covers = cover_null_count > 0 and cover_url_count > 0
    check("cover_has_null_and_url_values", has_mixed_covers,
          f"null covers: {cover_null_count}, URL covers: {cover_url_count} (both expected)")
    if not has_mixed_covers:
        overall_passed = False

    # --- Check label: string or null (not a number type) ---
    label_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        lb = item.get("label", "__MISSING__")
        if lb == "__MISSING__":
            label_errors.append(f"item[{i}] label field missing")
        elif lb is not None and not isinstance(lb, str):
            label_errors.append(f"item[{i}] label={repr(lb)} is {type(lb).__name__} (must be string or null)")
    label_ok = len(label_errors) == 0
    check("label_field_valid", label_ok,
          "Label fields are string or null" if label_ok else "; ".join(label_errors[:5]))
    if not label_ok:
        overall_passed = False

    # --- Check link field: non-empty string, starts with https://www.douyin.com ---
    link_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        lk = item.get("link", "")
        if not isinstance(lk, str) or not lk.startswith("https://www.douyin.com"):
            link_errors.append(f"item[{i}] link={repr(lk)[:80]}")
    link_ok = len(link_errors) == 0
    check("link_field_valid", link_ok,
          "All links are valid Douyin URLs" if link_ok else "; ".join(link_errors[:5]))
    if not link_ok:
        overall_passed = False

    # --- Check type field is non-empty string ---
    type_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        t = item.get("type", "")
        if not isinstance(t, str) or t.strip() == "":
            type_errors.append(f"item[{i}] type={repr(t)}")
    type_ok = len(type_errors) == 0
    check("type_field_valid", type_ok,
          "All type fields are non-empty strings" if type_ok else "; ".join(type_errors[:5]))
    if not type_ok:
        overall_passed = False

    # --- Check title field is non-empty string ---
    title_errors = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        t = item.get("title", "")
        if not isinstance(t, str) or t.strip() == "":
            title_errors.append(f"item[{i}] title={repr(t)}")
    title_ok = len(title_errors) == 0
    check("title_field_valid", title_ok,
          "All title fields are non-empty strings" if title_ok else "; ".join(title_errors[:5]))
    if not title_ok:
        overall_passed = False

    # --- Compute score ---
    passed_checks = sum(1 for r in results if r["passed"])
    score = round(passed_checks / len(results), 4)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": results
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)