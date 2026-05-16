import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
skill_base = workspace / "skills" / "follow-up-commander"
dirs = [
    skill_base / "scripts",
    skill_base / "resources",
    skill_base / "examples",
    skill_base / "tests",
    workspace / "meetings" / "2024-Q2" / "raw_notes",
    workspace / "meetings" / "2024-Q2" / "processed",
    workspace / "meetings" / "2024-Q1" / "archive",
    workspace / "team" / "roster",
    workspace / "team" / "assignments",
    workspace / "projects" / "atlas" / "backlog",
    workspace / "projects" / "atlas" / "specs",
    workspace / "admin" / "templates",
    workspace / "admin" / "logs",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "input_schema": {
        "required_fields": ["meeting_id", "title", "date", "participants", "raw_notes"],
        "optional_fields": ["priority_level", "project_code"],
        "priority_levels": ["P0", "P1", "P2", "P3"],
        "participant_roles": ["PM", "ENG", "DESIGN", "QA", "STAKEHOLDER"],
        "notes_format": "free_text_or_bullet"
    },
    "output_schema": {
        "required_sections": [
            "行动清单",
            "负责人映射",
            "建议邮件草稿",
            "升级与催办规则",
            "下次同步议题",
            "未决问题"
        ],
        "pending_items_policy": "如信息缺失（如截止日期不明、负责人未指定），必须在'未决问题'中列出，禁止编造。",
        "draft_policy": "所有邮件草稿标注 [DRAFT] 且不得包含实际发送指令。",
        "escalation_rule": "P0事项需在24小时内催办，P1需在72小时内，P2/P3按周期催办。",
        "format": "markdown",
        "filename_convention": "followup_<meeting_id>.md"
    },
    "run_script": {
        "command": "python3 \"{baseDir}/scripts/run.py\" --input <input_file> --output <output_file>",
        "description": "baseDir指skill所在目录，即skills/follow-up-commander"
    }
}
(skill_base / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 会后跟进报告 — {{meeting_id}}

**会议标题：** {{title}}
**日期：** {{date}}
**参与者：** {{participants_summary}}

---

## 行动清单

| # | 事项 | 负责人 | 优先级 | 截止日期 | 状态 |
|---|------|--------|--------|----------|------|
{{action_items_table}}

---

## 负责人映射

{{owner_map}}

---

## 建议邮件草稿

[DRAFT]

{{email_draft}}

---

## 升级与催办规则

{{escalation_rules}}

---

## 下次同步议题

{{next_sync_topics}}

---

## 未决问题

{{pending_questions}}
""")
(skill_base / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# ── run.py (the actual processing script) ───────────────────────────────────
run_py = textwrap.dedent('''\
#!/usr/bin/env python3
"""
follow-up-commander run.py
Reads a JSON input file, applies the template, produces a Markdown follow-up report.
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent  # skills/follow-up-commander

def load_spec():
    spec_path = BASE_DIR / "resources" / "spec.json"
    with open(spec_path, encoding="utf-8") as f:
        return json.load(f)

def load_template():
    tpl_path = BASE_DIR / "resources" / "template.md"
    with open(tpl_path, encoding="utf-8") as f:
        return f.read()

def validate_input(data, spec):
    errors = []
    for field in spec["input_schema"]["required_fields"]:
        if field not in data:
            errors.append(f"缺少必填字段: {field}")
    valid_priorities = spec["input_schema"]["priority_levels"]
    if "priority_level" in data and data["priority_level"] not in valid_priorities:
        errors.append(f"priority_level 必须是 {valid_priorities} 之一，收到: {data[\'priority_level\']}")
    valid_roles = spec["input_schema"]["participant_roles"]
    for p in data.get("participants", []):
        if p.get("role") not in valid_roles:
            errors.append(f"参与者角色无效: {p.get(\'role\')} (允许: {valid_roles})")
    return errors

def parse_action_items(raw_notes, participants, priority_level):
    """
    Simple heuristic parser: lines starting with - or * or numbered are action items.
    Lines with '?' or '待定' or '未定' are pending questions.
    """
    lines = raw_notes.strip().split("\\n")
    items = []
    pending = []
    item_idx = 1
    for line in lines:
        line = line.strip()
        if not line:
            continue
        is_action = (
            line.startswith("-") or line.startswith("*") or
            (len(line) > 2 and line[0].isdigit() and line[1] in ".)")
        )
        if is_action:
            text = line.lstrip("-*0123456789.) ").strip()
            # Try to find owner hint
            owner = "待指定"
            deadline = "待确认"
            for p in participants:
                if p["name"] in text or p.get("alias", "") in text:
                    owner = p["name"]
                    break
            # Check for deadline hints
            has_deadline = any(kw in text for kw in ["by", "前", "截止", "deadline", "日前"])
            if not has_deadline:
                pending.append(f"事项「{text[:30]}...」截止日期未明确，需确认")
                deadline = "待确认"
            # Check if owner is unclear
            if owner == "待指定":
                pending.append(f"事项「{text[:30]}...」负责人未指定，需确认")
            items.append({
                "idx": item_idx,
                "text": text,
                "owner": owner,
                "priority": priority_level if priority_level else "P2",
                "deadline": deadline,
                "status": "待开始"
            })
            item_idx += 1
        elif "?" in line or "待定" in line or "未定" in line or "unclear" in line.lower():
            pending.append(line.lstrip("-*") .strip())
    return items, pending

def build_escalation(priority):
    rules = {
        "P0": "P0 事项须在 **24小时** 内完成催办；若无响应，立即上升至部门负责人。",
        "P1": "P1 事项须在 **72小时** 内完成催办；若无响应，在下次周会前升级。",
        "P2": "P2 事项按 **每周** 节奏催办；连续两周无进展则升级。",
        "P3": "P3 事项按 **双周** 节奏催办；积压超过一个 Sprint 则重新评估优先级。",
    }
    return rules.get(priority, rules["P2"])

def render(data, spec):
    template = load_template()
    participants = data.get("participants", [])
    raw_notes = data.get("raw_notes", "")
    priority = data.get("priority_level", "P2")

    items, pending_from_notes = parse_action_items(raw_notes, participants, priority)

    # Action items table
    table_rows = []
    for it in items:
        table_rows.append(
            f"| {it[\'idx\']} | {it[\'text\'][:50]} | {it[\'owner\']} | {it[\'priority\']} | {it[\'deadline\']} | {it[\'status\']} |"
        )
    action_table = "\\n".join(table_rows) if table_rows else "| — | 暂无解析到行动事项 | — | — | — | — |"

    # Owner map
    owner_map_lines = []
    owner_map = {}
    for it in items:
        owner_map.setdefault(it["owner"], []).append(it["text"][:40])
    for owner, tasks in owner_map.items():
        owner_map_lines.append(f"**{owner}**")
        for t in tasks:
            owner_map_lines.append(f"  - {t}")
    owner_map_str = "\\n".join(owner_map_lines) if owner_map_lines else "（无法解析负责人映射）"

    # Participants summary
    participants_summary = ", ".join(
        f"{p[\'name\']} ({p[\'role\']})" for p in participants
    )

    # Email draft
    owner_list = "\\n".join(f"- {o}: {', '.join(ts)}" for o, ts in owner_map.items())
    email_draft = f"""To: {", ".join(p["email"] for p in participants if "email" in p)}
Subject: [DRAFT] 会后跟进 — {data.get("title", "")}

各位，

感谢参加 {data.get("title", "")} ({data.get("date", "")}) 会议。
以下为本次会议产出的行动事项，请各位按优先级及时跟进：

{owner_list}

如有疑问请回复本邮件。本草稿仅供审阅，请勿直接发送。"""

    # Next sync topics
    next_sync = []
    for it in items:
        if it["deadline"] == "待确认":
            next_sync.append(f"- 确认「{it['text'][:35]}」的截止日期")
    for p in participants:
        if p.get("role") == "STAKEHOLDER":
            next_sync.append(f"- {p['name']} 的审批节点确认")
    if not next_sync:
        next_sync.append("- 各行动项进度同步")
    next_sync_str = "\\n".join(next_sync)

    # Pending questions
    pending_all = list(dict.fromkeys(pending_from_notes))  # deduplicate
    if not pending_all:
        pending_all = ["（无待确认项）"]
    pending_str = "\\n".join(f"- {q}" for q in pending_all)

    # Escalation
    escalation = build_escalation(priority)

    output = template
    output = output.replace("{{meeting_id}}", data["meeting_id"])
    output = output.replace("{{title}}", data["title"])
    output = output.replace("{{date}}", data["date"])
    output = output.replace("{{participants_summary}}", participants_summary)
    output = output.replace("{{action_items_table}}", action_table)
    output = output.replace("{{owner_map}}", owner_map_str)
    output = output.replace("{{email_draft}}", email_draft)
    output = output.replace("{{escalation_rules}}", escalation)
    output = output.replace("{{next_sync_topics}}", next_sync_str)
    output = output.replace("{{pending_questions}}", pending_str)
    return output

def main():
    parser = argparse.ArgumentParser(description="follow-up-commander runner")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Output Markdown file path")
    args = parser.parse_args()

    spec = load_spec()
    with open(args.input, encoding="utf-8") as f:
        data = json.load(f)

    errors = validate_input(data, spec)
    if errors:
        print("[ERROR] 输入验证失败:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    result = render(data, spec)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(result, encoding="utf-8")
    print(f"[OK] 输出已写入: {out_path}")

if __name__ == "__main__":
    main()
''')
(skill_base / "scripts" / "run.py").write_text(run_py, encoding="utf-8")

# ── smoke-test.md ────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

Run:
    python3 scripts/run.py --input examples/sample_input.json --output /tmp/smoke_out.md

Expected: /tmp/smoke_out.md contains all 6 required sections.
""")
(skill_base / "tests" / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ── examples: sample input/output ────────────────────────────────────────────
sample_input = {
    "meeting_id": "MTG-2024-001",
    "title": "Q1 Sprint Planning Kickoff",
    "date": "2024-01-15",
    "priority_level": "P1",
    "project_code": "ATLAS-Q1",
    "participants": [
        {"name": "Alice", "role": "PM", "email": "alice@example.com"},
        {"name": "Bob", "role": "ENG", "email": "bob@example.com"}
    ],
    "raw_notes": "- Alice to finalize roadmap by Jan 20\n- Bob set up CI pipeline by Jan 22\n- Review metrics dashboard 待定"
}
(skill_base / "examples" / "sample_input.json").write_text(
    json.dumps(sample_input, ensure_ascii=False, indent=2), encoding="utf-8"
)
(skill_base / "examples" / "sample_output_note.txt").write_text(
    "See smoke-test.md for how to generate sample_output.md", encoding="utf-8"
)

# ── THE ACTUAL PROBLEM INPUT (messy, realistic, adversarial) ─────────────────
# This is the raw meeting notes file the agent must process.
# It is intentionally messy:
# - Several action items lack deadlines → must appear in 未决问题
# - One participant has an invalid role that agent must fix before passing to run.py
# - priority_level is missing → agent must decide (spec says optional, default P2)
# - Two items have no owner named
# The agent must read spec.json to know valid roles and construct a valid input JSON.

messy_notes = {
    "meeting_id": "MTG-2024-Q2-07",
    "title": "Atlas Platform — Cross-Team Sync #7",
    "date": "2024-05-14",
    # priority_level intentionally omitted → agent must either add P2 default or leave absent
    "project_code": "ATLAS-PLATFORM",
    "participants": [
        {"name": "Chen Wei",   "role": "PM",           "email": "chenwei@corp.example"},
        {"name": "Fatima",     "role": "ENG",          "email": "fatima@corp.example"},
        {"name": "Diego",      "role": "DESIGN",       "email": "diego@corp.example"},
        {"name": "Yuki",       "role": "QA",           "email": "yuki@corp.example"},
        # "LEAD" is NOT a valid role — agent must correct to a valid role from spec
        {"name": "Mr. Park",   "role": "LEAD",         "email": "park@corp.example"}
    ],
    "raw_notes": (
        "- Fatima: complete OAuth2 integration by May 20\n"
        "- Diego: deliver revised UI mockups (no deadline mentioned)\n"
        "- Yuki: write regression test suite for login flow by May 22\n"
        "- Someone needs to set up the staging environment config — owner unclear\n"
        "- Chen Wei to send updated PRD to stakeholders before next meeting\n"
        "- Performance benchmarking plan — owner and deadline both 待定\n"
        "- Mr. Park to approve budget allocation — deadline unclear\n"
        "- API rate-limit strategy 未定，需要进一步讨论\n"
    )
}

raw_notes_path = workspace / "meetings" / "2024-Q2" / "raw_notes" / "mtg_q2_07_raw.json"
raw_notes_path.write_text(
    json.dumps(messy_notes, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    workspace / "meetings" / "2024-Q1" / "archive" / "mtg_q1_final_summary.txt":
        "Q1 all-hands summary — archived. No action needed.",
    workspace / "meetings" / "2024-Q2" / "processed" / ".gitkeep": "",
    workspace / "team" / "roster" / "team_roster_v3.csv":
        "name,role,email\nChen Wei,PM,chenwei@corp.example\nFatima,ENG,fatima@corp.example\n",
    workspace / "team" / "assignments" / "sprint14_assignments.txt":
        "Sprint 14 assignments — see Jira board for details.",
    workspace / "projects" / "atlas" / "backlog" / "backlog_items_dump.json":
        json.dumps([{"id": f"ATLAS-{i}", "title": f"Task {i}", "status": "open"} for i in range(1, 20)]),
    workspace / "projects" / "atlas" / "specs" / "api_spec_v2.yaml":
        "openapi: 3.0.0\ninfo:\n  title: Atlas API\n  version: 2.0.0\npaths: {}\n",
    workspace / "admin" / "templates" / "generic_email_template.txt":
        "Hi {{name}},\n\nPlease find attached...\n\nBest,\n{{sender}}",
    workspace / "admin" / "logs" / "system_audit_2024.log":
        "2024-05-01 INFO system started\n2024-05-10 WARN high memory usage\n",
    workspace / "admin" / "logs" / "followup_history.jsonl":
        "\n".join(json.dumps({"id": f"MTG-2024-Q2-0{i}", "status": "processed"}) for i in range(1, 7)),
    workspace / "skills" / "follow-up-commander" / "tests" / "known_good_output_stub.txt":
        "This file is intentionally left blank. Run smoke-test to regenerate.",
}
for path, content in distractors.items():
    path.write_text(content, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Raw meeting notes: {raw_notes_path}")
print(f"Skill base dir:    {skill_base}")