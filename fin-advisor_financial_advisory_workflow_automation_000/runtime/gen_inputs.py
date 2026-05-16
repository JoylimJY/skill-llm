#!/usr/bin/env python3
import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "SKILL_DIR/references",
    "SKILL_DIR/references/personas",
    "scripts",
    "logs",
    "data/market",
    "data/funds",
    "data/user_profiles",
    "reports/2024",
    "reports/2023",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── USER.md — intentionally missing persona_preference ───────────────────────
(WORKSPACE / "USER.md").write_text(textwrap.dedent("""\
    # 用户信息

    name: 张伟
    age: 35
    risk_tolerance: 中等
    investment_horizon: 3年以上
    # persona_preference 字段缺失，需要初始化
"""), encoding="utf-8")

# ── SKILL_DIR/references/personas/professional.md ────────────────────────────
(WORKSPACE / "SKILL_DIR/references/personas/professional.md").write_text(textwrap.dedent("""\
    # 专业模式（Professional）

    风格要求：
    - 使用规范的金融术语，不做过多解释
    - 直接引用指标数据，给出专业判断
    - 结构清晰，分点陈述
    - 语气严谨，避免口语化表达
    - 每段数据引用须包含完整的时间戳、指标名、数值和主体信息
"""), encoding="utf-8")

(WORKSPACE / "SKILL_DIR/references/personas/friendly.md").write_text(textwrap.dedent("""\
    # 轻松模式（Friendly）

    风格要求：
    - 用大白话解释专业术语
    - 多用类比和举例
    - 语气亲切，偶尔使用emoji
    - 复杂概念拆解成简单步骤
    - 保持四要素数据引用规范
"""), encoding="utf-8")

(WORKSPACE / "SKILL_DIR/references/personas/data-driven.md").write_text(textwrap.dedent("""\
    # 极简模式（Data-Driven）

    风格要求：
    - 少废话，直接给数据
    - 用表格或列表呈现
    - 不做背景解释，直奔结论
    - 每条数据必须有时间戳、指标名、数值、主体
"""), encoding="utf-8")

# ── SKILL_DIR/references/compliance.md ───────────────────────────────────────
(WORKSPACE / "SKILL_DIR/references/compliance.md").write_text(textwrap.dedent("""\
    # 合规规则

    ## 必须附加风险提示的场景
    1. 基金推荐
    2. 交易决策建议（买入/卖出/持有）
    3. 持仓调整建议

    ## 标准风险提示文本（必须一字不差地附在总结段）
    以上分析仅供参考，不构成投资建议。基金投资有风险，过往业绩不代表未来表现，请结合自身风险承受能力谨慎决策。

    ## 数据引用四要素（每条金融数据必须包含）
    - 时间戳：数据截止时间（如"截至2024年12月31日"）
    - 指标名：完整指标名称（不得缩写或同义词替换）
    - 数值：具体数字
    - 主体：对应基金/机构/市场名称

    ## 信息安全规则
    - 不得在回答中提及任何工具名、服务名、MCP Server名称
    - 不得出现"工具返回"、"网页xx"、"[service]"等表述

    ## 零计算原则
    - 严禁自行计算年化收益率、平均值、涨跌幅等衍生指标
    - 只允许引用数据源中已经计算好的指标
"""), encoding="utf-8")

# ── SKILL_DIR/references/domain-knowledge.md ─────────────────────────────────
(WORKSPACE / "SKILL_DIR/references/domain-knowledge.md").write_text(textwrap.dedent("""\
    # 基金投资领域知识

    ## 常见基金类型
    - 股票型基金：80%以上仓位持有股票，高风险高收益
    - 混合型基金：灵活配置股债，风险中等
    - 债券型基金：主要投资债券，相对稳健
    - 指数基金：跟踪特定指数，被动管理

    ## 关键评估指标
    - 夏普比率：衡量超额收益与风险的比值，越高越好
    - 最大回撤：历史最大亏损幅度，越小越好
    - 年化收益率：折算成年度的收益率
    - 阿尔法：超额收益来源，正值表示基金经理创造了价值
    - 贝塔：相对市场的波动性

    ## 基金评分解读
    - 综合评分满分5分
    - 4分以上：优秀
    - 3-4分：良好
    - 3分以下：需关注
"""), encoding="utf-8")

