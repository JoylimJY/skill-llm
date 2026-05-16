import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    ws = Path(workspace)

    # ── Locate the output file ──────────────────────────────────────────────
    candidates = list(ws.rglob("pleading_script.txt"))
    if not candidates:
        return checks, False, 0.0, "pleading_script.txt not found anywhere in workspace"

    script_path = candidates[0]
    try:
        content = script_path.read_text(encoding="utf-8")
    except Exception as e:
        return checks, False, 0.0, f"Could not read file: {e}"

    content_lower = content.lower()

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Proper arbitration tribunal opening formula
    # Must contain "may it please" (case-insensitive)
    # ─────────────────────────────────────────────────────────────────────────
    c1_passed = bool(re.search(r'may it please', content, re.IGNORECASE))
    checks.append({
        "name": "opening_formula_may_it_please",
        "passed": c1_passed,
        "detail": "Opening must contain 'May it please the tribunal/Court'" if not c1_passed
                  else "Found 'May it please' in script"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Rebuttal time reservation stated in opening
    # Must mention reserving 1 minute (or "1-2 minutes") for rebuttal
    # ─────────────────────────────────────────────────────────────────────────
    c2_passed = bool(re.search(
        r'reserv\w*\s+[12]\s*(?:to\s*2\s*)?minute|leaving\s+[12]\s*minute|1\s*min\w*\s+for\s+rebuttal|rebuttal.*1\s*min',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "rebuttal_time_reserved",
        "passed": c2_passed,
        "detail": "Must explicitly reserve 1 minute for rebuttal in opening" if not c2_passed
                  else "Rebuttal time reservation found"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: Pre-emptive rebuttal phrase (A-party specific strategy)
    # Must contain "Respondent may argue" (or similar) + "we submit"
    # ─────────────────────────────────────────────────────────────────────────
    has_preemptive = bool(re.search(
        r'respondent\s+may\s+argue|the\s+respondent\s+might\s+argue|the\s+respondent\s+will\s+argue',
        content, re.IGNORECASE
    ))
    has_we_submit = bool(re.search(r'we\s+submit', content, re.IGNORECASE))
    c3_passed = has_preemptive and has_we_submit
    checks.append({
        "name": "preemptive_rebuttal_phrase",
        "passed": c3_passed,
        "detail": (
            "A-party must include pre-emptive rebuttal: 'The Respondent may argue… however, we submit…'. "
            f"Found preemptive: {has_preemptive}, Found 'we submit': {has_we_submit}"
        ) if not c3_passed else "Pre-emptive rebuttal phrase present"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: No forbidden phrases
    # "I think", "I believe", "I am sorry", "I'm sorry",
    # "is wrong", "made a mistake", "are wrong"
    # ─────────────────────────────────────────────────────────────────────────
    forbidden_patterns = [
        (r'\bI think\b', "I think"),
        (r'\bI believe\b', "I believe"),
        (r'\bI am sorry\b', "I am sorry"),
        (r"\bI'm sorry\b", "I'm sorry"),
        (r'\bis wrong\b', "is wrong"),
        (r'\bmade a mistake\b', "made a mistake"),
        (r'\bare wrong\b', "are wrong"),
    ]
    forbidden_found = []
    for pattern, label in forbidden_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            forbidden_found.append(label)

    c4_passed = len(forbidden_found) == 0
    checks.append({
        "name": "no_forbidden_phrases",
        "passed": c4_passed,
        "detail": f"Forbidden phrases found: {forbidden_found}" if not c4_passed
                  else "No forbidden phrases detected"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: Roadmap present with at least 2 differentiated transition keywords
    # Accepted: firstly/secondly, first/second, first submission/second submission
    # The roadmap section should enumerate ≥2 issues
    # ─────────────────────────────────────────────────────────────────────────
    roadmap_keywords = [
        r'\bfirstly\b', r'\bsecondly\b', r'\bthirdly\b',
        r'\bfirst\b', r'\bsecond\b', r'\bthird\b',
        r'first\s+(?:submission|pleading|issue|point)',
        r'second\s+(?:submission|pleading|issue|point)',
        r'namely\b',
    ]
    roadmap_hits = sum(1 for kw in roadmap_keywords if re.search(kw, content, re.IGNORECASE))
    c5_passed = roadmap_hits >= 2
    checks.append({
        "name": "roadmap_with_differentiated_keywords",
        "passed": c5_passed,
        "detail": f"Roadmap must enumerate ≥2 issues with distinct transition keywords. Found {roadmap_hits} keyword matches."
                  if not c5_passed else f"Roadmap keywords found ({roadmap_hits} matches)"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: At least one case citation in required format
    # Format: "xxx versus xxx" or "xxx v. xxx" or "xxx v xxx"
    # ─────────────────────────────────────────────────────────────────────────
    c6_passed = bool(re.search(
        r'\b\w[\w\s]+\s+v(?:ersus|\.)?\s+\w[\w\s]+',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "case_citation_format",
        "passed": c6_passed,
        "detail": "Must include at least one case citation in 'X versus Y' or 'X v. Y' format" if not c6_passed
                  else "Case citation found in required format"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: Abbreviation introduced with "for short"
    # ─────────────────────────────────────────────────────────────────────────
    c7_passed = bool(re.search(r'for short', content, re.IGNORECASE))
    checks.append({
        "name": "abbreviation_introduced_with_for_short",
        "passed": c7_passed,
        "detail": "Must introduce at least one abbreviation using '[Full Name], [ABBR] for short'" if not c7_passed
                  else "'for short' abbreviation introduction found"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: Approved signpost words used
    # From SKILL.md: "Turning to", "Having addressed", "Building on",
    # "Returning to", "We would highlight", "Next, we will address",
    # "The most important", "To briefly summarize"
    # ─────────────────────────────────────────────────────────────────────────
    signpost_patterns = [
        r'Turning to',
        r'Having addressed',
        r'Building on',
        r'Returning to',
        r'We would highlight',
        r'Next,?\s+we\s+will\s+address',
        r'The most (?:important|determinative|critical) point',
        r'To briefly summarize',
    ]
    signpost_hits = [p for p in signpost_patterns if re.search(p, content, re.IGNORECASE)]
    c8_passed = len(signpost_hits) >= 1
    checks.append({
        "name": "approved_signpost_words_used",
        "passed": c8_passed,
        "detail": "Must use at least one approved signpost word from the skill documentation" if not c8_passed
                  else f"Signpost words found: {signpost_hits}"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: Approved inter-issue transition phrase used
    # From SKILL.md: "Unless I may further assist", "I will now move on to",
    # "May I move to my second issue"
    # ─────────────────────────────────────────────────────────────────────────
    transition_patterns = [
        r'Unless I may further assist',
        r'I will now move on to',
        r'May I move to',
        r'move on to address',
        r'leads to my (?:second|next) point',
    ]
    transition_hits = [p for p in transition_patterns if re.search(p, content, re.IGNORECASE)]
    c9_passed = len(transition_hits) >= 1
    checks.append({
        "name": "approved_transition_phrase_between_issues",
        "passed": c9_passed,
        "detail": "Must use at least one approved transition phrase between issues (e.g., 'Unless I may further assist…', 'I will now move on to…')" if not c9_passed
                  else f"Transition phrase found: {transition_hits}"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 10: Self-introduction includes team co-counsel & client
    # Must mention co-counsel and the client (Claimant / ABT / Aurelion)
    # ─────────────────────────────────────────────────────────────────────────
    has_cocounsel = bool(re.search(r'co.?counsel', content, re.IGNORECASE))
    has_client = bool(re.search(r'claimant|aurelion|ABT', content, re.IGNORECASE))
    c10_passed = has_cocounsel and has_client
    checks.append({
        "name": "self_introduction_includes_cocounsel_and_client",
        "passed": c10_passed,
        "detail": f"Opening must introduce co-counsel and identify client. co-counsel: {has_cocounsel}, client: {has_client}"
                  if not c10_passed else "Co-counsel and client identified in opening"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 8  # must pass at least 8 out of 10

    return checks, overall_passed, score, ""


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "No workspace path provided"}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks, overall_passed, score, err = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [],
            "error": f"Evaluation crashed: {e}"
        }))
        sys.exit(1)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    if err:
        result["error"] = err
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()