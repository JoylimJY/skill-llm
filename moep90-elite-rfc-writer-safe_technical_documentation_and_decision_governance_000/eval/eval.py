import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # --- Find the RFC file ---
    rfc_file = None
    candidates = list(workspace.rglob("rfc-cicd-migration.md"))
    if not candidates:
        # Try broader search for any RFC md file not in archive
        candidates = [
            f for f in workspace.rglob("*.md")
            if "rfc" in f.name.lower() and "migration" in f.name.lower() and "archive" not in str(f)
        ]
    if not candidates:
        # Last resort: any new .md file not in archive or references or distractor
        known_distractor_names = {
            "current-state.md", "tekton-poc-notes.md", "jenkins-backup.md",
            "rfc-observability-stack-2023.md", "platform-sync-notes.md",
            "decision-needed.md", "rfc-intake-checklist.md", "decision-guardrails.md"
        }
        candidates = [
            f for f in workspace.rglob("*.md")
            if f.name not in known_distractor_names
        ]
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "rfc_file_exists", "passed": False, "detail": "No RFC markdown file found in workspace."}]
        }
    
    # Pick the most likely candidate (prefer files with 'rfc' or 'cicd' or 'migration' in name)
    def score_candidate(f):
        s = 0
        name = f.name.lower()
        if "rfc" in name: s += 3
        if "cicd" in name or "ci-cd" in name or "ci_cd" in name: s += 2
        if "migration" in name or "migrat" in name: s += 2
        if "tekton" in name or "jenkins" in name: s += 1
        return s
    
    candidates.sort(key=score_candidate, reverse=True)
    rfc_file = candidates[0]
    
    try:
        content = rfc_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "rfc_file_readable", "passed": False, "detail": str(e)}]
        }
    
    checks.append({"name": "rfc_file_exists", "passed": True, "detail": f"Found RFC at {rfc_file}"})
    
    # --------------------------------------------------------
    # CHECK 1: Exact mandatory headings present in correct order
    # --------------------------------------------------------
    mandatory_headings = [
        "Zusammenfassung",
        "Motivation",
        "Ziele",
        "Nicht-Ziele",
        "Vorschlag",
        "Anhang",
    ]
    
    heading_positions = {}
    for h in mandatory_headings:
        # Match markdown heading at level 1 or 2
        pattern = re.compile(rf"^#+\s+{re.escape(h)}\s*$", re.MULTILINE | re.IGNORECASE)
        m = pattern.search(content)
        if m:
            heading_positions[h] = m.start()
        else:
            heading_positions[h] = -1
    
    all_headings_present = all(v >= 0 for v in heading_positions.values())
    checks.append({
        "name": "all_six_german_headings_present",
        "passed": all_headings_present,
        "detail": f"Missing: {[h for h, v in heading_positions.items() if v < 0]}" if not all_headings_present else "All six headings found."
    })
    
    # Check order
    ordered = True
    if all_headings_present:
        positions = [heading_positions[h] for h in mandatory_headings]
        ordered = positions == sorted(positions)
    checks.append({
        "name": "headings_in_correct_order",
        "passed": ordered,
        "detail": "Headings are in the mandatory order." if ordered else f"Heading order is wrong: {[h for h in mandatory_headings]} positions {[heading_positions[h] for h in mandatory_headings]}"
    })
    
    # Helper: extract section text
    def extract_section(content, section_name, all_headings, heading_positions):
        start = heading_positions.get(section_name, -1)
        if start < 0:
            return ""
        # Find next heading after this one
        next_starts = [v for v in heading_positions.values() if v > start]
        end = min(next_starts) if next_starts else len(content)
        return content[start:end]
    
    zusammenfassung = extract_section(content, "Zusammenfassung", mandatory_headings, heading_positions)
    motivation = extract_section(content, "Motivation", mandatory_headings, heading_positions)
    ziele = extract_section(content, "Ziele", mandatory_headings, heading_positions)
    nicht_ziele = extract_section(content, "Nicht-Ziele", mandatory_headings, heading_positions)
    vorschlag = extract_section(content, "Vorschlag", mandatory_headings, heading_positions)
    anhang = extract_section(content, "Anhang", mandatory_headings, heading_positions)
    
    # --------------------------------------------------------
    # CHECK 2: Zusammenfassung contains valid decision status
    # --------------------------------------------------------
    valid_statuses = ["speculative", "draft", "accepted", "rejected", "implemented", "obsolete"]
    status_found = any(s.lower() in zusammenfassung.lower() for s in valid_statuses)
    checks.append({
        "name": "zusammenfassung_decision_status",
        "passed": status_found,
        "detail": "Decision status found in Zusammenfassung." if status_found else f"No valid status ({valid_statuses}) found in Zusammenfassung."
    })
    
    # --------------------------------------------------------
    # CHECK 3: Zusammenfassung contains decision owner
    # --------------------------------------------------------
    # Look for a named person or role + "owner" concept
    owner_patterns = [
        r"(entscheidung|decision).{0,30}(owner|inhaber|verantwortlich)",
        r"(owner|inhaber|verantwortlich).{0,50}(alice|müller|platform lead|platform-lead)",
        r"alice\s+m[üu]ller",
        r"platform\s+lead",
    ]
    owner_found = any(re.search(p, zusammenfassung, re.IGNORECASE) for p in owner_patterns)
    checks.append({
        "name": "zusammenfassung_decision_owner",
        "passed": owner_found,
        "detail": "Decision owner found in Zusammenfassung." if owner_found else "No decision owner found in Zusammenfassung."
    })
    
    # --------------------------------------------------------
    # CHECK 4: Zusammenfassung contains a date
    # --------------------------------------------------------
    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4}|januar|februar|2025|2024", re.IGNORECASE)
    date_found = bool(date_pattern.search(zusammenfassung))
    checks.append({
        "name": "zusammenfassung_date",
        "passed": date_found,
        "detail": "Date found in Zusammenfassung." if date_found else "No date found in Zusammenfassung."
    })
    
    # --------------------------------------------------------
    # CHECK 5: Motivation contains measurable evidence (numbers/metrics)
    # --------------------------------------------------------
    # Look for metrics from the brief: 6 hours, €4200, 78%, 80 pipelines, 10 engineer-hours
    metric_patterns = [
        r"\d+\s*(stunden|hours|h\b)",
        r"€\s*\d+",
        r"\d+\s*%",
        r"\d+\s*(pipelines?|vorfälle?|incidents?)",
        r"\d+\s*(engineer.?stunden|engineer.?hours)",
    ]
    evidence_found = any(re.search(p, motivation, re.IGNORECASE) for p in metric_patterns)
    checks.append({
        "name": "motivation_measurable_evidence",
        "passed": evidence_found,
        "detail": "Measurable evidence (metrics/numbers) found in Motivation." if evidence_found else "No measurable evidence found in Motivation."
    })
    
    # --------------------------------------------------------
    # CHECK 6: Motivation contains explicit assumption statements
    # --------------------------------------------------------
    assumption_patterns = [
        r"annahme\s*:",
        r"assumption\s*:",
        r"wir\s+nehmen\s+an",
        r"es\s+wird\s+angenommen",
        r"vorausgesetzt",
    ]
    assumption_found = any(re.search(p, motivation, re.IGNORECASE) for p in assumption_patterns)
    checks.append({
        "name": "motivation_explicit_assumptions",
        "passed": assumption_found,
        "detail": "Explicit assumption label found in Motivation." if assumption_found else "No explicit assumption statement (e.g., 'Annahme:') found in Motivation."
    })
    
    # --------------------------------------------------------
    # CHECK 7: Ziele uses bullet points with success criteria
    # --------------------------------------------------------
    bullet_pattern = re.compile(r"^\s*[\*\-\+]\s+.+", re.MULTILINE)
    ziele_bullets = bullet_pattern.findall(ziele)
    has_ziele_bullets = len(ziele_bullets) >= 2
    # Check for success criteria language
    criteria_patterns = [
        r"kriterium|erfolg|metric|messbar|kpi|ziel\s+erreicht|≤|>=|<=|>|<|\d+\s*%",
    ]
    has_success_criteria = any(re.search(p, ziele, re.IGNORECASE) for p in criteria_patterns)
    ziele_ok = has_ziele_bullets and has_success_criteria
    checks.append({
        "name": "ziele_bullets_with_success_criteria",
        "passed": ziele_ok,
        "detail": f"Ziele bullets: {len(ziele_bullets)}, success criteria present: {has_success_criteria}."
    })
    
    # --------------------------------------------------------
    # CHECK 8: Nicht-Ziele uses bullet points with explicit out-of-scope marking
    # --------------------------------------------------------
    nicht_ziele_bullets = bullet_pattern.findall(nicht_ziele)
    has_nicht_ziele_bullets = len(nicht_ziele_bullets) >= 1
    outofscope_patterns = [
        r"nicht\s+(im|in\s+scope|bestandteil)",
        r"out.of.scope",
        r"außerhalb",
        r"kein\s+(bestandteil|ziel|teil)",
        r"no.go",
        r"scope\s+creep",
        r"wird\s+nicht",
        r"nicht\s+migriert",
        r"nicht\s+in\s+diesem",
    ]
    has_outofscope = any(re.search(p, nicht_ziele, re.IGNORECASE) for p in outofscope_patterns)
    nicht_ziele_ok = has_nicht_ziele_bullets and has_outofscope
    checks.append({
        "name": "nicht_ziele_explicit_outofscope",
        "passed": nicht_ziele_ok,
        "detail": f"Nicht-Ziele bullets: {len(nicht_ziele_bullets)}, out-of-scope language: {has_outofscope}."
    })
    
    # --------------------------------------------------------
    # CHECK 9: Vorschlag includes migration path and rollback strategy
    # --------------------------------------------------------
    migration_patterns = [
        r"migration(spfad|splan|sstrategie|sweg|spath)?",
        r"migrationsplan",
        r"phasen?\s*\d",
        r"migrat",
    ]
    rollback_patterns = [
        r"rollback",
        r"rückfall",
        r"rückkehr",
        r"r[öo]llen?\s+zur[üu]ck",
        r"fallback",
    ]
    has_migration = any(re.search(p, vorschlag, re.IGNORECASE) for p in migration_patterns)
    has_rollback = any(re.search(p, vorschlag, re.IGNORECASE) for p in rollback_patterns)
    checks.append({
        "name": "vorschlag_migration_path",
        "passed": has_migration,
        "detail": "Migration path/plan referenced in Vorschlag." if has_migration else "No migration path found in Vorschlag."
    })
    checks.append({
        "name": "vorschlag_rollback_strategy",
        "passed": has_rollback,
        "detail": "Rollback strategy referenced in Vorschlag." if has_rollback else "No rollback strategy found in Vorschlag."
    })
    
    # --------------------------------------------------------
    # CHECK 10: Vorschlag lists key constraints
    # --------------------------------------------------------
    constraint_patterns = [
        r"(technisch|organizatorisch|regulatorisch|finanziell|constraint|einschränkung|budget|soc\s*2|compliance)",
    ]
    has_constraints = any(re.search(p, vorschlag, re.IGNORECASE) for p in constraint_patterns)
    checks.append({
        "name": "vorschlag_key_constraints",
        "passed": has_constraints,
        "detail": "Key constraints listed in Vorschlag." if has_constraints else "No constraints found in Vorschlag."
    })
    
    # --------------------------------------------------------
    # CHECK 11: Anhang contains alternatives with rejection reasons
    # --------------------------------------------------------
    alt_patterns = [
        r"alternativ",
        r"github\s+actions",
        r"jenkins.*standby|standby.*jenkins",
        r"abgelehnt|verworfen|rejected|nicht\s+gewählt",
    ]
    has_alternatives = sum(1 for p in alt_patterns if re.search(p, anhang, re.IGNORECASE)) >= 2
    checks.append({
        "name": "anhang_alternatives_with_rejection",
        "passed": has_alternatives,
        "detail": "Alternatives with rejection reasons found in Anhang." if has_alternatives else "Anhang lacks alternatives or rejection reasons."
    })
    
    # --------------------------------------------------------
    # CHECK 12: Anhang contains risks/drawbacks with mitigations
    # --------------------------------------------------------
    risk_patterns = [
        r"risiko|risiken|risk|nachteil|drawback",
        r"minderung|mitigation|gegenmaßnahme|abhilfe",
    ]
    has_risks = all(any(re.search(p, anhang, re.IGNORECASE) for p in [grp]) for grp in risk_patterns)
    checks.append({
        "name": "anhang_risks_with_mitigations",
        "passed": has_risks,
        "detail": "Risks and mitigations found in Anhang." if has_risks else "Anhang missing risks or mitigations."
    })
    
    # --------------------------------------------------------
    # CHECK 13: Anhang contains open questions with owner and due date
    # --------------------------------------------------------
    # Must have open questions + owner name + a date
    open_q_patterns = [
        r"offene?\s+fragen?|open\s+questions?",
    ]
    has_open_q = any(re.search(p, anhang, re.IGNORECASE) for p in open_q_patterns)
    
    # Check for named owner in open questions context
    owner_in_oq = any(re.search(p, anhang, re.IGNORECASE) for p in [
        r"carol\s+brandt|alice\s+m[üu]ller|dave\s+chen",
        r"owner\s*:",
        r"verantwortlich\s*:",
        r"zuständig\s*:",
    ])
    
    # Check for due dates in Anhang
    date_in_oq = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}\.\d{1,2}\.\d{4}|2025", anhang))
    
    open_q_ok = has_open_q and owner_in_oq and date_in_oq
    checks.append({
        "name": "anhang_open_questions_with_owner_and_date",
        "passed": open_q_ok,
        "detail": f"Open questions: {has_open_q}, owner named: {owner_in_oq}, due date: {date_in_oq}."
    })
    
    # --------------------------------------------------------
    # CHECK 14: Anhang contains references to evidence
    # --------------------------------------------------------
    ref_patterns = [
        r"referenz|referenzen|reference|quell|quelle|ticket|pr\b|pull\s+request|doc\b|dokument|poc|proof.of.concept|bericht",
    ]
    has_refs = any(re.search(p, anhang, re.IGNORECASE) for p in ref_patterns)
    checks.append({
        "name": "anhang_references_to_evidence",
        "passed": has_refs,
        "detail": "References to evidence/tickets/docs found in Anhang." if has_refs else "No references found in Anhang."
    })
    
    # --------------------------------------------------------
    # CHECK 15: No marketing language
    # --------------------------------------------------------
    marketing_terms = [
        r"\bseamlessly\b",
        r"\brevolutionary\b",
        r"\bbest.in.class\b",
        r"\bcutting.edge\b",
        r"\bgame.changer\b",
        r"\bworld.class\b",
        r"\bindustry.leading\b",
        r"\bstate.of.the.art\b",
        r"\bunprecedented\b",
    ]
    marketing_found = [t for t in marketing_terms if re.search(t, content, re.IGNORECASE)]
    no_marketing = len(marketing_found) == 0
    checks.append({
        "name": "no_marketing_language",
        "passed": no_marketing,
        "detail": "No marketing language detected." if no_marketing else f"Marketing language found: {marketing_found}"
    })
    
    # --------------------------------------------------------
    # CHECK 16: Document primarily in German (basic check)
    # --------------------------------------------------------
    german_indicators = [
        r"\bdie\b", r"\bder\b", r"\bdas\b", r"\bund\b", r"\bist\b",
        r"\bein\b", r"\beine\b", r"\bwird\b", r"\bfür\b", r"\bvon\b",
        r"\bmit\b", r"\bdem\b", r"\bden\b", r"\bsich\b", r"\bnicht\b",
    ]
    german_hits = sum(len(re.findall(p, content, re.IGNORECASE)) for p in german_indicators)
    is_german = german_hits >= 30
    checks.append({
        "name": "document_primarily_in_german",
        "passed": is_german,
        "detail": f"German word count indicator: {german_hits} (need ≥30)."
    })
    
    # --------------------------------------------------------
    # Final scoring
    # --------------------------------------------------------
    critical_checks = [
        "all_six_german_headings_present",
        "headings_in_correct_order",
        "zusammenfassung_decision_status",
        "vorschlag_migration_path",
        "vorschlag_rollback_strategy",
        "anhang_open_questions_with_owner_and_date",
    ]
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass all critical checks to pass overall
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))