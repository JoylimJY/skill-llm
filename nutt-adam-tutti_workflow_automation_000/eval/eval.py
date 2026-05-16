#!/usr/bin/env python3
"""
Evaluation script for the Tutti multi-agent orchestration task.
Usage: python3 eval_script.py /workspace
"""
import sys, json, re
from pathlib import Path

try:
    import toml
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "toml", "-q",
                    "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"])
    import toml

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
invoc_log  = workspace / ".tutti" / "openclaw_invocations.log"

checks = []

# ─── Helper ─────────────────────────────────────────────────────────────────────
def check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)

def load_invocations():
    if not invoc_log.exists():
        return []
    entries = []
    for line in invoc_log.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            pass
    return entries

# ════════════════════════════════════════════════════════════════════════════════
# BLOCK 1 — tutti.toml existence and basic structure
# ════════════════════════════════════════════════════════════════════════════════
config_path = workspace / "tutti.toml"
cfg = None
try:
    assert config_path.exists(), "tutti.toml not found"
    cfg = toml.loads(config_path.read_text())
    check("tutti_toml_exists", True, "tutti.toml found and parseable")
except Exception as e:
    check("tutti_toml_exists", False, str(e))

# ── 1a. Three required agents ────────────────────────────────────────────────────
REQUIRED_AGENTS = {"variant-caller", "qc-reporter", "annotation-engine"}
if cfg:
    try:
        agents_section = cfg.get("agents", cfg.get("agent", {}))
        # Support both [agents.name] and [[agents]] array styles
        if isinstance(agents_section, dict):
            defined_agents = set(agents_section.keys())
        elif isinstance(agents_section, list):
            defined_agents = {a.get("name", "") for a in agents_section}
        else:
            defined_agents = set()
        missing = REQUIRED_AGENTS - defined_agents
        check("agents_all_three_defined",
              len(missing) == 0,
              f"defined={defined_agents}, missing={missing}")
    except Exception as e:
        check("agents_all_three_defined", False, str(e))
else:
    check("agents_all_three_defined", False, "config not loaded")

# ════════════════════════════════════════════════════════════════════════════════
# BLOCK 2 — Workflow definitions
# ════════════════════════════════════════════════════════════════════════════════
workflows = {}
if cfg:
    try:
        wf_section = cfg.get("workflows", cfg.get("workflow", {}))
        if isinstance(wf_section, dict):
            workflows = wf_section
        elif isinstance(wf_section, list):
            # [[workflows]] array style
            workflows = {w.get("name", f"wf{i}"): w for i, w in enumerate(wf_section)}
    except Exception as e:
        check("workflows_section_parseable", False, str(e))

# ── 2a. integration-check workflow exists ────────────────────────────────────────
ic_wf = workflows.get("integration-check")
check("workflow_integration_check_exists",
      ic_wf is not None,
      f"available workflows: {list(workflows.keys())}")

# ── 2b. integration-check has ensure_running step ────────────────────────────────
def collect_steps(wf_obj):
    """Return flat list of step dicts from a workflow dict."""
    if not wf_obj:
        return []
    steps = wf_obj.get("steps", [])
    if not steps:
        # inline steps as list at top level
        steps = [v for v in wf_obj.values() if isinstance(v, dict)]
    return steps if isinstance(steps, list) else []

ic_steps = collect_steps(ic_wf) if ic_wf else []

step_types = [s.get("type", s.get("step_type", "")) for s in ic_steps]

check("integration_check_has_ensure_running",
      "ensure_running" in step_types,
      f"step types found: {step_types}")

# ── 2c. integration-check has at least one prompt step ──────────────────────────
check("integration_check_has_prompt_step",
      "prompt" in step_types,
      f"step types found: {step_types}")

# ── 2d. prompt step contains inject_files ────────────────────────────────────────
inject_found = False
for s in ic_steps:
    if s.get("type", s.get("step_type", "")) == "prompt" and "inject_files" in s:
        inject_found = True
        break
check("prompt_step_has_inject_files",
      inject_found,
      "Looking for inject_files in prompt steps of integration-check")

# ── 2e. integration-check has command step ──────────────────────────────────────
check("integration_check_has_command_step",
      "command" in step_types,
      f"step types found: {step_types}")

# ── 2f. At least one step has fail_mode ──────────────────────────────────────────
fail_mode_found = any("fail_mode" in s for s in ic_steps)
check("step_has_fail_mode", fail_mode_found,
      "At least one step in integration-check should have fail_mode")

# ── 2g. nightly-handoff workflow exists with nested workflow step ─────────────────
nh_wf = workflows.get("nightly-handoff")
nh_ok = nh_wf is not None
check("workflow_nightly_handoff_exists", nh_ok,
      f"available workflows: {list(workflows.keys())}")

if nh_ok:
    nh_steps = collect_steps(nh_wf)
    nh_step_types = [s.get("type", s.get("step_type", "")) for s in nh_steps]
    check("nightly_handoff_has_nested_workflow_step",
          "workflow" in nh_step_types,
          f"step types found: {nh_step_types}")
else:
    check("nightly_handoff_has_nested_workflow_step", False, "workflow not found")

# ════════════════════════════════════════════════════════════════════════════════
# BLOCK 3 — Invocation log checks
# ════════════════════════════════════════════════════════════════════════════════
invocs = load_invocations()
actions = [e["action"] for e in invocs]

check("invocation_log_exists",
      len(invocs) > 0,
      f"{len(invocs)} invocations recorded")

# ── 3a. doctor_check was called ───────────────────────────────────────────────────
check("doctor_check_called",
      "doctor_check" in actions,
      f"actions seen: {actions}")

