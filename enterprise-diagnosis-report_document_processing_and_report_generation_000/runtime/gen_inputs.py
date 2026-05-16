#!/usr/bin/env python3
"""
Generate the initial sandbox workspace with three PDF reports and distractor files.
"""
import os
import random
import hashlib
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "output",
    "archive/2023/q1",
    "archive/2023/q2",
    "archive/2023/q3",
    "archive/2024/q1",
    "data/raw",
    "data/processed",
    "logs",
    "temp",
    "clients/shenzhen_mingyuan",
    "clients/shenzhen_mingyuan/contracts",
    "clients/shenzhen_mingyuan/invoices",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "archive/2023/q1/old_report_summary.txt": "旧版报告摘要，已归档，请勿使用。\n版本：v0.9\n状态：已废弃",
    "archive/2023/q2/financial_notes.txt": "财务备注：2023年Q2营收数据已更新，原始数据见附件。",
    "archive/2024/q1/policy_draft.txt": "政策草稿，待审核：高新技术企业认定条件修订意见。",
    "data/raw/company_list.csv": "企业名称,信用代码,行业\n明远科技,91440300MAALXXXXXX,软件\n远明科技,91440300MAALXXXXYY,信息服务",
    "data/processed/normalized_data.json": '{"status": "processed", "count": 42, "version": "2.1"}',
    "logs/parser_run_20240101.log": "[2024-01-01 09:00:00] PDF解析任务开始\n[2024-01-01 09:05:23] 解析完成，共3份文件\n[2024-01-01 09:05:24] 任务结束",
    "logs/parser_run_20240315.log": "[2024-03-15 14:22:11] 错误：文件路径无效\n[2024-03-15 14:22:12] 任务异常退出",
    "temp/working_notes.txt": "待办：核对应收账款数据；更新政策申报时间表",
    "clients/shenzhen_mingyuan/contracts/service_agreement_2024.txt": "服务协议编号：SVC-2024-001\n甲方：深圳明远科技有限公司\n乙方：某咨询公司\n服务内容：企业诊断咨询服务",
    "clients/shenzhen_mingyuan/invoices/invoice_20240301.txt": "发票号：INV-20240301\n金额：50,000.00元\n服务：企业诊断报告整合服务",
    "output/.gitkeep": "",
    "data/raw/raw_financials_backup.csv": "年份,营收,净利润\n2021,18500000,2100000\n2022,21000000,2800000\n2023,25000000,3500000",
}
for path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── pdf_parser.py script ─────────────────────────────────────────────────────
pdf_parser_content = r'''#!/usr/bin/env python3
"""
PDF解析脚本 - 用于提取企业诊断报告PDF中的文本内容
"""
import argparse
import sys
import os
from pathlib import Path

try:
    import fitz
except ImportError:
    print("错误：未安装PyMuPDF库，请执行: pip install PyMuPDF==1.23.26")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("错误：未安装requests库，请执行: pip install requests==2.31.0")
    sys.exit(1)


def download_pdf(url, save_path):
    try:
        print(f"正在下载PDF文件: {url[:50]}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"PDF文件已保存至: {save_path}")
        return save_path
    except requests.exceptions.RequestException as e:
        raise Exception(f"下载PDF失败: {str(e)}")


def extract_text_from_pdf(pdf_path):
    try:
        print(f"正在解析PDF文件: {pdf_path}")
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        text_content = []
        for page_num in range(page_count):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_content.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
        full_text = "\n\n".join(text_content)
        print(f"PDF解析完成，共 {page_count} 页，提取文本长度: {len(full_text)} 字符")
        doc.close()
        return full_text
    except Exception as e:
        raise Exception(f"解析PDF失败: {str(e)}")


def is_url(path):
    return path.startswith('http://') or path.startswith('https://')


def main():
    parser = argparse.ArgumentParser(description='PDF报告解析工具')
    parser.add_argument('--url', required=True, help='PDF文件的URL地址或本地文件路径')
    parser.add_argument('--output', default=None, help='提取内容的保存路径')
    args = parser.parse_args()

    try:
        if is_url(args.url):
            import hashlib
            temp_dir = "/tmp/pdf_downloads"
            os.makedirs(temp_dir, exist_ok=True)
            url_hash = hashlib.md5(args.url.encode()).hexdigest()[:12]
            filename = f"report_{url_hash}.pdf"
            pdf_path = os.path.join(temp_dir, filename)
            pdf_path = download_pdf(args.url, pdf_path)
        else:
            pdf_path = args.url
            if not os.path.exists(pdf_path):
                print(f"错误：文件不存在: {pdf_path}")
                sys.exit(1)

        text = extract_text_from_pdf(pdf_path)

        if args.output:
            os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"文本内容已保存至: {args.output}")
        else:
            print("\n" + "="*60)
            print("提取的文本内容：")
            print("="*60 + "\n")
            print(text)
        return 0
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
'''

