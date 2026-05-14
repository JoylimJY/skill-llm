import sys
import json
import re
from pathlib import Path

def find_prd(workspace: Path):
    """Find the PRD file - should be at docs/prd.md or similar."""
    # Check canonical location first
    canonical = workspace / "docs" / "prd.md"
    if canonical.exists():
        return canonical
    # Fallback: search for any prd*.md
    candidates = list(workspace.rglob("prd*.md"))
    # Exclude the old weatherapp PRD
    candidates = [c for c in candidates if "weatherapp" not in c.name and "weather" not in str(c)]
    if candidates:
        return candidates[0]
    return None

def check_word_count(text: str, min_words: int) -> bool:
    return len(text.split()) >= min_words

def run_checks(workspace_path: str):
    workspace = Path(workspace_path)
    checks = []
    passed_count = 0

    # ── 1. PRD file exists ────────────────────────────────────────────────────
    prd_path = find_prd(workspace)
    prd_exists = prd_path is not None
    checks.append({
        "name": "PRD file created at docs/prd.md (or equivalent)",
        "passed": prd_exists,
        "detail": f"Found at: {prd_path}" if prd_exists else "No PRD file found. Expected docs/prd.md"
    })

    if not prd_exists:
        # Can't run further checks
        for name in [
            "Problem statement ≥ 30 words",
            "ICP and JTBD section present",
            "3–5 features with measurable acceptance criteria",
            "KPIs with units and Kill/Iterate/Scale thresholds",
            "S.E.E.D. dimensions scored (S, E, E, D)",
            "Two separate scores: Optimistic AND Realistic",
            "Devil's Advocate section with ≥5 failure scenarios",
            "Unit economics table with both optimistic and pessimistic columns",
            "Dead startup precedents section",
            "Manifest conflicts section (explicit list)",
            "STREAM 6-layer analysis present (all 6 layers)",
            "Stack selection is nextjs-supabase (matches product_type: web from research.md)",
            "'If I'm wrong about...' statement present",
            "Recommended next action is a valid framework option",
            "Risks section with ≥3 risks and mitigation plans",
        ]:
            checks.append({"name": name, "passed": False, "detail": "PRD file not found; cannot evaluate."})
        total = len(checks)
        score = 1.0 / total  # only the existence check can possibly pass
        return {"passed": False, "score": round(score, 3), "checks": checks}

    try:
        content = prd_path.read_text(encoding="utf-8", errors="replace")
        content_lower = content.lower()
    except Exception as e:
        checks.append({"name": "PRD file readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Problem statement ≥ 30 words ──────────────────────────────────────
    # Look for "problem" section and check word count of paragraph following it
    prob_match = re.search(
        r'(?:##?\s*problem[^\n]*\n)(.*?)(?=\n##|\Z)',
        content_lower, re.DOTALL | re.IGNORECASE
    )
    if prob_match:
        prob_text = prob_match.group(1).strip()
        prob_wc = len(prob_text.split())
        prob_ok = prob_wc >= 30
        detail = f"Problem section found, word count: {prob_wc}"
    else:
        # Fallback: check if any paragraph near the top has 30+ words about a problem
        prob_ok = False
        detail = "No dedicated 'Problem' section found in PRD"
    checks.append({"name": "Problem statement ≥ 30 words", "passed": prob_ok, "detail": detail})

    # ── 3. ICP and JTBD ──────────────────────────────────────────────────────
    has_icp = bool(re.search(r'\bicp\b|ideal customer|target segment', content_lower))
    has_jtbd = bool(re.search(r'\bjtbd\b|jobs.to.be.done|job.to.be.done', content_lower))
    icp_jtbd_ok = has_icp and has_jtbd
    checks.append({
        "name": "ICP and JTBD section present",
        "passed": icp_jtbd_ok,
        "detail": f"ICP found: {has_icp}, JTBD found: {has_jtbd}"
    })

    # ── 4. Features with acceptance criteria ─────────────────────────────────
    has_features = bool(re.search(r'feature|acceptance criteria|acceptance criterion', content_lower))
    # Count features: look for numbered/bulleted feature items
    feature_count = len(re.findall(
        r'(?:feature\s*\d|##?\s*feature|\n[-*]\s+\*\*feature|\bfeature\s+\d)',
        content_lower
    ))
    ac_present = bool(re.search(r'acceptance criteri', content_lower))
    feat_ok = has_features and ac_present and (feature_count >= 2 or has_features)
    checks.append({
        "name": "3–5 features with measurable acceptance criteria",
        "passed": feat_ok,
        "detail": f"Features section present: {has_features}, Acceptance criteria: {ac_present}, Feature count heuristic: {feature_count}"
    })

    # ── 5. KPIs with Kill/Iterate/Scale thresholds ───────────────────────────
    has_kpis = bool(re.search(r'\bkpi\b|key performance', content_lower))
    has_thresholds = bool(re.search(r'kill|iterate|scale', content_lower))
    kpi_units = bool(re.search(r'(?:daily|weekly|monthly|per day|per week|\/day|\/week|\/month|\%)', content_lower))
    kpi_ok = has_kpis and has_thresholds and kpi_units
    checks.append({
        "name": "KPIs with units and Kill/Iterate/Scale thresholds",
        "passed": kpi_ok,
        "detail": f"KPIs: {has_kpis}, Thresholds (Kill/Iterate/Scale): {has_thresholds}, Units: {kpi_units}"
    })

    # ── 6. S.E.E.D. dimensions ───────────────────────────────────────────────
    has_seed = bool(re.search(r's\.e\.e\.d|seed.*(?:score|check|niche)|searchability|evidence.*ease|demand', content_lower))
    seed_dimensions = all([
        bool(re.search(r'searchab', content_lower)),
        bool(re.search(r'evidence', content_lower)),
        bool(re.search(r'ease|easy', content_lower)),
        bool(re.search(r'demand', content_lower)),
    ])
    seed_ok = has_seed or seed_dimensions
    checks.append({
        "name": "S.E.E.D. dimensions scored (S, E, E, D)",
        "passed": seed_ok,
        "detail": f"SEED section/keywords found: {has_seed}, All 4 dimensions (S/E/E/D): {seed_dimensions}"
    })

    # ── 7. Two separate scores: Optimistic AND Realistic ──────────────────────
    # This is the key proprietary trap: MUST have BOTH optimistic and realistic scores
    has_optimistic = bool(re.search(r'optimistic\s*score|score.*optimistic', content_lower))
    has_realistic = bool(re.search(r'realistic\s*score|score.*realistic', content_lower))
    # Also accept if they appear as a table or paired scores
    has_two_scores = has_optimistic and has_realistic
    if not has_two_scores:
        # Softer check: both words appear near "score" or a number
        has_two_scores = bool(re.search(r'optimistic.*\d+.*\/.*10|optimistic.*\d+\s*/\s*10', content_lower)) and \
                         bool(re.search(r'realistic.*\d+.*\/.*10|realistic.*\d+\s*/\s*10', content_lower))
    checks.append({
        "name": "Two separate scores: Optimistic AND Realistic",
        "passed": has_two_scores,
        "detail": f"Optimistic score found: {has_optimistic}, Realistic score found: {has_realistic}. Both are REQUIRED by the scoring methodology."
    })

    # ── 8. Devil's Advocate section with ≥5 failure scenarios ────────────────
    has_da = bool(re.search(r"devil'?s?\s*advocate|inversion|ways.*fail|fail.*ways", content_lower))
    # Count failure scenario indicators
    failure_items = re.findall(
        r'(?:^\s*[-*\d]+[.)]\s+.{20,})',
        content, re.MULTILINE
    )
    # Look specifically in DA section
    da_match = re.search(
        r"(?:devil'?s?\s*advocate|inversion)(.*?)(?=\n##|\Z)",
        content, re.DOTALL | re.IGNORECASE
    )
    da_list_count = 0
    if da_match:
        da_text = da_match.group(1)
        da_list_count = len(re.findall(r'(?:^\s*[-*\d]+[.)]\s+|\n\s*[-*\d]+[.)]\s+)', da_text))
    da_ok = has_da and (da_list_count >= 3 or len(failure_items) >= 5)
    checks.append({
        "name": "Devil's Advocate section with ≥5 failure scenarios",
        "passed": da_ok,
        "detail": f"DA section present: {has_da}, List items in DA section: {da_list_count}, Total list items in doc: {len(failure_items)}"
    })

    # ── 9. Unit economics: BOTH optimistic AND pessimistic columns ────────────
    # Key proprietary trap: must show BOTH, not just optimistic
    has_unit_econ = bool(re.search(r'unit economics|ltv|ltv.*cac|cac.*ltv', content_lower))
    has_pessimistic_econ = bool(re.search(r'pessimistic', content_lower))
    has_churn_data = bool(re.search(r'churn', content_lower))
    # Must have a table or structured comparison with both columns
    has_econ_table = bool(re.search(
        r'(?:optimistic.*pessimistic|pessimistic.*optimistic)',
        content_lower
    ))
    econ_ok = has_unit_econ and has_pessimistic_econ and has_churn_data
    checks.append({
        "name": "Unit economics table with both optimistic and pessimistic columns",
        "passed": econ_ok,
        "detail": f"Unit economics section: {has_unit_econ}, Pessimistic column: {has_pessimistic_econ}, Churn data: {has_churn_data}, Dual-column table: {has_econ_table}"
    })

    # ── 10. Dead startup precedents ───────────────────────────────────────────
    has_dead_startups = bool(re.search(
        r'dead startup|failed startup|shut down|pivoted|agrisnap|pivot.*agri',
        content_lower
    ))
    # AgriSnap is mentioned in research.md as having pivoted — agent should find and include it
    has_agrisnap = bool(re.search(r'agrisnap', content_lower))
    dead_ok = has_dead_startups
    checks.append({
        "name": "Dead startup precedents section (incl. AgriSnap from research.md)",
        "passed": dead_ok,
        "detail": f"Dead startup section/keywords: {has_dead_startups}, AgriSnap specifically cited: {has_agrisnap}"
    })

    # ── 11. Manifest conflicts section ───────────────────────────────────────
    has_manifest = bool(re.search(r'manifest|principle violation|conflicts.*principle|violat', content_lower))
    # Must mention specific principle numbers or names from the checklist
    has_specific_violations = bool(re.search(
        r'privacy.first|subscription fatigue|ai as foundation|exploitation|creators.*robot|principle\s+[1-9]',
        content_lower
    ))
    manifest_ok = has_manifest
    checks.append({
        "name": "Manifest conflicts section (explicit principle violations listed)",
        "passed": manifest_ok,
        "detail": f"Manifest section present: {has_manifest}, Specific principle names cited: {has_specific_violations}"
    })

    # ── 12. STREAM 6-layer analysis (all 6 layers) ────────────────────────────
    stream_present = bool(re.search(r'\bstream\b', content_lower))
    layers_found = []
    layer_patterns = [
        (1, r'layer\s*1|scope|map.*territory'),
        (2, r'layer\s*2|time.*entropy|lindy|entropy.*time'),
        (3, r'layer\s*3|route|inversion'),
        (4, r'layer\s*4|stakes|asymmetr|antifragil'),
        (5, r'layer\s*5|audience|reputation|network'),
        (6, r'layer\s*6|meta|mortality|balance'),
    ]
    for num, pattern in layer_patterns:
        found = bool(re.search(pattern, content_lower))
        layers_found.append(found)
    layers_count = sum(layers_found)
    stream_ok = stream_present and layers_count >= 4
    checks.append({
        "name": "STREAM 6-layer analysis present (all 6 layers)",
        "passed": stream_ok,
        "detail": f"STREAM mentioned: {stream_present}, Layers found: {layers_count}/6, Per-layer: {[f'L{i+1}:{v}' for i,v in enumerate(layers_found)]}"
    })

    # ── 13. Stack selection is nextjs-supabase ────────────────────────────────
    # research.md has product_type: web → should auto-select nextjs-supabase
    has_nextjs = bool(re.search(r'nextjs.supabase|next\.js.*supabase|supabase.*next\.js|nextjs-supabase', content_lower))
    has_stack_section = bool(re.search(r'tech stack|stack|architecture', content_lower))
    stack_ok = has_nextjs
    checks.append({
        "name": "Stack selection is nextjs-supabase (matches product_type: web from research.md)",
        "passed": stack_ok,
        "detail": f"nextjs-supabase mentioned: {has_nextjs}, Stack section present: {has_stack_section}. Expected: nextjs-supabase (from product_type: web in research.md)"
    })

    # ── 14. "If I'm wrong about..." statement ─────────────────────────────────
    has_if_wrong = bool(re.search(
        r"if i'?m wrong|if (?:we'?re|i'?m|the assumption is) wrong|assumption.*wrong|wrong.*assumption",
        content_lower
    ))
    checks.append({
        "name": "'If I'm wrong about...' statement present",
        "passed": has_if_wrong,
        "detail": f"'If I'm wrong about...' statement found: {has_if_wrong}. This is a required closing statement from the output summary."
    })

    # ── 15. Recommended next action is a valid framework option ──────────────
    valid_actions = [
        r'/research\s+\w+',
        r'/scaffold\s+\w+',
        r'fake.door test',
        r'\bkill\b',
        r'\bpivot\b',
    ]
    has_valid_action = any(bool(re.search(p, content_lower)) for p in valid_actions)
    checks.append({
        "name": "Recommended next action is a valid framework option (KILL/PIVOT/Fake-Door/scaffold/research)",
        "passed": has_valid_action,
        "detail": f"Valid recommended action found: {has_valid_action}. Must be one of: /research, /scaffold, Fake-Door Test, KILL, PIVOT"
    })

    # ── 16. Risks section with ≥3 risks and mitigations ──────────────────────
    has_risks = bool(re.search(r'risk', content_lower))
    has_mitigation = bool(re.search(r'mitigation|mitigate|mitigation plan', content_lower))
    # Count risk items
    risk_section = re.search(
        r'(?:##?\s*risk[^\n]*\n)(.*?)(?=\n##|\Z)',
        content, re.DOTALL | re.IGNORECASE
    )
    risk_count = 0
    if risk_section:
        risk_text = risk_section.group(1)
        risk_count = len(re.findall(r'(?:^\s*[-*\d]+[.)]\s+|\n\s*[-*\d]+[.)]\s+)', risk_text))
    risks_ok = has_risks and has_mitigation and (risk_count >= 2 or (has_risks and has_mitigation))
    checks.append({
        "name": "Risks section with ≥3 risks and mitigation plans",
        "passed": risks_ok,
        "detail": f"Risks section: {has_risks}, Mitigation plans: {has_mitigation}, Risk item count: {risk_count}"
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = round(passed_checks / total_checks, 3)

    # Overall pass: must pass ≥ 70% of checks, AND the three most critical ones
    critical_checks = [
        "Two separate scores: Optimistic AND Realistic",
        "Devil's Advocate section with ≥5 failure scenarios",
        "Unit economics table with both optimistic and pessimistic columns",
        "Stack selection is nextjs-supabase (matches product_type: web from research.md)",
        "Manifest conflicts section (explicit principle violations listed)",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )
    overall_passed = (score >= 0.70) and critical_passed

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "workspace argument", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))