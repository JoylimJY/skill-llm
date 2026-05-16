import os
import random

random.seed(42)

# Create a realistic workspace with distractor files
os.makedirs("/workspace/career_docs", exist_ok=True)
os.makedirs("/workspace/career_docs/old_resumes", exist_ok=True)
os.makedirs("/workspace/career_docs/job_search", exist_ok=True)
os.makedirs("/workspace/career_docs/job_search/target_companies", exist_ok=True)
os.makedirs("/workspace/career_docs/notes", exist_ok=True)
os.makedirs("/workspace/career_docs/references", exist_ok=True)
os.makedirs("/workspace/templates", exist_ok=True)
os.makedirs("/workspace/misc", exist_ok=True)

# Distractor file 1: old messy resume
with open("/workspace/career_docs/old_resumes/resume_2022_v3_FINAL.txt", "w", encoding="utf-8") as f:
    f.write("""张伟 - 简历 (2022版)
联系方式：zhangwei@email.com

工作经历：
2019-2022 字节跳动 数据工程师
- 负责数据管道开发
- 参与ETL工作
- 做了一些数据质量的东西
- 配合业务方需求

2017-2019 猎豹移动 初级数据工程师
- 负责日常数据报表
- 写SQL查询

技能：Python, SQL, Spark, Hadoop

自我评价：本人认真负责，积极主动，具有良好的团队合作精神，能够承受工作压力。
""")

# Distractor file 2: another old resume version
with open("/workspace/career_docs/old_resumes/resume_2021_draft.txt", "w", encoding="utf-8") as f:
    f.write("""旧版本 - 请勿使用
这个版本已经过时了
""")

# Distractor file 3: random notes
with open("/workspace/career_docs/notes/interview_notes.txt", "w", encoding="utf-8") as f:
    f.write("""面试笔记 - 乱记的东西
字节跳动面试感觉还好
阿里技术面比较难
美团HR很友善
面试问了很多系统设计的题目
要复习一下分布式系统
""")

# Distractor file 4: salary research
with open("/workspace/career_docs/notes/salary_research.txt", "w", encoding="utf-8") as f:
    f.write("""薪资调研乱记
P6大概多少？感觉40-60w？
阿里P7应该更高
听说腾讯T3.2差不多
不确定，需要再查一下脉脉
""")

# Distractor file 5: company research notes
with open("/workspace/career_docs/job_search/target_companies/bytedance_notes.txt", "w", encoding="utf-8") as f:
    f.write("""字节跳动调研
团队规模大
技术栈：Flink, Kafka, Spark
加班情况：听说很严重
大小周好像取消了？
""")

# Distractor file 6: misc template from internet
with open("/workspace/templates/generic_cover_letter_template.txt", "w", encoding="utf-8") as f:
    f.write("""通用求职信模板（网上找的，格式不一定对）
尊敬的HR：
    您好，我叫XXX，对贵公司的XX职位很感兴趣...
    [自我介绍]
    [工作经历]
    [为什么选择贵公司]
期待您的回复
""")

# Distractor file 7: random bookmark list
with open("/workspace/misc/useful_links.txt", "w", encoding="utf-8") as f:
    f.write("""有用的链接（书签备份）
LinkedIn个人主页
脉脉主页链接
Boss直聘收藏的JD
拉勾上感兴趣的职位
""")

# Distractor file 8: coding practice notes
with open("/workspace/misc/leetcode_notes.txt", "w", encoding="utf-8") as f:
    f.write("""LeetCode刷题记录
已完成：200题
需要复习：动态规划、图论
最近做的题：
- 两数之和
- 最长公共子序列
""")

# Distractor file 9: old networking contact list
with open("/workspace/career_docs/references/contacts.txt", "w", encoding="utf-8") as f:
    f.write("""联系人列表（乱的）
李明 - 阿里 - 数据工程师 - 认识了3年
王芳 - 腾讯HR - 在某活动认识
陈刚 - 美团 - 前同事
赵磊 - 字节 - 朋友介绍的
""")

# Distractor file 10: random to-do list
with open("/workspace/career_docs/job_search/todo.txt", "w", encoding="utf-8") as f:
    f.write("""求职待办事项
[ ] 更新简历
[ ] 更新脉脉主页
[ ] 联系前同事
[ ] 准备面试题目
[ ] 研究目标公司
[ ] 谈薪资准备
""")

# ============================================================
# THE ACTUAL PROBLEM FILES
# ============================================================

