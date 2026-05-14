#!/usr/bin/env python3
"""
Evaluation script for the council-builder task.
Tests that a 3-agent data consultancy council was correctly built,
including all required files, content checks, and routing configuration.

Usage: python eval_script.py <workspace_path>
"""

import sys
import json
import re
from pathlib import Path

def load_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"__MISSING__: {e}"

def check_file_exists(path: Path, name: str) -> dict:
    exists = path.exists() and path.is_file()
    return {
        "name": name,
        "passed": exists,
        "detail": f"Found: {path}" if exists else f"Missing: {path}"
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(0)

    ws = Path(sys.argv[1])
    checks = []

    # ── 1. init-council.sh was actually run (agent dirs must exist) ────────────
    agents_dir = ws / "agents"
    agent_dirs = [d for d in agents_dir.iterdir() if d.is_dir()] if agents_dir.exists() else []
    agent_count = len(agent_dirs)

    checks.append({
        "name": "agent_count_3_to_7",
        "passed": 3 <= agent_count <= 7,
        "detail": f"Found {agent_count} agent directories. Expected 3-7."
    })

    if agent_count == 0:
        # No agents at all — fail fast
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "early_exit", "passed": False,
                                  "detail": "No agents found; skipping further checks."}]
        }))
        sys.exit(0)

    # ── 2. Per-agent structure checks ─────────────────────────────────────────
    all_agents_valid = True
    soul_texts = []

    for agent_dir in agent_dirs:
        aname = agent_dir.name

        # Required files per agent
        required_files = {
            f"{aname}/SOUL.md": agent_dir / "SOUL.md",
            f"{aname}/AGENTS.md": agent_dir / "AGENTS.md",
            f"{aname}/config.json": agent_dir / "config.json",
            f"{aname}/gotchas.md": agent_dir / "gotchas.md",
            f"{aname}/.learnings/LEARNINGS.md": agent_dir / ".learnings/LEARNINGS.md",
            f"{aname}/.learnings/ERRORS.md": agent_dir / ".learnings/ERRORS.md",
            f"{aname}/.learnings/FEATURE_REQUESTS.md": agent_dir / ".learnings/FEATURE_REQUESTS.md",
            f"{aname}/scripts/README.md": agent_dir / "scripts/README.md",
            f"{aname}/references/verification-checklist.md": agent_dir / "references/verification-checklist.md",
            f"{aname}/memory/learning-metrics.json": agent_dir / "memory/learning-metrics.json",
        }

        for label, fpath in required_files.items():
            c = check_file_exists(fpath, f"exists:{label}")
            checks.append(c)
            if not c["passed"]:
                all_agents_valid = False

        # config.json: setup_complete must be false, agent_name must not be placeholder
        config_path = agent_dir / "config.json"
        try:
            cfg = json.loads(config_path.read_text())
            sc = cfg.get("setup_complete", "__missing__")
            aname_cfg = cfg.get("agent_name", "")
            sc_ok = sc is False
            name_ok = aname_cfg not in ("", "[REPLACE]", None)
            checks.append({
                "name": f"config_setup_complete_false:{aname}",
                "passed": sc_ok,
                "detail": f"setup_complete={sc!r} (must be false)" if not sc_ok else "OK"
            })
            checks.append({
                "name": f"config_agent_name_set:{aname}",
                "passed": name_ok,
                "detail": f"agent_name={aname_cfg!r} (must not be placeholder)" if not name_ok else "OK"
            })
            if not sc_ok or not name_ok:
                all_agents_valid = False
        except Exception as e:
            checks.append({"name": f"config_parse:{aname}", "passed": False, "detail": str(e)})
            all_agents_valid = False

        # learning-metrics.json: must have agent_name and metrics block
        metrics_path = agent_dir / "memory/learning-metrics.json"
        try:
            metrics = json.loads(metrics_path.read_text())
            has_metrics = "metrics" in metrics
            has_name = metrics.get("agent_name", "") not in ("", "[REPLACE]", None)
            checks.append({
                "name": f"learning_metrics_structure:{aname}",
                "passed": has_metrics and has_name,
                "detail": f"metrics block present={has_metrics}, agent_name set={has_name}"
            })
        except Exception as e:
            checks.append({"name": f"learning_metrics_parse:{aname}", "passed": False, "detail": str(e)})
            all_agents_valid = False

        # SOUL.md: must not contain corporate language red flags
        soul_path = agent_dir / "SOUL.md"
        soul_text = load_text(soul_path)
        soul_texts.append(soul_text)
        corporate_flags = [
            "leverages synergies", "proactive stakeholder", "results-driven",
            "best-in-class", "value-add", "thought leader", "paradigm shift"
        ]
        corp_found = [f for f in corporate_flags if f.lower() in soul_text.lower()]
        checks.append({
            "name": f"soul_no_corporate_language:{aname}",
            "passed": len(corp_found) == 0,
            "detail": f"Corporate phrases found: {corp_found}" if corp_found else "OK"
        })

        # SOUL.md: must have Learning Triggers section
        has_triggers = bool(re.search(r"learning trigger", soul_text, re.IGNORECASE))
        checks.append({
            "name": f"soul_has_learning_triggers:{aname}",
            "passed": has_triggers,
            "detail": "Learning Triggers section present" if has_triggers else "Missing 'Learning Triggers' section in SOUL.md"
        })

        # SOUL.md: must NOT be a template placeholder (should have > 100 words)
        word_count = len(soul_text.split())
        soul_non_trivial = word_count > 80
        checks.append({
            "name": f"soul_content_non_trivial:{aname}",
            "passed": soul_non_trivial,
            "detail": f"SOUL.md word count: {word_count} (need >80)"
        })

    # ── 3. Soul uniqueness check (no two souls should be identical) ──────────
    if len(soul_texts) >= 2:
        unique_souls = len(set(soul_texts))
        souls_unique = unique_souls == len(soul_texts)
        checks.append({
            "name": "souls_are_unique",
            "passed": souls_unique,
            "detail": f"{unique_souls}/{len(soul_texts)} soul files are unique"
        })
    
    # ── 4. Root AGENTS.md checks ──────────────────────────────────────────────
    root_agents = ws / "AGENTS.md"
    checks.append(check_file_exists(root_agents, "root_AGENTS.md_exists"))

    root_text = load_text(root_agents)

    # Must contain all 4 routing tiers
    routing_tiers = ["fast", "think", "deep", "strategic"]
    for tier in routing_tiers:
        tier_present = bool(re.search(tier, root_text, re.IGNORECASE))
        checks.append({
            "name": f"root_agents_routing_tier_{tier}",
            "passed": tier_present,
            "detail": f"Tier '{tier}' found in root AGENTS.md" if tier_present else f"Missing tier '{tier}' in root AGENTS.md"
        })

    # Must contain de-escalation rule
    deescalate_present = bool(re.search(r"de.?escalat", root_text, re.IGNORECASE))
    checks.append({
        "name": "root_agents_deescalation_rule",
        "passed": deescalate_present,
        "detail": "De-escalation rule present" if deescalate_present else "Missing de-escalation rule in root AGENTS.md"
    })

    # Must contain rate-limit fallback
    ratelimit_present = bool(re.search(r"rate.?limit", root_text, re.IGNORECASE))
    checks.append({
        "name": "root_agents_rate_limit_fallback",
        "passed": ratelimit_present,
        "detail": "Rate-limit fallback present" if ratelimit_present else "Missing rate-limit fallback in root AGENTS.md"
    })

    # Must contain an agent routing table (pipe-delimited table)
    routing_table_present = bool(re.search(r"\|\s*Agent\s*\|", root_text, re.IGNORECASE))
    checks.append({
        "name": "root_agents_routing_table",
        "passed": routing_table_present,
        "detail": "Routing table found" if routing_table_present else "No routing table (pipe-delimited) in root AGENTS.md"
    })

    # ── 5. Adaptive routing architecture doc ─────────────────────────────────
    arch_doc = ws / "docs/architecture/ADAPTIVE-ROUTING-LEARNING.md"
    checks.append(check_file_exists(arch_doc, "adaptive_routing_learning_doc_exists"))
    arch_text = load_text(arch_doc)
    arch_has_content = len(arch_text.split()) > 40 and "__MISSING__" not in arch_text
    checks.append({
        "name": "adaptive_routing_doc_has_content",
        "passed": arch_has_content,
        "detail": f"Doc word count: {len(arch_text.split())} (need >40)" if arch_has_content else "Doc is empty or missing"
    })

    # ── 6. Shared learnings cross-agent file ──────────────────────────────────
    cross_agent = ws / "shared/learnings/CROSS-AGENT.md"
    checks.append(check_file_exists(cross_agent, "shared_cross_agent_learnings_exists"))

    # ── 7. Agent names must be memorable (not "Agent 1", "Agent1", "agent_1") ─
    for agent_dir in agent_dirs:
        aname = agent_dir.name
        generic_pattern = bool(re.match(r"^(agent|assistant|helper|bot)[\s_\-]?\d*$", aname, re.IGNORECASE))
        checks.append({
            "name": f"agent_name_not_generic:{aname}",
            "passed": not generic_pattern,
            "detail": f"Agent name '{aname}' is generic/placeholder" if generic_pattern else f"Agent name '{aname}' is memorable"
        })

    # ── 8. verify-output.sh or similar script per agent ──────────────────────
    for agent_dir in agent_dirs:
        aname = agent_dir.name
        scripts_dir = agent_dir / "scripts"
        has_verify = any(
            "verify" in f.name.lower() or "check" in f.name.lower()
            for f in scripts_dir.glob("*") if f.is_file()
        ) if scripts_dir.exists() else False
        checks.append({
            "name": f"agent_has_verify_script:{aname}",
            "passed": has_verify,
            "detail": "Verification script found" if has_verify else f"No verify/check script in {scripts_dir}"
        })

    # ── Score calculation ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0

    # Overall pass: at least 80% of checks pass AND core structural checks pass
    core_check_names = [
        "agent_count_3_to_7",
        "root_AGENTS.md_exists",
        "root_agents_routing_tier_fast",
        "root_agents_routing_tier_think",
        "root_agents_routing_tier_deep",
        "root_agents_routing_tier_strategic",
        "root_agents_deescalation_rule",
        "adaptive_routing_learning_doc_exists",
        "shared_cross_agent_learnings_exists",
    ]
    core_passed = all(
        any(c["name"] == cname and c["passed"] for c in checks)
        for cname in core_check_names
    )

    overall_passed = score >= 0.80 and core_passed

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()