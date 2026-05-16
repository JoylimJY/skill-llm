import os
import random

random.seed(42)

# Create a deeply nested directory structure
dirs = [
    "workspace/researcher_profile",
    "workspace/researcher_profile/publications",
    "workspace/researcher_profile/cv_drafts",
    "workspace/researcher_profile/media_coverage",
    "workspace/researcher_profile/collaborators",
    "workspace/institute_data",
    "workspace/institute_data/lab_overview",
    "workspace/institute_data/projects",
    "workspace/institute_data/equipment",
    "workspace/old_brand_attempts",
    "workspace/old_brand_attempts/2021_draft",
    "workspace/old_brand_attempts/2022_ideas",
    "workspace/reference_materials",
    "workspace/reference_materials/competitors",
    "workspace/reference_materials/industry_reports",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Main researcher profile - raw messy data (the primary input)
researcher_profile = """姓名: 林志远 (Zhiyuan Lin)
出生年份: 1988
当前职位: 副研究员
机构: 中国科学院物理研究所 固态能源材料实验室
所在城市: 北京

== 教育背景 ==
- 博士: 清华大学 材料科学与工程 2016年毕业
- 硕士: 北京大学 凝聚态物理 2012年毕业  
- 本科: 南京大学 物理学 2010年毕业

== 研究方向 (主要) ==
主攻: 固态电解质材料, 全固态锂电池界面工程
次要: 钠离子电池, 储能材料表征

== 学术成果 (粗略统计, 可能有误) ==
- 近5年发表论文: 大概28篇左右 (SCI论文, 主要在能源材料方向)
- 顶刊论文: Nature Energy 1篇(2022), Advanced Energy Materials 3篇, ACS Energy Letters 2篇, Joule 1篇(2023)
- 总被引次数: 约1850次 (Google Scholar, 2024年初数据)
- h-index: 23 (比较满意但希望继续提升)
- 授权专利: 8项 (6项国内, 2项PCT国际专利)
- 高被引论文 (ESI): 3篇

== 学术网络现状 ==
- 合作者: 与MIT合作(Prof. Yet-Ming Chiang组), 与斯坦福能源研究所有合作
- 国内合作: 北理工, 厦门大学, 宁德时代研究院
- 担任审稿人: Journal of Materials Chemistry A, ACS Nano, Electrochimica Acta
- 学术组织: 中国电化学学会会员, 中国材料学会青年委员
- 研究生: 已培养博士生3名(2名已毕业), 在读硕士生4名, 博士生2名
- 学术奖项: 2021年中国电化学学会青年奖, 2023年北京市自然科学奖二等奖

== 产业连接 (目前很薄弱) ==
- 企业合作: 与宁德时代有一个横向课题(2022-2024), 与比亚迪研究院有非正式联系
- 技术转让: 暂无正式技术转让
- 企业顾问: 目前没有
- 行业演讲: 只参加过学术会议, 没有参加过产业峰会
- 媒体采访: 中国科学报报道过一次(2023年), 没有其他媒体经验

== 数字化存在 (基本空白) ==
- Google Scholar: 有个人主页, 基本信息完整
- ResearchGate: 有账号但很少更新
- ORCID: 有档案
- 微信公众号: 没有
- 知乎: 有账号但只发过2篇文章 (2019年, 已经很久没更新)
- LinkedIn: 没有正式运营
- Twitter/X: 没有账号
- 头条号: 没有

== 个人特质描述 (自述) ==
我做科研比较严谨, 数据说话, 不喜欢夸夸其谈。比较内向, 不太擅长社交。
但我对固态电池的发展非常有热情, 认为这是未来10年最重要的能源技术之一。
我觉得科研成果应该走出实验室, 但不知道怎么做。
在学生看来我是一个负责任的导师, 会认真指导学生写作和实验设计。

== 近期目标 (模糊想法) ==
- 想在产业界建立一些影响力, 希望以后能参与行业标准制定
- 想在固态电池这个赛道上成为被行业认可的专家
- 计划在未来两三年内考虑科研创业可能性
- 希望能有更多企业来主动找我合作

== 最近的研究亮点 ==
2023年在Joule发表的研究: 开发了一种新型氧化物固态电解质涂层技术, 
将全固态锂电池的界面阻抗降低了78%, 循环寿命提升至800次以上, 
比现有技术提升约40%. 这个工作引起了宁德时代内部研究人员关注。

== 资源限制 ==
- 时间: 科研任务繁重, 每周能用于品牌建设的时间不超过3-4小时
- 经费: 没有专项品牌建设经费, 只能用免费或低成本工具
- 助手: 可以让研究生协助部分内容创作
"""

with open("workspace/researcher_profile/lin_zhiyuan_raw_profile.txt", "w", encoding="utf-8") as f:
    f.write(researcher_profile)

# Distractor files
distractor_pubs = """Publication list (incomplete draft):
1. Lin Z, et al. "Interface engineering of LLZO/Li metal interface..." Nature Energy 2022, 7, 999-1008.
2. Lin Z, Wang Y, et al. "Na-ion..." Advanced Energy Materials 2021.
3. [MISSING DOI - check with secretary]
4. Lin Z, et al. Joule 2023 - solid electrolyte coating...
5. [需要补充2020年的那篇ACS能源]
Note: Thomson Reuters profile might be outdated, use GS data
"""
with open("workspace/researcher_profile/publications/pub_list_draft_v3.txt", "w", encoding="utf-8") as f:
    f.write(distractor_pubs)

distractor_cv = """CV草稿 v7 (2024-01-15)
林志远副研究员
[基本信息见HR系统]
教育: 清华博士...
工作经历: 2016-2019 博后, 2019-至今 副研究员
[待补充: 2023年的奖项信息]
[待李秘书确认: 专利数量]
"""
with open("workspace/researcher_profile/cv_drafts/cv_v7_incomplete.txt", "w", encoding="utf-8") as f:
    f.write(distractor_cv)

distractor_media = """媒体报道记录:
2023-06-12: 中国科学报 《固态电池研究新进展》 - 林志远接受采访
  链接: [已失效]
  摘要: 简短介绍了Joule论文研究
2021-09-XX: 所内简报 (仅内部传播)
"""
with open("workspace/researcher_profile/media_coverage/media_log.txt", "w", encoding="utf-8") as f:
    f.write(distractor_media)

distractor_collab = """合作者联系方式 (内部文件):
- Prof. Yet-Ming Chiang (MIT): chiang@mit.edu [已通过合作论文建立关系]
- 北理工 陈教授: [电话略]
- 宁德时代 王博士: [内部联系人, 不对外公开]
- 厦门大学 固态电池课题组: [合作申请中]
"""
with open("workspace/researcher_profile/collaborators/contact_list.txt", "w", encoding="utf-8") as f:
    f.write(distractor_collab)

lab_overview = """固态能源材料实验室简介
成立时间: 2018年
主要设备: XRD, TEM, EIS测试平台, 手套箱...
在研项目: 国家重点研发计划, 自然科学基金重点项目
人员: PI 1名(研究员), 副研究员2名(包括林志远), 博士生6名, 硕士生8名
"""
with open("workspace/institute_data/lab_overview/lab_intro.txt", "w", encoding="utf-8") as f:
    f.write(lab_overview)

projects_note = """在研项目清单 (2024):
1. 国家重点研发: 固态电解质界面工程 (2022-2025, 负责人: 林志远)
2. 自然科学基金重点: 钠离子储能材料 (2021-2024, 参与)
3. 横向: 宁德时代 固态电池界面表征 (2022-2024)
4. 北京市科委: 固态电池快充技术 (2023-2026, 子课题负责人)
"""
with open("workspace/institute_data/projects/project_list_2024.txt", "w", encoding="utf-8") as f:
    f.write(projects_note)

equipment_note = """实验室设备台账 (仅供内部参考)
[大型仪器清单略]
接触角测试仪, 电化学工作站8台, 原位TEM...
"""
with open("workspace/institute_data/equipment/equipment_inventory.txt", "w", encoding="utf-8") as f:
    f.write(equipment_note)

old_draft_2021 = """2021年品牌想法草稿 (废弃)
想开个微信公众号叫"固态电池前沿"?
但是感觉没时间...
或者在知乎写专栏?
放弃了
"""
with open("workspace/old_brand_attempts/2021_draft/ideas_2021.txt", "w", encoding="utf-8") as f:
    f.write(old_draft_2021)

old_draft_2022 = """2022年记录:
听说某某教授在B站做科普很火, 要不要试试?
问了学生, 他们说可以帮忙剪辑视频
但是录视频太费时间, 暂时搁置
Note: 宁德时代的王博士建议我在LinkedIn上活跃一些
"""
with open("workspace/old_brand_attempts/2022_ideas/notes_2022.txt", "w", encoding="utf-8") as f:
    f.write(old_draft_2022)

competitor_note = """同方向研究者品牌分析 (粗略观察):
张XX (北京大学): 微信公众号10万+粉丝, 经常被DeepTech采访, 担任多家企业顾问
王XX (中科院化学所): LinkedIn活跃, Nature综述高被引, 行业会议常见嘉宾
陈XX (斯坦福归国): 知乎大V, 被红杉资本聘为LP专家顾问, 创业了
"""
with open("workspace/reference_materials/competitors/competitor_analysis_rough.txt", "w", encoding="utf-8") as f:
    f.write(competitor_note)

industry_report_note = """固态电池行业2024年报告摘要 (截取):
- 全球固态电池市场预计2030年达到XX亿
- 中国企业: 宁德时代, 比亚迪, 国轩高科均有布局
- 技术路线争议: 氧化物vs硫化物vs聚合物
- 产业化瓶颈: 界面阻抗, 规模化生产, 成本控制
- 关键意见领袖(KOL): 目前学术界KOL与产业界对话不足
"""
with open("workspace/reference_materials/industry_reports/solid_state_battery_2024.txt", "w", encoding="utf-8") as f:
    f.write(industry_report_note)

# A deliberately incomplete/wrong old brand attempt that agent should NOT reuse
wrong_canvas = """旧版定位尝试 (错误的, 勿用):
我是固态电池研究者
目标: 发更多论文
渠道: 随便
[这个文件是错误示例, 格式完全不对]
"""
with open("workspace/old_brand_attempts/2022_ideas/wrong_brand_canvas_DRAFT.txt", "w", encoding="utf-8") as f:
    f.write(wrong_canvas)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("workspace"):
    for f in files:
        print(f"  {os.path.join(root, f)}")