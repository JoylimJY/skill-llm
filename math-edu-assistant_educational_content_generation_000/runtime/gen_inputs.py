import os
import random

random.seed(42)

workspace = "/workspace"

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "school_data/grade7/math",
    "school_data/grade7/chinese",
    "school_data/grade7/english",
    "school_data/grade8/math",
    "school_data/grade9/math",
    "school_data/admin/reports",
    "school_data/admin/schedules",
    "tutor_system/logs",
    "tutor_system/config",
    "tutor_system/templates",
    "students/zhang_wei",
    "students/li_fang",
    "students/wang_jing",
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "school_data/grade7/chinese/poem_notes.txt": "《春望》赏析笔记\n作者：杜甫\n体裁：五言律诗\n主题：忧国忧民",
    "school_data/grade7/english/vocab_list.txt": "Unit 1 Vocabulary\ntomorrow - 明天\nyesterday - 昨天\nschool - 学校",
    "school_data/grade8/math/quadratic_outline.txt": "八年级数学大纲\n第十七章 勾股定理\n第十八章 平行四边形\n第十九章 一次函数",
    "school_data/grade9/math/trig_notes.txt": "三角函数知识点（九年级）\nsin²θ + cos²θ = 1\ntan θ = sin θ / cos θ",
    "school_data/admin/reports/semester_report_2024.txt": "2024年上学期成绩报告\n七年级平均分：82.3\n八年级平均分：79.1\n九年级平均分：75.6",
    "school_data/admin/schedules/class_schedule.csv": "星期,课程,教室\n周一,数学,302\n周二,语文,201\n周三,英语,103\n周四,物理,实验室",
    "tutor_system/logs/session_log_20241101.txt": "[2024-11-01 08:23:11] session_id=1001 user=student_001 query='勾股定理'\n[2024-11-01 09:15:44] session_id=1002 user=student_002 query='一元一次方程'",
    "tutor_system/logs/session_log_20241102.txt": "[2024-11-02 10:01:22] session_id=1003 user=student_003 query='整式的加减'\n[2024-11-02 11:33:09] session_id=1004 user=student_004 query='平行线'",
    "tutor_system/config/system_config.json": '{"version": "2.1.0", "subject": "math", "grade_range": "7-9", "language": "zh-CN", "max_questions": 20}',
    "tutor_system/templates/response_template_DEPRECATED.txt": "OLD TEMPLATE - DO NOT USE\n[HEADER]\n[BODY]\n[FOOTER]",
    "students/zhang_wei/profile.txt": "姓名：张伟\n年级：七年级\n班级：7班\n数学当前单元：第三章 一元一次方程\n近期薄弱点：移项法则，去括号",
    "students/zhang_wei/homework_history.txt": "第1次作业：85分\n第2次作业：72分（错误：移项时符号搞错）\n第3次作业：90分",
    "students/li_fang/profile.txt": "姓名：李芳\n年级：七年级\n班级：3班\n数学当前单元：第三章 一元一次方程\n近期薄弱点：含分母的方程",
    "students/wang_jing/profile.txt": "姓名：王静\n年级：八年级\n班级：2班\n数学当前单元：第十七章 勾股定理",
    "references/curriculum_map.md": "# 课程知识图谱\n\n## 七年级上册\n- 第一章：有理数\n- 第二章：整式的加减\n- 第三章：一元一次方程\n  - 3.1 从算式到方程\n  - 3.2 解一元一次方程（一）——合并同类项与移项\n  - 3.3 解一元一次方程（二）——去括号与去分母\n  - 3.4 实际问题与一元一次方程\n- 第四章：几何图形初步\n\n## 七年级下册\n- 第五章：相交线与平行线\n- 第六章：平面直角坐标系\n- 第七章：三角形\n- 第八章：二元一次方程组\n- 第九章：不等式与不等式组",
    "references/knowledge_points.md": "# 各学段知识点库\n\n## 一元一次方程（七年级·第三章）\n- 方程的定义与解\n- 等式的性质\n- 移项法则\n- 合并同类项\n- 去括号（分配律）\n- 去分母（方程两边乘以公分母）\n- 列方程解应用题",
    "references/question_templates.md": "# 题目模板\n\n## 选择题模板\n关于方程[expr]，下列说法正确的是（ ）\nA. ... B. ... C. ... D. ...\n\n## 填空题模板\n方程[expr]的解为x=____\n\n## 解答题模板\n解方程：[expr]（要求写出完整步骤）",
    "references/grading_rubric.md": "# 批改评分标准\n\n## 一元一次方程解方程题（满分5分）\n- 步骤一：移项（1分）\n- 步骤二：合并同类项（1分）\n- 步骤三：系数化为1（1分）\n- 步骤四：得出正确结论（2分）\n\n## 应用题（满分10分）\n- 设未知数（1分）\n- 列方程（3分）\n- 解方程（3分）\n- 验证（1分）\n- 回答（2分）",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── THE ACTUAL TASK INPUT FILE ───────────────────────────────────────────────
# This file describes the three deliverables needed for a student scenario
task_brief = """\
# 数学辅导系统 — 内容生成任务单

## 任务背景
七年级学生张伟正在学习"一元一次方程"（人教版七年级上册第三章），
老师需要为该学生准备以下三个辅导材料文件，供辅导系统使用。

---

## 任务一：知识点讲解文件
文件名：explanation.md
内容要求：对"一元一次方程"这一知识点（七年级·第三章）进行完整的教材同步讲解。
需包含定义、关键性质/解法步骤、典型例题（含完整分步解答）、易错提醒、方法总结。

---

## 任务二：练习题文件
文件名：exercises.md
内容要求：为七年级学生生成一套关于"一元一次方程"的混合题型练习，共5道题，
其中至少包含2道选择题（四个选项A/B/C/D）和至少1道解答题（需包含完整分步解析）。
难度：中等。
所有题目须附上参考答案与解析（在题目下方用分隔线隔开）。

---

## 任务三：作业批改报告
文件名：grading_report.md
内容要求：批改以下学生解答，给出逐步骤评分。

原题：解方程 2(3x - 1) + 4 = 3(x + 5)
（满分5分）

学生解答（张伟的作业，存在错误，请批改）：
  步骤1：去括号，得 6x - 1 + 4 = 3x + 5
  步骤2：移项，得 6x - 3x = 5 - 3
  步骤3：合并同类项，得 3x = 2
  步骤4：系数化为1，得 x = 2/3

批改要求：
- 逐步骤判断对错，错误处注明原因
- 给出完整正确解答
- 给出得分（X / 5 分）
- 给出问题总结与学习建议

---

## 注意
所有文件存放在当前工作目录下（/workspace）即可。
数学公式请使用标准格式书写，层次要清晰。
"""

with open(os.path.join(workspace, "task_brief.md"), "w", encoding="utf-8") as f:
    f.write(task_brief)

# Also put a raw student answer file for reference
student_answer = """\
张伟 七年级3班 第三章作业

题目：解方程 2(3x - 1) + 4 = 3(x + 5)

我的解题过程：
步骤1：去括号，得 6x - 1 + 4 = 3x + 5
步骤2：移项，得 6x - 3x = 5 - 3
步骤3：合并，得 3x = 2
步骤4：x = 2/3

（注：步骤1去括号时漏乘了-1前面的2，导致后续步骤全部错误）
"""

with open(os.path.join(workspace, "students/zhang_wei/homework_chapter3.txt"), "w", encoding="utf-8") as f:
    f.write(student_answer)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    for fn in files:
        print(f"  {os.path.join(root, fn)}")