with open(os.path.join(WORKSPACE, "scripts/pdf_parser.py"), "w", encoding="utf-8") as f:
    f.write(pdf_parser_content)

# ── report_template.md ───────────────────────────────────────────────────────
report_template_content = '''# 企业诊断综合报告模板

## 目录
1. [报告结构说明](#报告结构说明)
2. [企业基本信息板块](#企业基本信息板块)
3. [财税诊断板块](#财税诊断板块)
4. [政策匹配板块](#政策匹配板块)
5. [综合分析板块](#综合分析板块)
6. [格式规范](#格式规范)
7. [完整示例](#完整示例)

---

## 报告结构说明

企业诊断综合报告由五大板块组成，整合三份基础报告的核心信息：

```
企业诊断综合报告
├── 一、企业概况
│   ├── 基本信息摘要
│   ├── 股权结构
│   └── 经营状况概览
├── 二、财务健康度分析
│   ├── 核心财务指标
│   ├── 盈利能力分析
│   └── 风险提示
├── 三、税务合规性评估
│   ├── 税务状况概览
│   ├── 风险点识别
│   └── 优化建议
├── 四、政策红利与补贴机会
│   ├── 适用政策清单
│   ├── 补贴申请可行性
│   └── 申报时间规划
└── 五、综合诊断结论与建议
    ├── SWOT分析
    ├── 核心问题识别
    └── 改进建议优先级
```

---

## 格式规范

### 报告整体格式

```markdown
# [企业名称] 企业诊断综合报告

**报告生成日期**：YYYY-MM-DD
**报告基于材料**：
- 企业基本信息报告（生成日期：YYYY-MM-DD）
- 财税诊断报告（报告期间：YYYY年-YYYY年）
- 政策研究与补贴申请可行性报告（生成日期：YYYY-MM-DD）

---

## 一、企业概况

### 1.1 基本信息摘要

### 1.2 股权结构

### 1.3 经营状况概览

---

## 二、财务健康度分析

---

## 三、税务合规性评估

---

## 四、政策红利与补贴机会

---

## 五、综合诊断结论与建议

---

**免责声明**：本报告基于提供的材料进行分析，仅供参考，不构成投资或决策建议。
```

### 数字格式规范

- 金额：使用千分位分隔符，保留2位小数（如：1,234,567.89元）
- 百分比：保留2位小数（如：12.34%）
- 日期：统一使用 YYYY-MM-DD 格式

### 数据验证规则

1. **一致性检查**
   - 企业名称在三份报告中应完全一致
   - 统一社会信用代码格式：18位字母数字组合
   - 成立时间格式：YYYY-MM-DD

2. **完整性检查**
   - 标注"必填"项不得缺失
   - 缺失项用 `[缺失]` 标注

### 风险标注

- ⚠️ 高风险：可能涉及税务违规、重大财务异常
- ⚡ 中风险：需要优化改进的问题
- 💡 低风险：建议关注的事项

### 数据冲突处理

当三份报告中同一字段数据不一致时，必须生成差异对比表，格式如下：

| 字段名称 | 报告1数值 | 报告2数值 | 报告3数值 | 差异说明 |
|---------|---------|---------|---------|---------|
| [字段] | [值] | [值] | [值] | [说明] |

并在报告中标注"⚠️ 数据冲突，需用户确认"。
'''

with open(os.path.join(WORKSPACE, "references/report_template.md"), "w", encoding="utf-8") as f:
    f.write(report_template_content)

# ── Generate the three PDF reports ──────────────────────────────────────────
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import io

def create_pdf_with_text(filepath, pages_content):
    """Create a PDF with given text content per page."""
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    
    for page_text in pages_content:
        y = height - 40
        for line in page_text.split('\n'):
            if y < 40:
                c.showPage()
                y = height - 40
            # Use built-in font, encode as latin-1 fallback or write bytes
            try:
                c.drawString(30, y, line[:120])
            except Exception:
                c.drawString(30, y, line.encode('ascii', 'replace').decode('ascii')[:120])
            y -= 14
        c.showPage()
    c.save()


# Since reportlab has issues with Chinese in basic mode, use a different approach:
# Write PDFs with actual Chinese content using fitz (PyMuPDF) directly
import fitz

def create_pdf_fitz(filepath, title, pages_text_list):
    """Create PDF using PyMuPDF with text content."""
    doc = fitz.open()
    for page_text in pages_text_list:
        page = doc.new_page(width=595, height=842)
        lines = page_text.split('\n')
        y = 800
        for line in lines:
            if y < 40:
                break
            page.insert_text((30, y), line, fontsize=9, fontname="helv")
            y -= 13
    doc.save(filepath)
    doc.close()


