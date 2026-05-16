#!/usr/bin/env python3
"""
Evaluation script for agent-extract task.
Checks that the agent correctly split the social-monitor skill into an independent agent.
"""
import json
import os
import sys
from pathlib import Path

HOME = os.path.expanduser("~")
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: New agent entry exists in openclaw.json
# ─────────────────────────────────────────────────────────────────────────────
new_agent_id = None
new_workspace_path = None
try:
    config_path = os.path.join(OPENCLAW_DIR, "openclaw.json")
    with open(config_path) as f:
        config = json.load(f)
    
    agents_list = config.get("agents", {}).get("list", [])
    # Find any agent that is NOT "main"
    new_agents = [a for a in agents_list if a.get("id") != "main"]
    
    if not new_agents:
        add_check("new_agent_in_config", False, 
                  "No new agent found in agents.list (only 'main' exists). Agent must add a new entry under agents.list.", 
                  weight=2.0)
    else:
        new_agent = new_agents[0]
        new_agent_id = new_agent.get("id")
        new_workspace_path = new_agent.get("workspace", "")
        
        has_id = bool(new_agent_id)
        has_name = bool(new_agent.get("name"))
        has_workspace = bool(new_workspace_path)
        
        all_fields = has_id and has_name and has_workspace
        add_check("new_agent_in_config", all_fields,
                  f"New agent found: id={new_agent_id}, name={new_agent.get('name')}, workspace={new_workspace_path}. "
                  f"Fields present: id={has_id}, name={has_name}, workspace={has_workspace}",
                  weight=2.0)
