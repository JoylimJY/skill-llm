import os
import random
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create distractor directory structure
dirs = [
    "project_docs/archive/2022",
    "project_docs/archive/2023",
    "project_docs/submissions/draft",
    "project_docs/submissions/final",
    "reference_materials/standards",
    "reference_materials/templates",
    "admin/correspondence",
    "admin/contracts",
    "temp/backup",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "project_docs/archive/2022/old_report_v1.txt": "旧版查新报告草稿，已废弃。项目：可降解骨支架材料研究。",
    "project_docs/archive/2022/reviewer_comments.txt": "审稿意见：请补充英文检索词，结论部分需要加参考文献编号。",
    "project_docs/archive/2023/keywords_draft.txt": "骨支架\n生长因子\nhydroxyapatite\nbone scaffold\ngrowth factor\nPLGA",
    "project_docs/submissions/draft/cover_letter.txt": "尊敬的审核专家，请查阅附件查新报告。",
    "project_docs/submissions/final/submission_checklist.txt": "1. 报告正文\n2. 检索截图\n3. 文献清单\n4. 委托书",
    "reference_materials/standards/GB_T_standard_notes.txt": "《科技查新技术规范》GB/T 3179-2009 主要条款摘录（仅供参考）。",
    "reference_materials/standards/database_list.txt": "CNKI、万方、维普、PubMed、Web of Science、Embase、Scopus",
    "reference_materials/templates/report_template_v3.txt": "查新报告模板 v3.0 - 包含查新点、检索词、检索式、结论等章节。",
    "admin/correspondence/email_20231115.txt": "请于本周五前提交最终版查新报告，谢谢。",
    "admin/contracts/contract_2023_056.txt": "查新合同编号：2023-056，委托单位：XX生物医疗科技有限公司",
    "temp/backup/keywords_backup.txt": "备份检索词列表 - 请勿使用此版本",
}

for filepath, content in distractor_files.items():
    (workspace / filepath).write_text(content, encoding="utf-8")

# =============================================
# CREATE THE MAIN PROBLEM FILE: novelty_report.docx
# =============================================
doc = Document()

