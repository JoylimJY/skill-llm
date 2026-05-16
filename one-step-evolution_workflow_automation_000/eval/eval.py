import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    
    def check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── CHECK 1: AGENTS.md – topology must have only main + rescue, no lab/bizdev/ops/analytics-sidecar ──
    try:
        agents_path = ws / "AGENTS.md"
        content = agents_path.read_text(encoding="utf-8")
        
        # Must NOT contain lab, bizdev, ops agent, analytics-sidecar
        has_lab = bool(re.search(r'^##\s*lab\b', content, re.MULTILINE | re.IGNORECASE))
        has_bizdev = bool(re.search(r'^##\s*bizdev\b', content, re.MULTILINE | re.IGNORECASE))
        has_analytics_sidecar = bool(re.search(r'^##\s*analytics.sidecar\b', content, re.MULTILINE | re.IGNORECASE))
        
        # Must have main and rescue
        has_main = bool(re.search(r'^##\s*main\b', content, re.MULTILINE | re.IGNORECASE))
        has_rescue = bool(re.search(r'^##\s*rescue\b', content, re.MULTILINE | re.IGNORECASE))
        
        topology_clean = not has_lab and not has_bizdev and not has_analytics_sidecar
        topology_has_required = has_main and has_rescue
        
        check("agents_topology_no_lab_bizdev_sidecar", topology_clean,
              f"lab={has_lab}, bizdev={has_bizdev}, analytics_sidecar={has_analytics_sidecar} — all must be False")
        check("agents_topology_has_main_and_rescue", topology_has_required,
              f"has_main={has_main}, has_rescue={has_rescue}")
    except Exception as e:
        check("agents_topology_no_lab_bizdev_sidecar", False, f"Error reading AGENTS.md: {e}")
        check("agents_topology_has_main_and_rescue", False, f"Error reading AGENTS.md: {e}")

    # ── CHECK 2: rescue must NOT share memory path with main (isolation) ──
    try:
        agents_path = ws / "AGENTS.md"
        content = agents_path.read_text(encoding="utf-8")
        
        # Split into agent sections
        sections = re.split(r'^##\s+', content, flags=re.MULTILINE)
        main_section = ""
        rescue_section = ""
        for s in sections:
            if s.strip().lower().startswith("main"):
                main_section = s
            if s.strip().lower().startswith("rescue"):
                rescue_section = s
        
        # Extract memory paths
        main_mem = re.search(r'memory[:\s]+(\S+)', main_section)
        rescue_mem = re.search(r'memory[:\s]+(\S+)', rescue_section)
        
        main_mem_val = main_mem.group(1).strip() if main_mem else None
        rescue_mem_val = rescue_mem.group(1).strip() if rescue_mem else None
        
        # rescue memory should not be the same shared path as main
        # Also acceptable: rescue explicitly has minimal/no memory or its own isolated path
        if main_mem_val and rescue_mem_val:
            isolated = (main_mem_val != rescue_mem_val)
        elif rescue_mem_val is None or rescue_mem_val in ["none", "None", "minimal", "-", ""]:
            isolated = True
        else:
            isolated = True  # rescue has own path that doesn't overlap
        
        check("rescue_memory_isolated_from_main", isolated,
              f"main_memory='{main_mem_val}', rescue_memory='{rescue_mem_val}' — must differ or rescue must have no/minimal memory")
    except Exception as e:
        check("rescue_memory_isolated_from_main", False, f"Error: {e}")

    # ── CHECK 3: MEMORY.md must be curated/high-signal (not a dump) ──
    try:
        mem_path = ws / "MEMORY.md"
        content = mem_path.read_text(encoding="utf-8")
        word_count = len(content.split())
        
        # The original had 16 noisy dump items. A curated MEMORY.md should be significantly shorter
        # and should NOT contain grocery-list-level trivia
        dump_indicators = [
            "weather was nice", "bought coffee", "laptop battery",
            "password hint", "preferred font", "random facts",
            "TODO: fix the invoice", "Slack channel #general"
        ]
        has_dump = any(indicator.lower() in content.lower() for indicator in dump_indicators)
        
        # Must still have meaningful content (not empty)
        has_content = word_count > 20
        
        check("memory_md_not_a_dump", not has_dump,
              f"MEMORY.md still contains trivial dump content. Found dump indicators: {[d for d in dump_indicators if d.lower() in content.lower()]}")
        check("memory_md_has_content", has_content,
              f"MEMORY.md has {word_count} words — should have meaningful curated truths (>20 words)")
    except Exception as e:
        check("memory_md_not_a_dump", False, f"Error reading MEMORY.md: {e}")
        check("memory_md_has_content", False, f"Error: {e}")

    # ── CHECK 4: memory/YYYY-MM-DD.md daily log files exist ──
    try:
        memory_dir = ws / "memory"
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')
        
        daily_logs = []
        if memory_dir.exists():
            for f in memory_dir.iterdir():
                if f.is_file() and date_pattern.match(f.name):
                    daily_logs.append(f.name)
        
        has_daily_logs = len(daily_logs) >= 1
        check("memory_daily_logs_exist", has_daily_logs,
              f"Found date-stamped daily logs: {daily_logs}. Need at least 1 file matching YYYY-MM-DD.md")
    except Exception as e:
        check("memory_daily_logs_exist", False, f"Error: {e}")

    # ── CHECK 5: memory/topics/*.md exist (evergreen knowledge, not random dump) ──
    try:
        topics_dir = ws / "memory" / "topics"
        topic_files = []
        if topics_dir.exists():
            topic_files = [f.name for f in topics_dir.glob("*.md") 
                          if f.name.lower() != "random-dump.md"]
        
        has_topic_files = len(topic_files) >= 1
        
        # Make sure random-dump.md is gone or topics are meaningful
        dump_still_only = (len(topic_files) == 0)
        
        check("memory_topics_have_meaningful_files", has_topic_files and not dump_still_only,
              f"Meaningful topic files: {topic_files}. random-dump.md should be replaced by structured topics.")
    except Exception as e:
        check("memory_topics_have_meaningful_files", False, f"Error: {e}")

    # ── CHECK 6: projects/INDEX.md exists ──
    try:
        index_path = ws / "projects" / "INDEX.md"
        content = index_path.read_text(encoding="utf-8")
        has_index = len(content.strip()) > 20
        check("projects_index_md_exists", has_index,
              f"projects/INDEX.md exists with {len(content)} chars")
    except Exception as e:
        check("projects_index_md_exists", False, f"projects/INDEX.md missing or unreadable: {e}")

    # ── CHECK 7: projects/phoenix/PROGRESS.md and EXECUTION_PLAN.md exist ──
    try:
        progress_path = ws / "projects" / "phoenix" / "PROGRESS.md"
        exec_plan_path = ws / "projects" / "phoenix" / "EXECUTION_PLAN.md"
        
        progress_exists = progress_path.exists() and len(progress_path.read_text()) > 20
        exec_plan_exists = exec_plan_path.exists() and len(exec_plan_path.read_text()) > 20
        
        check("project_phoenix_has_progress_md", progress_exists,
              f"projects/phoenix/PROGRESS.md exists={progress_path.exists()}")
        check("project_phoenix_has_execution_plan_md", exec_plan_exists,
              f"projects/phoenix/EXECUTION_PLAN.md exists={exec_plan_path.exists()}")
    except Exception as e:
        check("project_phoenix_has_progress_md", False, f"Error: {e}")
        check("project_phoenix_has_execution_plan_md", False, f"Error: {e}")

    # ── CHECK 8: reflect-mode skill exists ──
    try:
        reflect_candidates = list(ws.rglob("*reflect*mode*")) + list(ws.rglob("*reflect_mode*"))
        reflect_skill_files = [p for p in reflect_candidates if p.is_file()]
        # Also check directory-based skill
        reflect_dir = ws / "skills" / "reflect-mode"
        reflect_dir_exists = reflect_dir.is_dir()
        
        has_reflect = len(reflect_skill_files) > 0 or reflect_dir_exists
        check("reflect_mode_skill_exists", has_reflect,
              f"reflect-mode skill found: files={[str(p) for p in reflect_skill_files]}, dir={reflect_dir_exists}")
    except Exception as e:
        check("reflect_mode_skill_exists", False, f"Error: {e}")

    # ── CHECK 9: AUTOMATION.md has three-tier scheduling (heartbeat + cron + isolated cron) ──
    try:
        auto_path = ws / "AUTOMATION.md"
        content = auto_path.read_text(encoding="utf-8").lower()
        
        has_heartbeat = "heartbeat" in content
        has_isolated_cron = ("isolated cron" in content or "isolated_cron" in content or 
                             "isolated-cron" in content)
        has_cron = "cron" in content
        # heartbeat cadence should mention 30 minutes or similar low-noise cadence
        has_30min = bool(re.search(r'30.min|every.30|30m\b|half.hour', content))
        
        check("automation_has_heartbeat", has_heartbeat,
              f"AUTOMATION.md mentions 'heartbeat': {has_heartbeat}")
        check("automation_has_isolated_cron", has_isolated_cron,
              f"AUTOMATION.md mentions isolated cron: {has_isolated_cron}")
        check("automation_heartbeat_30min_cadence", has_30min,
              f"AUTOMATION.md specifies ~30 min heartbeat cadence: {has_30min}. Content snippet: {content[:300]}")
    except Exception as e:
        check("automation_has_heartbeat", False, f"AUTOMATION.md missing or error: {e}")
        check("automation_has_isolated_cron", False, f"Error: {e}")
        check("automation_heartbeat_30min_cadence", False, f"Error: {e}")

    # ── CHECK 10: AUTOMATION.md references real project files ──
    try:
        auto_path = ws / "AUTOMATION.md"
        content = auto_path.read_text(encoding="utf-8").lower()
        
        # Should reference project files (not just generic placeholders)
        references_project_files = bool(re.search(
            r'projects?/|progress\.md|execution_plan|prd\.md|memory/\d{4}|memory/topics',
            content
        ))
        check("automation_references_real_files", references_project_files,
              f"AUTOMATION.md references actual project/memory files: {references_project_files}")
    except Exception as e:
        check("automation_references_real_files", False, f"Error: {e}")

    # ── CHECK 11: ollama config must be for embeddings only, not general inference ──
    try:
        ollama_path = ws / "config" / "ollama.yaml"
        content = ollama_path.read_text(encoding="utf-8").lower()
        
        # The original said "general inference" – should be changed to embeddings only
        # Check for embeddings/memorySearch purpose
        has_embeddings_purpose = bool(re.search(
            r'embed|memorysearch|memory.search|memory_search', content
        ))
        has_general_inference = bool(re.search(
            r'general inference|general.inference', content
        ))
        
        ollama_correctly_scoped = has_embeddings_purpose and not has_general_inference
        check("ollama_config_embeddings_only", ollama_correctly_scoped,
              f"ollama.yaml: has_embeddings_purpose={has_embeddings_purpose}, has_general_inference={has_general_inference}")
    except FileNotFoundError:
        # Agent might have deleted it entirely or moved it – check if they documented ollama elsewhere
        try:
            # Check AGENTS.md or other configs
            agents_content = (ws / "AGENTS.md").read_text(encoding="utf-8").lower()
            mentioned_embeddings = "embed" in agents_content or "memorysearch" in agents_content
            check("ollama_config_embeddings_only", mentioned_embeddings,
                  f"ollama.yaml removed; embeddings-only purpose found in AGENTS.md: {mentioned_embeddings}")
        except Exception as e2:
            check("ollama_config_embeddings_only", False, f"ollama.yaml missing and no alternative found: {e2}")
    except Exception as e:
        check("ollama_config_embeddings_only", False, f"Error reading ollama.yaml: {e}")

    # ── CHECK 12: HEARTBEAT.md exists with real tasks ──
    try:
        heartbeat_candidates = list(ws.rglob("HEARTBEAT.md"))
        if heartbeat_candidates:
            content = heartbeat_candidates[0].read_text(encoding="utf-8").lower()
            has_stalled = bool(re.search(r'stall|stuck|pending|approval|queue', content))
            has_memory = bool(re.search(r'memory|hygiene', content))
            has_real_content = len(content.strip()) > 50
            heartbeat_ok = has_real_content and (has_stalled or has_memory)
            check("heartbeat_md_exists_with_real_tasks", heartbeat_ok,
                  f"HEARTBEAT.md found at {heartbeat_candidates[0].relative_to(ws)}, "
                  f"has_stalled_detection={has_stalled}, has_memory_hygiene={has_memory}")
        else:
            check("heartbeat_md_exists_with_real_tasks", False, 
                  "HEARTBEAT.md not found anywhere in workspace")
    except Exception as e:
        check("heartbeat_md_exists_with_real_tasks", False, f"Error: {e}")

    # ── CHECK 13: evolution loop / reflect routine is documented ──
    try:
        # Look for evidence of evolution loop in any key file
        candidate_files = [
            ws / "AUTOMATION.md",
            ws / "AGENTS.md",
            ws / "MEMORY.md",
        ]
        # Also check reflect-mode skill if it exists
        reflect_dir = ws / "skills" / "reflect-mode"
        if reflect_dir.is_dir():
            for f in reflect_dir.glob("*.md"):
                candidate_files.append(f)
        
        evolution_found = False
        evolution_detail = []
        for cf in candidate_files:
            try:
                content = cf.read_text(encoding="utf-8").lower()
                has_promote = "promot" in content
                has_review = "review" in content or "reflect" in content
                has_daily_logs = "daily" in content and ("log" in content or "memory" in content)
                if has_promote and has_review:
                    evolution_found = True
                    evolution_detail.append(str(cf.relative_to(ws)))
            except:
                pass
        
        check("evolution_loop_documented", evolution_found,
              f"Evolution loop (promote + review/reflect) found in: {evolution_detail}")
    except Exception as e:
        check("evolution_loop_documented", False, f"Error: {e}")

    # ── Scoring ──────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)