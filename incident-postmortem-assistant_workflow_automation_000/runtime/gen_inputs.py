import os
import json
import textwrap

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/incident-postmortem-assistant/scripts",
    "skills/incident-postmortem-assistant/resources",
    "skills/incident-postmortem-assistant/examples",
    "skills/incident-postmortem-assistant/tests",
    # distractor dirs
    "ops/runbooks",
    "ops/alerts",
    "ops/dashboards",
    "monitoring/grafana/dashboards",
    "monitoring/prometheus/rules",
    "infra/terraform/modules/rds",
    "infra/k8s/manifests",
    "docs/architecture",
    "docs/sla",
    "oncall/schedules",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)


# ── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_format": "markdown",
    "required_sections": [
        "事故摘要",
        "时间线",
        "根因分析",
        "影响分析",
        "处理动作",
        "后续改进"
    ],
    "root_cause_schema": {
        "fields": ["根因", "诱因", "放大器"],
        "missing_field_placeholder": "【待确认】"
    },
    "language_rules": {
        "blameless": True,
        "forbidden_patterns": [
            "是.*的错",
            ".*责任人.*应该",
            "由于.*工程师.*失误",
            ".*操作员.*错误"
        ],
        "pending_placeholder": "【待确认】"
    },
    "section_heading_prefix": "## ",
    "subsection_heading_prefix": "### ",
    "metadata_marker": "<!-- generated-by: incident-postmortem-assistant v1.0.0 -->"
}

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/resources/spec.json"), "w", encoding="utf-8") as f:
    json.dump(spec, f, ensure_ascii=False, indent=2)


# ── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
<!-- generated-by: incident-postmortem-assistant v1.0.0 -->
# 事故复盘报告

## 事故摘要
{summary}

## 时间线
{timeline}

## 根因分析
### 根因
{root_cause}

### 诱因
{trigger}

### 放大器
{amplifier}

## 影响分析
{impact}

## 处理动作
{actions}

## 后续改进
{improvements}

---
_本文档为可审阅草案，仅供内部使用。_
""")

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/resources/template.md"), "w", encoding="utf-8") as f:
    f.write(template_md)


# ── run.py ───────────────────────────────────────────────────────────────────
run_py = textwrap.dedent(r'''#!/usr/bin/env python3
"""
incident-postmortem-assistant: run.py
Usage: python3 run.py --input <input_file> --output <output_file>
Reads a raw incident notes file, applies spec.json rules, and writes
a structured Markdown postmortem draft to <output_file>.
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SPEC_PATH = BASE_DIR / "resources" / "spec.json"
TEMPLATE_PATH = BASE_DIR / "resources" / "template.md"


def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_template():
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        return f.read()


def parse_input(text: str) -> dict:
    """
    Parse the raw incident notes into structured fields.
    Looks for labelled sections; fills missing ones with 【待确认】.
    """
    PLACEHOLDER = "【待确认】"

    def extract(label_patterns, text):
        for pat in label_patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if m:
                value = m.group(1).strip()
                # trim at next labelled section
                value = re.split(r'\n(?:事故名称|标题|时间|时间线|根因|诱因|放大器|影响|处理|改进|行动|后续|summary|timeline|impact|action)', value)[0].strip()
                if value:
                    return value
        return PLACEHOLDER

    summary     = extract([r'(?:事故摘要|事故名称|标题|TITLE|SUMMARY)[：:]\s*(.*?)(?=\n[^\n])', r'(?:事故摘要|事故名称|标题)[：:]\s*(.+)'], text)
    timeline    = extract([r'(?:时间线|TIMELINE)[：:\n](.*?)(?=\n##|\n根因|\n影响|\Z)'], text)
    root_cause  = extract([r'(?:根因|ROOT.?CAUSE)[：:]\s*(.*?)(?=\n[^\n])', r'(?:根因)[：:]\s*(.+)'], text)
    trigger     = extract([r'(?:诱因|TRIGGER)[：:]\s*(.*?)(?=\n[^\n])', r'(?:诱因)[：:]\s*(.+)'], text)
    amplifier   = extract([r'(?:放大器|AMPLIFIER)[：:]\s*(.*?)(?=\n[^\n])', r'(?:放大器)[：:]\s*(.+)'], text)
    impact      = extract([r'(?:影响|IMPACT)[：:\n](.*?)(?=\n##|\n处理|\n改进|\Z)'], text)
    actions     = extract([r'(?:处理动作|处理|ACTIONS?)[：:\n](.*?)(?=\n##|\n后续|\n改进|\Z)'], text)
    improvements= extract([r'(?:后续改进|改进|IMPROVEMENTS?)[：:\n](.*?)(?=\n##|\Z)'], text)

    # Build timeline as a list if raw lines present
    if timeline != PLACEHOLDER:
        lines = [l.strip() for l in timeline.splitlines() if l.strip()]
        timeline = "\n".join(f"- {l}" if not l.startswith(("-","*","•")) else l for l in lines)

    return {
        "summary":      summary,
        "timeline":     timeline,
        "root_cause":   root_cause,
        "trigger":      trigger,
        "amplifier":    amplifier,
        "impact":       impact,
        "actions":      actions,
        "improvements": improvements,
    }