# Title
title = doc.add_heading("科技查新报告", 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Basic info table
doc.add_heading("一、基本信息", level=1)
info_table = doc.add_table(rows=6, cols=2)
info_table.style = "Table Grid"
info_data = [
    ("项目名称", "负载生长因子的可降解聚合物骨支架材料的制备与应用"),
    ("委托单位", "XX生物医疗科技有限公司"),
    ("查新机构", "某省科技情报研究所"),
    ("查新员", "李某某"),
    ("查新日期", "2024年3月15日"),
    ("检索范围", "国内外"),
]
for i, (k, v) in enumerate(info_data):
    info_table.rows[i].cells[0].text = k
    info_table.rows[i].cells[1].text = v

# 二、查新点
doc.add_heading("二、查新点", level=1)
doc.add_paragraph(
    "查新点1：本项目研究了一种新型可降解聚乳酸-羟基乙酸共聚物（PLGA）骨支架，"
    "通过静电纺丝技术制备多孔纤维结构，同时利用微球包埋技术将骨形态发生蛋白-2（BMP-2）"
    "和血管内皮生长因子（VEGF）载入支架，实现双生长因子的序贯可控释放，"
    "促进成骨与血管化协同再生，并将支架孔隙率控制在75%-85%之间，"
    "降解周期为12-24周，抗压强度不低于2MPa。"
    "此外，本项目还对支架表面进行了氧等离子体处理以改善细胞黏附性能。"
)
doc.add_paragraph(
    "查新点2：本项目开发的骨支架采用三维打印（3D打印）技术构建仿生骨小梁结构，"
    "孔径为300-500μm，并在支架表面涂覆纳米羟基磷灰石（nHA）涂层，"
    "以提高支架的骨传导性和力学性能，其弹性模量达到1-5GPa范围。"
)

# 三、检索词
doc.add_heading("三、检索词", level=1)
kw_table = doc.add_table(rows=9, cols=3)
kw_table.style = "Table Grid"
kw_headers = ["序号", "中文检索词", "英文检索词"]
for i, h in enumerate(kw_headers):
    kw_table.rows[0].cells[i].text = h

kw_data = [
    ("1", "可降解骨支架", "degradable scaffold"),
    ("2", "聚乳酸-羟基乙酸共聚物", "PLGA"),
    ("3", "骨形态发生蛋白", "bone protein"),
    ("4", "血管内皮生长因子", "vascular growth factor"),
    ("5", "静电纺丝", "electrospinning"),
    ("6", "生长因子缓释", "growth factor"),
    ("7", "骨再生", "bone"),
    ("8", "纳米羟基磷灰石", "nano-hydroxyapatite"),
]
for i, (num, zh, en) in enumerate(kw_data, start=1):
    kw_table.rows[i].cells[0].text = num
    kw_table.rows[i].cells[1].text = zh
    kw_table.rows[i].cells[2].text = en

# 四、检索式
doc.add_heading("四、检索策略与检索式", level=1)
doc.add_paragraph("检索数据库：CNKI（中国知网）、万方数据、维普期刊")
doc.add_paragraph(
    "检索式示例（CNKI）：\n"
    "（可降解 OR 生物降解） AND 骨支架 AND 生长因子 AND PLGA AND 静电纺丝"
)
doc.add_paragraph("时间范围：2015年至今")
doc.add_paragraph("注：以上仅为主要检索式，实际检索中根据结果调整了若干检索策略。")

# 五、检索结果
doc.add_heading("五、检索结果", level=1)
doc.add_paragraph("共检索到相关文献92篇，经筛选后纳入分析文献37篇，均为中文期刊论文及学位论文。")
result_table = doc.add_table(rows=5, cols=4)
result_table.style = "Table Grid"
result_headers = ["数据库", "检索结果数", "筛选后数量", "语种"]
for i, h in enumerate(result_headers):
    result_table.rows[0].cells[i].text = h
result_data = [
    ("CNKI", "58", "22", "中文"),
    ("万方", "21", "9", "中文"),
    ("维普", "13", "6", "中文"),
]
for i, row in enumerate(result_data, start=1):
    for j, val in enumerate(row):
        result_table.rows[i].cells[j].text = val

doc.add_heading("代表性文献", level=2)
refs = [
    "[1] 张某某等. 静电纺PLGA纳米纤维支架负载BMP-2促进骨再生的研究. 中国生物医学工程学报, 2021.",
    "[2] 王某某等. 可降解聚合物骨支架的制备与体外降解性能研究. 生物材料学报, 2020.",
    "[3] 刘某某等. 双生长因子序贯释放骨支架的构建及成骨效果评价. 中华骨科杂志, 2022.",
    "[4] 陈某某等. 3D打印羟基磷灰石/PLGA复合骨修复支架研究. 无机材料学报, 2021.",
    "[5] 赵某某等. 仿生骨小梁结构多孔支架的力学性能与骨传导性研究. 复合材料学报, 2023.",
]
for ref in refs:
    doc.add_paragraph(ref)

# 六、查新结论
doc.add_heading("六、查新结论", level=1)
doc.add_paragraph(
    "经过系统检索与文献分析，本项目在可降解骨支架及生长因子负载领域填补了国内空白，"
    "技术水平国际领先。具体分析如下："
)
doc.add_paragraph(
    "针对查新点1，经检索CNKI、万方、维普等数据库，检索到与本项目相关的文献37篇。"
    "现有研究中，张某某等[1]研究了PLGA纳米纤维支架负载BMP-2的成骨效果，"
    "但未涉及双生长因子（BMP-2与VEGF）的序贯可控释放机制；刘某某等[3]虽构建了"
    "双生长因子释放支架，但其支架孔隙率（60%-70%）和降解周期（8-16周）与本项目存在差异。"
    "因此，本项目查新点1在所检文献范围内尚未见与之完全相同的报道。"
)
doc.add_paragraph(
    "综合以上检索结果，本项目技术方案具有创新性，在国内外相关领域均属首创，"
    "建议予以积极支持。"
)

# Save
report_path = workspace / "novelty_report.docx"
doc.save(str(report_path))
print(f"Created: {report_path}")
print("Workspace structure created successfully.")