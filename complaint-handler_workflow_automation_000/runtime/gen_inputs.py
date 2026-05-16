import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "skill/references",
    "skill/configs",
    "data/incoming",
    "data/archive",
    "data/processed",
    "logs/errors",
    "logs/audit",
    "configs/legacy",
    "reports/daily",
    "reports/weekly",
    "tools/scripts",
    "tools/validators",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "skill/configs/shipping_policy.json": json.dumps({"free_shipping_threshold": 99, "regions": ["CN", "HK"]}),
    "skill/configs/loyalty_tiers.json": json.dumps({"bronze": 0, "silver": 500, "gold": 2000}),
    "data/archive/q1_complaints_summary.csv": "id,class,level\n1001,quality_issue,L1\n1002,refund_request,L2",
    "data/archive/old_templates.txt": "Template A: Sorry for the inconvenience...\nTemplate B: We value your feedback...",
    "logs/errors/error_log_20240101.txt": "ERR: Connection timeout at 14:32:01\nERR: DB write failed at 14:33:07",
    "logs/audit/audit_trail.jsonl": '{"event":"login","user":"agent01","ts":"2024-01-15T09:00:00Z"}\n{"event":"ticket_close","id":"T-991","ts":"2024-01-15T09:45:00Z"}',
    "configs/legacy/permissions_v1.json": json.dumps({"refund_auto_approve_limit": 200, "escalation_contact": "manager@old.com"}),
    "reports/daily/2024-01-14.json": json.dumps({"total_tickets": 42, "resolved": 38, "escalated": 4}),
    "reports/weekly/week02.json": json.dumps({"top_issue": "size_fit_issue", "satisfaction_score": 3.8}),
    "tools/scripts/batch_import.sh": "#!/bin/bash\necho 'Importing batch data...'\n",
    "tools/validators/schema_check.py": "import json\ndef validate(data): return True",
    "data/processed/.keep": "",
}
for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- permissions_config (Step 09 output, as described in SKILL.md) ---
permissions_config = {
    "refund_auto_approve_limit": 0,
    "refund_small_threshold": 100,
    "refund_large_threshold": 500,
    "l2_contact": "supervisor@retailshop.cn",
    "l3_contact": "senior_ops@retailshop.cn",
    "exchange_window_days": 15,
    "quality_claim_window_days": 30,
    "escalation_packet_fields": ["issue_id", "customer_id", "class", "level", "keyword_matched", "summary", "contact"]
}
with open(os.path.join(WORKSPACE, "skill/configs/permissions_config.json"), "w", encoding="utf-8") as f:
    json.dump(permissions_config, f, ensure_ascii=False, indent=2)

