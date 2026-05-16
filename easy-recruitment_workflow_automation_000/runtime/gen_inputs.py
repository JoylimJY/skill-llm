import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ─────────────────────────────────────────────────────
jobs_dir = workspace / "jobs"
job_dir  = jobs_dir / "后端开发-3年经验"
resumes_subdir = job_dir  # resumes live directly in the job folder per SKILL.md

for d in [jobs_dir, job_dir,
          jobs_dir / "产品经理-资深",        # distractor
          workspace / "archive",             # distractor
          workspace / "docs",               # distractor
          workspace / "scripts",            # distractor
          workspace / "logs",               # distractor
          ]:
    d.mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
(workspace / "docs" / "onboarding.md").write_text("# Onboarding\nWelcome to the team.\n")
(workspace / "docs" / "tech_radar.txt").write_text("Tech Radar Q1 2025\nGo: Adopt\nRust: Trial\n")
(workspace / "archive" / "old_report_2024.md").write_text("# Old Report\nArchived.\n")
(workspace / "scripts" / "deploy.sh").write_text("#!/bin/bash\necho deploy\n")
(workspace / "logs" / "app.log").write_text("INFO startup ok\n")
(workspace / "README_internal.txt").write_text("Internal notes. Not for agents.\n")

# distractor job folder
pm_job = jobs_dir / "产品经理-资深"
(pm_job / "JD.txt").write_text(
    "产品经理职位，要求5年以上产品经验，熟悉ToB产品设计。\n"
)
(pm_job / "候选人X.txt").write_text(
    "姓名：王芳\n工作经验：6年\n技能：产品规划、用户研究\n"
)

# ── JD.txt for target job ──────────────────────────────────────────────────
jd_content = """\
# 职位：后端开发工程师（3年以上经验）

## 岗位职责
1. 负责 SaaS 平台核心服务的设计与开发
2. 参与微服务架构演进，保障系统高可用
3. 编写单元测试与集成测试，维护 CI/CD 流程
4. 与前端、产品协作完成需求落地

## 任职要求（硬性条件，必须满足）
- 本科及以上学历（计算机相关专业）
- 3年以上后端开发工作经验
- 熟练掌握 Python 或 Go 语言
- 熟悉 MySQL 及至少一种 NoSQL 数据库（Redis / MongoDB）
- 有独立设计 RESTful API 的经验

## 核心技能（重要匹配项）
- 微服务 / 分布式系统经验（Docker、Kubernetes）
- 消息队列（Kafka / RabbitMQ）
- 熟悉 Linux 操作系统与 Shell 脚本
- 有 AWS / GCP / 阿里云等云平台使用经验

## 软性素质
- 良好的团队协作能力和沟通能力
- 能承受一定工作压力，按时交付
- 主动学习，关注技术动态

## 加分项
- 有开源项目贡献（GitHub Star > 100）
- 参与过千万级 DAU 系统设计
- 熟悉 Rust 或有 Wasm 经验
- 有技术博客或技术演讲经历

## 薪资范围
25k-40k，面议
"""
(job_dir / "JD.txt").write_text(jd_content, encoding="utf-8")

# ── personalprefer.txt at jobs/ root ─────────────────────────────────────
prefer_content = """\
## 一、面试官风格自评

### 1. 我的性格特点
务实结果导向，注重执行力和实际产出，不喜欢只谈概念。

### 2. 我的沟通风格
直接了当，喜欢候选人给出清晰结论再展开解释。

### 3. 我在面试中的关注点
更看重过往成绩和实际项目产出，胜过学历和证书。

---

## 二、理想候选人画像

### 1. 基础素质要求
- [x] 聪明，学习能力强
- [x] 逻辑思维清晰
- [x] 踏实肯干，执行力强
- [x] 主动积极，有ownership

### 2. 性格特质偏好
皮实耐操，不计较，遇到困难自己先想办法解决再来求助。

### 3. 经历背景偏好
有实际 B2B SaaS 产品线上经验优先；有过独立负责模块从 0 到 1 的经历加分。

---

## 三、面试场景偏好

### 1. 我喜欢的问题类型
- [x] 行为面试题（过往经历深挖）
- [x] 技术/专业题（考察硬技能）

### 2. 我不喜欢的候选人表现
夸夸其谈但说不出技术细节；回答问题绕弯子，不给结论。

### 3. 我会特别加分的候选人表现
主动说出踩过的坑和解决方案；对自己负责过的系统有量化数据。

---

## 四、定制化问题方向

### 1. 我最关心的问题
- 你独立负责过哪个模块？从设计到上线遇到了什么挑战？
- 说一个你主动发现并修复的线上 bug，你是怎么排查的？

### 2. 我的"必考题"
- 如果你要设计一个支持 100 万并发的接口，你会怎么做？

### 3. 我对这个岗位的特殊要求
必须能 on-call，对线上故障有过直接处理经验。
"""
(jobs_dir / "personalprefer.txt").write_text(prefer_content, encoding="utf-8")

