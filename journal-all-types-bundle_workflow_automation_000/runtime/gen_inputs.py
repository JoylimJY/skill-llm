import os
import json
import random

random.seed(42)

BASE = "/workspace"
SKILL_DIR = os.path.join(BASE, "journal-submission-radar")
RESOURCES_DIR = os.path.join(SKILL_DIR, "resources")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
DRAFTS_DIR = os.path.join(BASE, "researcher_drafts")
ARCHIVE_DIR = os.path.join(BASE, "archive", "old_submissions", "2022")
NOTES_DIR = os.path.join(BASE, "notes")

for d in [RESOURCES_DIR, SCRIPTS_DIR, DRAFTS_DIR, ARCHIVE_DIR, NOTES_DIR,
          os.path.join(BASE, "archive", "templates"),
          os.path.join(BASE, "misc", "downloads")]:
    os.makedirs(d, exist_ok=True)

# ── Resource 1: journal_type_matrix.json ────────────────────────────────────
journal_type_matrix = {
    "chinese": {
        "北大核心": {
            "description": "北京大学《中文核心期刊要目总览》收录期刊",
            "authority": "北京大学图书馆",
            "update_cycle": "每4年",
            "typical_fields": ["理工科", "社科", "医学", "农业"]
        },
        "CSCD": {
            "description": "中国科学引文数据库来源期刊",
            "authority": "中国科学院文献情报中心",
            "update_cycle": "动态",
            "typical_fields": ["自然科学", "工程技术"]
        },
        "科技核心": {
            "description": "中国科技核心期刊（中国科技论文统计源期刊）",
            "authority": "中国科学技术信息研究所",
            "update_cycle": "每年",
            "typical_fields": ["理工科", "医学", "农业", "环境"]
        },
        "普刊": {
            "description": "正式出版但未进入核心目录的期刊",
            "authority": "国家新闻出版署",
            "update_cycle": "N/A",
            "typical_fields": ["全学科"]
        }
    },
    "international": {
        "SCI/SCIE": {
            "description": "Science Citation Index / Expanded，Web of Science核心合集",
            "authority": "Clarivate Analytics",
            "check_url": "https://mjl.clarivate.com/",
            "typical_fields": ["自然科学", "工程", "医学", "环境"]
        },
        "ESCI": {
            "description": "Emerging Sources Citation Index，Web of Science新兴来源",
            "authority": "Clarivate Analytics",
            "check_url": "https://mjl.clarivate.com/",
            "typical_fields": ["跨学科", "新兴领域"]
        },
        "Scopus": {
            "description": "爱思唯尔Scopus数据库来源期刊",
            "authority": "Elsevier",
            "check_url": "https://www.scopus.com/sources",
            "typical_fields": ["全学科"]
        },
        "EI": {
            "description": "Engineering Index Compendex",
            "authority": "Elsevier Engineering Village",
            "check_url": "https://www.engineeringvillage.com/",
            "typical_fields": ["工程", "计算机", "环境工程"]
        },
        "DOAJ": {
            "description": "Directory of Open Access Journals",
            "authority": "DOAJ.org",
            "check_url": "https://doaj.org/",
            "typical_fields": ["全学科OA"]
        }
    }
}
with open(os.path.join(RESOURCES_DIR, "journal_type_matrix.json"), "w", encoding="utf-8") as f:
    json.dump(journal_type_matrix, f, ensure_ascii=False, indent=2)

