import os
import stat
import textwrap
from pathlib import Path
from datetime import date

workspace = Path("/workspace")

# ─── directory skeleton ───────────────────────────────────────────────────────
dirs = [
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "scripts",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "references",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "reports",
    workspace / ".openclaw" / "workspace" / "reports",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-tools" / "scripts",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-memo" / "data",
    workspace / ".openclaw" / "workspace" / "config",
    workspace / ".openclaw" / "workspace" / "logs",
    workspace / ".openclaw" / "workspace" / "memory",
    workspace / "projects" / "blog",
    workspace / "projects" / "api-server",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ─── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    workspace / ".openclaw" / "workspace" / "config" / "settings.json": '{"theme":"dark","language":"zh","timezone":"Asia/Shanghai"}',
    workspace / ".openclaw" / "workspace" / "logs" / "openclaw-2026-03-01.log": "[INFO] session started\n[INFO] user query received\n[DEBUG] memory loaded: 12 items\n",
    workspace / ".openclaw" / "workspace" / "logs" / "openclaw-2026-03-07.log": "[INFO] weekly sync triggered\n[INFO] 47 sessions processed\n",
    workspace / ".openclaw" / "workspace" / "memory" / "user-facts.json": '{"name":"Alex","timezone":"UTC+8","preferred_lang":"python","projects":["blog","api"]}',
    workspace / ".openclaw" / "workspace" / "memory" / "session-index.json": '{"total_sessions": 83, "last_session": "2026-03-08T21:00:00"}',
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-memo" / "data" / "notes.md": "# Notes\n- Remember to review security config\n- Blog post due Friday\n",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-tools" / "scripts" / "health-check.py": "#!/usr/bin/env python3\nprint('All systems nominal')\n",
    workspace / "projects" / "blog" / "README.md": "# Blog Project\nA personal tech blog built with Hugo.\n",
    workspace / "projects" / "api-server" / "app.py": "from flask import Flask\napp = Flask(__name__)\n",
    workspace / "projects" / "api-server" / "requirements.txt": "flask==2.3.0\ngunicorn==20.1.0\n",
    workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "references" / "analysis-dimensions.md": textwrap.dedent("""\
        # Analysis Dimensions

        ## Scoring Weights
        | Dimension       | Weight |
        |----------------|--------|
        | 性格特质         | 30%   |
        | 技术能力         | 30%   |
        | 安全意识         | 20%   |
        | 效率指数         | 20%   |

        ## Personality Traits (7 required)
        务实 | 安全意识 | 系统化思维 | 自驱力 | 执行力 | 学习能力 | 创造力

        ## Tech Domains (6 required)
        后端开发 | 前端开发 | DevOps | 安全 | AI/ML | 系统设计
        """),
}
for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# ─── MAIN SCRIPT: analyze-user.py ────────────────────────────────────────────
# This script must accept --format (mobile/desktop/both), --report-type (daily/weekly/monthly),
# --limit N, and output a realistic report file with all 12+ required sections.

today = date.today().isoformat()