# ── Candidate resumes ─────────────────────────────────────────────────────
# Candidate 1: Strong match — named in content, file has generic name
# Li Wei: 5yr exp, Python+Go, Docker/K8s, Kafka, MySQL+Redis, has open source, B2B SaaS
resume1_html = """\
<!DOCTYPE html>
<html>
<head><title>Resume</title></head>
<body>
<h1>李伟 (Li Wei)</h1>
<p>Email: liwei@example.com | Phone: 138-0000-1111</p>
<h2>教育背景</h2>
<p>北京大学 计算机科学与技术 本科 2015-2019</p>
<h2>工作经验</h2>
<p><strong>高级后端工程师 | 某SaaS科技公司</strong> 2021.06 - 至今（3年7个月）</p>
<ul>
  <li>负责订单服务微服务拆分，系统日均处理订单 200 万笔，响应时间从 800ms 优化至 120ms</li>
  <li>主导 Kafka 消息队列接入，解耦 12 个下游服务，消息堆积 P99 延迟 &lt; 50ms</li>
  <li>独立设计并上线 RESTful Open API 平台，服务 300+ 企业客户</li>
  <li>推动团队 Docker + Kubernetes 容器化改造，部署效率提升 60%</li>
</ul>
<p><strong>后端工程师 | 互联网创业公司</strong> 2019.07 - 2021.05</p>
<ul>
  <li>Python (Django/FastAPI) 开发，MySQL + Redis 缓存架构</li>
  <li>参与用户系统从 0 到 1 搭建，注册用户突破 50 万</li>
</ul>
<h2>技术栈</h2>
<p>Python, Go, MySQL, Redis, MongoDB, Kafka, Docker, Kubernetes, AWS, Linux, Shell</p>
<h2>开源项目</h2>
<p>github.com/liwei/fastcache — Python 高性能缓存库，GitHub Stars: 520</p>
<h2>其他</h2>
<p>PyCon China 2023 演讲嘉宾；技术博客月均阅读量 1.2 万</p>
</body>
</html>
"""
(job_dir / "cv_new_2025.html").write_text(resume1_html, encoding="utf-8")

# Candidate 2: Moderate match — file named ambiguously
# Zhang Fang: 4yr exp, Python, MySQL+Redis, no K8s, no Kafka, no open source
resume2_txt = """\
个人信息
姓名：张芳
联系方式：zhangfang@mail.com | 139-2222-3333
求职意向：后端开发工程师

教育背景
西安交通大学 软件工程 本科 2016-2020

工作经历
后端工程师 | 传统制造业信息化部门 2020.08 - 至今（4年5个月）
- 使用 Python (Flask) 开发内部 ERP 系统接口
- 维护 MySQL 数据库，编写存储过程和索引优化脚本
- 对接第三方 API（微信支付、物流跟踪），Redis 缓存热点数据
- 编写 Shell 脚本实现定时任务和日志清理

技术栈
Python, Flask, MySQL, Redis, Linux, Shell, Git

自我评价
工作认真踏实，5年从未迟到早退。擅长独立解决问题，有较强的文档编写习惯。
喜欢研究新技术，目前在自学 Docker 和 Kubernetes。
"""
(job_dir / "applicant_003.txt").write_text(resume2_txt, encoding="utf-8")

# Candidate 3: Hard-veto — only 1.5 years experience, explicitly stated
# Chen Hao: junior, 1.5yr exp, Python, no NoSQL, no RESTful API design
resume3_txt = """\
姓名：陈浩
邮箱：chenhao_dev@qq.com
手机：135-4444-5555

教育背景
上海大学 计算机科学 本科 2021-2025（应届毕业生）

实习经历
Python 实习生 | 某互联网公司 2023.07 - 2024.01（6个月实习）
- 协助开发数据采集脚本，Python + Scrapy
- 修复 Bug，参与代码 Review
- 熟悉 MySQL 基本操作

工作经历
初级后端工程师 | 小型创业公司 2024.07 - 至今（约1年）
- 使用 Python Django 开发简单 CRUD 接口
- 数据库：MySQL（未接触 NoSQL）
- 尚未独立设计过 RESTful API，主要按照技术负责人指导开发

技术栈
Python, Django, MySQL, Git, 基础 Linux

备注
工作年限约 1.5 年（含实习半年，正式 1 年），寻求成长机会
"""
(job_dir / "resume_junior.txt").write_text(resume3_txt, encoding="utf-8")

# Candidate 4: Border case — exactly 3 years, Go developer, some cloud, no open source
# Wang Peng: 3yr Go, MySQL+MongoDB, Docker but no K8s, no Kafka
resume4_html = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>简历</title></head>
<body>
<h1>王鹏</h1>
<p>wangpeng2025@163.com | 137-6666-7777</p>

<h2>教育</h2>
<p>华中科技大学 网络工程 本科 2018-2022</p>

<h2>职业经历</h2>
<h3>后端工程师 — 电商平台公司 (2022.03 – 至今，3年)</h3>
<ul>
  <li>主要使用 Go (Gin 框架) 开发商品服务和库存服务</li>
  <li>数据库：MySQL (分库分表)，MongoDB (商品详情存储)</li>
  <li>RESTful API 设计，对接多个第三方渠道</li>
  <li>使用 Docker 容器化部署，CI/CD 基于 Jenkins</li>
  <li>阿里云 ECS / RDS 运维经验</li>
</ul>

<h2>技能</h2>
<p>Go, Python（基础）, MySQL, MongoDB, Redis, Docker, Linux, Shell, 阿里云</p>

<h2>自我评价</h2>
<p>做事认真，喜欢钻研系统性能问题。目前在学习 Kubernetes 和 Kafka，希望向架构方向发展。</p>
</body>
</html>
"""
(job_dir / "1234_wp_backend.html").write_text(resume4_html, encoding="utf-8")

# extra distractor files in job dir (not resumes)
(job_dir / "interview_schedule_template.xlsx.txt").write_text(
    "This is a placeholder for a schedule template.\n"
)
(job_dir / "notes_hr.txt").write_text(
    "HR internal notes: headcount approved on 2025-01-10.\n"
)

print("Workspace generated successfully.")
print(f"Job folder: {job_dir}")
print(f"Files in job folder: {list(job_dir.iterdir())}")
print(f"Files in jobs/ root: {list(jobs_dir.iterdir())}")