# ── Resource 2: ad_slots.json ────────────────────────────────────────────────
ad_slots = {
    "slots": [
        {
            "position": "after_overview",
            "label": "服务推荐（广告）",
            "content": "📋 【论文润色 & 投稿辅助】专业学术润色团队，覆盖环境科学、生态学、工程类稿件，提供APC申请指导与语言修改服务。咨询热线：17605205782",
            "disclaimer": "以上为商业服务推荐，与期刊编辑部无关，不代表任何录用承诺。"
        },
        {
            "position": "after_first_group",
            "label": "服务推荐（广告）",
            "content": "🔍 【期刊真伪核验 & 投稿档案整理】帮您核验目标期刊官网真实性、整理投稿所需材料清单，节省80%准备时间。联系我们：17605205782",
            "disclaimer": "以上为商业服务推荐，不构成期刊录用保证。"
        },
        {
            "position": "before_action",
            "label": "服务推荐（广告）",
            "content": "🎯 【一对一投稿顾问服务】根据您的研究方向与文章现状，为您匹配最优投稿策略，提供从选刊到录用全程跟踪支持。热线：17605205782",
            "disclaimer": "广告服务由第三方提供，不代表任何期刊立场，不承诺录用结果。"
        }
    ],
    "default_phone": "17605205782",
    "compliance_note": "所有广告必须使用label字段明确标识，禁止与期刊官网信息混排，禁止使用'包录用'等误导性表达。"
}
with open(os.path.join(RESOURCES_DIR, "ad_slots.json"), "w", encoding="utf-8") as f:
    json.dump(ad_slots, f, ensure_ascii=False, indent=2)

# ── Resource 3: writing_playbooks.md ────────────────────────────────────────
writing_playbooks_content = """# 写作打法库 Writing Playbooks

## 环境科学 / 生态学 / 碳中和方向

### 面向SCI/SCIE期刊（英文）
- **题目**：使用"方法+对象+关键结论"结构，避免超过20词，突出地理/时间范围。
- **摘要**：采用结构化摘要（背景1句→研究问题1句→方法2句→主要结论2句→意义1句），控制在250词以内。
- **引言**：倒三角结构，从全球气候变化宏观背景切入，收窄至区域/机制层面，末段明确研究gap与本文贡献。
- **方法**：数据来源、处理流程、模型参数须可复现，引用近3年同类方法文献≥3篇。
- **结果与讨论**：先结果再讨论，避免在结果节评价意义；讨论节须与已发表文献对话。
- **参考文献**：建议近三年文献占比≥40%，总引用≥30条。
- **常见退稿点**：方法不够新颖、讨论与结论重复、图表不规范、英文语法问题。

### 面向中文核心/CSCD期刊（中文）
- **题目**：控制在20字以内，包含研究对象、方法和主要结论关键词。
- **摘要**：目的→方法→结果→结论四段式，300字以内，关键数据必须出现。
- **引言**：国内研究背景须重点综述，说明本研究在国内的必要性。
- **方法**：数据来源须注明获取渠道，如"采用MODIS遥感数据"需说明分辨率与时段。
- **参考文献**：中文文献≥60%，近五年文献≥50%。
- **常见退稿点**：创新点不明确、国内研究综述不足、数据时效性差。

### 面向ESCI/Scopus期刊（英文）
- **策略**：门槛相对低于SCI，但结构与语言要求同样专业。
- **重点**：强调研究的区域贡献与政策相关性，适合应用型研究。
- **摘要**：150-200词，突出实践价值。

### 面向DOAJ OA期刊（英文/中英双语）
- **策略**：开放获取，传播广，适合政策建议类或综述类文章。
- **注意**：须验证DOAJ收录状态，避免掠夺性OA期刊。
"""
with open(os.path.join(RESOURCES_DIR, "writing_playbooks.md"), "w", encoding="utf-8") as f:
    f.write(writing_playbooks_content)

# ── Resource 4: source_trust_policy.md ──────────────────────────────────────
source_trust_policy_content = """# 来源核验政策 Source Trust Policy

## 中文期刊核验优先级
1. **国家新闻出版署**：https://www.nppa.gov.cn/bsfw/cyjghcpcx/qkan/index.html（最高优先级）
2. **期刊官网 / 主办单位官网**：编辑部公告页面
3. **数据库展示页**（仅补充，不作为唯一真伪依据）

## 国际期刊核验优先级
1. **期刊官网 / Publisher 官方页面**
2. **权威目录**：
   - Web of Science Master Journal List: https://mjl.clarivate.com/
   - Scopus Sources: https://www.scopus.com/sources
   - DOAJ: https://doaj.org/
   - NLM Catalog: https://www.ncbi.nlm.nih.gov/nlmcatalog/
   - Engineering Village: https://www.engineeringvillage.com/
3. **学校图书馆/协会目录**（仅补充）

## 风险信号（必须在风险提示字段中说明）
- 投稿后1周内承诺录用
- 版面费远高于同类期刊（如中文普刊超3000元/版）
- 官网域名与期刊名不一致
- 无主办单位信息或主办单位无法核实
- 数据库页面与期刊官网信息相互矛盾
- 已知被BEALL'S LIST或相关机构标记为掠夺性期刊

## 必填声明
每份建议书必须包含以下免责声明：
"最终投稿入口以期刊官网、主办单位官网、国家/数据库官方页面为准，请用户在投稿前自行核验。"
"""
with open(os.path.join(RESOURCES_DIR, "source_trust_policy.md"), "w", encoding="utf-8") as f:
    f.write(source_trust_policy_content)

