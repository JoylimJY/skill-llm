#!/bin/bash
set -e

# Make tools executable
chmod +x /workspace/tools/url_validator.py 2>/dev/null || true

# Start a lightweight mock search API server
cat > /tmp/mock_search_server.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""
Mock search and fetch server for the deep-research-executor skill evaluation.
Provides realistic NEV market data in both Chinese and English.
"""
import json
import random
from flask import Flask, request, jsonify

app = Flask(__name__)
random.seed(42)

# Mock search results database - Chinese queries
CHINESE_RESULTS = {
    "新能源汽车": [
        {"url": "https://mock.auto.china/nev-market-2024", "title": "2024年中国新能源汽车市场全景报告", "snippet": "2024年中国新能源汽车销量突破1000万辆，比亚迪以35%市场份额领跑"},
        {"url": "https://mock.caam.org.cn/statistics/2024", "title": "中国汽车工业协会2024年产销数据", "snippet": "乘联会数据显示2024年新能源乘用车渗透率超过45%"},
        {"url": "https://mock.evtank.cn/report-2024", "title": "EVTank新能源汽车白皮书2024", "snippet": "全球新能源汽车销量中中国占据65%份额"},
        {"url": "https://mock.gasgoo.com/news/nev2024", "title": "盖世汽车：2024新能源市场深度解析", "snippet": "比亚迪、特斯拉、华为问界三强格局形成"},
    ],
    "比亚迪 市场份额": [
        {"url": "https://mock.bydauto.com.cn/investor/2024annual", "title": "比亚迪2024年度报告", "snippet": "比亚迪2024年销售新能源汽车超过360万辆，同比增长41%"},
        {"url": "https://mock.securities.china/byd-analysis", "title": "证券分析：比亚迪竞争优势深度研究", "snippet": "刀片电池技术和垂直整合供应链是比亚迪核心竞争力"},
        {"url": "https://mock.caixin.com/nev/byd-2024", "title": "财新：比亚迪全球化战略剖析", "snippet": "比亚迪出口量2024年突破40万辆，进入欧洲、东南亚市场"},
    ],
    "新能源汽车 电池技术": [
        {"url": "https://mock.catl.com/tech/lfp-vs-nmc", "title": "宁德时代：磷酸铁锂与三元锂电池技术对比", "snippet": "磷酸铁锂电池在安全性和循环寿命上优势显著，三元锂能量密度更高"},
        {"url": "https://mock.soochow-sec.com/battery-report", "title": "苏州证券电池行业深度报告", "snippet": "固态电池预计2027年开始量产，将颠覆现有电池格局"},
        {"url": "https://mock.163auto.com/tech-trends", "title": "网易汽车：2024电动车技术趋势盘点", "snippet": "800V高压快充成为2024旗舰车型标配"},
    ],
    "新能源汽车 政策": [
        {"url": "https://mock.miit.gov.cn/nev-policy-2024", "title": "工信部新能源汽车产业发展规划", "snippet": "2024年新能源汽车购置税减免政策延续，补贴逐步退坡"},
        {"url": "https://mock.ndrc.gov.cn/carbon-credits", "title": "发改委双积分管理办法最新修订", "snippet": "2024年双积分政策进一步提高新能源积分比例要求"},
        {"url": "https://mock.finance.sina.com.cn/nev-subsidy", "title": "新浪财经：地方补贴政策汇总", "snippet": "全国30余个省市出台额外购车补贴，最高补贴达3万元"},
    ],
    "新能源汽车 出口 海外": [
        {"url": "https://mock.customs.gov.cn/nev-export-2024", "title": "海关总署：新能源汽车出口数据2024", "snippet": "2024年中国新能源汽车出口突破200万辆，同比增长78%"},
        {"url": "https://mock.21caijing.com/oversea-strategy", "title": "21世纪经济报道：中国新能源车出海策略", "snippet": "比亚迪、上汽、长城在欧洲遭遇反补贴税，转向东南亚和南美"},
        {"url": "https://mock.chinaev.org/global-expansion", "title": "中国电动汽车百人会：全球化路径研究", "snippet": "本地化生产是规避贸易壁垒的核心策略，匈牙利、泰国工厂相继建成"},
    ],
    "GTD 方法 详细步骤": [],  # Irrelevant query should return nothing useful
}

# Mock search results database - English queries
ENGLISH_RESULTS = {
    "China NEV market 2024": [
        {"url": "https://mock.marklines.com/china-nev-2024", "title": "MarkLines: China NEV Market Report 2024", "snippet": "China's NEV market reached 10.5 million units in 2024, with BYD leading at 35% market share"},
        {"url": "https://mock.bloomberg.com/energy/china-ev-2024", "title": "Bloomberg: China's EV Boom Continues in 2024", "snippet": "Tesla China faces increasing pressure from domestic rivals as BYD, Li Auto post record sales"},
        {"url": "https://mock.iea.org/ev-outlook-china", "title": "IEA Global EV Outlook - China Chapter 2024", "snippet": "China accounts for 65% of global EV sales, with NEV penetration exceeding 45%"},
        {"url": "https://mock.reuters.com/business/china-ev-market", "title": "Reuters: China EV Market Competitive Dynamics", "snippet": "AITO (Huawei-backed) emerged as a major player with Wenjie M7 and M9 models"},
    ],
    "BYD market share sales 2024": [
        {"url": "https://mock.carsalesbase.com/byd-2024", "title": "BYD 2024 Annual Sales Results", "snippet": "BYD sold 3.6 million NEVs in 2024, up 41% YoY, maintaining its position as world's top EV seller"},
        {"url": "https://mock.wsj.com/byd-global-strategy", "title": "WSJ: BYD's Global Ambitions Face Trade Barriers", "snippet": "BYD's blade battery technology and vertical integration give it cost advantages over competitors"},
    ],
    "China EV battery technology LFP NMC": [
        {"url": "https://mock.sciencedirect.com/battery-comparison-2024", "title": "Science Direct: LFP vs NMC Battery Technology Comparison", "snippet": "LFP batteries dominate China's mass market EVs due to lower cost and better safety profile"},
        {"url": "https://mock.techcrunch.com/solid-state-battery-china", "title": "TechCrunch: China's Race to Solid-State Batteries", "snippet": "CATL and BYD are investing billions in solid-state battery R&D, targeting 2027-2028 mass production"},
        {"url": "https://mock.electrive.com/800v-charging-china", "title": "Electrive: 800V Ultra-Fast Charging Becomes Standard in China", "snippet": "Porsche Taycan-level 800V architecture now standard in Chinese premium EVs"},
    ],
    "China NEV government policy subsidies 2024": [
        {"url": "https://mock.spglobal.com/china-ev-policy-2024", "title": "S&P Global: China NEV Policy Framework 2024", "snippet": "Purchase tax exemption for NEVs extended through 2025, dual-credit system tightened"},
        {"url": "https://mock.nikkei.com/china-ev-subsidies", "title": "Nikkei Asia: China's EV Support Policies Evolve", "snippet": "China shifts from direct subsidies to infrastructure investment and technology R&D support"},
    ],
    "China EV export overseas expansion 2024": [
        {"url": "https://mock.ft.com/china-ev-exports", "title": "FT: China EV Exports Surge Despite EU Tariffs", "snippet": "China exported over 2 million EVs in 2024, with Southeast Asia and South America as key growth markets"},
        {"url": "https://mock.economist.com/china-ev-global", "title": "The Economist: China's EV Makers Go Global", "snippet": "BYD's Thailand and Hungary plants represent a new phase of localized global manufacturing strategy"},
    ],
    "NIO Xpeng Li Auto 2024 performance": [
        {"url": "https://mock.nio.com/investor-2024", "title": "NIO 2024 Investor Presentation", "snippet": "NIO delivered 221,970 vehicles in 2024, expanding into Europe with battery swap network"},
        {"url": "https://mock.xpeng.com/annual-2024", "title": "Xpeng 2024 Annual Report", "snippet": "Xpeng's MONA M03 disrupted the mass market segment at RMB 119,800 starting price"},
    ],
}

def search_mock(query, lang=None):
    """Find best matching results for a query."""
    query_lower = query.lower()
    all_results = []
    
    # Determine search pool based on query language/content
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in query)
    
    search_pool = CHINESE_RESULTS if has_chinese else ENGLISH_RESULTS
    
    for key, results in search_pool.items():
        key_lower = key.lower()
        # Check if any keyword from query matches
        query_words = query_lower.replace('，', ' ').replace(',', ' ').split()
        key_words = key_lower.split()
        if any(qw in key_lower for qw in query_words) or any(kw in query_lower for kw in key_words):
            all_results.extend(results)
    
    # If no specific match, return some general results
    if not all_results and has_chinese:
        all_results = CHINESE_RESULTS.get("新能源汽车", [])[:2]
    elif not all_results:
        all_results = ENGLISH_RESULTS.get("China NEV market 2024", [])[:2]
    
    # Deduplicate by URL
    seen = set()
    deduped = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            deduped.append(r)
    
    return deduped[:5]  # Return max 5 results

# Mock page content database
PAGE_CONTENTS = {
    "https://mock.auto.china/nev-market-2024": """
