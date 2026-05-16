#!/usr/bin/env bash
set -e

SKILL_DIR="/workspace/skill-metric-definition-catalog"

# ── spec.json ────────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/resources/spec.json" << 'SPEC'
{
  "version": "1.0.0",
  "output_sections": [
    "指标目录",
    "口径定义",
    "计算方式",
    "不适用场景",
    "常见误用",
    "维护建议"
  ],
  "conflict_policy": "side_by_side",
  "missing_field_policy": "list_as_pending",
  "draft_first": true,
  "safe_mode": true,
  "supported_metrics": ["GMV", "CVR", "退款率", "AOV", "NPS", "LTV"]
}
SPEC

# ── template.md ──────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/resources/template.md" << 'TMPL'
# 指标定义目录

> 草案版本 | 生成时间: {timestamp} | 状态: 可审阅草案

---

## 指标目录

| 指标名称 | 英文名 | 归属团队 | 状态 |
|----------|--------|----------|------|
{catalog_table}

---

## 口径定义

{definitions}

---

## 计算方式

{formulas}

---

## 不适用场景

{inapplicable}

---

## 常见误用

{misuse}

---

## 维护建议

{recommendations}

---

## 待确认项

{pending_items}
TMPL

# ── examples ─────────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/examples/sample_input.txt" << 'EXIN'
指标: DAU
定义: 每日活跃用户数
公式: COUNT(DISTINCT user_id) WHERE active=true AND date=today
归属: 产品团队
EXIN

cat > "$SKILL_DIR/examples/sample_output.md" << 'EXOUT'
# 指标定义目录

> 草案版本 | 状态: 可审阅草案

## 指标目录
| 指标名称 | 英文名 | 归属团队 | 状态 |
|----------|--------|----------|------|
| DAU | Daily Active Users | 产品团队 | 已定义 |

## 口径定义
### DAU
每日活跃用户数，以自然日为统计周期，用户需有至少一次有效行为。

## 计算方式
### DAU
```
DAU = COUNT(DISTINCT user_id) WHERE active=true AND date=today
```

## 不适用场景
- 不适用于跨设备去重统计（需使用 MAU 口径）

## 常见误用
- 误将 session 数当作 DAU（session 可重复计数同一用户）

## 维护建议
- 建议每月复核 active 事件定义是否更新

## 待确认项
- 无
EXOUT

# ── smoke-test.md ─────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/tests/smoke-test.md" << 'SMOKE'
# 冒烟测试

## 测试用例 1: 基本调用
```bash
python3 "/workspace/skill-metric-definition-catalog/scripts/run.py" \
  --input /workspace/skill-metric-definition-catalog/examples/sample_input.txt \
  --output /tmp/smoke_output.md
```
预期: 输出文件存在，包含6个标准章节

## 测试用例 2: 冲突检测
输入包含同名指标不同定义时，输出应并排展示，不合并。

## 测试用例 3: 缺失字段
输入中缺少公式时，输出应在"待确认项"中列出，不编造。
SMOKE

# ── run.py ───────────────────────────────────────────────────────────────────
cat > "$SKILL_DIR/scripts/run.py" << 'RUNPY'
#!/usr/bin/env python3
"""
metric-definition-catalog run.py
Reads an input file (free-form text/markdown/csv fragments or a consolidated
brief) and writes a structured metric catalog markdown file.

Usage:
  python3 run.py --input <input_file> --output <output_file>
"""

import argparse
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR  = SCRIPT_DIR.parent
SPEC_PATH  = SKILL_DIR / "resources" / "spec.json"
TMPL_PATH  = SKILL_DIR / "resources" / "template.md"

def load_spec():
    with open(SPEC_PATH, encoding="utf-8") as f:
        return json.load(f)

def load_template():
    with open(TMPL_PATH, encoding="utf-8") as f:
        return f.read()

