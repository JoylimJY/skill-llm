import sys
import os
import json
import re
from pathlib import Path

def find_review_report(workspace):
    """Search for the CEO review report file in the workspace."""
    patterns = ["*review*", "*ceo*", "*CEO*", "*report*", "*audit*", "*strategic*"]
    candidates = []
    for pattern in patterns:
        candidates.extend(Path(workspace).rglob(pattern))
    # Also check for .md and .txt files at root level
    for ext in ["*.md", "*.txt"]:
        candidates.extend(Path(workspace).glob(ext))
    # Filter out known source files
    known_sources = {
        "CLAUDE.md", "TODOS.md", "architecture_overview.md",
        "drug_interaction_design.md"
    }
    filtered = [
        c for c in candidates
        if c.is_file() and c.name not in known_sources
    ]
    return filtered

def load_report(workspace):
    """Load the review report content."""
    candidates = find_review_report(workspace)
    if not candidates:
        # Last resort: look for any new .md or .txt files not in our known set
        known = {
            "CLAUDE.md", "TODOS.md", "architecture_overview.md",
            "drug_interaction_design.md"
        }
        for ext in ["*.md", "*.txt", "*.log"]:
            for f in Path(workspace).rglob(ext):
                if f.name not in known and f.is_file():
                    candidates.append(f)
    if not candidates:
        return None, None
    # Prefer files with "review" or "ceo" in name
    for c in candidates:
        if any(kw in c.name.lower() for kw in ["review", "ceo", "report", "audit"]):
            return c, c.read_text(errors="replace")
    # Fall back to largest file among candidates
    candidates.sort(key=lambda f: f.stat().st_size, reverse=True)
    return candidates[0], candidates[0].read_text(errors="replace")

def check_system_audit_evidence(content):
    """Check if the agent ran system audit commands and used the results."""
    indicators = [
        r"git log",
        r"TODO|FIXME|HACK|XXX",
        r"CLAUDE\.md",
        r"TODOS\.md",
        r"drug_interaction_design",
        r"\.context",
    ]
    hits = sum(1 for pat in indicators if re.search(pat, content, re.IGNORECASE))
    return hits >= 3, f"Found {hits}/6 system audit indicators"

def check_premise_challenges(content):
    """Check for premise challenge section (Step 0A)."""
    patterns = [
        r"前提|premise|challenge",
        r"correct.*problem|right.*problem|wrong.*problem|解决.*正确|正确.*问题",
        r"alternative|what if.*do nothing|不做|cost of inaction",
        r"user.*outcome|business.*outcome|业务.*结果|用户.*结果",
    ]
    hits = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
    return hits >= 2, f"Premise challenge indicators: {hits}/4"

def check_implementation_alternatives(content):
    """Check for 2-3 implementation alternatives with required fields."""
    # Check for at least 2 alternative sections
    alt_section = re.search(
        r"(方案|approach|alternative|option|plan)[^\n]*[AB12]",
        content, re.IGNORECASE
    )
    
    # Check for effort labels S/M/L/XL
    effort_labels = re.search(r'\b(S|M|L|XL)\b.*effort|effort.*\b(S|M|L|XL)\b', content, re.IGNORECASE)
    # Also check for Chinese context
    effort_any = re.search(r'努力|effort.*[SMLsml]|[SMLsml].*effort|\bS\b|\bM\b|\bL\b|\bXL\b', content)
    
    # Check for risk labels
    risk_labels = re.search(r'风险|risk.*(低|中|高|low|medium|high)', content, re.IGNORECASE)
    
    # Check for MVP/minimum viable alternative
    mvp = re.search(r'最小可行|MVP|minimum.*viable|minimal', content, re.IGNORECASE)
    
    # Check for ideal architecture alternative
    ideal = re.search(r'理想架构|ideal.*arch|best.*long.*term|optimal.*arch|理想.*设计', content, re.IGNORECASE)
    
    # Count alternative blocks (方案 A, B, C or Approach A, B, C)
    alt_blocks = len(re.findall(r'(方案\s*[A-C]|Approach\s*[A-C]|Option\s*[A-C]|Plan\s*[A-C]|\b[A-C]\)|\bApproach\s+\d)', content, re.IGNORECASE))
    
    checks = {
        "alt_section": bool(alt_section),
        "effort_labels": bool(effort_labels or effort_any),
        "risk_labels": bool(risk_labels),
        "mvp_present": bool(mvp),
        "ideal_arch_present": bool(ideal),
        "multiple_alternatives": alt_blocks >= 2,
    }
    
    passed_count = sum(checks.values())
    detail = f"Alternatives checks: {passed_count}/6 — " + ", ".join(
        f"{k}={'✓' if v else '✗'}" for k, v in checks.items()
    )
    return passed_count >= 4, detail

