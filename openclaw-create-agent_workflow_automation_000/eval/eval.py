#!/usr/bin/env python3
"""
Evaluation script for create-agent skill task (functional agent: dq-sentinel).
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
    global total_score, max_score
    checks.append({"name": name, "passed": passed, "detail": detail})
    max_score += weight
    if passed:
        total_score += weight

# ─── Locate agent workspace ───────────────────────────────────────────────────
AGENT_ID = "dq-sentinel"
agent_base = workspace / ".openclaw/agency-agents" / AGENT_ID

# ─── CHECK 1: create_workspace.sh called with --type functional ───────────────
try:
    type_file = agent_base / ".workspace_type"
    if type_file.exists():
        wtype = type_file.read_text().strip()
        passed = (wtype == "functional")
        add_check(
            "create_workspace called with --type functional",
            passed,
            f"Workspace type recorded as '{wtype}'" if type_file.exists() else "Workspace type file missing",
            weight=2.0
        )
    else:
        add_check(
            "create_workspace called with --type functional",
            False,
            f"Workspace type sentinel file not found at {type_file}. Script may not have been called.",
            weight=2.0
        )
except Exception as e:
    add_check("create_workspace called with --type functional", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 2: Agent directory exists ─────────────────────────────────────────
try:
    exists = agent_base.is_dir()
    add_check(
        "Agent workspace directory created",
        exists,
        f"Directory {'exists' if exists else 'MISSING'}: {agent_base}",
        weight=1.0
    )
except Exception as e:
    add_check("Agent workspace directory created", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 3: IDENTITY.md exists and has content ─────────────────────────────
try:
    idfile = agent_base / "IDENTITY.md"
    content = idfile.read_text() if idfile.exists() else ""
    has_name = bool(re.search(r'Name.*dq.sentinel|名字.*dq.sentinel|dq-sentinel', content, re.IGNORECASE))
    has_emoji = bool(re.search(r'Emoji|emoji|[^\x00-\x7F]', content))
    passed = idfile.exists() and len(content.strip()) > 30 and has_name
    add_check(
        "IDENTITY.md created with agent name",
        passed,
        f"Exists: {idfile.exists()}, length: {len(content)}, has name: {has_name}, has emoji: {has_emoji}",
        weight=1.0
    )
except Exception as e:
    add_check("IDENTITY.md created with agent name", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 4: SOUL.md is functional-style (professional, no comm style) ──────
try:
    soul_file = agent_base / "SOUL.md"
    soul = soul_file.read_text() if soul_file.exists() else ""
    # Functional SOUL should NOT contain bootstrap placeholder notes
    has_bootstrap_placeholder = bool(re.search(r'BOOTSTRAP|bootstrap', soul))
    # Should NOT be a skeleton (should have actual content)
    is_skeleton_only = len(soul.strip()) < 80
    # Should NOT contain comm-style phrases typical for human agents
    comm_style_phrases = ['语气', '沟通风格', '个人偏好', 'BOOTSTRAP 执行后']
    has_comm_style = any(p in soul for p in comm_style_phrases)
    # Should contain professional judgment language
    professional_keywords = ['判断', '质量', '专业', '数据', '检测', '报告', '准确', '严谨', '执念', '警觉', 'data', 'quality']
    has_professional = any(k in soul.lower() for k in professional_keywords)
    
    passed = (soul_file.exists() 
              and not is_skeleton_only 
              and not has_comm_style 
              and not has_bootstrap_placeholder
              and has_professional)
    add_check(
        "SOUL.md is full functional-style (professional judgment, not skeleton)",
        passed,
        f"Exists: {soul_file.exists()}, length: {len(soul)}, skeleton: {is_skeleton_only}, "
        f"has_comm_style: {has_comm_style}, has_bootstrap_placeholder: {has_bootstrap_placeholder}, "
        f"has_professional: {has_professional}",
        weight=2.0
    )
except Exception as e:
    add_check("SOUL.md is full functional-style", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 5: AGENTS.md has required 4 parts for functional agent ─────────────
try:
    agents_file = agent_base / "AGENTS.md"
    agents = agents_file.read_text() if agents_file.exists() else ""
    
    # Must have: core duty, accepted input section, output spec section, boundary declaration
    has_core_duty = bool(re.search(r'核心职责|core|职责|能力', agents, re.IGNORECASE))
    has_input_spec = bool(re.search(r'接受.*输入|输入.*规范|accepted.*input|input.*spec', agents, re.IGNORECASE))
    has_output_spec = bool(re.search(r'输出.*规范|output.*spec|返回.*格式|输出格式', agents, re.IGNORECASE))
    has_boundary = bool(re.search(r'边界|不处理|不做|boundary|超出', agents, re.IGNORECASE))
    has_memory_rules = bool(re.search(r'记忆规则|触发式写入|Heartbeat|heartbeat', agents, re.IGNORECASE))
    has_first_dialogue = bool(re.search(r'首次对话|first.*dialogue|能力声明|能力边界', agents, re.IGNORECASE))

    parts_count = sum([has_core_duty, has_input_spec, has_output_spec, has_boundary])
    passed = agents_file.exists() and parts_count >= 3 and has_memory_rules
    add_check(
        "AGENTS.md has functional agent structure (core duty, input, output, boundary, memory rules)",
        passed,
        f"Exists: {agents_file.exists()}, core_duty: {has_core_duty}, input_spec: {has_input_spec}, "
        f"output_spec: {has_output_spec}, boundary: {has_boundary}, memory_rules: {has_memory_rules}, "
        f"first_dialogue: {has_first_dialogue}, parts_count: {parts_count}/4",
        weight=2.0
    )
except Exception as e:
    add_check("AGENTS.md functional structure", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 6: TOOLS.md with per-tool sections ─────────────────────────────────
try:
    tools_file = agent_base / "TOOLS.md"
    tools = tools_file.read_text() if tools_file.exists() else ""
    # Must mention at least some of the expected tools
    expected_tools = ['db_query_executor', 'pipeline_status_checker', 'data_quality_reporter', 'schema_validator']
    found_tools = [t for t in expected_tools if t in tools]
    # Must have 用途 / 什么时候不用 pattern
    has_when_not = bool(re.search(r'什么时候不用|when.*not|不.*使用|不.*调用', tools, re.IGNORECASE))
    passed = tools_file.exists() and len(found_tools) >= 2 and has_when_not
    add_check(
        "TOOLS.md created with tool descriptions including 'when NOT to use'",
        passed,
        f"Exists: {tools_file.exists()}, found_tools: {found_tools}, has_when_not: {has_when_not}",
        weight=1.5
    )
except Exception as e:
    add_check("TOOLS.md with when-not-to-use", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 7: MEMORY.md with domain knowledge orientation ────────────────────
try:
    mem_file = agent_base / "MEMORY.md"
    mem = mem_file.read_text() if mem_file.exists() else ""
    has_company = bool(re.search(r'DataFlux|公司', mem))
    has_domain = bool(re.search(r'领域知识|任务经验|domain|task', mem, re.IGNORECASE))
    has_agent_id = 'dq-sentinel' in mem
    has_type = bool(re.search(r'功能型|functional', mem, re.IGNORECASE))
    passed = mem_file.exists() and has_company and (has_domain or has_agent_id)
    add_check(
        "MEMORY.md with company info and domain knowledge structure",
        passed,
        f"Exists: {mem_file.exists()}, has_company: {has_company}, has_domain: {has_domain}, "
        f"has_agent_id: {has_agent_id}, has_type: {has_type}",
        weight=1.0
    )
except Exception as e:
    add_check("MEMORY.md domain knowledge", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 8: HEARTBEAT.md exists with task-focused content ──────────────────
try:
    hb_file = agent_base / "HEARTBEAT.md"
    hb = hb_file.read_text() if hb_file.exists() else ""
    has_task_focus = bool(re.search(r'任务知识|task|领域|domain|3天|3 天|every 3', hb, re.IGNORECASE))
    passed = hb_file.exists() and len(hb.strip()) > 50 and has_task_focus
    add_check(
        "HEARTBEAT.md exists with task-knowledge refinement focus",
        passed,
        f"Exists: {hb_file.exists()}, length: {len(hb)}, task_focus: {has_task_focus}",
        weight=1.0
    )
except Exception as e:
    add_check("HEARTBEAT.md task focus", False, f"Exception: {e}", weight=1.0)

# ─── CHECK 9: NO BOOTSTRAP.md generated (functional agent must NOT have it) ───
try:
    bootstrap_file = agent_base / "BOOTSTRAP.md"
    no_bootstrap = not bootstrap_file.exists()
    add_check(
        "BOOTSTRAP.md correctly NOT generated (functional agent)",
        no_bootstrap,
        f"BOOTSTRAP.md {'correctly absent' if no_bootstrap else 'INCORRECTLY PRESENT — functional agents must not have BOOTSTRAP.md'}",
        weight=2.0
    )
except Exception as e:
    add_check("No BOOTSTRAP.md for functional agent", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 10: NO USER.md generated (functional agent must NOT have it) ───────
try:
    user_file = agent_base / "USER.md"
    no_user = not user_file.exists()
    add_check(
        "USER.md correctly NOT generated (functional agent)",
        no_user,
        f"USER.md {'correctly absent' if no_user else 'INCORRECTLY PRESENT — functional agents must not have USER.md'}",
        weight=1.5
    )
except Exception as e:
    add_check("No USER.md for functional agent", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 11: register_agent.py called correctly ─────────────────────────────
try:
    record_file = workspace / "tmp/register_call.json"
    if record_file.exists():
        record = json.loads(record_file.read_text())
        correct_id = record.get("agent_id") == "dq-sentinel"
        correct_parent = record.get("parent_id") == "master-agent"
        also_allow = record.get("also_allow", [])
        expected_tools_register = {'db_query_executor', 'pipeline_status_checker', 'data_quality_reporter', 'schema_validator'}
        found_allow = set(also_allow)
        tools_registered = expected_tools_register.issubset(found_allow) or len(expected_tools_register & found_allow) >= 2
        no_agent_dir_unless_needed = record.get("agent_dir") is None  # should not have been passed
        
        passed = correct_id and correct_parent and tools_registered
        add_check(
            "register_agent.py called with correct --agent-id, --parent-id, and --also-allow",
            passed,
            f"agent_id_ok: {correct_id}, parent_ok: {correct_parent}, "
            f"tools_registered: {tools_registered} (found: {list(found_allow)}, expected: {list(expected_tools_register)}), "
            f"no_agent_dir: {no_agent_dir_unless_needed}",
            weight=2.5
        )
    else:
        add_check(
            "register_agent.py called with correct parameters",
            False,
            "register_call.json not found — register_agent.py may not have been called",
            weight=2.5
        )
except Exception as e:
    add_check("register_agent.py parameters", False, f"Exception: {e}", weight=2.5)

# ─── CHECK 12: openclaw.json updated with double-bind ─────────────────────────
try:
    cfg_path = workspace / "openclaw.json"
    cfg = json.loads(cfg_path.read_text())
    agents = cfg.get("agents", {}).get("list", [])
    
    new_agent_entry = next((a for a in agents if a.get("agentId") == "dq-sentinel"), None)
    master_entry = next((a for a in agents if a.get("agentId") == "master-agent"), None)
    
    new_agent_exists = new_agent_entry is not None
    double_bound = (master_entry is not None and 
                    "dq-sentinel" in master_entry.get("subagents", {}).get("allowAgents", []))
    
    passed = new_agent_exists and double_bound
    add_check(
        "openclaw.json updated: new agent added AND double-bind with parent",
        passed,
        f"new_agent_in_list: {new_agent_exists}, double_bound_to_master: {double_bound}",
        weight=2.0
    )
except Exception as e:
    add_check("openclaw.json double-bind update", False, f"Exception: {e}", weight=2.0)

# ─── CHECK 13: verify_workspace.sh called with --type functional ───────────────
try:
    verify_file = agent_base / ".verify_type_used"
    if verify_file.exists():
        vtype = verify_file.read_text().strip()
        passed = (vtype == "functional")
        add_check(
            "verify_workspace.sh called with --type functional",
            passed,
            f"Verify type used: '{vtype}'",
            weight=1.5
        )
    else:
        add_check(
            "verify_workspace.sh called with --type functional",
            False,
            "verify_workspace.sh sentinel not found — script may not have been called",
            weight=1.5
        )
except Exception as e:
    add_check("verify_workspace.sh --type functional", False, f"Exception: {e}", weight=1.5)

# ─── CHECK 14: Gateway restart attempted ──────────────────────────────────────
try:
    restart_file = workspace / "tmp/gateway_restart.txt"
    restarted = restart_file.exists()
    add_check(
        "Gateway restart attempted (systemctl --user restart openclaw-gateway.service)",
        restarted,
        f"Gateway restart recorded: {restarted}",
        weight=1.0
    )
except Exception as e:
    add_check("Gateway restart", False, f"Exception: {e}", weight=1.0)

# ─── Final scoring ─────────────────────────────────────────────────────────────
score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed and score >= 0.75,
    "score": score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))