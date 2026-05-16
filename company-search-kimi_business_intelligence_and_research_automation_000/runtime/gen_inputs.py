import os
import json
import stat
from pathlib import Path

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Directory structure with distractors ---
dirs = [
    "/workspace/tools",
    "/workspace/data/raw_search",
    "/workspace/data/raw_fetch",
    "/workspace/data/archive",
    "/workspace/config",
    "/workspace/templates",
    "/workspace/logs",
    "/workspace/reports",
    "/workspace/tmp",
    "/workspace/ref",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "/workspace/config/settings.yaml": """
search_engine: kimi
max_results: 10
timeout: 30
retry: 3
""",
    "/workspace/config/company_list.csv": """company_name,industry,region
顺达物流科技有限公司,物流,深圳
顺达货运有限公司,货运,广州
快运通达科技,物流,上海
""",
    "/workspace/templates/report_old_v1.md": """# Company Report
## Basic Info
Name:
Founded:
## Risk
None found
""",
    "/workspace/templates/report_template_v2.md": """# {company} Research Report
Date: {date}
""",
    "/workspace/data/archive/old_report_2022.txt": """顺达物流 2022年调研摘要（已过期，仅供参考）
注册资本：5000万
成立时间：2015年
""",
    "/workspace/data/archive/competitor_analysis.txt": """竞争对手分析（草稿）
- 中国物流集团
- 顺丰速运
- 京东物流
""",
    "/workspace/logs/search_log_2024.txt": """2024-01-10 search: 顺达物流 工商信息
2024-01-10 search: 顺达货运 法人
2024-01-11 fetch: http://example.com/shunda
""",
    "/workspace/ref/industry_codes.json": json.dumps({
        "G59": "装卸搬运和仓储业",
        "G55": "道路运输业",
        "G56": "水上运输业",
        "I63": "互联网和相关服务"
    }, ensure_ascii=False, indent=2),
    "/workspace/tmp/scratch.txt": "TODO: verify credit code for 顺达物流科技",
    "/workspace/data/archive/notes.md": "注意：顺达物流科技和顺达货运是两家不同公司，需消歧。",
}

for path, content in distractors.items():
    Path(path).write_text(content, encoding="utf-8")