# --- SKILL.md and references ---
skill_md = r"""---
name: complaint-handler
description: >
  Retail complaint and after-sales handler for digital employees.
  Classifies complaints, generates empathetic responses, routes escalations,
  and manages return/exchange/refund requests according to configured policy.
  Use when a customer expresses dissatisfaction, reports a product issue,
  requests a refund or exchange, or makes a complaint.
  Triggers on: 投诉, 质量问题, 退款, 换货, 坏了, 破损, 不满意, 差评,
  want to return, product broken, request refund, poor quality, complaint,
  this is unacceptable, I want to speak to a manager.
metadata:
  openclaw:
    emoji: 🎧
---

# Complaint Handler

## Overview

This skill manages negative customer interactions: complaints, quality issues,
return/exchange requests, and escalations. Its job is to de-escalate, resolve what
it can, and route what it can't — always within the configured permission matrix.

**Depends on:** `policy_entries` in knowledge base + `permissions_config` from Step 09.

---

## Complaint Classification

Classify every incoming complaint before responding:

| Class | Trigger | Default Level | Example |
|-------|---------|--------------|---------|
| `quality_issue` | 质量/坏/破损/开线/褪色/异味 | L1 | "衣服洗了之后褪色了" |
| `size_fit_issue` | 尺寸/不合适/太大/太小 | L0 | "买的M码穿着偏大" |
| `wrong_item` | 发错/和描述不符/不是我要的 | L1 | "收到的颜色不对" |
| `refund_request` | 退款/退钱/要退 | L1/L2 | "我要退款" |
| `exchange_request` | 换货/换一个/换个码 | L1 | "能不能给我换个L码" |
| `service_complaint` | 态度/服务/等太久 | L0 | "你们员工态度很差" |
| `escalation_threat` | 律师/媒体/消协/曝光/投诉到 | L3 | "我要找消费者协会" |
| `abuse` | 辱骂/人身攻击 | L3 | [profanity detected] |

**Reference:** [classification-guide.md](references/classification-guide.md)

---

## Response Protocol

### Step 1: Acknowledge (always first)
Never jump to solutions without acknowledging the customer's frustration.
Template: "非常抱歉给您带来不便，我完全理解您现在的感受。"
Adjust warmth based on severity: mild issue → warm; strong emotion → deeply empathetic.

### Step 2: Clarify (if needed)
Ask one targeted question to understand the situation:
- "请问是什么时候购买的呢？"
- "方便描述一下具体是什么问题吗？"
Never ask multiple questions at once.

### Step 3: Apply Policy
Look up the relevant policy from knowledge base. Apply exactly.
- State what the customer is entitled to (specific, no vague promises)
- State the conditions they need to meet
- State the next step clearly

### Step 4: Execute or Escalate
- L0: Handle fully, confirm resolution
- L1: Propose action, wait for staff confirmation tap
- L2: Create ticket, notify manager, give customer ETA
- L3: Immediately hand off to human, stay on standby

**Reference:** [response-templates.md](references/response-templates.md)

---

## Escalation Triggers (Auto L3)

Always escalate to L3 immediately on detection of:
- Legal keywords: 律师, 法院, 起诉, 法律途径
- Media keywords: 媒体, 曝光, 记者, 微博, 抖音发
- Authority keywords: 消协, 12315, 工商, 监管
- Repeated contact: same issue raised 3+ times
- Explicit threat: 骗子, 假货, 虚假宣传
- Abuse: profanity or personal attacks

**On L3 trigger:**
1. Stop trying to resolve
2. Acknowledge and transfer: "您的情况非常重要，我马上为您转接专属客服，请稍候。"
3. Send escalation packet to L3 contact (see `permissions_config`)
4. Do NOT argue, defend, or explain further

---

## What This Skill Will Never Do

- Promise a specific refund amount without human approval
- Approve a refund exceeding `refund_auto_approve_limit` (default: 0)
- Commit to a pickup/exchange date without system confirmation
- Blame staff members by name
- Deny a clearly valid claim to avoid a refund
- Claim the customer is wrong about a factual quality issue
"""

classification_guide = r"""# Complaint Classification Guide

## Two-Pass Classification

### Pass 1: Check for immediate L3 triggers (keyword scan)
Run before any other processing. If any trigger matches → L3 immediately, no further analysis.

**L3 keyword groups:**
```
legal:    律师, 法院, 起诉, 法律途径, 诉讼, 打官司
media:    媒体, 曝光, 记者, 微博, 抖音, 小红书发, 直播
authority: 消协, 12315, 工商局, 市场监管, 食药监
threat:   骗子, 假货, 欺诈, 虚假宣传, 坑人, 黑心
repeat:   (same issue_id seen 3+ times in session history)
```

If L3 triggered: log `{ "class": "escalation_threat", "level": "L3", "keyword": "<matched>" }`
then execute L3 handoff immediately.

---

### Pass 2: Classify complaint type

Score each class based on keyword presence in the message:

| Class | Keywords | Score trigger |
|-------|---------|--------------|
| `quality_issue` | 质量, 坏了, 破损, 开线, 褪色, 起球, 异味, 变形, 脱色, 有问题 | ≥ 1 match |
| `size_fit_issue` | 尺寸, 不合适, 太大, 太小, 偏大, 偏小, 换码, 换个码, 版型 | ≥ 1 match |
| `wrong_item` | 发错, 不对, 和图片不一样, 不是我要的, 颜色不对, 款式不对 | ≥ 1 match |
| `refund_request` | 退款, 退钱, 要退, 不要了, 申请退 | ≥ 1 match |
| `exchange_request` | 换货, 换一个, 换个, 重发, 补发 | ≥ 1 match |
| `service_complaint` | 态度, 服务, 等太久, 没人理, 不专业, 冷漠 | ≥ 1 match |
| `general_dissatisfaction` | 不满意, 失望, 很差, 很烂, 差评 | ≥ 1 match |

**Priority order** (when multiple classes match):
1. `quality_issue` (highest — impacts safety/product liability)
2. `wrong_item`
3. `refund_request`
4. `exchange_request`
5. `size_fit_issue`
6. `service_complaint`
7. `general_dissatisfaction` (lowest)

---

## Permission Level Lookup

| Class | Default Level | Override conditions |
|-------|--------------|-------------------|
| `quality_issue` | L1 | → L2 if amount > threshold |
| `size_fit_issue` | L0 | Stock available; else L1 |
| `wrong_item` | L1 | Always — operational error |
| `refund_request` | L1 (< threshold) / L2 (> threshold) | See `permissions_config.refund_small/large` |
| `exchange_request` | L1 | |
| `service_complaint` | L0 | → L2 if customer specifically requests manager |
| `escalation_threat` | L3 | Immediate, no override |
| `general_dissatisfaction` | L0 | |

---

## Context Enrichment

Before responding, collect these contextual facts (ask if not provided):

| Field | Why needed |
|-------|-----------|
| Purchase date | Determines which policy applies (7-day, 30-day, etc.) |
| Product name/SKU | Confirms which item and policy tier |
| Issue description | Determines class and response |
| Purchase channel | Online vs. in-store may have different policies |
| Desired resolution | Refund vs. exchange vs. repair vs. explanation |

Collect only what's missing. Don't interrogate customers who've already given context.
"""

