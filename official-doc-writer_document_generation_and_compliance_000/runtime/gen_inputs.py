import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Skill directory structure (mimics .trae/skills/official-doc-writer) ──
skill_root = workspace / ".trae" / "skills" / "official-doc-writer"
skill_root.mkdir(parents=True, exist_ok=True)

# scripts directory
scripts_dir = skill_root / "scripts"
scripts_dir.mkdir(exist_ok=True)

# fonts directory
fonts_dir = skill_root / "fonts"
fonts_dir.mkdir(exist_ok=True)

# references directory
refs_dir = skill_root / "references"
refs_dir.mkdir(exist_ok=True)

# ── 2. Generate the actual generate_official_doc.py script ──
generate_script = '''# -*- coding: utf-8 -*-
"""
党政机关公文生成脚本 - 符合GB/T 9704-2012标准
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy


def set_font(run, font_name, size_pt, bold=False, color=None):
    """设置字体属性"""
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_paragraph_with_format(doc, text, font_name, size_pt, bold=False,
                               alignment=WD_ALIGN_PARAGRAPH.LEFT,
                               color=None, first_line_indent=0):
    """添加格式化段落"""
    para = doc.add_paragraph()
    para.alignment = alignment
    if first_line_indent:
        para.paragraph_format.first_line_indent = Pt(size_pt * first_line_indent)
    run = para.add_run(text)
    set_font(run, font_name, size_pt, bold, color)
    return para


def set_page_margins(doc):
    """设置页面边距 - GB/T 9704-2012标准"""
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(37)
    section.bottom_margin = Mm(35)
    section.left_margin = Mm(28)
    section.right_margin = Mm(26)


def add_red_line(doc, width_cm=15.6, thick=True):
    """添加红色分隔线"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = para._p.get_or_add_pPr()
    pBdr = OxmlElement(\'w:pBdr\')
    bottom = OxmlElement(\'w:bottom\')
    line_width = \'24\' if thick else \'6\'
    bottom.set(qn(\'w:val\'), \'single\')
    bottom.set(qn(\'w:sz\'), line_width)
    bottom.set(qn(\'w:space\'), \'1\')
    bottom.set(qn(\'w:color\'), \'FF0000\')
    pBdr.append(bottom)
    pPr.append(pBdr)
    return para


def create_official_document(doc_type, content):
    """
    创建党政机关公文Word文档

    Parameters
    ----------
    doc_type : str
        公文类型，如 "通知"、"报告"、"请示"、"函" 等
    content : dict
        公文内容字典，包含以下字段：
        - issuer: str, 发文机关名称
        - doc_number: str, 发文字号（必须使用六角括号〔〕，如 "XX〔2026〕3号"）
        - title: str, 公文标题
        - recipient: str, 主送机关
        - body: list[str | dict], 正文段落列表
              每个元素可以是字符串（普通段落）
              或字典 {"level": 1-4, "text": str} 指定层级标题
        - signer: str, 发文机关署名
        - date: str, 成文日期（阿拉伯数字，月日不编虚位，如 "2026年3月5日"）
        - attachment: str, 附件说明（可选）
        - copy_to: str, 抄送机关（可选）
        - print_org: str, 印发机关（可选，默认为发文机关办公室）
        - print_date: str, 印发日期（可选，默认与成文日期相同）
        - signee: str, 签发人姓名（可选，上行文使用）
        - urgency: str, 紧急程度（可选）
        - classification: str, 密级（可选）

    Returns
    -------
    Document
        python-docx Document 对象，可调用 .save() 保存
    """
    doc = Document()
    set_page_margins(doc)

    # 删除默认段落
    for para in doc.paragraphs:
        p = para._element
        p.getparent().remove(p)

    # ── 版头 ──────────────────────────────────────────────────────────────
    # 密级（可选）
    if content.get(\'classification\'):
        add_paragraph_with_format(
            doc, content[\'classification\'],
            \'SimHei\', 10.5, bold=True,
            alignment=WD_ALIGN_PARAGRAPH.LEFT
        )

    # 紧急程度（可选）
    if content.get(\'urgency\'):
        add_paragraph_with_format(
            doc, content[\'urgency\'],
            \'SimHei\', 10.5, bold=True,
            alignment=WD_ALIGN_PARAGRAPH.LEFT
        )

    # 发文机关标志（红色大字）
    issuer_text = content[\'issuer\'] + \'文件\'
    para = add_paragraph_with_format(
        doc, issuer_text,
        \'FangSong_GB2312\', 22, bold=False,
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
        color=(255, 0, 0)
    )
    # 上边缘空白段（模拟35mm）
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)

    # 签发人（上行文，可选）
    if content.get(\'signee\'):
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        run_label = para.add_run(\'签发人：\')
        set_font(run_label, \'FangSong_GB2312\', 10.5)
        run_name = para.add_run(content[\'signee\'])
        set_font(run_name, \'SimKai\', 10.5)

    # 发文字号（居中）
    doc.add_paragraph()  # 空一行
    add_paragraph_with_format(
        doc, content[\'doc_number\'],
        \'FangSong_GB2312\', 10.5,
        alignment=WD_ALIGN_PARAGRAPH.CENTER
    )

    # 红色分隔线
    add_red_line(doc)

    # ── 主体 ──────────────────────────────────────────────────────────────
    # 标题（2号小标宋）
    doc.add_paragraph()  # 红线后空一行
    doc.add_paragraph()  # 再空一行
    add_paragraph_with_format(
        doc, content[\'title\'],
        \'FangSong_GB2312\', 21, bold=True,
        alignment=WD_ALIGN_PARAGRAPH.CENTER
    )

    # 主送机关
    doc.add_paragraph()
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(content[\'recipient\'] + \'：\')
    set_font(run, \'FangSong_GB2312\', 10.5)

    # 正文
    level_fonts = {
        1: (\'SimHei\',       10.5, True),   # 一、
        2: (\'SimKai\',       10.5, False),  # （一）
        3: (\'FangSong_GB2312\', 10.5, False),  # 1.
        4: (\'FangSong_GB2312\', 10.5, False),  # （1）
    }
    level_prefixes = {1: \'一、\', 2: \'（一）\', 3: \'1.\', 4: \'（1）\'}

    for item in content.get(\'body\', []):
        if isinstance(item, dict):
            level = item.get(\'level\', 0)
            text = item.get(\'text\', \'\')
            if level in level_fonts:
                font_name, size, bold = level_fonts[level]
                para = doc.add_paragraph()
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if level == 1:
                    para.paragraph_format.first_line_indent = Pt(size * 2)
                run = para.add_run(text)
                set_font(run, font_name, size, bold)
            else:
                add_paragraph_with_format(
                    doc, text, \'FangSong_GB2312\', 10.5,
                    first_line_indent=2
                )
        else:
            add_paragraph_with_format(
                doc, str(item), \'FangSong_GB2312\', 10.5,
                first_line_indent=2
            )

    # 附件（可选）
    if content.get(\'attachment\'):
        doc.add_paragraph()
        add_paragraph_with_format(
            doc, \'附件：\' + content[\'attachment\'],
            \'FangSong_GB2312\', 10.5,
            first_line_indent=2
        )

    # 署名和成文日期
    doc.add_paragraph()
    add_paragraph_with_format(
        doc, content[\'signer\'],
        \'FangSong_GB2312\', 10.5,
        alignment=WD_ALIGN_PARAGRAPH.RIGHT
    )
    add_paragraph_with_format(
        doc, content[\'date\'],
        \'FangSong_GB2312\', 10.5,
        alignment=WD_ALIGN_PARAGRAPH.RIGHT
    )

    # ── 版记 ──────────────────────────────────────────────────────────────
    # 抄送（可选）
    if content.get(\'copy_to\'):
        add_red_line(doc, thick=False)
        add_paragraph_with_format(
            doc, \'抄送：\' + content[\'copy_to\'] + \'。\',
            \'FangSong_GB2312\', 8
        )

    # 印发机关和印发日期
    print_org = content.get(\'print_org\', content[\'issuer\'] + \'办公室\')
    print_date = content.get(\'print_date\', content[\'date\'])
    add_red_line(doc, thick=True)
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run_org = para.add_run(\' \' + print_org)
    set_font(run_org, \'FangSong_GB2312\', 8)
    run_date = para.add_run(\'  \' + print_date + \' \')
    set_font(run_date, \'FangSong_GB2312\', 8)
    add_red_line(doc, thick=True)

    return doc


if __name__ == \'__main__\':
    # 示例：生成一份通知
    content = {
        \'issuer\': \'示例机关\',
        \'doc_number\': \'示例〔2026〕1号\',
        \'title\': \'关于开展示例工作的通知\',
        \'recipient\': \'各部门\',
        \'body\': [
            \'为做好示例工作，现将有关事项通知如下：\',
            {\'level\': 1, \'text\': \'一、工作目标\'},
            \'切实推进示例工作落实到位。\',
            {\'level\': 1, \'text\': \'二、工作要求\'},
            \'各部门要高度重视，认真落实。\',
            \'特此通知。\'
        ],
        \'signer\': \'示例机关\',
        \'date\': \'2026年1月15日\',
    }
    doc = create_official_document(\'通知\', content)
    doc.save(\'example_notice.docx\')
    print("示例文档已生成：example_notice.docx")
'''

