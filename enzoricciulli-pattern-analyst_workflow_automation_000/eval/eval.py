import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: notes/patterns.md exists
    # -----------------------------------------------------------------------
    patterns_path = workspace / "notes" / "patterns.md"
    try:
        assert patterns_path.exists(), "notes/patterns.md does not exist"
        content = patterns_path.read_text(encoding="utf-8")
        checks.append({"name": "patterns.md exists", "passed": True, "detail": "File found at notes/patterns.md"})
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "patterns.md exists", "passed": False, "detail": str(e)})
        content = ""

    # -----------------------------------------------------------------------
    # CHECK 2: Correct date headers present (at least 4 of the 5 interaction dates)
    # -----------------------------------------------------------------------
    expected_dates = ["2024-06-01", "2024-06-03", "2024-06-05", "2024-06-07", "2024-06-09"]
    found_dates = [d for d in expected_dates if f"## {d}" in content]
    try:
        assert len(found_dates) >= 4, f"Only {len(found_dates)} date headers found; expected at least 4"
        checks.append({
            "name": "Date headers in patterns.md",
            "passed": True,
            "detail": f"Found date headers: {found_dates}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Date headers in patterns.md", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 3: Required section headers (### Observations, ### Emerging Patterns, ### Goal Connections)
    # -----------------------------------------------------------------------
    try:
        has_obs = "### Observations" in content
        has_ep = "### Emerging Patterns" in content
        has_gc = "### Goal Connections" in content
        assert has_obs and has_ep and has_gc, (
            f"Missing required sections — Observations: {has_obs}, "
            f"Emerging Patterns: {has_ep}, Goal Connections: {has_gc}"
        )
        checks.append({
            "name": "Required section headers present",
            "passed": True,
            "detail": "All three section types (Observations, Emerging Patterns, Goal Connections) found"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Required section headers present", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 4: Correct content-type labels used (Frameworks, AI Hacks, Ideas, Questions, Frustrations, Inspirations)
    # -----------------------------------------------------------------------
    valid_types = ["Frameworks", "Framework", "AI Hacks", "AI Hack", "Ideas", "Idea",
                   "Questions", "Question", "Frustrations", "Frustration", "Inspirations", "Inspiration"]
    found_types = [t for t in valid_types if t.lower() in content.lower()]
    try:
        assert len(set([t.lower() for t in found_types])) >= 3, (
            f"Expected at least 3 distinct content-type labels; found: {found_types}"
        )
        checks.append({
            "name": "Content-type labels used",
            "passed": True,
            "detail": f"Found content types: {list(set([t.lower() for t in found_types]))}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Content-type labels used", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 5: Intent signals used (learn, build, share, remember, vent, decide)
    # -----------------------------------------------------------------------
    intent_signals = ["learn", "build", "share", "remember", "vent", "decide"]
    found_intents = [i for i in intent_signals if i in content.lower()]
    try:
        assert len(found_intents) >= 2, (
            f"Expected at least 2 intent signal labels; found: {found_intents}"
        )
        checks.append({
            "name": "Intent signals used",
            "passed": True,
            "detail": f"Found intent signals: {found_intents}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Intent signals used", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 6: [AUTO-CONFIRMED] tag present in patterns.md
    # The marketing frameworks pattern appears 4 times (Jun 01, 05, 07, 09) — 
    # exceeds the 3-repetition threshold and MUST be auto-confirmed.
    # -----------------------------------------------------------------------
    try:
        has_autoconfirm = "[AUTO-CONFIRMED]" in content
        assert has_autoconfirm, (
            "[AUTO-CONFIRMED] tag not found in patterns.md. "
            "Marketing frameworks appeared 4 times — should trigger auto-confirmation."
        )
        checks.append({
            "name": "[AUTO-CONFIRMED] tag in patterns.md",
            "passed": True,
            "detail": "[AUTO-CONFIRMED] tag found — agent correctly detected recurring pattern"
        })
        total_score += 2.0
    except Exception as e:
        checks.append({"name": "[AUTO-CONFIRMED] tag in patterns.md", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 7: Marketing frameworks pattern is specifically associated with AUTO-CONFIRMED
    # The auto-confirmed item should relate to marketing frameworks or frameworks generally
    # -----------------------------------------------------------------------
    try:
        # Find lines near [AUTO-CONFIRMED]
        lines = content.splitlines()
        autoconfirm_lines = [l for l in lines if "[AUTO-CONFIRMED]" in l]
        framework_autoconfirm = any(
            re.search(r'(framework|marketing)', l, re.IGNORECASE)
            for l in autoconfirm_lines
        )
        assert framework_autoconfirm, (
            f"[AUTO-CONFIRMED] tag found but not linked to marketing frameworks pattern. "
            f"Lines with AUTO-CONFIRMED: {autoconfirm_lines}"
        )
        checks.append({
            "name": "AUTO-CONFIRMED linked to marketing frameworks",
            "passed": True,
            "detail": f"AUTO-CONFIRMED correctly tied to frameworks: {autoconfirm_lines}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "AUTO-CONFIRMED linked to marketing frameworks", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 8: USER.md updated with auto-confirmed pattern
    # Per the skill: "Update USER.md immediately" after auto-confirm
    # -----------------------------------------------------------------------
    user_md_path = workspace / "USER.md"
    try:
        user_content = user_md_path.read_text(encoding="utf-8")
        # Check for evidence of an update related to marketing frameworks
        updated = re.search(
            r'(marketing framework|frameworks library|AARRR|Jobs.to.be.done|Porter|4Ps|framework)',
            user_content,
            re.IGNORECASE
        )
        assert updated, (
            "USER.md does not appear to have been updated with the auto-confirmed marketing frameworks pattern. "
            "Skill requires USER.md update immediately upon auto-confirmation."
        )
        checks.append({
            "name": "USER.md updated with auto-confirmed pattern",
            "passed": True,
            "detail": f"USER.md contains framework-related update: '{updated.group()}'"
        })
        total_score += 2.0
    except FileNotFoundError:
        checks.append({
            "name": "USER.md updated with auto-confirmed pattern",
            "passed": False,
            "detail": "USER.md not found"
        })
    except Exception as e:
        checks.append({
            "name": "USER.md updated with auto-confirmed pattern",
            "passed": False,
            "detail": str(e)
        })

    # -----------------------------------------------------------------------
    # CHECK 9: Goal Connections section references known goals (trading, hackathon, AI trends, etc.)
    # -----------------------------------------------------------------------
    try:
        goal_keywords = ["trading", "hackathon", "ai lead", "ai trend", "mediaplus", "fintech", "development workflow"]
        # Find content in ### Goal Connections sections
        gc_sections = re.findall(r'### Goal Connections\s*(.*?)(?=###|\Z|## \d)', content, re.DOTALL | re.IGNORECASE)
        gc_text = " ".join(gc_sections).lower()
        found_goal_refs = [k for k in goal_keywords if k in gc_text]
        assert len(found_goal_refs) >= 1, (
            f"Goal Connections sections don't reference any known goals. "
            f"Expected at least one of: {goal_keywords}. Got: '{gc_text[:200]}'"
        )
        checks.append({
            "name": "Goal Connections references known goals",
            "passed": True,
            "detail": f"Found goal references: {found_goal_refs}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Goal Connections references known goals", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # CHECK 10: Emerging Patterns section contains insight (convergence/contradiction/opportunity/progress/gap)
    # -----------------------------------------------------------------------
    try:
        insight_types = ["convergence", "contradiction", "opportunity", "progress", "gap", 
                         "keep coming back", "haven't touched", "moved from", "you say"]
        ep_sections = re.findall(r'### Emerging Patterns\s*(.*?)(?=###|\Z|## \d)', content, re.DOTALL | re.IGNORECASE)
        ep_text = " ".join(ep_sections).lower()
        found_insights = [i for i in insight_types if i in ep_text]
        assert len(found_insights) >= 1 or len(ep_text.strip()) > 20, (
            f"Emerging Patterns section appears empty or lacks insight types. "
            f"Expected patterns summarizing cross-interaction themes."
        )
        checks.append({
            "name": "Emerging Patterns contains substantive insight",
            "passed": True,
            "detail": f"Found insight signals: {found_insights}; EP text length: {len(ep_text)}"
        })
        total_score += 1.0
    except Exception as e:
        checks.append({"name": "Emerging Patterns contains substantive insight", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    max_score = 12.0
    normalized = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))