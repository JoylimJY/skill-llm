import os
import random
import json
from pathlib import Path

random.seed(42)

workspace_root = Path("/app")

# Create the scripts directory and all required scripts from SKILL.md
scripts_dir = workspace_root / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── init_business.py ──────────────────────────────────────────────────────────
init_business_src = r'''#!/usr/bin/env python3
"""Initialize a new one-person company workspace."""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE_FILES = [
    "00-经营总盘.md",
    "01-创始人约束.md",
    "02-价值承诺与报价.md",
    "03-机会与成交管道.md",
    "04-产品与上线状态.md",
    "05-客户交付与回款.md",
    "06-现金流与经营健康.md",
    "07-资产与自动化.md",
    "08-风险与关键决策.md",
    "09-本周唯一主目标.md",
    "10-今日最短动作.md",
    "11-协作记忆.md",
    "12-会话交接.md",
]

VALID_STAGES = ["构建期", "验证期", "增长期", "稳定期"]

def main():
    parser = argparse.ArgumentParser(description="Initialize business workspace")
    parser.add_argument("company_name", help="Company name")
    parser.add_argument("--path", required=True, help="Base workspace path")
    parser.add_argument("--product-name", required=True, help="Product name")
    parser.add_argument("--stage", required=True, choices=VALID_STAGES, help="Business stage")
    args = parser.parse_args()

    if args.stage not in VALID_STAGES:
        print(f"ERROR: Invalid stage '{args.stage}'. Must be one of: {VALID_STAGES}", file=sys.stderr)
        sys.exit(1)

    company_dir = Path(args.path) / args.company_name
    company_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d")

    # 00
    (company_dir / "00-经营总盘.md").write_text(
        f"# 经营总盘\n\n公司：{args.company_name}\n产品：{args.product_name}\n阶段：{args.stage}\n初始化日期：{ts}\n\n## 核心循环\npromise -> buyer -> product capability -> delivery -> cash -> learning -> asset\n",
        encoding="utf-8"
    )
    # 01
    (company_dir / "01-创始人约束.md").write_text(
        f"# 创始人约束\n\n公司：{args.company_name}\n产品：{args.product_name}\n阶段：{args.stage}\n\n## 核心约束\n- 创始人为最终决策者\n- 定价、预算、法律等高风险动作须创始人审批\n",
        encoding="utf-8"
    )
    # 02
    (company_dir / "02-价值承诺与报价.md").write_text(
        f"# 价值承诺与报价\n\n产品：{args.product_name}\n\n## 当前价值承诺\n待定\n\n## 报价\n待定\n",
        encoding="utf-8"
    )
    # 03
    (company_dir / "03-机会与成交管道.md").write_text(
        f"# 机会与成交管道\n\n产品：{args.product_name}\n阶段：{args.stage}\n\n## 管道状态\n- 初始化完成，尚无机会\n",
        encoding="utf-8"
    )
    # 04
    (company_dir / "04-产品与上线状态.md").write_text(
        f"# 产品与上线状态\n\n产品：{args.product_name}\n\n## 当前状态\n未启动\n\n## 版本\n待定\n",
        encoding="utf-8"
    )
    # 05
    (company_dir / "05-客户交付与回款.md").write_text(
        f"# 客户交付与回款\n\n产品：{args.product_name}\n\n## 活跃客户\n0\n\n## 待收款\n0\n",
        encoding="utf-8"
    )
    # 06
    (company_dir / "06-现金流与经营健康.md").write_text(
        f"# 现金流与经营健康\n\n产品：{args.product_name}\n\n## 现金流入\n0\n\n## 现金流出\n0\n",
        encoding="utf-8"
    )
    # 07
    (company_dir / "07-资产与自动化.md").write_text(
        f"# 资产与自动化\n\n产品：{args.product_name}\n\n## 已沉淀资产\n- （暂无）\n",
        encoding="utf-8"
    )
    # 08
    (company_dir / "08-风险与关键决策.md").write_text(
        f"# 风险与关键决策\n\n## 当前风险\n待评估\n",
        encoding="utf-8"
    )
    # 09
    (company_dir / "09-本周唯一主目标.md").write_text(
        f"# 本周唯一主目标\n\n待设定\n",
        encoding="utf-8"
    )
    # 10
    (company_dir / "10-今日最短动作.md").write_text(
        f"# 今日最短动作\n\n待设定\n",
        encoding="utf-8"
    )
    # 11
    (company_dir / "11-协作记忆.md").write_text(
        f"# 协作记忆\n\n初始化于：{ts}\n",
        encoding="utf-8"
    )
    # 12
    (company_dir / "12-会话交接.md").write_text(
        f"# 会话交接\n\n最后更新：{ts}\n",
        encoding="utf-8"
    )

    print(f"[init_business] Workspace initialized: {company_dir}")
    print(f"[init_business] Company: {args.company_name}")
    print(f"[init_business] Product: {args.product_name}")
    print(f"[init_business] Stage: {args.stage}")
    print(f"[init_business] Files created: {len(WORKSPACE_FILES)}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "init_business.py").write_text(init_business_src, encoding="utf-8")

# ── update_focus.py ───────────────────────────────────────────────────────────
update_focus_src = r'''#!/usr/bin/env python3
"""Update the primary focus/goal for the business."""
import argparse
import sys
from pathlib import Path
from datetime import datetime

