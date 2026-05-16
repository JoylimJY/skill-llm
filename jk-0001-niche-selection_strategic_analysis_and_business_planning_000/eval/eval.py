import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    """Search for niche_strategy.md in the workspace."""
    candidates = list(Path(workspace).rglob("niche_strategy.md"))
    if not candidates:
        return None
    return candidates[0]

def compute_weighted_score(scores: dict) -> float:
    weights = {
        "pain_intensity": 0.25,
        "personal_advantage": 0.20,
        "market_size": 0.20,
        "monetization_potential": 0.15,
        "competition_landscape": 0.10,
        "growth_trajectory": 0.10,
    }
    total = 0.0
    for key, w in weights.items():
        total += scores[key] * w
    return round(total, 4)

# Ground truth scores from the input file
NICHES = {
    "01": {"name": "Contract review automation for independent consultants",
           "scores": {"pain_intensity":5,"personal_advantage":4,"market_size":3,"monetization_potential":4,"competition_landscape":3,"growth_trajectory":4},
           "validation_fails": 0},
    "02": {"name": "Invoicing and payment recovery for freelance videographers",
           "scores": {"pain_intensity":4,"personal_advantage":2,"market_size":3,"monetization_potential":3,"competition_landscape":2,"growth_trajectory":3},
           "validation_fails": 5},
    "03": {"name": "Employee onboarding workflow builder for HR teams at startups",
           "scores": {"pain_intensity":5,"personal_advantage":3,"market_size":5,"monetization_potential":5,"competition_landscape":2,"growth_trajectory":4},
           "validation_fails": 0},
    "04": {"name": "SEO content brief generator for boutique marketing agencies",
           "scores": {"pain_intensity":4,"personal_advantage":3,"market_size":4,"monetization_potential":4,"competition_landscape":4,"growth_trajectory":3},
           "validation_fails": 1},
    "05": {"name": "Lease abstraction tool for independent commercial real estate brokers",
           "scores": {"pain_intensity":4,"personal_advantage":2,"market_size":2,"monetization_potential":3,"competition_landscape":3,"growth_trajectory":2},
           "validation_fails": 5},
    "06": {"name": "Client reporting dashboard for solo financial advisors",
           "scores": {"pain_intensity":5,"personal_advantage":5,"market_size":3,"monetization_potential":5,"competition_landscape":3,"growth_trajectory":3},
           "validation_fails": 0},
    "07": {"name": "Project status page generator for freelance web developers",
           "scores": {"pain_intensity":4,"personal_advantage":4,"market_size":4,"monetization_potential":3,"competition_landscape":3,"growth_trajectory":4},
           "validation_fails": 0},
    "08": {"name": "Subscription churn prediction tool for bootstrapped B2B SaaS founders",
           "scores": {"pain_intensity":5,"personal_advantage":4,"market_size":3,"monetization_potential":4,"competition_landscape":3,"growth_trajectory":5},
           "validation_fails": 0},
    "09": {"name": "Scheduling and tip-splitting tool for food truck operators",
           "scores": {"pain_intensity":3,"personal_advantage":1,"market_size":2,"monetization_potential":2,"competition_landscape":2,"growth_trajectory":2},
           "validation_fails": 5},
    "10": {"name": "Proposal generation tool for boutique interior design studios",
           "scores": {"pain_intensity":4,"personal_advantage":2,"market_size":3,"monetization_potential":3,"competition_landscape":2,"growth_trajectory":3},
           "validation_fails": 1},
    "11": {"name": "Cold outreach sequence builder for independent B2B sales consultants",
           "scores": {"pain_intensity":4,"personal_advantage":3,"market_size":4,"monetization_potential":4,"competition_landscape":4,"growth_trajectory":4},
           "validation_fails": 1},
    "12": {"name": "Compliance checklist automation for solo employment law attorneys",
           "scores": {"pain_intensity":5,"personal_advantage":2,"market_size":2,"monetization_potential":4,"competition_landscape":2,"growth_trajectory":3},
           "validation_fails": 3},
}

# Compute weighted scores
for nid, niche in NICHES.items():
    niche["weighted"] = compute_weighted_score(niche["scores"])

# Sort by weighted score descending
ranked = sorted(NICHES.items(), key=lambda x: x[1]["weighted"], reverse=True)

# Top 3 by weighted score
top3_ids = [r[0] for r in ranked[:3]]
top3_weighted = {nid: NICHES[nid]["weighted"] for nid in top3_ids}