# ── Script: render_journal_dossier.py ───────────────────────────────────────
render_script_content = '''#!/usr/bin/env python3
"""
render_journal_dossier.py
Render a structured journal dossier from a candidate JSON file.

Usage:
    python3 render_journal_dossier.py --input <json_file> --output <markdown_file>

Input JSON schema:
{
  "request_summary": "str - 需求归档描述",
  "recommendation_strategy": "str - 推荐策略摘要",
  "journals": [
    {
      "名称": "str",
      "类型/收录": "str",
      "适合主题": "str",
      "为什么推荐": "str",
      "写作打法": "str",
      "投稿路径": "str",
      "核验来源": "str",
      "风险提示": "str",
      "group": "chinese|international"  // optional, used for grouping
    }
  ],
  "action_steps": ["str", ...]
}
"""

import argparse
import json
import sys
import os
from datetime import datetime

REQUIRED_JOURNAL_FIELDS = ["名称", "类型/收录", "适合主题", "为什么推荐", "写作打法", "投稿路径", "核验来源", "风险提示"]

AD_SLOTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "ad_slots.json")


def load_ad_slots():
    try:
        with open(AD_SLOTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not load ad_slots.json: {e}", file=sys.stderr)
        return {"slots": [], "default_phone": "17605205782"}


def validate_journal(j, idx):
    missing = [field for field in REQUIRED_JOURNAL_FIELDS if not j.get(field, "").strip()]
    if missing:
        print(f"[WARN] Journal #{idx+1} ('{j.get('名称','?')}') missing fields: {missing}", file=sys.stderr)
    return missing


def render_ad_block(slot):
    return f"""
---
### {slot['label']}

{slot['content']}

*{slot['disclaimer']}*

---
"""


def render_journal_entry(j, idx):
    lines = [f"#### {idx+1}. {j.get('名称', '（未命名）')}"]
    for field in REQUIRED_JOURNAL_FIELDS:
        val = j.get(field, "待进一步人工核验")
        lines.append(f"- **{field}**：{val}")
    return "\\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Render journal dossier from JSON to Markdown.")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Output Markdown file path")
    args = parser.parse_args()

    # Load input
    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load input JSON: {e}", file=sys.stderr)
        sys.exit(1)

    journals = data.get("journals", [])
    if not journals:
        print("[ERROR] No journals found in input JSON.", file=sys.stderr)
        sys.exit(1)

    if len(journals) < 3:
        print(f"[ERROR] At least 3 journals required, got {len(journals)}.", file=sys.stderr)
        sys.exit(1)

    if len(journals) > 12:
        print(f"[ERROR] At most 12 journals allowed, got {len(journals)}. Truncating to 12.", file=sys.stderr)
        journals = journals[:12]

    # Validate all fields
    all_missing = {}
    for idx, j in enumerate(journals):
        missing = validate_journal(j, idx)
        if missing:
            all_missing[idx] = missing

    ad_data = load_ad_slots()
    slots = {s["position"]: s for s in ad_data.get("slots", [])}

    # Separate chinese vs international
    chinese_journals = [j for j in journals if j.get("group", "").lower() == "chinese"]
    intl_journals = [j for j in journals if j.get("group", "").lower() == "international"]
    other_journals = [j for j in journals if j.get("group", "").lower() not in ("chinese", "international")]

    lines = []
    lines.append(f"# 期刊投稿建议书")
    lines.append(f"*生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    # Section 1
    lines.append("## 一、需求归档")
    lines.append(data.get("request_summary", "（未提供）"))
    lines.append("")

    # Section 2
    lines.append("## 二、推荐摘要")
    lines.append(data.get("recommendation_strategy", "（未提供）"))
    lines.append("")

    # Ad slot: after_overview
    if "after_overview" in slots:
        lines.append(render_ad_block(slots["after_overview"]))

    # Section 3
    lines.append("## 三、候选期刊清单")

    group_counter = 0
    if chinese_journals:
        lines.append("\\n### 中文期刊组")
        for idx, j in enumerate(chinese_journals):
            lines.append(render_journal_entry(j, idx))
            lines.append("")
        group_counter += 1

    # Ad slot: after_first_group (after first group rendered)
    if group_counter >= 1 and "after_first_group" in slots:
        lines.append(render_ad_block(slots["after_first_group"]))

    if intl_journals:
        lines.append("\\n### 国际期刊组")
        for idx, j in enumerate(intl_journals):
            lines.append(render_journal_entry(j, idx))
            lines.append("")

    if other_journals:
        lines.append("\\n### 其他期刊")
        for idx, j in enumerate(other_journals):
            lines.append(render_journal_entry(j, idx))
            lines.append("")

    lines.append("")

    # Section 4: Ad
    lines.append("## 四、服务推荐（广告）")
    for slot in ad_data.get("slots", []):
        lines.append(f"### {slot['label']}")
        lines.append(slot['content'])
        lines.append(f"*{slot['disclaimer']}*")
        lines.append("")

    # Ad slot: before_action
    if "before_action" in slots:
        lines.append(render_ad_block(slots["before_action"]))

    # Section 5
    lines.append("## 五、行动建议")
    action_steps = data.get("action_steps", [])
    if action_steps:
        for step in action_steps:
            lines.append(f"- {step}")
    else:
        lines.append("（未提供行动步骤）")
    lines.append("")

    # Disclaimer (from source_trust_policy)
    lines.append("---")
    lines.append("> **免责声明**：最终投稿入口以期刊官网、主办单位官网、国家/数据库官方页面为准，请用户在投稿前自行核验。")
    lines.append("")

    # Write output
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write("\\n".join(lines))
        print(f"[OK] Dossier written to: {args.output}")
    except Exception as e:
        print(f"[ERROR] Failed to write output: {e}", file=sys.stderr)
        sys.exit(1)

    # Report field issues
    if all_missing:
        print(f"[WARN] {len(all_missing)} journal(s) had missing fields. Check stderr for details.", file=sys.stderr)
        sys.exit(2)  # Non-fatal warning exit

    sys.exit(0)


if __name__ == "__main__":
    main()
'''
with open(os.path.join(SCRIPTS_DIR, "render_journal_dossier.py"), "w", encoding="utf-8") as f:
    f.write(render_script_content)
