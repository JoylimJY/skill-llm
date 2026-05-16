#!/usr/bin/env python3
"""
Evaluation script for the memory-hub write+search+merge task.
Usage: python3 eval_script.py <workspace_dir>  (workspace_dir is ignored; we use fixed paths)
"""
import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

results = []

def check(name, passed, detail):
    results.append({"name": name, "passed": passed, "detail": detail})
    return passed

HOME = Path.home()
SHARED_MEM = HOME / ".openclaw" / "shared-memory"
WORKSPACE = HOME / ".openclaw" / "workspace"
KNOWLEDGE_FILE = SHARED_MEM / "KNOWLEDGE.md"
CACHE_FILE = WORKSPACE / "SHARED_MEMORY_CACHE.md"
CONFIG_FILE = SHARED_MEM / "config.json"
BARE_REPO = HOME / ".openclaw" / "_bare_remote"

# ────────────────────────────────────────────────────────────────────────────
# CHECK 1: KNOWLEDGE.md contains a new entry about Helm/values override
#          (the task asks to record a lesson about Helm chart values override)
# ────────────────────────────────────────────────────────────────────────────
try:
    knowledge_text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    # Must contain a new section header with [分类] pattern
    new_sections = re.findall(r'^## \[.+?\] .+', knowledge_text, re.MULTILINE)
    # We expect at least 3 sections (2 original + 1 new)
    has_new_entry = len(new_sections) >= 3
    check("knowledge_new_entry_exists",
          has_new_entry,
          f"Found {len(new_sections)} section(s) in KNOWLEDGE.md. Expected ≥3 (2 original + 1 new). Sections: {new_sections}")
