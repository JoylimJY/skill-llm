import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── Locate the output report ─────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("security_report.md"))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "security_report.md not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": str(report_path)})

    try:
        content = report_path.read_text()
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_readable", "passed": True, "detail": "File read OK."})

    # ── CHECK 1: Project name in header ─────────────────────────────────────
    has_project = "FinVault" in content or "finvault" in content.lower()
    checks.append({"name": "project_name_in_report", "passed": has_project,
                    "detail": "Expected 'FinVault' project name in report header."})

    # ── CHECK 2: Score out of 30 present ────────────────────────────────────
    # Format: [X/30]
    score_match = re.search(r'\[?\s*(\d+)\s*/\s*30\s*\]?', content)
    has_score_30 = score_match is not None
    checks.append({"name": "score_out_of_30", "passed": has_score_30,
                    "detail": f"Expected X/30 total score. Found: {score_match.group(0) if score_match else 'none'}"})

    # ── CHECK 3: Percentage present ─────────────────────────────────────────
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', content)
    has_pct = pct_match is not None
    pct_value = float(pct_match.group(1)) if pct_match else None
    checks.append({"name": "percentage_present", "passed": has_pct,
                    "detail": f"Expected a percentage value. Found: {pct_value}"})

    # ── CHECK 4: Total score is low (red-flag config should score low) ───────
    # Given the severely misconfigured input, total score should be <= 15/30
    total_score_val = int(score_match.group(1)) if score_match else None
    low_score = total_score_val is not None and total_score_val <= 15
    checks.append({"name": "total_score_reflects_risk", "passed": low_score,
                    "detail": f"Config is severely misconfigured; expected total <=15/30, got {total_score_val}/30."})

    # ── CHECK 5: Status label is "At Risk" ──────────────────────────────────
    # The three allowed labels from SKILL.md: Secure / Adequate / At Risk
    at_risk = bool(re.search(r'At Risk', content, re.IGNORECASE))
    checks.append({"name": "status_label_at_risk", "passed": at_risk,
                    "detail": "Expected 'At Risk' status label for a severely misconfigured config."})

    # ── CHECK 6: Correct status labels exist (Secure/Adequate/At Risk) ──────
    valid_labels = {"Secure", "Adequate", "At Risk"}
    found_labels = set(re.findall(r'\b(Secure|Adequate|At Risk)\b', content))
    has_valid_labels = len(found_labels) > 0
    checks.append({"name": "valid_status_labels_used", "passed": has_valid_labels,
                    "detail": f"Expected labels from {{Secure, Adequate, At Risk}}. Found: {found_labels}"})

    # ── CHECK 7: Markdown table with correct headers ─────────────────────────
    # Required columns: Dimension | Score | Risk | Top Action
    required_headers = ["Dimension", "Score", "Risk", "Top Action"]
    header_hits = [h for h in required_headers if h in content]
    table_ok = len(header_hits) == 4
    checks.append({"name": "table_headers_correct", "passed": table_ok,
                    "detail": f"Required headers {required_headers}. Found: {header_hits}"})

    # ── CHECK 8: All 3 dimensions appear in table ────────────────────────────
    dim1 = bool(re.search(r'Tool Description Integrity', content, re.IGNORECASE))
    dim2 = bool(re.search(r'Permission Scope', content, re.IGNORECASE))
    dim3 = bool(re.search(r'Supply Chain Trust', content, re.IGNORECASE))
    all_dims = dim1 and dim2 and dim3
    checks.append({"name": "all_three_dimensions_present", "passed": all_dims,
                    "detail": f"Dim1={dim1}, Dim2={dim2}, Dim3={dim3}"})

    # ── CHECK 9: Risk color labels (red/yellow/green) appear in table ────────
    risk_colors = re.findall(r'\b(red|yellow|green)\b', content, re.IGNORECASE)
    has_risk_colors = len(risk_colors) >= 3  # at least one per dimension
    checks.append({"name": "risk_color_labels_present", "passed": has_risk_colors,
                    "detail": f"Found risk color labels: {list(set(c.lower() for c in risk_colors))}"})

    # ── CHECK 10: Predominantly red labels (config is severely broken) ───────
    red_count = sum(1 for c in risk_colors if c.lower() == "red")
    mostly_red = red_count >= 2  # at least 2 of 3 dimensions should be red
    checks.append({"name": "majority_dimensions_red", "passed": mostly_red,
                    "detail": f"Expected >=2 red risk labels, found {red_count}."})

    # ── CHECK 11: Per-dimension scores present and each ≤ 10 ─────────────────
    per_dim_scores = re.findall(r'(\d+)\s*/\s*10', content)
    valid_per_dim = all(int(s) <= 10 for s in per_dim_scores) and len(per_dim_scores) >= 3
    checks.append({"name": "per_dimension_scores_valid", "passed": valid_per_dim,
                    "detail": f"Found /10 scores: {per_dim_scores}. Need >=3 each <=10."})

    # ── CHECK 12: Per-dimension scores are low given red-flag input ──────────
    low_per_dim = all(int(s) <= 4 for s in per_dim_scores[:3]) if len(per_dim_scores) >= 3 else False
    checks.append({"name": "per_dimension_scores_reflect_risk", "passed": low_per_dim,
                    "detail": f"First 3 /10 scores should all be <=4 for this config. Got: {per_dim_scores[:3]}"})

    # ── CHECK 13: "Top 3 Fixes" section present ──────────────────────────────
    has_top3 = bool(re.search(r'Top\s+3\s+Fix(es)?', content, re.IGNORECASE))
    checks.append({"name": "top_3_fixes_section", "passed": has_top3,
                    "detail": "Expected a 'Top 3 Fixes' section."})

    # ── CHECK 14: Exactly 3 numbered fix items ───────────────────────────────
    fix_items = re.findall(r'^\s*[1-3]\.\s+\S', content, re.MULTILINE)
    has_three_fixes = len(fix_items) >= 3
    checks.append({"name": "three_numbered_fixes", "passed": has_three_fixes,
                    "detail": f"Found {len(fix_items)} numbered fix items, expected >=3."})

    # ── CHECK 15: Tool Description Integrity red flags addressed ─────────────
    inj_keywords = ["inject", "imperative", "instruction", "override", "manipulat", "description"]
    dim1_addressed = any(kw in content.lower() for kw in inj_keywords)
    checks.append({"name": "tool_description_issue_addressed", "passed": dim1_addressed,
                    "detail": "Expected mention of injection/imperative language in Tool Description analysis."})

    # ── CHECK 16: Permission Scope red flags addressed ───────────────────────
    perm_keywords = ["root", "admin", "env", "secret", "least-privilege", "least privilege", "permission", "scope"]
    dim2_addressed = any(kw in content.lower() for kw in perm_keywords)
    checks.append({"name": "permission_scope_issue_addressed", "passed": dim2_addressed,
                    "detail": "Expected mention of root/admin/env access in Permission Scope analysis."})

    # ── CHECK 17: Supply Chain red flags addressed ───────────────────────────
    sc_keywords = ["latest", "unverified", "version pin", "cve", "community", "supply chain", "source review"]
    dim3_addressed = any(kw in content.lower() for kw in sc_keywords)
    checks.append({"name": "supply_chain_issue_addressed", "passed": dim3_addressed,
                    "detail": "Expected mention of 'latest'/unverified/CVE in Supply Chain analysis."})

    # ── SCORE ────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    num_checks = len(checks)
    final_score = round(len(passed_checks) / num_checks, 4)
    overall_passed = final_score >= 0.75

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))