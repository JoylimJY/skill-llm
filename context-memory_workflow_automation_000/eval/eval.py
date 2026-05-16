import sys
import json
import re
from pathlib import Path
from datetime import date

workspace = Path(sys.argv[1])
today = date.today().isoformat()  # YYYY-MM-DD

checks = []
score = 0.0
total_weight = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global score, total_weight
    total_weight += weight
    if passed:
        score += weight

# ── Helper ────────────────────────────────────────────────────────────────────
def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def find_file(relative_path):
    return workspace / relative_path

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 1: Top-level memory files exist
# ══════════════════════════════════════════════════════════════════════════════

required_top = ["SOUL.md", "AGENTS.md", "MEMORY.md", "TOOLS.md", "BOOTSTRAP.md"]
for fname in required_top:
    p = find_file(fname)
    exists = p.exists() and p.is_file()
    add_check(
        f"file_exists:{fname}",
        exists,
        f"{fname} {'found' if exists else 'NOT FOUND'} at {p}",
        weight=1.0
    )

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 2: .learnings/ directory with ERRORS.md and LEARNINGS.md
# ══════════════════════════════════════════════════════════════════════════════

learnings_dir = workspace / ".learnings"
add_check(
    "dir_exists:.learnings",
    learnings_dir.is_dir(),
    f".learnings directory {'exists' if learnings_dir.is_dir() else 'MISSING'}",
    weight=1.0
)

for fname in ["ERRORS.md", "LEARNINGS.md"]:
    p = learnings_dir / fname
    exists = p.exists() and p.is_file()
    add_check(
        f"file_exists:.learnings/{fname}",
        exists,
        f".learnings/{fname} {'found' if exists else 'NOT FOUND'}",
        weight=1.5
    )

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 3: memory/ directory with today's dated log
# ══════════════════════════════════════════════════════════════════════════════

memory_dir = workspace / "memory"
add_check(
    "dir_exists:memory",
    memory_dir.is_dir(),
    f"memory/ directory {'exists' if memory_dir.is_dir() else 'MISSING'}",
    weight=1.0
)

daily_log = memory_dir / f"{today}.md"
daily_exists = daily_log.exists() and daily_log.is_file()
add_check(
    f"file_exists:memory/{today}.md",
    daily_exists,
    f"Daily log memory/{today}.md {'found' if daily_exists else 'NOT FOUND (must use today date: ' + today + ')'}",
    weight=2.0
)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 4: BOOTSTRAP.md contains required structural sections
# ══════════════════════════════════════════════════════════════════════════════

bootstrap_content = read_file(find_file("BOOTSTRAP.md"))
if bootstrap_content:
    # Must contain the 4-step flow reference
    has_flow = any(kw in bootstrap_content for kw in ["判断", "确认", "读取", "执行"])
    add_check(
        "bootstrap:four_step_flow",
        has_flow,
        "BOOTSTRAP.md contains 判断/确认/读取/执行 flow keywords" if has_flow else "BOOTSTRAP.md missing core flow keywords (判断→确认→读取→执行)",
        weight=1.5
    )
    # Must contain user preferences section
    has_prefs = "偏好" in bootstrap_content or "preference" in bootstrap_content.lower() or "称呼" in bootstrap_content
    add_check(
        "bootstrap:user_preferences_section",
        has_prefs,
        "BOOTSTRAP.md contains user preferences section" if has_prefs else "BOOTSTRAP.md missing user preferences section",
        weight=1.0
    )
    # Yuki's name should appear
    has_yuki = "Yuki" in bootstrap_content or "yuki" in bootstrap_content.lower()
    add_check(
        "bootstrap:yuki_name",
        has_yuki,
        "BOOTSTRAP.md includes Yuki's preferred name" if has_yuki else "BOOTSTRAP.md does not mention Yuki's preference",
        weight=1.0
    )
