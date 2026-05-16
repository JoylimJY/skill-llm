#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the sandbox workspace for the investment post-management report task.
"""
import os
import json
import random
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Replicate the skill's project directory structure ──────────────────────
skill_root = WORKSPACE / "projects" / "investment-post-management-report-updater"
scripts_dir = skill_root / "scripts"
references_dir = skill_root / "references"
for d in [scripts_dir, references_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Write the four referenced scripts/docs (as per SKILL.md) ──────────────
# scripts/parse_financial_data.py
parse_financial_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import sys
from typing import Dict, Any
import openpyxl
from datetime import datetime


def parse_financial_statement(file_path: str) -> Dict[str, Any]:
    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        result = {
            'file_name': file_path.split('/')[-1],
            'parse_time': datetime.now().isoformat(),
            'sheets': {},
            'summary': {}
        }
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            sheet_data = []
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    sheet_data.append([str(cell) if cell is not None else \'\' for cell in row])
            result[\'sheets\'][sheet_name] = sheet_data
        result[\'summary\'] = extract_key_metrics(result)
        return result
    except Exception as e:
        return {\'error\': f\'解析失败: {str(e)}\', \'file_path\': file_path}


def extract_key_metrics(data: Dict[str, Any]) -> Dict[str, Any]:
    metrics = {
        \'revenue\': None,
        \'gross_profit\': None,
        \'net_profit\': None,
        \'total_assets\': None,
        \'total_liabilities\': None,
        \'cash_flow\': None,
        \'detected_tables\': []
    }
    for sheet_name, sheet_data in data[\'sheets\'].items():
        for row_idx, row in enumerate(sheet_data):
            row_text = \' \'.join(row).lower()
            if any(keyword in row_text for keyword in [\'营业收入\', \'总收入\', \'收入\', \'revenue\']):
                if len(row) > 1 and row[1]:
                    try:
                        metrics[\'revenue\'] = float(row[1])
                    except (ValueError, IndexError):
                        pass
            if any(keyword in row_text for keyword in [\'净利润\', \'net profit\']):
                if len(row) > 1 and row[1]:
                    try:
                        metrics[\'net_profit\'] = float(row[1])
                    except (ValueError, IndexError):
                        pass
            if any(keyword in row_text for keyword in [\'资产总计\', \'总资产\', \'total assets\']):
                if len(row) > 1 and row[1]:
                    try:
                        metrics[\'total_assets\'] = float(row[1])
                    except (ValueError, IndexError):
                        pass
            if any(keyword in row_text for keyword in [\'负债合计\', \'总负债\', \'total liabilities\']):
                if len(row) > 1 and row[1]:
                    try:
                        metrics[\'total_liabilities\'] = float(row[1])
                    except (ValueError, IndexError):
                        pass
    metrics[\'detected_tables\'] = list(data[\'sheets\'].keys())
    return metrics


def main():
    parser = argparse.ArgumentParser(description=\'解析财务报表文件\')
    parser.add_argument(\'--file\', required=True, help=\'财务报表文件路径\')
    parser.add_argument(\'--output\', help=\'输出JSON文件路径\')
    args = parser.parse_args()
    result = parse_financial_statement(args.file)
    if \'error\' in result:
        print(json.dumps({\'error\': result[\'error\']}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, \'w\', encoding=\'utf-8\') as f:
            f.write(output_json)
        print(f\'结果已保存到: {args.output}\')
    else:
        print(output_json)


if __name__ == \'__main__\':
    main()
'''
(scripts_dir / "parse_financial_data.py").write_text(parse_financial_script, encoding="utf-8")

# scripts/parse_docx.py
parse_docx_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import sys
from typing import Dict, Any, List
from docx import Document
from datetime import datetime


def parse_docx_file(file_path: str) -> Dict[str, Any]:
    try:
        doc = Document(file_path)
        result = {
            \'file_name\': file_path.split(\'/\')[-1],
            \'parse_time\': datetime.now().isoformat(),
            \'paragraphs\': [],
            \'tables\': [],
            \'styles\': {},
            \'structure\': {
                \'total_paragraphs\': 0,
                \'total_tables\': 0,
                \'heading_levels\': {}
            }
        }
        for idx, para in enumerate(doc.paragraphs):
            para_info = {
                \'index\': idx,
                \'text\': para.text.strip(),
                \'style\': para.style.name if para.style else \'Normal\',
                \'level\': None
            }
            if para.style and para.style.name.startswith(\'Heading\'):
                try:
                    para_info[\'level\'] = int(para.style.name.split()[-1])
                except (ValueError, IndexError):
                    pass
            if para_info[\'text\']:
                result[\'paragraphs\'].append(para_info)
                if para_info[\'level\']:
                    level_key = f"Level_{para_info[\'level\']}"
                    result[\'structure\'][\'heading_levels\'][level_key] = result[\'structure\'][\'heading_levels\'].get(level_key, 0) + 1
        for table_idx, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                if any(row_data):
                    table_data.append(row_data)
            if table_data:
                result[\'tables\'].append({\'index\': table_idx, \'data\': table_data, \'rows\': len(table_data), \'cols\': len(table_data[0]) if table_data else 0})
        result[\'structure\'][\'total_paragraphs\'] = len(result[\'paragraphs\'])
        result[\'structure\'][\'total_tables\'] = len(result[\'tables\'])
        return result
    except Exception as e:
        return {\'error\': f\'解析失败: {str(e)}\', \'file_path\': file_path}


def get_full_text(data: Dict[str, Any]) -> str:
    paragraphs = [para[\'text\'] for para in data[\'paragraphs\']]
    return \'\\n\\n\'.join(paragraphs)


def main():
    parser = argparse.ArgumentParser(description=\'解析 DOCX 文件\')
    parser.add_argument(\'--file\', required=True, help=\'DOCX 文件路径\')
    parser.add_argument(\'--output\', help=\'输出JSON文件路径\')
    parser.add_argument(\'--text-only\', action=\'store_true\', help=\'仅输出纯文本内容\')
    args = parser.parse_args()
    result = parse_docx_file(args.file)
    if \'error\' in result:
        print(json.dumps({\'error\': result[\'error\']}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    if args.text_only:
        full_text = get_full_text(result)
        if args.output:
            with open(args.output, \'w\', encoding=\'utf-8\') as f:
                f.write(full_text)
            print(f\'纯文本已保存到: {args.output}\')
        else:
            print(full_text)
    else:
        output_json = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, \'w\', encoding=\'utf-8\') as f:
                f.write(output_json)
            print(f\'结果已保存到: {args.output}\')
        else:
            print(output_json)


if __name__ == \'__main__\':
    main()
'''
(scripts_dir / "parse_docx.py").write_text(parse_docx_script, encoding="utf-8")

# scripts/generate_report.py
generate_report_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import sys
import os
from typing import Dict, Any
from docx import Document
from docx.shared import Pt
from datetime import datetime


def generate_report(template_path, financial_data, financial_analysis, business_update, industry_update, output_path):
    try:
        doc = Document(template_path)
        if isinstance(financial_data, str):
            financial_data = json.loads(financial_data)
        updated_sections = set()
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip().lower()
            if \'财务数据\' in text or \'财务概况\' in text or \'财务指标\' in text:
                if \'financial\' not in updated_sections:
                    if financial_analysis:
                        new_para = para.insert_paragraph_before(financial_analysis)
                        new_para.style = para.style
                    updated_sections.add(\'financial\')
            elif \'经营情况\' in text or \'公司经营\' in text or \'业务进展\' in text:
                if \'business\' not in updated_sections:
                    if business_update:
                        if i + 1 < len(doc.paragraphs):
                            next_para = doc.paragraphs[i + 1]
                            if not next_para.style.name.startswith(\'Heading\'):
                                next_para.text = business_update
                    updated_sections.add(\'business\')
            elif \'行业\' in text or \'竞争格局\' in text or \'市场环境\' in text:
                if \'industry\' not in updated_sections:
                    if industry_update:
                        if i + 1 < len(doc.paragraphs):
                            next_para = doc.paragraphs[i + 1]
                            if not next_para.style.name.startswith(\'Heading\'):
                                next_para.text = industry_update
                    updated_sections.add(\'industry\')
        timestamp = datetime.now().strftime(\'%Y年%m月%d日\')
        timestamp_para = doc.paragraphs[0].insert_paragraph_before(f\'报告更新时间：{timestamp}\')
        timestamp_para.style = doc.styles[\'Normal\']
        doc.save(output_path)
        return True
    except Exception as e:
        print(f\'生成报告失败: {str(e)}\', file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description=\'生成投后管理报告\')
    parser.add_argument(\'--template\', required=True)
    parser.add_argument(\'--financial-data\', required=True)
    parser.add_argument(\'--financial-analysis\', required=True)
    parser.add_argument(\'--business-update\', required=True)
    parser.add_argument(\'--industry-update\', required=True)
    parser.add_argument(\'--output\', required=True)
    args = parser.parse_args()
    financial_data = args.financial_data
    if os.path.isfile(args.financial_data):
        with open(args.financial_data, \'r\', encoding=\'utf-8\') as f:
            financial_data = f.read()
    success = generate_report(
        template_path=args.template,
        financial_data=financial_data,
        financial_analysis=args.financial_analysis,
        business_update=args.business_update,
        industry_update=args.industry_update,
        output_path=args.output
    )
    if success:
        print(f\'报告已成功生成: {args.output}\')
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == \'__main__\':
    main()
'''
(scripts_dir / "generate_report.py").write_text(generate_report_script, encoding="utf-8")

# references/report-structure.md
(references_dir / "report-structure.md").write_text("""# 投后管理报告结构

