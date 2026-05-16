#!/usr/bin/env python3
"""
Generate the sandbox workspace for the official-document task.
Creates a realistic messy directory structure with distractor files
and a raw, unformatted input that the agent must process.
"""
import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "drafts/old_versions",
    "drafts/templates",
    "archive/2023/q1",
    "archive/2023/q4",
    "archive/2024/q1",
    "reports/internal",
    "reports/external",
    "meeting_notes",
    "correspondence/incoming",
    "correspondence/outgoing",
    "resources/fonts",
    "resources/logos",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "drafts/old_versions/water_notice_v1.txt": """\
关于加强水资源保护的通知（草稿一）
各单位：
这是第一版草稿，格式不规范，仅供参考。
严禁使用本版本。
""",
    "drafts/old_versions/water_notice_v2.txt": """\
关于加强水资源保护的通知（草稿二）
××水务局发〔2024〕5号
内容待完善...
""",
    "drafts/templates/generic_notice.txt": """\
[标题]

[文号]

[主送机关]：

[正文]

[附件]

[落款机关]
[日期]
""",
    "drafts/templates/report_template.md": """\
# 报告模板

一、基本情况

（一）概述

正文内容...

二、存在问题

三、下一步工作
""",
    "archive/2023/q1/env_notice_2023.docx.placeholder": "binary docx placeholder - do not use",
    "archive/2023/q4/year_end_report.txt": """\
2023年度水资源管理工作总结
全年完成各项目标任务...
""",
    "archive/2024/q1/q1_summary.txt": """\
2024年第一季度工作小结
水质达标率98.5%
""",
    "reports/internal/water_quality_data.csv": """\
month,location,ph,turbidity,status
2024-01,东区,7.2,0.8,达标
2024-01,西区,7.5,1.2,达标
2024-02,东区,6.9,0.9,达标
2024-02,南区,8.1,2.1,超标
""",
    "reports/external/press_release_draft.txt": """\
新闻稿（草稿）
我市水资源保护工作取得积极进展...
（本文件非公文格式，不可直接使用）
""",
    "meeting_notes/2024_03_15_water_meeting.txt": """\
会议纪要
时间：2024年3月15日
地点：第三会议室
议题：水资源保护工作部署
出席人员：局长、各科室负责人
主要内容：
1. 传达上级精神
2. 部署近期工作
3. 研究具体措施
""",
    "correspondence/incoming/ministry_directive_2024.txt": """\
水利部关于印发水资源保护指导意见的通知
（摘要）
各省级水务主管部门需在2024年6月前完成...
""",
    "correspondence/outgoing/reply_to_district_202403.txt": """\
关于××区水资源管理问题的复函
已收悉贵区来函，现答复如下：...
""",
    "resources/fonts/font_list.txt": """\
系统已安装字体清单：
- 仿宋 (FangSong)
- 黑体 (HeiTi / SimHei)  
- 楷体 (KaiTi)
- 宋体 (SongTi / SimSun)
注：方正小标宋需单独安装
""",
    "resources/logos/bureau_seal_info.txt": """\
单位公章信息（仅供参考）
单位名称：××市水务局
公章编号：XXXX-2019-001
""",
}

for rel_path, content in distractor_files.items():
    fp = WORKSPACE / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")

# ── THE ACTUAL TASK INPUT ────────────────────────────────────────────────────
# A raw, messy Markdown file that needs to be converted to an official document.
# It has correct GB/T 9704-2012 structure but the agent must identify it,
# and run the conversion tool properly.

task_input_md = """\
# 关于加强水资源保护和节约用水工作的通知

××水务局发〔2024〕18号

各区县水务局、各直属单位：

为深入贯彻落实习近平生态文明思想，切实加强全市水资源保护和节约用水管理工作，根据《中华人民共和国水法》及上级有关部署，现就有关事项通知如下。

一、总体要求

（一）指导思想

坚持以习近平新时代中国特色社会主义思想为指导，以最严格水资源管理制度为抓手，统筹推进水资源节约、保护和合理开发利用，为全市高质量发展提供坚实的水资源保障。

（二）基本原则

坚持节水优先、空间均衡、系统治理、两手发力的治水方针，突出重点、分类施策、协同推进。

（三）工作目标

到2024年底，全市万元GDP用水量较上年下降3%以上，城市供水管网漏损率控制在9%以内，农业灌溉水有效利用系数达到0.58以上。

二、重点工作任务

（一）强化水资源刚性约束

1.严格用水总量控制

各区县要严格落实用水总量控制指标，对接近或达到用水总量控制红线的地区，要暂停审批新增取水许可。

2.完善用水定额管理

（1）修订完善高耗水行业用水定额标准，建立健全定额动态调整机制。

（2）推行用水计划管理，对年用水量超过10万立方米的工业企业和年用水量超过5万立方米的公共机构实行重点监管。

（二）推进节水型社会建设

1.深化农业节水增效

全面推广高效节水灌溉技术，新增高效节水灌溉面积5万亩以上。加强灌区续建配套与节水改造，提升农田水利设施水平。

2.加快工业节水减排

（1）鼓励企业开展水平衡测试，推进企业内部循环用水和废水综合利用。

（2）新建、改建、扩建项目须配套建设节水设施，实行节水设施与主体工程同时设计、同时施工、同时投产。

3.提升城镇节水水平

加快推进城市供水管网改造，降低供水管网漏损率。推广使用节水型器具，公共机构节水型器具使用率达到100%。

（三）加大水资源保护力度

1.严格水功能区管理

加强饮用水水源地保护，开展水源地安全保障达标建设，确保城市集中式饮用水水源地水质达标率100%。

2.推进河湖生态保护修复

（1）全面落实河湖长制，强化河湖日常巡查管理，及时清理违法建筑物、障碍物和污染物。

（2）开展河湖生态补水，合理安排生态基流，保障河湖基本生态用水需求。

三、保障措施

（一）加强组织领导

各区县要将水资源保护和节约用水工作列入重要议事日程，主要领导亲自部署、分管领导具体抓落实，形成一级抓一级、层层抓落实的工作格局。

（二）强化资金保障

统筹整合相关专项资金，加大对水资源保护和节水工程建设的支持力度。积极引导社会资本参与节水工程建设和运营，拓宽资金筹集渠道。

（三）严格监督考核

将水资源保护和节约用水工作纳入年度综合考核体系，对成绩突出的单位和个人予以表彰奖励，对工作不力、完不成目标任务的严肃追责问责。

（此件公开发布）

××市水务局
2024年4月1日
"""

task_input_path = WORKSPACE / "water_resource_notice_raw.md"
task_input_path.write_text(task_input_md, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Task input file: {task_input_path}")
print(f"Total distractor files: {len(distractor_files)}")