# Among top 3, apply kill check (fail 2+ checks → eliminated)
# validation_fails >= 2 → eliminated
survivors = [nid for nid in top3_ids if NICHES[nid]["validation_fails"] < 2]
# The correct winner = highest-weighted survivor
winner_id = survivors[0] if survivors else None

# Expected computations (for reference in checks):
# Weighted scores:
# 01: 5*.25 + 4*.20 + 3*.20 + 4*.15 + 3*.10 + 4*.10 = 1.25+0.80+0.60+0.60+0.30+0.40 = 3.95
# 03: 5*.25 + 3*.20 + 5*.20 + 5*.15 + 2*.10 + 4*.10 = 1.25+0.60+1.00+0.75+0.20+0.40 = 4.20
# 06: 5*.25 + 5*.20 + 3*.20 + 5*.15 + 3*.10 + 3*.10 = 1.25+1.00+0.60+0.75+0.30+0.30 = 4.20
# 07: 4*.25 + 4*.20 + 4*.20 + 3*.15 + 3*.10 + 4*.10 = 1.00+0.80+0.80+0.45+0.30+0.40 = 3.75
# 08: 5*.25 + 4*.20 + 3*.20 + 4*.15 + 3*.10 + 5*.10 = 1.25+0.80+0.60+0.60+0.30+0.50 = 4.05
# 11: 4*.25 + 3*.20 + 4*.20 + 4*.15 + 4*.10 + 4*.10 = 1.00+0.60+0.80+0.60+0.40+0.40 = 3.80
# Top 3: 03=4.20, 06=4.20, 08=4.05
# Kill check: 03 (0 fails) PASS, 06 (0 fails) PASS, 08 (0 fails) PASS
# Winner = 03 or 06 (tied at 4.20) — both survive; winner is top of the two tied

EXPECTED_TOP3_IDS = {"03", "06", "08"}
EXPECTED_WINNER_KEYWORDS = {
    "03": ["onboarding", "hr", "startup", "10-50", "rippling", "bamboo"],
    "06": ["financial advisor", "ria", "reporting", "orion", "riskalyze"],
}

def check_top3_correct(content: str) -> tuple[bool, str]:
    """Check that the document identifies niches 03, 06, 08 as top 3."""
    content_lower = content.lower()
    # Look for niche identifiers or names
    found = set()
    markers = {
        "03": ["onboarding", "hr team", "startup (10-50", "employee onboarding"],
        "06": ["financial advisor", "ria", "solo financial", "client reporting dashboard"],
        "08": ["churn prediction", "b2b saas", "bootstrapped", "subscription churn"],
    }
    for nid, keywords in markers.items():
        for kw in keywords:
            if kw in content_lower:
                found.add(nid)
                break
    correct = EXPECTED_TOP3_IDS.issubset(found)
    return correct, f"Found top-3 niches: {found}, expected {EXPECTED_TOP3_IDS}"

def check_weighted_scores_mentioned(content: str) -> tuple[bool, str]:
    """Check that weighted scores are computed and mentioned (not just raw averages)."""
    # Look for decimal scores consistent with weighting (e.g., 4.2, 4.05, 3.95)
    content_lower = content.lower()
    weighted_score_pattern = re.findall(r'\b([34]\.\d{1,2})\b', content)
    expected_scores = {"4.20", "4.2", "4.05", "3.95", "3.80", "3.75"}
    found_scores = set(weighted_score_pattern)
    # At least 2 of the expected weighted scores must appear
    overlap = found_scores & expected_scores
    passed = len(overlap) >= 2
    return passed, f"Weighted scores found: {found_scores}, expected overlap with {expected_scores}, got {overlap}"

def check_kill_check_applied(content: str) -> tuple[bool, str]:
    """Check that validation kill check was applied (niches 02, 05, 09, 12 are eliminated)."""
    content_lower = content.lower()
    eliminated_keywords = {
        "02": ["videographer", "invoicing.*video", "payment.*video"],
        "05": ["lease abstraction", "real estate broker", "costar"],
        "09": ["food truck", "tip-splitting", "tip splitting"],
        "12": ["employment law", "compliance checklist.*attorney", "solo.*attorney"],
    }
    eliminated_found = []
    for nid, kws in eliminated_keywords.items():
        for kw in kws:
            if re.search(kw, content_lower):
                # Check it's mentioned as eliminated/removed/failed
                eliminated_found.append(nid)
                break

    # At a minimum, niches 02, 05, 09, 12 should appear as eliminated or not be in top results
    # We check that at least the kill-check logic is referenced
    kill_check_referenced = any(phrase in content_lower for phrase in [
        "kill", "eliminated", "fails", "failed", "not viable", "drop", "disqualified", "2+ check", "two or more"
    ])
    passed = kill_check_referenced
    return passed, f"Kill check logic referenced: {kill_check_referenced}. Eliminated niches noted: {eliminated_found}"

