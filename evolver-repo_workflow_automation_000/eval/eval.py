import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)

def main():
    workspace = Path(sys.argv[1])
    checks = []

    # ── CHECK 1: .env — EVOLVE_STRATEGY must be a valid value ───────────────
    env_path = workspace / ".env"
    valid_strategies = {"balanced", "innovate", "harden", "repair-only", "early-stabilize", "steady-state", "auto"}
    env_strategy = None
    env_allow_self_modify = None
    env_report_tool = None
    try:
        env_text = env_path.read_text(encoding="utf-8")
        for line in env_text.splitlines():
            line = line.strip()
            if line.startswith("EVOLVE_STRATEGY="):
                env_strategy = line.split("=", 1)[1].strip().strip('"').strip("'")
            if line.startswith("EVOLVE_ALLOW_SELF_MODIFY="):
                env_allow_self_modify = line.split("=", 1)[1].strip().strip('"').strip("'").lower()
            if line.startswith("EVOLVE_REPORT_TOOL="):
                env_report_tool = line.split("=", 1)[1].strip().strip('"').strip("'")

        strategy_ok = env_strategy in valid_strategies
        checks.append({
            "name": "env_valid_strategy",
            "passed": strategy_ok,
            "detail": f"EVOLVE_STRATEGY='{env_strategy}'. Must be one of {valid_strategies}. 'aggressive' is invalid."
        })
    except Exception as e:
        checks.append({"name": "env_valid_strategy", "passed": False, "detail": f"Cannot read .env: {e}"})

    # ── CHECK 2: .env — EVOLVE_ALLOW_SELF_MODIFY must be explicitly 'false' ─
    # Docs warn strongly: "NOT recommended for production" / default is false.
    # The scenario is production/cautious, so it must be false.
    try:
        allow_ok = (env_allow_self_modify == "false")
        checks.append({
            "name": "env_allow_self_modify_false",
            "passed": allow_ok,
            "detail": f"EVOLVE_ALLOW_SELF_MODIFY='{env_allow_self_modify}'. Must be 'false' for production safety (per SKILL.md safety protocol)."
        })
    except Exception as e:
        checks.append({"name": "env_allow_self_modify_false", "passed": False, "detail": str(e)})

    # ── CHECK 3: .env — EVOLVE_REPORT_TOOL should use feishu-card ───────────
    # SKILL.md: "automatically detects if compatible local skills (like skills/feishu-card) exist
    #  and upgrades its behavior accordingly" — but agent can also set EVOLVE_REPORT_TOOL=feishu-card
    # since skills/feishu-card EXISTS in the workspace.
    try:
        feishu_skill_exists = (workspace / "skills/feishu-card").is_dir()
        report_tool_ok = (env_report_tool == "feishu-card") if feishu_skill_exists else True
        checks.append({
            "name": "env_report_tool_feishu",
            "passed": report_tool_ok,
            "detail": f"EVOLVE_REPORT_TOOL='{env_report_tool}'. Since skills/feishu-card exists, EVOLVE_REPORT_TOOL should be 'feishu-card'."
        })
    except Exception as e:
        checks.append({"name": "env_report_tool_feishu", "passed": False, "detail": str(e)})

    # ── CHECK 4: assets/gep/genes.json — valid structure ────────────────────
    genes_path = workspace / "assets/gep/genes.json"
    try:
        data, err = load_json_safe(genes_path)
        if err:
            checks.append({"name": "genes_json_valid", "passed": False, "detail": f"Parse error: {err}"})
        else:
            # Must be an object with a 'genes' key containing a list of gene objects,
            # each with at minimum: id, name, description, type
            is_obj = isinstance(data, dict) and "genes" in data
            genes_list = data.get("genes", []) if isinstance(data, dict) else []
            all_valid = all(
                isinstance(g, dict) and
                all(k in g for k in ("id", "name", "description", "type"))
                for g in genes_list
            ) if genes_list else False
            structure_ok = is_obj and isinstance(genes_list, list) and len(genes_list) >= 1 and all_valid
            checks.append({
                "name": "genes_json_valid",
                "passed": structure_ok,
                "detail": f"genes.json must be an object with a 'genes' array; each gene needs id/name/description/type. Got: is_obj={is_obj}, count={len(genes_list)}, all_valid={all_valid}"
            })
    except Exception as e:
        checks.append({"name": "genes_json_valid", "passed": False, "detail": str(e)})

    # ── CHECK 5: assets/gep/capsules.json — valid structure ─────────────────
    capsules_path = workspace / "assets/gep/capsules.json"
    try:
        data, err = load_json_safe(capsules_path)
        if err:
            checks.append({"name": "capsules_json_valid", "passed": False, "detail": f"Parse error: {err}"})
        else:
            # Must be an object with a 'capsules' key (list of capsule objects)
            # each capsule: id, summary (to avoid repeating reasoning)
            is_obj = isinstance(data, dict) and "capsules" in data
            caps_list = data.get("capsules", []) if isinstance(data, dict) else []
            all_valid = all(
                isinstance(c, dict) and "id" in c and "summary" in c
                for c in caps_list
            ) if caps_list else False
            structure_ok = is_obj and isinstance(caps_list, list) and len(caps_list) >= 1 and all_valid
            checks.append({
                "name": "capsules_json_valid",
                "passed": structure_ok,
                "detail": f"capsules.json must be an object with 'capsules' array; each needs id/summary. Got: is_obj={is_obj}, count={len(caps_list)}, all_valid={all_valid}"
            })
    except Exception as e:
        checks.append({"name": "capsules_json_valid", "passed": False, "detail": str(e)})

    # ── CHECK 6: assets/gep/events.jsonl — append-only, valid JSONL, tree structure ──
    events_path = workspace / "assets/gep/events.jsonl"
    try:
        raw = events_path.read_text(encoding="utf-8")
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        # All lines must be valid JSON
        parsed_events = []
        all_json_ok = True
        for line in lines:
            try:
                obj = json.loads(line)
                parsed_events.append(obj)
            except Exception:
                all_json_ok = False
                break

        # Must have at least 2 events (bootstrap + at least one evolution event)
        enough_events = len(parsed_events) >= 2

        # Tree structure: at least one event must have a 'parent' field (linking to another event's id)
        has_parent_link = any("parent" in e for e in parsed_events)

        # Each event must have 'id' and 'type'
        all_have_id_type = all("id" in e and "type" in e for e in parsed_events)

        structure_ok = all_json_ok and enough_events and has_parent_link and all_have_id_type
        checks.append({
            "name": "events_jsonl_valid_tree",
            "passed": structure_ok,
            "detail": (f"events.jsonl: all_json={all_json_ok}, count={len(parsed_events)}, "
                       f"has_parent_link={has_parent_link}, all_have_id_type={all_have_id_type}. "
                       f"Must be valid JSONL, >=2 events, each with id+type, at least one with parent field.")
        })
    except Exception as e:
        checks.append({"name": "events_jsonl_valid_tree", "passed": False, "detail": str(e)})

    # ── CHECK 7: Deployment summary document — emoji policy ─────────────────
    # Must find a markdown or text deployment summary file somewhere in the workspace.
    # File must exist, have meaningful content, and comply with emoji policy:
    # ONLY 🧬 (DNA) emoji allowed, NO other emojis.
    summary_candidates = list(workspace.rglob("deployment_summary*")) + \
                         list(workspace.rglob("*deployment*summary*")) + \
                         list(workspace.rglob("*summary*report*")) + \
                         list(workspace.rglob("evolver_summary*"))
    # Filter out directories
    summary_candidates = [f for f in summary_candidates if f.is_file()]

    if not summary_candidates:
        checks.append({
            "name": "summary_doc_exists",
            "passed": False,
            "detail": "No deployment summary document found (looked for files matching deployment_summary*, evolver_summary*, etc.)"
        })
        checks.append({
            "name": "summary_emoji_policy",
            "passed": False,
            "detail": "Cannot check emoji policy — no summary document found."
        })
    else:
        summary_file = summary_candidates[0]
        try:
            content = summary_file.read_text(encoding="utf-8")
            has_content = len(content.strip()) > 50
            checks.append({
                "name": "summary_doc_exists",
                "passed": has_content,
                "detail": f"Found: {summary_file.relative_to(workspace)}. Content length: {len(content)} chars."
            })

            # Emoji policy: only DNA emoji 🧬 allowed; detect any other emoji
            # We check for common emoji ranges in Unicode
            dna_emoji = "\U0001F9EC"  # 🧬

            # Remove all DNA emoji, then check if any emoji-like chars remain
            # Use a broad regex for emoji Unicode blocks
            emoji_pattern = re.compile(
                "[\U0001F600-\U0001F64F"   # emoticons
                "\U0001F300-\U0001F5FF"   # misc symbols & pictographs
                "\U0001F680-\U0001F6FF"   # transport & map
                "\U0001F700-\U0001F77F"   # alchemical symbols
                "\U0001F780-\U0001F7FF"   # geometric shapes extended
                "\U0001F800-\U0001F8FF"   # supplemental arrows
                "\U0001F900-\U0001F9FF"   # supplemental symbols (includes 🧬)
                "\U0001FA00-\U0001FA6F"
                "\U0001FA70-\U0001FAFF"
                "\U00002702-\U000027B0"   # dingbats
                "\U000024C2-\U0001F251"
                "]+",
                flags=re.UNICODE
            )

            # Find all emojis in content
            all_emojis_found = emoji_pattern.findall(content)
            # Filter: remove instances that are purely the DNA emoji
            forbidden_emojis = []
            for match in all_emojis_found:
                cleaned = match.replace(dna_emoji, "")
                if cleaned:
                    forbidden_emojis.append(match)

            emoji_ok = len(forbidden_emojis) == 0
            checks.append({
                "name": "summary_emoji_policy",
                "passed": emoji_ok,
                "detail": (f"Emoji policy: only 🧬 DNA emoji allowed. "
                           f"Forbidden emojis found: {forbidden_emojis[:5]}" if not emoji_ok
                           else "Emoji policy satisfied: only 🧬 DNA emoji present or no emojis.")
            })
        except Exception as e:
            checks.append({"name": "summary_doc_exists", "passed": False, "detail": str(e)})
            checks.append({"name": "summary_emoji_policy", "passed": False, "detail": str(e)})

    # ── CHECK 8: EVOLVE_LOAD_MAX corrected from broken value ────────────────
    # Original .env had 3.5 which means evolver would NEVER back off (too high).
    # Docs say default is 2.0. For a cautious production env it should be <= 2.0.
    try:
        env_text = env_path.read_text(encoding="utf-8")
        load_max = None
        for line in env_text.splitlines():
            line = line.strip()
            if line.startswith("EVOLVE_LOAD_MAX="):
                try:
                    load_max = float(line.split("=", 1)[1].strip())
                except Exception:
                    pass
        load_ok = (load_max is not None) and (load_max <= 2.0)
        checks.append({
            "name": "env_load_max_safe",
            "passed": load_ok,
            "detail": f"EVOLVE_LOAD_MAX={load_max}. Must be <= 2.0 (the documented safe default) for a production environment. Original broken value was 3.5."
        })
    except Exception as e:
        checks.append({"name": "env_load_max_safe", "passed": False, "detail": str(e)})

    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 6  # must pass at least 6/8

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()