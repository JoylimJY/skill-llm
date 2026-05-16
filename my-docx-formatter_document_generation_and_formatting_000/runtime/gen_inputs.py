import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Build a realistic, deeply nested distractor directory structure ──────

distractor_dirs = [
    "archive/2024/reports",
    "archive/2024/drafts",
    "archive/2023/summaries",
    "internal/hr/attendance",
    "internal/hr/performance",
    "internal/finance/budget",
    "internal/finance/reimbursement",
    "projects/grain_subsidy/docs",
    "projects/rural_land/data",
    "projects/livestock/reports",
    "temp/staging",
    "temp/backup",
    "logs",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files with plausible content
distractors = {
    "archive/2024/reports/q3_summary.txt": "2024年第三季度农业生产情况汇报（草稿）\n本季度粮食产量同比增长5.2%...",
    "archive/2024/reports/policy_notice.txt": "关于加强农村土地承包经营权流转管理的通知\n各乡镇农业农村办公室...",
    "archive/2024/drafts/speech_draft.txt": "在全市农业工作会议上的讲话（初稿）\n同志们...",
    "archive/2023/summaries/annual_work.txt": "2023年度工作总结\n一、主要工作成效\n二、存在问题\n三、下一步打算",
    "internal/hr/attendance/jan_2025.csv": "姓名,出勤天数,请假天数\n张三,22,0\n李四,20,2",
    "internal/hr/performance/kpi_2024.json": json.dumps({"dept": "农业局", "year": 2024, "score": 92}, ensure_ascii=False),
    "internal/finance/budget/2025_plan.txt": "2025年度部门预算方案\n运行经费：120万元\n项目经费：350万元",
    "internal/finance/reimbursement/march.xlsx.txt": "（Excel文件，无法直接查看）",
    "projects/grain_subsidy/docs/procedure.md": "# 粮食补贴申报流程\n## 申报条件\n## 所需材料\n## 审核程序",
    "projects/rural_land/data/parcels.csv": "地块编号,面积(亩),承包人\nLD001,12.5,王五\nLD002,8.3,赵六",
    "projects/livestock/reports/cattle_census.txt": "全县牲畜普查结果\n牛：12450头\n猪：38200头",
    "temp/staging/old_format_test.docx.bak": "（备份文件）",
    "temp/backup/config_backup.json": json.dumps({"backup_date": "2025-01-15", "version": "1.2.3"}),
    "logs/system.log": "2025-03-01 09:00:01 INFO System started\n2025-03-01 09:00:05 INFO Document service ready",
}
for path, content in distractors.items():
    full = workspace / path
    full.write_text(content, encoding="utf-8")

# ── 2. Create the PROBLEM: raw unstructured brief that agent must convert ───
# This is the "messy input" — a plain text outline with no formatting whatsoever.
# The agent must author a proper Markdown file and then run the tool.

raw_brief = """县农业农村局2025年度工作总结材料（素材）

主标题：北阳县农业农村局2025年度工作总结

署名机构：北阳县农业农村局
日期：2025年12月31日

------内容提纲------

一级标题1：全面推进粮食安全生产
  二级标题1.1：落实耕地保护制度
    正文：全县耕地总面积稳定在42万亩以上，完成粮食播种面积38.6万亩，粮食总产量达到19.2万吨，同比增长3.1%。严格落实耕地占补平衡制度，全年补充耕地面积1200亩，整改撂荒地3500亩。
  二级标题1.2：强化农业科技支撑
    正文：全年推广优质粮食新品种12个，建设高标准农田示范区2万亩。组织农技培训班46期，培训农民技术员1800余人次。农业科技贡献率达到62%，较上年提高2个百分点。
    三级（行内）内容：1. 技术推广成效：示范带动辐射面积超过15万亩，亩均增产粮食50公斤以上。

一级标题2：扎实推进乡村振兴战略
  二级标题2.1：巩固拓展脱贫攻坚成果
    正文：持续开展防返贫动态监测，全县监测对象1246户3891人全部落实帮扶措施。脱贫人口人均纯收入达到16820元，同比增长12.4%，高于全市平均水平。
  二级标题2.2：推进农村人居环境整治
    正文：完成农村厕所改造8600户，累计完成率达到78%。创建美丽宜居村庄示范点12个，农村生活垃圾无害化处理率达到95%以上。
    三级（行内）内容：1. 整治重点：重点推进村庄清洁行动，农村面貌得到显著改善，群众满意度持续提升。

一级标题3：存在的主要问题和下一步打算
  二级标题3.1：存在的主要问题
    正文：一是农业基础设施仍然薄弱，部分农田水利设施老化失修，抗灾减灾能力有待提升。二是农业经营主体规模化程度不高，家庭农场和农民合作社整体实力偏弱。三是农村劳动力持续向城市转移，农业从业人员老龄化问题较为突出。
  二级标题3.2：下一步工作打算
    正文：坚持以习近平新时代中国特色社会主义思想为指导，全面贯彻党的二十大精神，重点抓好高标准农田建设、农业产业化发展和乡村建设行动三项重点工作，确保全年农业农村各项目标任务圆满完成。
"""

(workspace / "work_summary_brief.txt").write_text(raw_brief, encoding="utf-8")

# ── 3. Also place a badly-formatted "attempt" markdown that is WRONG ────────
# This traps agents that just use any markdown without reading the spec.
bad_md = """# 北阳县农业农村局2025年度工作总结

## 第一部分 全面推进粮食安全生产

#### 耕地保护（wrong level）

全县耕地总面积稳定在42万亩以上。

## 第二部分 乡村振兴战略

body text here.
"""
(workspace / "bad_attempt.md").write_text(bad_md, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")