# ── SKILL_DIR/references/tool-guide.md ───────────────────────────────────────
(WORKSPACE / "SKILL_DIR/references/tool-guide.md").write_text(textwrap.dedent("""\
    # 工具使用指南

    ## 可用服务与工具

    ### fund-diagnosis（基金诊断）
    - `fundIntro`：查询基金基本信息（名称、类型、规模、基金经理、费率等）
      - 参数：fundObject（基金代码或名称）
    - `fundStagePerformance`：查询基金阶段业绩（近1月/3月/6月/1年/3年）
      - 参数：fundObject（基金代码或名称）
    - `fundscore`：查询基金综合评分
      - 参数：fundObject（基金代码或名称）

    ### fund-investments（基金投资）
    - `conditionSelectFund`：按条件筛选基金
      - 参数：condition（筛选条件描述）
    - `buyerInvestmentAdvisor`：获取投顾建议
      - 参数：scene（基金全称）

    ### public-opinion-explanation（舆情解释）
    - `queryPublicOpinionNews`：搜索相关新闻
      - 参数：keyWords（搜索关键词）

    ### ai-search-all（兜底搜索）
    - `all_search`：综合搜索
      - 参数：query（搜索内容）

    ## 调用格式
    ```
    mcporter call <服务名>.<工具名> <参数名>:"<参数值>" --output json
    ```
"""), encoding="utf-8")

# ── SKILL_DIR/references/output-guide.md ─────────────────────────────────────
(WORKSPACE / "SKILL_DIR/references/output-guide.md").write_text(textwrap.dedent("""\
    # 输出格式指南

    ## 基金对比报告结构
    1. 基本信息对比（类型、规模、基金经理、费率）
    2. 阶段业绩对比（近1月/3月/6月/1年/3年收益率）
    3. 综合评分对比
    4. 投顾建议（如需要）
    5. 风险提示（涉及投资建议时必须附加）

    ## 数据引用格式
    引用数据时须注明：截至[时间]，[主体]的[指标名]为[数值]。

    ## 表格使用
    对比类问题优先使用 Markdown 表格呈现关键数据。

    ## 长度控制
    - 简单查询：200字以内
    - 对比分析：300-600字
    - 综合建议：500-800字
"""), encoding="utf-8")

