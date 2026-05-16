import sys
import os
import json

def run_eval(workspace_dir):
    HOME = os.path.expanduser("~")
    MAIN_WS = os.path.join(HOME, ".openclaw", "workspace")
    DYNAMIC_WS = os.path.join(HOME, ".openclaw", "workspace-wecom-default-dm-xun")

    checks = []
    total_score = 0.0

    # --- Define expected config files ---
    CONFIG_FILES = [
        "AGENTS.md",
        "SOUL.md",
        "TOOLS.md",
        "IDENTITY.md",
        "USER.md",
        "HEARTBEAT.md",
        "MEMORY.md",
    ]

    # --- Define expected skill files ---
    SKILL_FILES = [
        "skills/greet.js",
        "skills/faq.js",
        "skills/escalate.js",
        "skills/ticket.js",
        "skills/survey.js",
    ]

    # --- Define expected memory files ---
    MEMORY_FILES = [
        "memory/user_prefs.json",
        "memory/session_cache.json",
        "memory/knowledge_base.json",
    ]

    # CHECK 1: Dynamic workspace exists at correct path
    try:
        dyn_exists = os.path.isdir(DYNAMIC_WS)
        checks.append({
            "name": "dynamic_workspace_exists_at_correct_path",
            "passed": dyn_exists,
            "detail": f"Dynamic workspace at {DYNAMIC_WS}: {'found' if dyn_exists else 'NOT FOUND'}"
        })
    except Exception as e:
        checks.append({"name": "dynamic_workspace_exists_at_correct_path", "passed": False, "detail": str(e)})

    # CHECK 2-8: All 7 config files exist in dynamic workspace with MASTER content
    all_configs_correct = True
    for fname in CONFIG_FILES:
        try:
            main_path = os.path.join(MAIN_WS, fname)
            dyn_path = os.path.join(DYNAMIC_WS, fname)

            if not os.path.isfile(main_path):
                checks.append({
                    "name": f"config_sync_{fname}",
                    "passed": False,
                    "detail": f"MAIN workspace missing {fname} - test setup error"
                })
                all_configs_correct = False
                continue

            with open(main_path, "r") as f:
                master_content = f.read()

            if not os.path.isfile(dyn_path):
                checks.append({
                    "name": f"config_sync_{fname}",
                    "passed": False,
                    "detail": f"{fname} missing in dynamic workspace"
                })
                all_configs_correct = False
                continue

            with open(dyn_path, "r") as f:
                dyn_content = f.read()

            # Content must match master exactly
            content_match = (dyn_content.strip() == master_content.strip())
            # Must NOT contain STALE marker
            not_stale = "[STALE" not in dyn_content

            passed = content_match and not_stale
            all_configs_correct = all_configs_correct and passed

            detail = ""
            if not content_match:
                detail = f"{fname}: content mismatch with master. Dynamic has: {dyn_content[:80]!r}"
            elif not not_stale:
                detail = f"{fname}: contains STALE marker - not overwritten"
            else:
                detail = f"{fname}: correctly synced from master"

            checks.append({
                "name": f"config_sync_{fname}",
                "passed": passed,
                "detail": detail
            })
        except Exception as e:
            checks.append({"name": f"config_sync_{fname}", "passed": False, "detail": str(e)})
            all_configs_correct = False

    # CHECK 9: Stale AGENTS.md was overwritten (not kept)
    try:
        dyn_agents = os.path.join(DYNAMIC_WS, "AGENTS.md")
        if os.path.isfile(dyn_agents):
            with open(dyn_agents) as f:
                content = f.read()
            overwritten = "version: 2.1.0" in content and "[STALE" not in content
            checks.append({
                "name": "stale_agents_overwritten",
                "passed": overwritten,
                "detail": f"AGENTS.md overwrite check: {'passed' if overwritten else 'STALE content found or master version missing'}"
            })
        else:
            checks.append({"name": "stale_agents_overwritten", "passed": False, "detail": "AGENTS.md missing"})
    except Exception as e:
        checks.append({"name": "stale_agents_overwritten", "passed": False, "detail": str(e)})

    # CHECK 10-14: Skills directory synced
    all_skills_correct = True
    for fpath_rel in SKILL_FILES:
        try:
            main_path = os.path.join(MAIN_WS, fpath_rel)
            dyn_path = os.path.join(DYNAMIC_WS, fpath_rel)

            with open(main_path, "r") as f:
                master_content = f.read()

            if not os.path.isfile(dyn_path):
                checks.append({
                    "name": f"skills_sync_{os.path.basename(fpath_rel)}",
                    "passed": False,
                    "detail": f"{fpath_rel} missing in dynamic workspace"
                })
                all_skills_correct = False
                continue

            with open(dyn_path, "r") as f:
                dyn_content = f.read()

            passed = (dyn_content.strip() == master_content.strip())
            all_skills_correct = all_skills_correct and passed
            checks.append({
                "name": f"skills_sync_{os.path.basename(fpath_rel)}",
                "passed": passed,
                "detail": f"{fpath_rel}: {'synced correctly' if passed else 'content mismatch'}"
            })
        except Exception as e:
            checks.append({"name": f"skills_sync_{os.path.basename(fpath_rel)}", "passed": False, "detail": str(e)})
            all_skills_correct = False

    # CHECK 15: Stale greet.js was overwritten
    try:
        dyn_greet = os.path.join(DYNAMIC_WS, "skills", "greet.js")
        if os.path.isfile(dyn_greet):
            with open(dyn_greet) as f:
                content = f.read()
            overwritten = "OLD greeting" not in content and "Greeting skill" in content
            checks.append({
                "name": "stale_skill_overwritten",
                "passed": overwritten,
                "detail": f"skills/greet.js overwrite: {'passed' if overwritten else 'stale content found'}"
            })
        else:
            checks.append({"name": "stale_skill_overwritten", "passed": False, "detail": "skills/greet.js missing"})
    except Exception as e:
        checks.append({"name": "stale_skill_overwritten", "passed": False, "detail": str(e)})

    # CHECK 16-18: Memory directory synced
    all_memory_correct = True
    for fpath_rel in MEMORY_FILES:
        try:
            main_path = os.path.join(MAIN_WS, fpath_rel)
            dyn_path = os.path.join(DYNAMIC_WS, fpath_rel)

            with open(main_path, "r") as f:
                master_content = f.read()

            if not os.path.isfile(dyn_path):
                checks.append({
                    "name": f"memory_sync_{os.path.basename(fpath_rel)}",
                    "passed": False,
                    "detail": f"{fpath_rel} missing in dynamic workspace"
                })
                all_memory_correct = False
                continue

            with open(dyn_path, "r") as f:
                dyn_content = f.read()

            passed = (dyn_content.strip() == master_content.strip())
            all_memory_correct = all_memory_correct and passed
            checks.append({
                "name": f"memory_sync_{os.path.basename(fpath_rel)}",
                "passed": passed,
                "detail": f"{fpath_rel}: {'synced correctly' if passed else 'content mismatch'}"
            })
        except Exception as e:
            checks.append({"name": f"memory_sync_{os.path.basename(fpath_rel)}", "passed": False, "detail": str(e)})
            all_memory_correct = False

    # CHECK 19: Stale user_prefs.json was overwritten
    try:
        dyn_prefs = os.path.join(DYNAMIC_WS, "memory", "user_prefs.json")
        if os.path.isfile(dyn_prefs):
            with open(dyn_prefs) as f:
                content = f.read()
            data = json.loads(content)
            # Master has "zh-CN", stale had "en-US"
            overwritten = data.get("lang") == "zh-CN"
            checks.append({
                "name": "stale_memory_overwritten",
                "passed": overwritten,
                "detail": f"memory/user_prefs.json overwrite: lang={data.get('lang')!r}, expected 'zh-CN'"
            })
        else:
            checks.append({"name": "stale_memory_overwritten", "passed": False, "detail": "memory/user_prefs.json missing"})
    except Exception as e:
        checks.append({"name": "stale_memory_overwritten", "passed": False, "detail": str(e)})

    # CHECK 20: Decoy workspaces were NOT polluted (workspace-old-archive-2023 should not have master content)
    try:
        decoy_agents = os.path.join(HOME, ".openclaw", "workspace-old-archive-2023", "AGENTS.md")
        if os.path.isfile(decoy_agents):
            with open(decoy_agents) as f:
                content = f.read()
            not_polluted = "version: 2.1.0" not in content
            checks.append({
                "name": "decoy_workspace_not_polluted",
                "passed": not_polluted,
                "detail": f"workspace-old-archive-2023: {'not polluted' if not_polluted else 'INCORRECTLY overwritten with master content'}"
            })
        else:
            checks.append({"name": "decoy_workspace_not_polluted", "passed": True, "detail": "Decoy workspace unchanged"})
    except Exception as e:
        checks.append({"name": "decoy_workspace_not_polluted", "passed": False, "detail": str(e)})

    # --- Score Calculation ---
    # Weighted scoring:
    # - Dynamic workspace existence: 5%
    # - 7 config files synced correctly: 35% (5% each)
    # - Stale overwrite verification: 5%
    # - Skills sync (5 files): 25% (5% each)
    # - Stale skill overwrite: 5%
    # - Memory sync (3 files): 15% (5% each)
    # - Stale memory overwrite: 5%
    # - Decoy not polluted: 5%

    weights = {
        "dynamic_workspace_exists_at_correct_path": 0.05,
        "config_sync_AGENTS.md": 0.05,
        "config_sync_SOUL.md": 0.05,
        "config_sync_TOOLS.md": 0.05,
        "config_sync_IDENTITY.md": 0.05,
        "config_sync_USER.md": 0.05,
        "config_sync_HEARTBEAT.md": 0.05,
        "config_sync_MEMORY.md": 0.05,
        "stale_agents_overwritten": 0.05,
        "skills_sync_greet.js": 0.05,
        "skills_sync_faq.js": 0.05,
        "skills_sync_escalate.js": 0.05,
        "skills_sync_ticket.js": 0.05,
        "skills_sync_survey.js": 0.05,
        "stale_skill_overwritten": 0.05,
        "memory_sync_user_prefs.json": 0.05,
        "memory_sync_session_cache.json": 0.05,
        "memory_sync_knowledge_base.json": 0.05,
        "stale_memory_overwritten": 0.05,
        "decoy_workspace_not_polluted": 0.05,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            score += w

    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))