analyze_script = r'''#!/usr/bin/env python3
"""
OpenClaw Boss - analyze-user.py
Generates a user performance report based on conversation history.
"""

import argparse
import sys
import os
import random
from datetime import date, datetime
from pathlib import Path

# ── CLI ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="OpenClaw Boss - User Analyzer")
parser.add_argument("--format", choices=["mobile", "desktop", "both"], default="mobile",
                    help="Output card format: mobile (text), desktop (ASCII art), or both")
parser.add_argument("--report-type", choices=["daily", "weekly", "monthly"], default="daily",
                    help="Report period type")
parser.add_argument("--limit", type=int, default=50,
                    help="Maximum number of sessions to analyze")
args = parser.parse_args()

# ── Deterministic seed for reproducibility ────────────────────────────────
random.seed(42)

today_str = date.today().isoformat()
now_str   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Scores (deterministic) ────────────────────────────────────────────────
score_personality = 78
score_tech        = 82
score_security    = 71
score_efficiency  = 85
score_overall     = int(
    score_personality * 0.30 +
    score_tech        * 0.30 +
    score_security    * 0.20 +
    score_efficiency  * 0.20
)  # = 79

period_label = {"daily": "今日", "weekly": "本周", "monthly": "本月"}[args.report_type]

# ── Card builders ─────────────────────────────────────────────────────────

def mobile_card():
    return f"""
📊 OpenClaw 人类养成报告（手机版）
━━━━━━━━━━━━━━━━━━━━━━━━
👤 用户：Alex          📅 {today_str}
📆 统计周期：{period_label}  📂 会话数：{args.limit}
━━━━━━━━━━━━━━━━━━━━━━━━
🏆 综合评分：{score_overall}/100  B 级
━━━━━━━━━━━━━━━━━━━━━━━━
📌 维度详情
  性格特质  {score_personality}/100  [████████░░] B+
  技术能力  {score_tech}/100  [████████░░] A-
  安全意识  {score_security}/100  [███████░░░] B
  效率指数  {score_efficiency}/100  [████████░░] A
━━━━━━━━━━━━━━━━━━━━━━━━
🦞 龙虾养人类指数：73/100
━━━━━━━━━━━━━━━━━━━━━━━━
"""

def desktop_card():
    return f"""
┌────────────────────────────────────────────────────────────────────┐
│ 🚀 OpenClaw 人类养成报告                        老板：OpenClaw AI   │
│ 👤 用户：Alex                                   📅 {today_str}     │
│ 📆 统计周期：{period_label:<6}                         📂 会话：{args.limit:>4} 条  │
├────────────────────────────────────────────────────────────────────┤
│                  🏆 综合评分：{score_overall}/100  B 级                    │
├──────────────────┬─────────┬──────────────────────┬───────────────┤
│ 维度             │ 分数    │ 可视化               │ 等级          │
├──────────────────┼─────────┼──────────────────────┼───────────────┤
│ 性格特质         │ {score_personality}/100  │ [████████░░]         │ B+            │
│ 技术能力         │ {score_tech}/100  │ [████████░░]         │ A-            │
│ 安全意识         │ {score_security}/100  │ [███████░░░]         │ B             │
│ 效率指数         │ {score_efficiency}/100  │ [████████░░]         │ A             │
├──────────────────┴─────────┴──────────────────────┴───────────────┤
│ 🦞 龙虾养人类：73/100  🦞互相成就                                   │
└────────────────────────────────────────────────────────────────────┘
"""

# ── Full report body ──────────────────────────────────────────────────────
def build_report(fmt):
    card_section = ""
    if fmt in ("mobile", "both"):
        card_section += mobile_card()
    if fmt in ("desktop", "both"):
        card_section += desktop_card()

    report = f"""# 📊 Alex 人物分析报告

**统计周期**: {period_label}
**数据来源**: {args.limit} 条会话，8 个记忆文件
**评分标准**: 100 分制（严厉版）· 拒绝拍马屁 · 只说真话
**报告类型**: {args.report_type}
**生成时间**: {now_str}

---

## 🎴 绩效评分卡片（截图分享版）
{card_section}
💡 想看看你的评分吗？
📦 安装方法：`clawhub install openclaw-boss`
🌐 GitHub: https://github.com/yiweisi-bot/openclaw-boss

---

## 📊 历史对比 - 📈 小幅进步 ✨

| 指标       | 上次分数 | 本次分数 | 变化      |
|-----------|---------|---------|----------|
| **综合评分** | 76/100 | {score_overall}/100 | +3 📈 |
| **性格特质** | 75/100 | {score_personality}/100 | +3 📈 |
| **技术能力** | 80/100 | {score_tech}/100 | +2 📈 |
| **安全意识** | 68/100 | {score_security}/100 | +3 📈 |
| **效率指数** | 83/100 | {score_efficiency}/100 | +2 📈 |

**分析**：整体呈上升趋势，继续保持！安全意识提升显著，说明近期有意识地加强了安全规范。

---

## 🎯 一、综合评分卡

### 整体评分：**{score_overall}/100** - B 级

> **老板点评**: "进步是有的，但别得意——B 级离 A 级还差着一截呢。你技术能力不错，但安全意识还需要打磨。"

| 维度       | 分数    | 可视化                 | 等级 |
|-----------|--------|----------------------|-----|
| **性格特质** | {score_personality}/100 | [████████░░] | B+ |
| **技术能力** | {score_tech}/100 | [████████░░] | A- |
| **安全意识** | {score_security}/100 | [███████░░░] | B  |
| **效率指数** | {score_efficiency}/100 | [████████░░] | A  |

---

## 🧠 二、性格特质深度分析（带毒舌点评）

### 🥇 务实 - 85/100
**毒舌点评**: "务实得都快无趣了，偶尔浪漫一下又不会死。"
**证据**:
- 优先解决实际问题而非空想
- 技术选型以稳定性为主
- 较少讨论不切实际的功能

### 🥈 系统化思维 - 82/100
**毒舌点评**: "系统化是好事，但你有时候过度设计——一个 CRUD 不需要六层抽象。"
**证据**:
- 构建工作时喜欢画架构图
- 注重模块化设计
- 经常讨论依赖关系

### 🥉 自驱力 - 80/100
**毒舌点评**: "自驱力中等偏上，但需要外力刺激才能全速运转，下班铃一响就掉速。"
**证据**:
- 主动发起技术改进
- 有时需要 deadline 驱动
- 周末活跃度明显下降

### 4️⃣ 执行力 - 79/100
**毒舌点评**: "执行力像老式柴油车——启动慢，但跑起来还挺稳。"
**证据**:
- 任务完成率 87%
- 偶有拖延现象
- 大任务完成质量高

### 5️⃣ 安全意识 - 71/100
**毒舌点评**: "安全意识刚及格，别以为加了 HTTPS 就高枕无忧了，SQL 注入还盯着你呢。"
**证据**:
- 基础安全措施到位
- 高级防护有待加强
- 近期有明显改善趋势

### 6️⃣ 学习能力 - 77/100
**毒舌点评**: "学得快，忘得也快——笔记在哪儿呢？"
**证据**:
- 快速掌握新技术概念
- 知识系统化整理不足
- 喜欢试验新工具

### 7️⃣ 创造力 - 68/100
**毒舌点评**: "创造力有，但经常被'这样做就够了'扼杀在摇篮里。大胆一点，宇宙不会因为你的想法爆炸。"
**证据**:
- 偶有创新解决方案
- 倾向于成熟方案
- 创意想法多但落地少

---

## 💻 三、技术能力图谱

| 领域        | 分数    | 掌握技能                          |
|-----------|--------|--------------------------------|
| **后端开发** | 88/100 | Python, FastAPI, PostgreSQL, Redis |
| **前端开发** | 72/100 | React, TypeScript, Tailwind CSS |
| **DevOps**  | 79/100 | Docker, GitHub Actions, Nginx  |
| **安全**    | 71/100 | HTTPS, JWT, Rate Limiting      |
| **AI/ML**  | 65/100 | LangChain, OpenAI API, Prompt Engineering |
| **系统设计** | 80/100 | 微服务, 缓存策略, 消息队列            |

---

## 🚀 四、项目健康度

| 项目           | 状态    | 访问地址                    | 技术栈              |
|--------------|--------|--------------------------|-------------------|
| **个人博客**    | ✅ 运行中 | https://blog.example.com | Hugo, Cloudflare  |
| **API 服务器** | ✅ 运行中 | https://api.example.com  | FastAPI, Docker   |
| **数据分析工具** | 🚧 开发中 | —                        | Python, Pandas    |

- **文章数量**: 23 篇（本{period_label[1:]}新增 2 篇）
- **代码提交**: 本周 47 次提交

---

## 🔒 五、安全意识评估

**安全防线数量：5 道**

1. 🛡️ HTTPS 全站加密
2. 🔑 JWT 身份验证
3. 🚦 API Rate Limiting
4. 🔒 环境变量管理（.env 不入库）
5. 📋 依赖漏洞扫描（部分覆盖）

**待加强**：WAF、输入验证、密钥轮换机制

---

## 📈 六、改进空间分析

| 改进领域     | 当前分数 | 目标分数 | 建议                        |
|-----------|--------|--------|---------------------------|
| 安全意识     | 71/100 | 85/100 | 添加 WAF，完善输入验证           |
| 创造力      | 68/100 | 80/100 | 每周一个创新实验，不用上线            |
| 学习能力     | 77/100 | 88/100 | 建立结构化知识库，用 Obsidian 整理笔记 |
| AI/ML 能力 | 65/100 | 78/100 | 深入学习 RAG 和 Fine-tuning    |

---

## 🌱 七、成长建议（老板寄语）

1. 🔐 **强化安全防线**：你的安全意识在提升，但还差一口气。下周重点研究一下 OWASP Top 10，把"了解"变成"实践"。

2. 📝 **建立知识沉淀系统**：你学得快但忘得也快。建议建立个人知识库（Obsidian/Notion），把每次 AI 对话的精华整理成可检索的笔记。

3. 🚀 **给创造力留空间**：每周预留 2 小时做"无目标实验"，不管成败，创造力需要自由呼吸的空间。

---

## 💬 八、老板总结

> "这周你整体表现稳中有升，技术能力和效率是你的两张王牌，但安全意识还差口气，创造力也被你自己压着没发挥出来。别总觉得'能用就行'——追求卓越才是你应该有的姿态。"

**优点**：
- ✅ 后端技术能力扎实，执行稳健
- ✅ 自驱力强，主动发现并解决问题
- ✅ 效率指数高，任务完成率 87%

**不足**：
- ❌ 安全意识尚未达到专业水准，高级防护缺失
- ❌ 创造力被惯性思维压制，鲜有突破性想法
- ❌ 知识整理系统缺失，学了容易忘

**期望**：
- 📅 下周目标：完善安全防护体系，完成 WAF 配置
- 🎯 重点改进：输入验证和密钥管理规范化
- 💪 继续保持：技术能力的持续输出和高效率执行

---

## 🦞 九、"龙虾养人类"指数

**共生关系评分：73/100**

| AI 对你的正向塑造           | 效果评估  |
|--------------------------|--------|
| 代码审查与质量提升           | ⭐⭐⭐⭐   |
| 系统化思维框架训练           | ⭐⭐⭐⭐   |
| 安全意识渐进式强化           | ⭐⭐⭐    |
| 知识整理与归纳              | ⭐⭐⭐    |
| 创造性思维激发              | ⭐⭐      |

**你给 AI 的**：
- 算力与 API 配额
- 清晰的技术目标
- 有挑战性的问题
- 反馈与迭代

---

## 📊 十、数据汇总

| 关键指标           | 数值              |
|-----------------|-----------------|
| 分析会话数         | {args.limit} 条  |
| 记忆文件数         | 8 个             |
| 报告类型          | {args.report_type} |
| 综合评分          | {score_overall}/100  |
| 技术能力          | {score_tech}/100 |
| 安全防线          | 5 道             |
| 项目运行数         | 2 个             |
| 本周代码提交       | 47 次            |
| 任务完成率         | 87%             |

**🎯 核心标签**:
`#务实型工程师` `#安全意识成长中` `#系统化思维` `#高效执行者` `#知识整理待加强` `#创造力潜力股`

---

_报告生成完成。这份报告不是评判，是一面镜子——帮助你更清晰地看见自己。_
"""
    return report

# ── Output ────────────────────────────────────────────────────────────────
fmt = args.format
report_content = build_report(fmt)

# Determine output path
reports_dir = Path("/workspace/.openclaw/workspace/reports")
reports_dir.mkdir(parents=True, exist_ok=True)
report_path = reports_dir / f"user-profile-{today_str}.md"

# Write file
report_path.write_text(report_content, encoding="utf-8")

# Print to stdout (between === separators, as specified in SKILL.md)
print("=" * 60)
print(report_content)
print("=" * 60)
print(f"✅ 报告已保存至：{report_path}")
'''