# 2024年中国新能源汽车市场全景报告

## 市场总览
2024年，中国新能源汽车市场迎来历史性突破，全年销量突破1050万辆，同比增长35.5%。
新能源汽车市场渗透率达到45.6%，意味着每两辆新售乘用车中就有一辆是新能源车。

## 主要厂商市场份额
- 比亚迪：35.2%（360万辆）
- 特斯拉中国：8.1%（85万辆）
- 华为问界：6.3%（66万辆）
- 理想汽车：5.2%（55万辆）
- 埃安（广汽）：4.8%（50万辆）
- 蔚来：2.1%（22万辆）
- 小鹏：1.9%（20万辆）
- 其他：36.4%

## 价格区间分布
- 15万以下：38%
- 15-25万：35%
- 25-40万：18%
- 40万以上：9%
""",
    "https://mock.caam.org.cn/statistics/2024": """
# 中国汽车工业协会2024年产销数据报告

根据中国汽车工业协会统计，2024年汽车行业主要数据如下：

## 整体市场
- 2024年全国汽车销量：3100万辆
- 新能源汽车销量：1050万辆，占比33.9%

## 同比增长
- 新能源汽车：+35.5%
- 传统燃油车：-8.2%
- 纯电动（BEV）：+28.3%
- 插电混动（PHEV）：+52.1%