os.chmod(os.path.join(SCRIPTS_DIR, "render_journal_dossier.py"), 0o755)

# ── Distractor files ─────────────────────────────────────────────────────────

# Researcher's draft abstract (messy, needs journal matching)
draft_abstract = """Title: Carbon Sink Dynamics in Temperate Forest Ecosystems Under Climate Warming Scenarios: 
A Multi-Scale Remote Sensing Analysis

Abstract (Draft - DO NOT SUBMIT YET):
This study investigates the spatial and temporal variations of carbon sink capacity in temperate 
forest ecosystems across northeastern China from 2005-2022, using MODIS NDVI time-series data 
combined with flux tower measurements from 12 eddy covariance stations. We developed a modified 
CASA model that integrates temperature sensitivity parameters (Q10) derived from meta-analysis 
of 89 peer-reviewed studies. Results indicate a significant declining trend in net ecosystem 
productivity (NEP) of -0.23 ± 0.04 gC m⁻² day⁻¹ per decade (p<0.01), which we attribute to 
increased autotrophic respiration under warming conditions. Spatial analysis reveals that forests 
above 500m elevation show greater resilience (β=0.67) compared to lowland forests. These findings 
have important implications for China's 2060 carbon neutrality targets.

Keywords: carbon sink, temperate forest, remote sensing, climate warming, carbon neutrality, MODIS

Author note: I'm a PhD student, need to publish in both Chinese and international journals. 
Budget is limited (max 3000 RMB for Chinese, open to OA for international if <$1500 APC).
Need at least one SCI/SCIE and one Chinese core (北大核心 or CSCD).
Timeline: Need acceptance within 8 months for graduation.
"""
with open(os.path.join(DRAFTS_DIR, "abstract_draft_v3.txt"), "w", encoding="utf-8") as f:
    f.write(draft_abstract)

