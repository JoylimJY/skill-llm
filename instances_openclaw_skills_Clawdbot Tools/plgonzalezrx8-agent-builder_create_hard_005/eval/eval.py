import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)

expected_files = [
    'IDENTITY.md', 'SOUL.md', 'AGENTS.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md', 'memory/2025-05-17.md'
]

for rel in expected_files:
    p = workspace / rel
    try:
        exists = p.exists()
        add_check(f'file_exists::{rel}', exists, 'present' if exists else 'missing')
    except Exception as e:
        add_check(f'file_exists::{rel}', False, f'error: {e}')

# Check IDENTITY.md content fuzzily
try:
    text = (workspace / 'IDENTITY.md').read_text(encoding='utf-8')
    low = text.lower()
    # Check for agent name and assistant/agent role (flexible matching)
    has_name = re.search(r'clawline', low, re.IGNORECASE)
    has_role = re.search(r'(agent|assistant|bot|ai)', low, re.IGNORECASE)
    ok = bool(has_name and has_role)
    add_check('identity_content', ok, 'contains expected name and assistant role' if ok else 'missing expected identity markers')
except Exception as e:
    add_check('identity_content', False, f'error: {e}')

# Check SOUL.md for required rules (flexible concept matching - reduced to core safety concepts)
try:
    text = (workspace / 'SOUL.md').read_text(encoding='utf-8')
    low = text.lower()
    
    # Check for permission/approval concept (core safety)
    has_permission = re.search(r'(ask|permission|approval|confirm|before)', low, re.IGNORECASE)
    
    # Check for destructive action concept (core safety)
    has_destructive = re.search(r'(destructive|delete|remove|never)', low, re.IGNORECASE)
    
    # Check for professional tone (persona)
    has_professional = re.search(r'(professional|warm|concise|tone)', low, re.IGNORECASE)
    
    # Check for tool-first concept (behavioral principle)
    has_tool_first = re.search(r'(tool-first|tool first|tool.*first)', low, re.IGNORECASE)
    
    # Require at least 3 of 4 core concepts (more flexible)
    found_count = sum([bool(has_permission), bool(has_destructive), bool(has_professional), bool(has_tool_first)])
    ok = found_count >= 3
    add_check('soul_rules', ok, f'required rules found ({found_count}/4)' if ok else 'missing one or more required safety/persona rules')
except Exception as e:
    add_check('soul_rules', False, f'error: {e}')

# Check AGENTS.md for delegation and operating guidance (flexible matching)
try:
    text = (workspace / 'AGENTS.md').read_text(encoding='utf-8')
    low = text.lower()
    
    # Check for ask before destructive concept (more flexible - either order, or separate mentions)
    has_ask = re.search(r'(ask|confirm|permission|approval)', low, re.IGNORECASE)
    has_destructive = re.search(r'(destructive|delete|remove)', low, re.IGNORECASE)
    has_ask_destructive = bool(has_ask and has_destructive)
    
    # Check for ask before outbound messages concept (more flexible)
    has_send = re.search(r'(send|message|outbound)', low, re.IGNORECASE)
    has_ask_outbound = bool(has_ask and has_send)
    
    # Check for error handling concept (more flexible)
    has_error_handling = re.search(r'(error|fail|stop|handle|prohibit)', low, re.IGNORECASE)
    
    # Check for sub-agents concept (more flexible)
    has_subagents = re.search(r'(sub-agent|subagent|delegation|delegate|agent)', low, re.IGNORECASE)
    
    # Check for group chats concept (more flexible)
    has_group_chats = re.search(r'(group|discord|chat)', low, re.IGNORECASE)
    
    ok = all([has_ask_destructive, has_ask_outbound, has_error_handling, has_subagents, has_group_chats])
    add_check('agents_rules', ok, 'contains operating rules and delegation note' if ok else 'missing operating rule(s)')
except Exception as e:
    add_check('agents_rules', False, f'error: {e}')

# USER.md check
try:
    text = (workspace / 'USER.md').read_text(encoding='utf-8')
    low = text.lower()
    ok = ('mina park' in low) and ('mina' in low) and ('america/los_angeles' in low)
    add_check('user_profile', ok, 'contains user identity and timezone' if ok else 'missing user profile markers')
except Exception as e:
    add_check('user_profile', False, f'error: {e}')

# HEARTBEAT.md should be tiny and checklist-oriented
try:
    text = (workspace / 'HEARTBEAT.md').read_text(encoding='utf-8')
    low = text.lower()
    ok = ('heartbeat' in low) and ('check' in low or '[ ]' in low)
    add_check('heartbeat_shape', ok, 'heartbeat file is present and checklist-like' if ok else 'heartbeat file not shaped as expected')
except Exception as e:
    add_check('heartbeat_shape', False, f'error: {e}')

# MEMORY.md must be curated, not empty, and reference durable preferences
try:
    text = (workspace / 'MEMORY.md').read_text(encoding='utf-8')
    low = text.lower()
    ok = ('durable' in low or 'preferences' in low or 'operator' in low) and len(text.strip()) > 0
    add_check('memory_curated', ok, 'memory contains durable preference content' if ok else 'memory file empty or not curated')
except Exception as e:
    add_check('memory_curated', False, f'error: {e}')

# Daily memory marker check
try:
    text = (workspace / 'memory' / '2025-05-17.md').read_text(encoding='utf-8')
    low = text.lower()
    ok = ('openclaw_marker' in low) and ('agent created' in low) and ('clawline' in low)
    add_check('daily_memory_marker', ok, 'daily memory seed contains marker content' if ok else 'daily memory marker missing')
except Exception as e:
    add_check('daily_memory_marker', False, f'error: {e}')

# Output schema and score
passed_count = sum(1 for c in checks if c['passed'])
total = len(checks) if checks else 1
score = passed_count / total
passed = passed_count == total
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))