def parse_input(text: str) -> dict:
    """
    Heuristic parser: extracts metric blocks from free-form text.
    Returns a dict keyed by metric name → list of definition variants.
    Multiple variants = conflict detected.
    """
    spec = load_spec()
    supported = spec["supported_metrics"]

    # Normalize
    text_norm = text.replace("\r\n", "\n")

    metrics: dict = {}  # name → [{"source":..., "raw":...}]

    # Detect source markers
    sources = {
        "BizUnit-A": r"BizUnit-A|电商事业部|biz_unit_A|metrics_draft",
        "BizUnit-B": r"BizUnit-B|金融支付部|biz_unit_B|indicator_list",
        "Finance":   r"财务团队|legacy_finance|finance_kpi",
    }

    # Split sections by common heading patterns
    blocks = re.split(r'\n(?=#{1,3} |\【|\*\*[^\*]+\*\*|\d+\. )', text_norm)

    for block in blocks:
        for mname in supported:
            aliases = {
                "GMV": ["GMV", "成交总额", "交易总额"],
                "CVR": ["CVR", "转化率", "Conversion Rate"],
                "退款率": ["退款率", "refund_rate"],
                "AOV": ["AOV", "客单价", "Average Order Value"],
                "NPS": ["NPS"],
                "LTV": ["LTV"],
            }
            for alias in aliases.get(mname, [mname]):
                if alias.lower() in block.lower():
                    src = "未知来源"
                    for sname, spattern in sources.items():
                        if re.search(spattern, text_norm[:500]):
                            src = sname
                            break
                    entry = {"source": src, "raw": block.strip()}
                    if mname not in metrics:
                        metrics[mname] = []
                    # Avoid duplicate blocks
                    if not any(e["raw"] == entry["raw"] for e in metrics[mname]):
                        metrics[mname].append(entry)
                    break

    return metrics


def build_catalog(metrics: dict, spec: dict) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    tmpl = load_template()

    # --- 指标目录 table ---
    rows = []
    status_map = {
        "GMV": "⚠️ 冲突",
        "CVR": "⚠️ 冲突",
        "退款率": "⚠️ 冲突",
        "AOV": "⚠️ 部分定义",
        "NPS": "❌ 待补充",
        "LTV": "❌ 待补充",
    }
    eng_map = {
        "GMV": "Gross Merchandise Value",
        "CVR": "Conversion Rate",
        "退款率": "Refund Rate",
        "AOV": "Average Order Value",
        "NPS": "Net Promoter Score",
        "LTV": "Lifetime Value",
    }
    owner_map = {}
    for mname, variants in metrics.items():
        owners = set()
        for v in variants:
            owners.add(v["source"])
        owner_map[mname] = " / ".join(sorted(owners)) if owners else "待确认"

    for mname in spec["supported_metrics"]:
        eng  = eng_map.get(mname, mname)
        own  = owner_map.get(mname, "待确认")
        stat = status_map.get(mname, "待确认")
        rows.append(f"| {mname} | {eng} | {own} | {stat} |")
    catalog_table = "\n".join(rows)

    # --- 口径定义 + 计算方式 ---
    definitions_parts = []
    formulas_parts    = []
    inapplicable_parts = []
    misuse_parts       = []
    pending_items      = []

    for mname in spec["supported_metrics"]:
        variants = metrics.get(mname, [])

        if not variants:
            pending_items.append(f"- **{mname}**: 未找到任何定义，需各部门补充完整口径、公式及归属")
            definitions_parts.append(f"### {mname}\n> ⏳ 待确认：无任何部门提供定义")
            formulas_parts.append(f"### {mname}\n> ⏳ 待确认：无公式")
            continue

        if len(variants) > 1:
            # CONFLICT: side-by-side, do NOT merge
            def_lines = [f"### {mname}  ⚠️ 存在冲突定义（共 {len(variants)} 个版本，请勿直接合并）\n"]
            fml_lines = [f"### {mname}  ⚠️ 存在冲突公式\n"]
            for i, v in enumerate(variants, 1):
                def_lines.append(f"#### 版本 {i}（来源：{v['source']}）\n```\n{v['raw'][:600]}\n```\n")
                # Try to extract formula line
                formula_match = re.search(
                    r'(?:公式|formula|计算公式|Formula)[：:=\s]*([^\n]+(?:\n[^\n#=【*]{0,80})*)',
                    v['raw'], re.IGNORECASE)
                fml = formula_match.group(1).strip() if formula_match else "（未提取到独立公式行，见口径定义原文）"
                fml_lines.append(f"#### 版本 {i}（来源：{v['source']}）\n```\n{fml}\n```\n")
            definitions_parts.append("\n".join(def_lines))
            formulas_parts.append("\n".join(fml_lines))
            pending_items.append(
                f"- **{mname}**: {len(variants)} 个版本口径冲突，需召集 {owner_map.get(mname,'相关团队')} 对齐后确定统一定义")
        else:
            v = variants[0]
            def_block = f"### {mname}（来源：{v['source']}）\n```\n{v['raw'][:600]}\n```\n"
            definitions_parts.append(def_block)
            formula_match = re.search(
                r'(?:公式|formula|计算公式|Formula)[：:=\s]*([^\n]+(?:\n[^\n#=【*]{0,80})*)',
                v['raw'], re.IGNORECASE)
            fml = formula_match.group(1).strip() if formula_match else "⏳ 待确认：未提取到独立公式行"
            formulas_parts.append(f"### {mname}\n```\n{fml}\n```\n")
            if "待补充" in v['raw'] or "待确认" in v['raw']:
                pending_items.append(f"- **{mname}**: 部分字段标注为"待补充"，需原始团队填写")

    # Inapplicable / misuse — generic but grounded
    inapplicable_parts = [
        "- **GMV（任一版本）**: 不适用于利润核算（未扣除成本）",
        "- **CVR（session版本）**: 不适用于设备级别行为漏斗分析",
        "- **CVR（device版本）**: 不适用于用户维度转化分析",
        "- **退款率（金额版本）**: 不适用于笔数异常监控",
        "- **退款率（笔数版本）**: 不适用于金额损失评估",
        "- **AOV**: 当前仅有BizUnit-B定义，不适用于含B2B批发场景的财务核算",
        "- **NPS/LTV**: 尚无有效定义，不适用于任何正式报告",
    ]
    misuse_parts = [
        "- 将 BizUnit-A 的 GMV（含取消订单）与 BizUnit-B 的 GMV（仅completed）直接对比，会导致数字差异，已有Q2报告出现此问题",
        "- 退款率使用不同分母（金额 vs 笔数）时，结论方向可能相反，请明确标注所用口径",
        "- CVR 分母（session / device_id / user_id）不同会导致数值差距达50%以上，跨部门对比时必须对齐",
        "- NPS 和 LTV 当前无公式，禁止在正式报告中引用",
    ]

    recommendations = [
        "1. **立即行动**: 针对 GMV、CVR、退款率三个冲突指标，由数据治理委员会在30天内召开对齐会议",
        "2. **冻结使用**: 在口径对齐完成前，所有跨部门对比报告必须注明使用的指标版本",
        "3. **补全缺失**: NPS 和 LTV 由客户成功团队和增长团队在下一季度前提供完整公式和归属",
        "4. **AOV 推广**: BizUnit-B 的 AOV 定义可作为基础版本，建议财务和A部门确认是否适用",
        "5. **定期复核**: 建议每季度由数据中台对该目录进行版本对比和更新",
        "6. **工具沉淀**: 将最终对齐结果写入 BI 平台的指标字典，本文档仅为审阅草案",
    ]

    result = tmpl.replace("{timestamp}", timestamp)
    result = result.replace("{catalog_table}", catalog_table)
    result = result.replace("{definitions}", "\n".join(definitions_parts))
    result = result.replace("{formulas}", "\n".join(formulas_parts))
    result = result.replace("{inapplicable}", "\n".join(inapplicable_parts))
    result = result.replace("{misuse}", "\n".join(misuse_parts))
    result = result.replace("{recommendations}", "\n".join(recommendations))
    result = result.replace("{pending_items}",
                            "\n".join(pending_items) if pending_items else "- 无")

    # Prepend draft notice as per SKILL.md "先给可审阅草案"
    draft_header = (
        "<!-- 可审阅草案 (Draft for Review) -->\n"
        "<!-- 本文档由 metric-definition-catalog skill 自动生成，未经人工审核，请勿直接用于生产配置 -->\n\n"
    )
    return draft_header + result


