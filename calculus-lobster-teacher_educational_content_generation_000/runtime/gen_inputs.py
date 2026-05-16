import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested directory structure with distractor files ---

dirs = [
    "references",
    "course_materials/chapter5",
    "course_materials/chapter6",
    "course_materials/chapter7",
    "course_materials/chapter8",
    "submissions/student_A",
    "submissions/student_B",
    "submissions/student_C",
    "grading/chapter5",
    "grading/chapter7",
    "platform/skills",
    "platform/graph",
    "admin/reports",
    "admin/archive",
    "temp/drafts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "references/calculus-topics.md": """# 同济七版考点速查

## 第7章 微分方程
- 7.1 微分方程基本概念
- 7.2 可分离变量方程
- 7.3 齐次方程
- 7.4 一阶线性方程：y' + P(x)y = Q(x)，积分因子法
- 7.5 伯努利方程
- 7.6 二阶常系数齐次线性方程
- 7.7 二阶常系数非齐次线性方程（待定系数法、变参数法）
- 7.8 欧拉方程

## 第8章 向量与空间解析几何
- 8.1 向量的运算
- 8.2 平面与直线方程
""",

    "references/sample-exam-v2.1.0.md": """# 样卷 v2.1.0（高阶导向）

此文件为平台示例，实际命题请按Blueprint执行。

记忆：10分 | 理解：20分 | 应用：30分 | 分析：25分 | 评价：10分 | 创造：5分

高阶合计（分析+评价+创造）= 40分 = 40%
""",

    "references/sample-exam-ch8-spatial-analytic-geometry.md": """# 第8章专项样卷

空间解析几何命题示例，仅供参考。
""",

    "course_materials/chapter5/notes.md": "# 第5章 定积分\n积分概念、牛顿-莱布尼茨公式。",
    "course_materials/chapter6/applications.md": "# 第6章 积分应用\n面积、体积、弧长。",
    "course_materials/chapter7/lecture_outline.md": """# 第7章讲义大纲

1. 引入：物理中的增长模型
2. 分类讲解各方程类型
3. 习题课：二阶方程综合
""",
    "course_materials/chapter8/vectors.md": "# 第8章 向量\n点积、叉积、混合积。",
    "platform/skills/skill_ids.json": json.dumps({
        "常微分方程Skill": "ode_basic",
        "常微分方程求解Skill": "ode_solve",
        "积分技巧Skill": "int_tech",
        "数值分析Skill": "num_analysis"
    }, ensure_ascii=False, indent=2),
    "platform/graph/nodes.json": json.dumps([
        {"id": "node_ode_01", "title": "一阶线性微分方程", "skillId": "常微分方程求解Skill",
         "prerequisites": ["node_int_01"], "successors": ["node_ode_02"]},
        {"id": "node_ode_02", "title": "二阶常系数方程", "skillId": "常微分方程求解Skill",
         "prerequisites": ["node_ode_01"], "successors": []},
        {"id": "node_int_01", "title": "积分技巧综合", "skillId": "积分技巧Skill",
         "prerequisites": [], "successors": ["node_ode_01"]}
    ], ensure_ascii=False, indent=2),
    "admin/reports/semester_summary.csv": "student_id,avg_score,chapter\nA001,82,7\nA002,67,7\nA003,91,7\n",
    "admin/archive/old_exam_ch7_2022.md": "# 旧版第7章考卷（2022年）\n已废弃，请勿使用。",
    "temp/drafts/unfinished_homework.md": "# 草稿\n尚未完成，勿用。",
    "grading/chapter5/feedback_ch5.md": "# 第5章批改记录\n略。",
    "submissions/student_B/ch6_work.md": "# 学生B第6章提交\n略。",
    "submissions/student_C/ch8_work.md": "# 学生C第8章提交\n略。",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# --- THE CORE PROBLEM: Student submission with deliberate flaws ---

student_submission = """# 学生A 第7章作业提交

## 题目
证明：初值问题
  y' + P(x)y = Q(x),  y(x₀) = y₀
的解存在且唯一（在P,Q连续的区间上），并求解 y' - y = eˣ, y(0) = 1。

## 学生解答

### 第一部分：存在唯一性

因为方程是一阶线性方程，所以解显然存在且唯一。

由于 y' = Q(x) - P(x)y，右端对 y 是线性的，所以利用 Picard 迭代可以得到解。

结论：解存在唯一。（证毕）

### 第二部分：求解 y' - y = eˣ, y(0) = 1

方程标准形式：y' - y = eˣ，即 P(x) = -1, Q(x) = eˣ。

积分因子 μ = e^∫(-1)dx = e^(-x)。

两边乘以 μ：
  e^(-x)·y' - e^(-x)·y = 1

左边 = d/dx[e^(-x)·y]

积分两边：
  e^(-x)·y = x + C

所以 y = (x + C)·eˣ。

代入初值 y(0) = 1：
  1 = (0 + C)·e⁰ = C

所以 C = 1，y = (x + 1)eˣ。

验证：y' = eˣ + (x+1)eˣ = (x+2)eˣ
      y' - y = (x+2)eˣ - (x+1)eˣ = eˣ ✓
      y(0) = 1 ✓

结论：y = (x+1)eˣ。
"""

with open(os.path.join(workspace, "submissions/student_A/ch7_proof.md"), "w", encoding="utf-8") as f:
    f.write(student_submission)

# --- Task specification file for the agent ---
task_spec = """# 第7章教学材料制作任务

## 任务说明

教研组需要为第7章（微分方程）准备完整的教学材料包，包含三个文件：

1. **exam_ch7.md** — 第7章正式考卷
2. **homework_ch7.md** — 第7章课后作业集
3. **grading_ch7_studentA.md** — 对 submissions/student_A/ch7_proof.md 的正式批改报告

请严格按照平台教学助手规范生成上述三个文件，确保认知层级分布、高阶导向、作业模板格式、批改反馈话术均符合规范，并正确关联知识图谱技能标签。

参考资料在 references/ 和 platform/ 目录中。
"""

with open(os.path.join(workspace, "TASK.md"), "w", encoding="utf-8") as f:
    f.write(task_spec)

print("Workspace initialized successfully.")