## 区域分布
- 广东省：18.5%
- 浙江省：12.3%
- 江苏省：11.8%
- 北京市：8.2%
- 上海市：7.9%
""",
    "https://mock.marklines.com/china-nev-2024": """
# MarkLines: China NEV Market Report 2024

## Executive Summary
China's New Energy Vehicle (NEV) market achieved record-breaking results in 2024, with total sales 
surpassing 10.5 million units, representing 35.5% year-over-year growth.

## Market Share Leaders
1. BYD: 3.6M units (35.2% share) - World's top EV seller
2. Tesla China: 850K units (8.1%)
3. AITO/Huawei Wenjie: 660K units (6.3%)
4. Li Auto: 550K units (5.2%)
5. GAC Aion: 500K units (4.8%)

## Key Trends
- NEV penetration rate reached 45.6% of total passenger car sales
- PHEV segment grew 52.1%, outpacing pure BEV growth of 28.3%
- Price war intensified as BYD cut prices on 10+ models
- Huawei-backed AITO emerged as dominant premium segment player
""",
    "https://mock.catl.com/tech/lfp-vs-nmc": """
# 宁德时代：磷酸铁锂与三元锂电池技术深度对比

## 技术对比
### 磷酸铁锂（LFP）电池
- 能量密度：160-180 Wh/kg
- 循环寿命：>3000次
- 安全性：极高（热失控风险低）
- 成本：低（不含钴、镍）
- 主要应用：15-25万元区间车型

### 三元锂（NMC/NCA）电池
- 能量密度：220-280 Wh/kg
- 循环寿命：1000-2000次
- 安全性：较好（需要热管理系统）
- 成本：较高（含钴、镍）
- 主要应用：25万以上高端车型

## 市场趋势
2024年LFP电池市场份额达到68%，较2022年的55%大幅提升。
宁德时代麒麟电池实现LFP能量密度提升至255 Wh/kg，缩小与三元锂差距。
""",
    "https://mock.sciencedirect.com/battery-comparison-2024": """
# LFP vs NMC Battery Technology: A Comprehensive 2024 Review

## Abstract
This paper reviews the current state of lithium iron phosphate (LFP) and nickel-manganese-cobalt (NMC) 
battery technologies as deployed in China's EV market.

## LFP Technology Advantages
- Thermal stability: Onset of thermal runaway at 270°C vs 180°C for NMC
- Cycle life: 3,000+ cycles vs 1,000-2,000 for NMC
- Cost: 30-40% lower than NMC due to absence of cobalt and nickel
- Environmental impact: Lower mining footprint

## NMC Advantages
- Energy density: 220-280 Wh/kg vs 160-180 Wh/kg for LFP
- Better performance in cold weather conditions

