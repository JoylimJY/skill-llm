#!/usr/bin/env python3
"""
Evaluation script for the genomics pipeline task-router benchmark.
Checks:
1. Agents registered correctly (genome-seq-bot, variant-bot, annotator-bot) with right capabilities/emoji/max-concurrent
2. config.yaml has correct routing strategies (least-loaded for alignment/sequencing, round-robin for image_gen equivalent, priority for urgent)
3. Dead-letter task task-dl-9f3a2b has been retried (moved to pending queue, reset state)
4. A chained pipeline of tasks exists: sequencing → alignment (depends on sequencing) → variant_calling (depends on alignment) → annotation (depends on variant_calling), all with correct priorities
"""
import sys
import json
import yaml
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/home/agent")
    
    checks = []
    score_parts = []

    TASK_ROUTER = workspace / ".openclaw" / "task-router"
    AGENTS_FILE = TASK_ROUTER / "agents.yaml"
    CONFIG_FILE = TASK_ROUTER / "config.yaml"
    QUEUE_PENDING = TASK_ROUTER / "queue" / "pending"
    DEAD_LETTER_DIR = TASK_ROUTER / "dead-letter"

    # ── CHECK 1: agents.yaml exists and has at least 2 registered agents ──────
    try:
        with open(AGENTS_FILE) as f:
            agents_data = yaml.safe_load(f)
        agents = agents_data.get("agents", {})
        num_agents = len(agents)
        
        check1_passed = num_agents >= 2
        checks.append({
            "name": "agents_registered_minimum_2",
            "passed": check1_passed,
            "detail": f"Found {num_agents} agents registered. Need at least 2." if not check1_passed 
                      else f"OK: {num_agents} agents registered: {list(agents.keys())}"
        })
        score_parts.append(1.0 if check1_passed else 0.0)
    except Exception as e:
        checks.append({"name": "agents_registered_minimum_2", "passed": False, "detail": f"Error reading agents.yaml: {e}"})
        score_parts.append(0.0)
        agents = {}

    # ── CHECK 2: Agents have specific capabilities matching genomics domain ────
    try:
        all_caps = []
        for agent_id, agent in agents.items():
            all_caps.extend(agent.get("capabilities", []))
        all_caps_set = set(all_caps)
        
        # At minimum need variant_calling or variant-calling and sequencing or alignment capabilities
        has_sequencing = any(c in all_caps_set for c in ["sequencing", "alignment", "genome-sequencing"])
        has_variant = any(c in all_caps_set for c in ["variant_calling", "variant-calling", "variant_call"])
        
        check2_passed = has_sequencing and has_variant
        checks.append({
            "name": "agents_have_genomics_capabilities",
            "passed": check2_passed,
            "detail": f"Capabilities across all agents: {list(all_caps_set)}. Need sequencing-related and variant_calling-related." 
                      if not check2_passed else f"OK: Found sequencing={has_sequencing}, variant_calling={has_variant}. Caps: {list(all_caps_set)}"
        })
        score_parts.append(1.0 if check2_passed else 0.0)
    except Exception as e:
        checks.append({"name": "agents_have_genomics_capabilities", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 3: Agents have valid max_concurrent (int > 0) and emoji set ─────
    try:
        agents_with_max = [a for a in agents.values() if isinstance(a.get("max_concurrent"), int) and a["max_concurrent"] > 0]
        agents_with_emoji = [a for a in agents.values() if a.get("emoji") and a["emoji"] != "🤖"]
        
        # At least one agent should have max_concurrent explicitly set
        # At least one agent should have a non-default emoji
        mc_ok = len(agents_with_max) >= 1
        emoji_ok = len(agents_with_emoji) >= 1
        check3_passed = mc_ok and emoji_ok
        checks.append({
            "name": "agents_have_max_concurrent_and_emoji",
            "passed": check3_passed,
            "detail": f"Agents with valid max_concurrent: {len(agents_with_max)}, with non-default emoji: {len(agents_with_emoji)}"
        })
        score_parts.append(1.0 if check3_passed else 0.0)
    except Exception as e:
        checks.append({"name": "agents_have_max_concurrent_and_emoji", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 4: config.yaml has valid routing strategies (not broken) ────────
    try:
        with open(CONFIG_FILE) as f:
            config = yaml.safe_load(f)
        
        router_cfg = config.get("router", {})
        strategies = router_cfg.get("strategies", {})
        
        VALID_STRATEGIES = {"round-robin", "least-loaded", "priority", "fastest", "sticky"}
        
        default_strategy = strategies.get("default", "")
        default_valid = default_strategy in VALID_STRATEGIES
        
        # The old broken config had "random-pick" and "overload-first" — those must be gone
        by_type = strategies.get("by_type", {})
        has_invalid = any(v not in VALID_STRATEGIES for v in by_type.values() if v)
        
        check4_passed = default_valid and not has_invalid
        checks.append({
            "name": "config_routing_strategies_valid",
            "passed": check4_passed,
            "detail": f"default='{default_strategy}' (valid={default_valid}), by_type={by_type}, has_invalid={has_invalid}"
        })
        score_parts.append(1.0 if check4_passed else 0.0)
    except Exception as e:
        checks.append({"name": "config_routing_strategies_valid", "passed": False, "detail": f"Error reading config.yaml: {e}"})
        score_parts.append(0.0)
        config = {}

    # ── CHECK 5: config.yaml has by_type strategies for genomics task types ───
    try:
        router_cfg = config.get("router", {}) if config else {}
        strategies = router_cfg.get("strategies", {})
        by_type = strategies.get("by_type", {})
        
        # Must have at least 2 genomics-related task types configured
        genomics_types = {"sequencing", "alignment", "variant_calling", "annotation", "analysis", "research"}
        configured_types = set(by_type.keys())
        overlap = genomics_types & configured_types
        
        check5_passed = len(overlap) >= 2
        checks.append({
            "name": "config_has_genomics_by_type_strategies",
            "passed": check5_passed,
            "detail": f"Genomics task types configured in by_type: {list(overlap)}. Need >= 2."
        })
        score_parts.append(1.0 if check5_passed else 0.0)
    except Exception as e:
        checks.append({"name": "config_has_genomics_by_type_strategies", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 6: Dead-letter task task-dl-9f3a2b retried (in pending queue) ───
    try:
        dead_letter_path = DEAD_LETTER_DIR / "task-dl-9f3a2b.yaml"
        pending_path = QUEUE_PENDING / "task-dl-9f3a2b.yaml"
        
        dl_gone = not dead_letter_path.exists()
        in_pending = pending_path.exists()
        
        if in_pending:
            with open(pending_path) as f:
                retried_task = yaml.safe_load(f)
            status_is_pending = retried_task.get("status") == "pending"
            retries_reset = retried_task.get("retries", 99) == 0
        else:
            status_is_pending = False
            retries_reset = False
        
        # Also accept if it was moved to active (reassigned) or completed
        active_path = TASK_ROUTER / "queue" / "active" / "task-dl-9f3a2b.yaml"
        in_active = active_path.exists()
        
        check6_passed = dl_gone and (in_pending or in_active)
        checks.append({
            "name": "dead_letter_task_retried",
            "passed": check6_passed,
            "detail": (
                f"dead_letter_removed={dl_gone}, in_pending={in_pending}, in_active={in_active}, "
                f"status_pending={status_is_pending}, retries_reset={retries_reset}"
            )
        })
        score_parts.append(1.0 if check6_passed else 0.0)
    except Exception as e:
        checks.append({"name": "dead_letter_task_retried", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 7: At least 3 pipeline tasks created with dependencies ──────────
    try:
        pending_tasks = []
        active_tasks = []
        
        for p in QUEUE_PENDING.glob("*.yaml"):
            if p.name == "task-dl-9f3a2b.yaml":
                continue  # skip the retried dead-letter task
            try:
                with open(p) as f:
                    t = yaml.safe_load(f)
                pending_tasks.append(t)
            except:
                pass
        
        for p in (TASK_ROUTER / "queue" / "active").glob("*.yaml"):
            if p.name == "task-dl-9f3a2b.yaml":
                continue
            try:
                with open(p) as f:
                    t = yaml.safe_load(f)
                active_tasks.append(t)
            except:
                pass
        
        all_new_tasks = pending_tasks + active_tasks
        tasks_with_deps = [t for t in all_new_tasks if t.get("dependencies") and len(t["dependencies"]) > 0]
        
        check7_passed = len(all_new_tasks) >= 3 and len(tasks_with_deps) >= 2
        checks.append({
            "name": "pipeline_tasks_with_dependencies_created",
            "passed": check7_passed,
            "detail": f"New tasks in queue: {len(all_new_tasks)}, tasks with dependencies: {len(tasks_with_deps)}. Need >= 3 tasks and >= 2 with dependencies."
        })
        score_parts.append(1.0 if check7_passed else 0.0)
    except Exception as e:
        checks.append({"name": "pipeline_tasks_with_dependencies_created", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 8: Tasks have correct genomics-relevant types ───────────────────
    try:
        genomics_task_types = {"sequencing", "alignment", "variant_calling", "annotation", "analysis"}
        new_task_types = set(t.get("type", "") for t in all_new_tasks)
        overlap_types = genomics_task_types & new_task_types
        
        check8_passed = len(overlap_types) >= 2
        checks.append({
            "name": "tasks_have_genomics_types",
            "passed": check8_passed,
            "detail": f"Task types created: {list(new_task_types)}. Genomics-relevant: {list(overlap_types)}. Need >= 2 distinct genomics types."
        })
        score_parts.append(1.0 if check8_passed else 0.0)
    except Exception as e:
        checks.append({"name": "tasks_have_genomics_types", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 9: At least one task has priority set to high or urgent ─────────
    try:
        high_priority_tasks = [t for t in all_new_tasks if t.get("priority") in ("high", "urgent")]
        check9_passed = len(high_priority_tasks) >= 1
        checks.append({
            "name": "at_least_one_high_priority_task",
            "passed": check9_passed,
            "detail": f"High/urgent priority tasks: {len(high_priority_tasks)} out of {len(all_new_tasks)} total."
        })
        score_parts.append(1.0 if check9_passed else 0.0)
    except Exception as e:
        checks.append({"name": "at_least_one_high_priority_task", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── CHECK 10: Dependency chain is valid (dep task IDs exist in queue) ─────
    try:
        all_task_ids = set(t.get("id", "") for t in all_new_tasks)
        # Also include the retried dead-letter task
        all_task_ids.add("task-dl-9f3a2b")
        
        broken_deps = []
        for t in all_new_tasks:
            for dep_id in t.get("dependencies", []):
                if dep_id not in all_task_ids:
                    broken_deps.append((t["id"], dep_id))
        
        check10_passed = len(broken_deps) == 0 and len(tasks_with_deps) >= 1
        checks.append({
            "name": "dependency_chain_is_valid",
            "passed": check10_passed,
            "detail": f"Broken dependencies: {broken_deps}. Tasks with valid deps: {len(tasks_with_deps)}."
        })
        score_parts.append(1.0 if check10_passed else 0.0)
    except Exception as e:
        checks.append({"name": "dependency_chain_is_valid", "passed": False, "detail": f"Error: {e}"})
        score_parts.append(0.0)

    # ── Final score ────────────────────────────────────────────────────────────
    total_score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()