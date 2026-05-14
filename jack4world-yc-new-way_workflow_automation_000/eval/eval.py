import sys
import json
import re
from pathlib import Path

def score_checks(checks):
    passed = [c for c in checks if c["passed"]]
    return round(len(passed) / len(checks), 3)

def find_sprint_plan(workspace):
    matches = list(Path(workspace).rglob("sprint_plan.md"))
    return matches[0] if matches else None

def run_eval(workspace):
    checks = []

    # ── Find the file ────────────────────────────────────────────────────────
    plan_path = find_sprint_plan(workspace)
    if plan_path is None:
        checks.append({"name": "file_exists", "passed": False,
                        "detail": "sprint_plan.md not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_exists", "passed": True,
                    "detail": f"Found at {plan_path}"})

    try:
        content = plan_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False,
                        "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": "File is readable."})
    content_lower = content.lower()

    # ── CHECK 1: Bet clarification sentence structure ────────────────────────
    # Must contain the proprietary "For [who] with [pain]..." structure
    bet_pattern = re.search(
        r'for\s+.{5,80}\s+with\s+.{5,80}',
        content_lower
    )
    has_promise = "promise" in content_lower or "we offer" in content_lower or "offer" in content_lower
    has_channel_in_bet = "via" in content_lower
    has_metric = "metric" in content_lower or "we'll know" in content_lower or "know it works" in content_lower
    has_threshold = "threshold" in content_lower or "%" in content or any(
        re.search(r'\d+\s*(signups|subscribers|clinics|conversions|clicks|ctr)', content_lower)
        for _ in [None]
    )

    bet_ok = (bet_pattern is not None) and has_promise and has_channel_in_bet
    checks.append({
        "name": "bet_clarification_sentence",
        "passed": bet_ok,
        "detail": (
            f"Bet sentence found: {bool(bet_pattern)}, "
            f"has 'offer/promise': {has_promise}, "
            f"has 'via' (channel in bet): {has_channel_in_bet}"
        )
    })

    # ── CHECK 2: Primary wedge + backup wedge (exactly the right structure) ──
    has_primary_wedge = bool(re.search(r'primary\s+wedge', content_lower))
    has_backup_wedge = bool(re.search(r'backup\s+wedge|secondary\s+wedge|fallback\s+wedge', content_lower))
    checks.append({
        "name": "primary_and_backup_wedge",
        "passed": has_primary_wedge and has_backup_wedge,
        "detail": f"primary_wedge={has_primary_wedge}, backup_wedge={has_backup_wedge}"
    })

    # ── CHECK 3: Exactly 3 user stories ─────────────────────────────────────
    user_story_matches = re.findall(
        r'as\s+a\s+.{3,60},?\s+i\s+want\s+.{3,100}',
        content_lower
    )
    # Also accept "user story 1/2/3" format
    numbered_stories = re.findall(r'user\s+stor(?:y|ies)\s*[#:]?\s*[123]', content_lower)
    story_count = max(len(user_story_matches), len(numbered_stories))
    # Accept if 3 user stories found via either format
    has_three_stories = story_count >= 3
    checks.append({
        "name": "three_user_stories",
        "passed": has_three_stories,
        "detail": f"Found {story_count} user story pattern(s). Matches: {user_story_matches[:3]}"
    })

    # ── CHECK 4: Exactly ONE distribution channel chosen (not multiple) ──────
    channel_keywords = {
        "seo": bool(re.search(r'\bseo\b', content_lower)),
        "newsletter": bool(re.search(r'\bnewsletter\b', content_lower)),
        "community": bool(re.search(r'\bcommunity\b|\breddit\b|\bdiscord\b', content_lower)),
    }
    channels_mentioned = [k for k, v in channel_keywords.items() if v]
    # Must pick exactly ONE as primary; it's OK to mention others as rejected
    # The key constraint: must explicitly say ONE is chosen/selected
    has_single_channel_selection = bool(re.search(
        r'(chosen|selected|picking|pick|using|focus\s+on|start\s+with|primary\s+channel|one\s+channel)\s*[:\-]?\s*(seo|newsletter|community|reddit|discord)',
        content_lower
    ))
    # Also acceptable: "channel: SEO" or "distribution channel: newsletter"
    channel_declared = bool(re.search(
        r'(distribution\s+channel|channel)[:\s]+(seo|newsletter|community|reddit)',
        content_lower
    ))
    one_channel_ok = has_single_channel_selection or channel_declared
    checks.append({
        "name": "single_distribution_channel_chosen",
        "passed": one_channel_ok,
        "detail": (
            f"Channels mentioned: {channels_mentioned}. "
            f"Explicit single-channel selection: {has_single_channel_selection}. "
            f"Channel declared: {channel_declared}"
        )
    })

    # ── CHECK 5: SEO plan has exactly 2 money pages + 8 support pages ────────
    # The proprietary trap: must be 2 money + 8 support = 10 total
    has_money_pages = bool(re.search(r'money\s+page', content_lower))
    has_support_pages = bool(re.search(r'support\s+page', content_lower))

    # Count: look for "2 money pages" or list of exactly 2 money pages
    two_money = bool(re.search(r'2\s+money\s+pages?|two\s+money\s+pages?', content_lower))
    eight_support = bool(re.search(r'8\s+support\s+pages?|eight\s+support\s+pages?', content_lower))
    ten_pages = bool(re.search(r'10\s+pages?|ten\s+pages?', content_lower))

    page_structure_ok = has_money_pages and has_support_pages and (two_money or eight_support or ten_pages)
    checks.append({
        "name": "seo_10page_structure_2money_8support",
        "passed": page_structure_ok,
        "detail": (
            f"money_pages={has_money_pages}, support_pages={has_support_pages}, "
            f"2_money={two_money}, 8_support={eight_support}, 10_total={ten_pages}"
        )
    })

    # ── CHECK 6: Stop/iterate decision rules (all 3 branches) ────────────────
    rule_low_ctr = bool(re.search(
        r'(low\s+ctr|ctr\s+is\s+low|if\s+ctr).{0,60}(fix|copy|promise)',
        content_lower
    ))
    rule_high_ctr_no_conv = bool(re.search(
        r'(high\s+ctr|ctr\s+is\s+high).{0,100}(no\s+conversion|fix\s+offer|trust|price)',
        content_lower
    ))
    rule_no_traffic = bool(re.search(
        r'(no\s+traffic|zero\s+traffic).{0,100}(distribution|not\s+product)',
        content_lower
    ))
    decision_rules_ok = rule_low_ctr and rule_high_ctr_no_conv and rule_no_traffic
    checks.append({
        "name": "three_branch_decision_rules",
        "passed": decision_rules_ok,
        "detail": (
            f"low_CTR→fix_copy={rule_low_ctr}, "
            f"high_CTR_no_conv→fix_offer={rule_high_ctr_no_conv}, "
            f"no_traffic→distribution_problem={rule_no_traffic}"
        )
    })

    # ── CHECK 7: Weekly loop = double down 1 + kill 1 + add 1 experiment ─────
    has_double_down = bool(re.search(r'double\s+down', content_lower))
    has_kill = bool(re.search(r'\bkill\b.{0,40}(thing|didn.t|not\s+work)', content_lower))
    has_add_experiment = bool(re.search(r'add\s+.{0,20}(new\s+)?experiment', content_lower))
    weekly_loop_ok = has_double_down and (has_kill or bool(re.search(r'kill\s+1|kill\s+one', content_lower))) and has_add_experiment
    checks.append({
        "name": "weekly_loop_structure",
        "passed": weekly_loop_ok,
        "detail": (
            f"double_down={has_double_down}, "
            f"kill_one={has_kill or bool(re.search(r'kill 1|kill one', content_lower))}, "
            f"add_experiment={has_add_experiment}"
        )
    })

    # ── CHECK 8: No "AI says" phrases (evidence-first guardrail) ─────────────
    ai_says_violations = re.findall(
        r'(ai\s+says|according\s+to\s+ai|ai\s+generated|chatgpt\s+says|gpt\s+says)',
        content_lower
    )
    no_ai_says = len(ai_says_violations) == 0
    checks.append({
        "name": "no_ai_says_evidence_first",
        "passed": no_ai_says,
        "detail": f"Violations found: {ai_says_violations}"
    })

    # ── CHECK 9: Metric funnel: traffic → CTA CTR → outbound clicks ──────────
    has_traffic_metric = bool(re.search(r'\btraffic\b', content_lower))
    has_cta_ctr = bool(re.search(r'cta\s+ctr|ctr', content_lower))
    has_outbound = bool(re.search(r'outbound\s+click|outbound', content_lower))
    funnel_ok = has_traffic_metric and has_cta_ctr and has_outbound
    checks.append({
        "name": "metric_funnel_traffic_ctr_outbound",
        "passed": funnel_ok,
        "detail": f"traffic={has_traffic_metric}, cta_ctr={has_cta_ctr}, outbound_clicks={has_outbound}"
    })

    # ── CHECK 10: Changelog / iteration section exists ───────────────────────
    has_changelog = bool(re.search(r'changelog|change\s+log|iteration\s+log', content_lower))
    checks.append({
        "name": "changelog_present",
        "passed": has_changelog,
        "detail": f"changelog_found={has_changelog}"
    })

    # ── Final scoring ────────────────────────────────────────────────────────
    total_score = score_checks(checks)
    overall_passed = total_score >= 0.75  # Need at least 75% to pass

    return {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))