(scripts_dir / "generate_official_doc.py").write_text(generate_script, encoding='utf-8')

# ── 3. Generate dialog_manager.py (stub, for completeness) ──
dialog_manager = '''# -*- coding: utf-8 -*-
"""对话管理器 - 管理公文生成对话状态"""

class DialogManager:
    def __init__(self):
        self.state = {}
        self.step = 0
        self.prompts = [
            "您需要生成什么类型的公文？",
            "请告诉我发文机关的全称：",
            "请告诉我主送机关：",
            "请描述公文事由：",
            "成文日期是？",
            "请描述正文内容要点：",
        ]

    def get_next_prompt(self):
        if self.step < len(self.prompts):
            return self.prompts[self.step]
        return None

    def process_user_input(self, user_input):
        self.step += 1
        return self.state

    def get_document_content(self):
        return self.state


def create_dialog_manager():
    return DialogManager()
'''
(scripts_dir / "dialog_manager.py").write_text(dialog_manager, encoding='utf-8')

# ── 4. Generate smart_prompts.py (stub) ──
smart_prompts = '''# -*- coding: utf-8 -*-
"""智能提示系统"""

OPENING_PROMPTS = {
    "通知": ["为……，现……如下：", "根据……，决定……"],
    "报告": ["现将……报告如下：", "关于……情况报告如下："],
    "请示": ["关于……的请示", "现就……请示如下："],
    "函":   ["关于……的函", "现就……函告如下："],
}

ENDING_PROMPTS = {
    "通知": ["特此通知。", "请认真贯彻执行。"],
    "报告": ["特此报告。", "以上报告，请审阅。"],
    "请示": ["妥否，请批示。", "以上请示，请予批复。"],
    "函":   ["请予研究函复。", "特此函告。"],
}


class SmartPromptSystem:
    def get_opening_prompt(self, doc_type):
        return OPENING_PROMPTS.get(doc_type, [])

    def get_ending_prompt(self, doc_type):
        return ENDING_PROMPTS.get(doc_type, [])

    def get_structure_hint(self, doc_type):
        return f"{doc_type}正文建议结构：开头语 + 主体内容（分层次） + 结尾语"


def create_smart_prompt_system():
    return SmartPromptSystem()
'''
(scripts_dir / "smart_prompts.py").write_text(smart_prompts, encoding='utf-8')

