FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install python-docx lxml -i https://pypi.tuna.tsinghua.edu.cn/simple

RUN npm config set registry https://registry.npmmirror.com && \
    npm install -g openclaw --prefix /root/.npm-global 2>/dev/null || true

# Manually create the skill directory structure since npm install may not have it
RUN mkdir -p /root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/references

# Write the format rules reference file
RUN python3 - << 'PYEOF'
import os
content = '''# 公文格式规范

## 页面设置
- 纸张：A4（210mm × 297mm）
- 上边距：37mm
- 下边距：35mm
- 左边距：28mm
- 右边距：26mm

## 正文字体
- 字体：仿宋_GB2312
- 字号：四号（14磅）
- 行距：固定值28磅
- 对齐：两端对齐

## 标题层级

### 一级标题
- 识别标志：文字前有"一、"、"二、"、"三、"等中文数字序号
- 字体：黑体
- 字号：四号（14磅）
- 加粗：否

### 二级标题
- 识别标志：文字前有"（一）"、"（二）"、"（三）"等括号中文数字序号
- 字体：楷体_GB2312
- 字号：四号（14磅）
- 加粗：否

### 三级标题
- 识别标志：文字前有"1."、"2."、"3."等阿拉伯数字加点序号
- 字体：仿宋_GB2312
- 字号：四号（14磅）
- 加粗：是

### 四级标题
- 识别标志：文字前有"（1）"、"（2）"、"（3）"等括号阿拉伯数字序号
- 字体：仿宋_GB2312
- 字号：四号（14磅）
- 加粗：否
- 斜体：否

## 表格格式
- 字体：仿宋_GB2312
- 字号：五号（10.5磅）
- 表格居中

## 页码
- 位置：页面底端居中
- 字体：四号（14磅）
- 格式：阿拉伯数字，居中

## 文件主标题（文件第一段若为标题行）
- 字体：方正小标宋简体
- 字号：二号（22磅）
- 对齐：居中
- 加粗：否
'''
path = '/root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/references/format-rules.md'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Written format-rules.md')
PYEOF

# Write the main format_gw.py script
RUN python3 - << 'PYEOF'
import os
content = '''#!/usr/bin/env python3
"""
公文排版工具 - 根据公文格式规范自动排版Word文档
"""

import sys
import re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy


def set_page_margins(doc):
    """设置页边距：上37mm 下35mm 左28mm 右26mm"""
    for section in doc.sections:
        section.top_margin = Cm(3.7)
        section.bottom_margin = Cm(3.5)
        section.left_margin = Cm(2.8)
        section.right_margin = Cm(2.6)
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)


def set_run_font(run, font_name, font_size_pt, bold=False, italic=False):
    """设置run的字体"""
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    run.font.bold = bold
    run.font.italic = italic
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:eastAsia"), font_name)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)


def set_paragraph_line_spacing(para, spacing_pt):
    """设置段落固定行距"""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    pPr = para._p.get_or_add_pPr()
    spacing = pPr.find(qn("w:spacing"))
    if spacing is None:
        spacing = OxmlElement("w:spacing")
        pPr.append(spacing)
    spacing.set(qn("w:line"), str(int(spacing_pt * 20)))
    spacing.set(qn("w:lineRule"), "exact")


def detect_paragraph_type(text):
    text = text.strip()
    if re.match(r"^[一二三四五六七八九十]+、", text):
        return "heading1"
    if re.match(r"^（[一二三四五六七八九十]+）", text):
        return "heading2"
    if re.match(r"^\d+\.", text):
        return "heading3"
    if re.match(r"^（\d+）", text):
        return "heading4"
    return "body"


def format_paragraph(para, para_type, is_first_para=False):
    if para_type == "title_main" or is_first_para:
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in para.runs:
            set_run_font(run, "方正小标宋简体", 22, bold=False)
        set_paragraph_line_spacing(para, 28)
    elif para_type == "heading1":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in para.runs:
            set_run_font(run, "黑体", 14, bold=False)
        set_paragraph_line_spacing(para, 28)
    elif para_type == "heading2":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in para.runs:
            set_run_font(run, "楷体_GB2312", 14, bold=False)
        set_paragraph_line_spacing(para, 28)
    elif para_type == "heading3":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in para.runs:
            set_run_font(run, "仿宋_GB2312", 14, bold=True)
        set_paragraph_line_spacing(para, 28)
    elif para_type == "heading4":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in para.runs:
            set_run_font(run, "仿宋_GB2312", 14, bold=False, italic=False)
        set_paragraph_line_spacing(para, 28)
    else:
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for run in para.runs:
            set_run_font(run, "仿宋_GB2312", 14, bold=False)
        set_paragraph_line_spacing(para, 28)


def format_tables(doc):
    for table in doc.tables:
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        set_run_font(run, "仿宋_GB2312", 10.5, bold=False)


def add_page_numbers(doc):
    for section in doc.sections:
        footer = section.footer
        footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in footer_para.runs:
            run.text = ""
        run = footer_para.add_run()
        set_run_font(run, "仿宋_GB2312", 14)
        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(qn("w:fldCharType"), "begin")
        run._r.append(fldChar1)
        instrText = OxmlElement("w:instrText")
        instrText.text = "PAGE"
        run._r.append(instrText)
        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(qn("w:fldCharType"), "end")
        run._r.append(fldChar2)


def format_document(input_path, output_path):
    doc = Document(input_path)
    set_page_margins(doc)
    first_content_para = True
    for i, para in enumerate(doc.paragraphs):
        text = para.text.strip()
        if not text:
            continue
        if first_content_para:
            format_paragraph(para, "title_main", is_first_para=True)
            first_content_para = False
            continue
        para_type = detect_paragraph_type(text)
        format_paragraph(para, para_type)
    format_tables(doc)
    add_page_numbers(doc)
    doc.save(output_path)
    print(f"格式化完成：{output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python3 format_gw.py <input.docx> <output.docx>")
        sys.exit(1)
    format_document(sys.argv[1], sys.argv[2])
'''
path = '/root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/format_gw.py'
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Written format_gw.py')
PYEOF

RUN chmod +x /root/.npm-global/lib/node_modules/openclaw/skills/doc-format-gw/format_gw.py