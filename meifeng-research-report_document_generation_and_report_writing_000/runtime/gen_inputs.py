import os
import random

random.seed(42)

# Create directory structure
dirs = [
    "/workspace/project_inputs/policy_docs",
    "/workspace/project_inputs/survey_data",
    "/workspace/project_inputs/references",
    "/workspace/project_inputs/drafts",
    "/workspace/references",
    "/workspace/archive/2023",
    "/workspace/archive/2024",
    "/workspace/templates",
    "/workspace/outputs",
    "/workspace/tools",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ============================================================
# DISTRACTOR FILES (10+ irrelevant files)
# ============================================================

with open("/workspace/archive/2023/old_report_draft.txt", "w", encoding="utf-8") as f:
    f.write("（草稿，已废弃）\n2023年某省公司人力资源工作总结\n本文件已作废，请勿使用。\n")

with open("/workspace/archive/2024/meeting_minutes_0318.txt", "w", encoding="utf-8") as f:
    f.write("2024年3月18日工作例会纪要\n参会人员：张三、李四、王五\n主要议题：无关事项讨论\n")

with open("/workspace/templates/generic_template.txt", "w", encoding="utf-8") as f:
    f.write("通用模板文件\n此模板不适用于本项目。\n格式要求：另见相关规范文件。\n")

with open("/workspace/templates/font_list.txt", "w", encoding="utf-8") as f:
    f.write("备用字体清单（非正式）\nArial, Times New Roman, Calibri\n注意：此为英文字体清单，中文项目请勿使用。\n")

with open("/workspace/tools/data_cleaner.py", "w", encoding="utf-8") as f:
    f.write("# 数据清洗工具（与本报告无关）\nprint('cleaning data...')\n")

with open("/workspace/tools/chart_gen.py", "w", encoding="utf-8") as f:
    f.write("# 图表生成脚本（本次报告不需要图表）\nprint('generating charts...')\n")

with open("/workspace/archive/2023/salary_data_raw.csv", "w", encoding="utf-8") as f:
    f.write("year,company,avg_salary\n2020,A公司,80000\n2021,A公司,85000\n2022,A公司,88000\n")

with open("/workspace/project_inputs/drafts/abandoned_outline_v1.txt", "w", encoding="utf-8") as f:
    f.write("废弃大纲（第一版，结构混乱，已否定）\n一、背景\n二、现状\n三、问题\n四、建议\n（此大纲逻辑层次不清，请勿沿用）\n")

with open("/workspace/project_inputs/drafts/abandoned_outline_v2.txt", "w", encoding="utf-8") as f:
    f.write("废弃大纲（第二版）\n本版本与第一版相同，均已废弃。\n")

with open("/workspace/outputs/.gitkeep", "w") as f:
    f.write("")

with open("/workspace/archive/2024/irrelevant_notice.txt", "w", encoding="utf-8") as f:
    f.write("某省公司关于开展员工体检工作的通知\n各单位：根据公司安排，请于本月内完成员工体检工作。\n此通知与本研究报告无关。\n")

with open("/workspace/project_inputs/drafts/notes_random.txt", "w", encoding="utf-8") as f:
    f.write("个人随笔（无关内容）\n今天天气不错，思考了一些关于管理的问题，但与本项目无关。\n")

# ============================================================
# ACTUAL INPUT MATERIALS (3 key files)
# ============================================================

# Input A: Academic Reference
with open("/workspace/project_inputs/references/学术参考文献摘要.txt", "w", encoding="utf-8") as f:
    f.write("""【学术参考文献摘要】
来源：《国有企业分类考核机制研究》，《管理世界》2022年第4期，作者：刘明华等

核心观点摘录：

1. 企业功能分类是差异化考核的逻辑起点
国有企业依据主业性质可分为商业竞争类、公益保障类和特殊功能类三大类型。商业竞争类企业以市场化为导向，考核重点在于经济效益与市场竞争力；公益保障类企业承担特定社会功能，考核兼顾服务质量与成本控制；特殊功能类企业服务于国家战略，考核侧重任务完成度与安全稳定。

2. 考核链条设计的关键要素
有效的考核链条应具备三个特征：（1）上下贯通性——集团总部的战略目标能够逐层分解至基层单位；（2）责权匹配性——考核主体须与管理授权相匹配；（3）激励相容性——个体行为导向与组织整体目标方向一致。

3. 原集体企业改革的主要挑战
原集体企业改革面临三重困境：历史遗留问题复杂（劳动关系混同、资产权属不清）；管理权限模糊（属地管理与省级管理边界不清晰）；激励机制滞后（工资总额管控缺乏弹性，难以体现市场竞争力）。

4. 工资总额联动机制
研究表明，工资总额与经营效益的联动机制设计应遵循"刚弹结合"原则：刚性部分保障员工基本收入稳定，弹性部分与企业效益、员工绩效挂钩，二者比例建议为6:4至7:3之间。
""")

# Input B: Policy Document
with open("/workspace/project_inputs/policy_docs/国网政策文件摘录.txt", "w", encoding="utf-8") as f:
    f.write("""【国网政策文件摘录】
文件一：《国家电网有限公司原集体企业深化改革工作指导意见》（国网人资〔2021〕XXX号）

主要内容摘录：

第一条（目标）：以"产权清晰、管理规范、激励有效、风险可控"为目标，推动原集体企业实现治理结构现代化、管理机制市场化、激励约束差异化。

第三条（分类管理原则）：原集体企业按照主业属性和功能定位，分为三类进行差异化管理：
（一）主业配套类：承接电网主业配套服务，纳入国网统一管理体系；
（二）市场竞争类：面向外部市场经营，推行市场化考核机制；
（三）特困帮扶类：承担特定政策性任务，给予适当政策支持。

第五条（考核机制）：对原集体企业实行"年度综合考核+专项考核"双轨机制。年度综合考核权重不低于70%，专项考核权重不超过30%。考核结果与工资总额挂钩，挂钩系数区间为0.8至1.2。

第八条（工资总额管理）：建立工资总额"核定基数+效益联动"机制。核定基数参照上年度实发工资总额，效益联动部分根据企业利润完成率和考核结果确定，联动比例不超过核定基数的20%。

文件二：《关于进一步规范原集体企业岗位管理工作的通知》（国网人资〔2022〕YYY号）

主要内容摘录：

一、原集体企业应建立健全岗位管理体系，明确岗位层级、职责边界和任职条件。

二、岗位设置应遵循"因事设岗、以岗定责、责薪匹配"原则，避免因人设岗。

三、各单位应于每年3月底前完成岗位体系评审，评审结果报上级主管部门备案。

四、对于关键岗位（核心技术岗位和管理岗位），应实行差异化薪酬管理，拉开薪酬档差，增强吸引力和保留率。
""")

# Input C: Survey Data
with open("/workspace/project_inputs/survey_data/调研数据摘要.txt", "w", encoding="utf-8") as f:
    f.write("""【项目调研数据摘要】
调研时间：2024年9月-11月
调研范围：某省公司下属7家原集体企业
调研方式：深度访谈（管理人员32人）、问卷调查（员工245人）、资料查阅

一、基本情况
7家原集体企业中：
- 主业配套类3家，员工合计约680人
- 市场竞争类3家，员工合计约420人
- 特困帮扶类1家，员工约85人

二、考核机制现状
（1）考核主体与授权界面
访谈显示，7家企业中有5家存在"考核主体不明确"问题：省公司人资部、业务管理部、企业自身三方均认为自己是考核主体，导致考核结果出现分歧。
（2）考核指标体系
现行考核指标以财务指标为主（平均占比约65%），非财务指标（安全、质量、创新）占比偏低（约35%）。访谈中有78%的管理人员认为非财务指标权重应提升至45%以上。
（3）考核周期
3家市场竞争类企业实行季度考核+年度综合考核；其余4家仅实行年度考核，缺乏过程管控。

三、工资总额管理现状
（1）总额核定机制
5家企业反映工资总额核定主要依据上年实发数，缺乏与经营效益的有效联动，"旱涝保收"现象明显。
（2）内部分配
内部分配层面，绩效工资占比平均约28%，低于国内同类企业平均水平（40-45%）。管理人员与一线员工薪酬比约为2.1:1，分配差距偏小。
（3）激励缺口
有67%的被访谈管理人员表示，现行激励强度不足以吸引和保留核心技术与管理人才。

四、主要问题归纳
1. 治理管控层面：考核主体界定不清，管理授权边界模糊
2. 考核体系层面：指标结构失衡，过程考核缺失，分类考核未落实
3. 激励分配层面：工资总额弹性不足，内部分配差距偏小，激励效果有限
4. 改革推进层面：历史遗留问题（如劳动关系混同）尚未有效解决，制约深化改革

五、典型案例（企业A，主业配套类）
企业A现有员工约230人，近三年营业收入分别为1.2亿、1.35亿、1.41亿元，利润率约8%。
现行工资总额约1800万元，人均年薪约7.8万元，低于省内同行业平均水平（约9.2万元）。
关键岗位流失率近两年约为12%，主要原因为薪酬竞争力不足。
""")

# references/分析框架参考.md and references/文档风格规范.md (referenced in SKILL.md)
with open("/workspace/references/分析框架参考.md", "w", encoding="utf-8") as f:
    f.write("""# 分析框架参考

## 原集体企业考核管理模式分析框架

### 主线一：治理管控与功能定位
- 股权结构 → 管理授权边界 → 考核主体界定
- 企业功能分类（商业竞争类/公益保障类/特殊功能类）→ 差异化管理策略

### 主线二：考核体系设计
- 指标体系逻辑（战略分解 → KPI设计 → 指标权重 → 考核周期）
- 考核链条梳理（上级考核下级的链路与界面）
- 分类考核模式（按企业类型、属地/省管差异等）

### 主线三：激励分配机制
- 工资总额管理（总额核定依据、联动机制、刚弹性结构）
- 内部分配机制（岗效工资制、绩效工资占比、分配拉开系数）
- 激励约束平衡（超额激励、负向约束条款）

### 主线四：改革路径
- 原集体企业历史背景、改革阶段划分
- 历史遗留问题的成因分析与解决方向
""")

with open("/workspace/references/文档风格规范.md", "w", encoding="utf-8") as f:
    f.write("""# 国网文档风格规范

## 标题层级体系
```
一、  一级标题（报告主章）
（一）  二级标题（章节）
1.  三级标题（子节）
（1）  四级标题（细节要点，如需要）
①  列举项（正文中）
```

## 语言风格
- 正式书面语，用词庄重、准确
- 客观陈述：多用"……表明"、"……显示"、"……存在"
- 逻辑连接词：善用"在此基础上"、"由此可见"、"从实践来看"、"综上所述"

## 段落结构
- 每段150-300字为宜
- 二级标题下：先摆现状/问题，再分析成因，最后提出建议/方案

## 常用表述模板
- 问题导入："当前，……存在……问题，主要表现在……"
- 原因分析："究其原因，一是……；二是……；三是……"
- 建议表述："为此，建议……，具体措施包括：一是……；二是……"
""")

print("Workspace setup complete.")
print("Key input files created:")
print("  - /workspace/project_inputs/references/学术参考文献摘要.txt")
print("  - /workspace/project_inputs/policy_docs/国网政策文件摘录.txt")
print("  - /workspace/project_inputs/survey_data/调研数据摘要.txt")
print("Distractor files: 12 irrelevant files in archive/, templates/, tools/, drafts/")