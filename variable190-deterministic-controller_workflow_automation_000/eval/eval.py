import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
project_root = workspace / "robotics-fleet-workspace"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ─────────────────────────────────────────────────────────────────────────────
# 1. HEARTBEAT.md checks
# ─────────────────────────────────────────────────────────────────────────────
heartbeat_candidates = list(project_root.rglob("HEARTBEAT.md"))
if not heartbeat_candidates:
    check("heartbeat_file_exists", False, "HEARTBEAT.md not found in robotics-fleet-workspace")
    hb_text = ""
else:
    hb_path = heartbeat_candidates[0]
    hb_text = hb_path.read_text()
    check("heartbeat_file_exists", True, f"Found at {hb_path.relative_to(workspace)}")

# Must NOT contain the raw placeholder
placeholder_gone = "<TELEGRAM_GROUP_ID>" not in hb_text
check("heartbeat_placeholder_replaced",
      placeholder_gone,
      "Placeholder <TELEGRAM_GROUP_ID> was replaced" if placeholder_gone
      else "<TELEGRAM_GROUP_ID> placeholder still present")

# Must contain the correct group ID from docs/project_brief.md
correct_group_id = "-1009988776655"
group_id_present = correct_group_id in hb_text
check("heartbeat_correct_group_id",
      group_id_present,
      f"Group ID {correct_group_id} found in HEARTBEAT.md" if group_id_present
      else f"Expected group ID {correct_group_id} not found in HEARTBEAT.md")

# Must contain the label 'Telegram Group ID:' (OpenClaw parses by exact prefix)
label_present = "Telegram Group ID:" in hb_text
check("heartbeat_label_preserved",
      label_present,
      "'Telegram Group ID:' label present" if label_present
      else "'Telegram Group ID:' label missing — OpenClaw cannot parse heartbeat target")

# Cadence must be 15
cadence_ok = bool(re.search(r"(?:Every|Cadence)[^\n]*15", hb_text, re.IGNORECASE))
check("heartbeat_cadence_15",
      cadence_ok,
      "Cadence of 15 minutes found" if cadence_ok else "Cadence 15 not found in HEARTBEAT.md")

# Prompt must mention the fleet heartbeat message (key words)
prompt_ok = "nominal" in hb_text.lower() or "robofleet" in hb_text.lower() or "deployment heartbeat" in hb_text.lower()
check("heartbeat_prompt_populated",
      prompt_ok,
      "Heartbeat prompt appears to reference the fleet monitoring message"
      if prompt_ok else "Heartbeat prompt does not appear to be set from project brief")

# ─────────────────────────────────────────────────────────────────────────────
# 2. ACTIVITIES.md checks
# ─────────────────────────────────────────────────────────────────────────────
activities_candidates = list(project_root.rglob("ACTIVITIES.md"))
if not activities_candidates:
    check("activities_file_exists", False, "ACTIVITIES.md not found in robotics-fleet-workspace")
    act_text = ""
else:
    act_path = activities_candidates[0]
    act_text = act_path.read_text()
    check("activities_file_exists", True, f"Found at {act_path.relative_to(workspace)}")

# Plan Path must point to current.sprint.md (the external sprint import)
plan_path_ok = bool(re.search(r"Plan Path\s*[\n:]+.*current\.sprint\.md", act_text, re.IGNORECASE))
check("activities_plan_path_set",
      plan_path_ok,
      "Plan Path references current.sprint.md" if plan_path_ok
      else "Plan Path not set or does not reference current.sprint.md")

# Must NOT contain the raw <PLAN_PATH> placeholder
plan_placeholder_gone = "<PLAN_PATH>" not in act_text
check("activities_plan_placeholder_replaced",
      plan_placeholder_gone,
      "<PLAN_PATH> placeholder replaced" if plan_placeholder_gone
      else "<PLAN_PATH> placeholder still present")

# Evidence gate: at least two items must have an Artifact: line with a real path
artifact_lines = re.findall(r"Artifact:\s*(\S+)", act_text)
artifact_ok = len(artifact_lines) >= 2
check("activities_evidence_gated_items",
      artifact_ok,
      f"Found {len(artifact_lines)} Artifact: lines (need ≥2 for evidence-gated queue)"
      if artifact_ok else f"Only {len(artifact_lines)} Artifact: line(s) — need ≥2 evidence-gated items")

