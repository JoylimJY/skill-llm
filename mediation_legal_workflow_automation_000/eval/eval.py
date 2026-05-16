#!/usr/bin/env python3
import sys
import json
import os
import re
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception during check: {e}"}

def find_brief(workspace):
    """Find mediation_brief.md anywhere in workspace."""
    hits = list(Path(workspace).rglob("mediation_brief.md"))
    if not hits:
        return None
    return hits[0]

def get_expected_outputs(workspace):
    """Run the actual scripts to get ground-truth content."""
    script = os.path.join(workspace, "scripts", "script.sh")
    results = {}
    for cmd in ["process", "techniques", "settlement", "checklist"]:
        try:
            out = subprocess.check_output(
                ["bash", script, cmd],
                stderr=subprocess.STDOUT,
                env={**os.environ, "MEDIATION_DIR": os.path.join(workspace, ".mediation/")},
                cwd=workspace,
                timeout=10,
            )
            results[cmd] = out.decode("utf-8", errors="replace").lower()
        except Exception as e:
            results[cmd] = ""
    return results

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    # --- Find the file ---
    brief_path = find_brief(workspace)
    
    def check_file_exists():
        if brief_path is None:
            return False, "mediation_brief.md not found anywhere in workspace."
        return True, f"Found at: {brief_path}"
    
    checks.append(run_check("file_exists", check_file_exists))
    
    if brief_path is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result))
        return

    # Read the brief
    try:
        content = brief_path.read_text(encoding="utf-8", errors="replace")
        content_lower = content.lower()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Get ground truth from scripts
    gt = get_expected_outputs(workspace)

    # ---- CHECK 1: All 5 process stages present ----
    def check_all_five_stages():
        # From scripts/script.sh process output
        required_stages = [
            "opening statement",
            "joint session",
            "caucus",
            "negotiation",
            "closure"
        ]
        missing = [s for s in required_stages if s not in content_lower]
        if missing:
            return False, f"Missing process stages: {missing}"
        return True, "All 5 process stages (Opening Statement, Joint Session, Caucus, Negotiation, Closure) present."

    checks.append(run_check("all_five_process_stages", check_all_five_stages))

    # ---- CHECK 2: All 4 mediator techniques present ----
    def check_four_techniques():
        # From scripts/script.sh techniques output
        required_techniques = [
            "reframing",
            "reality testing",
            "batna",
            "watna",
            "anchoring"
        ]
        missing = [t for t in required_techniques if t not in content_lower]
        if missing:
            return False, f"Missing mediator techniques/concepts: {missing}"
        return True, "All 4 mediator techniques (Reframing, Reality Testing, BATNA/WATNA, Anchoring) present."

    checks.append(run_check("all_four_mediator_techniques", check_four_techniques))

    # ---- CHECK 3: Settlement agreement essential terms (from script output) ----
    def check_settlement_terms():
        # From scripts/script.sh settlement — all 10 essential terms
        required_terms = [
            "parties",
            "recitals",
            "payment terms",
            "releases",
            "confidentiality",
            "dismissal",
            "breach remedies",
            "governing law",
            "signatures",
        ]
        missing = [t for t in required_terms if t not in content_lower]
        if len(missing) > 2:
            return False, f"Missing {len(missing)} settlement essential terms: {missing}"
        if missing:
            return True, f"Most settlement terms present; minor gaps: {missing}"
        return True, "All essential settlement agreement terms present."

    checks.append(run_check("settlement_essential_terms", check_settlement_terms))

    # ---- CHECK 4: Checklist items present (pre/day-of/post sections) ----
    def check_checklist_sections():
        # From scripts/script.sh checklist output — three temporal sections
        required = [
            "pre-mediation",
            "day-of",
            "post-mediation",
        ]
        missing = [r for r in required if r not in content_lower]
        if missing:
            return False, f"Missing checklist sections: {missing}. Brief must include Pre-Mediation, Day-Of, and Post-Mediation checklist sections."
        return True, "All three checklist sections (Pre-Mediation, Day-Of, Post-Mediation) present."

    checks.append(run_check("checklist_three_sections", check_checklist_sections))

    # ---- CHECK 5: Checklist authority item ----
    def check_checklist_authority():
        # Specific bespoke item from checklist: "full settlement authority"
        if "settlement authority" not in content_lower and "full authority" not in content_lower:
            return False, "Missing 'settlement authority' item from checklist — required per tool output."
        return True, "Settlement authority checklist item present."

    checks.append(run_check("checklist_authority_item", check_checklist_authority))

    # ---- CHECK 6: Caucus confidentiality nuance ----
    def check_caucus_confidentiality():
        # From process stage 3: "Information shared in caucus is kept confidential"
        # Must appear in the caucus section context
        if "caucus" in content_lower and ("confidential" in content_lower):
            return True, "Caucus confidentiality correctly referenced."
        return False, "Caucus confidentiality not addressed. The tool output specifies caucus information is confidential unless permission granted."

    checks.append(run_check("caucus_confidentiality", check_caucus_confidentiality))

    # ---- CHECK 7: BATNA/WATNA both present and correctly framed ----
    def check_batna_watna_framing():
        # Both terms must appear and be associated with "alternative" meaning
        has_batna = "batna" in content_lower
        has_watna = "watna" in content_lower
        has_best = "best alternative" in content_lower
        has_worst = "worst alternative" in content_lower
        if not has_batna:
            return False, "BATNA not mentioned in brief."
        if not has_watna:
            return False, "WATNA not mentioned. Tool output defines both; brief must include both."
        if not (has_best or has_worst):
            return False, "BATNA/WATNA not explained (missing 'best alternative' or 'worst alternative' framing from tool output)."
        return True, "BATNA and WATNA both present with correct framing."

    checks.append(run_check("batna_watna_both_defined", check_batna_watna_framing))

    # ---- CHECK 8: Enforceability/tax notes from settlement command ----
    def check_settlement_enforceability():
        # From scripts/script.sh settlement — enforceability notes
        has_enforce = any(kw in content_lower for kw in [
            "enforceab", "consent judgment", "court order", "contract formation"
        ])
        has_tax = any(kw in content_lower for kw in [
            "tax", "irc", "income", "compensatory"
        ])
        if not has_enforce:
            return False, "Missing enforceability notes from settlement section (e.g., consent judgment, contract formation)."
        if not has_tax:
            return False, "Missing tax implications from settlement section (required by tool output)."
        return True, "Enforceability and tax implication notes present from settlement command output."

    checks.append(run_check("settlement_enforceability_and_tax", check_settlement_enforceability))

    # ---- CHECK 9: Document is structured (has headings / sections) ----
    def check_document_structure():
        # Must have markdown headings for at minimum: Process, Techniques, Settlement, Checklist
        heading_pattern = re.compile(r'^#{1,3}\s+.+', re.MULTILINE)
        headings = heading_pattern.findall(content)
        if len(headings) < 4:
            return False, f"Document has only {len(headings)} markdown section headings. Expected at least 4 structured sections covering process, techniques, settlement, and checklist."
        return True, f"Document has {len(headings)} markdown headings — well structured."

    checks.append(run_check("document_has_structure", check_document_structure))

    # ---- CHECK 10: Post-mediation impasse guidance ----
    def check_impasse_guidance():
        # From checklist: "If impasse: evaluate next ADR step (arbitration, ENE, or litigation)"
        if "impasse" in content_lower:
            return True, "Impasse handling (post-mediation) mentioned as required by checklist."
        return False, "Missing impasse guidance in post-mediation section — required by tool's checklist output."

    checks.append(run_check("post_mediation_impasse_guidance", check_impasse_guidance))

    # ---- Scoring ----
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4)
    
    # Must pass file_exists + at least 7 of the remaining 9 content checks to pass overall
    content_checks_passed = sum(1 for c in checks[1:] if c["passed"])
    overall_passed = checks[0]["passed"] and content_checks_passed >= 7

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()