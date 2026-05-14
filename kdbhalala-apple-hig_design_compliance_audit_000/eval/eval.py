import sys
import json
from pathlib import Path

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def evaluate(workspace_dir):
    checks = []
    
    # Find the compliance report
    workspace = Path(workspace_dir)
    report_files = list(workspace.rglob("streamflow_compliance_report.json"))
    
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "streamflow_compliance_report.json not found anywhere in workspace"}]
        }
    
    report_path = report_files[0]
    
    try:
        report = load_json(report_path)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": f"Could not parse JSON: {e}"}]
        }

    checks.append({"name": "file_exists_and_parseable", "passed": True, "detail": f"Found at {report_path}"})

    # Helper to search nested structure for a key or value
    def find_in_report(keys_path, obj=None):
        """Navigate nested dict using dot-separated path"""
        if obj is None:
            obj = report
        parts = keys_path.split('.')
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
        return obj

    def report_str():
        return json.dumps(report).lower()

    report_text = report_str()

    # ---- CHECK 1: iOS tab count violation detected ----
    # Tab bar max is 5; submission has 7 tabs
    check_name = "ios_tab_count_violation_detected"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section).lower()
        # Look for mention of 7 tabs being wrong, or max 5, or tab count violation
        passed = (
            "7" in ios_str and ("5" in ios_str or "max" in ios_str or "violation" in ios_str or "exceed" in ios_str or "too many" in ios_str)
        ) or (
            "tab" in ios_str and ("5" in ios_str or "max" in ios_str or "exceed" in ios_str)
        )
        # Broader check across full report
        if not passed:
            passed = (
                ("7 tab" in report_text or "tab_count.*7" in report_text or '"tab_count": 7' in json.dumps(report)) and
                ("max.*5" in report_text or "5.*tab" in report_text or "maximum.*5" in report_text or "exceed" in report_text)
            )
        checks.append({"name": check_name, "passed": passed, "detail": "iOS tab bar max is 5; submission has 7. Must flag this violation."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 2: iOS grid base must be 8pt (not 6pt) ----
    check_name = "ios_grid_base_corrected_to_8pt"
    try:
        report_json_str = json.dumps(report)
        # The corrected value should be 8 for grid base
        passed = False
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section)
        # Check for correction of grid to 8 or flagging of 6pt
        if "8" in ios_str and ("grid" in ios_str.lower() or "base" in ios_str.lower()):
            passed = True
        if not passed:
            # Check if violation of 6pt grid is flagged anywhere
            passed = ("6" in report_text and "8" in report_text and "grid" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "iOS grid base must be 8pt. Submission has 6pt. Must be corrected or flagged."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 3: iOS iPhone margin must be 16pt (not 12pt) ----
    check_name = "ios_iphone_margin_corrected_to_16pt"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section)
        passed = False
        # Should flag 12pt as wrong and specify 16pt
        if "16" in ios_str and ("margin" in ios_str.lower() or "iphone" in ios_str.lower()):
            passed = True
        if not passed:
            passed = "16" in report_text and "12" in report_text and "margin" in report_text
        checks.append({"name": check_name, "passed": passed, "detail": "iPhone margin must be 16pt. Submission has 12pt. Must be corrected or flagged."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 4: iOS Dynamic Type support must be true ----
    check_name = "ios_dynamic_type_violation_detected"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section).lower()
        passed = False
        # Submission has supports_dynamic_type: false — must be flagged/corrected
        if "dynamic_type" in ios_str or "dynamic type" in ios_str:
            if "true" in ios_str or "required" in ios_str or "violation" in ios_str or "must" in ios_str or "false" in ios_str:
                passed = True
        if not passed:
            passed = "dynamic" in report_text and ("false" in report_text or "violation" in report_text or "required" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "iOS Dynamic Type (supports_dynamic_type) must be true. Submission has false."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 5: iOS WCAG contrast ratio must be at least 4.5:1 (not 3.5) ----
    check_name = "ios_wcag_contrast_violation_detected"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section).lower()
        passed = False
        # 3.5 is wrong; must be 4.5
        if "4.5" in ios_str or "wcag" in ios_str:
            passed = True
        if not passed:
            passed = "4.5" in report_text and ("3.5" in report_text or "contrast" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "iOS WCAG AA contrast for normal text must be 4.5:1. Submission has 3.5."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 6: iOS semantic colors must be used (dark mode) ----
    check_name = "ios_semantic_colors_violation_detected"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section).lower()
        passed = False
        if "semantic" in ios_str:
            passed = True
        if not passed:
            passed = "semantic" in report_text and ("false" in report_text or "violation" in report_text or "required" in report_text or "true" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "iOS dark mode must use semantic colors. Submission has uses_semantic_colors: false."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 7: iOS screen transition animation duration (0.6s is too slow, should be 0.3-0.5s) ----
    check_name = "ios_sheet_animation_duration_violation"
    try:
        ios_section = report.get("platforms", {}).get("ios", report.get("ios", {}))
        ios_str = json.dumps(ios_section).lower()
        passed = False
        # sheet_presentation_duration_s: 0.6 — exceeds standard 0.3-0.5s range
        if "0.6" in ios_str or "0.5" in ios_str:
            passed = True
        if not passed:
            passed = ("0.6" in report_text and ("0.5" in report_text or "standard" in report_text or "duration" in report_text or "violation" in report_text))
        checks.append({"name": check_name, "passed": passed, "detail": "Sheet presentation duration 0.6s exceeds standard 0.3-0.5s range. Button press 0.15s below quick 0.2s minimum."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 8: watchOS font must be SF Compact (Rounded), NOT SF Pro ----
    check_name = "watchos_font_violation_detected"
    try:
        watch_section = report.get("platforms", {}).get("watchos", report.get("watchos", {}))
        watch_str = json.dumps(watch_section).lower()
        passed = False
        # Submission says SF Pro — must be SF Compact (Rounded)
        if "sf compact" in watch_str or "compact" in watch_str:
            passed = True
        if not passed:
            passed = ("compact" in report_text and "watch" in report_text) or ("sf compact" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "watchOS system font must be SF Compact (Rounded), not SF Pro. Submission incorrectly specifies SF Pro."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 9: watchOS rounded variant must be true ----
    check_name = "watchos_rounded_variant_violation_detected"
    try:
        watch_section = report.get("platforms", {}).get("watchos", report.get("watchos", {}))
        watch_str = json.dumps(watch_section).lower()
        passed = False
        # Submission has uses_rounded_variant: false — must be true for SF Compact Rounded
        if "rounded" in watch_str:
            passed = True
        if not passed:
            passed = "rounded" in report_text and "watch" in report_text
        checks.append({"name": check_name, "passed": passed, "detail": "watchOS font uses_rounded_variant must be true (SF Compact Rounded). Submission has false."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 10: tvOS tab bar position must be TOP (not bottom) ----
    check_name = "tvos_tab_position_violation_detected"
    try:
        tv_section = report.get("platforms", {}).get("tvos", report.get("tvos", {}))
        tv_str = json.dumps(tv_section).lower()
        passed = False
        # Submission has position: bottom — tvOS tab bar is at TOP
        if "top" in tv_str and ("tab" in tv_str or "position" in tv_str):
            passed = True
        if not passed:
            passed = "top" in report_text and "tvos" in report_text and ("tab" in report_text or "position" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "tvOS tab bar is at the TOP of the screen, not bottom. Submission has position: bottom."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 11: tvOS minimum touch target must be 250pt (not 150pt) ----
    check_name = "tvos_touch_target_violation_detected"
    try:
        tv_section = report.get("platforms", {}).get("tvos", report.get("tvos", {}))
        tv_str = json.dumps(tv_section).lower()
        passed = False
        # Submission has 150pt — must be 250pt
        if "250" in tv_str:
            passed = True
        if not passed:
            passed = "250" in report_text and ("tvos" in report_text or "tv" in report_text) and ("touch" in report_text or "target" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "tvOS minimum touch target must be 250pt. Submission has 150pt."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 12: macOS minimum window size violation (480x320 < 600x400) ----
    check_name = "macos_window_size_violation_detected"
    try:
        mac_section = report.get("platforms", {}).get("macos", report.get("macos", {}))
        mac_str = json.dumps(mac_section).lower()
        passed = False
        # Submission has 480x320 — minimum is 600x400
        if "600" in mac_str or ("400" in mac_str and "window" in mac_str):
            passed = True
        if not passed:
            passed = "600" in report_text and ("macos" in report_text or "mac" in report_text) and ("window" in report_text or "width" in report_text)
        checks.append({"name": check_name, "passed": passed, "detail": "macOS document window minimum is 600x400pt. Submission has 480x320pt."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- CHECK 13: Report has structured violations or corrections section ----
    check_name = "report_has_structured_violations"
    try:
        # Report should have some organized structure — violations, corrections, or compliance status
        has_structure = False
        for key in ["violations", "issues", "corrections", "compliance", "findings", "errors", "non_compliant"]:
            if key in report or key in report_text:
                has_structure = True
                break
        # Also accept if platforms are individually annotated
        if not has_structure:
            platforms_present = "ios" in report_text and "tvos" in report_text and "watchos" in report_text
            has_structure = platforms_present and len(report) >= 2
        checks.append({"name": check_name, "passed": has_structure, "detail": "Report must have structured content covering multiple platforms with violations/corrections."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Error: {e}"})

    # ---- SCORING ----
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 10  # Must get at least 10/13

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))