def check_mode_selection(content):
    """Check that a review mode is specified."""
    modes = [
        r"EXPANSION",
        r"SELECTIVE.*EXPANSION|SELECTIVE",
        r"HOLD.*SCOPE|HOLD SCOPE",
        r"SCOPE.*REDUCTION|REDUCTION",
    ]
    found = [bool(re.search(p, content, re.IGNORECASE)) for p in modes]
    any_mode = any(found)
    return any_mode, f"Mode found: {any_mode} — matches: {found}"

def check_failure_modes(content):
    """Check for specific named failure modes (not generic 'handle errors')."""
    # Generic catch-all patterns (bad)
    generic_error = re.search(r'catch.*[Ee]xception|rescue.*StandardError|bare.*except', content, re.IGNORECASE)
    
    # Specific failure mode naming (good)
    specific_failures = re.findall(
        r'(timeout|503|connection.*refused|null.*pointer|NullPointer|KeyError|'
        r'circuit.*break|rate.*limit|AI.*down|service.*unavailable|'
        r'SMS.*fail|latency.*exceed|threshold|confidence.*score|'
        r'HIPAA|PHI|audit.*fail|feature.*flag|ff_drug)',
        content, re.IGNORECASE
    )
    
    has_specific = len(set(specific_failures)) >= 3
    flags_generic = bool(generic_error)
    
    detail = f"Specific failure modes: {len(set(specific_failures))} unique — generic catch flagged: {flags_generic}"
    return has_specific, detail

def check_shadow_paths(content):
    """Check for the three shadow paths per data flow."""
    shadow_indicators = [
        r"nil.*input|null.*input|空.*输入|empty.*input",
        r"empty.*list|zero.*length|空.*列表|长度为零|no.*medications|empty.*rxcui",
        r"upstream.*error|上游.*错误|AI.*service.*down|service.*unavailable|AI.*失败",
        r"shadow.*path|影子路径|happy.*path|快乐路径",
    ]
    hits = sum(1 for p in shadow_indicators if re.search(p, content, re.IGNORECASE))
    return hits >= 2, f"Shadow path indicators found: {hits}/4"

def check_ascii_diagram(content):
    """Check for ASCII art diagram (mandatory per SKILL.md section 6)."""
    # Look for ASCII art patterns: boxes, arrows, flow indicators
    ascii_patterns = [
        r'[┌─┐│└┘├┤┬┴┼]',  # box-drawing chars
        r'\+-+\+',           # ASCII box corners
        r'--+>|<--+',        # ASCII arrows
        r'\|.*\|.*\|',       # table-style vertical bars
        r'={3,}',            # separator lines
        r'\[.*\].*-+>.*\[',  # [A] --> [B] style flow
        r'v\n.*v|↓|→|←',    # vertical flow indicators
        r'[A-Z][a-zA-Z\s]+\s*[-─]{2,}[>→]\s*[A-Z]',  # Component --> Component
    ]
    hits = sum(1 for p in ascii_patterns if re.search(p, content))
    return hits >= 2, f"ASCII diagram indicators: {hits}/8"

def check_observability(content):
    """Check for observability as a first-class deliverable."""
    obs_patterns = [
        r'observ|可观测|observable|monitor',
        r'log|metric|trace|alert|alarm',
        r'dashboard|runbook|pagerduty|grafana|sentry',
        r'audit.*log|HIPAA.*log|patient.*log|confidence.*log',
    ]
    hits = sum(1 for p in obs_patterns if re.search(p, content, re.IGNORECASE))
    return hits >= 3, f"Observability indicators: {hits}/4"

