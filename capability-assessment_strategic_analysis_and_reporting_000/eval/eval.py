import sys
import re
import json
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # Find the output file
    candidates = list(workspace_path.rglob("medicore_capability_assessment.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                         "detail": "File 'medicore_capability_assessment.md' not found anywhere in workspace."}]
        }

    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, "detail": str(e)}]
        }

    # ── CHECK 1: Top-level header with company name ──────────────────────────
    check1_passed = bool(re.search(r'##\s+Capability Assessment.*MediCore', content, re.IGNORECASE))
    checks.append({
        "name": "top_level_header_with_company",
        "passed": check1_passed,
        "detail": "Must contain '## Capability Assessment: MediCore...' header."
    })

    # ── CHECK 2: Capability Radar section exists ─────────────────────────────
    check2_passed = bool(re.search(r'###\s+Capability Radar', content, re.IGNORECASE))
    checks.append({
        "name": "capability_radar_section_exists",
        "passed": check2_passed,
        "detail": "Must contain '### Capability Radar' section header."
    })

    # ── CHECK 3: ASCII radar uses ★ symbols ──────────────────────────────────
    star_count = content.count('★')
    check3_passed = star_count >= 2
    checks.append({
        "name": "radar_ascii_uses_star_symbol",
        "passed": check3_passed,
        "detail": f"ASCII radar must use ★ at axis endpoints. Found {star_count} ★ symbols (need ≥2)."
    })

    # ── CHECK 4: Radar has slash/backslash arm structure ─────────────────────
    has_slashes = bool(re.search(r'[/\\]{2,}', content))
    has_dashes = bool(re.search(r'─{5,}', content))
    check4_passed = has_slashes and has_dashes
    checks.append({
        "name": "radar_ascii_arm_structure",
        "passed": check4_passed,
        "detail": f"ASCII radar must use / \\ arms and ─── horizontal axis. slashes={has_slashes}, dashes={has_dashes}."
    })

    # ── CHECK 5: All 6 capabilities appear in the scores table ───────────────
    required_capabilities = [
        "Regulatory",
        "Clinical AI",
        "Data Infrastructure",
        "Patient Experience",
        "Interoperability",
        "Talent"
    ]
    missing_caps = [cap for cap in required_capabilities if cap.lower() not in content.lower()]
    check5_passed = len(missing_caps) == 0
    checks.append({
        "name": "all_six_capabilities_present",
        "passed": check5_passed,
        "detail": f"Missing capabilities: {missing_caps}" if missing_caps else "All 6 capabilities found."
    })

    # ── CHECK 6: Capability Scores section with correct columns ──────────────
    check6_passed = bool(re.search(r'###\s+Capability Scores', content, re.IGNORECASE))
    has_table_headers = bool(re.search(r'\|\s*Capability\s*\|.*Our Score.*\|.*Benchmark.*\|.*Gap.*\|.*Priority', content, re.IGNORECASE))
    check6_passed = check6_passed and has_table_headers
    checks.append({
        "name": "capability_scores_table_structure",
        "passed": check6_passed,
        "detail": "Must have '### Capability Scores' and table with Capability|Our Score|Benchmark|Gap|Priority columns."
    })

    # ── CHECK 7: Correct Our Scores ──────────────────────────────────────────
    # Expected: Regulatory=8, Clinical AI=5, Data Infra=6, Patient Exp=7, Interop=4, Talent=6
    expected_our_scores = {
        "regulatory": 8,
        "clinical ai": 5,
        "data infrastructure": 6,
        "patient experience": 7,
        "interoperability": 4,
        "talent": 6,
    }
    # Parse table rows: look for lines with | ... | X/10 | Y/10 |
    table_rows = re.findall(r'\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|([^|]+)\|', content)
    score_errors = []
    found_scores = {}
    for row in table_rows:
        cap_cell = row[0].strip().lower()
        our_score_cell = row[1].strip()
        benchmark_cell = row[2].strip()

        for cap_key in expected_our_scores:
            if cap_key in cap_cell:
                m = re.search(r'(\d+)', our_score_cell)
                if m:
                    found_scores[cap_key] = int(m.group(1))

    score_mismatches = []
    for cap_key, expected_val in expected_our_scores.items():
        if cap_key in found_scores:
            if found_scores[cap_key] != expected_val:
                score_mismatches.append(f"{cap_key}: expected {expected_val}, got {found_scores[cap_key]}")
        else:
            score_mismatches.append(f"{cap_key}: score not found in table")

    check7_passed = len(score_mismatches) == 0
    checks.append({
        "name": "correct_our_scores_in_table",
        "passed": check7_passed,
        "detail": f"Score mismatches: {score_mismatches}" if score_mismatches else "All our scores correct."
    })

    # ── CHECK 8: Correct Benchmark Scores ────────────────────────────────────
    # Expected: Regulatory=9, Clinical AI=9, Data Infra=8, Patient Exp=8, Interop=9, Talent=7
    expected_benchmarks = {
        "regulatory": 9,
        "clinical ai": 9,
        "data infrastructure": 8,
        "patient experience": 8,
        "interoperability": 9,
        "talent": 7,
    }
    found_benchmarks = {}
    for row in table_rows:
        cap_cell = row[0].strip().lower()
        benchmark_cell = row[2].strip()
        for cap_key in expected_benchmarks:
            if cap_key in cap_cell:
                m = re.search(r'(\d+)', benchmark_cell)
                if m:
                    found_benchmarks[cap_key] = int(m.group(1))

    bench_mismatches = []
    for cap_key, expected_val in expected_benchmarks.items():
        if cap_key in found_benchmarks:
            if found_benchmarks[cap_key] != expected_val:
                bench_mismatches.append(f"{cap_key}: expected {expected_val}, got {found_benchmarks[cap_key]}")
        else:
            bench_mismatches.append(f"{cap_key}: benchmark score not found in table")

    check8_passed = len(bench_mismatches) == 0
    checks.append({
        "name": "correct_benchmark_scores_in_table",
        "passed": check8_passed,
        "detail": f"Benchmark mismatches: {bench_mismatches}" if bench_mismatches else "All benchmark scores correct."
    })

    # ── CHECK 9: Gap values correctly computed and signed ────────────────────
    # Gap = Our - Benchmark
    # Regulatory: 8-9=-1, Clinical AI: 5-9=-4, Data Infra: 6-8=-2,
    # Patient Exp: 7-8=-1, Interop: 4-9=-5, Talent: 6-7=-1
    expected_gaps = {
        "regulatory": -1,
        "clinical ai": -4,
        "data infrastructure": -2,
        "patient experience": -1,
        "interoperability": -5,
        "talent": -1,
    }
    found_gaps = {}
    for row in table_rows:
        cap_cell = row[0].strip().lower()
        gap_cell = row[3].strip()
        for cap_key in expected_gaps:
            if cap_key in cap_cell:
                m = re.search(r'([+-]?\d+)', gap_cell)
                if m:
                    found_gaps[cap_key] = int(m.group(1))

    gap_errors = []
    for cap_key, expected_val in expected_gaps.items():
        if cap_key in found_gaps:
            if found_gaps[cap_key] != expected_val:
                gap_errors.append(f"{cap_key}: expected {expected_val:+d}, got {found_gaps[cap_key]:+d}")
        else:
            gap_errors.append(f"{cap_key}: gap not found")

    check9_passed = len(gap_errors) == 0
    checks.append({
        "name": "correct_gap_values_with_sign",
        "passed": check9_passed,
        "detail": f"Gap errors: {gap_errors}" if gap_errors else "All gap values correct with proper sign."
    })

    # ── CHECK 10: Priority labels use exact proprietary vocabulary ───────────
    # All gaps are negative → no ✅ Strength expected
    # Severity: Interop=-5 → Critical, Clinical AI=-4 → Critical, 
    # Data Infra=-2 → High, Regulatory=-1 → Medium, Patient Exp=-1 → Medium, Talent=-1 → Medium
    # The skill defines: positive gap = ✅ Strength
    # The skill example: -1=Medium, -2=High, -3=Critical (by analogy, -4/-5 also Critical)
    has_critical = bool(re.search(r'Critical', content))
    has_high = bool(re.search(r'\bHigh\b', content))
    has_medium = bool(re.search(r'\bMedium\b', content))
    no_spurious_strength = not bool(re.search(r'✅\s*Strength', content))  # none should be strength
    check10_passed = has_critical and has_high and has_medium and no_spurious_strength
    checks.append({
        "name": "priority_labels_use_exact_vocabulary",
        "passed": check10_passed,
        "detail": (
            f"has_critical={has_critical}, has_high={has_high}, has_medium={has_medium}, "
            f"no_spurious_strength={no_spurious_strength}. "
            "Expected Critical/High/Medium labels; no '✅ Strength' since all gaps are negative."
        )
    })

    # ── CHECK 11: Capability Details section with Strengths and Gaps ─────────
    has_details_section = bool(re.search(r'###\s+Capability Details', content, re.IGNORECASE))
    has_strengths_subsection = bool(re.search(r'\*\*Strengths\*\*', content))
    has_gaps_subsection = bool(re.search(r'\*\*Gaps\*\*', content))
    check11_passed = has_details_section and has_strengths_subsection and has_gaps_subsection
    checks.append({
        "name": "capability_details_section_structure",
        "passed": check11_passed,
        "detail": f"has_details={has_details_section}, has_strengths={has_strengths_subsection}, has_gaps={has_gaps_subsection}."
    })

    # ── CHECK 12: Investment Priorities section exists and is ordered list ────
    has_invest_section = bool(re.search(r'###\s+Investment Priorities', content, re.IGNORECASE))
    # Should have numbered list items for gaps
    numbered_items = re.findall(r'^\s*\d+\.\s+\*\*', content, re.MULTILINE)
    check12_passed = has_invest_section and len(numbered_items) >= 3
    checks.append({
        "name": "investment_priorities_ordered_list",
        "passed": check12_passed,
        "detail": f"has_section={has_invest_section}, numbered_bold_items={len(numbered_items)} (need ≥3)."
    })

    # ── CHECK 13: Investment Priorities use the required format ──────────────
    # Format: "Gap: X, Impact: Y → Action: [description]"
    priority_format_matches = re.findall(r'Gap:\s*[-\d]+.*Impact:\s*\w+.*→\s*Action:', content)
    check13_passed = len(priority_format_matches) >= 3
    checks.append({
        "name": "investment_priorities_format",
        "passed": check13_passed,
        "detail": f"Found {len(priority_format_matches)} entries matching 'Gap: X, Impact: Y → Action:' (need ≥3)."
    })

    # ── CHECK 14: Interoperability correctly identified as most critical ──────
    # Interop has gap of -5, the largest deficit, must appear as first investment priority
    # or be labelled Critical
    interop_critical = bool(re.search(r'[Ii]nteroperab\w*.*Critical|Critical.*[Ii]nteroperab', content))
    # Also check if it appears first in investment priorities
    invest_section = re.search(r'###\s+Investment Priorities(.*?)(?=###|\Z)', content, re.DOTALL | re.IGNORECASE)
    interop_first = False
    if invest_section:
        invest_text = invest_section.group(1)
        first_item = re.search(r'1\.\s+\*\*([^*]+)\*\*', invest_text)
        if first_item:
            interop_first = 'interop' in first_item.group(1).lower() or 'integration' in first_item.group(1).lower()
    check14_passed = interop_critical or interop_first
    checks.append({
        "name": "interoperability_highest_priority",
        "passed": check14_passed,
        "detail": f"interop_critical={interop_critical}, interop_first_in_priorities={interop_first}. Interop gap=-5, must be Critical and/or first priority."
    })

    # ── CHECK 15: Legend in radar (Our Company vs Benchmark lines) ───────────
    has_legend = bool(re.search(r'Our Company|─── Our|MediCore\s*$', content, re.MULTILINE | re.IGNORECASE))
    has_benchmark_legend = bool(re.search(r'Benchmark|Competitor|Apex|─ ─|-- |- -', content, re.IGNORECASE))
    check15_passed = has_legend and has_benchmark_legend
    checks.append({
        "name": "radar_legend_present",
        "passed": check15_passed,
        "detail": f"has_company_legend={has_legend}, has_benchmark_legend={has_benchmark_legend}."
    })

    # ── Score computation ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 11  # Must pass ≥11/15 checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))