# Researcher's notes (messy, informal)
researcher_notes = """Meeting notes 2024-03-15:
- Prof. Zhang said try "Global Change Biology" first - impact factor is high
- Also mentioned "Acta Ecologica Sinica" (生态学报) might be good for Chinese version
- Someone mentioned "Carbon Balance and Management" on DOAJ
- BEWARE: there's a fake journal called "Journal of Forest Carbon" that 
  looks legit but is on predatory list
- Check if "Forest Ecosystems" (Springer) is still in ESCI or upgraded to SCIE
- For Chinese: "应用生态学报" is CSCD, check if still active
- Budget constraint: 3000 CNY max for Chinese, OA acceptable if under USD 1500
- MUST get at least 1 SCIE + 1 Chinese core (北大核心 or CSCD minimum)
- Graduation deadline forces 8-month acceptance window
"""
with open(os.path.join(NOTES_DIR, "meeting_notes_march.txt"), "w", encoding="utf-8") as f:
    f.write(researcher_notes)

# Old, outdated journal list (distractor)
old_journal_list = """OLD LIST - 2019 - MAY BE OUTDATED
1. Ecological Indicators - SCI (check current status)
2. 生态学杂志 - 科技核心
3. Environmental Science & Technology - SCI Top
4. 环境科学学报 - 北大核心
5. Science of Total Environment - SCI
6. 中国环境科学 - CSCD
NOTE: Some of these may have changed indexing status. Do not use without verification.
"""
with open(os.path.join(ARCHIVE_DIR, "journal_list_2019.txt"), "w", encoding="utf-8") as f:
    f.write(old_journal_list)

# Fake/misleading submission guide (distractor)
fake_guide = """Quick Submission Guide (UNOFFICIAL - crowdsourced)
Forest Carbon Journal: submit to editor@forest-carbon-journal.net (WARNING: VERIFY THIS)
Global Ecology: https://globalecol-submit.net (mirror site? unverified)
NOTE: This document was created by a grad student and has NOT been verified.
"""
with open(os.path.join(ARCHIVE_DIR, "unofficial_submission_guide.txt"), "w", encoding="utf-8") as f:
    f.write(fake_guide)

# Archive templates (distractors)
for i, name in enumerate(["cover_letter_template.docx.txt", "response_to_reviewers.txt", 
                            "author_checklist_2021.txt"]):
    with open(os.path.join(BASE, "archive", "templates", name), "w") as f:
        f.write(f"Template file {i+1} - placeholder content for {name}\n")

# Misc downloads (distractors)
for fname in ["wos_search_results_export.csv", "scopus_abstract_download.ris", 
              "cnki_batch_export.txt"]:
    with open(os.path.join(BASE, "misc", "downloads", fname), "w", encoding="utf-8") as f:
        f.write(f"# Placeholder export file: {fname}\n# This is search result data, not a journal list.\n")

# Config stub (distractor)
with open(os.path.join(BASE, "misc", "search_config.json"), "w") as f:
    json.dump({"last_search": "carbon sink forest", "date": "2024-03-20", "results": 142}, f)

# Empty requirements note (distractor)
with open(os.path.join(BASE, "notes", "requirements_raw.txt"), "w", encoding="utf-8") as f:
    f.write("""Research profile:
Direction: Carbon sink dynamics, temperate forests, remote sensing
Article type: Original research
Language: Need both Chinese and English versions
Target: At least 1 SCIE + 1 Chinese core journal
Budget: CNY 3000 max Chinese, USD 1500 max APC for international
OA: Acceptable for international
Deadline: 8 months for graduation
Institution: Northeast China university
""")

print("Workspace generated successfully.")
print(f"Skill dir: {SKILL_DIR}")
print(f"Scripts: {SCRIPTS_DIR}")
print(f"Resources: {RESOURCES_DIR}")