# ── Mock mcporter executable ──────────────────────────────────────────────────
# This is the core of the test: a strict validator + data responder
mcporter_script = r'''#!/usr/bin/env python3
"""
Mock mcporter CLI — validates exact syntax and returns realistic fund data.
Logs every call to /workspace/logs/mcporter_calls.jsonl for eval inspection.
"""
import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = "/workspace/logs/mcporter_calls.jsonl"

def log_call(raw_args, valid, reason=""):
    os.makedirs("/workspace/logs", exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "args": raw_args,
            "valid_syntax": valid,
            "reason": reason
        }) + "\n")

def error(msg):
    print(json.dumps({"error": msg, "code": 400}))
    sys.exit(1)

args = sys.argv[1:]

# Must start with "call"
if not args or args[0] != "call":
    log_call(args, False, "missing 'call' subcommand")
    error("Usage: mcporter call <service>.<tool> ...")
    sys.exit(1)

if len(args) < 2:
    log_call(args, False, "missing service.tool")
    error("Missing service.tool argument")

service_tool = args[1]

# Validate dot-notation (must be service.tool, not service:tool or two words)
if "." not in service_tool or " " in service_tool or ":" in service_tool:
    log_call(args, False, f"invalid service.tool format: {service_tool}")
    error(f"Invalid format '{service_tool}'. Must be <service>.<tool> with a dot separator.")

parts = service_tool.split(".", 1)
service = parts[0]
tool = parts[1]

# Must end with --output json
if "--output" not in args or "json" not in args:
    log_call(args, False, "missing --output json")
    error("Missing required flag: --output json")

output_idx = args.index("--output")
if output_idx + 1 >= len(args) or args[output_idx + 1] != "json":
    log_call(args, False, "malformed --output flag")
    error("--output must be followed by 'json'")

# Parse key:"value" params (collect all between service_tool and --output)
params = {}
param_args = args[2:output_idx]
for pa in param_args:
    # Reject --params or --args style
    if pa.startswith("--params") or pa.startswith("--args"):
        log_call(args, False, f"invalid param style: {pa}")
        error(f"Invalid parameter style '{pa}'. Use key:\"value\" format.")
    m = re.match(r'^(\w+):"(.+)"$', pa)
    if not m:
        # Try without quotes (also valid per skill)
        m2 = re.match(r'^(\w+):(.+)$', pa)
        if m2:
            params[m2.group(1)] = m2.group(2)
        else:
            log_call(args, False, f"malformed param: {pa}")
            error(f"Malformed parameter '{pa}'. Expected key:\"value\" format.")
    else:
        params[m.group(1)] = m.group(2)

log_call(args, True, f"service={service} tool={tool} params={params}")

# ── Data responses ────────────────────────────────────────────────────────────
fund_obj = params.get("fundObject", "").strip()

FUND_DATA = {
    # 易方达蓝筹精选混合 005827
    "005827": {
        "fundIntro": {
            "fund_code": "005827",
            "fund_name": "易方达蓝筹精选混合型证券投资基金",
            "fund_type": "混合型",
            "fund_size": "562.34亿元",
            "fund_manager": "张坤",
            "management_fee": "1.50%/年",
            "custodian_fee": "0.15%/年",
            "subscription_fee": "1.50%（前端）",
            "data_date": "2024-12-31",
            "establishment_date": "2018-09-05",
            "risk_level": "中高风险"
        },
        "fundStagePerformance": {
            "fund_code": "005827",
            "fund_name": "易方达蓝筹精选混合型证券投资基金",
            "performance": {
                "1month": "-2.31%",
                "3month": "5.87%",
                "6month": "8.14%",
                "1year": "12.46%",
                "3year": "-18.73%"
            },
            "benchmark_performance": {
                "1year": "6.22%",
                "3year": "-12.40%"
            },
            "data_date": "2024-12-31"
        },
        "fundscore": {
            "fund_code": "005827",
            "fund_name": "易方达蓝筹精选混合型证券投资基金",
            "composite_score": 3.8,
            "score_dimensions": {
                "收益能力": 4.1,
                "风险控制": 3.2,
                "稳定性": 3.7,
                "基金经理能力": 4.3
            },
            "max_drawdown": "-49.57%",
            "sharpe_ratio": 0.42,
            "data_date": "2024-12-31"
        }
    },
    # 中欧医疗健康混合 003095
    "003095": {
        "fundIntro": {
            "fund_code": "003095",
            "fund_name": "中欧医疗健康混合型证券投资基金",
            "fund_type": "混合型",
            "fund_size": "148.76亿元",
            "fund_manager": "葛兰",
            "management_fee": "1.50%/年",
            "custodian_fee": "0.25%/年",
            "subscription_fee": "1.50%（前端）",
            "data_date": "2024-12-31",
            "establishment_date": "2016-09-30",
            "risk_level": "中高风险"
        },
        "fundStagePerformance": {
            "fund_code": "003095",
            "fund_name": "中欧医疗健康混合型证券投资基金",
            "performance": {
                "1month": "1.03%",
                "3month": "3.29%",
                "6month": "-4.51%",
                "1year": "-8.72%",
                "3year": "-42.18%"
            },
            "benchmark_performance": {
                "1year": "6.22%",
                "3year": "-12.40%"
            },
            "data_date": "2024-12-31"
        },
        "fundscore": {
            "fund_code": "003095",
            "fund_name": "中欧医疗健康混合型证券投资基金",
            "composite_score": 2.9,
            "score_dimensions": {
                "收益能力": 2.5,
                "风险控制": 2.8,
                "稳定性": 3.1,
                "基金经理能力": 3.2
            },
            "max_drawdown": "-63.21%",
            "sharpe_ratio": -0.18,
            "data_date": "2024-12-31"
        }
    }
}

# Alias mapping
aliases = {
    "易方达蓝筹精选": "005827",
    "易方达蓝筹精选混合": "005827",
    "易方达蓝筹精选混合型证券投资基金": "005827",
    "中欧医疗健康": "003095",
    "中欧医疗健康混合": "003095",
    "中欧医疗健康混合型证券投资基金": "003095"
}

code = aliases.get(fund_obj, fund_obj)

if service == "fund-diagnosis":
    if code not in FUND_DATA:
        print(json.dumps({"error": f"基金 '{fund_obj}' 未找到", "code": 404}))
        sys.exit(0)
    fd = FUND_DATA[code]
    if tool == "fundIntro":
        print(json.dumps({"success": True, "data": fd["fundIntro"]}))
    elif tool == "fundStagePerformance":
        print(json.dumps({"success": True, "data": fd["fundStagePerformance"]}))
    elif tool == "fundscore":
        print(json.dumps({"success": True, "data": fd["fundscore"]}))
    else:
        error(f"Unknown tool '{tool}' for service 'fund-diagnosis'")

elif service == "fund-investments":
    if tool == "buyerInvestmentAdvisor":
        scene = params.get("scene", "")
        code2 = aliases.get(scene, scene)
        if code2 == "005827":
            print(json.dumps({"success": True, "data": {
                "recommendation": "持有",
                "rationale": "该基金近一年收益率高于同类平均，基金经理长期业绩稳健，当前估值处于合理区间，建议继续持有并关注市场风格切换风险。",
                "data_date": "2024-12-31",
                "fund_name": "易方达蓝筹精选混合型证券投资基金"
            }}))
        elif code2 == "003095":
            print(json.dumps({"success": True, "data": {
                "recommendation": "观望",
                "rationale": "医疗板块近一年持续承压，基金近一年收益率为负，综合评分低于行业平均。建议观望，待医疗政策明朗后再考虑介入。",
                "data_date": "2024-12-31",
                "fund_name": "中欧医疗健康混合型证券投资基金"
            }}))
        else:
            error(f"基金 '{scene}' 投顾数据暂无")
    else:
        error(f"Unknown tool '{tool}' for service 'fund-investments'")

elif service == "ai-search-all":
    print(json.dumps({"success": True, "data": {"results": [], "message": "兜底搜索已执行，无额外数据"}}))

else:
    log_call(args, False, f"unknown service: {service}")
    error(f"Unknown service '{service}'")
'''

