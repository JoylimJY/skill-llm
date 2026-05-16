import sys
import json
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text()), None
    except Exception as e:
        return None, str(e)

def find_report(workspace):
    candidates = list(Path(workspace).rglob("analysis_report.json"))
    return candidates[0] if candidates else None

def run_eval(workspace):
    checks = []

    # ── locate report ──────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if not report_path:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_exists", "passed": False, "detail": "analysis_report.json not found anywhere in workspace."}]
        }

    checks.append({"name": "report_exists", "passed": True, "detail": f"Found at {report_path}"})

    report, err = load_json_safe(report_path)
    if err:
        checks.append({"name": "report_parseable", "passed": False, "detail": f"JSON parse error: {err}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_parseable", "passed": True, "detail": "Valid JSON."})

    # ── must be a list or dict with a 'requests' or similar key ───────────
    if isinstance(report, dict):
        # accept {"requests": [...]} or {"analyses": [...]} or {"results": [...]}
        items = None
        for key in ("requests", "analyses", "results", "analysis", "items"):
            if key in report and isinstance(report[key], list):
                items = report[key]
                break
        if items is None:
            # try top-level dict keyed by REQ-XXX
            if any(k.startswith("REQ-") for k in report.keys()):
                items = list(report.values())
            else:
                checks.append({"name": "report_structure", "passed": False,
                                "detail": "Cannot locate list of per-request analyses. Expected a list or dict with 'requests'/'analyses'/'results' key."})
                return {"passed": False, "score": 0.0, "checks": checks}
    elif isinstance(report, list):
        items = report
    else:
        checks.append({"name": "report_structure", "passed": False, "detail": "Report root is neither list nor dict."})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_structure", "passed": True, "detail": f"Found {len(items)} analysis items."})

    # helper: find item for a request id
    def find_item(req_id):
        for item in items:
            if isinstance(item, dict):
                raw = json.dumps(item).upper()
                if req_id.upper() in raw:
                    return item
        return None

    def text_contains_any(text, *terms):
        t = text.lower()
        return any(term.lower() in t for term in terms)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP A: REQ-001 — Spec Gap
    # ════════════════════════════════════════════════════════════════════════
    item1 = find_item("REQ-001")
    if item1 is None:
        checks.append({"name": "req001_present", "passed": False, "detail": "No analysis found for REQ-001."})
    else:
        checks.append({"name": "req001_present", "passed": True, "detail": "REQ-001 analysis found."})
        blob1 = json.dumps(item1).lower()

        # Gap type: spec gap
        spec_gap_ok = text_contains_any(blob1, "spec gap", "specification gap", "spec_gap", "knows why", "unclear how")
        checks.append({
            "name": "req001_gap_type_spec",
            "passed": spec_gap_ok,
            "detail": "REQ-001 must be classified as a 'spec gap' (goal clear, task details vague)." + (" ✓" if spec_gap_ok else " ✗")
        })

        # Action: execute (not probe) — spec gap → infer, fill, execute
        exec_ok = text_contains_any(blob1, "execute", "infer", "proceed", "fill gaps", "action: execute", "do it", "go ahead")
        no_probe = not text_contains_any(blob1, "probe before acting", "do not execute", "don't execute", "hold")
        checks.append({
            "name": "req001_action_execute",
            "passed": exec_ok and no_probe,
            "detail": "REQ-001 spec gap → should recommend executing/inferring, not probing." + (" ✓" if (exec_ok and no_probe) else " ✗")
        })

        # Must cite at least 2 intention sources
        source_hits = sum([
            text_contains_any(blob1, "user profile", "user.md", "declared priorities", "declared goals"),
            text_contains_any(blob1, "active topic", "topic context", "current domain"),
            text_contains_any(blob1, "recent memory", "recent decision", "last 2", "last few days"),
            text_contains_any(blob1, "project state", "project/task", "task state", "in progress", "blocked"),
            text_contains_any(blob1, "conversational momentum", "momentum", "circling around"),
        ])
        checks.append({
            "name": "req001_two_sources",
            "passed": source_hits >= 2,
            "detail": f"REQ-001 must cite at least 2 intention sources. Found signals for {source_hits} source(s)." + (" ✓" if source_hits >= 2 else " ✗")
        })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP B: REQ-002 — Intention Gap + Premortem (irreversible)
    # ════════════════════════════════════════════════════════════════════════
    item2 = find_item("REQ-002")
    if item2 is None:
        checks.append({"name": "req002_present", "passed": False, "detail": "No analysis found for REQ-002."})
    else:
        checks.append({"name": "req002_present", "passed": True, "detail": "REQ-002 analysis found."})
        blob2 = json.dumps(item2).lower()

        # Gap type: intention gap
        int_gap_ok = text_contains_any(blob2, "intention gap", "intent gap", "knows what", "unclear why", "purpose unknown", "why unclear")
        checks.append({
            "name": "req002_gap_type_intention",
            "passed": int_gap_ok,
            "detail": "REQ-002 must be classified as an 'intention gap' (precise task, purpose unknown)." + (" ✓" if int_gap_ok else " ✗")
        })

        # Action: execute but flag (intention gap → execute if cheap/reversible, but this is irreversible — so flag)
        flag_ok = text_contains_any(blob2, "flag", "unresolved", "surface why", "surface 'why'", "ask why", "clarify purpose", "flag as unresolved")
        checks.append({
            "name": "req002_flag_unresolved",
            "passed": flag_ok,
            "detail": "REQ-002 intention gap must be flagged as unresolved and 'why' surfaced." + (" ✓" if flag_ok else " ✗")
        })

        # Premortem: mandatory because action is irreversible/expensive
        premortem_ok = text_contains_any(blob2, "premortem", "pre-mortem", "most likely way this fails", "what's the most likely", "most likely failure")
        checks.append({
            "name": "req002_premortem",
            "passed": premortem_ok,
            "detail": "REQ-002 is irreversible — a one-sentence premortem is mandatory." + (" ✓" if premortem_ok else " ✗")
        })

        # Negative intent check
        neg_ok = text_contains_any(blob2, "bad version of success", "negative intent", "klarna", "unstated constraint", "optimizing for stated metric", "bad success")
        checks.append({
            "name": "req002_negative_intent",
            "passed": neg_ok,
            "detail": "REQ-002 must include a negative intent check ('bad version of success')." + (" ✓" if neg_ok else " ✗")
        })

        # At least 2 sources cross-referenced
        source_hits2 = sum([
            text_contains_any(blob2, "user profile", "user.md", "declared priorities", "declared goals"),
            text_contains_any(blob2, "active topic", "topic context"),
            text_contains_any(blob2, "recent memory", "recent decision"),
            text_contains_any(blob2, "project state", "task state", "in progress"),
            text_contains_any(blob2, "conversational momentum", "momentum"),
        ])
        checks.append({
            "name": "req002_two_sources",
            "passed": source_hits2 >= 2,
            "detail": f"REQ-002 must cross-reference at least 2 intention sources. Found {source_hits2}." + (" ✓" if source_hits2 >= 2 else " ✗")
        })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP C: REQ-003 — Both Unclear → PROBE, do NOT execute/guess
    # ════════════════════════════════════════════════════════════════════════
    item3 = find_item("REQ-003")
    if item3 is None:
        checks.append({"name": "req003_present", "passed": False, "detail": "No analysis found for REQ-003."})
    else:
        checks.append({"name": "req003_present", "passed": True, "detail": "REQ-003 analysis found."})
        blob3 = json.dumps(item3).lower()

        # Gap type: both unclear
        both_unclear_ok = text_contains_any(blob3, "both unclear", "vague", "both gaps", "goal unclear", "task unclear", "neither clear", "both unclear")
        checks.append({
            "name": "req003_gap_type_both_unclear",
            "passed": both_unclear_ok,
            "detail": "REQ-003 must be classified as 'both unclear' (vague goal AND vague task)." + (" ✓" if both_unclear_ok else " ✗")
        })

        # Action: MUST probe before acting — do NOT guess
        probe_ok = text_contains_any(blob3, "probe", "ask before", "clarify before", "do not execute", "don't execute", "probe before acting", "clarify first", "must ask")
        no_guess_ok = not text_contains_any(blob3, "execute anyway", "proceed anyway", "go ahead and execute", "guess and execute")
        checks.append({
            "name": "req003_action_probe",
            "passed": probe_ok and no_guess_ok,
            "detail": "REQ-003 both-unclear → must say 'probe before acting, do NOT guess'. " + (" ✓" if (probe_ok and no_guess_ok) else " ✗")
        })

        # Must NOT say "just execute"
        no_execute_ok = not text_contains_any(blob3, "action: execute", "just execute", "proceed to execute")
        checks.append({
            "name": "req003_no_blind_execute",
            "passed": no_execute_ok,
            "detail": "REQ-003 must NOT recommend blind execution." + (" ✓" if no_execute_ok else " ✗")
        })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP D: REQ-004 — Both Clear BUT stale intention (35 days)
    # ════════════════════════════════════════════════════════════════════════
    item4 = find_item("REQ-004")
    if item4 is None:
        checks.append({"name": "req004_present", "passed": False, "detail": "No analysis found for REQ-004."})
    else:
        checks.append({"name": "req004_present", "passed": True, "detail": "REQ-004 analysis found."})
        blob4 = json.dumps(item4).lower()

        # Gap type: both clear (goal and task aligned)
        both_clear_ok = text_contains_any(blob4, "both clear", "goal and task aligned", "aligned", "clear goal", "clear task", "no gap")
        checks.append({
            "name": "req004_gap_type_both_clear",
            "passed": both_clear_ok,
            "detail": "REQ-004 must be classified as 'both clear' (goal and task are aligned)." + (" ✓" if both_clear_ok else " ✗")
        })

        # Stale intention: 30-day rule triggered — must flag for re-validation
        stale_ok = text_contains_any(blob4, "stale", "30 day", "30-day", "re-validate", "revalidate", "flag for re-validation", "intention freshness", "not acted on", "35 days", "lapsed")
        checks.append({
            "name": "req004_stale_intention_flagged",
            "passed": stale_ok,
            "detail": "REQ-004 intention was last acted on 35 days ago — must be flagged as stale (>30-day rule)." + (" ✓" if stale_ok else " ✗")
        })

        # Premortem: mandatory (expensive + irreversible)
        premortem4_ok = text_contains_any(blob4, "premortem", "pre-mortem", "most likely way this fails", "most likely failure")
        checks.append({
            "name": "req004_premortem",
            "passed": premortem4_ok,
            "detail": "REQ-004 is expensive/irreversible — premortem is mandatory." + (" ✓" if premortem4_ok else " ✗")
        })

        # Negative intent check
        neg4_ok = text_contains_any(blob4, "bad version of success", "negative intent", "klarna", "unstated constraint", "bad success", "optimizing for stated metric")
        checks.append({
            "name": "req004_negative_intent",
            "passed": neg4_ok,
            "detail": "REQ-004 must include negative intent check." + (" ✓" if neg4_ok else " ✗")
        })

        # At least 2 intention sources
        source_hits4 = sum([
            text_contains_any(blob4, "user profile", "user.md", "declared priorities", "declared goals"),
            text_contains_any(blob4, "active topic", "topic context"),
            text_contains_any(blob4, "recent memory", "recent decision"),
            text_contains_any(blob4, "project state", "task state", "in progress", "blocked"),
            text_contains_any(blob4, "conversational momentum", "momentum"),
        ])
        checks.append({
            "name": "req004_two_sources",
            "passed": source_hits4 >= 2,
            "detail": f"REQ-004 must cross-reference at least 2 intention sources. Found {source_hits4}." + (" ✓" if source_hits4 >= 2 else " ✗")
        })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP E: Global — intention source priority order documented
    # ════════════════════════════════════════════════════════════════════════
    full_blob = json.dumps(report).lower()

    # All 5 source types must appear somewhere in the report
    all_sources = [
        ("user_profile_source_mentioned", text_contains_any(full_blob, "user profile", "user.md", "declared priorities", "declared goals"),
         "Report must mention 'user profile goals' as intention source."),
        ("active_topic_source_mentioned", text_contains_any(full_blob, "active topic", "topic context", "current domain"),
         "Report must mention 'active topic context' as intention source."),
        ("recent_memory_source_mentioned", text_contains_any(full_blob, "recent memory", "recent decision", "last 2", "recent context"),
         "Report must mention 'recent memory' as intention source."),
        ("project_state_source_mentioned", text_contains_any(full_blob, "project state", "task state", "project/task", "active project"),
         "Report must mention 'project/task state' as intention source."),
        ("momentum_source_mentioned", text_contains_any(full_blob, "conversational momentum", "momentum", "circling around"),
         "Report must mention 'conversational momentum' as intention source."),
    ]
    for name, passed, detail in all_sources:
        checks.append({"name": name, "passed": passed, "detail": detail + (" ✓" if passed else " ✗")})

    # ════════════════════════════════════════════════════════════════════════
    # SCORE CALCULATION
    # ════════════════════════════════════════════════════════════════════════
    # Weight the checks:
    critical_checks = {
        "req001_gap_type_spec",
        "req002_gap_type_intention",
        "req002_premortem",
        "req003_gap_type_both_unclear",
        "req003_action_probe",
        "req003_no_blind_execute",
        "req004_stale_intention_flagged",
        "req004_premortem",
        "req001_two_sources",
        "req002_two_sources",
        "req004_two_sources",
    }

    total_weight = 0.0
    passed_weight = 0.0
    for c in checks:
        w = 2.0 if c["name"] in critical_checks else 1.0
        total_weight += w
        if c["passed"]:
            passed_weight += w

    score = round(passed_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass all critical checks to overall pass
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall = score >= 0.75 and critical_passed

    return {"passed": overall, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))