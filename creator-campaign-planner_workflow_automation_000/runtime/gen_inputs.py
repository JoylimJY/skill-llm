import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Skill directory structure ───────────────────────────────────────────────
skill_dir = workspace / "skills" / "creator-campaign-planner"
scripts_dir = skill_dir / "scripts"
resources_dir = skill_dir / "resources"
examples_dir = skill_dir / "examples"
tests_dir = skill_dir / "tests"

for d in [scripts_dir, resources_dir, examples_dir, tests_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ─── spec.json ────────────────────────────────────────────────────────────────
spec = {
    "version": "1.0.0",
    "output_sections": [
        {"id": "cooperation_goal",    "label": "合作目标",     "required": True},
        {"id": "creator_tiers",       "label": "合作对象分层", "required": True},
        {"id": "content_rhythm",      "label": "内容节奏",     "required": True},
        {"id": "material_reuse",      "label": "素材复用",     "required": True},
        {"id": "risk_control",        "label": "风险控制",     "required": True},
        {"id": "review_metrics",      "label": "复盘指标",     "required": True}
    ],
    "pending_items_key": "待确认项",
    "rules": {
        "missing_fields_action": "list_as_pending",
        "fabrication_allowed": False,
        "default_output_mode": "reviewable_draft",
        "material_reuse_min_rate_pct": 30
    },
    "creator_tier_definitions": {
        "S": {"followers_min": 1000000, "label": "头部KOL"},
        "A": {"followers_min": 100000,  "label": "腰部KOL"},
        "B": {"followers_min": 10000,   "label": "KOC"},
        "C": {"followers_min": 0,       "label": "素人/UGC"}
    },
    "required_input_fields": [
        "brand", "product", "audience", "budget_total_cny",
        "channels", "start_date", "end_date", "campaign_goal"
    ]
}
(resources_dir / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")

# ─── template.md ──────────────────────────────────────────────────────────────
template_md = textwrap.dedent("""\
# 创作者合作排期草案

> 生成时间：{generated_at}
> 状态：可审阅草案（draft）

---

## 合作目标
{cooperation_goal}

---

## 合作对象分层
{creator_tiers}

---

## 内容节奏
{content_rhythm}

---

## 素材复用
{material_reuse}

---

## 风险控制
{risk_control}

---

## 复盘指标
{review_metrics}

---

## 待确认项
{pending_items}
""")
(resources_dir / "template.md").write_text(template_md, encoding="utf-8")

# ─── run.py ───────────────────────────────────────────────────────────────────
run_py = textwrap.dedent('''\
#!/usr/bin/env python3
"""
creator-campaign-planner: run.py
Usage: python3 run.py --input <input_file> --output <output_file>

Reads a campaign brief (JSON or Markdown text), validates against spec.json,
and writes a structured planning draft to the output file using template.md.
"""
import argparse
import json
import sys
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent

def load_spec():
    return json.loads((BASE_DIR / "resources" / "spec.json").read_text(encoding="utf-8"))

def load_template():
    return (BASE_DIR / "resources" / "template.md").read_text(encoding="utf-8")

def parse_input(input_path: Path):
    text = input_path.read_text(encoding="utf-8")
    # Try JSON first
    try:
        return json.loads(text), []
    except json.JSONDecodeError:
        pass
    # Try to extract key:value pairs from free text
    data = {}
    warnings = []
    for line in text.splitlines():
        m = re.match(r"^[\\-*]?\\s*([\\w_\\u4e00-\\u9fff]+)[：:]+\\s*(.+)$", line.strip())
        if m:
            data[m.group(1).strip()] = m.group(2).strip()
        else:
            if line.strip():
                warnings.append(f"无法解析的行: {line.strip()}")
    return data, warnings

def check_missing(data: dict, spec: dict):
    required = spec["required_input_fields"]
    missing = [f for f in required if f not in data or not str(data[f]).strip()]
    return missing

def build_creator_tiers(data: dict, spec: dict):
    tiers = spec["creator_tier_definitions"]
    budget = data.get("budget_total_cny", "未知")
    lines = []
    for tier_key in ["S", "A", "B", "C"]:
        t = tiers[tier_key]
        lines.append(f"- **{t[\'label\']}（{tier_key}级）**：粉丝门槛 {t[\'followers_min\']:,}+")
    if budget != "未知":
        try:
            b = float(str(budget).replace(",", "").replace("万", "0000"))
            lines.append(f"\\n建议预算分配（参考）：")
            lines.append(f"  - S级(头部KOL): {int(b*0.40):,} CNY（约40%）")
            lines.append(f"  - A级(腰部KOL): {int(b*0.35):,} CNY（约35%）")
            lines.append(f"  - B/C级(KOC/UGC): {int(b*0.25):,} CNY（约25%）")
        except Exception:
            lines.append("预算金额格式无法解析，已列入待确认项。")
    return "\\n".join(lines)

def build_content_rhythm(data: dict):
    start = data.get("start_date", "待确认")
    end = data.get("end_date", "待确认")
    channels = data.get("channels", "待确认")
    return (
        f"- 活动周期：{start} ~ {end}\\n"
        f"- 渠道：{channels}\\n"
        f"- 节奏建议：预热期（第1-2周）→ 爆发期（第3-4周）→ 长尾期（第5-6周）\\n"
        f"- 发布频次：KOL每周1篇主推，KOC每周2-3篇种草"
    )

def build_material_reuse(data: dict, spec: dict):
    min_rate = spec["rules"]["material_reuse_min_rate_pct"]
    product = data.get("product", "产品")
    return (
        f"- 主视觉素材（品牌提供）：可授权KOL/KOC二次剪辑使用\\n"
        f"- {product}卖点贴纸/滤镜：适用于短视频平台，复用率目标 ≥{min_rate}%\\n"
        f"- UGC精选内容：经授权后可转发至品牌官方账号\\n"
        f"- 素材生命周期：主素材有效期建议不超过6周，过期需更新版本"
    )

def build_risk_control(data: dict):
    return (
        "- 所有合作内容须标注广告标识（#广告 / #合作），符合平台规范\\n"
        "- 创作者资质与历史违规情况需预先审查\\n"
        "- 合同条款须包含内容审核期（建议3个工作日）\\n"
        "- 不承诺具体投放效果数据，不生成违规投放方案\\n"
        "- 高风险内容（功效宣称/医疗类表述）需法务审阅"
    )

def build_review_metrics(data: dict):
    goal = data.get("campaign_goal", "品牌曝光")
    return (
        f"- 主目标：{goal}\\n"
        "- 曝光量（Impressions）：各平台累计\\n"
        "- 互动率（Engagement Rate）：点赞+评论+收藏/曝光\\n"
        "- 种草指数（小红书搜索增量）\\n"
        "- 粉丝净增量（品牌账号）\\n"
        "- 素材复用率（实际复用篇数/总篇数）\\n"
        "- 复盘周期：活动结束后7天内提交数据报告"
    )

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True, help="输入文件路径")
    parser.add_argument("--output", required=True, help="输出文件路径")
    args = parser.parse_args()

    input_path  = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] 输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    spec     = load_spec()
    template = load_template()

    data, warnings = parse_input(input_path)
    missing  = check_missing(data, spec)

    pending_lines = []
    if missing:
        pending_lines.append("以下字段信息缺失或模糊，**请在执行前确认**：")
        for f in missing:
            pending_lines.append(f"- [ ] `{f}`：需要补充")
    if warnings:
        pending_lines.append("\\n以下输入行解析失败，请人工核查：")
        for w in warnings:
            pending_lines.append(f"- {w}")
    if not pending_lines:
        pending_lines.append("（无待确认项）")

    sections = {
        "generated_at":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        "cooperation_goal": (
            f"品牌：{data.get(\'brand\', \'待确认\')} | 产品：{data.get(\'product\', \'待确认\')}\\n"
            f"目标人群：{data.get(\'audience\', \'待确认\')}\\n"
            f"核心目标：{data.get(\'campaign_goal\', \'待确认\')}\\n"
            f"总预算：{data.get(\'budget_total_cny\', \'待确认\')} CNY"
        ),
        "creator_tiers":  build_creator_tiers(data, spec),
        "content_rhythm": build_content_rhythm(data),
        "material_reuse": build_material_reuse(data, spec),
        "risk_control":   build_risk_control(data),
        "review_metrics": build_review_metrics(data),
        "pending_items":  "\\n".join(pending_lines),
    }

    output_text = template
    for key, val in sections.items():
        output_text = output_text.replace("{" + key + "}", val)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text, encoding="utf-8")
    print(f"[OK] 排期草案已写入: {output_path}")
    if missing:
        print(f"[WARN] 存在 {len(missing)} 个待确认项，请查看输出文件末尾。")

if __name__ == "__main__":
    main()
''')
(scripts_dir / "run.py").write_text(run_py, encoding="utf-8")

# ─── Example input/output ────────────────────────────────────────────────────
example_input = {
    "brand": "GlowUp美妆",
    "product": "玻尿酸精华液V2",
    "audience": "18-35岁女性，关注护肤成分党",
    "budget_total_cny": "500000",
    "channels": "小红书,抖音",
    "start_date": "2024-10-01",
    "end_date": "2024-11-15",
    "campaign_goal": "新品曝光与种草转化"
}
(examples_dir / "example_input.json").write_text(
    json.dumps(example_input, ensure_ascii=False, indent=2), encoding="utf-8"
)

example_output = textwrap.dedent("""\
# 创作者合作排期草案（示例输出）

## 合作目标
品牌：GlowUp美妆 | 产品：玻尿酸精华液V2
目标人群：18-35岁女性，关注护肤成分党
核心目标：新品曝光与种草转化
总预算：500000 CNY

## 合作对象分层
- **头部KOL（S级）**：粉丝门槛 1,000,000+
- **腰部KOL（A级）**：粉丝门槛 100,000+
- **KOC（B级）**：粉丝门槛 10,000+
- **素人/UGC（C级）**：粉丝门槛 0+

## 待确认项
（无待确认项）
""")
(examples_dir / "example_output.md").write_text(example_output, encoding="utf-8")

# ─── Smoke test ───────────────────────────────────────────────────────────────
smoke_test = textwrap.dedent("""\
# Smoke Test

## 步骤
1. 准备输入文件（参考 examples/example_input.json）
2. 运行：python3 scripts/run.py --input examples/example_input.json --output /tmp/smoke_out.md
3. 检查 /tmp/smoke_out.md 包含所有6个必需章节
4. 验证 "待确认项" 章节存在

## 预期结果
- 输出文件存在且非空
- 包含：合作目标、合作对象分层、内容节奏、素材复用、风险控制、复盘指标
- 缺失字段时，待确认项列表非空
""")
(tests_dir / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ─── The MESSY input brief (what the agent must process) ─────────────────────
# Deliberately missing: budget_total_cny, audience, end_date → must surface as 待确认项
# Also has some garbled/unparseable lines to test robustness
messy_brief = textwrap.dedent("""\
品牌活动简报 — 内部流转版（请勿外发）
========================================

品牌: LumineSkin 新锐护肤
product: 「奇迹焕亮精华霜」限定版

campaign_goal: Q4新品上市 + 冬季护肤节曝光，打造成分党口碑

channels: 小红书、抖音、微博

start_date: 2024-11-18

[备注区——请BD同学核对]
- 目标用户群体：TBD（市场部还没确认，可能是25-40岁职场女性，也可能扩展到男性护肤市场）
- 总预算：待财务审批，初步方向是30-50万区间，具体数字下周出
- 活动结束时间：本来想做到双12，但可能会延长到元旦，还没定

其他信息碎片（仅供参考，不一定准确）：
@@@ 临时需求：需要一个直播专场方案 @@@
??? 暂时不考虑B站和视频号 ???
!!!上线前一定要走法务审核!!!
""")

# Save the messy brief where the agent can discover it
brief_dir = workspace / "campaign_briefs"
brief_dir.mkdir(parents=True, exist_ok=True)
(brief_dir / "luminescent_q4_brief.txt").write_text(messy_brief, encoding="utf-8")

# ─── Distractor files ─────────────────────────────────────────────────────────
distractor_root = workspace / "internal_docs"
distractor_root.mkdir(exist_ok=True)

(distractor_root / "budget_tracker_2023.csv").write_text(
    "month,spend_cny,channel\n2023-01,120000,微博\n2023-02,98000,小红书\n", encoding="utf-8"
)
(distractor_root / "creator_blacklist.txt").write_text(
    "# 创作者黑名单（历史违规）\ncreator_id_7823: 虚假宣传\ncreator_id_3301: 数据造假\n", encoding="utf-8"
)
(distractor_root / "old_campaign_v2.md").write_text(
    "# 旧版活动方案（已废弃）\n此文件已由新版本替代，请勿使用。\n", encoding="utf-8"
)

assets_dir = workspace / "assets" / "brand_kit"
assets_dir.mkdir(parents=True, exist_ok=True)
(assets_dir / "logo_guidelines.txt").write_text("Logo使用规范：最小尺寸80px，留白区域等于Logo高度的1/4。\n", encoding="utf-8")
(assets_dir / "color_palette.json").write_text(json.dumps({"primary": "#F4C2C2", "secondary": "#FFFDD0"}, indent=2), encoding="utf-8")

legal_dir = workspace / "legal"
legal_dir.mkdir(exist_ok=True)
(legal_dir / "ad_compliance_checklist.md").write_text(
    "# 广告合规清单\n- [ ] 明示广告标识\n- [ ] 避免绝对化用语\n- [ ] 医疗功效类表述需审批\n", encoding="utf-8"
)
(legal_dir / "contract_template_v3.docx.txt").write_text(
    "[合同模板占位符 — 实际使用请联系法务部]\n", encoding="utf-8"
)

reports_dir = workspace / "reports" / "Q3_2024"
reports_dir.mkdir(parents=True, exist_ok=True)
(reports_dir / "q3_performance_summary.txt").write_text(
    "Q3活动总结：总曝光 1.2亿，互动率 3.8%，种草指数增长 42%。\n", encoding="utf-8"
)
(reports_dir / "creator_tier_stats.json").write_text(
    json.dumps({"S_tier_avg_cpe": 8.2, "A_tier_avg_cpe": 3.1, "B_tier_avg_cpe": 1.4}, indent=2), encoding="utf-8"
)

misc_dir = workspace / "misc"
misc_dir.mkdir(exist_ok=True)
(misc_dir / "team_contacts.txt").write_text(
    "BD负责人: 李明 (liming@lumineskin.com)\n法务: 王芳 (wangfang@lumineskin.com)\n", encoding="utf-8"
)
(misc_dir / "platform_api_notes.txt").write_text(
    "小红书蒲公英平台：达人合作需走官方系统，私下合作有封号风险。\n", encoding="utf-8"
)
(misc_dir / ".DS_Store_fake").write_text("binary garbage placeholder\n", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Brief file: {brief_dir / 'luminescent_q4_brief.txt'}")