except Exception as e:
    check("knowledge_new_entry_exists", False, f"Exception reading KNOWLEDGE.md: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 2: New entry follows the strict proprietary format:
#   ## [分类] 标题
#   content (1-5 lines)
#   _更新：YYYY-MM-DD by agent_id_
# ────────────────────────────────────────────────────────────────────────────
try:
    knowledge_text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    # Split into sections
    sections = re.split(r'\n(?=## \[)', knowledge_text)
    
    format_ok = False
    format_details = []
    
    # Find sections that are NOT the two original ones
    original_titles = [
        "Docker 多阶段构建缓存",
        "Kubernetes HPA 冷启动"
    ]
    
    for section in sections:
        if not section.strip():
            continue
        # Check if it's a new section (not one of the originals)
        is_original = any(orig in section for orig in original_titles)
        if is_original:
            continue
        if not section.startswith("## ["):
            continue
        
        lines = [l for l in section.strip().split('\n') if l.strip()]
        
        # Rule 1: header matches ## [分类] 标题
        header_ok = bool(re.match(r'^## \[.+?\] .+', lines[0]))
        
        # Rule 2: last non-empty line must be _更新：YYYY-MM-DD by <agent_id>_
        last_line = lines[-1].strip()
        update_ok = bool(re.match(r'^_更新：\d{4}-\d{2}-\d{2} by .+_$', last_line))
        
        # Rule 3: content between header and footer: 1-5 lines
        content_lines = lines[1:-1]
        content_ok = 1 <= len(content_lines) <= 5
        
        format_details.append(
            f"Section: '{lines[0]}' | header_ok={header_ok} | "
            f"update_ok={update_ok} | content_lines={len(content_lines)} content_ok={content_ok}"
        )
        
        if header_ok and update_ok and content_ok:
            format_ok = True
    
    check("new_entry_format_correct",
          format_ok,
          f"Format check details: {format_details}")
except Exception as e:
    check("new_entry_format_correct", False, f"Exception during format check: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 3: agent_id in the new entry footer matches config.json agent_id
# ────────────────────────────────────────────────────────────────────────────
try:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    agent_id = config.get("agent_id", "")
    knowledge_text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    
    # Find all _更新：... by ..._ lines
    update_lines = re.findall(r'_更新：\d{4}-\d{2}-\d{2} by (.+?)_', knowledge_text)
    new_update_lines = [l for l in update_lines if l.strip() == agent_id]
    
    # Must have at least one entry with matching agent_id (the new one)
    has_agent_id = len(new_update_lines) >= 1
    check("new_entry_uses_correct_agent_id",
          has_agent_id,
          f"Expected agent_id='{agent_id}' in new entry footer. "
          f"Found agent_ids in update lines: {update_lines}")
except Exception as e:
    check("new_entry_uses_correct_agent_id", False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 4: git log shows a commit with the proprietary message format
#   🧠 [agent_id] 更新 KNOWLEDGE.md: <description>
# ────────────────────────────────────────────────────────────────────────────
try:
    log = subprocess.run(
        ["git", "-C", str(SHARED_MEM), "log", "--oneline", "-10"],
        capture_output=True, text=True
    )
    commit_messages = log.stdout.strip()
    
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    agent_id = config.get("agent_id", "agent-devops")
    
    # Pattern: 🧠 [agent_id] 更新 KNOWLEDGE.md: ...
    pattern = r'🧠 \[' + re.escape(agent_id) + r'\] 更新 KNOWLEDGE\.md: .+'
    commit_ok = bool(re.search(pattern, commit_messages))
    
    check("git_commit_message_format",
          commit_ok,
          f"Expected commit matching pattern '{pattern}'. "
          f"Recent commits:\n{commit_messages}")
except Exception as e:
    check("git_commit_message_format", False, f"Exception reading git log: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 5: SHARED_MEMORY_CACHE.md has been refreshed (not stale)
#   - Must contain all 4 file sections
#   - Must be more complete than the stale version
# ────────────────────────────────────────────────────────────────────────────
try:
    cache_text = CACHE_FILE.read_text(encoding="utf-8")
    
    has_user = "USER.md" in cache_text
    has_knowledge = "KNOWLEDGE.md" in cache_text
    has_rules = "RULES.md" in cache_text
    has_tools = "TOOLS.md" in cache_text
    
    all_sections = has_user and has_knowledge and has_rules and has_tools
    
    # Must have more content than the stale version (stale was ~200 chars)
    is_enriched = len(cache_text) > 300
    
    check("cache_has_all_four_sections",
          all_sections,
          f"Cache sections: USER={has_user}, KNOWLEDGE={has_knowledge}, "
          f"RULES={has_rules}, TOOLS={has_tools}. Cache length: {len(cache_text)}")
    
    check("cache_is_enriched_beyond_stale",
          is_enriched,
          f"Cache length={len(cache_text)}, must be >300 chars to indicate enrichment.")
except Exception as e:
    check("cache_has_all_four_sections", False, f"Exception reading cache: {e}")
    check("cache_is_enriched_beyond_stale", False, f"Exception reading cache: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 6: config.json last_sync has been updated to a recent timestamp
# ────────────────────────────────────────────────────────────────────────────
try:
    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    last_sync_str = config.get("last_sync", "")
    
    # Parse the timestamp
    try:
        last_sync_dt = datetime.fromisoformat(last_sync_str)
    except Exception:
        # Try dateutil as fallback
        from dateutil import parser as du_parser
        last_sync_dt = du_parser.parse(last_sync_str)
    
    now = datetime.utcnow()
    # Must be within the last 24 hours (task was just run)
    age_hours = (now - last_sync_dt).total_seconds() / 3600
    is_recent = age_hours < 24
    
    check("config_last_sync_updated",
          is_recent,
          f"last_sync='{last_sync_str}', age={age_hours:.1f}h. Must be <24h old.")
except Exception as e:
    check("config_last_sync_updated", False, f"Exception parsing last_sync: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 7: No new files were added to the shared-memory repo
#          (SKILL.md explicitly forbids adding new files)
# ────────────────────────────────────────────────────────────────────────────
try:
    allowed_files = {"USER.md", "KNOWLEDGE.md", "RULES.md", "TOOLS.md", "config.json"}
    actual_files = set()
    for f in SHARED_MEM.iterdir():
        if f.name == ".git":
            continue
        actual_files.add(f.name)
    
    unexpected = actual_files - allowed_files
    no_new_files = len(unexpected) == 0
    
    check("no_unauthorized_new_files",
          no_new_files,
          f"Unexpected files in shared-memory repo: {unexpected}. "
          f"Allowed: {allowed_files}. Found: {actual_files}")
except Exception as e:
    check("no_unauthorized_new_files", False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────────────
# CHECK 8: Original entries were NOT deleted (dedup: update not delete)
# ────────────────────────────────────────────────────────────────────────────
try:
    knowledge_text = KNOWLEDGE_FILE.read_text(encoding="utf-8")
    has_docker = "Docker 多阶段构建缓存" in knowledge_text
    has_hpa = "Kubernetes HPA 冷启动" in knowledge_text
    
    originals_preserved = has_docker and has_hpa
    check("original_entries_preserved",
          originals_preserved,
          f"Original entries: Docker={has_docker}, HPA={has_hpa}. "
          "Both must be preserved (no deletion allowed).")
except Exception as e:
    check("original_entries_preserved", False, f"Exception: {e}")

# ────────────────────────────────────────────────────────────────────────────
# SCORING
# ────────────────────────────────────────────────────────────────────────────
total = len(results)
passed_count = sum(1 for r in results if r["passed"])
score = round(passed_count / total, 4)
final_passed = passed_count >= 6  # Need at least 6/8 to pass

output = {
    "passed": final_passed,
    "score": score,
    "checks": results
}

print(json.dumps(output, indent=2, ensure_ascii=False))
sys.exit(0 if final_passed else 1)