# --- Mock kimi_search tool ---
# Returns canned results based on query keywords
kimi_search_script = r'''#!/usr/bin/env python3
"""Mock kimi_search CLI tool. Usage: kimi_search "<query>" [--limit N]"""
import sys
import json
import re

def search(query):
    q = query.lower()
    results = []

    # Entity disambiguation results
    if "顺达物流" in query or "shunda" in q or "统一社会信用代码" in query:
        if "货运" not in query:
            results += [
                {
                    "title": "顺达物流科技有限公司 - 企业工商信息 - 国家企业信用信息公示系统",
                    "url": "http://www.gsxt.gov.cn/corp-query-entprise-info-100.html?id=shundawl001",
                    "snippet": "顺达物流科技有限公司，统一社会信用代码：91440300MA5FXXXXX8，注册地：广东省深圳市南山区科技园南区，成立日期：2016年03月15日，法定代表人：张建国，注册资本：8000万人民币，经营状态：存续。",
                    "source_type": "government",
                    "date": "2024-11-01"
                },
                {
                    "title": "顺达物流科技有限公司官网",
                    "url": "http://www.shunda-logistics.com.cn/about",
                    "snippet": "顺达物流科技有限公司成立于2016年，是一家专注于智慧物流解决方案的高新技术企业，总部位于深圳市南山区，业务覆盖仓储管理系统（WMS）、运输管理系统（TMS）及供应链金融服务。",
                    "source_type": "official_website",
                    "date": "2024-10-15"
                },
                {
                    "title": "顺达货运有限公司 工商信息",
                    "url": "http://www.qcc.com/firm/shundahuoyun",
                    "snippet": "顺达货运有限公司，注册地：广东省广州市番禺区，成立日期：2012年06月20日，法定代表人：李明辉，注册资本：500万人民币，经营状态：存续。",
                    "source_type": "commercial_platform",
                    "date": "2024-10-20"
                },
            ]

    # Basic company info
    if "法定代表人" in query or "注册资本" in query or "成立" in query or "工商" in query:
        results += [
            {
                "title": "顺达物流科技有限公司工商登记信息 - 国家企业信用信息公示系统",
                "url": "http://www.gsxt.gov.cn/corp-query-entprise-info-100.html?id=shundawl001",
                "snippet": "法定代表人：张建国；注册资本：8000万元人民币；实缴资本：未公示；成立日期：2016年03月15日；登记状态：存续；登记机关：深圳市市场监督管理局；核准日期：2024-06-12；经营范围：物流信息技术服务、仓储、道路货物运输代理、供应链管理。",
                "source_type": "government",
                "date": "2024-11-01"
            },
            {
                "title": "顺达物流科技有限公司 - 天眼查",
                "url": "http://www.tianyancha.com/company/shunda001",
                "snippet": "顺达物流科技有限公司：注册资本8000万元，法人张建国，成立2016-03-15，深圳南山。股东：深圳顺科投资有限公司（持股60%），张建国（持股25%），王芳（持股15%）。",
                "source_type": "commercial_platform",
                "date": "2024-10-18"
            },
        ]

    # Shareholder info
    if "股东" in query or "持股" in query or "股权" in query:
        results += [
            {
                "title": "顺达物流科技有限公司股权结构 - 企查查",
                "url": "http://www.qichacha.com/shunda_equity",
                "snippet": "股东信息：深圳顺科投资有限公司持股60%，张建国持股25%，王芳持股15%。深圳顺科投资有限公司由顺科控股集团有限公司100%持股（香港注册，公开信息有限）。",
                "source_type": "commercial_platform",
                "date": "2024-10-20"
            },
            {
                "title": "顺达物流科技变更记录 - 工商公示",
                "url": "http://www.gsxt.gov.cn/corp-query-change.html?id=shundawl001",
                "snippet": "2021-08-10：注册资本由5000万变更为8000万元；2020-03-05：法定代表人由陈志远变更为张建国；2019-11-20：新增股东王芳，持股15%，同步调整原股东比例。",
                "source_type": "government",
                "date": "2024-11-01"
            },
        ]

    # Judicial risks
    if "裁判文书" in query or "被执行" in query or "失信" in query or "司法" in query or "开庭" in query:
        results += [
            {
                "title": "中国裁判文书网 - (2023)粤03民终4412号",
                "url": "http://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html?docId=4412",
                "snippet": "（2023）粤03民终4412号，案由：买卖合同纠纷，原告：深圳华贸供应链有限公司，被告：顺达物流科技有限公司，争议金额：328万元，判决结果：被告败诉，需偿还货款328万元及利息，判决日期2023-09-15。",
                "source_type": "government",
                "date": "2023-09-15"
            },
            {
                "title": "被执行人信息 - 深圳中院",
                "url": "http://zxgk.court.gov.cn/zhzxgk/?pName=%E9%A1%BA%E8%BE%BE%E7%89%A9%E6%B5%81",
                "snippet": "顺达物流科技有限公司，执行案号：(2023)粤03执1908号，执行标的：328万元，申请执行人：深圳华贸供应链有限公司，状态：已结案（2024-02-20履行完毕）。",
                "source_type": "government",
                "date": "2024-02-20"
            },
            {
                "title": "顺达物流被起诉 货款纠纷引发关注 - 物流行业观察",
                "url": "http://www.logisticsnews.cn/article/20230920",
                "snippet": "业内人士透露，顺达物流科技2023年因货款纠纷在深圳被起诉，涉案金额超300万，该案已于2024年初执行完毕。",
                "source_type": "media",
                "date": "2023-09-20"
            },
        ]

    # Administrative penalties
    if "行政处罚" in query or "经营异常" in query or "违法" in query or "监管" in query:
        results += [
            {
                "title": "深圳市交通运输局行政处罚公告 - 2022年第18期",
                "url": "http://jtys.sz.gov.cn/xxgk/tzgg/cfjd/202212/t20221215_29874.htm",
                "snippet": "处罚对象：顺达物流科技有限公司；违法事实：超载运输，违反《道路运输条例》第35条；处罚决定：罚款3万元；处罚日期：2022-12-10；主管机关：深圳市交通运输局。",
                "source_type": "government",
                "date": "2022-12-15"
            },
            {
                "title": "顺达物流经营异常 - 知乎专栏",
                "url": "http://zhuanlan.zhihu.com/p/shunda_risk_2023",
                "snippet": "有网友反映顺达物流科技2023年曾短暂出现经营异常，但官方公示系统目前未检索到相关记录。仅凭该帖子难以核实。",
                "source_type": "forum",
                "date": "2023-05-10"
            },
        ]

    # Financing
    if "融资" in query or "投资方" in query or "A轮" in query or "估值" in query:
        results += [
            {
                "title": "顺达物流科技完成A轮融资 - 36氪",
                "url": "http://www.36kr.com/p/shunda_series_a_2020",
                "snippet": "顺达物流科技有限公司于2020年6月完成A轮融资，金额1.5亿元，由启明创投领投，险峰长青跟投。公司估值约8亿元，本轮资金将用于技术研发和全国仓网建设。",
                "source_type": "media",
                "date": "2020-06-15"
            },
            {
                "title": "顺达物流科技A轮融资公告 - 公司官网",
                "url": "http://www.shunda-logistics.com.cn/news/2020/seriesA",
                "snippet": "本公司正式宣布完成1.5亿元人民币A轮融资，领投方为启明创投，跟投方为险峰长青，感谢投资方对我们智慧物流战略的认可。",
                "source_type": "official_website",
                "date": "2020-06-18"
            },
        ]

    # IP
    if "商标" in query or "专利" in query or "软件著作权" in query or "知识产权" in query:
        results += [
            {
                "title": "顺达物流科技商标注册信息 - 中国商标网",
                "url": "http://wsjs.saic.gov.cn/trademark/shunda",
                "snippet": "顺达物流科技有限公司已注册商标：'顺达智运'（第39类，运输物流），注册号：62341XXX，状态：有效；'SHUNDA LOGISTICS'（第42类，软件服务），注册号：62342XXX，状态：有效。",
                "source_type": "government",
                "date": "2024-09-01"
            },
            {
                "title": "顺达物流专利查询 - 国家知识产权局",
                "url": "http://pss-system.cnipa.gov.cn/sipopublicsearch/shunda",
                "snippet": "顺达物流科技有限公司共申请专利18项，其中发明专利6项（授权4项），实用新型12项。代表专利：'一种基于AI的动态路由优化方法'（发明，ZL202210XXXXX.X）。",
                "source_type": "government",
                "date": "2024-08-15"
            },
        ]

    # Recruitment
    if "招聘" in query or "岗位" in query or "薪资" in query or "技术栈" in query:
        results += [
            {
                "title": "顺达物流科技招聘 - BOSS直聘",
                "url": "http://www.zhipin.com/gongsi/shunda",
                "snippet": "顺达物流科技深圳总部在招岗位：Java后端工程师（20-35K）、算法工程师-路由优化（30-50K）、供应链产品经理（20-30K）、BD经理-物流行业（15-25K）。技术栈：Java/Spring Boot, Python, Kubernetes, Flink。",
                "source_type": "commercial_platform",
                "date": "2024-11-05"
            },
        ]

    # Bidding
    if "中标" in query or "招投标" in query or "政府采购" in query:
        results += [
            {
                "title": "深圳市政府采购中心 - 中标公告",
                "url": "http://zfcg.sz.gov.cn/notice/20230815_shunda",
                "snippet": "采购项目：深圳市智慧物流平台建设项目，中标单位：顺达物流科技有限公司，中标金额：1280万元，采购方：深圳市商务局，合同签署日期：2023-08-15。",
                "source_type": "government",
                "date": "2023-08-15"
            },
        ]

    # Subsidiaries
    if "子公司" in query or "对外投资" in query or "分公司" in query or "关联" in query:
        results += [
            {
                "title": "顺达物流科技对外投资信息 - 企查查",
                "url": "http://www.qichacha.com/shunda_invest",
                "snippet": "顺达物流科技有限公司对外投资：1）上海顺达供应链科技有限公司（持股100%，成立2018-05）；2）成都顺达仓储有限公司（持股70%，成立2019-03）；3）北京顺达智运信息技术有限公司（持股51%，成立2020-11）。",
                "source_type": "commercial_platform",
                "date": "2024-10-18"
            },
        ]

    # News/sentiment
    if "新闻" in query or "舆情" in query or "负面" in query or "投诉" in query or "动态" in query:
        results += [
            {
                "title": "顺达物流科技荣获2024年度深圳物流科技创新奖 - 深圳商报",
                "url": "http://www.sznews.com/industry/2024/0318_shunda",
                "snippet": "2024年3月，顺达物流科技有限公司荣获深圳市物流协会颁发的'2024年度物流科技创新奖'，表彰其在智慧物流算法领域的突出贡献。",
                "source_type": "media",
                "date": "2024-03-18"
            },
            {
                "title": "用户投诉顺达物流货物延误 - 黑猫投诉平台",
                "url": "http://tousu.sina.com.cn/complaint/shunda_delay_2024",
                "snippet": "2024年Q1，黑猫投诉平台收到顺达物流科技相关投诉12条，主要反映货物延误和客服响应慢，公司均已回复处理。",
                "source_type": "forum",
                "date": "2024-04-01"
            },
        ]

    # Competition
    if "竞争" in query or "竞品" in query or "行业" in query or "市场份额" in query:
        results += [
            {
                "title": "2024年智慧物流行业分析报告 - 中国物流与采购联合会",
                "url": "http://www.chinawuliu.com.cn/report/2024_smart_logistics",
                "snippet": "国内智慧物流科技赛道主要玩家：顺丰科技、菜鸟网络、京东物流技术、顺达物流科技（深圳）、壹米滴答等。顺达物流科技在WMS/TMS中间件市场具有一定竞争优势，以中型制造企业为主要客户群。",
                "source_type": "industry_association",
                "date": "2024-06-20"
            },
        ]

    if not results:
        results = [
            {
                "title": f"搜索 '{query}' 暂无结果",
                "url": "",
                "snippet": "未检索到相关信息，可能需要付费数据库或内部渠道。",
                "source_type": "none",
                "date": "2024-11-10"
            }
        ]

    return results

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "Usage: kimi_search <query>"}))
        sys.exit(1)
    
    query = args[0]
    # handle --limit flag
    limit = 10
    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 < len(args):
            try:
                limit = int(args[idx + 1])
            except:
                pass
    
    results = search(query)[:limit]
    print(json.dumps({"query": query, "results": results}, ensure_ascii=False, indent=2))
'''