## 目录
1. 报告概述
2. 财务情况分析
3. 公司经营情况
4. 行业情况分析
5. 风险提示
6. 投资建议

## 报告结构

### 1. 报告概述
内容要求：报告期间、核心财务指标摘要、重大经营事件、关键结论预览

### 2. 财务情况分析

#### 2.1 财务数据
核心指标：营业收入及增长率、毛利润及毛利率、净利润及净利率、现金流状况、资产负债结构

#### 2.2 财务分析
分析维度：同比分析、环比分析、预算达成率、趋势分析

### 3. 公司经营情况

#### 3.1 业务进展
#### 3.2 团队与组织
#### 3.3 重大事件

### 4. 行业情况分析

#### 4.1 行业发展趋势
#### 4.2 竞争格局
#### 4.3 行业风险

### 5. 风险提示
### 6. 投资建议
""", encoding="utf-8")

# references/financial-analysis-guide.md
(references_dir / "financial-analysis-guide.md").write_text("""# 财务分析指南

## 关键财务指标

### 盈利能力指标

#### 营业收入
收入增长率 = (本期收入 - 上期收入) / 上期收入 × 100%

#### 毛利润与毛利率
毛利润 = 营业收入 - 营业成本
毛利率 = 毛利润 / 营业收入 × 100%