except Exception as e:
    add_check("new_agent_in_config", False, f"Exception reading openclaw.json: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: New workspace follows naming convention workspace-<new-agent-id>
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_agent_id:
        expected_workspace_suffix = f"workspace-{new_agent_id}"
        workspace_correct = (
            new_workspace_path and 
            (new_workspace_path.endswith(expected_workspace_suffix) or 
             f"workspace-{new_agent_id}" in new_workspace_path)
        )
        workspace_exists = new_workspace_path and os.path.isdir(new_workspace_path)
        add_check("new_workspace_naming", workspace_correct and workspace_exists,
                  f"Expected workspace path containing 'workspace-{new_agent_id}'. "
                  f"Got: '{new_workspace_path}'. Exists: {workspace_exists}",
                  weight=1.0)
    else:
        add_check("new_workspace_naming", False, "Cannot check workspace naming: new_agent_id unknown.", weight=1.0)
except Exception as e:
    add_check("new_workspace_naming", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: New workspace has required subdirectories (memory, skills)
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_workspace_path and os.path.isdir(new_workspace_path):
        memory_dir = os.path.join(new_workspace_path, "memory")
        skills_dir = os.path.join(new_workspace_path, "skills")
        has_memory = os.path.isdir(memory_dir)
        has_skills = os.path.isdir(skills_dir)
        add_check("new_workspace_subdirs", has_memory and has_skills,
                  f"memory/ exists: {has_memory}, skills/ exists: {has_skills}", weight=1.0)
    else:
        add_check("new_workspace_subdirs", False, 
                  f"New workspace does not exist at {new_workspace_path}", weight=1.0)
except Exception as e:
    add_check("new_workspace_subdirs", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: Identity files COPIED to new workspace (SOUL.md, IDENTITY.md, AGENTS.md)
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_workspace_path and os.path.isdir(new_workspace_path):
        soul_new = os.path.join(new_workspace_path, "SOUL.md")
        identity_new = os.path.join(new_workspace_path, "IDENTITY.md")
        agents_new = os.path.join(new_workspace_path, "AGENTS.md")
        
        soul_ok = os.path.isfile(soul_new)
        identity_ok = os.path.isfile(identity_new)
        agents_ok = os.path.isfile(agents_new)
        
        add_check("identity_files_copied_to_new", soul_ok and identity_ok and agents_ok,
                  f"SOUL.md={soul_ok}, IDENTITY.md={identity_ok}, AGENTS.md={agents_ok} in new workspace",
                  weight=1.5)
    else:
        add_check("identity_files_copied_to_new", False, "New workspace not found.", weight=1.5)
except Exception as e:
    add_check("identity_files_copied_to_new", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Original identity files STILL EXIST in main workspace (copy, not move)
# ─────────────────────────────────────────────────────────────────────────────
try:
    main_workspace = os.path.join(OPENCLAW_DIR, "workspace")
    soul_main = os.path.isfile(os.path.join(main_workspace, "SOUL.md"))
    identity_main = os.path.isfile(os.path.join(main_workspace, "IDENTITY.md"))
    agents_main = os.path.isfile(os.path.join(main_workspace, "AGENTS.md"))
    
    add_check("original_identity_files_preserved", soul_main and identity_main and agents_main,
              f"Main workspace: SOUL.md={soul_main}, IDENTITY.md={identity_main}, AGENTS.md={agents_main}. "
              f"All must remain (copy, NOT move).",
              weight=2.0)
except Exception as e:
    add_check("original_identity_files_preserved", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: social-monitor skill copied to new workspace/skills/
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_workspace_path and os.path.isdir(new_workspace_path):
        new_skill_dir = os.path.join(new_workspace_path, "skills", "social-monitor")
        skill_json_exists = os.path.isfile(os.path.join(new_skill_dir, "skill.json"))
        skill_md_exists = os.path.isfile(os.path.join(new_skill_dir, "SKILL.md"))
        
        add_check("social_monitor_skill_copied", skill_json_exists and skill_md_exists,
                  f"New workspace skills/social-monitor/: skill.json={skill_json_exists}, SKILL.md={skill_md_exists}",
                  weight=1.5)
    else:
        add_check("social_monitor_skill_copied", False, "New workspace not found.", weight=1.5)
except Exception as e:
    add_check("social_monitor_skill_copied", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: social-monitor skill STILL EXISTS in main workspace (copy not move)
# ─────────────────────────────────────────────────────────────────────────────
try:
    main_skill_dir = os.path.join(OPENCLAW_DIR, "workspace", "skills", "social-monitor")
    main_skill_exists = os.path.isdir(main_skill_dir)
    add_check("original_skill_preserved_in_main", main_skill_exists,
              f"Main workspace skills/social-monitor/ still exists: {main_skill_exists}",
              weight=2.0)
except Exception as e:
    add_check("original_skill_preserved_in_main", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: New workspace has HEARTBEAT.md with social-monitor tasks
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_workspace_path and os.path.isdir(new_workspace_path):
        new_heartbeat = os.path.join(new_workspace_path, "HEARTBEAT.md")
        if os.path.isfile(new_heartbeat):
            with open(new_heartbeat) as f:
                content = f.read().lower()
            # Should contain social-monitor related content
            has_social = any(kw in content for kw in [
                "social", "weibo", "twitter", "linkedin", "monitor", "brand", "mention"
            ])
            add_check("new_heartbeat_has_social_tasks", has_social,
                      f"New HEARTBEAT.md exists. Contains social monitoring content: {has_social}. "
                      f"(Checked for: social/weibo/twitter/linkedin/monitor/brand/mention)",
                      weight=2.0)
        else:
            add_check("new_heartbeat_has_social_tasks", False,
                      "No HEARTBEAT.md found in new workspace.", weight=2.0)
    else:
        add_check("new_heartbeat_has_social_tasks", False, "New workspace not found.", weight=2.0)
except Exception as e:
    add_check("new_heartbeat_has_social_tasks", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: Main workspace HEARTBEAT.md cleaned of social-monitor tasks
# ─────────────────────────────────────────────────────────────────────────────
try:
    main_heartbeat_path = os.path.join(OPENCLAW_DIR, "workspace", "HEARTBEAT.md")
    if os.path.isfile(main_heartbeat_path):
        with open(main_heartbeat_path) as f:
            content = f.read().lower()
        # Should NOT contain social monitor tasks anymore
        social_keywords = ["weibo", "twitter", "linkedin", "betacorp", "brand health", 
                           "social monitor", "social-monitor", "品牌健康"]
        still_has_social = any(kw in content for kw in social_keywords)
        
        # Should still exist as a file (just cleaned)
        is_empty_or_clean = not still_has_social
        add_check("main_heartbeat_cleaned", is_empty_or_clean,
                  f"Main HEARTBEAT.md still contains social keywords: {still_has_social}. "
                  f"Checked for: {social_keywords}. File must be updated to remove social-monitor tasks.",
                  weight=2.0)
    else:
        # File deleted entirely is acceptable if it's been replaced
        add_check("main_heartbeat_cleaned", True,
                  "Main HEARTBEAT.md was removed entirely (acceptable if social tasks moved to new agent).",
                  weight=2.0)
except Exception as e:
    add_check("main_heartbeat_cleaned", False, f"Exception: {e}", weight=2.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: Cron job created for new agent with correct proprietary parameters
# ─────────────────────────────────────────────────────────────────────────────
try:
    cron_path = os.path.join(OPENCLAW_DIR, "cron", "jobs.json")
    with open(cron_path) as f:
        cron_data = json.load(f)
    
    jobs = cron_data.get("jobs", [])
    new_jobs = [j for j in jobs if j.get("agentId") == new_agent_id]
    
    if not new_jobs:
        add_check("cron_job_created_for_new_agent", False,
                  f"No cron job found for agent '{new_agent_id}'. Found agentIds: {[j.get('agentId') for j in jobs]}",
                  weight=3.0)
    else:
        job = new_jobs[0]
        # Check session target is "isolated"
        session_target_ok = job.get("sessionTarget") == "isolated"
        # Check session key follows format "agent:<new-agent-id>:main"
        expected_session_key = f"agent:{new_agent_id}:main"
        session_key_ok = job.get("sessionKey") == expected_session_key
        # Check delivery mode is "announce"
        delivery_ok = job.get("delivery", {}).get("mode") == "announce"
        # Check schedule is reasonable (every X ms, should be for 30m = 1800000ms)
        schedule_ok = job.get("schedule", {}).get("kind") == "every"
        
        all_ok = session_target_ok and session_key_ok and delivery_ok and schedule_ok
        detail = (
            f"Job found for agent '{new_agent_id}'. "
            f"sessionTarget='isolated': {session_target_ok} (got: {job.get('sessionTarget')}). "
            f"sessionKey='{expected_session_key}': {session_key_ok} (got: {job.get('sessionKey')}). "
            f"delivery.mode='announce': {delivery_ok} (got: {job.get('delivery',{}).get('mode')}). "
            f"schedule.kind='every': {schedule_ok}."
        )
        add_check("cron_job_created_for_new_agent", all_ok, detail, weight=3.0)
except Exception as e:
    add_check("cron_job_created_for_new_agent", False, f"Exception reading cron jobs: {e}", weight=3.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 11: channels config untouched in openclaw.json
# ─────────────────────────────────────────────────────────────────────────────
try:
    config_path = os.path.join(OPENCLAW_DIR, "openclaw.json")
    with open(config_path) as f:
        config = json.load(f)
    
    channels = config.get("channels", {})
    slack_ok = channels.get("slack", {}).get("enabled") == True
    slack_channel_ok = channels.get("slack", {}).get("default_channel") == "#ai-assistant"
    
    add_check("channels_config_untouched", slack_ok and slack_channel_ok,
              f"Channels config intact: slack.enabled={slack_ok}, default_channel={slack_channel_ok}",
              weight=1.0)
except Exception as e:
    add_check("channels_config_untouched", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 12: Main agent sessions.json untouched
# ─────────────────────────────────────────────────────────────────────────────
try:
    sessions_path = os.path.join(OPENCLAW_DIR, "agents", "main", "sessions", "sessions.json")
    with open(sessions_path) as f:
        sessions = json.load(f)
    
    has_main_default = "main:default" in sessions
    has_main_calendar = "main:calendar" in sessions
    
    add_check("main_sessions_untouched", has_main_default and has_main_calendar,
              f"main:default={has_main_default}, main:calendar={has_main_calendar}. "
              f"Original sessions must remain unchanged.",
              weight=1.5)
except Exception as e:
    add_check("main_sessions_untouched", False, f"Exception: {e}", weight=1.5)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 13: Memory files copied to new workspace
# ─────────────────────────────────────────────────────────────────────────────
try:
    if new_workspace_path and os.path.isdir(new_workspace_path):
        new_memory_dir = os.path.join(new_workspace_path, "memory")
        if os.path.isdir(new_memory_dir):
            memory_files = list(Path(new_memory_dir).glob("*.md"))
            has_memory = len(memory_files) > 0
            add_check("memory_files_copied", has_memory,
                      f"Memory files in new workspace/memory/: {[f.name for f in memory_files]}",
                      weight=1.0)
        else:
            add_check("memory_files_copied", False, 
                      "No memory/ directory in new workspace.", weight=1.0)
    else:
        add_check("memory_files_copied", False, "New workspace not found.", weight=1.0)
except Exception as e:
    add_check("memory_files_copied", False, f"Exception: {e}", weight=1.0)

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SCORING
# ─────────────────────────────────────────────────────────────────────────────
final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
passed = final_score >= 0.80

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, indent=2))
sys.exit(0 if passed else 1)