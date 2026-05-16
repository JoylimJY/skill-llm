import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Create the official skill directory structure ──────────────────────────────

# scripts/
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

# Write the real md2docx.py conversion script
md2docx_script = r'''#!/usr/bin/env python3
"""
md2docx.py  —  Convert Markdown to an official Chinese government-style .docx
Optionally also produce a PDF via LibreOffice.

Usage:
    python scripts/md2docx.py input.md -o output.docx
    python scripts/md2docx.py input.md -o output.pdf --pdf
    python scripts/md2docx.py input.md -o output.docx --pdf
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)


# ── Heading counters ──────────────────────────────────────────────────────────
def cn_num(n):
    nums = "一二三四五六七八九十"
    if 1 <= n <= 10:
        return nums[n - 1]
    return str(n)


def arabic_to_paren(n):
    return f"（{n}）"


class HeadingCounter:
    def __init__(self):
        self.counters = {2: 0, 3: 0, 4: 0, 5: 0}

    def next(self, level):
        self.counters[level] += 1
        # reset deeper levels
        for deeper in range(level + 1, 6):
            if deeper in self.counters:
                self.counters[deeper] = 0
        return self.counters[level]

    def format(self, level, n):
        if level == 2:
            return f"{cn_num(n)}、"
        elif level == 3:
            return f"（{cn_num(n)}）"
        elif level == 4:
            return f"{n}."
        elif level == 5:
            return f"（{n}）"
        return ""


# ── Paragraph helpers ─────────────────────────────────────────────────────────
def set_font(run, name_cn="仿宋_GB2312", name_en="Times New Roman", size_pt=16):
    run.font.size = Pt(size_pt)
    run.font.name = name_en
    run.element.rPr.rFonts.set(qn("w:eastAsia"), name_cn)


def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(22)
    run.font.name = "Times New Roman"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "方正小标宋简体")
    return p


def add_heading(doc, level, text, counter):
    n = counter.next(level)
    prefix = counter.format(level, n)
    full_text = prefix + text

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = None

    if level == 2:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(full_text)
        run.bold = True
        run.font.size = Pt(16)
        run.font.name = "Times New Roman"
        run.element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    elif level == 3:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(full_text)
        run.bold = False
        run.font.size = Pt(16)
        run.font.name = "Times New Roman"
        run.element.rPr.rFonts.set(qn("w:eastAsia"), "楷体_GB2312")
    elif level == 4:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(full_text)
        run.bold = False
        run.font.size = Pt(16)
        run.font.name = "Times New Roman"
        run.element.rPr.rFonts.set(qn("w:eastAsia"), "仿宋_GB2312")
    elif level == 5:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(full_text)
        run.bold = False
        run.font.size = Pt(14)
        run.font.name = "Times New Roman"
        run.element.rPr.rFonts.set(qn("w:eastAsia"), "仿宋_GB2312")
    return p


def add_body(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Pt(32)
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(text)
    run.font.size = Pt(16)
    run.font.name = "Times New Roman"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "仿宋_GB2312")
    return p


# ── Markdown parser ───────────────────────────────────────────────────────────
def parse_markdown(md_text):
    """Return list of (type, level, text) tuples."""
    items = []
    for line in md_text.splitlines():
        m = re.match(r'^(#{1,5})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            items.append(("heading", level, text))
        elif line.strip():
            items.append(("body", 0, line.strip()))
    return items


# ── Build document ────────────────────────────────────────────────────────────
def build_docx(items, output_path):
    doc = Document()

    # Page margins (A4, standard official)
    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.left_margin = Cm(2.8)
    section.right_margin = Cm(2.6)
    section.top_margin = Cm(3.7)
    section.bottom_margin = Cm(3.5)

    counter = HeadingCounter()

    for typ, level, text in items:
        if typ == "heading":
            if level == 1:
                add_title(doc, text)
            else:
                add_heading(doc, level, text, counter)
        else:
            add_body(doc, text)

    doc.save(str(output_path))
    print(f"[OK] Saved docx: {output_path}")


# ── PDF via LibreOffice ───────────────────────────────────────────────────────
def convert_to_pdf(docx_path, pdf_path):
    out_dir = pdf_path.parent
    cmd = [
        "soffice", "--headless", "--convert-to", "pdf",
        "--outdir", str(out_dir), str(docx_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] LibreOffice conversion failed:\n{result.stderr}")
        sys.exit(1)
    # LibreOffice names it after the docx stem
    generated = out_dir / (docx_path.stem + ".pdf")
    if generated != pdf_path:
        generated.rename(pdf_path)
    print(f"[OK] Saved pdf:  {pdf_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Markdown → Official DOCX")
    parser.add_argument("input", help="Input .md file")
    parser.add_argument("-o", "--output", required=True, help="Output file path (.docx or .pdf)")
    parser.add_argument("--pdf", action="store_true", help="Also produce a PDF alongside the docx")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}")
        sys.exit(1)

    md_text = input_path.read_text(encoding="utf-8")
    items = parse_markdown(md_text)

    if args.pdf and output_path.suffix.lower() != ".pdf":
        # Output docx AND pdf
        build_docx(items, output_path)
        pdf_path = output_path.with_suffix(".pdf")
        convert_to_pdf(output_path, pdf_path)
    elif output_path.suffix.lower() == ".pdf":
        # Output only pdf (build temp docx first)
        tmp_docx = output_path.with_suffix(".docx")
        build_docx(items, tmp_docx)
        convert_to_pdf(tmp_docx, output_path)
        tmp_docx.unlink(missing_ok=True)
    else:
        # Output only docx
        build_docx(items, output_path)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "md2docx.py").write_text(md2docx_script, encoding="utf-8")

# references/
refs_dir = workspace / "references"
refs_dir.mkdir(exist_ok=True)

official_format_rules = """# 党政机关公文格式规则（参考）

## 一、页面设置
- 纸张：A4（21cm × 29.7cm）
- 上边距：3.7cm；下边距：3.5cm；左边距：2.8cm；右边距：2.6cm

## 二、标题层级与字体

| Markdown 层级 | 公文层级 | 自动编号格式 | 字体     | 字号 |
|--------------|---------|------------|---------|------|
| `#`          | 文件标题 | 居中        | 方正小标宋简体 | 22pt |
| `##`         | 一级标题 | 一、二、三、 | 黑体     | 16pt |
| `###`        | 二级标题 | （一）（二）| 楷体_GB2312 | 16pt |
| `####`       | 三级标题 | 1. 2. 3.   | 仿宋_GB2312 | 16pt |
| `#####`      | 四级标题 | （1）（2） | 仿宋_GB2312 | 14pt |
| 普通段落     | 正文    | —          | 仿宋_GB2312 | 16pt |

## 三、关键约束
1. **禁止手写序号**：不得在 Markdown 中手动写 `一、`、`（一）`、`1.` 等编号，转换脚本自动生成。
2. 正文段落首行缩进 2 字符（32pt）。
3. 标题不缩进，左对齐（文件标题居中）。

## 四、正文规范
- 使用仿宋_GB2312，16pt
- 段落间距：段前 0pt，段后 0pt
- 行间距：固定值 28pt（脚本默认）

## 五、PDF 输出
- 使用 LibreOffice（soffice）转换
- 命令：`python scripts/md2docx.py input.md -o output.docx --pdf`（同时输出两者）
"""

(refs_dir / "official-format-rules.md").write_text(official_format_rules, encoding="utf-8")

# ── Create the messy raw input that the agent must process ────────────────────
# This is the "problem": a raw draft with manually written numbers (WRONG),
# wrong heading depths, and mixed formatting that violates official rules.

raw_draft = """# 某区城市管理局2024年度综合执法工作要点

## 一、总体要求
深入贯彻党的二十大精神，以习近平新时代中国特色社会主义思想为指导，全面落实市委、市政府关于城市精细化管理的工作部署，着力提升城市环境品质，为广大市民创造整洁、有序、美丽的城市生活环境。

## 二、主要任务
### （一）强化市容秩序管理
切实加大占道经营、乱停乱放等违规行为的整治力度，实现城区主次干道市容秩序全面达标。

#### 1.开展专项整治行动
全年组织不少于12次专项整治行动，重点针对早市夜市、背街小巷的占道经营问题，做到发现一处、处置一处。

#### 2.推进联合执法机制
建立与公安、市场监管等部门的联合执法协调机制，每季度开展不少于一次联合执法行动。

### （二）提升垃圾分类管理水平
按照"减量化、资源化、无害化"原则，持续深化生活垃圾分类工作。

#### 1.完善分类投放设施
年内完成全区不少于200处垃圾分类投放点的规范化改造，确保设施配置达标率100%。

#### 2.强化宣传引导
通过进社区、进学校、进单位等方式，全年开展垃圾分类宣传活动不少于50场次。

##### （1）社区宣传
重点针对老旧小区居民开展入户宣传，提升居民分类投放准确率。

##### （2）单位宣传
对辖区内党政机关、企事业单位开展专项培训，推动单位生活垃圾分类全覆盖。

## 三、保障措施
### （一）加强组织领导
成立由局长任组长的综合执法工作领导小组，统筹协调推进各项工作任务落实。

### （二）强化督查考核
建立月度工作台账，每月对各科室工作完成情况进行通报，考核结果纳入年度绩效考核体系。

## 四、工作要求
各科室要高度重视，切实增强责任感和使命感，严格按照本要点明确的任务分工和时间节点抓好落实，确保各项工作任务高质量完成。
"""

(workspace / "raw_draft.md").write_text(raw_draft, encoding="utf-8")

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_dir = workspace / "archive"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "2023_work_summary.txt").write_text(
    "2023年工作总结草稿——未完成版本，请勿使用。\n包含大量未核实数据。", encoding="utf-8"
)

(distractor_dir / "template_old.docx.bak").write_text(
    "This is a backup of an old template. Not valid.", encoding="utf-8"
)

old_scripts_dir = distractor_dir / "old_scripts"
old_scripts_dir.mkdir(exist_ok=True)
(old_scripts_dir / "convert_v1.py").write_text(
    "# Deprecated conversion script - DO NOT USE\nprint('deprecated')", encoding="utf-8"
)
(old_scripts_dir / "convert_v2.sh").write_text(
    "#!/bin/bash\necho 'This script is no longer maintained'", encoding="utf-8"
)

misc_dir = workspace / "misc"
misc_dir.mkdir(exist_ok=True)

(misc_dir / "meeting_notes_raw.txt").write_text(
    "会议记录（原始速记）\n时间：2024年3月15日\n地点：三楼会议室\n出席人员：张局长、李副局长……（速记内容，格式混乱）",
    encoding="utf-8"
)

(misc_dir / "policy_references.txt").write_text(
    "相关政策文件清单\n1. 《党政机关公文处理工作条例》（国办发〔2012〕14号）\n2. 《党政机关公文格式》（GB/T 9704-2012）",
    encoding="utf-8"
)

(misc_dir / "draft_notice.txt").write_text(
    "通知草稿（未格式化）\n关于开展城市管理专项整治行动的通知\n各相关单位：根据市局统一部署……",
    encoding="utf-8"
)

config_dir = workspace / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "font_config.json").write_text(
    json.dumps({"default_font": "仿宋_GB2312", "title_font": "方正小标宋简体", "heading1_font": "黑体"}, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

(config_dir / "page_settings.json").write_text(
    json.dumps({"paper": "A4", "margin_top_cm": 3.7, "margin_bottom_cm": 3.5, "margin_left_cm": 2.8, "margin_right_cm": 2.6}, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

logs_dir = workspace / "logs"
logs_dir.mkdir(exist_ok=True)

(logs_dir / "conversion_history.log").write_text(
    "2024-01-10 14:23:11 INFO Converted report_q4.md -> report_q4.docx [OK]\n"
    "2024-01-15 09:11:44 WARN Font fallback used for 方正小标宋简体\n"
    "2024-02-03 16:45:22 INFO Converted plan_2024.md -> plan_2024.docx [OK]\n",
    encoding="utf-8"
)

(logs_dir / "error.log").write_text(
    "2024-02-20 10:00:01 ERROR soffice not found in PATH - PDF conversion skipped\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")