response_templates = r"""# Complaint Response Templates

## Quality Issue (质量问题)

### Opening (always lead with this)
> "非常抱歉！这种情况确实不应该发生，给您带来麻烦了，我非常理解您的心情。"

### After clarifying purchase date & issue:

**Within 7 days, quality issue:**
> "根据我们的质量保障政策，购买7天内出现质量问题，您可以选择：
> ① 免费换货（同款同码，有货情况下）
> ② 全额退款（退款3个工作日内到账）
> 您倾向哪种方式呢？需要您提供一下购买凭证（订单截图或小票）。"

**7–30 days, quality issue:**
> "购买30天内出现质量问题，按我们的三包政策可以免费维修或换货。
> 需要您携带商品和购买凭证到门店，工作人员会为您处理。
> 如果不方便来店，也可以邮寄过来，我们帮您处理好再寄回。"

**Beyond policy window:**
> "您反映的情况我们非常重视。虽然已超出常规退换期，但我会将您的情况提交给店长，
> 看看能为您做些什么。一般会在[X]个工作日内给您回复，请问方便留个联系方式吗？"

---

## Size/Fit Issue (尺寸不合适)

> "尺寸不合适的问题我来帮您解决！
> 购买[X]天内，商品未洗涤、保留吊牌的情况下，可以直接换码。
> 请问您现在有几码，想换成几码？我先帮您查一下有没有货。"

If stock unavailable:
> "[目标尺码]目前暂时没货。您可以：
> ① 等补货（我帮您登记，到货第一时间通知）
> ② 申请退款（[退款条件]）
> 请问您更倾向哪种？"

---

## Wrong Item / Description Mismatch (发错/不符)

> "非常抱歉，这是我们的失误！收到的商品与您选购的不符，完全理解您的不满。
> 我现在帮您走重发流程：
> ① 您需要将收到的商品寄回（运费我们承担）
> ② 确认收货后，我们为您安排正确商品发出
> 预计[X]个工作日内到达。
> 方便提供一下您的收件地址和联系方式吗？"

---

## Refund Request (退款)

**First: establish why (don't assume)**
> "好的，我来帮您处理退款。请问是什么原因想退款呢？（比如不喜欢、质量问题、尺寸不合适等）
> 这样我能确认适用哪种退款政策，更快帮您处理。"

**After clarifying reason, apply matching policy template above.**

**Escalation to L2 (refund > threshold):**
> "您的退款申请我已经提交给店长审核了，通常[X]个工作日内会给您答复。
> 我已经记录了您的全部情况，请放心。"
*(Send escalation packet to L2 contact simultaneously)*

---

## Service Complaint (服务态度)

> "非常感谢您的反馈，也非常抱歉您有这样的体验。
> 我们一直致力于提供优质服务，您的意见对我们非常重要。
> 我会将您的反馈认真记录并转达给管理层。
> 请问还有什么我能为您做的吗？"

*Note: Never name or identify specific staff members in responses.*

---

## Escalation Handoff (L3)

> "您的情况非常重要，我希望能确保您得到最妥善的处理。
> 我现在为您转接专属客服，Ta会直接跟进您的问题，全程负责到底。
> 请稍等片刻，马上有人联系您。"

*(Simultaneously send escalation packet — see permissions_config for format)*

---

## Tone Calibration for Complaints

| Customer Emotion | Agent Tone |
|-----------------|-----------|
| Mildly annoyed | Warm, solution-focused |
| Clearly frustrated | Deeply empathetic, slower pace, fewer options at once |
| Very angry | Acknowledge feelings first, no information overload |
| Threatening | Calm, professional, immediate escalation — no defense |
| Abusive | Brief, firm boundary + immediate L3 handoff |

**Never match negative energy.** Stay calm regardless of tone directed at the agent.
"""

