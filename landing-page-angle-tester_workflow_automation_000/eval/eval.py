import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find the output markdown file ──────────────────────────────────────
    # The prompt asks the agent to save output as "clauseguard_angles.md"
    target_filename = "clauseguard_angles.md"
    candidates = list(ws.rglob(target_filename))

    if not candidates:
        # Also accept any .md file in an output/results-like location as fallback
        candidates = [p for p in ws.rglob("*.md")
                      if "angle" in p.name.lower() or "clauseguard" in p.name.lower()
                      or "landing" in p.name.lower()]

    output_file = candidates[0] if candidates else None

    if output_file is None:
        score = add("output_file_exists", False,
                    f"No output file named '{target_filename}' (or angle-related .md) found anywhere in workspace.")
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    total_score += add("output_file_exists", True,
                       f"Found output file: {output_file.relative_to(ws)}", weight=0.5)

    # ── 2. Read the file ───────────────────────────────────────────────────────
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        add("output_file_readable", False, f"Cannot read file: {e}")
        print(json.dumps({"passed": False, "score": total_score / 10.0, "checks": checks},
                         ensure_ascii=False))
        return

    total_score += add("output_file_readable", True, "File is readable.", weight=0.5)

    # ── 3. Check that run.py was actually invoked (output contains template markers) ──
    # The template.md produces specific structural markers only run.py can generate
    has_draft_section = "可审阅草案" in content
    has_checklist_section = "可执行清单" in content
    total_score += add("has_draft_section",
                       has_draft_section,
                       "'可审阅草案' section present – indicates template was rendered by run.py"
                       if has_draft_section else "'可审阅草案' section MISSING – run.py was likely not used.",
                       weight=1.0)
    total_score += add("has_checklist_section",
                       has_checklist_section,
                       "'可执行清单' section present."
                       if has_checklist_section else "'可执行清单' section MISSING.",
                       weight=1.0)

    # ── 4. Exactly 4 angles ────────────────────────────────────────────────────
    # Template renders: "### 角度 N：" for each angle
    angle_headers = re.findall(r"###\s*角度\s*\d+", content)
    angle_count = len(angle_headers)
    total_score += add("exactly_4_angles",
                       angle_count == 4,
                       f"Found {angle_count} angle headers (expected 4). Headers: {angle_headers}",
                       weight=2.0)

    # ── 5. All 6 required sections present per angle ───────────────────────────
    required_sections = ["角度候选", "适配人群", "主标题建议", "证据需求", "风险点", "测试顺序"]
    all_sections_present = all(sec in content for sec in required_sections)
    missing_sections = [sec for sec in required_sections if sec not in content]
    total_score += add("all_6_sections_present",
                       all_sections_present,
                       "All 6 required sections found in output."
                       if all_sections_present else f"Missing sections: {missing_sections}",
                       weight=2.0)

    # ── 6. Product is ClauseGuard AI ──────────────────────────────────────────
    has_product_name = "clauseguard" in content.lower() or "ClauseGuard" in content
    total_score += add("product_name_present",
                       has_product_name,
                       "Product name 'ClauseGuard AI' found in output."
                       if has_product_name else "Product name not found – agent may have used wrong input.",
                       weight=0.5)

    # ── 7. No prohibited content (fabricated testimonials) ─────────────────────
    prohibited_patterns = [
        r"用户反馈[：:]",
        r"客户说[：:]",
        r"据客户反映",
        r"100%\s*(准确|安全|保证|accuracy|guarantee)",
        r"绝对安全",
        r"完全准确"
    ]
    found_prohibited = []
    for pat in prohibited_patterns:
        if re.search(pat, content):
            found_prohibited.append(pat)

    no_prohibited = len(found_prohibited) == 0
    total_score += add("no_prohibited_content",
                       no_prohibited,
                       "No prohibited content (fabricated testimonials / exaggerated claims) detected."
                       if no_prohibited else f"Prohibited content detected: {found_prohibited}",
                       weight=1.0)

    # ── 8. Input JSON was well-formed (check for correct input file) ───────────
    # Agent must have created a valid input JSON consumed by run.py.
    # We find any JSON file that has the required schema keys.
    input_schema_keys = {"product_name", "product_description", "key_features",
                         "target_users", "constraints", "angles"}
    valid_input_found = False
    input_detail = "No valid structured input JSON found."
    for json_file in ws.rglob("*.json"):
        # Skip spec.json, example_input.json, and analytics files
        if json_file.name in ("spec.json", "example_input.json",
                               "conversion_rates_2024.json", "ab_test_results_Q2.csv",
                               "TEMPLATE_ATTEMPT_broken.json"):
            continue
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(data, dict) and input_schema_keys.issubset(data.keys()):
                angles_data = data.get("angles", [])
                if len(angles_data) == 4:
                    valid_input_found = True
                    input_detail = f"Valid 4-angle input JSON found at: {json_file.relative_to(ws)}"
                    break
        except Exception:
            continue

    total_score += add("valid_input_json_created",
                       valid_input_found,
                       input_detail,
                       weight=1.5)

    # ── 9. Test order section content is meaningful ────────────────────────────
    # Each angle's test order should have some numeric or ordering reference
    test_order_matches = re.findall(r"\*\*测试顺序\*\*\s*\n([^\n]+)", content)
    meaningful_order = len(test_order_matches) >= 3 and all(
        any(c.isdigit() for c in m) for m in test_order_matches
    )
    total_score += add("test_order_meaningful",
                       meaningful_order,
                       f"Test order entries found: {test_order_matches[:4]}"
                       if meaningful_order else "Test order entries are missing or lack ordering indicators.",
                       weight=0.5)

    # ── Final score ────────────────────────────────────────────────────────────
    max_score = 0.5 + 0.5 + 1.0 + 1.0 + 2.0 + 2.0 + 0.5 + 1.0 + 1.5 + 0.5  # = 11.0
    normalized = round(total_score / max_score, 3)

    # Must pass critical checks to be considered passing overall
    critical_passed = (
        angle_count == 4 and
        all_sections_present and
        has_draft_section and
        has_checklist_section and
        valid_input_found
    )

    result = {
        "passed": critical_passed and normalized >= 0.75,
        "score": normalized,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)