import sys
import json
import re
from pathlib import Path

def load_plan(workspace: str):
    hits = list(Path(workspace).rglob("education_program_plan.md"))
    if not hits:
        return None, "education_program_plan.md not found anywhere in workspace"
    # prefer root-level if multiple
    hits.sort(key=lambda p: len(p.parts))
    return hits[0].read_text(encoding="utf-8"), str(hits[0])

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1]
    text, location = load_plan(workspace)

    checks = []
    score = 0.0
    total_weights = 0.0

    # Helper
    def add(c, weight=1.0):
        nonlocal score, total_weights
        total_weights += weight
        if c["passed"]:
            score += weight
        checks.append(c)

    if text is None:
        checks.append(check("file_exists", False, location))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("file_exists", True, f"Found at {location}"))
    score += 1.0
    total_weights += 1.0

    tl = text.lower()

    # ── 1. Project context was read ────────────────────────────────────────
    # Should mention CodeLens / Pro plan / $29 or the product name
    ctx_read = "codelens" in tl or "code lens" in tl
    add(check(
        "project_context_read",
        ctx_read,
        "Plan should reference the product name 'CodeLens' extracted from project-context.md"
    ), weight=1.5)

    # ── 2. Discount structure: first-time in 30-50% range ─────────────────
    first_time_numbers = re.findall(r'(\d+)\s*%', text)
    first_time_ints = [int(n) for n in first_time_numbers]
    ft_ok = any(30 <= n <= 50 for n in first_time_ints)
    add(check(
        "first_time_discount_in_range",
        ft_ok,
        f"First-time discount must be 30–50%. Found percentages: {first_time_ints}"
    ), weight=2.0)

    # ── 3. Renewal discount in 15-25% range ───────────────────────────────
    renewal_ok = any(15 <= n <= 25 for n in first_time_ints)
    add(check(
        "renewal_discount_in_range",
        renewal_ok,
        f"Renewal discount must be 15–25%. Found percentages: {first_time_ints}"
    ), weight=2.0)

    # ── 4. First-time discount is strictly higher than renewal ────────────
    # Find two distinct values that satisfy the ranges
    first_time_vals = [n for n in first_time_ints if 30 <= n <= 50]
    renewal_vals = [n for n in first_time_ints if 15 <= n <= 25]
    hierarchy_ok = bool(first_time_vals and renewal_vals and max(first_time_vals) > max(renewal_vals))
    add(check(
        "first_time_greater_than_renewal",
        hierarchy_ok,
        f"First-time discount ({first_time_vals}) must be numerically higher than renewal ({renewal_vals})"
    ), weight=1.0)

    # ── 5. Verification method named ──────────────────────────────────────
    verif_methods = ["sheerid", "unidays", ".edu", "edu email", "student id"]
    verif_found = [m for m in verif_methods if m in tl]
    verif_ok = len(verif_found) >= 1
    add(check(
        "verification_method_present",
        verif_ok,
        f"Must name at least one verification method (SheerID, UNiDAYS, .edu, student ID). Found: {verif_found}"
    ), weight=1.5)

    # ── 6. P0 placement = registration / signup ───────────────────────────
    p0_ok = bool(re.search(r'p0', tl)) and bool(
        re.search(r'(registr|signup|sign.up)', tl)
    )
    # Also accept phrasing without P0 label but correct content
    if not p0_ok:
        p0_ok = bool(re.search(
            r'(registr|signup|sign.up).{0,120}(highest|primary|first|core|must|p0)',
            tl, re.DOTALL
        ))
    add(check(
        "p0_placement_registration",
        p0_ok,
        "Registration/signup must be identified as the highest-priority (P0) placement"
    ), weight=2.0)

    # ── 7. P1 placement = pricing page ────────────────────────────────────
    p1_pricing_ok = bool(re.search(r'p1', tl)) and bool(re.search(r'pricing', tl))
    if not p1_pricing_ok:
        p1_pricing_ok = bool(re.search(r'pricing.{0,80}(p1|secondary|support)', tl, re.DOTALL))
    add(check(
        "p1_placement_pricing_page",
        p1_pricing_ok,
        "Pricing page must be identified as P1 placement"
    ), weight=1.5)

    # ── 8. Page strategy: registration-only or embed; NOT standalone as primary ──
    # The product discount applies at signup (per project-context), so standalone page
    # is P2 (optional). The plan should NOT recommend standalone as the primary strategy.
    standalone_as_primary = bool(re.search(
        r'(primary|main|core|recommended|should create|create a standalone).{0,80}(standalone|/student-discount)',
        tl, re.DOTALL
    ))
    # pricing page embed or registration wording should be primary
    embed_or_reg = bool(re.search(
        r'(embed.{0,60}pricing|pricing.{0,60}embed|registr.{0,60}(primary|core|main)|page strategy.{0,120}(embed|registr))',
        tl, re.DOTALL | re.IGNORECASE
    ))
    page_strategy_ok = embed_or_reg and not standalone_as_primary
    add(check(
        "page_strategy_correct",
        page_strategy_ok,
        "Page strategy should favour embed-in-pricing or registration-only; standalone /student-discount is P2 only"
    ), weight=2.0)

    # ── 9. Graduation / transition plan mentioned ──────────────────────────
    grad_ok = bool(re.search(r'(graduat|transition|expir|eligib)', tl))
    add(check(
        "graduation_transition_mentioned",
        grad_ok,
        "Plan must address graduation/eligibility expiry and transition to full price"
    ), weight=1.0)

    # ── 10. Related skills from SKILL.md referenced ───────────────────────
    skill_refs = [
        "pricing-page-generator",
        "top-banner-generator",
        "signup-login-page-generator",
        "discount-marketing-strategy",
    ]
    found_skills = [s for s in skill_refs if s.replace("-", " ") in tl or s in tl]
    skills_ok = len(found_skills) >= 2
    add(check(
        "related_skills_referenced",
        skills_ok,
        f"Must reference ≥2 related skills. Found: {found_skills}"
    ), weight=1.5)

    # ── 11. 65% statistic or long-term acquisition framing ────────────────
    ltv_ok = bool(re.search(r'(65\s*%|long.term|post.grad|ltv|future customer)', tl))
    add(check(
        "ltv_framing_present",
        ltv_ok,
        "Should reference 65% post-grad retention or long-term customer acquisition framing"
    ), weight=1.0)

    # ── 12. Abuse prevention / annual re-verification ─────────────────────
    abuse_ok = bool(re.search(r'(re.verif|annual|abuse|revok|ineligible|limit per)', tl))
    add(check(
        "abuse_prevention_mentioned",
        abuse_ok,
        "Plan must mention abuse prevention (annual re-verification, revocation, or per-person limit)"
    ), weight=1.0)

    # ── Final scoring ──────────────────────────────────────────────────────
    final_score = round(score / total_weights, 4) if total_weights > 0 else 0.0
    overall_passed = final_score >= 0.72 and all(
        c["passed"] for c in checks
        if c["name"] in {
            "file_exists",
            "first_time_discount_in_range",
            "renewal_discount_in_range",
            "p0_placement_registration",
            "page_strategy_correct",
        }
    )

    print(json.dumps({
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()