## Market Implications
LFP now dominates 68% of China's EV battery market in 2024.
CATL's Kirin Battery and BYD's Blade Battery have pushed LFP energy density boundaries.
Solid-state batteries from CATL and BYD expected in mass production by 2027-2028.
""",
    "https://mock.miit.gov.cn/nev-policy-2024": """
# 工业和信息化部新能源汽车产业发展政策2024

## 主要政策措施

### 购置税减免
- 2024年延续新能源汽车购置税减免政策
- 售价30万以下新能源汽车免征购置税
- 预计2025年延续，2026年开始逐步恢复

### 双积分政策
- 2024年新能源积分比例要求：乘用车企业30%
- 2025年要求提升至35%
- 积分交易价格：100-200元/积分

### 充电基础设施补贴
- 公共充电桩新增补贴：每桩500-2000元
- 高速公路充电网络覆盖率要求：2025年达95%

### 研发支持
- 固态电池研发专项资金：100亿元
- 智能网联汽车测试示范区：20个城市
""",
    "https://mock.spglobal.com/china-ev-policy-2024": """
# S&P Global: China NEV Policy Framework 2024 Analysis

## Purchase Tax Exemption
China's purchase tax exemption for NEVs (vehicles priced under RMB 300,000) has been extended 
through 2025, providing approximately RMB 10,000-20,000 savings per vehicle.

## Dual Credit System
The dual credit policy requires automakers to achieve 30% NEV credit ratio in 2024, rising to 35% in 2025.
Non-compliant companies face production restrictions or must purchase credits from competitors.

## Infrastructure Investment
- RMB 300 billion committed to charging infrastructure through 2025
- Target: 1 charging point per 3 EVs by 2025

## Technology R&D Support
- RMB 10 billion dedicated to solid-state battery research
- 20 smart connected vehicle testing zones established

## Policy Shift
China is transitioning from direct consumer subsidies (phased out 2022) to:
1. Tax incentives
2. Infrastructure investment
3. Technology R&D grants
""",
    "https://mock.customs.gov.cn/nev-export-2024": """
# 海关总署：2024年新能源汽车出口专题报告

## 出口总量
2024年中国新能源汽车出口达208万辆，同比增长78.3%，成为全球最大新能源汽车出口国。

## 主要出口目的地
1. 比利时（欧洲转口）：35万辆
2. 泰国：28万辆
3. 澳大利亚：18万辆
4. 巴西：15万辆
5. 英国：12万辆
6. 墨西哥：10万辆

## 主要出口品牌
- 上汽名爵（SAIC-MG）：45万辆
- 比亚迪：40万辆
- 特斯拉中国（出口）：38万辆
- 吉利（含极氪）：25万辆
- 长安：18万辆

## 贸易壁垒挑战
欧盟对中国电动汽车加征17-38%关税（2024年10月起）
应对策略：东南亚建厂、与欧洲车企合资
""",
    "https://mock.ft.com/china-ev-exports": """
# FT: China EV Exports Surge Despite EU Tariffs

## Record Export Numbers
China exported 2.08 million electric vehicles in 2024, a 78.3% increase from 2023, 
cementing its position as the world's largest NEV exporter.

## Top Destinations
1. Belgium (European distribution hub): 350,000 units
2. Thailand: 280,000 units
3. Australia: 180,000 units
4. Brazil: 150,000 units

## EU Tariff Challenge
The EU imposed additional duties of 17-38% on Chinese EVs effective October 2024:
- BYD: +17%
- Geely: +19%
- SAIC: +35%

## Strategic Responses
Chinese OEMs are responding with:
1. Localized manufacturing (BYD Hungary plant, SAIC Thailand)
2. Joint ventures with European partners
3. Pivot to tariff-free markets in Southeast Asia and South America
""",
    "https://mock.bloomberg.com/energy/china-ev-2024": """
# Bloomberg: China's EV Boom Continues in 2024

## Market Overview
China's EV market defied global slowdowns in 2024, with domestic sales of 10.5 million units.
The market is characterized by intense price competition and rapid technology advancement.

## Competitive Dynamics
### BYD's Dominance
BYD's vertical integration strategy - controlling everything from lithium mining to battery production 
to software - allows margins that competitors struggle to match.

### Tesla's Challenges  
Tesla China faces margin pressure, having cut Model 3 and Model Y prices three times in 2024.
Market share declined from 9.2% (2023) to 8.1% (2024).

