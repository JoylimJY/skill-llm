import sys
import json
import re
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight

    MAX_SCORE = 10.0  # sum of all weights below

    # ── 1. chart_data.json exists and is valid ───────────────────────────────
    chart_files = list(workspace.rglob("chart_data.json"))
    if not chart_files:
        # Also check /tmp
        tmp_chart = Path("/tmp/chart_data.json")
        if tmp_chart.exists():
            chart_files = [tmp_chart]

    if not chart_files:
        add("chart_data.json produced", False, "No chart_data.json found in workspace or /tmp", weight=1.0)
        chart_data = None
    else:
        try:
            chart_data = json.loads(chart_files[0].read_text())
            add("chart_data.json produced", True,
                f"Found at {chart_files[0]} with keys: {list(chart_data.keys())}", weight=1.0)
        except Exception as e:
            add("chart_data.json produced", False, f"JSON parse error: {e}", weight=1.0)
            chart_data = None

    # ── 2. chart_data.json has required metric keys ──────────────────────────
    if chart_data is not None:
        required_keys = {'rhr', 'hrv', 'vo2max', 'steps'}
        present = required_keys.intersection(chart_data.keys())
        ok = len(present) == len(required_keys)
        add("chart_data contains RHR/HRV/VO2Max/steps",
            ok, f"Present keys: {list(chart_data.keys())}", weight=1.0)

        # Check data has reasonable month count (>=6 months)
        rhr_months = len(chart_data.get('rhr', {}))
        ok2 = rhr_months >= 6
        add("chart_data has ≥6 months of RHR data", ok2,
            f"RHR monthly entries: {rhr_months}", weight=0.5)
    else:
        add("chart_data contains RHR/HRV/VO2Max/steps", False, "chart_data.json missing", weight=1.0)
        add("chart_data has ≥6 months of RHR data", False, "chart_data.json missing", weight=0.5)

    # ── 3. health_report.html exists ────────────────────────────────────────
    html_files = list(workspace.rglob("health_report.html"))
    if not html_files:
        add("health_report.html produced", False, "No health_report.html found anywhere in workspace", weight=1.5)
        html_content = None
    else:
        try:
            html_content = html_files[0].read_text(encoding='utf-8')
            add("health_report.html produced", True,
                f"Found at {html_files[0]}, size={len(html_content)} chars", weight=1.5)
        except Exception as e:
            add("health_report.html produced", False, f"Read error: {e}", weight=1.5)
            html_content = None

    if html_content is None:
        # Add remaining checks as failed
        for name, w in [
            ("Correct gender=female in report", 0.5),
            ("Correct age=34 in report", 0.5),
            ("Weight unit lb used (proprietary trap)", 1.0),
            ("Hyperthyroidism condition passed", 1.0),
            ("Correct RHR reference range (female 26-35)", 1.0),
            ("Correct HRV reference range (age 30-40)", 0.5),
            ("Correct VO2Max reference range (female 30-39)", 0.5),
            ("Activity=active → steps target 10000", 0.5),
            ("Verdict text present", 0.5),
        ]:
            add(name, False, "html missing", weight=w)
        result = {
            "passed": False,
            "score": round(total_score / MAX_SCORE, 3),
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    html_lower = html_content.lower()

    # ── 4. Gender: female ───────────────────────────────────────────────────
    has_female = 'female' in html_lower
    add("Correct gender=female in report", has_female,
        "Found 'female' in HTML" if has_female else "No 'female' keyword in HTML", weight=0.5)

    # ── 5. Age: 34 ──────────────────────────────────────────────────────────
    has_age = bool(re.search(r'\b34\b', html_content))
    add("Correct age=34 in report", has_age,
        "Found '34' in HTML" if has_age else "Age 34 not found in HTML", weight=0.5)

    # ── 6. Weight unit: lb (the KEY proprietary trap) ───────────────────────
    # The report must show weight_unit=lb and/or mention lb conversion
    has_lb = 'lb' in html_lower
    add("Weight unit lb used (proprietary trap)", has_lb,
        "Found 'lb' in HTML (correct Apple Health default weight unit)" if has_lb
        else "No 'lb' in HTML — agent likely passed wrong unit or skipped this", weight=1.0)

    # ── 7. Hyperthyroidism condition noted ───────────────────────────────────
    has_thyroid = ('hyperthyroid' in html_lower or
                   'thyroid' in html_lower or
                   '甲状腺' in html_content or
                   '甲亢' in html_content)
    add("Hyperthyroidism condition passed", has_thyroid,
        "Found thyroid-related content in HTML" if has_thyroid
        else "No thyroid reference in HTML — --conditions flag likely missing/wrong", weight=1.0)

    # ── 8. Correct RHR reference range for female 26-35 ────────────────────
    # Expected: excellent<55, good≤61, normal≤74, high≤83
    # At minimum, values 55 and 61 and/or 74 should appear in the RHR reference row
    has_rhr_ref = (
        bool(re.search(r'\b55\b', html_content)) and
        bool(re.search(r'\b61\b', html_content))
    )
    add("Correct RHR reference range (female 26-35)",
        has_rhr_ref,
        "Found RHR bracket values 55 and 61 for female 26-35" if has_rhr_ref
        else "RHR reference values 55/61 not found — wrong age bracket or gender", weight=1.0)

    # ── 9. Correct HRV reference for age 30-40: low=20, high=45 ────────────
    has_hrv_ref = (
        bool(re.search(r'\b20\b', html_content)) and
        bool(re.search(r'\b45\b', html_content))
    )
    add("Correct HRV reference range (age 30-40)",
        has_hrv_ref,
        "Found HRV bracket values 20 and 45 for age 30-40" if has_hrv_ref
        else "HRV reference values 20/45 not found — wrong age bracket applied", weight=0.5)

    # ── 10. Correct VO2Max reference for female 30-39 ───────────────────────
    # Expected: poor<28, fair≥28, good≥33, excellent≥41, elite≥46
    has_vo2_ref = (
        bool(re.search(r'\b28\b', html_content)) and
        bool(re.search(r'\b33\b', html_content))
    )
    add("Correct VO2Max reference range (female 30-39)",
        has_vo2_ref,
        "Found VO2Max bracket values 28 and 33 for female 30-39" if has_vo2_ref
        else "VO2Max reference values 28/33 not found — wrong age/gender bracket", weight=0.5)

    # ── 11. Activity=active → steps target 10000 ────────────────────────────
    has_steps_target = '10000' in html_content
    add("Activity=active → steps target 10000",
        has_steps_target,
        "Found '10000' steps target in HTML" if has_steps_target
        else "Steps target 10000 not found — activity level not mapped correctly", weight=0.5)

    # ── 12. Verdict text present (non-empty) ────────────────────────────────
    # Should not be placeholder/empty
    has_verdict = bool(re.search(r'综合评估|verdict|整体判断|overall|assessment', html_lower))
    add("Verdict text present", has_verdict,
        "Found verdict/assessment section in HTML" if has_verdict
        else "No verdict section found", weight=0.5)

    # ── Final scoring ────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(total_score / MAX_SCORE, 3)
    overall_passed = (score >= 0.75 and
                      any(c["name"] == "Weight unit lb used (proprietary trap)" and c["passed"] for c in checks) and
                      any(c["name"] == "Hyperthyroidism condition passed" and c["passed"] for c in checks))

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/workspace")