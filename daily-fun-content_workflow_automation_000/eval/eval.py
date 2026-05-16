import sys
import json
import subprocess
import re
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ---- CHECK 1: Cache file exists at correct location ----
    cache_file = workspace / "skills" / "daily-fun-content" / "cache" / "daily-fun.json"
    check1_passed = cache_file.exists()
    checks.append({
        "name": "cache/daily-fun.json exists at correct path",
        "passed": check1_passed,
        "detail": f"Expected at {cache_file}. {'Found.' if check1_passed else 'NOT FOUND. Note: a decoy file exists at skills/daily-fun-content/daily-fun.json (wrong dir).'}"
    })
    if check1_passed:
        total_score += 0.10

    if not check1_passed:
        # Can't do further checks meaningfully
        for name in [
            "JSON is valid and parseable",
            "Top-level fields: date (YYYY-MM-DD), generated (ISO 8601 UTC), items array",
            "Item count is between 6 and 8 (inclusive)",
            "All items have required 'type' and 'content' fields",
            "meme items have required 'title' field",
            "At least one item of each type: joke, meme, chat_tip",
            "generate.mjs validation passes (no errors)",
            "get-content.mjs returns a valid item (exits 0)"
        ]:
            checks.append({"name": name, "passed": False, "detail": "Skipped: cache file not found at correct path."})
        score = total_score / 1.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ---- CHECK 2: Valid JSON ----
    data = None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "JSON is valid and parseable", "passed": True, "detail": "JSON parsed successfully."})
        total_score += 0.10
    except Exception as e:
        checks.append({"name": "JSON is valid and parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        for name in [
            "Top-level fields: date (YYYY-MM-DD), generated (ISO 8601 UTC), items array",
            "Item count is between 6 and 8 (inclusive)",
            "All items have required 'type' and 'content' fields",
            "meme items have required 'title' field",
            "At least one item of each type: joke, meme, chat_tip",
            "generate.mjs validation passes (no errors)",
            "get-content.mjs returns a valid item (exits 0)"
        ]:
            checks.append({"name": name, "passed": False, "detail": "Skipped: invalid JSON."})
        score = total_score / 1.0
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ---- CHECK 3: Top-level schema ----
    try:
        has_date = "date" in data and isinstance(data["date"], str)
        has_generated = "generated" in data and isinstance(data["generated"], str)
        has_items = "items" in data and isinstance(data["items"], list)

        date_ok = has_date and bool(re.match(r"^\d{4}-\d{2}-\d{2}$", data.get("date", "")))
        generated_ok = has_generated and bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", data.get("generated", "")))

        check3_passed = date_ok and generated_ok and has_items
        detail_parts = []
        if not date_ok:
            detail_parts.append(f"'date' field invalid or missing. Got: {data.get('date', 'MISSING')!r}. Expected YYYY-MM-DD.")
        if not generated_ok:
            detail_parts.append(f"'generated' field invalid or missing. Got: {data.get('generated', 'MISSING')!r}. Expected YYYY-MM-DDThh:mm:ssZ.")
        if not has_items:
            detail_parts.append("'items' array missing or not an array.")
        checks.append({
            "name": "Top-level fields: date (YYYY-MM-DD), generated (ISO 8601 UTC), items array",
            "passed": check3_passed,
            "detail": "; ".join(detail_parts) if detail_parts else "All top-level fields valid."
        })
        if check3_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "Top-level fields: date (YYYY-MM-DD), generated (ISO 8601 UTC), items array", "passed": False, "detail": f"Exception: {e}"})

    # ---- CHECK 4: Item count 6-8 ----
    try:
        items = data.get("items", [])
        count = len(items)
        count_ok = 6 <= count <= 8
        checks.append({
            "name": "Item count is between 6 and 8 (inclusive)",
            "passed": count_ok,
            "detail": f"Found {count} items. {'OK.' if count_ok else 'FAIL: must be 6-8.'}"
        })
        if count_ok:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "Item count is between 6 and 8 (inclusive)", "passed": False, "detail": f"Exception: {e}"})

    # ---- CHECK 5: All items have type and content ----
    try:
        items = data.get("items", [])
        valid_types = {"joke", "meme", "chat_tip"}
        bad_items = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                bad_items.append(f"item[{i}] is not an object")
                continue
            if item.get("type") not in valid_types:
                bad_items.append(f"item[{i}].type={item.get('type')!r} invalid")
            if not item.get("content") or not isinstance(item.get("content"), str) or not item["content"].strip():
                bad_items.append(f"item[{i}] missing/empty content")

        check5_passed = len(bad_items) == 0
        checks.append({
            "name": "All items have required 'type' and 'content' fields",
            "passed": check5_passed,
            "detail": "; ".join(bad_items) if bad_items else f"All {len(items)} items have valid type and content."
        })
        if check5_passed:
            total_score += 0.15
    except Exception as e:
        checks.append({"name": "All items have required 'type' and 'content' fields", "passed": False, "detail": f"Exception: {e}"})

    # ---- CHECK 6: meme items have title (KEY PROPRIETARY TRAP) ----
    try:
        items = data.get("items", [])
        meme_items = [item for item in items if isinstance(item, dict) and item.get("type") == "meme"]
        bad_memes = []
        for i, item in enumerate(meme_items):
            if not item.get("title") or not isinstance(item.get("title"), str) or not item["title"].strip():
                bad_memes.append(f"meme item missing 'title' field: {json.dumps(item, ensure_ascii=False)[:80]}")

        check6_passed = len(meme_items) > 0 and len(bad_memes) == 0
        if len(meme_items) == 0:
            detail = "No meme items found (need at least one with 'title')."
            check6_passed = False
        else:
            detail = "; ".join(bad_memes) if bad_memes else f"All {len(meme_items)} meme items have 'title' field."

        checks.append({
            "name": "meme items have required 'title' field",
            "passed": check6_passed,
            "detail": detail
        })
        if check6_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "meme items have required 'title' field", "passed": False, "detail": f"Exception: {e}"})

    # ---- CHECK 7: At least one of each type ----
    try:
        items = data.get("items", [])
        types_present = set(item.get("type") for item in items if isinstance(item, dict))
        has_joke = "joke" in types_present
        has_meme = "meme" in types_present
        has_chat_tip = "chat_tip" in types_present
        check7_passed = has_joke and has_meme and has_chat_tip
        missing = [t for t, present in [("joke", has_joke), ("meme", has_meme), ("chat_tip", has_chat_tip)] if not present]
        checks.append({
            "name": "At least one item of each type: joke, meme, chat_tip",
            "passed": check7_passed,
            "detail": f"Missing types: {missing}" if missing else f"All three types present: {sorted(types_present)}"
        })
        if check7_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "At least one item of each type: joke, meme, chat_tip", "passed": False, "detail": f"Exception: {e}"})

    # ---- CHECK 8: generate.mjs validates successfully ----
    try:
        result = subprocess.run(
            ["node", str(workspace / "skills" / "daily-fun-content" / "scripts" / "generate.mjs")],
            capture_output=True, text=True, timeout=15,
            cwd=str(workspace / "skills" / "daily-fun-content")
        )
        check8_passed = result.returncode == 0
        detail = f"Exit code: {result.returncode}. stdout: {result.stdout[:200].strip()}. stderr: {result.stderr[:200].strip()}"
        checks.append({
            "name": "generate.mjs validation passes (no errors)",
            "passed": check8_passed,
            "detail": detail
        })
        if check8_passed:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "generate.mjs validation passes (no errors)", "passed": False, "detail": f"Exception running generate.mjs: {e}"})

    # ---- CHECK 9: get-content.mjs returns valid item ----
    try:
        result = subprocess.run(
            ["node", str(workspace / "skills" / "daily-fun-content" / "scripts" / "get-content.mjs")],
            capture_output=True, text=True, timeout=15,
            cwd=str(workspace / "skills" / "daily-fun-content")
        )
        check9_passed = result.returncode == 0 and len(result.stdout.strip()) > 0
        # Output should start with [joke], [meme], or [chat_tip]
        output_ok = bool(re.match(r"^\[(joke|meme|chat_tip)\]", result.stdout.strip()))
        check9_passed = check9_passed and output_ok
        detail = f"Exit code: {result.returncode}. Output: {result.stdout[:200].strip()!r}. stderr: {result.stderr[:100].strip()}"
        checks.append({
            "name": "get-content.mjs returns a valid item (exits 0)",
            "passed": check9_passed,
            "detail": detail
        })
        if check9_passed:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "get-content.mjs returns a valid item (exits 0)", "passed": False, "detail": f"Exception running get-content.mjs: {e}"})

    # Final pass/fail: require all critical checks (1-8) to pass
    critical_checks = checks[:8]  # checks 1-8 (0-indexed: 0-7)
    all_critical_passed = all(c["passed"] for c in critical_checks)

    return {
        "passed": all_critical_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))