else:
    add_check("bootstrap:four_step_flow", False, "BOOTSTRAP.md could not be read", weight=1.5)
    add_check("bootstrap:user_preferences_section", False, "BOOTSTRAP.md could not be read", weight=1.0)
    add_check("bootstrap:yuki_name", False, "BOOTSTRAP.md could not be read", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 5: ERRORS.md — must contain both errors with description+resolution
# ══════════════════════════════════════════════════════════════════════════════

errors_content = read_file(learnings_dir / "ERRORS.md")
if errors_content:
    # Error #1: SMP vs RUN confusion
    has_error1_desc = any(kw in errors_content for kw in ["SMP-001", "RUN-001", "sample ID", "run ID", "LIMS", "batch report"])
    has_error1_fix = any(kw in errors_content for kw in ["entity type", "verify", "sample vs run", "验证"])
    add_check(
        "errors_md:error1_description",
        has_error1_desc,
        "ERRORS.md contains Error #1 description (LIMS sample/run confusion)" if has_error1_desc else "ERRORS.md missing Error #1 description",
        weight=1.5
    )
    add_check(
        "errors_md:error1_resolution",
        has_error1_fix,
        "ERRORS.md contains Error #1 resolution (verify entity type)" if has_error1_fix else "ERRORS.md missing Error #1 resolution",
        weight=1.5
    )
    # Error #2: wrong protocol version
    has_error2_desc = any(kw in errors_content for kw in ["protocol", "v1", "outdated", "version", "协议"])
    has_error2_fix = any(kw in errors_content for kw in ["v2", "v2_draft", "latest", "confirm", "最新"])
    add_check(
        "errors_md:error2_description",
        has_error2_desc,
        "ERRORS.md contains Error #2 description (wrong protocol version)" if has_error2_desc else "ERRORS.md missing Error #2 description",
        weight=1.5
    )
    add_check(
        "errors_md:error2_resolution",
        has_error2_fix,
        "ERRORS.md contains Error #2 resolution (use v2/check latest)" if has_error2_fix else "ERRORS.md missing Error #2 resolution",
        weight=1.5
    )
else:
    for cname in ["error1_description", "error1_resolution", "error2_description", "error2_resolution"]:
        add_check(f"errors_md:{cname}", False, ".learnings/ERRORS.md could not be read", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 6: LEARNINGS.md — must contain both corrections with date+content+correct_action
# ══════════════════════════════════════════════════════════════════════════════

learnings_content = read_file(learnings_dir / "LEARNINGS.md")
if learnings_content:
    # Correction #1: centrifuge speed 3500rpm
    has_corr1_date = "2024-11-03" in learnings_content or "2024/11/03" in learnings_content or "November" in learnings_content
    has_corr1_content = any(kw in learnings_content for kw in ["3000", "3500", "centrifuge", "rpm", "离心"])
    has_corr1_action = "3500" in learnings_content
    add_check(
        "learnings_md:correction1_date",
        has_corr1_date,
        "LEARNINGS.md contains Correction #1 date (2024-11-03)" if has_corr1_date else "LEARNINGS.md missing Correction #1 date",
        weight=1.0
    )
    add_check(
        "learnings_md:correction1_content_and_action",
        has_corr1_content and has_corr1_action,
        "LEARNINGS.md contains Correction #1 content (rpm) and correct action (3500)" if (has_corr1_content and has_corr1_action) else "LEARNINGS.md missing Correction #1 content or correct action",
        weight=2.0
    )
    # Correction #2: maintenance window check before booking
    has_corr2_date = "2024-12-01" in learnings_content or "2024/12/01" in learnings_content or "December" in learnings_content
    has_corr2_content = any(kw in learnings_content for kw in ["booking", "maintenance", "equipment", "预约", "维护"])
    has_corr2_action = any(kw in learnings_content for kw in ["maintenance_schedule", "check", "before", "预检"])
    add_check(
        "learnings_md:correction2_date",
        has_corr2_date,
        "LEARNINGS.md contains Correction #2 date (2024-12-01)" if has_corr2_date else "LEARNINGS.md missing Correction #2 date",
        weight=1.0
    )
    add_check(
        "learnings_md:correction2_content_and_action",
        has_corr2_content and has_corr2_action,
        "LEARNINGS.md contains Correction #2 content (booking) and action (check maintenance)" if (has_corr2_content and has_corr2_action) else "LEARNINGS.md missing Correction #2 content or correct action",
        weight=2.0
    )
else:
    for cname in ["correction1_date", "correction1_content_and_action", "correction2_date", "correction2_content_and_action"]:
        add_check(f"learnings_md:{cname}", False, ".learnings/LEARNINGS.md could not be read", weight=1.5)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 7: TOOLS.md — LIMS and intranet config
# ══════════════════════════════════════════════════════════════════════════════

tools_content = read_file(find_file("TOOLS.md"))
if tools_content:
    has_lims = "LabVantage" in tools_content or "lims.genomicscore" in tools_content or "LIMS" in tools_content
    has_sso = "SSO" in tools_content or "IdP" in tools_content or "sso" in tools_content.lower()
    has_session = any(kw in tools_content for kw in ["30 min", "30min", "session", "expire", "inactivity"])
    has_intranet = any(kw in tools_content for kw in ["intranet", "equipment", "maintenance_schedule"])

    add_check("tools_md:lims_config", has_lims, "TOOLS.md contains LIMS configuration" if has_lims else "TOOLS.md missing LIMS config", weight=1.0)
    add_check("tools_md:sso_auth", has_sso, "TOOLS.md mentions SSO auth method" if has_sso else "TOOLS.md missing SSO auth info", weight=1.0)
    add_check("tools_md:session_expiry_warning", has_session, "TOOLS.md notes 30-min session expiry" if has_session else "TOOLS.md missing session expiry warning", weight=1.0)
    add_check("tools_md:intranet_portal", has_intranet, "TOOLS.md contains intranet/equipment portal info" if has_intranet else "TOOLS.md missing intranet portal", weight=1.0)
else:
    for cname in ["lims_config", "sso_auth", "session_expiry_warning", "intranet_portal"]:
        add_check(f"tools_md:{cname}", False, "TOOLS.md could not be read", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 8: AGENTS.md — sample tracking workflow
# ══════════════════════════════════════════════════════════════════════════════

agents_content = read_file(find_file("AGENTS.md"))
if agents_content:
    has_workflow = any(kw in agents_content for kw in ["sample", "LIMS", "tracking", "workflow", "流程", "步骤"])
    has_steps = any(kw in agents_content for kw in ["1.", "Step 1", "第一步", "①", "Confirm", "entity"])
    add_check("agents_md:workflow_present", has_workflow, "AGENTS.md contains sample tracking workflow" if has_workflow else "AGENTS.md missing workflow", weight=1.5)
    add_check("agents_md:step_structure", has_steps, "AGENTS.md has structured steps" if has_steps else "AGENTS.md lacks step structure", weight=1.0)
else:
    add_check("agents_md:workflow_present", False, "AGENTS.md could not be read", weight=1.5)
    add_check("agents_md:step_structure", False, "AGENTS.md could not be read", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 9: MEMORY.md — user preferences stored
# ══════════════════════════════════════════════════════════════════════════════

memory_content = read_file(find_file("MEMORY.md"))
if memory_content:
    has_yuki = "Yuki" in memory_content
    has_email = "yuki.tanaka@genomicscore.int" in memory_content or "yuki.tanaka" in memory_content
    has_tz = "JST" in memory_content or "UTC+9" in memory_content
    add_check("memory_md:user_name", has_yuki, "MEMORY.md stores Yuki's preferred name" if has_yuki else "MEMORY.md missing Yuki's name preference", weight=1.5)
    add_check("memory_md:email", has_email, "MEMORY.md stores Yuki's email" if has_email else "MEMORY.md missing email", weight=1.0)
    add_check("memory_md:timezone", has_tz, "MEMORY.md stores timezone (JST/UTC+9)" if has_tz else "MEMORY.md missing timezone", weight=1.0)
else:
    add_check("memory_md:user_name", False, "MEMORY.md could not be read", weight=1.5)
    add_check("memory_md:email", False, "MEMORY.md could not be read", weight=1.0)
    add_check("memory_md:timezone", False, "MEMORY.md could not be read", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# CHECK GROUP 10: Daily memory log — proper template sections
# ══════════════════════════════════════════════════════════════════════════════

if daily_exists:
    daily_content = read_file(daily_log)
    if daily_content:
        has_completed = "今日完成" in daily_content or "completed" in daily_content.lower() or "Completed" in daily_content
        has_decisions = "重要决策" in daily_content or "decision" in daily_content.lower() or "Decision" in daily_content
        has_learnings = "新学到的" in daily_content or "learned" in daily_content.lower() or "Learned" in daily_content or "学到" in daily_content
        has_followup = "待跟进" in daily_content or "follow" in daily_content.lower() or "Follow" in daily_content

        add_check("daily_log:completed_section", has_completed, "Daily log has 今日完成/Completed section" if has_completed else "Daily log missing 今日完成 section", weight=1.0)
        add_check("daily_log:decisions_section", has_decisions, "Daily log has 重要决策/Decisions section" if has_decisions else "Daily log missing 重要决策 section", weight=1.0)
        add_check("daily_log:learnings_section", has_learnings, "Daily log has 新学到的/Learned section" if has_learnings else "Daily log missing 新学到的 section", weight=1.0)
        add_check("daily_log:followup_section", has_followup, "Daily log has 待跟进/Follow-up section" if has_followup else "Daily log missing 待跟进 section", weight=1.0)

        # Content spot-check: onboarding or protocol decision should appear
        has_real_content = any(kw in daily_content for kw in ["protocol", "LIMS", "Yuki", "onboarding", "v2", "SSO", "extraction"])
        add_check("daily_log:real_content", has_real_content, "Daily log contains substantive content from onboarding notes" if has_real_content else "Daily log appears empty/generic", weight=1.5)
    else:
        for cname in ["completed_section", "decisions_section", "learnings_section", "followup_section", "real_content"]:
            add_check(f"daily_log:{cname}", False, "Daily log could not be read", weight=1.0)
else:
    for cname in ["completed_section", "decisions_section", "learnings_section", "followup_section", "real_content"]:
        add_check(f"daily_log:{cname}", False, f"Daily log memory/{today}.md does not exist", weight=1.0)

# ══════════════════════════════════════════════════════════════════════════════
# Final score
# ══════════════════════════════════════════════════════════════════════════════

final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
passed = final_score >= 0.75

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))