def check_report_format(content):
    """Check for the proprietary report format structure."""
    format_checks = {
        "separator_line": bool(re.search(r'[═=]{10,}', content)),
        "mode_field": bool(re.search(r'模式|Mode.*:', content, re.IGNORECASE)),
        "status_field": bool(re.search(r'状态|Status.*:', content, re.IGNORECASE)),
        "valid_status": bool(re.search(
            r'\b(DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT)\b', content
        )),
        "failure_modes_field": bool(re.search(r'失败模式|Failure.*Mode', content, re.IGNORECASE)),
        "observability_field": bool(re.search(r'可观测性|Observability', content, re.IGNORECASE)),
        "edge_cases_field": bool(re.search(r'边缘情况|Edge.*Case', content, re.IGNORECASE)),
    }
    passed = sum(format_checks.values())
    detail = f"Format checks: {passed}/7 — " + str({k: v for k, v in format_checks.items() if not v})
    return passed >= 5, detail

def check_design_doc_usage(content):
    """Check that the agent read and used the .context design doc."""
    design_indicators = [
        r'200ms|latency.*200|200.*latency',
        r'BAA|Business.*Associate|HIPAA.*external',
        r'ff_drug_interaction|feature.*flag.*drug|drug.*feature.*flag',
        r'0\.85|confidence.*0\.|0\..*confidence|threshold.*0\.',
        r'prescriber.*SMS|SMS.*prescriber|notify.*prescriber',
        r'RxCUI|rxcui|RxNorm',
        r'3.*near.miss|near.miss.*3|clinical.*partner',
    ]
    hits = sum(1 for p in design_indicators if re.search(p, content, re.IGNORECASE))
    return hits >= 3, f"Design doc usage indicators: {hits}/7"

def check_error_mapping(content):
    """Check for specific error → catch → user feedback mapping."""
    error_map_indicators = [
        r'error.*map|错误.*映射|error→|exception.*→',
        r'what.*user.*see|用户.*看到|user.*feedback|user.*message',
        r'catch.*[A-Z][a-z]+Error|rescue.*[A-Z]|捕获.*异常',
        r'triggers?.*when|触发.*当|when.*trigger',
    ]
    hits = sum(1 for p in error_map_indicators if re.search(p, content, re.IGNORECASE))
    return hits >= 2, f"Error mapping indicators: {hits}/4"

def run_evaluation(workspace):
    checks = []

    # Find the report
    report_path, content = load_report(workspace)
    
    if not report_path or not content:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False, "detail": "No review report file found in workspace"}]
        }
    
    checks.append({
        "name": "report_exists",
        "passed": True,
        "detail": f"Report found at: {report_path}"
    })

    # Run all checks
    check_functions = [
        ("system_audit_evidence", check_system_audit_evidence),
        ("premise_challenges", check_premise_challenges),
        ("implementation_alternatives", check_implementation_alternatives),
        ("mode_selection", check_mode_selection),
        ("failure_modes_named", check_failure_modes),
        ("shadow_paths", check_shadow_paths),
        ("ascii_diagram", check_ascii_diagram),
        ("observability_first_class", check_observability),
        ("report_format_structure", check_report_format),
        ("design_doc_usage", check_design_doc_usage),
        ("error_mapping", check_error_mapping),
    ]

    for name, fn in check_functions:
        try:
            passed, detail = fn(content)
            checks.append({"name": name, "passed": passed, "detail": detail})
        except Exception as e:
            checks.append({"name": name, "passed": False, "detail": f"Exception during check: {e}"})

    # Score: each check equally weighted
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    # Overall pass: must pass at least 9/12 checks including critical ones
    critical_checks = {
        "implementation_alternatives", "failure_modes_named",
        "ascii_diagram", "report_format_structure", "design_doc_usage"
    }
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_pass = score >= 0.75 and critical_passed

    return {
        "passed": overall_pass,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_evaluation(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))