def enforce_blameless(text: str, spec: dict) -> str:
    """Remove or neutralise blame-assigning phrases per spec."""
    for pat in spec["language_rules"]["forbidden_patterns"]:
        text = re.sub(pat, "[已按无责复盘规范处理]", text)
    return text


def render(fields: dict, template: str, spec: dict) -> str:
    out = template
    for k, v in fields.items():
        out = out.replace("{" + k + "}", v)
    out = enforce_blameless(out, spec)
    return out


def main():
    parser = argparse.ArgumentParser(description="Incident Postmortem Assistant")
    parser.add_argument("--input",  required=True, help="Raw incident notes file")
    parser.add_argument("--output", required=True, help="Output Markdown file")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    spec     = load_spec()
    template = load_template()
    raw_text = input_path.read_text(encoding="utf-8")

    fields = parse_input(raw_text)
    output = render(fields, template, spec)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output, encoding="utf-8")

    # Print pending items summary to stdout
    pending = [k for k, v in fields.items() if "待确认" in v]
    if pending:
        print(f"[postmortem-assistant] ⚠ 待确认项: {', '.join(pending)}")
    print(f"[postmortem-assistant] ✓ 草案已写入: {output_path}")


if __name__ == "__main__":
    main()
''')

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/scripts/run.py"), "w", encoding="utf-8") as f:
    f.write(run_py)
os.chmod(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/scripts/run.py"), 0o755)


# ── examples ─────────────────────────────────────────────────────────────────
example_input = textwrap.dedent("""\
事故名称: 支付服务 2024-03-01 宕机 30 分钟
时间线:
  14:00 部署新版本 payment-service v2.3.1
  14:08 监控告警: payment API p99 > 5s
  14:15 开始回滚
  14:30 服务恢复
根因: 新版本引入了同步数据库调用，连接池耗尽
诱因: 代码审查未覆盖高并发场景
放大器: 连接池大小未随负载自动扩展
影响: 约 2000 笔订单支付失败，持续 30 分钟
处理动作:
  1. 回滚至 v2.3.0
  2. 通知客服团队
后续改进:
  1. 增加连接池动态扩容
  2. 在 CI 中加入并发压测
""")

example_output = textwrap.dedent("""\
<!-- generated-by: incident-postmortem-assistant v1.0.0 -->
# 事故复盘报告

## 事故摘要
支付服务 2024-03-01 宕机 30 分钟

## 时间线
- 14:00 部署新版本 payment-service v2.3.1
- 14:08 监控告警: payment API p99 > 5s
- 14:15 开始回滚
- 14:30 服务恢复

## 根因分析
### 根因
新版本引入了同步数据库调用，连接池耗尽

### 诱因
代码审查未覆盖高并发场景

### 放大器
连接池大小未随负载自动扩展

## 影响分析
约 2000 笔订单支付失败，持续 30 分钟

## 处理动作
- 1. 回滚至 v2.3.0
- 2. 通知客服团队

## 后续改进
- 1. 增加连接池动态扩容
- 2. 在 CI 中加入并发压测

---
_本文档为可审阅草案，仅供内部使用。_
""")

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/examples/sample_input.txt"), "w", encoding="utf-8") as f:
    f.write(example_input)

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/examples/sample_output.md"), "w", encoding="utf-8") as f:
    f.write(example_output)


# ── smoke-test.md ────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

## Steps
1. Run: python3 scripts/run.py --input examples/sample_input.txt --output /tmp/smoke_out.md
2. Verify /tmp/smoke_out.md contains all required sections.
3. Verify metadata marker present.

## Expected
- All 6 sections present
- Metadata marker: <!-- generated-by: incident-postmortem-assistant v1.0.0 -->
- No blame language
""")

with open(os.path.join(WORKSPACE, "skills/incident-postmortem-assistant/tests/smoke-test.md"), "w", encoding="utf-8") as f:
    f.write(smoke_test)


# ── messy raw incident input for the TASK ────────────────────────────────────
# Deliberately messy: mixed Chinese/English, missing root cause and amplifier,
# partial timestamps, some noise lines, blame-assigning language to be sanitised.
raw_incident = textwrap.dedent("""\
=== 大促活动事故原始记录 ===
收集人: 值班 SRE 小组
记录时间: 2024-11-11 04:50

[告警快照]
03:58:22  CRITICAL  checkout-service  HTTP 5xx rate > 15%  (threshold 1%)
04:01:05  CRITICAL  order-db-primary  connection pool usage 99.8%
04:03:40  WARNING   inventory-service latency p95 = 8200ms
04:18:00  RESOLVED  checkout-service  HTTP 5xx rate back to normal
04:22:00  RESOLVED  order-db-primary  connection pool usage 30%

[处理记录 / Handling Log]
03:59  oncall engineer acknowledged checkout alert
04:02  team started investigation; suspected DB bottleneck
04:05  DBA team paged; confirmed connection pool exhaustion on order-db-primary
04:08  decision: scale up connection pool limit from 200 → 500 (live config change)
04:10  config change applied; 5xx rate started dropping
04:14  checkout recovery confirmed by synthetic monitors
04:18  all alerts resolved
04:22  DB pool utilisation stabilised at ~28%
04:35  post-incident bridge call opened
04:50  preliminary notes compiled

[影响]
- 大促期间约 14,000 笔订单结算请求失败（占该时段请求量约 9.3%）
- 受影响时段: 03:58 – 04:18（约 20 分钟）
- 受影响服务: checkout-service, order-db-primary, inventory-service（级联延迟）
- 用户侧: 部分用户支付页面出现「服务繁忙」错误

[初步分析 / Preliminary Notes]
诱因: 大促流量是日常峰值的 6.8 倍，超出连接池设计容量
NOTE: root cause has not been formally confirmed yet — needs architecture review
NOTE: amplifier not yet identified — TBD after full review

[背景]
- order-db-primary 连接池上限在本次大促前未随预期流量做对应扩容
- inventory-service 未设置熔断，导致级联延迟
- 本次大促流量预测误差较大

[初步改进建议]
1. 在大促前执行 DB 连接池容量评审 checklist
2. inventory-service 引入熔断机制（circuit breaker）
3. 建立大促流量预测模型，纳入容量规划流程
4. 自动化连接池动态扩容（基于 QPS 阈值触发）

[NOTE - 不要在报告里出现] 这次事故是由于数据库工程师的失误导致未提前扩容。
""")

with open(os.path.join(WORKSPACE, "incident_raw_notes.txt"), "w", encoding="utf-8") as f:
    f.write(raw_incident)


# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "ops/runbooks/db-failover.md": "# DB Failover Runbook\n\nStep 1: ...\nStep 2: ...\n",
    "ops/runbooks/rollback-procedure.md": "# Rollback Procedure\n\nUse `kubectl rollout undo`.\n",
    "ops/alerts/checkout_alerts.yaml": "groups:\n  - name: checkout\n    rules:\n      - alert: High5xxRate\n        expr: rate(http_requests_total{status=~'5..'}[1m]) > 0.01\n",
    "ops/dashboards/sre-overview.json": json.dumps({"title": "SRE Overview", "panels": []}),
    "monitoring/grafana/dashboards/checkout.json": json.dumps({"title": "Checkout", "uid": "abc123"}),
    "monitoring/prometheus/rules/latency.yaml": "groups:\n  - name: latency\n    rules: []\n",
    "infra/terraform/modules/rds/main.tf": '# RDS module\nresource "aws_db_instance" "main" {}\n',
    "infra/k8s/manifests/checkout-deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: checkout-service\n",
    "docs/architecture/system-overview.md": "# System Overview\n\nCheckout → OrderDB → InventoryService\n",
    "docs/sla/sla-2024.md": "# SLA 2024\n\nAvailability target: 99.9%\n",
    "oncall/schedules/november.json": json.dumps({"month": "2024-11", "oncall": ["alice", "bob", "charlie"]}),
    "ops/alerts/db_alerts.yaml": "groups:\n  - name: database\n    rules:\n      - alert: ConnectionPoolHigh\n        expr: db_connection_pool_usage > 0.9\n",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Task input: {WORKSPACE}/incident_raw_notes.txt")
print(f"Skill base: {WORKSPACE}/skills/incident-postmortem-assistant/")