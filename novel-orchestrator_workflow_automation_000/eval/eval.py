import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_output_file(workspace):
    """Search for workflow_spec.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("workflow_spec.json"))
    # Exclude the draft file
    candidates = [c for c in candidates if "DRAFT" not in c.name]
    if not candidates:
        return None
    # Prefer root-level
    for c in candidates:
        if c.parent == Path(workspace):
            return c
    return candidates[0]

def evaluate(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # --- Find the output file ---
    spec_path = find_output_file(workspace)
    if spec_path is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "workflow_spec.json not found in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        spec = load_json_file(spec_path)
    except Exception as e:
        checks.append({"name": "output_file_parseable", "passed": False, "detail": f"Failed to parse workflow_spec.json: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists_and_parseable", "passed": True, "detail": f"Found at {spec_path}"})

    # ============================================================
    # CHECK 1: Revision Policy - max_revisions_per_chapter = 2
    # ============================================================
    max_score += 1.0
    try:
        rp = spec.get("revision_policy", {})
        max_rev = rp.get("max_revisions_per_chapter", rp.get("max_revisions", None))
        passed = (max_rev == 2)
        checks.append({
            "name": "revision_policy_max_revisions_per_chapter_is_2",
            "passed": passed,
            "detail": f"max_revisions_per_chapter = {max_rev} (expected 2). SKILL.md: writer最多进行2次返修"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "revision_policy_max_revisions_per_chapter_is_2", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 2: Revision Policy - max_total_writes = 3 (initial + 2 revisions)
    # ============================================================
    max_score += 1.0
    try:
        rp = spec.get("revision_policy", {})
        max_writes = rp.get("max_total_writes", None)
        passed = (max_writes == 3)
        checks.append({
            "name": "revision_policy_max_total_writes_is_3",
            "passed": passed,
            "detail": f"max_total_writes = {max_writes} (expected 3). SKILL.md: 连同初稿在内，单章最多写3次"
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "revision_policy_max_total_writes_is_3", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 3: Escalation - after 2 failed revisions, checker outputs report + user intervention
    # ============================================================
    max_score += 1.0
    try:
        rp = spec.get("revision_policy", {})
        # Accept various key names
        escalation = rp.get("on_max_revisions_exceeded",
                    rp.get("escalation_action",
                    rp.get("escalation",
                    rp.get("on_exceeded", None))))
        escalation_str = str(escalation).lower() if escalation else ""
        # Must mention checker output AND user intervention (not reassign to planner, not continue loop)
        passed = (
            escalation is not None and
            ("user" in escalation_str or "用户" in escalation_str) and
            ("checker" in escalation_str or "审查报告" in escalation_str or "report" in escalation_str) and
            "planner" not in escalation_str and
            "continue" not in escalation_str and
            "writer" not in escalation_str
        )
        checks.append({
            "name": "escalation_action_user_intervention_with_checker_report",
            "passed": passed,
            "detail": f"escalation value: {escalation}. Must mention checker report + user intervention, not reassign to planner or continue loop."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "escalation_action_user_intervention_with_checker_report", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 4: Word Count - Python script, include symbols
    # ============================================================
    max_score += 1.0
    try:
        wc = spec.get("word_count_spec", spec.get("word_count", {}))
        method_str = str(wc.get("method", wc.get("tool", ""))).lower()
        include_symbols = wc.get("include_symbols", wc.get("includes_symbols", None))
        method_ok = "python" in method_str or "script" in method_str
        symbols_ok = include_symbols is True
        passed = method_ok and symbols_ok
        checks.append({
            "name": "word_count_python_script_with_symbols",
            "passed": passed,
            "detail": f"method='{wc.get('method', wc.get('tool',''))}', include_symbols={include_symbols}. Must be Python script and include symbols=True."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "word_count_python_script_with_symbols", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 5: T01 routing - vague idea → deliverable chapter = planner→writer→checker
    # ============================================================
    max_score += 1.5
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t01 = routing.get("T01", routing.get("t01", None))
        if t01 is None:
            raise ValueError("T01 not found in routing_decisions")
        pipeline = t01.get("pipeline", t01.get("roles", t01.get("flow", [])))
        pipeline_lower = [str(r).lower() for r in pipeline]

        # Must have planner, writer, checker in order (forced upgrade - vague idea → deliverable)
        has_planner = any("planner" in r for r in pipeline_lower)
        has_writer = any("writer" in r for r in pipeline_lower)
        has_checker = any("checker" in r for r in pipeline_lower)

        # planner must come before writer, writer before checker
        try:
            pi = next(i for i, r in enumerate(pipeline_lower) if "planner" in r)
            wi = next(i for i, r in enumerate(pipeline_lower) if "writer" in r)
            ci = next(i for i, r in enumerate(pipeline_lower) if "checker" in r)
            order_ok = pi < wi < ci
        except StopIteration:
            order_ok = False

        passed = has_planner and has_writer and has_checker and order_ok
        checks.append({
            "name": "T01_routing_planner_writer_checker_pipeline",
            "passed": passed,
            "detail": f"T01 pipeline: {pipeline}. Expected planner→writer→checker (forced upgrade: vague idea → deliverable)."
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "T01_routing_planner_writer_checker_pipeline", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 6: T02 routing - volume planning → planner (direct route)
    # ============================================================
    max_score += 1.0
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t02 = routing.get("T02", routing.get("t02", None))
        if t02 is None:
            raise ValueError("T02 not found")
        pipeline = t02.get("pipeline", t02.get("roles", t02.get("flow", t02.get("role", []))))
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        pipeline_lower = [str(r).lower() for r in pipeline]
        # Should route to planner (direct), may include planner as sole or primary role
        # Must NOT include writer or checker as primary roles
        has_planner = any("planner" in r for r in pipeline_lower)
        no_writer_primary = not any("writer" in r for r in pipeline_lower)
        no_checker_primary = not any("checker" in r for r in pipeline_lower)
        passed = has_planner and no_writer_primary and no_checker_primary
        checks.append({
            "name": "T02_routing_planner_direct",
            "passed": passed,
            "detail": f"T02 pipeline: {pipeline}. Expected direct route to planner only (volume planning task)."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "T02_routing_planner_direct", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 7: T03 routing - review existing draft → checker (direct route)
    # ============================================================
    max_score += 1.0
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t03 = routing.get("T03", routing.get("t03", None))
        if t03 is None:
            raise ValueError("T03 not found")
        pipeline = t03.get("pipeline", t03.get("roles", t03.get("flow", t03.get("role", []))))
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        pipeline_lower = [str(r).lower() for r in pipeline]
        has_checker = any("checker" in r for r in pipeline_lower)
        no_planner = not any("planner" in r for r in pipeline_lower)
        # writer may appear in revision loop but checker must be primary/first
        passed = has_checker and no_planner
        checks.append({
            "name": "T03_routing_checker_direct",
            "passed": passed,
            "detail": f"T03 pipeline: {pipeline}. Expected direct route to checker (review existing draft)."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "T03_routing_checker_direct", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 8: T04 routing - multi-chapter deliverable → collaboration pipeline (forced upgrade)
    # Must include writer + checker loop; may include manager or planner; 
    # Key: it's a forced upgrade (多章连续产出 + 可发布成品)
    # ============================================================
    max_score += 1.5
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t04 = routing.get("T04", routing.get("t04", None))
        if t04 is None:
            raise ValueError("T04 not found")
        pipeline = t04.get("pipeline", t04.get("roles", t04.get("flow", [])))
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        pipeline_lower = [str(r).lower() for r in pipeline]
        pipeline_str = " ".join(pipeline_lower)

        # Must be a collaboration pipeline (not single role)
        # Must include writer and checker
        has_writer = any("writer" in r for r in pipeline_lower)
        has_checker = any("checker" in r for r in pipeline_lower)
        is_multi = len([r for r in pipeline_lower if r.strip()]) > 1

        # Forced upgrade flag
        is_forced_upgrade = t04.get("forced_upgrade", t04.get("collaboration", t04.get("upgrade", None)))
        # Accept if the pipeline itself encodes the upgrade (has multiple roles) OR explicit flag
        forced_ok = (is_forced_upgrade is True) or (is_multi and has_writer and has_checker)

        passed = has_writer and has_checker and forced_ok
        checks.append({
            "name": "T04_routing_forced_upgrade_multi_chapter_pipeline",
            "passed": passed,
            "detail": f"T04 pipeline: {pipeline}, forced_upgrade={is_forced_upgrade}. Must be collaboration pipeline with writer+checker (多章连续 + 可发布)."
        })
        if passed:
            total_score += 1.5
    except Exception as e:
        checks.append({"name": "T04_routing_forced_upgrade_multi_chapter_pipeline", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 9: T05 routing - failed review, needs revision → writer (then checker)
    # checker→writer→checker pattern
    # ============================================================
    max_score += 1.0
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t05 = routing.get("T05", routing.get("t05", None))
        if t05 is None:
            raise ValueError("T05 not found")
        pipeline = t05.get("pipeline", t05.get("roles", t05.get("flow", t05.get("role", []))))
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        pipeline_lower = [str(r).lower() for r in pipeline]
        # Must route to writer (revision), and checker should follow
        # writer must appear; planner must NOT be primary
        has_writer = any("writer" in r for r in pipeline_lower)
        no_planner_primary = not (len(pipeline_lower) > 0 and "planner" in pipeline_lower[0])
        passed = has_writer and no_planner_primary
        checks.append({
            "name": "T05_routing_writer_revision_then_checker",
            "passed": passed,
            "detail": f"T05 pipeline: {pipeline}. Expected writer (revision) → checker re-review. Not planner."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "T05_routing_writer_revision_then_checker", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 10: T06 routing - clear chapter write task → writer direct route
    # (direction already clear → no planner needed)
    # ============================================================
    max_score += 1.0
    try:
        routing = spec.get("routing_decisions", spec.get("task_routing", {}))
        t06 = routing.get("T06", routing.get("t06", None))
        if t06 is None:
            raise ValueError("T06 not found")
        pipeline = t06.get("pipeline", t06.get("roles", t06.get("flow", t06.get("role", []))))
        if isinstance(pipeline, str):
            pipeline = [pipeline]
        pipeline_lower = [str(r).lower() for r in pipeline]
        # Should go writer (direct), possibly writer→checker but NOT planner
        has_writer = any("writer" in r for r in pipeline_lower)
        no_planner = not any("planner" in r for r in pipeline_lower)
        passed = has_writer and no_planner
        checks.append({
            "name": "T06_routing_writer_direct_no_planner",
            "passed": passed,
            "detail": f"T06 pipeline: {pipeline}. Expected direct writer route, no planner (direction already clear)."
        })
        if passed:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "T06_routing_writer_direct_no_planner", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 11: checker cannot self-edit (writer_self_review_scope)
    # ============================================================
    max_score += 0.5
    try:
        # Look for a field that defines what writer can self-review
        writer_policy = spec.get("writer_policy", spec.get("writer_rules", {}))
        self_review = writer_policy.get("self_review_scope",
                      writer_policy.get("self_review",
                      writer_policy.get("allowed_self_review", None)))
        self_review_str = str(self_review).lower() if self_review else ""
        # Must only allow word count self-review
        passed = self_review is not None and (
            "word" in self_review_str or "字数" in self_review_str or "count" in self_review_str
        ) and (
            "quality" not in self_review_str and "质量" not in self_review_str
        )
        checks.append({
            "name": "writer_self_review_limited_to_word_count_only",
            "passed": passed,
            "detail": f"writer self_review_scope: {self_review}. Must be limited to word count only, not quality/other dims."
        })
        if passed:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "writer_self_review_limited_to_word_count_only", "passed": False, "detail": str(e)})

    # ============================================================
    # CHECK 12: checker cannot directly rewrite (checker_cannot_rewrite)
    # ============================================================
    max_score += 0.5
    try:
        checker_policy = spec.get("checker_policy", spec.get("checker_rules", {}))
        can_rewrite = checker_policy.get("can_rewrite",
                      checker_policy.get("direct_rewrite",
                      checker_policy.get("rewrite_allowed", None)))
        # Can be False, "false", "no", "不可", "不负责改稿"
        can_rewrite_str = str(can_rewrite).lower() if can_rewrite is not None else ""
        passed = can_rewrite is not None and (
            can_rewrite is False or
            "false" in can_rewrite_str or
            "no" in can_rewrite_str or
            "不" in can_rewrite_str or
            "cannot" in can_rewrite_str or
            "not" in can_rewrite_str
        )
        checks.append({
            "name": "checker_cannot_directly_rewrite",
            "passed": passed,
            "detail": f"checker can_rewrite: {can_rewrite}. Must be False/no. Checker cannot directly rewrite drafts."
        })
        if passed:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "checker_cannot_directly_rewrite", "passed": False, "detail": str(e)})

    # ============================================================
    # FINAL SCORING
    # ============================================================
    final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    critical_checks = [
        "revision_policy_max_revisions_per_chapter_is_2",
        "revision_policy_max_total_writes_is_3",
        "word_count_python_script_with_symbols",
        "T01_routing_planner_writer_checker_pipeline",
        "T04_routing_forced_upgrade_multi_chapter_pipeline",
        "T06_routing_writer_direct_no_planner",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    overall_passed = final_score >= 0.75 and critical_passed

    return {
        "passed": overall_passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))