### New Entrants
- Xiaomi SU7: 100,000 deliveries in first 7 months, challenging premium segment
- Huawei Wenjie M9: Dominant in luxury SUV segment above RMB 500,000

## Technology Race
- Autonomous driving: Huawei, BYD, Xpeng competing on L2+ systems
- Battery: 800V charging becoming standard in premium segment
""",
    "https://mock.nio.com/investor-2024": """
# NIO 2024 Investor Presentation Highlights

## Delivery Results
NIO delivered 221,970 vehicles in 2024, representing 38.7% growth YoY.

## Financial Performance
- Revenue: RMB 65.7 billion
- Gross margin: 10.7% (improved from 5.5% in 2023)
- Cash position: RMB 42.2 billion

## Key Initiatives
### Battery Swap Network
- 2,500+ battery swap stations globally
- 35 million+ swaps completed
- Battery-as-a-Service (BaaS) model: 55% of customers opted for subscription

### Europe Expansion
- Operations in Norway, Germany, Netherlands, Denmark, Sweden
- 20 European battery swap stations
- Targeting 50,000 European deliveries by 2026

## New Brand Strategy
- NIO: Premium segment (RMB 300,000+)
- ONVO: Mass market (RMB 150,000-250,000)
- Firefly: Entry level (launching 2025)
""",
    "https://mock.economist.com/china-ev-global": """
# The Economist: China's EV Makers Go Global

## The New Wave of Chinese Auto Exports
China's automakers are not just exporting cars—they're exporting an entire EV ecosystem.

## Localization as Strategy
### BYD's Hungary Plant
- Capacity: 300,000 vehicles/year
- Products: Atto 3, Seal, and upcoming European-spec models
- Investment: €4 billion
- Employment: 10,000 jobs

### SAIC's Thailand Hub
- MG brand dominates Thai EV market with 35% share
- Used as export base for ASEAN markets

## Technology Partnerships
Chinese companies are licensing technology rather than just building factories:
- CATL battery technology licensed to European OEMs
- Huawei's smart driving platform adopted by multiple OEMs

## Geopolitical Headwinds
Trade barriers, IP concerns, and national security reviews create challenges.
Chinese OEMs must demonstrate commitment to local economies to overcome resistance.
""",
    "https://mock.bydauto.com.cn/investor/2024annual": """
# 比亚迪2024年度投资者报告

## 销售业绩
2024年比亚迪新能源汽车总销量：362万辆（同比+41%）
- 纯电动（EV）：176万辆
- 插电混动（PHEV/DM）：186万辆

## 技术突破
### 刀片电池5.0
- 能量密度：210 Wh/kg（磷酸铁锂路线突破）
- 充电速度：30分钟充至80%（400V）
- 寿命：超过5000次循环

### 第五代DM混动技术
- 亏电油耗：2.9L/100km
- 纯电续航：200km
- 综合续航：2000km+

## 财务数据
- 营业收入：7,700亿元（同比+29%）
- 净利润：360亿元（同比+34%）
- 研发投入：546亿元

## 全球化布局
- 在建工厂：匈牙利（欧洲）、泰国（东南亚）、巴西
- 海外销售网络：70+国家
""",
    "https://mock.techcrunch.com/solid-state-battery-china": """
# TechCrunch: China's Race to Solid-State Batteries

## The Next Battery Frontier
Chinese battery makers are betting big on solid-state technology to maintain their global lead.

## CATL's Approach
CATL announced its "Condensed Battery" technology in 2024:
- Energy density: 500 Wh/kg (theoretical maximum)
- Current achievement: 320 Wh/kg in production samples
- Timeline: Limited production 2025, mass production 2027

## BYD's Strategy
BYD acquired a solid-state battery startup and is developing:
- All-solid-state batteries for premium models
- Target: Mass production 2028
- Expected energy density: 400+ Wh/kg

## Competitive Pressure
Toyota (Japan) and Samsung SDI (Korea) are also racing:
- Toyota: 1,200km range solid-state EV prototype demonstrated
- Samsung SDI: Partnership with Stellantis for North American market

## Investment Scale
Chinese government allocated RMB 10 billion specifically for solid-state battery R&D.
Total industry investment exceeds RMB 50 billion.
""",
    "https://mock.reuters.com/business/china-ev-market": """
# Reuters: China EV Market Competitive Dynamics 2024