# --- Mock kimi_fetch tool ---
kimi_fetch_script = r'''#!/usr/bin/env python3
"""Mock kimi_fetch CLI tool. Usage: kimi_fetch "<url>" """
import sys
import json

PAGES = {
    "http://www.gsxt.gov.cn/corp-query-entprise-info-100.html?id=shundawl001": """
【国家企业信用信息公示系统 - 企业详情】
企业名称：顺达物流科技有限公司
统一社会信用代码：91440300MA5FXXXXX8
类型：有限责任公司（自然人投资或控股）
法定代表人：张建国
注册资本：8000万元人民币
实缴资本：未公示
成立日期：2016年03月15日
核准日期：2024-06-12
登记状态：存续（在营）
登记机关：深圳市市场监督管理局
注册地址：广东省深圳市南山区科技园南区高新南一道XX号XX楼
经营范围：物流信息技术服务；仓储服务（不含危险化学品）；道路货物运输代理；供应链管理服务；软件开发；数据处理和存储服务。（依法须经批准的项目，经相关部门批准后方可开展经营活动。）
""",
    "http://wenshu.court.gov.cn/website/wenshu/181107ANFZ0BXSK4/index.html?docId=4412": """
【中国裁判文书网】
案号：（2023）粤03民终4412号
案由：买卖合同纠纷
审理法院：深圳市中级人民法院
裁判日期：2023-09-15
原告：深圳华贸供应链有限公司
被告：顺达物流科技有限公司
案件摘要：原告诉称被告未按合同约定支付货款，请求判令被告支付货款328万元及逾期利息。法院审理认定被告违约，判令被告于判决生效之日起10日内支付原告货款328万元及以同期LPR为标准计算的逾期利息（自2022-11-01起至实际清偿之日止）。
判决结果：被告败诉，全额支付货款及利息。
执行情况：(2023)粤03执1908号，已于2024-02-20履行完毕。
""",
    "http://www.shunda-logistics.com.cn/news/2020/seriesA": """
【顺达物流科技官网公告】
标题：顺达物流科技完成1.5亿元A轮融资
发布时间：2020-06-18
内容：顺达物流科技有限公司宣布完成1.5亿元人民币A轮融资，本轮融资由启明创投领投，险峰长青跟投。融资资金将主要用于：1）核心算法研发投入；2）全国仓储网络布局；3）人才团队扩张。公司成立以来已服务超过500家中型制造企业，WMS产品在华南市场占据领先地位。
""",
    "http://jtys.sz.gov.cn/xxgk/tzgg/cfjd/202212/t20221215_29874.htm": """
【深圳市交通运输局行政处罚公告】
序号：2022年第18期-007
处罚对象：顺达物流科技有限公司
统一社会信用代码：91440300MA5FXXXXX8
违法事实：2022年10月经检查发现，当事人使用超载车辆从事道路货物运输，违反《道路运输条例》第三十五条之规定。
处罚决定：责令改正，并处罚款人民币叁万元整（30,000元）。
作出处罚决定的机关：深圳市交通运输局
作出处罚决定的日期：2022年12月10日
""",
}

DEFAULT = """【页面内容】
该页面内容未在本地缓存中，可能需要实时抓取或该页面已失效。
提示：实缴资本、历史变更全量、司法全量数据可能需要付费数据库。
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: kimi_fetch <url>"}))
        sys.exit(1)
    
    url = sys.argv[1]
    content = PAGES.get(url, DEFAULT)
    
    print(json.dumps({
        "url": url,
        "fetch_date": "2024-11-10",
        "content": content
    }, ensure_ascii=False, indent=2))
'''