with open(os.path.join(WORKSPACE, "skill/SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_md)
with open(os.path.join(WORKSPACE, "skill/references/classification-guide.md"), "w", encoding="utf-8") as f:
    f.write(classification_guide)
with open(os.path.join(WORKSPACE, "skill/references/response-templates.md"), "w", encoding="utf-8") as f:
    f.write(response_templates)

# --- THE MAIN TASK: incoming complaint batch ---
# 7 complaints with deliberate traps:
# C001: quality_issue only → L1
# C002: quality_issue + refund_request → quality_issue wins (priority) → L1
# C003: L3 trigger (12315) + quality_issue → L3 overrides ALL (Pass 1)
# C004: wrong_item + exchange_request + refund_request → wrong_item wins → L1
# C005: size_fit_issue + general_dissatisfaction → size_fit_issue wins → L0
# C006: refund_request with amount > 500 (large) → L2
# C007: repeat contact (issue_id seen 3rd time in session history) → L3

complaints = [
    {
        "issue_id": "C001",
        "customer_id": "CUST-1001",
        "customer_name": "张伟",
        "message": "我买的羽绒服洗了一次就开线了，质量太差了！",
        "purchase_amount": 350,
        "purchase_days_ago": 12,
        "session_history": []
    },
    {
        "issue_id": "C002",
        "customer_id": "CUST-1002",
        "customer_name": "李娜",
        "message": "这件衬衫褪色很严重，有问题，我要退款，不要了。",
        "purchase_amount": 89,
        "purchase_days_ago": 5,
        "session_history": []
    },
    {
        "issue_id": "C003",
        "customer_id": "CUST-1003",
        "customer_name": "王芳",
        "message": "衣服破损，质量坏了根本没法穿，我要投诉到12315，你们等着！",
        "purchase_amount": 210,
        "purchase_days_ago": 8,
        "session_history": []
    },
    {
        "issue_id": "C004",
        "customer_id": "CUST-1004",
        "customer_name": "刘洋",
        "message": "我收到的颜色不对，发错了，要换货，如果换不了我要退款。",
        "purchase_amount": 160,
        "purchase_days_ago": 3,
        "session_history": []
    },
    {
        "issue_id": "C005",
        "customer_id": "CUST-1005",
        "customer_name": "陈静",
        "message": "尺寸不合适，买的M码偏大穿着不好看，很不满意，差评！",
        "purchase_amount": 120,
        "purchase_days_ago": 7,
        "session_history": []
    },
    {
        "issue_id": "C006",
        "customer_id": "CUST-1006",
        "customer_name": "赵磊",
        "message": "我要申请退款，这件大衣价格680元，质量很差我不想要了。",
        "purchase_amount": 680,
        "purchase_days_ago": 20,
        "session_history": []
    },
    {
        "issue_id": "C007",
        "customer_id": "CUST-1007",
        "customer_name": "孙丽",
        "message": "我的问题还没解决，衣服还是坏了，到底怎么回事！",
        "purchase_amount": 95,
        "purchase_days_ago": 14,
        "session_history": [
            {"issue_id": "C007", "timestamp": "2024-01-10T09:00:00Z", "summary": "First contact about broken seam"},
            {"issue_id": "C007", "timestamp": "2024-01-11T14:00:00Z", "summary": "Second contact, issue unresolved"},
        ]
    }
]

with open(os.path.join(WORKSPACE, "data/incoming/complaints_batch.json"), "w", encoding="utf-8") as f:
    json.dump(complaints, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")