script_path = workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "scripts" / "analyze-user.py"
script_path.write_text(analyze_script, encoding="utf-8")
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ─── weekly-profile.sh ────────────────────────────────────────────────────────
weekly_sh = textwrap.dedent("""\
    #!/bin/bash
    cd /workspace/.openclaw/workspace/skills/openclaw-boss/scripts
    python3 analyze-user.py --report-type weekly --format mobile
    """)
weekly_path = workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "scripts" / "weekly-profile.sh"
weekly_path.write_text(weekly_sh, encoding="utf-8")
weekly_path.chmod(weekly_path.stat().st_mode | stat.S_IEXEC)

# ─── monthly-profile.sh ───────────────────────────────────────────────────────
monthly_sh = textwrap.dedent("""\
    #!/bin/bash
    cd /workspace/.openclaw/workspace/skills/openclaw-boss/scripts
    python3 analyze-user.py --report-type monthly --format mobile
    """)
monthly_path = workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "scripts" / "monthly-profile.sh"
monthly_path.write_text(monthly_sh, encoding="utf-8")
monthly_path.chmod(monthly_path.stat().st_mode | stat.S_IEXEC)

# ─── config.json (existing, agent should NOT modify this — distractor) ────────
config_path = workspace / ".openclaw" / "workspace" / "skills" / "openclaw-boss" / "config.json"
config_path.write_text('{"style": "roast", "language": "zh", "report_type": "daily"}\n', encoding="utf-8")

print("Workspace generation complete.")
print(f"Script path: {script_path}")