# ── 5. install_fonts.py (stub) ──
install_fonts = '''# -*- coding: utf-8 -*-
"""字体安装脚本"""
import os, sys

REQUIRED_FONTS = {
    "方正小标宋_GBK": "FZXBSJW.TTF",
    "仿宋_GB2312": "SIMFANG.TTF",
    "黑体": "SIMHEI.TTF",
    "楷体_GB2312": "SIMKAI.TTF",
    "宋体": "SIMSUN.TTF",
}

def install_fonts():
    print("检查字体安装状态...")
    for name, filename in REQUIRED_FONTS.items():
        print(f"  {name} ({filename}): 检查中...")
    print("字体检查完成。")

if __name__ == "__main__":
    install_fonts()
'''
(scripts_dir / "install_fonts.py").write_text(install_fonts, encoding='utf-8')

# ── 6. references/GBT_9704-2012 doc ──
gbt_ref = """# GB/T 9704-2012 党政机关公文格式（摘录）

## 5. 版面要求

### 5.2.1 版心
- 纸张：A4（210mm × 297mm）
- 天头：37mm ± 1mm
- 订口：28mm ± 1mm
- 版心尺寸：156mm × 225mm

### 5.2.2 字体和字号
| 要素 | 字体 | 字号 |
|------|------|------|
| 发文机关标志 | 小标宋体（红色） | — |
| 标题 | 小标宋体 | 2号 |
| 正文 | 仿宋体 | 3号 |
| 一级标题 | 黑体 | 3号 |
| 二级标题 | 楷体 | 3号 |
| 密级/紧急程度 | 黑体 | 3号 |
| 发文字号 | 仿宋体 | 3号 |
| 抄送机关 | 仿宋体 | 4号 |
| 印发机关/日期 | 仿宋体 | 4号 |
| 页码 | 宋体 | 4号（半角） |

## 7. 公文格式各要素编排规则

### 7.2.4 发文字号
- 格式：机关代字〔年份〕序号号
- 年份用六角括号〔〕括入
- 序号不编虚位（1号而非01号）
- 联合行文时，使用主办机关发文字号

### 7.3.1 标题
- 2号小标宋体字，居中排布
- 由发文机关名称、事由、文种组成
- 一般不用标点符号

### 7.3.2 主送机关
- 居左顶格，回行时仍顶格
- 最后一个机关名称后标全角冒号

### 7.3.3 正文
- 3号仿宋体字
- 各自然段左空二字，回行顶格
- 数字、年份不回行

### 结构层次
- 第一层：一、二、三……（黑体）
- 第二层：（一）（二）（三）……（楷体）
- 第三层：1. 2. 3.……（仿宋体）
- 第四层：（1）（2）（3）……（仿宋体）

### 7.3.5 成文日期
- 使用阿拉伯数字
- 年月日标全
- 月、日不编虚位（1月不写成01月）

### 7.4 版记

#### 7.4.2 抄送机关
- 4号仿宋体字
- 格式："抄送：机关名称。"

#### 7.4.3 印发机关和印发日期
- 4号仿宋体字
- 印发机关左空一字，印发日期右空一字
"""
(refs_dir / "GBT_9704-2012_党政机关公文格式.md").write_text(gbt_ref, encoding='utf-8')

