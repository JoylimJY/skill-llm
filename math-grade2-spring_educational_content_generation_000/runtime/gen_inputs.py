import os
import random

random.seed(42)

# Create the full workspace directory structure
base = "/workspace"

# Create the skill directory structure (as referenced in SKILL.md)
dirs = [
    "references",
    "assets/exercises",
    "assets/templates",
    "assets/charts",
    "logs/student_progress",
    "logs/error_records",
    "config",
    "scripts",
    "data/raw",
    "data/processed",
    "tests",
    "docs",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Create SKILL.md in workspace
skill_content = """---
name: math-grade2-spring
description: 北师大版小学数学二年级下册学习助手。当用户提到二年级数学、北师大版数学、数学二年级下册、数学学习、数学辅导、数学练习、数学作业辅导时使用此技能。
---

# 北师大版小学数学二年级下册学习助手

## 概述

这是专门为北师大版小学数学二年级下册学生设计的学习助手技能，覆盖教材所有章节知识点，提供知识点讲解、例题分析、练习题生成、学习进度追踪等功能。

## 教材信息

**版本：** 北京师范大学出版社 2025 年 12 月第一版（新课标）  
**年级：** 二年级下册  
**科目：** 数学  

---

## 教材章节结构

### 一、除法
**1.1 分苹果**（P2-3）
- 知识点：平均分的概念
- 学习目标：理解平均分的含义，掌握平均分的方法
- 重点：理解"平均分"就是每份分得同样多
- 难点：解决实际生活中的平均分问题

**1.2 搭一搭（一）**（P4-5）
- 知识点：用小棒摆图形
- 学习目标：用小棒摆三角形、正方形等图形
- 重点：认识图形的边数
- 难点：理解图形的构成

**1.3 搭一搭（二）**（P6-7）
- 知识点：用小棒摆图形的进阶
- 学习目标：继续练习用小棒摆各种图形
- 重点：图形的拼接和组合
- 难点：复杂图形的拼搭

**1.4 分草莓**（P8-9）
- 知识点：认识除法的初步认识
- 学习目标：了解除法的含义
- 重点：除法的读写
- 难点：理解除法的意义

**1.5 分橘子**（P10-11）
- 知识点：除法算式的各部分名称
- 学习目标：认识被除数、除数、商
- 重点：除法算式的读写
- 难点：区分被除数和除数

**1.6 分一分**（P12-13）
- 知识点：平均分的两种分法
- 学习目标：掌握按份数分、按每份数分
- 重点：两种平均分方法的区别
- 难点：选择合适的方法

**练习课**（P14-15）

### 二、混合运算
**2.1 小熊购物**（P16-17）
- 知识点：加减乘除混合运算
- 学习目标：掌握混合运算的顺序
- 重点：先乘除后加减
- 难点：带有括号的运算

**2.2 买鲜花**（P18-19）
- 知识点：应用题中的混合运算
- 学习目标：解决实际购物问题
- 重点：理解题意，列式计算
- 难点：多步运算的应用

**2.3 周长**（P20-21）
- 知识点：认识周长
- 学习目标：理解周长的概念
- 重点：计算长方形、正方形的周长
- 难点：周长公式的应用

**练习课**（P22-23）

### 三、生活中的大数
**3.1 数一数**（P24-25）
- 知识点：认识1000以内的数
- 学习目标：会数1000以内的数
- 重点：数的组成
- 难点：数的读写

**3.2 拨一拨**（P26-27）
- 知识点：认识10000以内的数
- 学习目标：会数10000以内的数
- 重点：数的顺序和大小比较
- 难点：中间或末尾有0的读写

**3.3 比一比**（P28-29）
- 知识点：万以内数的大小比较
- 学习目标：掌握万以内数的大小比较
- 重点：位数不同和位数相同的比较
- 难点：中间有0的比较

**3.4 有多少个字**（P30-31）
- 知识点：估计的方法
- 学习目标：学会估计数量
- 重点：估计策略
- 难点：提高估计的准确性

**练习课**（P32-33）

### 四、测量
**4.1 铅笔有多长**（P34-35）
- 知识点：认识厘米、分米
- 学习目标：认识长度单位厘米和分米
- 重点：厘米和分米的换算
- 难点：正确选择长度单位

**4.2 1千米有多长**（P36-37）
- 知识点：认识千米
- 学习目标：认识长度单位千米
- 重点：千米的实际意义
- 难点：千米与其他单位的换算

**练习课**（P38-39）

### 五、加与减
**5.1 买电器**（P40-41）
- 知识点：整十、整百、整千数的加减
- 学习目标：掌握整十、整百、整千数的加减法
- 重点：口算方法
- 难点：灵活运用口算方法

**5.2 回收废电池**（P42-43）
- 知识点：三位数的加减法
- 学习目标：掌握三位数的加减法
- 重点：竖式计算的方法
- 难点：进位和退位

**练习课**（P44-45）

### 六、认识图形
**6.1 认识角**（P46-47）
- 知识点：认识角
- 学习目标：认识角，知道角的各部分名称
- 重点：直角、锐角、钝角的区分
- 难点：角的大小比较

**6.2 认识长方形和正方形**（P48-49）
- 知识点：认识长方形和正方形
- 学习目标：认识长方形和正方形的特征
- 重点：长方形和正方形的区别
- 难点：图形的判断

**练习课**（P50-51）

### 七、时、分、秒
**7.1 1分有多长**（P52-53）
- 知识点：认识分
- 学习目标：认识时间单位分
- 重点：分的实际意义
- 难点：时与分的关系

**7.2 1秒有多长**（P54-55）
- 知识点：认识秒
- 学习目标：认识时间单位秒
- 重点：秒的实际意义
- 难点：秒与分的关系

**练习课**（P56-57）

### 八、调查与记录
**8.1 评选吉祥物**（P58-59）
- 知识点：数据的收集和整理
- 学习目标：学习收集数据的方法
- 重点：用符号记录数据
- 难点：数据的整理和分析

**8.2 最喜欢的水果**（P60-61）
- 知识点：数据的分类和统计
- 学习目标：学习简单的统计方法
- 重点：统计表的认识
- 难点：根据统计表解决问题

**练习课**（P62-63）

---

## 核心功能

### 1. 知识点讲解
### 2. 例题分析
### 3. 练习题生成
### 4. 学习进度追踪
### 5. 错题管理
### 6. 学习计划

---

## 学习资源

### 参考资料文件
- `references/chapter_guide.md` - 各章节详细指南
- `references/exercises.md` - 练习题库
- `references/common_errors.md` - 常见错误汇总
- `references/learning_tips.md` - 学习方法和技巧

### 资源文件
- `assets/exercises/` - 各章节练习题
- `assets/templates/` - 学习计划模板
- `assets/charts/` - 学习进度图表

---

## 使用建议

### 对于学生
- 每天坚持学习30-40分钟
- 学习新知识前先复习旧知识
- 做练习题时要独立思考
- 错题要及时整理和复习
- 多联系生活实际理解数学

### 对于家长
- 关注孩子的学习进度
- 鼓励孩子多思考多提问
- 营造轻松的学习氛围
- 定期检查学习效果
- 及时给予肯定和鼓励

---

## 重要提示

- 本技能基于北师大版2024版教材
- 学习过程中要注重理解，不要死记硬背
- 数学学习要多动手、多思考、多练习
"""

with open(os.path.join(base, "SKILL.md"), "w", encoding="utf-8") as f:
    f.write(skill_content)

# Create distractor files to increase difficulty

# Config files
with open(os.path.join(base, "config", "settings.json"), "w", encoding="utf-8") as f:
    f.write('{"version": "1.0", "language": "zh-CN", "grade": 2, "semester": "spring"}\n')

with open(os.path.join(base, "config", "chapter_order.txt"), "w", encoding="utf-8") as f:
    f.write("章节顺序配置文件\n错误示例：章节1,章节2,章节3\n")

# Partial/incorrect reference files as distractors
with open(os.path.join(base, "references", "chapter_guide.md"), "w", encoding="utf-8") as f:
    f.write("# 章节指南（待完善）\n\n本文件为空白模板，需要填充内容。\n")

with open(os.path.join(base, "references", "learning_tips.md"), "w", encoding="utf-8") as f:
    f.write("# 学习技巧\n\n## 通用技巧\n- 多练习\n- 多思考\n\n（内容待补充）\n")

# Incorrect/misleading exercise file stub
with open(os.path.join(base, "references", "exercises_stub.md"), "w", encoding="utf-8") as f:
    f.write("# 练习题（旧版，已废弃）\n\n此文件已废弃，请使用 exercises.md\n\n错误的章节顺序：\n- 第一章：几何\n- 第二章：代数\n")

# Old/wrong common errors file
with open(os.path.join(base, "references", "errors_old.txt"), "w", encoding="utf-8") as f:
    f.write("旧版错误记录（三年级版本，不适用）\n1. 分数计算错误\n2. 小数点位置错误\n")

# Distractors in logs
with open(os.path.join(base, "logs", "student_progress", "student_001.json"), "w", encoding="utf-8") as f:
    f.write('{"student_id": "001", "chapters_completed": [], "last_active": "2025-01-01"}\n')

with open(os.path.join(base, "logs", "student_progress", "student_002.json"), "w", encoding="utf-8") as f:
    f.write('{"student_id": "002", "chapters_completed": ["chapter1"], "score": 85}\n')

# Data files
with open(os.path.join(base, "data", "raw", "exercise_bank_v1.csv"), "w", encoding="utf-8") as f:
    f.write("id,question,answer,chapter\n")
    f.write("1,2+3=?,5,unknown\n")
    f.write("2,10-4=?,6,unknown\n")

with open(os.path.join(base, "data", "processed", "stats.json"), "w", encoding="utf-8") as f:
    f.write('{"total_questions": 0, "total_students": 0, "avg_score": 0}\n')

# Assets distractors  
with open(os.path.join(base, "assets", "exercises", "placeholder.txt"), "w", encoding="utf-8") as f:
    f.write("各章节练习题文件目录\n本目录存放各章节的练习题文件。\n")

with open(os.path.join(base, "assets", "charts", "progress_template.txt"), "w", encoding="utf-8") as f:
    f.write("学习进度图表模板\n待实现\n")

# Scripts folder
with open(os.path.join(base, "scripts", "generate_report.py"), "w", encoding="utf-8") as f:
    f.write("# 报告生成脚本\n# 此脚本用于生成学习报告\nprint('TODO')\n")

with open(os.path.join(base, "scripts", "import_data.sh"), "w", encoding="utf-8") as f:
    f.write("#!/bin/bash\n# 数据导入脚本\necho 'TODO: implement data import'\n")

# Tests
with open(os.path.join(base, "tests", "test_exercises.py"), "w", encoding="utf-8") as f:
    f.write("# 测试文件\nimport unittest\nclass TestExercises(unittest.TestCase):\n    def test_placeholder(self):\n        pass\n")

# Docs
with open(os.path.join(base, "docs", "api_reference.md"), "w", encoding="utf-8") as f:
    f.write("# API 参考文档\n\n## 接口列表\n\n（待完善）\n")

with open(os.path.join(base, "docs", "deployment.md"), "w", encoding="utf-8") as f:
    f.write("# 部署文档\n\n## 环境要求\n\n（待完善）\n")

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(base):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")