#### 净利润与净利率
净利率 = 净利润 / 营业收入 × 100%

### 营运效率指标

#### 应收账款周转率
应收账款周转率 = 营业收入 / 平均应收账款
应收账款周转天数 = 365 / 应收账款周转率

### 财务稳健性指标

#### 资产负债率
资产负债率 = 总负债 / 总资产 × 100%

### 分析方法

同比增长率 = (本期收入 - 去年同期收入) / 去年同期收入 × 100%
环比增长率 = (本期收入 - 上季度收入) / 上季度收入 × 100%
""", encoding="utf-8")

# references/content-update-template.md
(references_dir / "content-update-template.md").write_text("""# 内容更新模板

## 财务分析更新模板

本季度财务指标如下：
- 营业收入：XX万元，同比增长XX%，环比增长XX%
- 毛利润：XX万元，毛利率XX%
- 净利润：XX万元，净利率XX%
- 经营现金流：XX万元
- 总资产：XX万元，总负债：XX万元

## 经营情况更新模板

本季度公司业务进展如下：
核心业务发展：[业务线1]、[业务线2]
产品/服务更新：[更新内容]
客户拓展：[进展描述]

## 行业分析更新模板

本季度行业发展趋势：
市场规模：整体市场规模XX亿元
增长驱动因素：[驱动因素1]、[驱动因素2]
竞争格局：[主要动态]
政策环境：[政策影响]
""", encoding="utf-8")

# ── 3. Create the TASK INPUT FILES ────────────────────────────────────────────

task_input_dir = WORKSPACE / "task_inputs"
task_input_dir.mkdir(parents=True, exist_ok=True)

# ── 3a. Q4 2024 Financial Statement (XLSX) ────────────────────────────────────
wb = openpyxl.Workbook()

# Sheet 1: 利润表 (Income Statement)
ws1 = wb.active
ws1.title = "利润表"
ws1.append(["云启科技有限公司", "2024年第四季度利润表", "", ""])
ws1.append(["项目", "2024Q4（万元）", "2024Q3（万元）", "2023Q4（万元）"])
ws1.append(["营业收入", "6800", "5950", "5200"])
ws1.append(["营业成本", "3400", "3094", "2860"])
ws1.append(["毛利润", "3400", "2856", "2340"])
ws1.append(["销售费用", "680", "595", "520"])
ws1.append(["管理费用", "408", "357", "312"])
ws1.append(["研发费用", "952", "833", "728"])
ws1.append(["财务费用", "34", "30", "26"])
ws1.append(["营业利润", "1326", "1041", "754"])
ws1.append(["净利润", "1193.4", "936.9", "678.6"])

# Sheet 2: 资产负债表 (Balance Sheet)
ws2 = wb.create_sheet("资产负债表")
ws2.append(["云启科技有限公司", "2024年第四季度资产负债表", "", ""])
ws2.append(["项目", "2024Q4末（万元）", "2024Q3末（万元）", ""])
ws2.append(["流动资产", "", "", ""])
ws2.append(["货币资金", "8500", "7200", ""])
ws2.append(["应收账款", "2040", "1785", ""])
ws2.append(["存货", "510", "476", ""])
ws2.append(["其他流动资产", "340", "297", ""])
ws2.append(["流动资产合计", "11390", "9758", ""])
ws2.append(["非流动资产", "", "", ""])
ws2.append(["固定资产", "1020", "1071", ""])
ws2.append(["无形资产", "680", "714", ""])
ws2.append(["非流动资产合计", "1700", "1785", ""])
ws2.append(["资产总计", "13090", "11543", ""])
ws2.append(["流动负债", "", "", ""])
ws2.append(["应付账款", "1360", "1190", ""])
ws2.append(["其他流动负债", "680", "595", ""])
ws2.append(["流动负债合计", "2040", "1785", ""])
ws2.append(["非流动负债", "654.5", "577.15", ""])
ws2.append(["负债合计", "2694.5", "2362.15", ""])
ws2.append(["股东权益合计", "10395.5", "9180.85", ""])

# Sheet 3: 现金流量表 (Cash Flow Statement)
ws3 = wb.create_sheet("现金流量表")
ws3.append(["云启科技有限公司", "2024年第四季度现金流量表", "", ""])
ws3.append(["项目", "2024Q4（万元）", "2024Q3（万元）", ""])
ws3.append(["经营活动现金流入", "7140", "6248", ""])
ws3.append(["经营活动现金流出", "5440", "4726", ""])
ws3.append(["经营活动产生的现金流量净额", "1700", "1522", ""])
ws3.append(["投资活动现金流入", "0", "0", ""])
ws3.append(["投资活动现金流出", "340", "297", ""])
ws3.append(["投资活动产生的现金流量净额", "-340", "-297", ""])
ws3.append(["筹资活动现金流量净额", "0", "0", ""])
ws3.append(["现金及现金等价物净增加额", "1360", "1225", ""])

financial_path = task_input_dir / "云启科技2024Q4财务报表.xlsx"
wb.save(str(financial_path))

# ── 3b. Interview Transcript (DOCX) ──────────────────────────────────────────
doc_interview = Document()
doc_interview.add_heading("云启科技2024Q4访谈纪要", 0)
doc_interview.add_paragraph("访谈时间：2025年1月15日")
doc_interview.add_paragraph("访谈对象：云启科技CEO 张明远、CFO 李晓华")
doc_interview.add_paragraph("访谈人：某投资机构投后团队")

doc_interview.add_heading("一、业务进展", 1)
doc_interview.add_paragraph(
    "张明远表示，2024年第四季度公司核心SaaS业务增长强劲，企业客户数量从上季度的320家增至385家，"
    "新签年合同价值（ACV）达到1200万元，较上季度增长约22%。大客户（年合同额超50万元）占比提升至35%，"
    "较上季度的28%有明显改善。公司重点推进的政务云产品在本季度完成了3个省级客户落地，"
    "合同金额合计约480万元。"
)

doc_interview.add_heading("二、产品与技术更新", 1)
doc_interview.add_paragraph(
    "研发团队本季度完成了v3.2版本发布，核心亮点包括：AI辅助工单分析功能上线，"
    "将平均处理时长缩短40%；多租户架构优化使系统并发处理能力提升60%；"
    "新增与主流ERP系统（SAP、用友、金蝶）的原生集成接口。"
    "目前研发团队规模为58人，本季度新增招聘高级算法工程师5名。"
)

doc_interview.add_heading("三、团队与组织", 1)
doc_interview.add_paragraph(
    "公司本季度完成组织架构调整，新设立'行业解决方案中心'，下设政务、制造、金融三个垂直行业组。"
    "截至2024年底，公司总员工数为186人（上季度为172人），净增14人。"
    "销售总监王刚于11月加入，此前在某头部云服务商担任大客户销售负责人，具有丰富的政务云销售经验。"
)

doc_interview.add_heading("四、重大事件", 1)
doc_interview.add_paragraph(
    "公司于2024年12月与某省级国有企业签署战略合作协议，对方将成为公司政务云产品的渠道合作伙伴，"
    "覆盖该省100余个地级市及县级单位的潜在客户。预计该渠道在2025年带来不低于2000万元的合同收入。"
    "此外，公司完成B轮融资收尾工作，总金额5000万元，本季度到账3000万元。"
)

doc_interview.add_heading("五、行业与竞争", 1)
doc_interview.add_paragraph(
    "李晓华介绍，企业数字化管理SaaS市场2024年整体规模约580亿元，同比增长约18%。"
    "头部厂商竞争加剧，某竞争对手在本季度推出低价策略，将中小客户版本定价下调30%，"
    "但对公司大客户策略影响有限，目前公司在政务垂直领域市场份额约7%，排名第三。"
    "国家数字政府建设相关政策持续推进，工信部发布《企业数字化转型指引》，"
    "为政务SaaS市场带来明确政策支撑。"
)

interview_path = task_input_dir / "云启科技2024Q4访谈纪要.docx"
doc_interview.save(str(interview_path))

# ── 3c. Q3 2024 Previous Report (DOCX) ───────────────────────────────────────
doc_prev = Document()
doc_prev.add_heading("云启科技有限公司", 0)
doc_prev.add_heading("2024年第三季度投后管理报告", 0)
doc_prev.add_paragraph("报告日期：2024年10月20日")
doc_prev.add_paragraph("报告单位：某投资机构投后管理部")

# Section 1
doc_prev.add_heading("一、报告概述", 1)
doc_prev.add_paragraph(
    "本报告覆盖2024年第三季度（2024年7月1日至9月30日）云启科技有限公司的经营情况。"
    "公司本季度营业收入5950万元，净利润936.9万元，整体运营稳健，符合预期。"
)

# Section 2 - Financial (with trigger keyword '财务数据')
doc_prev.add_heading("二、财务情况分析", 1)
doc_prev.add_heading("2.1 财务数据", 2)
doc_prev.add_paragraph(
    "2024Q3核心财务数据：营业收入5950万元，同比增长24.0%，环比增长9.2%；"
    "毛利润2856万元，毛利率48.0%；净利润936.9万元，净利率15.7%；"
    "经营现金流1522万元；总资产11543万元，总负债2362.15万元，资产负债率20.5%。"
)
doc_prev.add_heading("2.2 财务分析", 2)
doc_prev.add_paragraph(
    "本季度收入增长主要来自企业客户数量增加及大客户ACV提升。"
    "毛利率较上季度提升约1个百分点，成本控制良好。"
    "经营现金流健康，现金流/净利润比率约1.62，利润质量较高。"
    "资产负债率维持在20%左右，财务风险较低。"
)

# Section 3 - Business (with trigger keyword '经营情况')
doc_prev.add_heading("三、公司经营情况", 1)
doc_prev.add_heading("3.1 业务进展", 2)
# The paragraph after this heading will be replaced by the agent
doc_prev.add_paragraph(
    "2024Q3公司核心SaaS业务持续增长，企业客户数量从上季度285家增至320家，"
    "新增政务云试点客户2个。研发团队完成v3.1版本迭代，新增批量导入功能。"
    "本季度客户留存率为94%，高于行业平均水平。"
)
doc_prev.add_heading("3.2 团队与组织", 2)
doc_prev.add_paragraph(
    "截至2024Q3末，公司总员工数172人，研发53人，销售48人，运营及管理71人。"
    "本季度新增招聘12人，无关键岗位离职。"
)
doc_prev.add_heading("3.3 重大事件", 2)
doc_prev.add_paragraph(
    "本季度完成一次小额战略投资，投资某上下游数据服务供应商，金额150万元，占股10%。"
    "无其他重大事件。"
)

# Section 4 - Industry (with trigger keyword '行业')
doc_prev.add_heading("四、行业情况分析", 1)
doc_prev.add_heading("4.1 行业发展趋势", 2)
# The paragraph after this heading will be replaced by the agent
doc_prev.add_paragraph(
    "2024Q3企业数字化管理SaaS市场整体规模约540亿元，同比增速约18%。"
    "政务数字化为主要增长引擎，头部厂商加速布局垂直行业。"
    "AI与SaaS融合成为重要趋势，多家厂商推出AI原生产品功能。"
)
doc_prev.add_heading("4.2 竞争格局", 2)
doc_prev.add_paragraph(
    "政务SaaS领域市场集中度逐步提升，头部三家厂商合计市场份额约35%。"
    "云启科技在政务垂直领域排名第三，市场份额约6%。"
    "竞争对手本季度均有新产品发布，价格竞争压力有所增加。"
)
doc_prev.add_heading("4.3 行业风险", 2)
doc_prev.add_paragraph(
    "主要风险包括：政策执行进度不确定性、头部厂商价格竞争加剧、"
    "AI技术快速迭代带来的产品替代风险。当前整体风险等级为中等。"
)

# Section 5
doc_prev.add_heading("五、风险提示", 1)
doc_prev.add_paragraph(
    "1. 财务风险：低，现金储备充足，无高息债务；\n"
    "2. 经营风险：中，大客户集中度有所上升，需关注续约情况；\n"
    "3. 行业风险：中，政策依赖度较高，需持续跟踪政策执行情况；\n"
    "4. 合规风险：低，无重大合规事项。"
)

# Section 6
doc_prev.add_heading("六、投资建议", 1)
doc_prev.add_paragraph(
    "建议继续持有。公司财务表现良好，收入增速保持高位，"
    "大客户战略推进顺利，政务云赛道景气度维持。"
    "建议重点关注B轮融资进展及政务云大客户落地情况。"
)

prev_report_path = task_input_dir / "云启科技2024Q3投后管理报告.docx"
doc_prev.save(str(prev_report_path))

# ── 4. Distractor files (to simulate real-world messy workspace) ──────────────
distractors_dir = WORKSPACE / "archive"
distractors_dir.mkdir(exist_ok=True)

# Old reports from other portfolio companies
for company, quarter in [("星河医疗", "2024Q2"), ("蓝图物流", "2024Q3"), ("峰值能源", "2024Q1")]:
    d = Document()
    d.add_heading(f"{company}{quarter}投后管理报告", 0)
    d.add_paragraph(f"这是{company}的历史报告，请勿使用。")
    d.save(str(distractors_dir / f"{company}{quarter}投后管理报告.docx"))

# Old financial data files
for company, quarter in [("星河医疗", "2024Q2"), ("蓝图物流", "2024Q3")]:
    wb2 = openpyxl.Workbook()
    ws = wb2.active
    ws.title = "利润表"
    ws.append(["项目", "金额（万元）"])
    ws.append(["营业收入", str(random.randint(1000, 8000))])
    ws.append(["净利润", str(random.randint(100, 1000))])
    wb2.save(str(distractors_dir / f"{company}{quarter}财务报表.xlsx"))

# Some raw notes and temp files
(distractors_dir / "meeting_notes_raw.txt").write_text(
    "临时会议记录，非正式文件，不得引用。\n数据仅供参考。", encoding="utf-8"
)
(distractors_dir / "TODO.txt").write_text(
    "待办事项：\n1. 整理2024年全年报告\n2. 更新估值模型\n3. 联系律师确认合规事项", encoding="utf-8"
)

# Valuation model spreadsheet (distractor)
wb3 = openpyxl.Workbook()
ws3 = wb3.active
ws3.title = "估值模型"
ws3.append(["估值方法", "PS倍数", "估值（万元）"])
ws3.append(["收入倍数法", "8x", "54400"])
wb3.save(str(distractors_dir / "云启科技估值模型_草稿.xlsx"))

# Template drafts
templates_dir = WORKSPACE / "templates"
templates_dir.mkdir(exist_ok=True)
for name in ["报告封面模板.docx", "财务分析表格模板.xlsx"]:
    if name.endswith(".docx"):
        d = Document()
        d.add_paragraph("模板文件，请勿直接使用。")
        d.save(str(templates_dir / name))
    else:
        wb4 = openpyxl.Workbook()
        wb4.active.title = "模板"
        wb4.active.append(["模板字段", "示例值"])
        wb4.save(str(templates_dir / name))

# Legal review subfolder
legal_dir = WORKSPACE / "legal_review"
legal_dir.mkdir(exist_ok=True)
(legal_dir / "合规检查清单_2024.txt").write_text(
    "合规检查项目：\n1. VIE架构合规性 ✓\n2. 数据安全合规 ✓\n3. 劳动法合规 进行中", encoding="utf-8"
)

# ── 5. Print summary ──────────────────────────────────────────────────────────
print("Workspace generated successfully.")
print(f"Task inputs created in: {task_input_dir}")
print(f"  - Financial statement: {financial_path.name}")
print(f"  - Interview transcript: {interview_path.name}")
print(f"  - Previous Q3 report: {prev_report_path.name}")
print(f"Skill scripts created in: {scripts_dir}")
print(f"Reference docs created in: {references_dir}")
print(f"Distractor files created in: {distractors_dir} and {templates_dir}")