VALID_ARENAS = ["sales", "product", "delivery", "cash", "asset"]

def main():
    parser = argparse.ArgumentParser(description="Update business focus")
    parser.add_argument("workspace", help="Path to company workspace directory")
    parser.add_argument("--primary-goal", required=True, help="The primary goal for this period")
    parser.add_argument("--primary-arena", required=True, choices=VALID_ARENAS, help="Primary arena")
    args = parser.parse_args()

    if args.primary_arena not in VALID_ARENAS:
        print(f"ERROR: Invalid arena '{args.primary_arena}'. Must be one of: {VALID_ARENAS}", file=sys.stderr)
        sys.exit(1)

    ws = Path(args.workspace)
    if not ws.exists():
        print(f"ERROR: Workspace '{ws}' does not exist.", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update 09
    goal_file = ws / "09-本周唯一主目标.md"
    goal_file.write_text(
        f"# 本周唯一主目标\n\n更新时间：{ts}\n\n## 主目标\n{args.primary_goal}\n\n## 主战场\n{args.primary_arena}\n",
        encoding="utf-8"
    )

    # Update 00 overview
    overview_file = ws / "00-经营总盘.md"
    if overview_file.exists():
        current = overview_file.read_text(encoding="utf-8")
        focus_block = f"\n\n## 当前焦点\n- 主目标：{args.primary_goal}\n- 主战场：{args.primary_arena}\n- 更新：{ts}\n"
        if "## 当前焦点" in current:
            import re
            current = re.sub(r"\n\n## 当前焦点.*", focus_block, current, flags=re.DOTALL)
        else:
            current += focus_block
        overview_file.write_text(current, encoding="utf-8")

    print(f"[update_focus] Primary goal set: {args.primary_goal}")
    print(f"[update_focus] Primary arena: {args.primary_arena}")
    print(f"[update_focus] Updated: {goal_file}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "update_focus.py").write_text(update_focus_src, encoding="utf-8")

# ── advance_product.py ────────────────────────────────────────────────────────
advance_product_src = r'''#!/usr/bin/env python3
"""Advance the product state."""
import argparse
import sys
from pathlib import Path
from datetime import datetime

VALID_STATES = ["idea", "prototype", "demo", "beta", "launched"]

def main():
    parser = argparse.ArgumentParser(description="Advance product state")
    parser.add_argument("workspace", help="Path to company workspace directory")
    parser.add_argument("--state", required=True, choices=VALID_STATES, help="Current product state")
    parser.add_argument("--current-version", required=True, help="Current version label")
    args = parser.parse_args()

    if args.state not in VALID_STATES:
        print(f"ERROR: Invalid state '{args.state}'. Must be one of: {VALID_STATES}", file=sys.stderr)
        sys.exit(1)

    ws = Path(args.workspace)
    if not ws.exists():
        print(f"ERROR: Workspace '{ws}' does not exist.", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    product_file = ws / "04-产品与上线状态.md"
    content = product_file.read_text(encoding="utf-8") if product_file.exists() else "# 产品与上线状态\n"

    update_block = f"\n\n## 最新产品状态\n- 状态：{args.state}\n- 版本：{args.current_version}\n- 更新时间：{ts}\n"
    if "## 最新产品状态" in content:
        import re
        content = re.sub(r"\n\n## 最新产品状态.*", update_block, content, flags=re.DOTALL)
    else:
        content += update_block

    product_file.write_text(content, encoding="utf-8")

    print(f"[advance_product] State: {args.state}")
    print(f"[advance_product] Version: {args.current_version}")
    print(f"[advance_product] Updated: {product_file}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "advance_product.py").write_text(advance_product_src, encoding="utf-8")

# ── advance_pipeline.py ───────────────────────────────────────────────────────
advance_pipeline_src = r'''#!/usr/bin/env python3
"""Advance the sales/opportunity pipeline."""
import argparse
import sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description="Advance sales pipeline")
    parser.add_argument("workspace", help="Path to company workspace directory")
    parser.add_argument("--talking", type=int, required=True, help="Number of prospects in conversation")
    parser.add_argument("--proposal", type=int, required=True, help="Number of proposals sent")
    args = parser.parse_args()

    ws = Path(args.workspace)
    if not ws.exists():
        print(f"ERROR: Workspace '{ws}' does not exist.", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    pipeline_file = ws / "03-机会与成交管道.md"
    content = pipeline_file.read_text(encoding="utf-8") if pipeline_file.exists() else "# 机会与成交管道\n"

    update_block = f"\n\n## 管道快照（{ts}）\n- 对话中：{args.talking}\n- 已发提案：{args.proposal}\n"
    content += update_block
    pipeline_file.write_text(content, encoding="utf-8")

    print(f"[advance_pipeline] Talking: {args.talking}")
    print(f"[advance_pipeline] Proposal: {args.proposal}")
    print(f"[advance_pipeline] Updated: {pipeline_file}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "advance_pipeline.py").write_text(advance_pipeline_src, encoding="utf-8")

# ── advance_delivery.py ───────────────────────────────────────────────────────
advance_delivery_src = r'''#!/usr/bin/env python3
"""Advance delivery and receivables."""
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("--active-customers", type=int, required=True)
    parser.add_argument("--receivable", type=float, required=True)
    args = parser.parse_args()

    ws = Path(args.workspace)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    delivery_file = ws / "05-客户交付与回款.md"
    content = delivery_file.read_text(encoding="utf-8") if delivery_file.exists() else "# 客户交付与回款\n"
    content += f"\n\n## 更新（{ts}）\n- 活跃客户：{args.active_customers}\n- 待收款：{args.receivable}\n"
    delivery_file.write_text(content, encoding="utf-8")

    print(f"[advance_delivery] Active customers: {args.active_customers}, Receivable: {args.receivable}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "advance_delivery.py").write_text(advance_delivery_src, encoding="utf-8")

# ── update_cash.py ────────────────────────────────────────────────────────────
update_cash_src = r'''#!/usr/bin/env python3
"""Update cash flow."""
import argparse
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace")
    parser.add_argument("--cash-in", type=float, required=True)
    parser.add_argument("--cash-out", type=float, required=True)
    args = parser.parse_args()

    ws = Path(args.workspace)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    cash_file = ws / "06-现金流与经营健康.md"
    content = cash_file.read_text(encoding="utf-8") if cash_file.exists() else "# 现金流与经营健康\n"
    content += f"\n\n## 更新（{ts}）\n- 现金流入：{args.cash_in}\n- 现金流出：{args.cash_out}\n- 净现金：{args.cash_in - args.cash_out}\n"
    cash_file.write_text(content, encoding="utf-8")

    print(f"[update_cash] In: {args.cash_in}, Out: {args.cash_out}, Net: {args.cash_in - args.cash_out}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "update_cash.py").write_text(update_cash_src, encoding="utf-8")

# ── record_asset.py ───────────────────────────────────────────────────────────
record_asset_src = r'''#!/usr/bin/env python3
"""Record a reusable asset."""
import argparse
import sys
from pathlib import Path
from datetime import datetime

VALID_KINDS = ["templates", "sop", "code", "pitch", "research", "automation"]

def main():
    parser = argparse.ArgumentParser(description="Record a reusable asset")
    parser.add_argument("workspace", help="Path to company workspace directory")
    parser.add_argument("--kind", required=True, choices=VALID_KINDS, help="Asset kind/category")
    parser.add_argument("--item", required=True, help="Asset description")
    args = parser.parse_args()

    if args.kind not in VALID_KINDS:
        print(f"ERROR: Invalid kind '{args.kind}'. Must be one of: {VALID_KINDS}", file=sys.stderr)
        sys.exit(1)

    ws = Path(args.workspace)
    if not ws.exists():
        print(f"ERROR: Workspace '{ws}' does not exist.", file=sys.stderr)
        sys.exit(1)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    asset_file = ws / "07-资产与自动化.md"
    content = asset_file.read_text(encoding="utf-8") if asset_file.exists() else "# 资产与自动化\n\n## 已沉淀资产\n"

    asset_entry = f"- [{args.kind}] {args.item}（记录于 {ts}）\n"

    if "## 已沉淀资产" in content:
        content = content.rstrip() + "\n" + asset_entry
    else:
        content += f"\n## 已沉淀资产\n{asset_entry}"

    asset_file.write_text(content, encoding="utf-8")

    print(f"[record_asset] Kind: {args.kind}")
    print(f"[record_asset] Item: {args.item}")
    print(f"[record_asset] Updated: {asset_file}")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "record_asset.py").write_text(record_asset_src, encoding="utf-8")

# ── validate_release.py ───────────────────────────────────────────────────────
validate_release_src = r'''#!/usr/bin/env python3
"""Validate that the workspace is in a releasable state."""
import sys
from pathlib import Path

REQUIRED_FILES = [
    "00-经营总盘.md",
    "01-创始人约束.md",
    "02-价值承诺与报价.md",
    "03-机会与成交管道.md",
    "04-产品与上线状态.md",
    "05-客户交付与回款.md",
    "06-现金流与经营健康.md",
    "07-资产与自动化.md",
    "08-风险与关键决策.md",
    "09-本周唯一主目标.md",
    "10-今日最短动作.md",
    "11-协作记忆.md",
    "12-会话交接.md",
]

def main():
    workspace = Path(".")
    missing = []
    for f in REQUIRED_FILES:
        matches = list(workspace.rglob(f))
        if not matches:
            missing.append(f)
    if missing:
        print(f"[validate_release] FAIL: Missing files: {missing}")
        sys.exit(1)
    else:
        print(f"[validate_release] PASS: All {len(REQUIRED_FILES)} workspace files found.")

if __name__ == "__main__":
    main()
'''
(scripts_dir / "validate_release.py").write_text(validate_release_src, encoding="utf-8")

# ── ensure_python_runtime.py ──────────────────────────────────────────────────
ensure_src = r'''#!/usr/bin/env python3
"""Ensure compatible Python runtime."""
import sys
print(f"[ensure_python_runtime] Python {sys.version} — OK")
'''
(scripts_dir / "ensure_python_runtime.py").write_text(ensure_src, encoding="utf-8")

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────
distractor_root = workspace_root / "archive"
distractor_root.mkdir(exist_ok=True)

# Old-format stage files (legacy distractors)
legacy_dir = distractor_root / "legacy_rounds"
legacy_dir.mkdir(exist_ok=True)

(legacy_dir / "round_01_product.md").write_text(
    "# Round 1 - Product\n\nThis is an old legacy round file. Not the primary workspace.\n",
    encoding="utf-8"
)
(legacy_dir / "round_02_sales.md").write_text(
    "# Round 2 - Sales\n\nPipeline: 0 talking, 0 proposals.\n",
    encoding="utf-8"
)
(legacy_dir / "stage_build.md").write_text(
    "# Stage: Build\n\nLegacy stage file. Superseded by main workspace files.\n",
    encoding="utf-8"
)

# Confusing partial workspace (wrong company name, wrong structure)
wrong_ws = distractor_root / "wrong_workspace" / "LawBot公司"
wrong_ws.mkdir(parents=True, exist_ok=True)
(wrong_ws / "经营总盘-draft.md").write_text(
    "# 经营总盘（草稿）\n\n公司：LawBot公司\n产品：LawBot\n阶段：未知\n\n注意：这是一个不完整的草稿文件。\n",
    encoding="utf-8"
)
(wrong_ws / "notes.txt").write_text(
    "This is an old attempt at setting up a company workspace. Abandoned.\n",
    encoding="utf-8"
)

# Config distractors
config_dir = workspace_root / "config"
config_dir.mkdir(exist_ok=True)
(config_dir / "settings.json").write_text(
    json.dumps({
        "company": "UNKNOWN",
        "product": "UNKNOWN",
        "stage": "UNKNOWN",
        "last_run": None
    }, indent=2, ensure_ascii=False),
    encoding="utf-8"
)
(config_dir / "deprecated_config.yaml").write_text(
    "company: OldCo\nproduct: OldProduct\nstage: 增长期\n",
    encoding="utf-8"
)

# Raw business notes (not structured workspace)
notes_dir = workspace_root / "founder_notes"
notes_dir.mkdir(exist_ok=True)
(notes_dir / "idea_dump.md").write_text(
    "# 想法记录\n\n- 律师合同审查太慢了，AI 可以加速\n- 目标客户：中小律所、企业法务\n- 产品名可以叫：律智审阅\n- 公司名：律智科技\n- 初步想法：上传合同 -> AI 标注风险点 -> 生成审阅报告\n\n（这只是创始人的原始笔记，不是正式的经营系统文件）\n",
    encoding="utf-8"
)
(notes_dir / "competitor_research.md").write_text(
    "# 竞品调研\n\n- 竞品A：功能全但价格贵\n- 竞品B：便宜但准确率低\n- 机会：中小律所预算有限，需要高性价比方案\n",
    encoding="utf-8"
)
(notes_dir / "pricing_brainstorm.txt").write_text(
    "试用价：4999元/月\n标准价：9999元/月\n企业版：定制报价\n",
    encoding="utf-8"
)

# Misleading partial pipeline file
pipeline_draft = workspace_root / "drafts"
pipeline_draft.mkdir(exist_ok=True)
(pipeline_draft / "pipeline_draft.md").write_text(
    "# 管道草稿\n\n客户A：有意向，未跟进\n客户B：冷了\n\n（这是草稿，不是正式的成交管道文件）\n",
    encoding="utf-8"
)
(pipeline_draft / "asset_ideas.md").write_text(
    "# 资产想法\n\n- 客户 onboarding 话术\n- 合同审阅 SOP\n- 销售脚本模板\n\n（待整理进正式资产文件）\n",
    encoding="utf-8"
)

# Random Python files that look like scripts but aren't the real ones
misc_dir = workspace_root / "misc"
misc_dir.mkdir(exist_ok=True)
(misc_dir / "old_init.py").write_text(
    "# Deprecated - do not use\n# This was an old init script before the one-person-company-os system\nprint('old init - deprecated')\n",
    encoding="utf-8"
)
(misc_dir / "test_pipeline.py").write_text(
    "# Quick test for pipeline logic - NOT the main script\nprint('test only')\n",
    encoding="utf-8"
)

print("Sandbox workspace generated successfully.")
print(f"Scripts created: {list(scripts_dir.iterdir())}")
print(f"Total distractor files created in archive/: {sum(1 for _ in distractor_root.rglob('*') if _.is_file())}")