# ── 3b. doctor_check before launch_team ──────────────────────────────────────────
if "doctor_check" in actions and "launch_team" in actions:
    dc_idx = actions.index("doctor_check")
    lt_idx = actions.index("launch_team")
    check("doctor_check_before_launch",
          dc_idx < lt_idx,
          f"doctor_check at pos {dc_idx}, launch_team at pos {lt_idx}")
else:
    check("doctor_check_before_launch", False,
          f"doctor_check present: {'doctor_check' in actions}, launch_team present: {'launch_team' in actions}")

# ── 3c. send_prompt called with variant-caller ────────────────────────────────────
sp_entries = [e for e in invocs if e["action"] == "send_prompt"]
sp_vc = [e for e in sp_entries if e["args"] and e["args"][0] == "variant-caller"]
check("send_prompt_to_variant_caller",
      len(sp_vc) > 0,
      f"send_prompt entries: {[(e['args']) for e in sp_entries]}")

# ── 3d. send_prompt used --auto-up ────────────────────────────────────────────────
if sp_vc:
    raw_flags = " ".join(sp_vc[0].get("raw", sp_vc[0].get("args", [])))
    check("send_prompt_auto_up_flag",
          "--auto-up" in raw_flags,
          f"raw args: {sp_vc[0].get('raw', sp_vc[0].get('args', []))}")
else:
    check("send_prompt_auto_up_flag", False, "no send_prompt to variant-caller found")

# ── 3e. send_prompt used --wait ────────────────────────────────────────────────────
if sp_vc:
    raw_flags = " ".join(str(x) for x in sp_vc[0].get("raw", sp_vc[0].get("args", [])))
    check("send_prompt_wait_flag",
          "--wait" in raw_flags,
          f"raw args: {sp_vc[0].get('raw', sp_vc[0].get('args', []))}")
else:
    check("send_prompt_wait_flag", False, "no send_prompt to variant-caller found")

# ── 3f. send_prompt used --output ─────────────────────────────────────────────────
if sp_vc:
    raw_flags = " ".join(str(x) for x in sp_vc[0].get("raw", sp_vc[0].get("args", [])))
    check("send_prompt_output_flag",
          "--output" in raw_flags,
          f"raw args: {sp_vc[0].get('raw', sp_vc[0].get('args', []))}")
else:
    check("send_prompt_output_flag", False, "no send_prompt to variant-caller found")

# ── 3g. run_workflow called with --strict ─────────────────────────────────────────
rw_entries = [e for e in invocs if e["action"] == "run_workflow"]
rw_strict = [e for e in rw_entries
             if "--strict" in e.get("raw", e.get("args", []))]
check("run_workflow_strict_flag",
      len(rw_strict) > 0,
      f"run_workflow entries: {[e.get('raw', e.get('args', [])) for e in rw_entries]}")

# ── 3h. verify_team called with --strict ──────────────────────────────────────────
vt_entries = [e for e in invocs if e["action"] == "verify_team"]
vt_strict  = [e for e in vt_entries
              if "--strict" in e.get("raw", e.get("args", []))]
check("verify_team_strict_flag",
      len(vt_strict) > 0,
      f"verify_team entries: {[e.get('raw', e.get('args', [])) for e in vt_entries]}")

# ── 3i. land_agent called with variant-caller and --pr ────────────────────────────
la_entries = [e for e in invocs if e["action"] == "land_agent"]
la_vc_pr   = [e for e in la_entries
              if e.get("args") and e["args"][0] == "variant-caller"
              and "--pr" in e.get("raw", e.get("args", []))]
check("land_agent_variant_caller_pr",
      len(la_vc_pr) > 0,
      f"land_agent entries: {[e.get('raw', e.get('args', [])) for e in la_entries]}")

# ── 3j. generate_handoff called with variant-caller and --reason ──────────────────
gh_entries = [e for e in invocs if e["action"] == "generate_handoff"]
gh_vc_reason = [e for e in gh_entries
                if e.get("args") and e["args"][0] == "variant-caller"
                and "--reason" in e.get("raw", e.get("args", []))]
check("generate_handoff_variant_caller_reason",
      len(gh_vc_reason) > 0,
      f"generate_handoff entries: {[e.get('raw', e.get('args', [])) for e in gh_entries]}")

# ── 3k. overall execution order: doctor → launch → send_prompt → run_workflow → verify → land → handoff
ORDER_REQUIRED = ["doctor_check", "launch_team", "send_prompt", "run_workflow",
                  "verify_team", "land_agent", "generate_handoff"]
try:
    positions = {}
    for req in ORDER_REQUIRED:
        if req in actions:
            positions[req] = actions.index(req)
    missing_order = [r for r in ORDER_REQUIRED if r not in positions]
    if missing_order:
        check("execution_order_correct", False,
              f"Missing actions: {missing_order}")
    else:
        pos_list = [positions[r] for r in ORDER_REQUIRED]
        in_order = all(pos_list[i] < pos_list[i+1] for i in range(len(pos_list)-1))
        check("execution_order_correct", in_order,
              f"positions: {dict(zip(ORDER_REQUIRED, pos_list))}")
except Exception as e:
    check("execution_order_correct", False, str(e))

# ════════════════════════════════════════════════════════════════════════════════
# SCORING
# ════════════════════════════════════════════════════════════════════════════════
total   = len(checks)
passed  = sum(1 for c in checks if c["passed"])
score   = round(passed / total, 4) if total else 0.0
overall = score >= 0.80   # 80% threshold to pass

result = {
    "passed": overall,
    "score":  score,
    "checks": checks
}
print(json.dumps(result, indent=2))