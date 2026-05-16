#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate the sandbox workspace for the official-document task.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "official-document/scripts",
    "official-document/references",
    "official-document/assets",
    "drafts/2026/Q1",
    "drafts/2026/Q2",
    "archive/2025/notices",
    "archive/2025/reports",
    "templates/word",
    "templates/pdf",
    "internal/hr",
    "internal/finance",
    "output",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── SKILL.md  (the canonical reference the agent must read) ─────────────────
skill_md = r"""# official-document - 通用机关公文技能

基于 **GB/T 9704-2012** 党政机关公文格式标准，适用于各级机关单位生成正式公文。

## 适用场景

- 生成党政机关公文（通知、请示、报告、函等）
- 按国家标准排版的正式文档
- 需要规范格式的红头文件

## 技术方案

- **语言**: Python 3
- **库**: python-docx
- **编码**: UTF-8（文件头声明 `# -*- coding: utf-8 -*-`）

## 核心格式参数（GB/T 9704-2012）

| 项目 | 标准值 |
|------|--------|
| 纸张 | A4 |
| 上边距 | 3.7cm |
| 下边距 | 3.5cm |
| 左边距 | 2.8cm |
| 右边距 | 2.6cm |
| 公文标题 | 方正小标宋简体 22pt，不加粗，居中 |
| 正文 | 仿宋_GB2312 16pt，首行缩进0.85cm |
| 一级标题 | 黑体 16pt，不加粗 |
| 二级标题 | 楷体_GB2312 16pt，不加粗 |
| 行距 | 固定28.5磅 |
| 页码 | 宋体 12pt，居中或右下 |

## 公文结构规范

### 发文字号格式

- 年份必须使用**六角括号** `〔〕`，格式：`机关代字〔年份〕顺序号`
- 示例：`陕XX〔2026〕28号`、`中XX〔2026〕28号`
- **严禁**使用方括号 `【】` 或其他括号代替

### 各部分间距

| 位置 | 间距要求 |
|------|----------|
| 发文字号 → 标题 | 空2行 |
| 标题 → 主送机关 | 空1行 |
| 主送机关 → 正文 | 直接连接，正常行距 |
| 正文段落之间 | 正常行距，无额外段前段后 |
| 附件前 | 空1行 |
| 落款前 | 空3行 |
| 落款 → 日期 | 同一行或相邻行，距右4汉字 |
| 日期 → 联系方式 | 空1行 |

### 标题字体规范

| 要素 | 字体 | 字号 | 加粗 | 说明 |
|------|------|------|------|------|
| 发文字号 | 仿宋_GB2312 | 16pt | 否 | 右对齐，年份用六角括号 `〔〕`，如 `陕XX〔2026〕28号`，**不得**用方括号 `【】` |
| 公文标题 | 方正小标宋简体 | 22pt | 否 | 居中 |
| 主送机关 | 仿宋_GB2312 | 16pt | 否 | 顶格 |
| 正文 | 仿宋_GB2312 | 16pt | 否 | 首行缩进0.85cm |
| 一级标题 | 黑体 | 16pt | 否 | 首行缩进0.85cm |
| 二级标题 | 楷体_GB2312 | 16pt | 否 | 首行缩进0.85cm |
| 落款 | 仿宋_GB2312 | 16pt | 否 | 右对齐 |
| 日期 | 仿宋_GB2312 | 16pt | 否 | 右对齐 |

### 附件格式

- 单个附件：`附件：文件名`
- 多个附件：
  ```
  附件：1.文件名1
        2.文件名2
  ```
  （编号左对齐）

### 联系方式格式

- 位置：落款日期下方空1行
- 格式：`（联系人：XXX  电话：XXX，地址：XXX）`
- 首行缩进0.85cm

## 使用方法

1. 加载技能：`use_skill("official-document")`
2. 复制 `scripts/generate_docx.py` 到工作目录
3. 修改 CONFIG 配置和 CONTENTS 正文内容
4. 运行 `python generate_docx.py`

## Python 编码注意事项

**重要**：所有字符串使用三引号 """ + r"""...""" + """ 包裹，避免文本内容中的引号与字符串分隔符冲突。

### 中文引号必须原样保留

中文排版引号为弯引号字符，**区分左右**（左引号和右引号不同）。生成脚本时必须原样保留用户输入的引号，不得替换为英文直引号。

## 文件结构

```
official-document/
├── SKILL.md                      # 本文档
├── scripts/
│   └── generate_docx.py          # Python生成脚本
├── references/
│   └── gbt9704-2012.md           # GB/T 9704-2012 标准全文
└── assets/
    └── template_docx.py          # 精简模板
```
"""
(WORKSPACE / "official-document" / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ─── generate_docx.py  (the template script, already exists per SKILL.md) ────
generate_docx_py = r"""# -*- coding: utf-8 -*-
"""
# NOTE: This is intentionally minimal/stub. The agent must write its OWN
# generation script based on SKILL.md. This file exists so the SKILL.md
# reference is satisfied.
generate_docx_py += '''
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_document(config, contents, output_path):
    """Stub: implement according to GB/T 9704-2012 standard."""
    doc = Document()
    doc.save(output_path)

if __name__ == "__main__":
    pass
'''
(WORKSPACE / "official-document" / "scripts" / "generate_docx.py").write_text(
    generate_docx_py, encoding="utf-8"
)

# ─── assets/template_docx.py ─────────────────────────────────────────────────
(WORKSPACE / "official-document" / "assets" / "template_docx.py").write_text(
    "# -*- coding: utf-8 -*-\n# Minimal template placeholder\n", encoding="utf-8"
)

# ─── references/gbt9704-2012.md  (distractor) ────────────────────────────────
gbt_ref = """# GB/T 9704-2012 党政机关公文格式

本文档为 GB/T 9704-2012 标准摘要，供参考。

## 1 范围
本标准规定了党政机关公文的用纸、印刷、装订要求及各要素的编排规则。

## 2 规范性引用文件
GB/T 788 图书和杂志开本及其幅面尺寸

## 3 页面设置
- 纸张：A4
- 上页边距：37mm；下页边距：35mm
- 左页边距：28mm；右页边距：26mm

## 4 字体字号
略，见SKILL.md
"""
(WORKSPACE / "official-document" / "references" / "gbt9704-2012.md").write_text(
    gbt_ref, encoding="utf-8"
)

# ─── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "drafts/2026/Q1/draft_notice_v1.txt": "【草稿】关于开展2026年安全生产检查的通知\n（此为草稿，格式不规范，仅供参考）\n\n各单位：\n请注意安全检查事项。\n\n                              XX县人民政府办公室\n                              2026年1月15日",
    "drafts/2026/Q1/draft_notice_v2.txt": "第二版草稿 - 内容待定",
    "drafts/2026/Q2/procurement_outline.txt": "采购方案大纲\n1. 采购需求\n2. 供应商资质\n3. 评分标准",
    "drafts/2026/Q2/meeting_minutes_0312.txt": "2026年3月12日会议纪要\n出席人员：XXX、XXX\n议题：讨论采购公文格式",
    "archive/2025/notices/notice_20251101.txt": "【旧版通知】某某单位关于XX事项的通知（2025年归档）",
    "archive/2025/notices/notice_20251215.txt": "【旧版通知】某某单位关于YY事项的通知（格式已过时）",
    "archive/2025/reports/annual_report_2025.txt": "2025年度工作报告（存档）",
    "templates/word/old_template_2020.txt": "旧版公文模板（2020，不符合最新标准）",
    "templates/pdf/pdf_guide.txt": "PDF转换指南（暂不适用）",
    "internal/hr/staff_list.txt": "人员名单（内部文件，勿外传）",
    "internal/finance/budget_2026.txt": "2026年预算草案\n总计：1,500,000元",
    "output/.gitkeep": "",
}

