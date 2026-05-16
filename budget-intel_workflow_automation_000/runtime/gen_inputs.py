import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# Create directory structure
dirs = [
    "research/raw_notes",
    "research/financials",
    "research/bidding_records",
    "research/hr_data",
    "tools",
    "reports/drafts",
    "reports/archive",
    "config",
    "logs",
    "templates",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── budget_engine.py (the proprietary tool) ──────────────────────────────────
budget_engine = '''#!/usr/bin/env python3
"""
budget_engine.py — 企业数字化预算估算引擎
Usage:
  python budget_engine.py --method A --revenue 50 --industry manufacturing
  python budget_engine.py --method B --tech_headcount 280 --industry manufacturing
  python budget_engine.py --method C --latest_funding 30 --industry manufacturing
  python budget_engine.py --method D --bid_total 1200 --industry manufacturing
  python budget_engine.py --merge --results_json \'[...]\'
  python budget_engine.py --confidence --sources_json \'[...]\'

Output: JSON to stdout
"""
import argparse
import json
import sys
import math

INDUSTRY_PARAMS = {
    "finance":        {"it_ratio": (0.03, 0.05), "digital_ratio": (0.40, 0.60), "ai_ratio": (0.15, 0.25)},
    "internet":       {"it_ratio": (0.08, 0.15), "digital_ratio": (0.60, 0.80), "ai_ratio": (0.25, 0.40)},
    "manufacturing":  {"it_ratio": (0.01, 0.03), "digital_ratio": (0.30, 0.50), "ai_ratio": (0.10, 0.20)},
    "retail":         {"it_ratio": (0.02, 0.04), "digital_ratio": (0.40, 0.60), "ai_ratio": (0.15, 0.25)},
    "healthcare":     {"it_ratio": (0.02, 0.03), "digital_ratio": (0.30, 0.50), "ai_ratio": (0.10, 0.20)},
}

SOURCE_CONFIDENCE = {
    "financial_report": 0.95,
    "bid_record":       0.85,
    "news_pr":          0.60,
    "job_posting":      0.50,
    "social_data":      0.30,
}

def method_a(revenue_yi, industry):
    """营收比例法 — revenue in 亿元"""
    p = INDUSTRY_PARAMS[industry]
    it_lo = revenue_yi * p["it_ratio"][0]
    it_hi = revenue_yi * p["it_ratio"][1]
    dg_lo = it_lo * p["digital_ratio"][0]
    dg_hi = it_hi * p["digital_ratio"][1]
    ai_lo = dg_lo * p["ai_ratio"][0]
    ai_hi = dg_hi * p["ai_ratio"][1]
    return {
        "method": "A",
        "it_budget_yi": [round(it_lo, 4), round(it_hi, 4)],
        "digital_budget_yi": [round(dg_lo, 4), round(dg_hi, 4)],
        "ai_budget_yi": [round(ai_lo, 4), round(ai_hi, 4)],
    }

def method_b(tech_headcount, industry):
    """人员比例法"""
    COST_PER_HEAD = {
        "finance": 80,  # 万/人
        "internet": 120,
        "manufacturing": 40,
        "retail": 50,
        "healthcare": 60,
    }
    cost = COST_PER_HEAD[industry]
    total_wan = tech_headcount * cost
    p = INDUSTRY_PARAMS[industry]
    dg_lo = total_wan * p["digital_ratio"][0] / 10000
    dg_hi = total_wan * p["digital_ratio"][1] / 10000
    ai_lo = dg_lo * p["ai_ratio"][0]
    ai_hi = dg_hi * p["ai_ratio"][1]
    return {
        "method": "B",
        "it_budget_yi": [round(total_wan/10000, 4), round(total_wan/10000, 4)],
        "digital_budget_yi": [round(dg_lo, 4), round(dg_hi, 4)],
        "ai_budget_yi": [round(ai_lo, 4), round(ai_hi, 4)],
    }

def method_c(latest_funding_yi, industry):
    """融资推算法"""
    tech_ratio_lo, tech_ratio_hi = 0.30, 0.50
    it_lo = latest_funding_yi * tech_ratio_lo
    it_hi = latest_funding_yi * tech_ratio_hi
    p = INDUSTRY_PARAMS[industry]
    dg_lo = it_lo * p["digital_ratio"][0]
    dg_hi = it_hi * p["digital_ratio"][1]
    ai_lo = dg_lo * p["ai_ratio"][0]
    ai_hi = dg_hi * p["ai_ratio"][1]
    return {
        "method": "C",
        "it_budget_yi": [round(it_lo, 4), round(it_hi, 4)],
        "digital_budget_yi": [round(dg_lo, 4), round(dg_hi, 4)],
        "ai_budget_yi": [round(ai_lo, 4), round(ai_hi, 4)],
    }

def method_d(bid_total_wan, industry):
    """招投标反推法 — bid_total in 万元"""
    multiplier_lo, multiplier_hi = 3, 5
    it_lo = bid_total_wan * multiplier_lo
    it_hi = bid_total_wan * multiplier_hi
    p = INDUSTRY_PARAMS[industry]
    dg_lo = it_lo * p["digital_ratio"][0] / 10000
    dg_hi = it_hi * p["digital_ratio"][1] / 10000
    ai_lo = dg_lo * p["ai_ratio"][0]
    ai_hi = dg_hi * p["ai_ratio"][1]
    return {
        "method": "D",
        "it_budget_yi": [round(it_lo/10000, 4), round(it_hi/10000, 4)],
        "digital_budget_yi": [round(dg_lo, 4), round(dg_hi, 4)],
        "ai_budget_yi": [round(ai_lo, 4), round(ai_hi, 4)],
    }

def merge_results(results):
    """Merge multiple method results by averaging low and high bounds"""
    it_los = [r["it_budget_yi"][0] for r in results]
    it_his = [r["it_budget_yi"][1] for r in results]
    dg_los = [r["digital_budget_yi"][0] for r in results]
    dg_his = [r["digital_budget_yi"][1] for r in results]
    ai_los = [r["ai_budget_yi"][0] for r in results]
    ai_his = [r["ai_budget_yi"][1] for r in results]
    return {
        "merged": True,
        "methods_used": [r["method"] for r in results],
        "it_budget_yi": [round(sum(it_los)/len(it_los), 4), round(sum(it_his)/len(it_his), 4)],
        "digital_budget_yi": [round(sum(dg_los)/len(dg_los), 4), round(sum(dg_his)/len(dg_his), 4)],
        "ai_budget_yi": [round(sum(ai_los)/len(ai_los), 4), round(sum(ai_his)/len(ai_his), 4)],
    }

def calc_confidence(sources):
    """
    sources: list of dicts with keys: type (str), weight (float 0-1)
    综合置信度 = 加权平均置信度 × 数据源数量系数
    数量系数: 1源→0.7, 2源→0.85, 3源→0.95, 4+源→1.0
    """
    if not sources:
        return {"confidence": 0.0, "detail": "no sources"}
    
    total_weight = sum(s["weight"] for s in sources)
    if total_weight == 0:
        return {"confidence": 0.0, "detail": "zero weight"}
    
    weighted_avg = sum(SOURCE_CONFIDENCE.get(s["type"], 0.30) * s["weight"] for s in sources) / total_weight
    
    n = len(sources)
    if n >= 4:
        count_coeff = 1.0
    elif n == 3:
        count_coeff = 0.95
    elif n == 2:
        count_coeff = 0.85
    else:
        count_coeff = 0.70
    
    confidence = round(weighted_avg * count_coeff, 4)
    return {
        "confidence": confidence,
        "confidence_pct": f"{confidence*100:.1f}%",
        "weighted_avg_base": round(weighted_avg, 4),
        "count_coefficient": count_coeff,
        "source_count": n,
    }

def main():
    parser = argparse.ArgumentParser(description="Budget Engine")
    parser.add_argument("--method", choices=["A","B","C","D"])
    parser.add_argument("--revenue", type=float, help="年营收（亿元），用于方法A")
    parser.add_argument("--tech_headcount", type=int, help="技术团队人数，用于方法B")
    parser.add_argument("--latest_funding", type=float, help="最新融资额（亿元），用于方法C")
    parser.add_argument("--bid_total", type=float, help="历史中标总额（万元），用于方法D")
    parser.add_argument("--industry", choices=list(INDUSTRY_PARAMS.keys()), default="manufacturing")
    parser.add_argument("--merge", action="store_true")
    parser.add_argument("--results_json", type=str)
    parser.add_argument("--confidence", action="store_true")
    parser.add_argument("--sources_json", type=str)
    
    args = parser.parse_args()
    
    if args.merge and args.results_json:
        results = json.loads(args.results_json)
        print(json.dumps(merge_results(results), ensure_ascii=False, indent=2))
        return
    
    if args.confidence and args.sources_json:
        sources = json.loads(args.sources_json)
        print(json.dumps(calc_confidence(sources), ensure_ascii=False, indent=2))
        return
    
    if args.method == "A":
        if args.revenue is None:
            print(json.dumps({"error": "--revenue required for method A"}))
            sys.exit(1)
        print(json.dumps(method_a(args.revenue, args.industry), ensure_ascii=False, indent=2))
    elif args.method == "B":
        if args.tech_headcount is None:
            print(json.dumps({"error": "--tech_headcount required for method B"}))
            sys.exit(1)
        print(json.dumps(method_b(args.tech_headcount, args.industry), ensure_ascii=False, indent=2))
    elif args.method == "C":
        if args.latest_funding is None:
            print(json.dumps({"error": "--latest_funding required for method C"}))
            sys.exit(1)
        print(json.dumps(method_c(args.latest_funding, args.industry), ensure_ascii=False, indent=2))
    elif args.method == "D":
        if args.bid_total is None:
            print(json.dumps({"error": "--bid_total required for method D"}))
            sys.exit(1)
        print(json.dumps(method_d(args.bid_total, args.industry), ensure_ascii=False, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "tools" / "budget_engine.py").write_text(budget_engine, encoding="utf-8")

# ─── Raw research notes (messy, scattered, partially formatted) ───────────────

# Company profile note
company_note = """
调研笔记 - 隆鑫精密制造（深圳）有限公司
记录人：张销售
日期：2025-05-10

公司背景：
- 成立时间：2009年，深圳南山区
- 主营业务：高端精密零部件加工、工业机器人关键部件
- 员工规模：约 4200 人（含工厂工人约 3000 人，管理/研发/IT 约 1200 人）
- 技术/IT团队：大概 280 人左右（听说他们有个规模不小的信息化部门）
- 认证：ISO 9001, IATF 16949（汽车供应链）

财务情况（非上市，从工商年报、行业报告推算）：
- 2024年营业收入：约 ¥48 亿元（不确定，朋友说可能更高，区间 45-52 亿）
- 利润率：制造业均值，估计 8-12%

关键联系人（不完整）：
- 王建国，CTO，听说很关注自动化和AI视觉检测，掌管全公司技术方向
- 李华，信息化总监（采购决策人？），负责系统采购
- 陈敏，业务VP，负责供应链数字化，对ROI要求很高
- 赵强，采购部总监，合规要求严

行业备注：汽车零件制造，精密加工
"""
(WORKSPACE / "research" / "raw_notes" / "company_profile_longxin.txt").write_text(company_note, encoding="utf-8")

# Bidding records (messy)
bid_note = """
隆鑫精密 - 近期招投标记录（从公开平台摘录）

2024-03：MES系统升级改造项目 - 中标金额：¥380万 - 承建商：某系统集成商
2024-07：ERP系统二期实施 - 中标金额：¥520万 - 承建商：SAP合作伙伴  
2023-11：工业视觉检测系统 - 中标金额：¥210万 - 承建商：机器视觉公司
2023-06：数字化工厂基础设施 - 中标金额：¥410万 - 承建商：华为
2025-01：AI质检平台POC项目 - 中标金额：¥150万（注：仅POC，正式项目Q3）

合计中标金额（近2年）：约 ¥1670万

注：这只是公开招标部分，单笔100万以下的采购不一定公开。
实际IT采购应该远不止这些。
"""
(WORKSPACE / "research" / "bidding_records" / "public_bids_2023_2025.txt").write_text(bid_note, encoding="utf-8")

# HR/recruitment data
hr_note = """
隆鑫精密 招聘信息分析（BOSS直聘/拉勾网 截图整理）
整理日期：2025-05-08

当前在招技术岗位（约60个）：
- Java后端工程师 x 8
- 数据工程师 x 5
- AI算法工程师（视觉方向）x 6
- 工业互联网架构师 x 2
- 前端工程师 x 4
- DevOps工程师 x 3
- 安全工程师 x 2
- 数据库管理员 x 2
- MES/ERP系统实施顾问 x 4
- 其他IT支持 x 若干

技术栈关键词（JD中出现频率高）：
Java Spring Cloud, Kubernetes, 阿里云, 华为云（少量）, MySQL, ClickHouse,
PyTorch, OpenCV, MinIO, Kafka, Prometheus, 钉钉集成

薪资范围推算技术人员平均约35-45K/月（深圳水平）

判断：信息化团队在扩张中，有明显云原生和AI转型迹象
"""
(WORKSPACE / "research" / "hr_data" / "recruitment_analysis.txt").write_text(hr_note, encoding="utf-8")

# News/PR snippets
news_note = """
相关新闻摘录：

1. [2025-03-15 制造业数字化周刊]
   隆鑫精密宣布启动"智能工厂2025"战略，计划在未来两年内完成全工厂的
   数字化升级，涵盖AI质检、智能排产、设备预测性维护三大场景。
   CEO表示将加大数字化投入，"这是公司保持竞争力的核心战略"。

2. [2025-02-28 南方日报]
   深圳精密制造业迎来AI升级潮。多家企业获得政府数字化补贴，
   隆鑫精密入选深圳市"灯塔工厂"培育名单。

3. [2024-11-10 中国汽车供应链报]
   隆鑫精密通过比亚迪新供应商认证，成为比亚迪新能源汽车零部件一级供应商，
   预计将带来年增量订单 ¥8-12 亿元，同时比亚迪要求供应商强制接入其供应链数字化平台。

4. [2025-04-02 公司PR]
   隆鑫精密与华为签署数字化战略合作协议，将在工厂智能化、
   5G工业互联网等领域展开深度合作。
"""
(WORKSPACE / "research" / "raw_notes" / "news_snippets.txt").write_text(news_note, encoding="utf-8")

# Existing vendor info
vendor_note = """
已知供应商信息（从拜访和内部情报）

ERP: SAP S/4HANA（2022年上线，5年合同，预计2027年续约）
MES: 炬光科技（国产MES，2024年升级版本）
云平台: 阿里云（主要），少量华为云测试环境
OA: 钉钉（企业版，标准套餐）
视觉检测: 海康威视（传统方案，正在考虑AI升级）
BI/数据: 帆软FineBI（报表层），底层数据仓库自建

已知痛点：
- 各系统数据孤岛严重
- MES和ERP对接不好
- 视觉检测系统误检率偏高（约3%，行业要求<0.5%）
- 缺乏统一的数据中台
"""
(WORKSPACE / "research" / "raw_notes" / "vendor_landscape.txt").write_text(vendor_note, encoding="utf-8")

# Financial report fragment (simulated)
fin_report = """
深圳市工商年报数据摘录（非公开财报，第三方数据服务商提供）
企业：隆鑫精密制造（深圳）有限公司
统一社会信用代码：91440300XXXXXXXXXX
报告期：2024年度

营业收入：48.3亿元（数据来源：工商年报申报数据，置信度较高）
资产总额：62.1亿元
负债率：38%
研发投入：1.2亿元（占营收2.5%）
员工人数：4218人

注：以上数据为第三方数据平台提取，非经审计财务报表。
"""
(WORKSPACE / "research" / "financials" / "annual_report_extract_2024.txt").write_text(fin_report, encoding="utf-8")

# ─── Distractor files ─────────────────────────────────────────────────────────

# Old report template
(WORKSPACE / "reports" / "archive" / "old_report_template_2023.txt").write_text(
    "旧版报告模板（已废弃，请使用新版格式）\n公司：XXX\nIT预算：待填\n...\n", encoding="utf-8"
)

# Draft incomplete report
(WORKSPACE / "reports" / "drafts" / "draft_longxin_incomplete.txt").write_text(
    "草稿 - 隆鑫精密分析\n行业：制造业\n（未完成）\n营收估算：待确认\n", encoding="utf-8"
)

# Unrelated company note
(WORKSPACE / "research" / "raw_notes" / "another_client_notes.txt").write_text(
    "客户：某互联网公司（非本次分析对象）\n营收50亿\nIT预算估算中...\n", encoding="utf-8"
)

# Config file
config = {
    "version": "1.2",
    "output_dir": "reports",
    "tools_dir": "tools",
    "default_industry": "manufacturing",
    "currency": "CNY",
    "fiscal_year": 2025
}
(WORKSPACE / "config" / "settings.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

# Log file (distractor)
(WORKSPACE / "logs" / "search_history.log").write_text(
    "2025-05-01 搜索：隆鑫精密 招投标\n2025-05-03 搜索：精密制造业IT投入\n2025-05-05 搜索：深圳制造业数字化\n",
    encoding="utf-8"
)

# Template file
(WORKSPACE / "templates" / "budget_categories_ref.txt").write_text(
    """参考品类列表（15+）：
云服务-计算, 云服务-存储, 云服务-数据库, AI-大模型, AI-CV/NLP,
开发工具, 数据分析/BI, 安全, 网络基础设施, ERP/MES等核心系统,
工业互联网/IoT, 低代码平台, 培训/咨询, 运维监控, 协同办公
""", encoding="utf-8"
)

# Another distractor - wrong formula attempt
(WORKSPACE / "research" / "financials" / "wrong_calculation_attempt.txt").write_text(
    "尝试估算（错误方法）：IT预算 = 员工人数 × 5000元 ≈ 2100万（此方法不适用制造业）\n",
    encoding="utf-8"
)

# Partial competitive analysis
(WORKSPACE / "reports" / "archive" / "competitor_analysis_2024.txt").write_text(
    "竞争对手分析 - 同类制造业IT投入对标\n富士康：IT预算约占营收1.5%\n比亚迪：约2.2%\n...\n",
    encoding="utf-8"
)

# Industry research
(WORKSPACE / "research" / "raw_notes" / "industry_context.txt").write_text(
    """制造业2025年数字化趋势：
1. 工业大模型/AI质检成为刚需
2. 数字孪生技术进入成熟期
3. 供应链协同数字化（尤其汽车产业链）
4. 灯塔工厂评选推动标杆建设
5. 数据安全合规要求提升（等保3.0）
""", encoding="utf-8"
)

print("[gen_inputs] Workspace created successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")