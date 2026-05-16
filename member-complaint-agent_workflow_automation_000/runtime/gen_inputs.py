import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "issues",
    "references",
    "sop",
    "logs/archive",
    "logs/daily",
    "members/profiles",
    "members/tiers",
    "configs",
    "templates/reply",
    "templates/analysis",
    "digests",
    "exports",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = r"""---
name: member-complaint-agent
description: Handle member/customer complaint workflows with a Linear-centered operating model. Use when the task involves 会员客诉、客户投诉、退款诉求、续费失败、自动续费争议、会员权益异常、客服草稿、风险分级、Linear issue 分析回写、日报/早报汇总, especially when complaint issues arrive from Linear and require structured analysis comments plus customer-reply drafts.
---

# Member Complaint Agent

## Overview

Turn complaint issues into a structured case analysis and a usable reply draft.

Default operating model for this skill:
- treat **Linear as the only action surface**
- treat Feishu or other chat channels as read-only display unless the user explicitly asks otherwise
- parse deterministic metadata with rules first
- use AI for intent, risk, tone, and drafting

Do not promise compensation, refunds, exceptions, or timelines unless the user provides the exact policy.

## Linear-Centered Workflow

### 1. Intake from Linear issue

When the source is a Linear issue, extract these fields first if present:
- issue id / issue url
- raw customer message
- member identifier
- membership tier
- metadata tags like platform, vendor, app version, device model, os version, product line
- links to logs, profile page, or feedback page

Keep a clean separation between:
- raw facts from the issue
- deterministic parses from metadata
- AI judgments

### 2. Deterministic metadata parse

Parse these with rules, not AI, whenever they are available in metadata:
- platform: iOS / Android / other
- vendor: Apple / OPPO / HONOR / Xiaomi / Vivo / Huawei / unknown
- app version
- device model
- OS version
- product line or package

Examples:
- `[PLUS会员][iOS][5.8.1(136138)][iPhone 12 Pro Max][26.2][plus]`
- `[android][5.3.10 (1571, honor)][HONOR ANY-AN00][13 (33)][plus]`

If metadata is ambiguous, say it is ambiguous instead of guessing.

### 3. Complaint analysis

Use AI for these judgments:
- primary intent
- subtype
- emotion intensity
- risk level
- whether SOP should be referenced
- whether escalation is needed
- what missing information would improve handling

Use this v1 taxonomy unless the user provides a more specific business taxonomy:
- refund-request
- auto-renew-dispute
- renewal-failure
- membership-rights-issue
- product-bug-or-function-failure
- service-attitude-complaint
- expectation-mismatch
- other

Typical mappings:
- `还是想退了` -> `refund-request`
- `我的账号不能续费了` -> `renewal-failure`

### 4. SOP routing

When a complaint is channel-dependent, route by parsed platform/vendor before drafting:
- iOS / Apple related purchase or refund issues -> Apple/iOS SOP
- Android + vendor-specific billing/renewal issue -> vendor SOP when available
- no SOP available -> say SOP not loaded and avoid inventing steps

Treat SOPs as authoritative only when the user has actually provided them.

### 5. Write back two Linear comments

Default output is two comments, not one.

#### Comment A: AI analysis comment

Use this structure:

```text
【AI客诉分析】
- 客诉类型：
- 子意图：
- 情绪强度：低 / 中 / 高
- 风险等级：低 / 中 / 高 / 升级
- 渠道识别：
- 会员信息：
- 是否命中SOP：是 / 否 / 待确认
- 是否建议升级：是 / 否
- 判断依据：
  1.
  2.
  3.
- 待补充信息：
  1.
  2.
```

#### Comment B: customer reply draft

Use this structure:

```text
【对客回复草稿】
您好，

...

【客服发送前检查】
- 需补充变量：
- 禁止承诺项：
- 建议时效：
```

Keep the customer draft short, calm, and directly usable by support staff.

### 6. Daily digest mode

When asked for a daily report / morning brief from complaint issues, summarize:
- total issue count
- intent distribution
- platform/vendor distribution
- unresolved issues older than 12 hours
- high-risk issues
- top recurring causes
- ratio of refund / rights-related complaints if available

Do not fake metrics if the underlying issue list is incomplete.

## Output Rules

### Separate fact from judgment

Always label the difference between:
- confirmed facts from issue content
- inferred classification
- recommended action

### Prefer minimum-safe drafting

If the case touches refunds, legal risk, privacy, or public escalation:
- acknowledge the issue
- summarize what is known
- recommend next step
- avoid final commitments unless backed by policy

## Guardrails

- Do not invent refund policy or channel rules.
- Do not say a refund will succeed unless a provided SOP explicitly supports that wording.
- Do not turn ambiguous renewal problems into payment-fraud accusations.
- Do not present metadata guesses as facts.
- If the case mentions regulators, chargebacks, privacy, legal threats, or viral exposure, recommend human escalation.
- If a required SOP is missing, say what is missing.

## References

Read `references/complaint-playbook.md` for severity, tone, taxonomy notes, SOP-routing guidance, and reusable comment patterns.
"""
(WORKSPACE / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── references/complaint-playbook.md ────────────────────────────────────────
playbook = """# Complaint Playbook

## Severity Tiers

| Level   | Criteria                                           |
|---------|----------------------------------------------------|
| 低      | First contact, no financial loss, calm tone        |
| 中      | Repeated contacts, emotion rising, or payment affected |
| 高      | Legal threat, chargeback mention, viral risk       |
| 升级    | Regulator mention, media exposure, data privacy    |

## Tone Guidelines

- Stay neutral and empathetic.
- Avoid definitive commitments without policy backing.
- For refund disputes: acknowledge, do not promise outcome.

## Taxonomy Notes

- `auto-renew-dispute`: user did not knowingly authorize, or renewal happened after cancel attempt
- `renewal-failure`: user tried to renew but system prevented it
- These two are often confused; parse the complaint carefully.

## SOP Routing

- HONOR vendor: check HONOR-specific billing SOP before drafting refund steps
- If SOP file is absent from workspace, state "HONOR厂商SOP未加载，建议联系相关渠道核实"

## Reusable Patterns

- Opening: 您好，感谢您联系我们。
- Closing: 如有其他问题请随时联系我们。
- Missing info placeholder: [待确认：{variable}]
"""
(WORKSPACE / "references" / "complaint-playbook.md").write_text(playbook, encoding="utf-8")

# ── THE MAIN ISSUE: LINEAR-2847.json ───────────────────────────────────────
issue = {
    "id": "LINEAR-2847",
    "url": "https://linear.app/acme/issue/LINEAR-2847",
    "title": "【会员客诉】自动续费扣款后会员未到账，要求退款",
    "created_at": "2024-07-15T08:23:11Z",
    "status": "open",
    "assignee": None,
    "member_id": "UID-88234701",
    "metadata_raw": "[android][5.3.10 (1571, honor)][HONOR ANY-AN00][13 (33)][plus]",
    "membership_tier": "PLUS会员",
    "customer_message": (
        "你好，我昨天晚上手机自动续费了，扣了我18块钱，但是我的会员到今天早上还没有到账，"
        "APP里显示的还是普通会员。我已经重启了好几次手机了还是没有更新。"
        "我觉得你们这个系统有问题，这种情况不是第一次了。"
        "如果今天还解决不了我就去投诉平台举报你们，我要退款！"
    ),
    "attachments": [
        {"type": "log_link", "url": "https://internal.logs/uid-88234701/renewal-20240715"},
        {"type": "profile_page", "url": "https://internal.members/uid-88234701"}
    ],
    "tags": ["auto-renew", "honor", "plus", "payment"],
    "comments": []
}
(WORKSPACE / "issues" / "LINEAR-2847.json").write_text(
    json.dumps(issue, ensure_ascii=False, indent=2), encoding="utf-8"
)

# ── distractor issue files ───────────────────────────────────────────────────
distractor_issues = [
    {
        "id": "LINEAR-2841",
        "title": "iOS用户无法下载会员内容",
        "metadata_raw": "[PLUS会员][iOS][5.8.1(136138)][iPhone 12 Pro Max][26.2][plus]",
        "status": "resolved",
        "customer_message": "下载按钮点不了，但是我有会员的。",
        "comments": [{"author": "cs_agent", "body": "已处理"}]
    },
    {
        "id": "LINEAR-2835",
        "title": "Xiaomi设备续费失败",
        "metadata_raw": "[android][5.2.9 (1520, xiaomi)][Xiaomi MI-10][12 (32)][standard]",
        "status": "open",
        "customer_message": "小米手机无法续费，一直报错。",
        "comments": []
    },
    {
        "id": "LINEAR-2800",
        "title": "用户投诉客服态度差",
        "metadata_raw": "",
        "status": "closed",
        "customer_message": "上次的客服太冷漠了，完全不解决问题。",
        "comments": [{"author": "cs_lead", "body": "已跟进"}]
    }
]
for di in distractor_issues:
    fname = f"{di['id']}.json"
    (WORKSPACE / "issues" / fname).write_text(
        json.dumps(di, ensure_ascii=False, indent=2), encoding="utf-8"
    )

# ── distractor SOP stubs (not the HONOR sop — intentionally missing) ────────
ios_sop = """# Apple / iOS Refund SOP

1. Verify purchase via App Store receipt.
2. Direct user to Settings > Apple ID > Subscriptions.
3. If charge unrecognized, guide to reportaproblem.apple.com.
4. Do NOT process refund directly; Apple controls iOS billing.
"""
(WORKSPACE / "sop" / "ios_apple_sop.md").write_text(ios_sop, encoding="utf-8")

xiaomi_sop = """# Xiaomi Billing SOP

1. Confirm Xiaomi Pay binding status.
2. Check renewal order in Xiaomi account center.
3. If failed: clear cache, retry after 24h.
"""
(WORKSPACE / "sop" / "xiaomi_billing_sop.md").write_text(xiaomi_sop, encoding="utf-8")

# NOTE: honor_sop.md is intentionally NOT created — agent must note SOP missing

# ── distractor config / log files ───────────────────────────────────────────
(WORKSPACE / "configs" / "agent_config.yaml").write_text(
    "model: gpt-4o\nmax_tokens: 2048\ntemperature: 0.3\n", encoding="utf-8"
)

(WORKSPACE / "logs" / "archive" / "2024-07-14.log").write_text(
    "2024-07-14 10:00:01 INFO renewal job started\n"
    "2024-07-14 10:00:45 ERROR uid-99123 payment gateway timeout\n"
    "2024-07-14 10:01:02 INFO renewal job finished\n",
    encoding="utf-8"
)

(WORKSPACE / "logs" / "daily" / "2024-07-15.log").write_text(
    "2024-07-15 08:22:58 INFO auto-renew batch start uid-88234701\n"
    "2024-07-15 08:23:05 INFO payment deducted uid-88234701 amount=18.00\n"
    "2024-07-15 08:23:07 ERROR membership_grant failed uid-88234701 code=5031\n",
    encoding="utf-8"
)

(WORKSPACE / "members" / "profiles" / "UID-88234701.json").write_text(
    json.dumps({
        "uid": "UID-88234701",
        "tier": "standard",
        "last_renewed": "2024-07-15T08:23:05Z",
        "payment_status": "deducted",
        "grant_status": "failed",
        "device_last_seen": "HONOR ANY-AN00"
    }, ensure_ascii=False, indent=2), encoding="utf-8"
)

(WORKSPACE / "members" / "tiers" / "tier_config.json").write_text(
    json.dumps({
        "PLUS": {"price_monthly": 18, "features": ["4K", "download", "no-ads"]},
        "standard": {"price_monthly": 6, "features": ["HD", "no-ads"]}
    }, ensure_ascii=False, indent=2), encoding="utf-8"
)

(WORKSPACE / "digests" / "2024-07-14_digest.md").write_text(
    "# 2024-07-14 日报\n\n- 共 12 个客诉\n- refund-request: 4\n- renewal-failure: 5\n- other: 3\n",
    encoding="utf-8"
)

(WORKSPACE / "exports" / "README_exports.txt").write_text(
    "Export files for BI dashboard. CSV format. Auto-generated nightly.\n",
    encoding="utf-8"
)

(WORKSPACE / "templates" / "reply" / "generic_reply.txt").write_text(
    "您好，感谢您的反馈，我们已收到您的问题，将尽快处理。\n",
    encoding="utf-8"
)

(WORKSPACE / "templates" / "analysis" / "analysis_template.txt").write_text(
    "【AI客诉分析】\n- 客诉类型：\n- 子意图：\n...\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {list(WORKSPACE.rglob('*'))}")