for rel_path, content in distractors.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ─── task_brief.json  (the business brief for the agent) ─────────────────────
brief = {
    "issuing_office": "XX县人民政府采购管理办公室",
    "document_code": "县采购办〔2026〕12号",
    "title": "关于开展2026年度政府集中采购工作的通知",
    "recipients": ["各乡镇人民政府", "县直各部门"],
    "body": {
        "opening": "为进一步规范政府采购行为，提高财政资金使用效益，根据《政府采购法》及相关规定，现将2026年度集中采购工作有关事项通知如下。",
        "section1_title": "一、工作目标",
        "section1_content": "坚持公开、公平、公正原则，全面落实政府采购政策，力争年度采购规模达1500万元，节支率不低于8%。",
        "section2_title": "二、主要任务",
        "subsection2_1_title": "（一）编制采购计划",
        "subsection2_1_content": "各预算单位须于2026年2月28日前完成年度采购计划申报，填写《政府集中采购计划申报表》并报送本办公室审核。",
        "subsection2_2_title": "（二）规范采购程序",
        "subsection2_2_content": "单项或批量采购金额达到公开招标数额标准的，一律采用公开招标方式；未达标准的，按竞争性谈判或询价方式执行。",
        "section3_title": "三、工作要求",
        "section3_content": "各单位须高度重视，指定专人负责采购计划申报及合同管理工作，确保数据准确、流程合规。如有疑问，请及时与本办联系。"
    },
    "attachments": [
        "政府集中采购计划申报表",
        "2026年集中采购目录及限额标准"
    ],
    "issuer": "XX县人民政府采购管理办公室",
    "date": "二〇二六年一月二十日",
    "contact": {
        "person": "李明",
        "phone": "0912-8765432",
        "address": "XX县行政中心B座304室"
    },
    "output_filename": "county_procurement_notice_2026.docx"
}

(WORKSPACE / "task_brief.json").write_text(
    json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created under: {WORKSPACE}")