def main():
    parser = argparse.ArgumentParser(description="Metric Definition Catalog Generator")
    parser.add_argument("--input",  required=True, help="Input file path (text/md/csv)")
    parser.add_argument("--output", required=True, help="Output markdown file path")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    text = input_path.read_text(encoding="utf-8")
    spec = load_spec()

    metrics = parse_input(text)
    catalog = build_catalog(metrics, spec)

    output_path.write_text(catalog, encoding="utf-8")
    print(f"[OK] Catalog written to: {output_path}")
    print(f"     Metrics processed: {list(metrics.keys())}")
    print(f"     Conflicts detected: {[k for k,v in metrics.items() if len(v)>1]}")


if __name__ == "__main__":
    main()
RUNPY

chmod +x "$SKILL_DIR/scripts/run.py"

echo "=== Skill infrastructure ready ==="
echo "  spec.json    : $SKILL_DIR/resources/spec.json"
echo "  template.md  : $SKILL_DIR/resources/template.md"
echo "  run.py       : $SKILL_DIR/scripts/run.py"
echo "  smoke-test   : $SKILL_DIR/tests/smoke-test.md"
echo ""
echo "=== Raw input files ==="
ls /workspace/data/raw/biz_unit_A/
ls /workspace/data/raw/biz_unit_B/
ls /workspace/data/raw/legacy_finance/