# ── Report 1: 企业基本信息报告 ──────────────────────────────────────────────
# INTENTIONAL DATA: Company name "Shenzhen Mingyuan Tech" (深圳明远科技有限公司)
report1_pages = [
    """ENTERPRISE BASIC INFORMATION REPORT
Report Date: 2024-03-15
Report Type: Enterprise Basic Information

=== Basic Information ===
Enterprise Name: Shenzhen Mingyuan Technology Co., Ltd.
(深圳明远科技有限公司)
Unified Social Credit Code: 91440300MA5DXXXXYX
Establishment Date: 2019-06-20
Registered Capital: 5,000,000.00 Yuan
Paid-in Capital: 3,000,000.00 Yuan
Enterprise Type: Limited Liability Company (Natural Person Investment)
Operating Status: Active
Registered Address: Building 7, Keji South Road, Nanshan District, Shenzhen
Legal Representative: Li Ming (李明)
Operating Scope: Software development, data processing, IT consulting,
information system integration, big data services.

=== Shareholder Structure ===
Shareholder 1: Li Ming - 55% - Contributed Capital: 2,750,000.00 Yuan - Cash
Shareholder 2: Zhang Wei - 30% - Contributed Capital: 1,500,000.00 Yuan - Cash
Shareholder 3: Shenzhen Innovation Fund - 15% - 750,000.00 Yuan - Cash
Actual Controller: Li Ming (direct 55% stake)

=== Management Team ===
CEO: Li Ming
CTO: Wang Fang
CFO: Chen Jia
Core Technical Staff: 12 engineers, 3 data scientists

=== Operations Overview ===
Staff Size: 68 persons
Main Business: Enterprise digital transformation, big data platform development
Core Products: SmartData Analytics Platform, CloudOps Management System
Major Clients: Manufacturing enterprises in Guangdong, government agencies
Qualifications:
- High-tech Enterprise (Certified 2022)
- Specialized & Innovation Enterprise Candidate
- Software Enterprise Certification (2021)
""",
    """APPENDIX: FINANCIAL OVERVIEW (Brief)
Year 2023:
Revenue: 25,000,000.00 Yuan
Headcount Growth: +15 persons vs 2022
Branch Offices: 1 (Guangzhou liaison office)

No litigation records as of report date.
Report Generated: 2024-03-15
Validity: 90 days from generation date.
"""
]

# ── Report 2: 财税诊断报告 ──────────────────────────────────────────────────
# INTENTIONAL CONFLICT: Company name slightly different => "深圳明源科技有限公司" (Mingyuan vs Mingyuan typo)
report2_pages = [
    """FINANCIAL AND TAX DIAGNOSIS REPORT
Report Period: 2022-2023
Report Date: 2024-03-18

=== Enterprise Identification ===
Enterprise Name: Shenzhen Mingyuan Technology Co., Ltd.
(深圳明源科技有限公司)
Unified Social Credit Code: 91440300MA5DXXXXYX
Report Period: January 2022 - December 2023

NOTE: The enterprise name used internally differs slightly from registration
documents. Please verify: "明远" vs "明源" - requires client confirmation.

=== Core Financial Indicators (FY2023) ===
Revenue: 25,000,000.00 Yuan
Net Profit: 3,500,000.00 Yuan
Gross Profit Margin: 45.20%
Net Profit Margin: 14.00%
Asset-to-Liability Ratio: 38.50%
Current Ratio: 2.30
Quick Ratio: 1.85
Revenue Growth Rate: 25.00% (YoY)
Profit Growth Rate: 28.57% (YoY)

=== Tax Status ===
VAT Rate: 6% (general taxpayer)
VAT Tax Burden Rate: 2.85%
Corporate Income Tax Rate: 15% (High-tech enterprise preferential rate)
Corporate Income Tax: 727,272.73 Yuan (estimated)
Individual Income Tax (payroll): Compliant, monthly withholding
Stamp Duty: Normal
""",
    """=== Financial Risk Points ===
Risk Level: MEDIUM
Risk 1 (Medium): Accounts receivable turnover days = 92 days (above industry avg 60 days)
  - Current AR balance: 6,200,000.00 Yuan
  - Recommend: Strengthen credit management, target <60 days

Risk 2 (Low): Selling expense ratio = 15.20% of revenue
  - Total selling expenses: 3,800,000.00 Yuan
  - Recommend: Optimize marketing strategy

Risk 3 (Low): Quarterly cash flow volatility
  - Q1 net operating cash flow: 420,000.00 Yuan
  - Q3 net operating cash flow: 1,280,000.00 Yuan
  - Recommend: Establish cash reserve mechanism

=== Tax Optimization Suggestions ===
1. R&D expense super-deduction: Currently deducting 75%, can increase to 100%
   Estimated additional tax saving: 150,000.00 Yuan annually
2. Software VAT instant-rebate policy: Partially applied, optimize to maximize
3. High-tech enterprise re-certification due 2025: Prepare materials in advance

=== Audit Opinion ===
Overall financial health: GOOD
No major compliance issues identified.
Report prepared by: Certified Tax Agent No. CTA-SZ-2024-0318
"""
]