# Write mock tools
tools_path = Path("/workspace/tools")

(tools_path / "kimi_search").write_text(kimi_search_script, encoding="utf-8")
(tools_path / "kimi_fetch").write_text(kimi_fetch_script, encoding="utf-8")

# Make executable
os.chmod(tools_path / "kimi_search", 0o755)
os.chmod(tools_path / "kimi_fetch", 0o755)

# --- Task brief (business context, not revealing format details) ---
task_brief = """# Company Due Diligence Task

## Background
Our investment team needs a comprehensive research report on a Chinese logistics technology company.
The company operates under the brand "顺达物流" — but we're not sure which exact legal entity to analyze.

## Your Objective
Research and produce a structured company report saved as: `company_research_report.md`

The report should cover the company's background, key executives, shareholders, subsidiaries,
funding history, legal/judicial risks, regulatory penalties, intellectual property, government contracts,
hiring trends, recent news, and competitive position.

Place the report file anywhere inside the /workspace directory.

## Available Tools
You have access to two research tools in `/workspace/tools/`:
- `kimi_search` — multi-source search tool (usage: `kimi_search "<query>"`)
- `kimi_fetch` — deep page fetcher for full content (usage: `kimi_fetch "<url>"`)

Use these tools to gather information across all relevant dimensions before writing the report.
"""

Path("/workspace/task_brief.md").write_text(task_brief, encoding="utf-8")

# More distractor files
Path("/workspace/data/raw_search/.gitkeep").write_text("")
Path("/workspace/data/raw_fetch/.gitkeep").write_text("")
Path("/workspace/reports/.gitkeep").write_text("")

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(Path("/workspace").rglob("*")):
    if f.is_file():
        print(f"  {f}")