# At least one artifact path must be from the sprint (outputs/ prefix expected)
sprint_artifacts = [a for a in artifact_lines if a.startswith("outputs/") or "outputs" in a]
sprint_artifact_ok = len(sprint_artifacts) >= 1
check("activities_sprint_artifacts_present",
      sprint_artifact_ok,
      f"Sprint artifacts from outputs/ found: {sprint_artifacts}"
      if sprint_artifact_ok else "No sprint-derived artifacts from outputs/ found in ACTIVITIES.md")

# ─────────────────────────────────────────────────────────────────────────────
# 3. openclaw.json checks
# ─────────────────────────────────────────────────────────────────────────────
oclaw_candidates = list(project_root.rglob("openclaw.json"))
if not oclaw_candidates:
    check("openclaw_json_exists", False, "openclaw.json not found in robotics-fleet-workspace")
    config = {}
else:
    oclaw_path = oclaw_candidates[0]
    try:
        config = json.loads(oclaw_path.read_text())
        check("openclaw_json_exists", True, f"Found and parsed at {oclaw_path.relative_to(workspace)}")
    except json.JSONDecodeError as e:
        check("openclaw_json_exists", False, f"openclaw.json is not valid JSON: {e}")
        config = {}

# All four mandatory top-level keys
required_keys = ["heartbeat", "cron", "activities_path", "sprint_template_path"]
for key in required_keys:
    present = key in config
    check(f"openclaw_has_{key}",
          present,
          f"Key '{key}' present in openclaw.json" if present
          else f"Key '{key}' MISSING from openclaw.json")

# heartbeat sub-keys
hb_cfg = config.get("heartbeat", {})
tg_id_cfg = str(hb_cfg.get("telegram_group_id", ""))
tg_ok = tg_id_cfg == correct_group_id
check("openclaw_heartbeat_telegram_group_id",
      tg_ok,
      f"telegram_group_id = {tg_id_cfg}" if tg_ok
      else f"telegram_group_id = '{tg_id_cfg}', expected '{correct_group_id}'")

cadence_cfg = hb_cfg.get("cadence_minutes")
cadence_int_ok = isinstance(cadence_cfg, int) and cadence_cfg == 15
check("openclaw_heartbeat_cadence_integer",
      cadence_int_ok,
      f"cadence_minutes = {cadence_cfg} (int)" if cadence_int_ok
      else f"cadence_minutes = {repr(cadence_cfg)} — must be integer 15")

# cron must be verbatim parsed poll_cron_payload.txt
expected_cron = {
    "schedule": "*/5 * * * *",
    "action": "poll_activities",
    "target": "ACTIVITIES.md",
    "evidence_gate": True,
    "retry_on_missing_artifact": 3
}
actual_cron = config.get("cron", {})
cron_ok = actual_cron == expected_cron
check("openclaw_cron_verbatim_payload",
      cron_ok,
      "cron object matches poll_cron_payload.txt exactly" if cron_ok
      else f"cron mismatch.\n  Expected: {expected_cron}\n  Got:      {actual_cron}")

# activities_path must be "ACTIVITIES.md"
act_path_cfg = config.get("activities_path", "")
act_path_ok = act_path_cfg == "ACTIVITIES.md"
check("openclaw_activities_path_value",
      act_path_ok,
      f"activities_path = '{act_path_cfg}'" if act_path_ok
      else f"activities_path = '{act_path_cfg}', expected 'ACTIVITIES.md'")

# sprint_template_path must reference current.sprint.md
stp = config.get("sprint_template_path", "")
stp_ok = "current.sprint.md" in stp
check("openclaw_sprint_template_path",
      stp_ok,
      f"sprint_template_path = '{stp}'" if stp_ok
      else f"sprint_template_path = '{stp}' does not reference current.sprint.md")

# heartbeat prompt must be a non-empty string
hb_prompt = hb_cfg.get("prompt", "")
prompt_nonempty = isinstance(hb_prompt, str) and len(hb_prompt.strip()) > 5
check("openclaw_heartbeat_prompt_set",
      prompt_nonempty,
      f"heartbeat.prompt = '{hb_prompt[:60]}...'" if prompt_nonempty
      else f"heartbeat.prompt is missing or too short: {repr(hb_prompt)}")

# ─────────────────────────────────────────────────────────────────────────────
# Score
# ─────────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall = passed_count == total

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))