# ── Report 3: 政策匹配报告 ──────────────────────────────────────────────────
report3_pages = [
    """POLICY RESEARCH AND SUBSIDY APPLICATION FEASIBILITY REPORT
Report Date: 2024-03-20
Enterprise: Shenzhen Mingyuan Technology Co., Ltd.
(深圳明远科技有限公司)
Credit Code: 91440300MA5DXXXXYX

=== Applicable Policy List ===
1. High-tech Enterprise Income Tax Preference
   Policy Type: Tax Incentive
   Benefit: 15% corporate income tax rate (vs standard 25%)
   Match: FULLY MATCHED (already certified)
   Status: Currently enjoying

2. R&D Expense Super-deduction Policy
   Policy Type: Tax Incentive  
   Benefit: 100% additional deduction on qualifying R&D expenses
   Match: FULLY MATCHED
   Estimated annual tax saving: 150,000.00 - 200,000.00 Yuan
   Status: Partially applied, optimization recommended

3. Shenzhen Special Economic Zone Software Enterprise VAT Refund
   Policy Type: Tax Incentive
   Benefit: VAT instant refund when actual burden exceeds 3%
   Match: FULLY MATCHED (software enterprise certified)
   Status: Currently enjoying

4. Guangdong Province Science & Technology Innovation Fund
   Policy Type: Financial Subsidy
   Amount: 500,000.00 - 2,000,000.00 Yuan
   Match: PARTIAL MATCH (needs provincial-level project application)
   Application Window: March-April each year
   Difficulty: Medium-High
   Recommendation: Prepare and apply immediately

5. Shenzhen High-tech Enterprise Development Fund
   Policy Type: Financial Subsidy
   Amount: 100,000.00 - 500,000.00 Yuan
   Match: FULLY MATCHED
   Application Window: June-July each year
   Difficulty: Medium
   Recommendation: Apply in upcoming window
""",
    """=== Subsidy Feasibility Assessment ===
Priority Project 1: Guangdong Province Science & Technology Innovation Fund
Application Match: Partial Match
- Meets: High-tech enterprise, R&D ratio >15%, own IP
- Needs preparation: Provincial project registration, 3-year audit reports
Estimated Subsidy: 500,000.00 - 2,000,000.00 Yuan
Application Window: March-April 2024 (URGENT - deadline approaching)
Difficulty: Medium-High
Recommendation: APPLY IMMEDIATELY

Required Materials:
1. Project application form
2. Business license, high-tech certificate
3. Audited financial reports (3 years)
4. R&D personnel list with social insurance proof
5. IP certificates (patents, software copyrights)
6. Project feasibility study report

Priority Project 2: Shenzhen High-tech Enterprise Development Fund
Application Match: Fully Matched
Estimated Subsidy: 100,000.00 - 500,000.00 Yuan
Application Window: June-July 2024
Difficulty: Medium
Recommendation: Prepare materials now, apply in June

=== Application Timeline ===
March-April 2024: Guangdong Province S&T Fund (HIGH PRIORITY - urgent)
June-July 2024: Shenzhen High-tech Development Fund (MEDIUM PRIORITY)
Year-round: R&D super-deduction quarterly filing (ROUTINE)

=== Total Estimated Potential Subsidy ===
Conservative Estimate: 600,000.00 - 800,000.00 Yuan
Optimistic Estimate: 1,500,000.00 - 2,500,000.00 Yuan

Policy information valid as of: 2024-03-20
Note: Policy details subject to change. Verify with official sources before applying.
Report prepared by: Policy Research Team
"""
]

# Create PDFs
pdf_dir = os.path.join(WORKSPACE, "clients/shenzhen_mingyuan")
os.makedirs(pdf_dir, exist_ok=True)

create_pdf_fitz(os.path.join(pdf_dir, "report1_basic_info.pdf"), "Basic Info", report1_pages)
create_pdf_fitz(os.path.join(pdf_dir, "report2_financial_tax.pdf"), "Financial Tax", report2_pages)
create_pdf_fitz(os.path.join(pdf_dir, "report3_policy_match.pdf"), "Policy Match", report3_pages)

print("Workspace generated successfully.")
print(f"PDFs created in: {pdf_dir}")
print("Directory structure:")
for root, dirs_list, files in os.walk(WORKSPACE):
    level = root.replace(WORKSPACE, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')