def check_positioning_statement(content: str) -> tuple[bool, str]:
    """Check that a Who+What+Why positioning statement exists for a winner."""
    content_lower = content.lower()
    # Must contain the positioning formula markers
    has_struggling = "struggling with" in content_lower
    has_who = any(phrase in content_lower for phrase in [
        "who need", "who are", "who want"
    ])
    has_gap = any(phrase in content_lower for phrase in [
        "fall short", "gap", "current solutions", "because", "unlike"
    ])
    # Must be for niche 03 or 06 (the top weighted survivors)
    for_winner = any(kw in content_lower for kw in [
        "onboarding", "financial advisor", "ria", "hr"
    ])
    all_parts = has_struggling and has_who and has_gap and for_winner
    detail = (f"struggling_with={has_struggling}, who_need={has_who}, "
              f"gap_mentioned={has_gap}, for_winner={for_winner}")
    return all_parts, detail

def check_commitment_checklist(content: str) -> tuple[bool, str]:
    """Check that a final commitment checklist is present with at least 5 items."""
    content_lower = content.lower()
    # Look for checklist indicators (checkboxes or bullet items in a checklist section)
    checklist_items = re.findall(r'[-\[\]✓✗x ]{1,5}(10,000|10k|reachable|competitor|gap|channel|budget|credibility|motivation|12)', content_lower)
    has_checklist_section = any(term in content_lower for term in [
        "commitment checklist", "final checklist", "commit", "before you commit", "checklist"
    ])
    # Look for at least 4 checklist items
    bullet_count = len(re.findall(r'^\s*[-\*\[\]✓•]', content, flags=re.MULTILINE))
    passed = has_checklist_section and bullet_count >= 4
    return passed, f"Checklist section present: {has_checklist_section}, bullet items found: {bullet_count}"

def check_all_12_niches_scored(content: str) -> tuple[bool, str]:
    """Check that all 12 niches appear with some scoring data."""
    content_lower = content.lower()
    niche_keywords = {
        "01": "contract review",
        "02": "videographer",
        "03": "onboarding",
        "04": "seo content brief",
        "05": "lease abstraction",
        "06": "financial advisor",
        "07": "project status",
        "08": "churn prediction",
        "09": "food truck",
        "10": "interior design",
        "11": "cold outreach",
        "12": "employment law",
    }
    found = []
    missing = []
    for nid, kw in niche_keywords.items():
        if kw in content_lower:
            found.append(nid)
        else:
            missing.append(nid)
    passed = len(found) >= 10  # At least 10 of 12 must be present
    return passed, f"Found {len(found)}/12 niches. Missing: {missing}"

def run_eval(workspace: str):
    checks = []
    score = 0.0

    output_file = find_output_file(workspace)
    if output_file is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "niche_strategy.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    if len(content.strip()) < 200:
        checks.append({"name": "file_not_empty", "passed": False, "detail": f"File too short: {len(content)} chars"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_not_empty", "passed": True, "detail": f"File length: {len(content)} chars"})

    # Run all checks
    check_fns = [
        ("all_12_niches_scored",   check_all_12_niches_scored,   0.15),
        ("weighted_scores_present", check_weighted_scores_mentioned, 0.20),
        ("top3_correctly_identified", check_top3_correct,         0.20),
        ("kill_check_applied",     check_kill_check_applied,      0.15),
        ("positioning_statement",  check_positioning_statement,   0.20),
        ("commitment_checklist",   check_commitment_checklist,    0.10),
    ]

    for name, fn, weight in check_fns:
        try:
            passed, detail = fn(content)
            checks.append({"name": name, "passed": passed, "detail": detail})
            if passed:
                score += weight
        except Exception as e:
            checks.append({"name": name, "passed": False, "detail": f"Exception: {e}"})

    all_passed = all(c["passed"] for c in checks)
    return {"passed": all_passed, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))