import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("codebase_report.md"))
    if candidates:
        return candidates[0]
    return None

def evaluate(workspace: str):
    checks = []

    # ── 1. File exists ───────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append({"name": "report_file_exists",
                        "passed": False,
                        "detail": "codebase_report.md not found anywhere in workspace"})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "report_file_exists",
                    "passed": True,
                    "detail": f"Found at {report_path}"})

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable",
                        "passed": False,
                        "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_readable",
                    "passed": True,
                    "detail": "File read successfully"})

    lower = content.lower()
    lines = content.splitlines()

    # ── 2. Situation summary ≤ 5 lines ───────────────────────────────────────
    # Find the situation summary section and count its lines
    sit_passed = False
    sit_detail = "Situation summary section not found"
    sit_pattern = re.compile(
        r"(?:situation\s*summary|situation\s*overview|executive\s*summary)",
        re.IGNORECASE
    )
    heading_indices = [i for i, l in enumerate(lines) if sit_pattern.search(l)]

    if heading_indices:
        start = heading_indices[0] + 1
        # Collect non-empty lines until next heading or end
        summary_lines = []
        for l in lines[start:]:
            stripped = l.strip()
            if re.match(r"^#+\s", stripped) or re.match(r"^---", stripped):
                break
            if stripped:
                summary_lines.append(stripped)
        count = len(summary_lines)
        if count <= 5:
            sit_passed = True
            sit_detail = f"Situation summary has {count} lines (≤5 required)"
        else:
            sit_detail = f"Situation summary has {count} lines (exceeds 5-line max: proprietary constraint)"
    checks.append({"name": "situation_summary_5_lines_max",
                    "passed": sit_passed,
                    "detail": sit_detail})

    # ── 3. Top findings ranked by impact ────────────────────────────────────
    findings_passed = False
    findings_detail = "Top findings section not found"
    findings_pattern = re.compile(r"top\s*findings?|key\s*findings?", re.IGNORECASE)
    found_section = any(findings_pattern.search(l) for l in lines)

    if found_section:
        # Check for ranking indicators: numbers, priority words, or explicit rank labels
        rank_indicators = re.compile(
            r"(\b(critical|high|medium|low|p[0-1])\b|"
            r"^\s*[\*\-]\s*\*?\*?(critical|high|medium|low|impact)|"
            r"ranked|by impact|severity|priority|"
            r"^\s*[1-9]\d*[\.\)])",
            re.IGNORECASE | re.MULTILINE
        )
        ranking_matches = rank_indicators.findall(content)
        # Also check that findings are numbered/ordered
        numbered = re.findall(r"^\s*[1-9][\.\)]\s+\S", content, re.MULTILINE)
        if len(ranking_matches) >= 2 or len(numbered) >= 2:
            findings_passed = True
            findings_detail = f"Findings appear ranked ({len(numbered)} numbered items, {len(ranking_matches)} impact indicators)"
        else:
            findings_detail = "Findings section found but no clear ranking by impact detected"
    checks.append({"name": "findings_ranked_by_impact",
                    "passed": findings_passed,
                    "detail": findings_detail})

    # ── 4. Action plan split today / this week ───────────────────────────────
    today_found = bool(re.search(r"\btoday\b", lower))
    week_found = bool(re.search(r"this\s+week|week\b", lower))
    action_section = bool(re.search(r"action\s*plan", lower))
    split_passed = action_section and today_found and week_found
    checks.append({
        "name": "action_plan_today_this_week_split",
        "passed": split_passed,
        "detail": (
            f"action_plan={action_section}, today={today_found}, this_week={week_found}"
        )
    })

    # ── 5. Risks + mitigations section ───────────────────────────────────────
    risks_passed = bool(re.search(r"risk", lower)) and (
        bool(re.search(r"mitigat", lower)) or bool(re.search(r"fallback|contingency|workaround", lower))
    )
    checks.append({
        "name": "risks_and_mitigations_present",
        "passed": risks_passed,
        "detail": "risks+mitigations section found" if risks_passed else "risks and/or mitigations section missing"
    })

    # ── 6. Fallback plan ────────────────────────────────────────────────────
    fallback_passed = bool(re.search(r"fallback|contingency|if.*fails|plan\s*b|alternative", lower))
    checks.append({
        "name": "fallback_plan_present",
        "passed": fallback_passed,
        "detail": "Fallback/contingency plan found" if fallback_passed else "No fallback plan detected (required by quality gate)"
    })

    # ── 7. Owner + ETA for each next step ────────────────────────────────────
    owner_pattern = re.compile(r"(@\w+|owner\s*:\s*\w+|owned by|responsible\s*:\s*\w+)", re.IGNORECASE)
    eta_pattern = re.compile(r"(ETA|by\s+\w+\s*\d{4}|deadline|due\s+\w+|Q[1-4]\s*\d{4}|day\s*\d+|\d+\s*days?)", re.IGNORECASE)
    owner_hits = owner_pattern.findall(content)
    eta_hits = eta_pattern.findall(content)
    owner_eta_passed = len(owner_hits) >= 2 and len(eta_hits) >= 2
    checks.append({
        "name": "owner_and_eta_per_step",
        "passed": owner_eta_passed,
        "detail": f"owner mentions={len(owner_hits)}, ETA mentions={len(eta_hits)} (need ≥2 each)"
    })

    # ── 8. Evidence-backed claims: must reference actual module/file names ────
    codebase_refs = [
        "engine.py", "validator.py", "ledger_sync.py", "runner.py",
        "pci_check.py", "stripe", "settings.py", "config/settings",
        "_INTERNAL_FEE_RATE", "LEDGER_ENDPOINT", "ledger_sync",
        "batch", "settlement", "feature_flags", "card_number"
    ]
    found_refs = [r for r in codebase_refs if r.lower() in lower]
    evidence_passed = len(found_refs) >= 5
    checks.append({
        "name": "evidence_backed_claims_with_file_refs",
        "passed": evidence_passed,
        "detail": f"Referenced {len(found_refs)} codebase artifacts: {found_refs[:8]}"
    })

    # ── 9. Checklist or exact commands present ────────────────────────────────
    checklist_passed = bool(re.search(r"```|`[^`]+`|\[ \]|\[x\]|^- \[", content, re.MULTILINE)) or \
                       bool(re.search(r"^\s*-\s+\w.{10,}", content, re.MULTILINE))
    checks.append({
        "name": "checklist_or_commands_present",
        "passed": checklist_passed,
        "detail": "Checklist items or code commands found" if checklist_passed else "No checklist or commands found (required by output format)"
    })

    # ── 10. Explicit assumptions / tradeoffs ─────────────────────────────────
    assumptions_passed = bool(re.search(r"assumption|assum|trade.?off|tradeoff|caveat|constraint", lower))
    checks.append({
        "name": "explicit_assumptions_or_tradeoffs",
        "passed": assumptions_passed,
        "detail": "Assumptions/tradeoffs section found" if assumptions_passed else "No explicit assumptions or tradeoffs stated (quality gate requirement)"
    })

    # ── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 0.05,
        "report_readable": 0.03,
        "situation_summary_5_lines_max": 0.12,
        "findings_ranked_by_impact": 0.12,
        "action_plan_today_this_week_split": 0.12,
        "risks_and_mitigations_present": 0.10,
        "fallback_plan_present": 0.10,
        "owner_and_eta_per_step": 0.10,
        "evidence_backed_claims_with_file_refs": 0.14,
        "checklist_or_commands_present": 0.07,
        "explicit_assumptions_or_tradeoffs": 0.05,
    }
    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])
    passed = all(c["passed"] for c in checks)

    return {"passed": passed, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))