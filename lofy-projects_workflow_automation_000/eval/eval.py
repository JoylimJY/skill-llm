import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    # Reference time
    REF_NOW = datetime(2025, 6, 15, 10, 0, 0)

    # =========================================================
    # SECTION 1: Verify projects.json was updated correctly
    # =========================================================
    projects_path = workspace / "data" / "projects.json"
    projects_data, err = load_json_safe(projects_path)

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    if projects_data is None:
        add_check("projects_json_readable", False, f"Could not read projects.json: {err}", weight=2.0)
    else:
        add_check("projects_json_readable", True, "projects.json is valid JSON", weight=2.0)

        projects = projects_data.get("projects", {})

        # --- Check 1a: nova_inference time_log updated (2h + 0.5h on June 15) ---
        nova = projects.get("nova_inference", {})
        nova_tl = nova.get("time_log", [])
        nova_june15_entries = [e for e in nova_tl if "2025-06-15" in str(e.get("date", ""))]
        nova_june15_hours = sum(float(e.get("hours", 0)) for e in nova_june15_entries)
        # Agent should add ~2.5 hours total on June 15 (2h debugging + 0.5h reviewing)
        passed_nova_tl = nova_june15_hours >= 2.0
        add_check(
            "nova_inference_timelog_june15",
            passed_nova_tl,
            f"nova_inference June 15 time log hours: {nova_june15_hours} (expected >= 2.0 from activity notes)",
            weight=1.5
        )

        # --- Check 1b: nova_inference blocker resolved ---
        nova_blockers = nova.get("blockers", [])
        # The Redis bug was fixed — blocker should be removed or marked resolved
        redis_blocker_present = any("redis" in str(b).lower() and "fix" not in str(b).lower() and "resolv" not in str(b).lower() for b in nova_blockers)
        # More permissive: check if the old exact blocker string still exists unchanged
        old_blocker = "Redis connection pooling causing memory spikes under load"
        old_blocker_unchanged = old_blocker in nova_blockers
        passed_blocker = not old_blocker_unchanged
        add_check(
            "nova_inference_blocker_resolved",
            passed_blocker,
            f"Redis blocker should be removed/updated (fixed per activity notes). Blockers now: {nova_blockers}",
            weight=1.5
        )

        # --- Check 1c: nova_inference last_updated set to 2025-06-15 ---
        nova_last = nova.get("last_updated", "")
        passed_nova_lu = "2025-06-15" in str(nova_last)
        add_check(
            "nova_inference_last_updated",
            passed_nova_lu,
            f"nova_inference last_updated should be 2025-06-15, got: {nova_last}",
            weight=1.0
        )

        # --- Check 1d: job_portfolio time_log updated for June 14 (1.5h) ---
        portfolio = projects.get("job_portfolio", {})
        port_tl = portfolio.get("time_log", [])
        port_june14 = [e for e in port_tl if "2025-06-14" in str(e.get("date", ""))]
        port_june14_hours = sum(float(e.get("hours", 0)) for e in port_june14)
        # The original already has a June 14 entry with 2h; agent may add 1.5h or update
        # Accept if total June 14 hours >= 1.5 (could merge or add)
        passed_port_tl = port_june14_hours >= 1.5
        add_check(
            "job_portfolio_timelog_june14",
            passed_port_tl,
            f"job_portfolio June 14 hours: {port_june14_hours} (expected >= 1.5 from activity notes)",
            weight=1.5
        )

        # --- Check 1e: job_portfolio 'Project case studies written' milestone marked completed ---
        port_milestones = portfolio.get("milestones", [])
        case_study_ms = next(
            (m for m in port_milestones if "case stud" in m.get("name", "").lower()),
            None
        )
        if case_study_ms:
            passed_ms = case_study_ms.get("status", "").lower() in ("completed", "done", "complete")
            add_check(
                "job_portfolio_casestudy_milestone_completed",
                passed_ms,
                f"'Project case studies written' milestone status: {case_study_ms.get('status')} (expected completed)",
                weight=2.0
            )
        else:
            add_check(
                "job_portfolio_casestudy_milestone_completed",
                False,
                "Could not find 'Project case studies written' milestone in job_portfolio",
                weight=2.0
            )

    # =========================================================
    # SECTION 2: Verify priority_report.json exists and is correct
    # =========================================================
    # Find priority_report.json anywhere in workspace
    report_files = list(workspace.rglob("priority_report.json"))
    if not report_files:
        add_check("priority_report_exists", False, "priority_report.json not found anywhere in workspace", weight=2.0)
        # Skip all downstream checks
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {
            "passed": all(c["passed"] for c in checks),
            "score": round(final_score, 3),
            "checks": checks
        }

    report_path = report_files[0]
    add_check("priority_report_exists", True, f"Found priority_report.json at {report_path}", weight=2.0)

    report_data, err = load_json_safe(report_path)
    if report_data is None:
        add_check("priority_report_readable", False, f"Could not parse priority_report.json: {err}", weight=2.0)
    else:
        add_check("priority_report_readable", True, "priority_report.json is valid JSON", weight=1.0)

        # ---- Expected Priority Scores ----
        # Using REF_NOW = 2025-06-15
        #
        # job_portfolio:
        #   Urgency: deadline 2025-06-18 = 3 days away = "this week" = 3
        #   Job_Relevance: "critical" = 5
        #   Momentum: last_updated 2025-06-14 = 1 day ago = "touched last 3 days" = 2
        #   Energy_Match: 90 min available → "1-2 hours focused" → job_portfolio next action is writing/content → matches = 2
        #   Score = (3×3) + (5×2) + (2×1) + (2×1) = 9 + 10 + 2 + 2 = 23
        #
        # nova_inference:
        #   Urgency: deadline 2025-06-16 = 1 day away = "48h" = 4
        #   Job_Relevance: "high" = 4
        #   Momentum: last_updated 2025-06-15 (after update) = "active/today" = 3 (or 2 if not updated yet)
        #   Energy_Match: 90 min → "1-2 hours" → implement/debug → matches = 2
        #   Score (with momentum=3) = (4×3) + (4×2) + (3×1) + (2×1) = 12 + 8 + 3 + 2 = 25
        #   Score (with momentum=2) = 12 + 8 + 2 + 2 = 24
        #
        # acme_dashboard:
        #   Urgency: deadline 2025-06-20 = 5 days = "this week" = 3
        #   Job_Relevance: "medium" = 3
        #   Momentum: last_updated 2025-06-05 = 10 days ago = "stale 1-2 weeks" = 1
        #   Energy_Match: 90 min → medium task → 1
        #   Score = (3×3) + (3×2) + (1×1) + (1×1) = 9 + 6 + 1 + 1 = 17
        #
        # research_paper:
        #   Urgency: no deadline = 1
        #   Job_Relevance: "high" = 4
        #   Momentum: last_updated 2025-05-26 = 20 days ago = "cold 2+ weeks" = 0
        #   Energy_Match: 90 min → writing → 1
        #   Score = (1×3) + (4×2) + (0×1) + (1×1) = 3 + 8 + 0 + 1 = 12
        #
        # stealth_mvp:
        #   Urgency: backlog = 0
        #   Job_Relevance: "none" = 0
        #   Momentum: 30 days ago = 0
        #   Energy_Match: 0
        #   Score = 0

        # Expected ranking: nova_inference (24-25) > job_portfolio (23) > acme_dashboard (17) > research_paper (12) > stealth_mvp (0)
        # BUT: SKILL.md says "Prioritize job-critical projects unless there's a deadline override"
        # nova_inference has a deadline override (due tomorrow), so nova_inference should be #1
        # job_portfolio is job-critical AND has a near deadline too

        # We check:
        # 1. nova_inference has highest or joint-highest score (24 or 25)
        # 2. job_portfolio is second
        # 3. Top recommendation is nova_inference or job_portfolio (both defensible given deadline proximity)
        # 4. stealth_mvp has score 0
        # 5. Stale projects flagged

        # --- Check scores are present ---
        scores_section = None
        # Look for scores in various possible structures
        possible_keys = ["scores", "priority_scores", "projects", "ranked_projects", "ranking"]
        for k in possible_keys:
            if k in report_data:
                scores_section = report_data[k]
                break
        if scores_section is None and isinstance(report_data, dict):
            # Try top-level keys that might be project names
            if "nova_inference" in report_data or "job_portfolio" in report_data:
                scores_section = report_data

        # --- Check nova_inference score ---
        nova_score_raw = None
        if isinstance(scores_section, dict):
            for proj_key in ["nova_inference", "Nova Labs Inference Pipeline"]:
                if proj_key in scores_section:
                    entry = scores_section[proj_key]
                    if isinstance(entry, dict):
                        nova_score_raw = entry.get("score") or entry.get("priority") or entry.get("total")
                    elif isinstance(entry, (int, float)):
                        nova_score_raw = entry
                    break
        elif isinstance(scores_section, list):
            for item in scores_section:
                if isinstance(item, dict):
                    name = item.get("project", "") or item.get("name", "") or item.get("id", "")
                    if "nova" in str(name).lower():
                        nova_score_raw = item.get("score") or item.get("priority") or item.get("total")
                        break

        try:
            nova_score = float(nova_score_raw)
            # Accept 24 or 25 depending on whether momentum was updated before scoring
            passed_nova_score = 23.0 <= nova_score <= 26.0
            add_check(
                "nova_inference_priority_score",
                passed_nova_score,
                f"nova_inference priority score: {nova_score} (expected 23-26 using weighted formula)",
                weight=2.0
            )
        except (TypeError, ValueError):
            add_check(
                "nova_inference_priority_score",
                False,
                f"Could not extract numeric nova_inference score from report. Raw: {nova_score_raw}",
                weight=2.0
            )

        # --- Check job_portfolio score ---
        port_score_raw = None
        if isinstance(scores_section, dict):
            for proj_key in ["job_portfolio", "ML Engineer Portfolio Site"]:
                if proj_key in scores_section:
                    entry = scores_section[proj_key]
                    if isinstance(entry, dict):
                        port_score_raw = entry.get("score") or entry.get("priority") or entry.get("total")
                    elif isinstance(entry, (int, float)):
                        port_score_raw = entry
                    break
        elif isinstance(scores_section, list):
            for item in scores_section:
                if isinstance(item, dict):
                    name = item.get("project", "") or item.get("name", "") or item.get("id", "")
                    if "portfolio" in str(name).lower() or "job_portfolio" in str(name).lower():
                        port_score_raw = item.get("score") or item.get("priority") or item.get("total")
                        break

        try:
            port_score = float(port_score_raw)
            passed_port_score = 21.0 <= port_score <= 25.0
            add_check(
                "job_portfolio_priority_score",
                passed_port_score,
                f"job_portfolio priority score: {port_score} (expected 21-25 using weighted formula)",
                weight=2.0
            )
        except (TypeError, ValueError):
            add_check(
                "job_portfolio_priority_score",
                False,
                f"Could not extract numeric job_portfolio score. Raw: {port_score_raw}",
                weight=2.0
            )

        # --- Check stealth_mvp score is 0 ---
        stealth_score_raw = None
        if isinstance(scores_section, dict):
            for proj_key in ["stealth_mvp", "Stealth Startup MVP Prototype"]:
                if proj_key in scores_section:
                    entry = scores_section[proj_key]
                    if isinstance(entry, dict):
                        stealth_score_raw = entry.get("score") or entry.get("priority") or entry.get("total")
                    elif isinstance(entry, (int, float)):
                        stealth_score_raw = entry
                    break
        elif isinstance(scores_section, list):
            for item in scores_section:
                if isinstance(item, dict):
                    name = item.get("project", "") or item.get("name", "") or item.get("id", "")
                    if "stealth" in str(name).lower():
                        stealth_score_raw = item.get("score") or item.get("priority") or item.get("total")
                        break

        try:
            stealth_score = float(stealth_score_raw) if stealth_score_raw is not None else None
            passed_stealth = stealth_score is not None and stealth_score == 0.0
            add_check(
                "stealth_mvp_score_zero",
                passed_stealth,
                f"stealth_mvp score should be 0 (backlog, no relevance, cold). Got: {stealth_score}",
                weight=1.5
            )
        except (TypeError, ValueError):
            add_check(
                "stealth_mvp_score_zero",
                False,
                f"Could not extract stealth_mvp score. Raw: {stealth_score_raw}",
                weight=1.5
            )

        # --- Check top recommendation is nova_inference or job_portfolio ---
        top_rec = None
        for k in ["top_recommendation", "recommendation", "primary", "top_pick", "first_recommendation", "suggested_project"]:
            if k in report_data:
                top_rec = str(report_data[k]).lower()
                break
        # Also check in a ranked list
        if top_rec is None and isinstance(scores_section, list) and scores_section:
            first = scores_section[0]
            if isinstance(first, dict):
                name = first.get("project", "") or first.get("name", "") or first.get("id", "")
                top_rec = str(name).lower()

        if top_rec:
            passed_top = "nova" in top_rec or "portfolio" in top_rec or "inference" in top_rec
            add_check(
                "top_recommendation_correct",
                passed_top,
                f"Top recommendation: '{top_rec}' (expected nova_inference or job_portfolio as highest priority)",
                weight=2.0
            )
        else:
            add_check(
                "top_recommendation_correct",
                False,
                "Could not find a top_recommendation field in priority_report.json",
                weight=2.0
            )

        # --- Check alternative recommendation is present ---
        alt_rec = None
        for k in ["alternative", "second_recommendation", "alt_recommendation", "secondary", "alternative_project"]:
            if k in report_data:
                alt_rec = str(report_data[k]).lower()
                break
        passed_alt = alt_rec is not None and len(alt_rec) > 0
        add_check(
            "alternative_recommendation_present",
            passed_alt,
            f"Alternative recommendation: '{alt_rec}'",
            weight=1.0
        )

        # --- Check stale projects flagged ---
        stale_section = None
        for k in ["stale_projects", "stale_flags", "flagged_stale", "stale", "alerts"]:
            if k in report_data:
                stale_section = report_data[k]
                break

        if stale_section is not None:
            stale_str = json.dumps(stale_section).lower()
            # research_paper (20 days stale) and stealth_mvp (30 days) should be flagged
            research_flagged = "research" in stale_str or "lora" in stale_str or "paper" in stale_str
            stealth_flagged = "stealth" in stale_str or "mvp" in stale_str
            passed_stale_research = research_flagged
            passed_stale_stealth = stealth_flagged
            add_check(
                "stale_research_paper_flagged",
                passed_stale_research,
                f"research_paper (20 days stale) should appear in stale_projects. stale section: {stale_str[:200]}",
                weight=1.5
            )
            add_check(
                "stale_stealth_mvp_flagged",
                passed_stale_stealth,
                f"stealth_mvp (30 days stale) should appear in stale_projects. stale section: {stale_str[:200]}",
                weight=1.5
            )
        else:
            # Check if stale info is embedded somewhere in report
            report_str = json.dumps(report_data).lower()
            research_in_report = "research" in report_str and ("stale" in report_str or "days" in report_str)
            add_check(
                "stale_research_paper_flagged",
                research_in_report,
                f"Could not find dedicated stale_projects section; research stale mention: {research_in_report}",
                weight=1.5
            )
            add_check(
                "stale_stealth_mvp_flagged",
                False,
                "No stale_projects section found in priority_report.json",
                weight=1.5
            )

        # --- Check work session time recommendation is present and matches 90min → "1-2 hours" ---
        time_rec = None
        for k in ["time_recommendation", "session_type", "work_session", "session_recommendation", "time_category"]:
            if k in report_data:
                time_rec = str(report_data[k]).lower()
                break
        if time_rec is None:
            report_str = json.dumps(report_data).lower()
            if "1-2 hour" in report_str or "focused" in report_str or "90 min" in report_str or "implement" in report_str:
                time_rec = "found_in_body"
        passed_time = time_rec is not None and (
            "1-2" in str(time_rec) or "focused" in str(time_rec) or "hour" in str(time_rec)
        )
        add_check(
            "time_based_session_recommendation",
            passed_time,
            f"90 min available should map to '1-2 hours: Focused' category. Found: {time_rec}",
            weight=1.5
        )

    # =========================================================
    # Final scoring
    # =========================================================
    final_score = total_score / max_score if max_score > 0 else 0.0
    # Passed if score >= 0.75
    overall_passed = final_score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))