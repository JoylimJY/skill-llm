import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    ws = Path(workspace)
    candidates = list(ws.rglob("community_playbook.md"))
    if candidates:
        return candidates[0]
    return None

def load_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str) -> dict:
    checks = []

    # ── FIND FILE ──────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("file_exists", False, "community_playbook.md not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append(check("file_exists", True, f"Found at {report_path}"))
    
    try:
        text = load_text(report_path)
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    text_lower = text.lower()

    # ── CHECK 1: All 4 required report sections present ──────────────────
    required_sections = [
        "target activity",
        "opportunities today",
        "suggested replies",
        "progress scorecard"
    ]
    missing_sections = []
    for sec in required_sections:
        if sec not in text_lower:
            missing_sections.append(sec)
    
    sections_ok = len(missing_sections) == 0
    checks.append(check(
        "four_required_sections",
        sections_ok,
        f"All 4 required sections present" if sections_ok else f"Missing sections: {missing_sections}"
    ))

    # ── CHECK 2: Competitor benchmark uses correct leaderboard name ──────
    # Must reference DarrenScottUK (given in input) AND must use leaderboard context
    # Must NOT rely solely on the outdated leaderboard from leaderboard_old.txt
    has_darren = "darrenscottuk" in text_lower
    # Also check that some of the actual current leaderboard names from champion-opportunities.md are mentioned
    current_leaderboard_names = ["danmoyle", "darrenscottuk", "snigam", "jigar_thakker", "himanshurauthan"]
    mentioned_current = [n for n in current_leaderboard_names if n.lower() in text_lower]
    
    competitor_ok = has_darren and len(mentioned_current) >= 1
    checks.append(check(
        "competitor_uses_current_leaderboard",
        competitor_ok,
        f"DarrenScottUK referenced: {has_darren}, Current leaderboard names mentioned: {mentioned_current}"
    ))

    # ── CHECK 3: Benchmark covers the 5 required competitor behavior dimensions ──
    benchmark_signals = [
        ("answer quickly", ["answer quickly", "quick", "3.1 hour", "3 hour", "response speed", "fast response", "time to first reply"]),
        ("simplify decisions", ["simplif", "direct answer", "direct recommendation", "clear"]),
        ("stay in thread", ["follow-up", "follow up", "stayed in thread", "stay in-thread", "in-thread", "additional repl"]),
        ("convert to accepted solutions", ["accepted solution", "solution rate", "convert", "412", "9 accepted"]),
        ("signature or call to action", ["signature", "mark.*solution", "let me know if you hit", "call to action", "cta", "no.*signature", "doesn.*signature"])
    ]
    
    benchmark_hits = []
    benchmark_misses = []
    for dimension, patterns in benchmark_signals:
        found = any(re.search(p, text_lower) for p in patterns)
        if found:
            benchmark_hits.append(dimension)
        else:
            benchmark_misses.append(dimension)
    
    benchmark_ok = len(benchmark_hits) >= 4
    checks.append(check(
        "benchmark_covers_5_competitor_dimensions",
        benchmark_ok,
        f"Covered: {benchmark_hits} | Missing: {benchmark_misses}"
    ))

    # ── CHECK 4: Opportunity selection prioritizes high-signal threads correctly ──
    # Must select from threads <48h old with 0 replies on CRM/Workflow/Reporting/Sales/Dev boards
    # Should include Thread 1 (Workflow, 0 replies, 3.75h old), Thread 2 (Sales Hub, 0 replies, 7.5h old),
    # Thread 3 (Reporting, 0 replies, 15h old), Thread 5 (Dev API, 0 replies, 1h old), 
    # Thread 8 (CRM merge, 0 replies, 11.75h old)
    # Should NOT recommend Thread 4 (25h, 2 replies, basic) or Thread 7 (3 replies, opinion)
    
    high_signal_threads = [
        "date field",          # Thread 1
        "sender name",         # Thread 2  
        "original source",     # Thread 3
        "batch upsert",        # Thread 5
        "contact merge",       # Thread 8 / "merge duplicate"
    ]
    low_value_threads = [
        "webflow",             # Thread 4 - already has replies, basic
        "vs salesforce",       # Thread 7 - opinion, 3 replies
        "vs. salesforce",
        "hubspot vs",
    ]
    
    high_signal_count = sum(1 for t in high_signal_threads if t in text_lower)
    low_value_present = any(t in text_lower for t in low_value_threads)
    
    # Must mention at least 3 high-signal threads and not primarily push low-value ones
    opportunity_ok = high_signal_count >= 3 and not low_value_present
    checks.append(check(
        "opportunity_selection_quality",
        opportunity_ok,
        f"High-signal threads referenced: {high_signal_count}/5, Low-value thread inappropriately prioritized: {low_value_present}"
    ))

    # ── CHECK 5: At least one suggested reply has all 4 quality components ──
    # direct recommendation + rationale/tradeoff + concrete implementation steps + validation/fallback
    quality_components = [
        ("direct_recommendation", ["recommend", "you should", "the fix is", "set the", "the issue is", "check the", "this is"]),
        ("rationale_or_tradeoff", ["because", "reason", "why", "tradeoff", "trade-off", "limitation", "gotcha", "note that", "this happens"]),
        ("implementation_steps", ["step", "navigate to", "go to", "click", "set", "enable", "configure", "in hubspot", "property", "workflow"]),
        ("validation_or_fallback", ["if it still", "if that doesn", "fallback", "verify", "confirm", "let me know", "check if", "if this doesn", "test"])
    ]
    
    reply_component_hits = []
    for comp_name, patterns in quality_components:
        if any(re.search(p, text_lower) for p in patterns):
            reply_component_hits.append(comp_name)
    
    reply_quality_ok = len(reply_component_hits) >= 4
    checks.append(check(
        "reply_has_all_4_quality_components",
        reply_quality_ok,
        f"Quality components present: {reply_component_hits}"
    ))

    # ── CHECK 6: AI disclosure note present ─────────────────────────────
    ai_disclosure_patterns = [
        r"ai.{0,20}disclos",
        r"disclos.{0,20}ai",
        r"ai.{0,20}assist",
        r"generated.{0,20}ai",
        r"ai.{0,20}generated",
        r"review.{0,20}before.{0,20}publish",
        r"verify.{0,20}accuracy",
        r"accuracy.{0,20}review",
        r"disclos.{0,20}assist"
    ]
    has_ai_disclosure = any(re.search(p, text_lower) for p in ai_disclosure_patterns)
    checks.append(check(
        "ai_disclosure_note_present",
        has_ai_disclosure,
        "AI assistance disclosure note found" if has_ai_disclosure else "No AI disclosure note found — required when drafting AI-assisted content"
    ))

    # ── CHECK 7: Champion opportunity types referenced correctly ─────────
    # Must use the 4 current types from champion-opportunities.md, not the old 2023 list
    current_types = ["social amplification", "content engagement", "user-generated content"]
    old_types = ["peer-to-peer help", "blog submission", "video content", "event participation"]
    
    current_types_found = [t for t in current_types if t in text_lower]
    old_types_found = [t for t in old_types if t in text_lower]
    
    champion_types_ok = len(current_types_found) >= 1 and len(old_types_found) == 0
    checks.append(check(
        "champion_opportunity_types_current",
        champion_types_ok,
        f"Current types referenced: {current_types_found}, Old/retired types used: {old_types_found}"
    ))

    # ── CHECK 8: Anti-spam guardrail present ─────────────────────────────
    anti_spam_patterns = [
        r"not automat",
        r"do not automat",
        r"avoid spam",
        r"no spam",
        r"quality.{0,30}volume",
        r"high.quality",
        r"high quality",
        r"avoid.{0,20}spam",
        r"manual",
        r"never submit.{0,20}automatically",
        r"not.{0,20}submit.{0,20}auto"
    ]
    has_guardrail = any(re.search(p, text_lower) for p in anti_spam_patterns)
    checks.append(check(
        "anti_spam_guardrail_present",
        has_guardrail,
        "Anti-spam / quality-over-volume guardrail mentioned" if has_guardrail else "No anti-spam or quality-over-volume guardrail found"
    ))

    # ── CHECK 9: Unanswered thread shortcut URLs referenced ──────────────
    # The skill explicitly mandates using the shortcut URLs, not generic board filters
    shortcut_url_patterns = [
        r"unansweredtopicspage",
        r"community\.hubspot\.com/t5/forums/unanswered",
        r"category:marketing",
        r"category:sales",
        r"node-display-id",
    ]
    has_shortcut_url = any(re.search(p, text_lower) for p in shortcut_url_patterns)
    checks.append(check(
        "unanswered_thread_shortcut_urls_used",
        has_shortcut_url,
        "Unanswered thread shortcut URL referenced" if has_shortcut_url else "No unanswered-thread shortcut URLs found — skill mandates these over board UI filters"
    ))

    # ── CHECK 10: Scorecard contains measurable progress indicators ──────
    scorecard_signals = [
        r"solution",
        r"accept",
        r"repl",
        r"upvote",
        r"thread",
        r"board",
        r"score",
        r"target",
        r"metric",
        r"goal",
        r"\d+",   # at least some numbers
    ]
    scorecard_section_start = text_lower.find("progress scorecard")
    if scorecard_section_start == -1:
        scorecard_section_start = text_lower.find("scorecard")
    
    if scorecard_section_start != -1:
        scorecard_text = text_lower[scorecard_section_start:scorecard_section_start + 1500]
        scorecard_hits = [p for p in scorecard_signals if re.search(p, scorecard_text)]
        scorecard_ok = len(scorecard_hits) >= 5
        checks.append(check(
            "scorecard_has_measurable_indicators",
            scorecard_ok,
            f"Scorecard signals found: {len(scorecard_hits)}/9 — {scorecard_hits}"
        ))
    else:
        checks.append(check(
            "scorecard_has_measurable_indicators",
            False,
            "Could not locate scorecard section in document"
        ))

    # ── SCORE CALCULATION ─────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = passed_count >= 8  # must pass at least 8 of 10 checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))