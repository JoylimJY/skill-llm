#!/usr/bin/env python3
"""Evaluation script for the key-takeaways batch task."""
import json
import sys
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    passed_all = True

    skill_root = Path(workspace) / "20260318" / "scientific-skills" / "Evidence Insight" / "key-takeaways"

    # ── Helper ───────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        nonlocal passed_all
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            passed_all = False

    # ── 1. Locate board_summaries/ output directory ───────────────────────────
    # Search under skill_root first, then workspace-wide
    candidates = list(skill_root.rglob("board_summaries")) + list(Path(workspace).rglob("board_summaries"))
    out_dir = None
    for c in candidates:
        if c.is_dir():
            out_dir = c
            break

    if out_dir is None:
        add("output_dir_exists", False, "No directory named 'board_summaries' found anywhere in workspace.")
        return checks, False

    add("output_dir_exists", True, f"Found board_summaries at: {out_dir}")

    # ── 2. All five documents produced a JSON output ──────────────────────────
    expected_stems = {
        "memo_q1_strategy",
        "memo_product_launch",
        "memo_board_risk",
        "memo_partnership",
        "memo_hr_offsite",
    }
    json_files = {f.stem: f for f in out_dir.glob("*.json")}
    found_stems = set(json_files.keys())
    missing = expected_stems - found_stems

    if not missing:
        add("all_five_json_files_present", True,
            f"All 5 JSON files present: {sorted(found_stems)}")
    else:
        add("all_five_json_files_present", False,
            f"Missing JSON outputs for: {sorted(missing)}. Found: {sorted(found_stems)}")

    # ── 3. Every present JSON is valid and has correct schema keys ────────────
    schema_ok_count = 0
    schema_details  = []
    parsed_results  = {}

    for stem in expected_stems:
        if stem not in json_files:
            schema_details.append(f"{stem}: file missing – skipped")
            continue
        fpath = json_files[stem]
        try:
            data = json.loads(fpath.read_text(encoding="utf-8"))
            parsed_results[stem] = data
        except Exception as exc:
            schema_details.append(f"{stem}: JSON parse error – {exc}")
            continue

        # Must have key_points, action_items, decisions (default style)
        required_keys = {"key_points", "action_items", "decisions"}
        present_keys  = set(data.keys())
        if required_keys.issubset(present_keys):
            schema_ok_count += 1
            schema_details.append(f"{stem}: schema OK (keys={sorted(present_keys)})")
        else:
            missing_keys = required_keys - present_keys
            schema_details.append(f"{stem}: missing keys {missing_keys}")

    all_schema_ok = schema_ok_count == len(expected_stems)
    add("json_schema_correct",
        all_schema_ok,
        f"{schema_ok_count}/{len(expected_stems)} files have correct schema. " + " | ".join(schema_details))

    # ── 4. max_points=4 respected: key_points list ≤ 4 items in every file ───
    cap_ok_count  = 0
    cap_details   = []

    for stem, data in parsed_results.items():
        kp = data.get("key_points", [])
        if not isinstance(kp, list):
            cap_details.append(f"{stem}: key_points is not a list")
            continue
        if len(kp) <= 4:
            cap_ok_count += 1
            cap_details.append(f"{stem}: key_points has {len(kp)} items (≤4 ✓)")
        else:
            cap_details.append(f"{stem}: key_points has {len(kp)} items (>4 ✗)")

    all_cap_ok = (cap_ok_count == len(parsed_results)) and len(parsed_results) == len(expected_stems)
    add("max_points_4_respected",
        all_cap_ok,
        f"{cap_ok_count}/{len(parsed_results)} files respect max_points=4. " + " | ".join(cap_details))

    # ── 5. non-technical audience tag is reflected in key_points ─────────────
    audience_ok_count = 0
    audience_details  = []

    for stem, data in parsed_results.items():
        kp = data.get("key_points", [])
        if not isinstance(kp, list) or len(kp) == 0:
            audience_details.append(f"{stem}: no key_points to check")
            continue
        # The implementation appends "[audience: non-technical]" to each point
        tagged = any("non-technical" in str(pt) for pt in kp)
        if tagged:
            audience_ok_count += 1
            audience_details.append(f"{stem}: audience tag present ✓")
        else:
            audience_details.append(f"{stem}: audience tag missing ✗")

    all_audience_ok = (audience_ok_count == len(parsed_results)) and len(parsed_results) == len(expected_stems)
    add("non_technical_audience_applied",
        all_audience_ok,
        f"{audience_ok_count}/{len(parsed_results)} files contain audience tag. " + " | ".join(audience_details))

    # ── 6. Config file was used (must exist somewhere in skill workspace) ─────
    # Accept any file named like "config*.json" under skill_root or workspace
    config_files = list(skill_root.rglob("config*.json")) + list(Path(workspace).rglob("board_summaries_config*.json"))
    # Also accept any json file with max_points=4 as proxy for a valid config
    config_found = False
    config_detail = "No config file with max_points=4 found."
    all_json_candidates = list(Path(workspace).rglob("*.json"))
    for cf in all_json_candidates:
        try:
            d = json.loads(cf.read_text(encoding="utf-8"))
            if isinstance(d, dict) and str(d.get("max_points", "")) == "4":
                config_found = True
                config_detail = f"Found config with max_points=4 at {cf}"
                break
        except Exception:
            pass

    add("config_file_with_max_points_4_exists",
        config_found,
        config_detail)

    # ── 7. action_items and decisions lists are non-empty for at least 3 docs ──
    nonempty_count = 0
    nonempty_details = []
    for stem, data in parsed_results.items():
        ai = data.get("action_items", [])
        dec = data.get("decisions", [])
        if isinstance(ai, list) and len(ai) > 0 and isinstance(dec, list) and len(dec) > 0:
            nonempty_count += 1
            nonempty_details.append(f"{stem}: action_items={len(ai)}, decisions={len(dec)} ✓")
        else:
            nonempty_details.append(f"{stem}: action_items={len(ai) if isinstance(ai,list) else '?'}, decisions={len(dec) if isinstance(dec,list) else '?'} ✗")

    add("action_items_and_decisions_populated",
        nonempty_count >= 3,
        f"{nonempty_count} docs have non-empty action_items AND decisions. " + " | ".join(nonempty_details))

    return checks, passed_all


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, passed = run_checks(workspace)
    except Exception as exc:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(exc)}],
        }
        print(json.dumps(result, indent=2))
        return

    score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
    result = {"passed": passed, "score": round(score, 4), "checks": checks}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()