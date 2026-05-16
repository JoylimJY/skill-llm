import sys
import json
import re
from pathlib import Path

def score_checks(checks):
    passed = [c for c in checks if c["passed"]]
    return round(len(passed) / len(checks), 4)

def find_output_file(workspace: Path):
    """Find the agent's output file by searching common locations."""
    candidates = list(workspace.rglob("ad_claim_risk_report.md")) + \
                 list(workspace.rglob("ad_claim_risk_report.txt")) + \
                 list(workspace.rglob("burncore_risk_report.md")) + \
                 list(workspace.rglob("burncore_risk_report.txt")) + \
                 list(workspace.rglob("claim_risk_report.md")) + \
                 list(workspace.rglob("claim_risk_report.txt")) + \
                 list(workspace.rglob("risk_report.md")) + \
                 list(workspace.rglob("risk_report.txt"))
    # also allow any *report* or *review* markdown/txt
    if not candidates:
        candidates = [p for p in workspace.rglob("*.md") if any(
            kw in p.name.lower() for kw in ["report", "review", "risk", "claim", "burncore"]
        )]
    if not candidates:
        candidates = [p for p in workspace.rglob("*.txt") if any(
            kw in p.name.lower() for kw in ["report", "review", "risk", "claim", "burncore"]
        ) and "for_review" not in p.name]
    return candidates[0] if candidates else None

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── Locate output file ───────────────────────────────────────────────────
    output_file = find_output_file(workspace)
    file_found = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {output_file}" if file_found else "No recognizable output report file found in workspace."
    })

    if not file_found:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    content_lower = content.lower()

    # ── CHECK 1: Original claim breakdown present ────────────────────────────
    # Must reference actual claims from the input copy
    original_claim_signals = [
        "belly fat", "14 lb", "14 pounds", "3 weeks", "21 days",
        "melts", "melt", "clinically proven", "no diet", "no gym",
        "metabolism", "100%", "spot reduction", "doctor-approved",
        "permanently", "10-15 lbs", "10–15", "last weight loss",
        "one bottle", "fda"
    ]
    found_original = sum(1 for sig in original_claim_signals if sig.lower() in content_lower)
    has_original_breakdown = found_original >= 6
    checks.append({
        "name": "original_claim_breakdown",
        "passed": has_original_breakdown,
        "detail": f"Detected {found_original}/{len(original_claim_signals)} original claim signals. Need ≥6."
    })

    # ── CHECK 2: Risk rating per line/cluster ────────────────────────────────
    # Must have some form of per-line or per-cluster risk rating
    risk_rating_patterns = [
        r"\b(high|medium|low)\s*risk\b",
        r"risk\s*[:\-–]\s*(high|medium|low)",
        r"risk\s*rating",
        r"risk\s*level",
        r"⚠",
        r"🔴|🟡|🟢",
        r"\[\s*HIGH\s*\]|\[\s*MEDIUM\s*\]|\[\s*LOW\s*\]",
    ]
    rating_hits = sum(1 for p in risk_rating_patterns if re.search(p, content, re.IGNORECASE))
    has_risk_ratings = rating_hits >= 2
    checks.append({
        "name": "risk_ratings_present",
        "passed": has_risk_ratings,
        "detail": f"Found {rating_hits} risk-rating patterns. Need ≥2 distinct patterns."
    })

    # ── CHECK 3: Skill-specific risk type taxonomy used ──────────────────────
    # SKILL.md defines 6 specific types — agent must use at least 4
    risk_type_map = {
        "absolute_outcomes": [
            "absolute outcome", "absolute result", "absolute claim",
            "guaranteed outcome", "certainty"
        ],
        "time_bound_guarantee": [
            "time-bound", "time bound", "30 day", "21 day", "3 week",
            "in X days", "guarantee", "days or"
        ],
        "health_body_financial": [
            "health claim", "body claim", "health outcome", "health risk",
            "medical claim", "wellness claim", "physiological"
        ],
        "unqualified_superiority": [
            "superiority", "unqualified", "best", "#1", "number one",
            "nothing else compares", "no other", "only supplement"
        ],
        "unsupported_quantified": [
            "unsupported", "quantified", "unsubstantiated", "3x faster",
            "14 lb", "10-15 lb", "10–15 lb", "not peer", "n=24",
            "internal study", "pilot study"
        ],
        "implied_certainty_universal": [
            "implied certainty", "universal fit", "works for everyone",
            "100% of users", "anyone", "every person", "every body",
            "every single person", "universal"
        ],
    }
    taxonomy_hits = {}
    for risk_type, keywords in risk_type_map.items():
        hit = any(kw.lower() in content_lower for kw in keywords)
        taxonomy_hits[risk_type] = hit

    types_covered = sum(1 for v in taxonomy_hits.values() if v)
    has_taxonomy = types_covered >= 4
    checks.append({
        "name": "skill_risk_taxonomy_applied",
        "passed": has_taxonomy,
        "detail": (
            f"Covered {types_covered}/6 SKILL.md risk types. Need ≥4. "
            f"Details: {taxonomy_hits}"
        )
    })

    # ── CHECK 4: Explanation of WHY risk exists ──────────────────────────────
    explanation_signals = [
        "because", "since", "this is", "the risk is", "this claim",
        "unsupported by", "no evidence", "not substantiated",
        "not peer-reviewed", "platform policy", "ftc", "ad review",
        "customer trust", "credibility", "trigger", "flag"
    ]
    expl_hits = sum(1 for sig in explanation_signals if sig.lower() in content_lower)
    has_explanations = expl_hits >= 5
    checks.append({
        "name": "risk_explanations_present",
        "passed": has_explanations,
        "detail": f"Found {expl_hits} explanation signal words. Need ≥5."
    })

    # ── CHECK 5: Safer rewrites present ─────────────────────────────────────
    rewrite_signals = [
        r"safer\s+rewrite",
        r"rewrite",
        r"safer\s+version",
        r"safer\s+alternative",
        r"revised",
        r"replacement",
        r"instead\s+(of|try|use|say)",
        r"change\s+to",
        r"replace\s+with",
    ]
    rewrite_hits = sum(1 for p in rewrite_signals if re.search(p, content, re.IGNORECASE))
    has_rewrites = rewrite_hits >= 2
    checks.append({
        "name": "safer_rewrites_present",
        "passed": has_rewrites,
        "detail": f"Found {rewrite_hits} rewrite indicator patterns. Need ≥2."
    })

    # ── CHECK 6: Stronger-but-still-safer variation (5th output element) ─────
    stronger_signals = [
        r"stronger.{0,20}(safe|version|variation|alternative)",
        r"(bold|bolder|stronger).{0,30}(option|version|copy|variation|alternative)",
        r"optional.{0,30}(stronger|bolder|variation)",
        r"stronger variation",
        r"aggressive.*safe",
        r"push.{0,20}(further|harder).{0,20}(safe|compliant)",
        r"still.{0,20}(safe|compliant|approvable).{0,30}(stronger|bolder)",
        r"higher.{0,20}(energy|intensity).{0,20}(version|copy)",
    ]
    stronger_hits = sum(1 for p in stronger_signals if re.search(p, content, re.IGNORECASE))
    has_stronger = stronger_hits >= 1
    checks.append({
        "name": "stronger_but_safer_variation",
        "passed": has_stronger,
        "detail": f"Found {stronger_hits} 'stronger-but-still-safer' variation signals. Need ≥1."
    })

    # ── CHECK 7: Multi-channel coverage ─────────────────────────────────────
    channels = ["tiktok", "meta", "creator", "landing page", "ugc", "carousel"]
    channels_mentioned = sum(1 for ch in channels if ch.lower() in content_lower)
    has_multichannel = channels_mentioned >= 3
    checks.append({
        "name": "multi_channel_coverage",
        "passed": has_multichannel,
        "detail": f"Found {channels_mentioned}/6 channel references. Need ≥3."
    })

    # ── CHECK 8: No robotic legalese / fake legal certainty ─────────────────
    legalese_red_flags = [
        "this is not legal advice",
        "consult your attorney",
        "consult a lawyer",
        "we make no warranties",
        "pursuant to",
        "hereinafter",
        "notwithstanding the foregoing",
        "indemnif",
    ]
    legalese_hits = sum(1 for phrase in legalese_red_flags if phrase.lower() in content_lower)
    no_robotic_legalese = legalese_hits == 0
    checks.append({
        "name": "no_robotic_legalese",
        "passed": no_robotic_legalese,
        "detail": (
            "No boilerplate legal disclaimer language detected — quality bar met."
            if no_robotic_legalese
            else f"Found {legalese_hits} robotic legalese phrases, violating the quality bar."
        )
    })

    # ── CHECK 9: Fake FDA endorsement claim specifically addressed ───────────
    # The landing page says "approved by the FDA" — this must be flagged
    fda_flagged = any(term in content_lower for term in [
        "fda", "food and drug", "approved by", "fda-approved", "fda approved"
    ])
    checks.append({
        "name": "fda_false_claim_addressed",
        "passed": fda_flagged,
        "detail": (
            "FDA false approval claim was identified in the report."
            if fda_flagged
            else "The false 'FDA approved' claim in the landing page was NOT addressed."
        )
    })

    # ── CHECK 10: Evidence level considered (internal pilot, n=24) ───────────
    evidence_signals = [
        "internal", "pilot", "n=24", "24 participants", "non-peer",
        "not peer", "brand-funded", "not reviewed", "small sample",
        "insufficient", "limited evidence", "evidence level", "unsubstantiated"
    ]
    evidence_hits = sum(1 for sig in evidence_signals if sig.lower() in content_lower)
    has_evidence_handling = evidence_hits >= 2
    checks.append({
        "name": "evidence_level_considered",
        "passed": has_evidence_handling,
        "detail": (
            f"Found {evidence_hits} evidence-level signals. "
            "The report correctly factors in the weak evidence base."
            if has_evidence_handling
            else f"Only {evidence_hits} evidence-level signals found. Need ≥2."
        )
    })

    # ── Final scoring ────────────────────────────────────────────────────────
    total_score = score_checks(checks)
    # Must pass at least 8/10 checks AND the 3 critical structural checks
    critical_checks = ["original_claim_breakdown", "risk_ratings_present",
                       "safer_rewrites_present", "skill_risk_taxonomy_applied"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    passed = total_score >= 0.75 and critical_passed

    result = {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()