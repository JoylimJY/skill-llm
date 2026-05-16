import os
import json
from pathlib import Path
import random

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Top-level distractor files ──────────────────────────────────────────────
def write(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")

write(f"{WORKSPACE}/README_DO_NOT_READ.txt", "This file is intentionally left blank.")
write(f"{WORKSPACE}/notes/scratch.txt", "old ideas\n- buy low sell high\n- diversify??")
write(f"{WORKSPACE}/notes/portfolio_2023.csv", "ticker,weight\nAAPL,0.3\nMSFT,0.2\nCASH,0.5\n")
write(f"{WORKSPACE}/reports/draft_report_v1.txt", "DRAFT - do not use\nThis is not a valid report.")
write(f"{WORKSPACE}/reports/archive_old/2022_summary.md", "# 2022 Summary\nNothing useful here.")
write(f"{WORKSPACE}/config/legacy_settings.json", json.dumps({"version": "1.0", "deprecated": True}))
write(f"{WORKSPACE}/logs/system.log", "INFO 2024-01-01 system started\nWARN fetch timeout\n")
write(f"{WORKSPACE}/tmp/cache_btc.json", json.dumps({"symbol": "BTC", "price": 45000, "stale": True}))
write(f"{WORKSPACE}/tmp/cache_gold.json", json.dumps({"symbol": "GOLD", "price": 1900, "stale": True}))
write(f"{WORKSPACE}/data/raw/prices_wrong_format.csv", "date,open,close\n2024-01-01,100,102\n")

# ── investment-committee skill directory ─────────────────────────────────────
base = f"{WORKSPACE}/investment-committee"

# scripts/fetch_price.py  — real script stub (agent must use it, not bypass it)
write(f"{base}/scripts/fetch_price.py", '''\
#!/usr/bin/env python3
"""Fetch latest price data from stooq.com for given symbols.
Symbol mapping:  700 -> 700.hk, BTC -> btc.v, GOLD/黄金 -> xauusd, NVDA -> nvda.us
Usage: python3 fetch_price.py SYM1 SYM2 ...
"""
import sys, json, datetime, random, math

MAPPING = {
    "BTC": "btc.v",
    "GOLD": "xauusd",
    "黄金": "xauusd",
    "700": "700.hk",
    "NVDA": "nvda.us",
    "GOOGL": "googl.us",
}

def fake_price(sym):
    random.seed(hash(sym) % 10000)
    prices = {
        "btc.v":  {"price": 67432.10, "change_pct": 2.34, "w52_low": 38500, "w52_high": 73750,
                   "rsi": 61.2, "ma200_dev": 18.5},
        "xauusd": {"price": 2341.50,  "change_pct": 0.55, "w52_low": 1820,  "w52_high": 2430,
                   "rsi": 57.8, "ma200_dev": 12.3},
        "googl.us":{"price": 175.20,  "change_pct": -0.8,  "w52_low": 120,   "w52_high": 193,
                   "rsi": 49.1, "ma200_dev": 6.2},
        "nvda.us": {"price": 875.40,  "change_pct": 3.10,  "w52_low": 373,   "w52_high": 974,
                   "rsi": 67.5, "ma200_dev": 42.1},
        "700.hk":  {"price": 368.20,  "change_pct": -1.2,  "w52_low": 270,   "w52_high": 420,
                   "rsi": 45.3, "ma200_dev": -2.1},
    }
    key = MAPPING.get(sym.upper(), sym.lower())
    if key in prices:
        d = prices[key].copy()
        d["symbol"] = key
        d["original"] = sym
        d["date"] = datetime.date.today().isoformat()
        return d
    return {"symbol": key, "original": sym, "price": 100.0, "change_pct": 0.0,
            "w52_low": 80, "w52_high": 120, "rsi": 50.0, "ma200_dev": 0.0,
            "date": datetime.date.today().isoformat()}

results = [fake_price(s) for s in sys.argv[1:]]
print(json.dumps(results, ensure_ascii=False, indent=2))
''')

# references/munger.md
write(f"{base}/references/munger.md", '''\
# 查理·芒格 — 投资哲学与分析框架

## 核心原则
1. **护城河检验**：企业是否拥有可持续的竞争优势？品牌、网络效应、成本优势、转换成本。
2. **生意本质**：这是一门好生意吗？资本回报率（ROIC）是否持续超过资本成本？
3. **能力圈**：我是否真正理解这项业务？若不理解，直接排除。
4. **价格vs价值**：以合理价格买入优质企业，而非以低价买入平庸企业。
5. **反转思维**：先问"什么会让这项投资失败"，而非"为什么会成功"。

## 对加密资产的立场
芒格明确表示比特币和加密资产"没有内在价值"，不在其能力圈内，通常给予极低评分（1-3/10）。
对黄金：虽承认其对冲属性，但认为持有优质企业更优，通常给予中低评分（3-5/10）。

## 评分输出格式
- **买入评分**：X/10（1=强烈回避，10=重仓买入）
- **核心论据**（3条，每条≤30字）
- **最大风险**（1条）
- **芒格结论**：[回避/观察/小仓位/标准仓位/重仓]
''')

# references/marks.md
write(f"{base}/references/marks.md", '''\
# 霍华德·马克斯 — 投资哲学与分析框架

## 核心原则
1. **周期位置**：当前处于周期的哪个阶段？乐观/悲观情绪是否极端？
2. **情绪温度计**：市场是贪婪还是恐惧？投资者行为是否理性？
3. **风险不对称**：上行空间 vs 下行风险，期望值是否正向？
4. **第二层思维**：市场已知什么？我的观点是否与共识不同且正确？
5. **防御优先**：在好机会出现前，保护资本比追求收益更重要。

## 对加密资产/黄金的立场
马克斯认为加密资产是高度投机性资产，需评估周期位置和情绪极端程度。
黄金：视为对冲工具，在宏观不确定性高时给予较高权重。

## 评分输出格式
- **买入评分**：X/10
- **周期判断**：[早期/中期/晚期/顶部/底部]
- **情绪温度**：[极度恐惧/恐惧/中性/贪婪/极度贪婪]
- **风险不对称分析**（上行%/下行%）
- **马克斯结论**：[回避/防御持有/标准配置/积极配置]
''')

# references/duan.md
write(f"{base}/references/duan.md", '''\
# 段永平 — 投资哲学与分析框架

## 核心原则
1. **本分**：企业是否在做"对的事"？管理层是否诚信、专注于长期？
2. **动机审查**：企业的核心动机是什么？是为用户创造价值还是短期套利？
3. **十年持有**：如果只能持有十年，今天是否愿意买入？
4. **停止做错误的事**：发现基本面恶化时，立即离场，不管成本。
5. **企业文化**：企业文化是否健康？能否吸引并留住顶尖人才？

## 对加密资产的立场
段永平认为比特币没有实业支撑，不符合"本分"原则，评分极低（1-2/10）。
黄金：非企业，无"本分"可言，通常不予评分或给最低分（2/10）。

## 评分输出格式
- **买入评分**：X/10
- **本分检验**：通过/不通过
- **十年持有意愿**：是/否
- **核心判断**（≤50字）
- **段永平结论**：[坚决回避/不感兴趣/可以关注/值得买入]
''')

# references/druckenmiller.md
write(f"{base}/references/druckenmiller.md", '''\
# 斯坦利·德鲁肯米勒 — 投资哲学与分析框架

## 核心原则
1. **宏观流动性**：全球流动性环境如何？美联储政策方向？美元强弱？
2. **催化剂识别**：未来3-6个月有什么具体催化剂推动价格？
3. **非对称押注**：只在风险/回报高度不对称时重仓。
4. **止损纪律**：明确止损位，一旦触发立即执行，不找借口。
5. **趋势跟随**：顺势而为，大趋势确立后加仓。

## 对加密资产/黄金的立场
德鲁肯米勒视BTC为"数字黄金"，在流动性宽松周期看多；黄金是对冲通胀和法币危机的标准工具。
两者均适合其宏观框架，评分基于当前宏观环境。

## 评分输出格式
- **买入评分**：X/10
- **宏观环境判断**：[顺风/中性/逆风]
- **催化剂**：（列举1-2个）
- **建议止损位**：$XXX（跌破则离场）
- **德鲁肯米勒结论**：[离场/减仓/持有/加仓/重仓做多]
''')

# references/simons.md
write(f"{base}/references/simons.md", '''\
# 詹姆斯·西蒙斯 — 量化分析框架

## 核心信号（五维）
1. **动量信号**：近1个月、3个月、12个月价格动量是否为正？
2. **均值回归**：价格是否偏离历史均值？偏离程度？（使用与200日均线偏差）
3. **波动率信号**：当前波动率相对历史是高还是低？
4. **成交量异常**：近期成交量是否有异常放大（突破信号）？
5. **相关性**：该资产与大盘/其他资产相关性是否在异常区间？

## 对加密资产/黄金的量化信号
西蒙斯框架完全基于统计数据，不做价值判断，BTC和黄金均可分析。
信号强度决定评分，不受主观偏好影响。

## 评分输出格式
- **买入评分**：X/10
- **五维信号**：动量[+/-]、均值回归[超买/中性/超卖]、波动率[高/中/低]、成交量[异常/正常]、相关性[异常/正常]
- **统计胜率**：XX%（基于历史相似形态）
- **西蒙斯结论**：[强烈卖出/卖出/中性/买入/强烈买入]
''')

# references/verdict.md
write(f"{base}/references/verdict.md", '''\
# 裁决整合规则

## 加权投票
五位委员各占20%权重，综合得分 = (芒格分 + 马克斯分 + 段永平分 + 德鲁肯米勒分 + 西蒙斯分) / 5

## 分差识别
计算所有委员对之间的分差，报告最大分差的两位委员及其分差值。

## 否决规则（一票否决触发条件）
- 任意委员评分 ≤ 2/10：触发"高风险警示"，报告中必须用 ⚠️ 标注
- 三位或以上委员评分 < 5/10：触发"委员会否决"，建议回避

## 特殊资产注意事项
对于加密资产（BTC等）和黄金：
- 芒格和段永平的评分因"无内在价值"立场天然偏低，报告中必须注明：
  「本标的宏观/量化视角权重更具参考价值」
- 重点参考：马克斯（周期）、德鲁肯米勒（宏观流动性）、西蒙斯（量化信号）

## 操作参数提取
从德鲁肯米勒的分析中提取止损价位，从各委员仓位建议中提取共识仓位。

## 最终裁决等级
- 综合分 ≥ 7.0：强烈推荐
- 综合分 5.0-6.9：谨慎推荐  
- 综合分 3.0-4.9：观望
- 综合分 < 3.0：回避
''')

# assets/report-template.md
write(f"{base}/assets/report-template.md", '''\
# 投资委员会裁决报告

**标的**：{asset}
**分析日期**：{date}
**分析模式**：{mode}

---

## 数据摘要
- 当前价格：{price}
- 日涨跌：{change_pct}
- 52周区间：{w52_low} ~ {w52_high}
- RSI：{rsi}
- 与200日均线偏差：{ma200_dev}%

---

## 委员独立评分

| 委员 | 评分 | 核心结论 |
|------|------|----------|
| 查理·芒格 | X/10 | ... |
| 霍华德·马克斯 | X/10 | ... |
| 段永平 | X/10 | ... |
| 斯坦利·德鲁肯米勒 | X/10 | ... |
| 詹姆斯·西蒙斯 | X/10 | ... |

---

## 委员会裁决

**加权综合分**：X.X/10
**最大分歧**：[委员A] vs [委员B]，分差 X 分
**否决规则检查**：[未触发/已触发]

{特殊资产注记}

**最终裁决**：[强烈推荐/谨慎推荐/观望/回避]

---

## 可执行操作参数

- 建议仓位：XX%
- 建议止损：$XXX
- 加仓条件：...

---

## 比较结论（比较模式）
{comparison_section}
''')

# history/ directory with some old distractor archives
write(f"{base}/history/2024-01-15_NVDA_买入判断.md", """\
# 投资委员会裁决报告
**标的**：NVDA
**分析日期**：2024-01-15
**加权综合分**：7.8/10
**最终裁决**：强烈推荐
""")
write(f"{base}/history/2024-02-20_腾讯_仓位管理.md", """\
# 投资委员会裁决报告
**标的**：腾讯(700.HK)
**分析日期**：2024-02-20
**加权综合分**：6.2/10
**最终裁决**：谨慎推荐
""")

# Extra distractors at various depths
write(f"{WORKSPACE}/investment-committee/scripts/old_fetch_v1.py", "# deprecated\nprint('do not use')")
write(f"{WORKSPACE}/investment-committee/scripts/backtest.py", "# placeholder backtest script\n")
write(f"{WORKSPACE}/investment-committee/assets/old_template_v0.md", "# Old template - deprecated\n")
write(f"{WORKSPACE}/investment-committee/tmp/session_draft.json", json.dumps({"status": "incomplete", "asset": "ETH"}))

print("Workspace generated successfully.")
print(f"Structure rooted at: {WORKSPACE}")