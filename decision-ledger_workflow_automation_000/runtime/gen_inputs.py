import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory skeleton ──────────────────────────────────────────────
dirs = [
    "skills/decision-ledger/scripts",
    "skills/decision-ledger/resources",
    "skills/decision-ledger/examples",
    "skills/decision-ledger/tests",
    "project/infra-phase2/meetings",
    "project/infra-phase2/contracts",
    "project/infra-phase2/reports",
    "project/stakeholders",
    "archive/2023/q4",
    "archive/2024/q1",
    "tmp/scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ────────────────────────────────────────────────
distractors = {
    "project/infra-phase2/contracts/contract_v2.txt": (
        "CONTRACT REF: INFRA-2024-887\n"
        "Parties: Northgate Civil Ltd, Riverstone Council\n"
        "Scope: Phase 2 bridge reinforcement works.\n"
        "Penalty clause: 0.5% per day delay.\n"
        "Sign date: 2024-03-01\n"
    ),
    "project/infra-phase2/reports/risk_register.csv": (
        "risk_id,description,likelihood,impact\n"
        "R001,Ground subsidence near pier 4,medium,high\n"
        "R002,Supplier delay for steel beams,high,medium\n"
        "R003,Regulatory approval lag,low,high\n"
    ),
    "project/stakeholders/contact_list.txt": (
        "Alice Tran - Project Director - alice@northgate.example\n"
        "Bob Mensah - Structural Lead - bob@northgate.example\n"
        "Carol Lin - Procurement - carol@northgate.example\n"
        "David Park - Site Safety Officer - david@northgate.example\n"
        "Emma Zhou - Client Rep (Riverstone) - emma@riverstone.example\n"
    ),
    "archive/2023/q4/old_minutes_2023-11-15.txt": (
        "Meeting: Q4 Planning\nDate: 2023-11-15\n"
        "Decision: Defer steel order to Q1 2024. Owner: Carol Lin.\n"
        "Note: Budget frozen pending audit.\n"
    ),
    "archive/2024/q1/minutes_2024-02-08.txt": (
        "Meeting: Q1 Kickoff\nDate: 2024-02-08\n"
        "Agreed to proceed with Phase 2 mobilisation by end of February.\n"
        "Owner: Alice Tran. Budget confirmed: £2.3M.\n"
    ),
    "tmp/scratch/draft_email.txt": (
        "Hi team,\nJust a reminder that the pier inspection is TBD.\n"
        "No formal decision yet on subcontractor selection.\n"
    ),
    "project/infra-phase2/meetings/agenda_2024-07-10.txt": (
        "AGENDA – 10 July 2024 Progress Meeting\n"
        "1. Steel delivery update\n2. Subcontractor shortlist review\n"
        "3. Safety audit scheduling\n4. Budget variance discussion\n"
        "5. AOB\n"
    ),
    "project/stakeholders/org_chart.txt": (
        "Northgate Civil Ltd\n  └── Alice Tran (Project Director)\n"
        "       ├── Bob Mensah (Structural Lead)\n"
        "       │    └── Site Team A, B\n"
        "       ├── Carol Lin (Procurement)\n"
        "       └── David Park (Safety)\n"
    ),
    "archive/2024/q1/budget_summary.txt": (
        "Phase 2 Budget Summary – Q1 2024\n"
        "Total approved: £2,300,000\n"
        "Spent to date: £340,000\n"
        "Forecast to complete: £2,100,000 (over by £140k, flagged)\n"
    ),
    "tmp/scratch/notes.txt": (
        "Random personal notes:\n"
        "- Call Bob re: rebar specs\n"
        "- Check council planning portal\n"
        "- REMINDER: Emma's feedback due Friday\n"
    ),
}

for rel_path, content in distractors.items():
    with open(os.path.join(workspace, rel_path), "w", encoding="utf-8") as f:
        f.write(content)

# ── skill spec.json (canonical schema the agent must follow) ────────
spec = {
    "version": "1.0.0",
    "output_sections": [
        {
            "key": "confirmed_decisions",
            "label": "已确认决策",
            "required": True,
            "item_fields": ["id", "description", "owner", "deadline", "status"],
            "status_values": ["已确认", "待确认"]
        },
        {
            "key": "pending_items",
            "label": "待确认事项",
            "required": True,
            "description": "Items where information is explicitly missing or ambiguous; must NOT be fabricated."
        },
        {
            "key": "owners_and_deadlines",
            "label": "负责人和截止日",
            "required": True,
            "item_fields": ["decision_id", "owner", "deadline"],
            "note": "Deadline format: YYYY-MM-DD. If unknown, write '待确认'."
        },
        {
            "key": "assumptions",
            "label": "前提假设",
            "required": True,
            "item_fields": ["assumption", "source", "inferred"],
            "note": "If assumption is not stated explicitly, set inferred=true and tag with 【推断】."
        },
        {
            "key": "revocation_conditions",
            "label": "推翻条件",
            "required": True,
            "item_fields": ["decision_id", "condition"],
            "note": "Conditions under which a decision would be revoked or revisited."
        },
        {
            "key": "followup_dependencies",
            "label": "后续依赖",
            "required": True,
            "item_fields": ["description", "depends_on", "blocking"]
        }
    ],
    "inference_tag": "【推断】",
    "pending_marker": "待确认",
    "prohibited": [
        "Do not fabricate decisions not present in the source material.",
        "Do not omit pending_items when information is missing.",
        "Do not suppress revocation_conditions even if speculative."
    ],
    "output_format": "markdown",
    "cli": {
        "command": "python3",
        "script": "{baseDir}/scripts/run.py",
        "args": ["--input", "<input_file>", "--output", "<output_file>"]
    }
}

with open(os.path.join(workspace, "skills/decision-ledger/resources/spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)

# ── template.md (output template the agent must follow) ─────────────
template_md = """\
# 决策台账

> 来源：{source}
> 生成日期：{date}

---

## 已确认决策

| ID | 决策描述 | 负责人 | 截止日 | 状态 |
|----|----------|--------|--------|------|
| {id} | {description} | {owner} | {deadline} | {status} |

---

## 待确认事项

- {pending_item_1}
- {pending_item_2}

---

## 负责人和截止日

| 决策ID | 负责人 | 截止日 |
|--------|--------|--------|
| {decision_id} | {owner} | {deadline} |

---

## 前提假设

- {assumption} — 来源：{source} {inferred_tag}

---

## 推翻条件

| 决策ID | 推翻条件 |
|--------|----------|
| {decision_id} | {condition} |

---

## 后续依赖

- {description}（依赖：{depends_on}，是否阻塞：{blocking}）

---
*本台账为可审阅草案，未经授权不得执行。*
"""

with open(os.path.join(workspace, "skills/decision-ledger/resources/template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)

# ── run.py (the processing script) ─────────────────────────────────
run_py = '''\
#!/usr/bin/env python3
"""
decision-ledger run.py
Processes a raw meeting notes file and produces a structured decision ledger
conforming to spec.json and template.md.

Usage:
    python3 run.py --input <input_file> --output <output_file>
"""
import argparse
import json
import re
import sys
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).parent.parent
SPEC_PATH = BASE_DIR / "resources" / "spec.json"
TEMPLATE_PATH = BASE_DIR / "resources" / "template.md"

INFERENCE_TAG = "【推断】"
PENDING_MARKER = "待确认"

def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)

def parse_input(text: str) -> dict:
    """
    Heuristic parser: extracts structured fields from messy meeting notes.
    Returns a dict with extracted data ready for ledger generation.
    """
    data = {
        "decisions": [],
        "pending_items": [],
        "assumptions": [],
        "revocation_conditions": [],
        "followup_dependencies": [],
    }

    # --- Decision extraction ---
    decision_patterns = [
        r"(?:决定|决议|DECISION|Decided|Agreed|批准|确认)[：:]\s*(.+)",
        r"D\\d+[.、]\\s*(.+)",
    ]
    owner_patterns = [
        r"(?:负责人|Owner|Responsible)[：:]\s*([\\w\\s]+)",
        r"([\\w\\s]+)\\s+(?:负责|will lead|to own|is responsible)",
    ]
    deadline_patterns = [
        r"(?:截止|Deadline|Due|by)[：:\\s]*([\\d]{4}[-/][\\d]{1,2}[-/][\\d]{1,2})",
        r"(?:by end of|before)\\s+([A-Za-z]+ [\\d]{4})",
    ]
    revoke_patterns = [
        r"(?:如果|If|unless|除非|一旦|当)(.+?)(?:则|,|，|则撤销|则重新讨论)",
    ]

    lines = text.splitlines()
    decision_counter = [0]

    def next_id():
        decision_counter[0] += 1
        return f"D{decision_counter[0]:03d}"

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check for decision signals
        is_decision_line = any(
            re.search(p, line, re.IGNORECASE) for p in decision_patterns
        )
        if is_decision_line:
            # Extract description
            desc = line
            for p in decision_patterns:
                m = re.search(p, line, re.IGNORECASE)
                if m:
                    desc = m.group(1).strip()
                    break

            # Look ahead for owner/deadline in next 5 lines
            context_lines = lines[i:min(i+6, len(lines))]
            context = " ".join(context_lines)

            owner = PENDING_MARKER
            for p in owner_patterns:
                m = re.search(p, context, re.IGNORECASE)
                if m:
                    owner = m.group(1).strip()
                    break

            deadline = PENDING_MARKER
            for p in deadline_patterns:
                m = re.search(p, context, re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    # normalise date
                    deadline = re.sub(r"[/]", "-", raw)
                    break

            status = "已确认" if owner != PENDING_MARKER else "待确认"

            did = next_id()
            data["decisions"].append({
                "id": did,
                "description": desc,
                "owner": owner,
                "deadline": deadline,
                "status": status,
            })

            # Revocation conditions
            for p in revoke_patterns:
                for cl in context_lines:
                    m = re.search(p, cl, re.IGNORECASE)
                    if m:
                        data["revocation_conditions"].append({
                            "decision_id": did,
                            "condition": m.group(1).strip() + m.group(0)[m.end(1):].strip(),
                        })

        # Pending / TBD lines
        if re.search(r"\\bTBD\\b|待定|未定|尚未确认|to be confirmed|pending|unclear", line, re.IGNORECASE):
            data["pending_items"].append(line)

        # Assumption lines
        if re.search(r"假设|assume|assuming|前提|based on assumption", line, re.IGNORECASE):
            inferred = not re.search(r"明确|explicitly|stated", line, re.IGNORECASE)
            data["assumptions"].append({
                "assumption": line,
                "source": "meeting notes",
                "inferred": inferred,
            })

        # Dependency lines
        if re.search(r"依赖|depends on|blocked by|waiting for|before we can", line, re.IGNORECASE):
            data["followup_dependencies"].append({
                "description": line,
                "depends_on": PENDING_MARKER,
                "blocking": "是",
            })

        i += 1

    # If nothing found, add a blanket pending item
    if not data["decisions"] and not data["pending_items"]:
        data["pending_items"].append("未能从输入中提取到明确决策，请人工复核。")

    # Generate inferred assumptions for decisions without explicit deadline
    for dec in data["decisions"]:
        if dec["deadline"] == PENDING_MARKER:
            data["assumptions"].append({
                "assumption": f"决策 {dec[\'id\']} 的截止日期尚未明确",
                "source": "自动推断",
                "inferred": True,
            })

    return data


def render_ledger(data: dict, source_name: str) -> str:
    spec = load_spec()
    today = date.today().isoformat()
    lines = []

    lines.append("# 决策台账")
    lines.append("")
    lines.append(f"> 来源：{source_name}")
    lines.append(f"> 生成日期：{today}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 1: confirmed decisions
    lines.append("## 已确认决策")
    lines.append("")
    lines.append("| ID | 决策描述 | 负责人 | 截止日 | 状态 |")
    lines.append("|----|----------|--------|--------|------|")
    if data["decisions"]:
        for d in data["decisions"]:
            lines.append(
                f"| {d[\'id\']} | {d[\'description\']} | {d[\'owner\']} | {d[\'deadline\']} | {d[\'status\']} |"
            )
    else:
        lines.append("| — | 无已确认决策 | — | — | 待确认 |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 2: pending items
    lines.append("## 待确认事项")
    lines.append("")
    if data["pending_items"]:
        for item in data["pending_items"]:
            lines.append(f"- {item}")
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 3: owners and deadlines
    lines.append("## 负责人和截止日")
    lines.append("")
    lines.append("| 决策ID | 负责人 | 截止日 |")
    lines.append("|--------|--------|--------|")
    if data["decisions"]:
        for d in data["decisions"]:
            lines.append(f"| {d[\'id\']} | {d[\'owner\']} | {d[\'deadline\']} |")
    else:
        lines.append("| — | — | — |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 4: assumptions
    lines.append("## 前提假设")
    lines.append("")
    if data["assumptions"]:
        for a in data["assumptions"]:
            tag = f" {spec[\'inference_tag\']}" if a.get("inferred") else ""
            lines.append(f"- {a[\'assumption\']} — 来源：{a[\'source\']}{tag}")
    else:
        lines.append("- 无明确前提假设")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 5: revocation conditions
    lines.append("## 推翻条件")
    lines.append("")
    lines.append("| 决策ID | 推翻条件 |")
    lines.append("|--------|----------|")
    if data["revocation_conditions"]:
        for r in data["revocation_conditions"]:
            lines.append(f"| {r[\'decision_id\']} | {r[\'condition\']} |")
    else:
        lines.append("| — | 无明确推翻条件 |")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Section 6: followup dependencies
    lines.append("## 后续依赖")
    lines.append("")
    if data["followup_dependencies"]:
        for dep in data["followup_dependencies"]:
            lines.append(
                f"- {dep[\'description\']}（依赖：{dep[\'depends_on\']}，是否阻塞：{dep[\'blocking\']}）"
            )
    else:
        lines.append("- 无明确后续依赖")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*本台账为可审阅草案，未经授权不得执行。*")

    return "\\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Decision Ledger Generator")
    parser.add_argument("--input", required=True, help="Path to raw meeting notes file")
    parser.add_argument("--output", required=True, help="Path to write the decision ledger")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    source_name = input_path.name

    parsed = parse_input(text)
    ledger = render_ledger(parsed, source_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(ledger, encoding="utf-8")
    print(f"Decision ledger written to: {output_path}")


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "skills/decision-ledger/scripts/run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)

# ── smoke-test.md ────────────────────────────────────────────────────
smoke_test = """\
# Smoke Test – Decision Ledger

## Test Input
Short meeting notes with one clear decision, one TBD item, and one assumption.

## Expected Behaviour
- run.py completes without error.
- Output contains all 6 sections.
- TBD items appear under 待确认事项.
- Inferred items are tagged with 【推断】.
- Audit footer is present.
"""

with open(os.path.join(workspace, "skills/decision-ledger/tests/smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_test)

# ── Example I/O ─────────────────────────────────────────────────────
example_input = """\
Meeting: Phase 1 Close-out – 2024-05-20
Attendees: Alice Tran, Bob Mensah, Carol Lin

决定：关闭 Phase 1 账目，移交资产清单至采购部门。
负责人：Carol Lin
截止：2024-06-30
如果审计发现差异，则重新开放账目。

TBD: Phase 2 开工日期未定，等待规划局批复。

假设：规划局将在6月内批复（尚未明确）。
"""

example_output = """\
# 决策台账

> 来源：example_input.txt
> 生成日期：2024-05-20

---

## 已确认决策

| ID | 决策描述 | 负责人 | 截止日 | 状态 |
|----|----------|--------|--------|------|
| D001 | 关闭 Phase 1 账目，移交资产清单至采购部门。 | Carol Lin | 2024-06-30 | 已确认 |

---

## 待确认事项

- TBD: Phase 2 开工日期未定，等待规划局批复。

---

## 负责人和截止日

| 决策ID | 负责人 | 截止日 |
|--------|--------|--------|
| D001 | Carol Lin | 2024-06-30 |

---

## 前提假设

- 假设：规划局将在6月内批复（尚未明确）。 — 来源：meeting notes 【推断】

---

## 推翻条件

| 决策ID | 推翻条件 |
|--------|----------|
| D001 | 审计发现差异 |

---

## 后续依赖

- 无明确后续依赖

---
*本台账为可审阅草案，未经授权不得执行。*
"""

with open(os.path.join(workspace, "skills/decision-ledger/examples/example_input.txt"), "w", encoding="utf-8") as f:
    f.write(example_input)

with open(os.path.join(workspace, "skills/decision-ledger/examples/example_output.md"), "w", encoding="utf-8") as f:
    f.write(example_output)

# ── THE ACTUAL TASK INPUT: messy, multi-source meeting notes ─────────
# This is intentionally messy with:
# - Mixed Chinese/English
# - Multiple decisions with different information completeness
# - Implicit assumptions not stated as such
# - TBD items scattered throughout
# - Revocation conditions embedded in sentences
# - Dependency references
raw_meeting_notes = """\
NORTHGATE CIVIL LTD – PHASE 2 BRIDGE REINFORCEMENT
Progress Meeting Notes – 10 July 2024
Location: Site Office A / Video call
Attendees: Alice Tran (Chair), Bob Mensah, Carol Lin, David Park, Emma Zhou (Riverstone Council)

=== STEEL DELIVERY UPDATE ===

Carol reported that Steelco has confirmed partial delivery of Grade S355 rebar — 40 tonnes arriving 2024-07-25.
决定：接受 Steelco 部分交付，剩余 60 吨推迟至 2024-08-15。
负责人：Carol Lin
截止日：2024-07-18（需在收货前签署修订采购订单）
如果 Steelco 无法保证 2024-08-15 到货，则重新开放供应商招标。

Bob noted that rebar placement drawings must be updated before steel arrives.
ACTION: Bob Mensah to update pier 4 rebar drawings. Deadline: 2024-07-20.
If ground survey results (due 2024-07-12) reveal subsidence beyond 15mm, pier 4 design must be fully revisited.

=== SUBCONTRACTOR SHORTLIST ===

Discussed three shortlisted firms: FastBuild Ltd, Apex Groundworks, and TerraForm Civil.
决议：授权 Carol Lin 发出邀请招标书（ITT）给三家入围公司。
截止日：2024-07-22（ITT 发出截止）
负责人：Carol Lin
如果有入围公司在 2024-07-22 前撤出，需重新评估资格名单。

TBD: 最终分包商选择日期 — 待收到报价后评估，预计 2024-08-10 前完成，但未正式确认。

Assuming all three shortlisted firms will respond to the ITT within 14 days (not explicitly confirmed by firms).

=== SAFETY AUDIT ===

David Park raised that the mandatory safety audit has not been scheduled.
决定：安排安全审计，目标周为 2024-08-05 至 2024-08-09。
Owner: TBD — David to confirm with approved auditor by 2024-07-17.
如果 2024-07-17 前未能确认审计师，则将目标周推迟一周并上报至 Alice Tran。

Assumed that the approved auditor list (held by head office) is current — this has not been verified this year.

=== BUDGET VARIANCE ===

Emma Zhou (Riverstone Council) flagged concern over the £140k projected overrun.
决议：提交预算差异说明报告至 Riverstone Council，附补救方案。
负责人：Alice Tran
截止日：2024-07-31
如果 Riverstone Council 不接受补救方案，则暂停所有非关键路径工作，待进一步指示。

Before we can submit the report, Alice needs sign-off from the Finance Director (name TBD).
Depends on: Finance Director approval (pending identification of current post-holder).

=== AOB ===

Bob mentioned that the ground survey vendor (GeoScan Ltd) has not sent the pier 4 subsidence report yet.
TBD: GeoScan subsidence report — expected 2024-07-12 but not confirmed.

Emma noted that Riverstone Council planning portal approval is still pending.
Waiting for: planning portal decision reference number.

Next meeting: TBD — Alice to circulate date by end of week.
"""

raw_notes_path = os.path.join(workspace, "project/infra-phase2/meetings/minutes_2024-07-10_raw.txt")
with open(raw_notes_path, "w", encoding="utf-8") as f:
    f.write(raw_meeting_notes)

print("Workspace generated successfully.")
print(f"Raw meeting notes: {raw_notes_path}")
print(f"Skill base dir: {os.path.join(workspace, 'skills/decision-ledger')}")