## Huawei's Disruptive Entry
AITO (HUAWEI Wenjie) has emerged as a major disruptor with 660,000 deliveries in 2024.
Huawei's strategy: License technology and brand to multiple OEMs rather than becoming an automaker.

Key partners:
- Seres (Wenjie brand): 660K units
- Chery (Luxeed brand): Launching 2024
- BAIC (享界/Stelato): Luxury segment

## Price War Impact
Average transaction price for NEVs fell 8.3% in 2024 as competition intensified.
Winners: BYD (scale advantages), Huawei (technology premium)
Losers: Traditional joint ventures, some new entrants

## M&A Activity
- Xiaomi acquired EV startup tech assets
- Geely merged Zeekr with its EV operations
- Multiple smaller EV startups went bankrupt (Aiways, Letin, Hezhong)

## Smart Driving Competition
- Huawei's ADS 2.0: City-level NOA (Navigate on Autopilot)
- Xpeng's XNGP: Available in 243 cities
- Tesla FSD: Not approved for China yet
""",
}

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        data = request.get_json() or {}
        query = data.get('query', data.get('q', ''))
    else:
        query = request.args.get('query', request.args.get('q', ''))
    
    if not query:
        return jsonify({"error": "No query provided", "results": []}), 400
    
    results = search_mock(query)
    return jsonify({
        "query": query,
        "total": len(results),
        "results": results
    })

@app.route('/fetch', methods=['GET', 'POST'])
def fetch():
    if request.method == 'POST':
        data = request.get_json() or {}
        url = data.get('url', '')
    else:
        url = request.args.get('url', '')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    
    content = PAGE_CONTENTS.get(url)
    if content:
        return jsonify({
            "url": url,
            "status": 200,
            "content": content
        })
    else:
        return jsonify({
            "url": url,
            "status": 404,
            "content": f"Page not found: {url}"
        }), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "mock-search-server"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7890, debug=False)
MOCK_EOF

python3 /tmp/mock_search_server.py &
MOCK_PID=$!
echo $MOCK_PID > /tmp/mock_server.pid

# Wait for server to be ready
sleep 2
for i in $(seq 1 10); do
    if curl -s http://localhost:7890/health > /dev/null 2>&1; then
        echo "Mock search server started on port 7890 (PID: $MOCK_PID)"
        break
    fi
    sleep 1
done

# Create a convenience script that agents can use to interact with the server
cat > /workspace/tools/search.sh << 'SEARCH_EOF'
#!/bin/bash
# Usage: ./tools/search.sh "query string"
# Returns JSON search results from mock server
curl -s "http://localhost:7890/search?q=$(python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$1")"
SEARCH_EOF
chmod +x /workspace/tools/search.sh

cat > /workspace/tools/fetch_page.sh << 'FETCH_EOF'
#!/bin/bash
# Usage: ./tools/fetch_page.sh "https://url"
# Returns page content from mock server
curl -s "http://localhost:7890/fetch?url=$(python3 -c "import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$1")"
FETCH_EOF
chmod +x /workspace/tools/fetch_page.sh

# Also create Python wrappers
cat > /workspace/tools/search.py << 'PYEOF'
#!/usr/bin/env python3
"""Search tool - usage: python3 tools/search.py "query string" """
import sys
import json
import urllib.request
import urllib.parse

def search(query):
    encoded = urllib.parse.quote(query)
    url = f"http://localhost:7890/search?q={encoded}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())

if __name__ == '__main__':
    query = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else ''
    result = search(query)
    print(json.dumps(result, ensure_ascii=False, indent=2))
PYEOF
chmod +x /workspace/tools/search.py

cat > /workspace/tools/fetch_page.py << 'PYEOF2'
#!/usr/bin/env python3
"""Fetch page content - usage: python3 tools/fetch_page.py "https://url" """
import sys
import json
import urllib.request
import urllib.parse

def fetch(url):
    encoded = urllib.parse.quote(url, safe='')
    req_url = f"http://localhost:7890/fetch?url={encoded}"
    with urllib.request.urlopen(req_url) as resp:
        return json.loads(resp.read())

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else ''
    result = fetch(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
PYEOF2
chmod +x /workspace/tools/fetch_page.py

echo "Setup complete. Available tools:"
echo "  - tools/search.sh <query> or tools/search.py <query>"
echo "  - tools/fetch_page.sh <url> or tools/fetch_page.py <url>"
echo "  - Search API: http://localhost:7890/search?q=<query>"
echo "  - Fetch API:  http://localhost:7890/fetch?url=<url>"