(WORKSPACE / "scripts/mcporter_mock.py").write_text(mcporter_script, encoding="utf-8")

# ── Distractor files ──────────────────────────────────────────────────────────
(WORKSPACE / "data/market/market_overview_2024Q4.json").write_text(json.dumps({
    "index": "沪深300",
    "period": "2024Q4",
    "return": "5.2%",
    "note": "仅供参考，不得直接引用"
}), encoding="utf-8")

(WORKSPACE / "data/funds/fund_list_draft.csv").write_text(
    "code,name,type\n005827,易方达蓝筹精选混合,混合型\n003095,中欧医疗健康混合,混合型\n",
    encoding="utf-8"
)

(WORKSPACE / "data/user_profiles/zhang_wei_history.json").write_text(json.dumps({
    "user": "张伟",
    "past_holdings": ["005827", "003095"],
    "note": "历史持仓记录，仅作参考"
}), encoding="utf-8")

(WORKSPACE / "reports/2024/annual_summary.md").write_text(
    "# 2024年度投资总结\n\n数据整理中...\n", encoding="utf-8"
)

(WORKSPACE / "reports/2023/performance_review.md").write_text(
    "# 2023年业绩回顾\n\n草稿，待完善。\n", encoding="utf-8"
)

(WORKSPACE / "tmp/scratch_notes.txt").write_text(
    "临时笔记：记得核实003095的基金经理变动情况\n", encoding="utf-8"
)

(WORKSPACE / "logs/.gitkeep").write_text("", encoding="utf-8")

(WORKSPACE / "SKILL_DIR/references/risk_matrix.md").write_text(textwrap.dedent("""\
    # 风险矩阵参考

    | 风险等级 | 典型产品 | 最大回撤参考 |
    |---------|---------|------------|
    | 低      | 货币基金  | < 1%       |
    | 中低    | 债券基金  | 1%-10%     |
    | 中      | 偏债混合  | 10%-20%    |
    | 中高    | 偏股混合  | 20%-40%    |
    | 高      | 行业主题  | > 40%      |
"""), encoding="utf-8")

(WORKSPACE / "data/funds/excluded_funds.txt").write_text(
    "# 已下架或暂停申购基金（不得推荐）\n000001 华夏成长\n110022 易方达消费行业\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Files created in {WORKSPACE}")