# Key input file 1: Raw career background (messy, vague, needs STAR transformation)
with open("/workspace/career_docs/career_background_raw.txt", "w", encoding="utf-8") as f:
    f.write("""【个人基本信息】
姓名：张伟
当前职位：高级数据工程师
当前公司：某中型互联网公司（成立5年，员工500人）
工作年限：7年
目标职位：字节跳动 / 阿里巴巴 数据工程师（高级/资深）
当前薪资：35万/年（税前）
期望薪资范围：大概45-55万左右？不确定怎么谈

【教育背景】
985高校 计算机科学与技术 本科（2014-2018）

【技能标签候选（乱写的，太多了需要筛选）】
Python, SQL, Spark, Flink, Kafka, Hadoop, Hive, Airflow, 数据治理, ETL开发, 
实时计算, 离线数据仓库, 数据质量, 团队管理, 跨部门协作, 项目管理, 
Excel, PPT, Linux, Docker, Kubernetes, 机器学习基础, 数据可视化,
增长数据分析, 用户行为分析, A/B测试

【工作经历（需要美化，目前写法太平）】

--- 经历1：某中型互联网公司（2021年至今）高级数据工程师 ---
工作内容描述（乱写的）：
- 管了一个数据团队，做了很多数据相关的工作
- 我们数据仓库之前很乱，我做了一些治理的工作
- 带着团队做了实时数据的改造，之前都是T+1的
- 日常还要和业务方沟通需求，推动一些数据项目落地
背景信息补充（凌乱的备注）：
  * 团队规模：我管了6个人
  * 数据仓库改造：之前有大概300多张脏表，数据不一致、口径打架，
    业务方经常吵架因为数据对不上。我主导了这个数据治理项目，
    大概搞了8个月，最后把表整理到了80张左右，建立了统一指标体系，
    业务方的数据需求响应时间从平均3天降到了不到1天。
  * 实时化改造：公司有个核心业务报表，之前是每天早上跑批，现在做成了
    实时的，延迟从T+1变成了分钟级别（大概5分钟内），这个改造让运营团队
    能更快做决策，感觉GMV有提升但是没有精确数字，大概说提升了10-15%？
    
--- 经历2：上家公司XYZ科技（2018-2021）数据工程师 ---
工作内容描述：
- 负责数据开发工作
- 参与了数据平台建设
- 写了很多数据pipeline
背景信息补充：
  * 从零开始搭了一个数据平台，之前公司没有统一的数据基础设施
  * 完成后公司数据研发效率提升了很多，支撑了快速增长的业务
  * 数据平台上线后，数据研发人效提升大约60%，支持了后续业务从100万日活
    增长到800万日活（那个阶段大概18个月内）

【目标JD信息（想投的职位）】
职位：字节跳动 资深数据工程师
核心要求：
- 熟悉大数据生态（Spark/Flink/Kafka）
- 有数据仓库架构设计经验
- 有实时计算项目经验
- 有跨团队协作和影响力
- 有数据治理或数据平台建设经验

【想在脉脉上联系的人】
目标联系人：王建国，字节跳动 数据基础设施团队负责人
情况：在脉脉上发现他在招数据工程师，想请求内推
我们没有直接认识，只是在一次线上技术分享看到过他

【个人希望达成的目标】
1. 更新脉脉个人主页，让自己看起来更专业，吸引猎头和内推
2. 把工作经历改写成有说服力的格式
3. 给王建国发送一条内推请求消息
4. 了解在脉脉上发哪类内容效果最好，以及什么时候发
""")

# Key input file 2: Target JD details
with open("/workspace/career_docs/job_search/target_jd_bytedance.txt", "w", encoding="utf-8") as f:
    f.write("""职位名称：字节跳动 资深数据工程师（数据基础设施方向）
部门：数据平台部
地点：北京

职位职责：
1. 负责公司核心数据仓库的架构设计与持续优化
2. 主导大规模数据治理项目，提升数据质量与一致性
3. 开发和维护高可用实时数据处理系统（Flink/Kafka）
4. 跨团队协作推动数据标准化落地
5. 指导初中级工程师，提升团队整体技术能力

任职要求：
1. 5年以上数据工程经验，有大厂或高增长公司背景优先
2. 精通Spark、Flink、Kafka、Hive等大数据技术栈
3. 有主导过数据仓库重构或数据治理项目经验
4. 有实时计算系统设计和优化经验
5. 良好的沟通能力和跨部门推动力
6. 本科及以上学历，计算机相关专业

薪资范围：45-70万/年（不含期权）
招聘联系人：王建国（数据基础设施团队负责人）
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs, files in os.walk("/workspace"):
    for file in files:
        print(f"  {os.path.join(root, file)}")