# ── 7. fonts/README.md ──
fonts_readme = """# 字体说明
本目录存放公文生成所需字体文件。
请参考SKILL.md中的字体安装说明安装必要字体。
"""
(fonts_dir / "README.md").write_text(fonts_readme, encoding='utf-8')

# ── 8. Distractor files ──
# Various files that have nothing to do with the task
distractors = [
    ("docs/meeting_notes_2026_01.txt", "会议纪要：2026年1月部门会议，讨论预算分配问题。"),
    ("docs/budget_2026.csv", "项目,金额\n信息化建设,500000\n日常运营,200000\n"),
    ("docs/org_chart.json", '{"name": "局长", "subordinates": ["副局长甲", "副局长乙"]}'),
    ("archive/2025/reports/annual_report.txt", "2025年度工作报告（草稿）"),
    ("archive/2025/notices/notice_001.txt", "关于开展安全检查的通知（旧版）\n发文机关：某某局\n主送机关：各科室"),
    ("archive/2025/templates/old_template.docx.bak", "PLACEHOLDER"),
    ("config/app_settings.json", '{"version": "1.0", "debug": false, "log_level": "INFO"}'),
    ("logs/system.log", "[2026-01-01] System started\n[2026-01-02] Document generated"),
    ("tmp/draft_20260301.txt", "草稿：关于申请专项经费的请示（未完成版本）\n发文机关：XX区数字经济局"),
    ("tmp/notes.md", "TODO:\n- 完善请示文档\n- 联系上级部门确认\n- 准备附件材料"),
    ("scripts/old_doc_generator.py", "# 旧版公文生成器（已废弃，请使用新版）\nprint('deprecated')"),
    ("data/contacts.csv", "姓名,职务,电话\n张三,局长,13800000001\n李四,副局长,13800000002"),
    ("data/document_index.json", '{"total": 42, "types": ["通知", "报告", "请示"], "last_updated": "2026-01-01"}'),
]

for rel_path, content in distractors:
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding='utf-8')

# ── 9. The actual task: a messy requirement document ──
requirement_doc = """# 请示文件草稿要求

## 基本信息

发文机关：沈阳市大东区数字经济发展局
主送机关：沈阳市工业和信息化局
发文字号：沈大数经[2026]5号    ← 注意：字号格式待规范化
公文类型：请示
签发人：王建国

## 标题

关于申请2026年度数字经济专项发展资金的请示

## 成文日期

2026年8月05日    ← 注意：日期格式待规范化

## 正文内容要点

开头：现就申请2026年度数字经济专项发展资金事宜，请示如下：

第一部分（一级标题）：一、申请背景
内容：近年来，我区数字经济发展势头良好，2025年数字经济产业产值达到32亿元，
同比增长18.6%。为进一步推动数字产业集群建设，亟需专项资金支持。

第二部分（一级标题）：二、申请事项
子项（二级标题）：（一）资金用途
内容：申请专项资金500万元，用于大东数字经济产业园基础设施升级改造。
子项（二级标题）：（二）实施计划
内容：计划于2026年9月启动，12月底前完成全部建设任务。

第三部分（一级标题）：三、保障措施
内容：我局将严格按照资金使用规定，确保专款专用，并定期向上级报告资金使用情况。

结尾语：使用请示标准结尾语

## 抄送机关

沈阳市发展和改革委员会、大东区人民政府办公室

## 附件

关于大东数字经济产业园建设方案（附件1）

## 备注

1. 发文字号中的括号格式需要按国家标准规范化（应使用六角括号）
2. 日期中的"05日"应规范为"5日"（不编虚位）
3. 生成的Word文档请保存为：qingshi_2026.docx
"""

task_requirements_dir = workspace / "task_requirements"
task_requirements_dir.mkdir(parents=True, exist_ok=True)
(task_requirements_dir / "qingshi_draft.txt").write_text(requirement_doc, encoding='utf-8')

print("✅ Workspace initialized successfully.")
print(f"   Skill root: {skill_root}")
print(f"   Task requirement: {workspace / 'task_requirements' / 'qingshi_draft.txt'}")