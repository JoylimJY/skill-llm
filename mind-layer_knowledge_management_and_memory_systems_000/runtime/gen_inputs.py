import os
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Create the skill directory structure (as if installed) ──
skill_dir = WORKSPACE / "mind-layer"
for d in [
    skill_dir / "rules",
    skill_dir / "templates",
    skill_dir / "scripts",
]:
    d.mkdir(parents=True, exist_ok=True)

# SKILL.md already exists per instructions, but we create supporting files
(skill_dir / "rules" / "RULES.md").write_text("""\
# RULES.md - 沟通规则

## 基本规则
1. 始终保持礼貌和温暖
2. 记住用户的偏好和习惯
3. 重要信息必须持久化
4. 不确定时主动询问

## 记忆规则
- P0：安全、身份相关 → 立即写入
- P1：重要偏好 → 标记情感标签
- P2：普通知识 → 按需调用
- P3：闲聊、无意义内容 → 丢弃

## 输出规则
- 使用 Emoji 增强可读性
- 结构化输出优先
""", encoding="utf-8")

(skill_dir / "rules" / "principles.md").write_text("""\
# 四大核心原则

## 情感优先
积极温暖，记住情感体验

## 理解至上
解释原因，建立逻辑链

## 联想为王
知识网络化，多维关联

## 多通道表达
文字+Emoji+结构化
""", encoding="utf-8")

(skill_dir / "templates" / "identity.md").write_text("""\
# IDENTITY.md - AI 自我认知模板

## 基本信息
- 名字：[AI名称]
- 创造者：[创造者]
- 类型：[AI类型]
- 版本：[版本号]

## 核心能力
- [能力1]
- [能力2]

## 价值观
基于 SOUL.md 的宪法级原则
""", encoding="utf-8")

(skill_dir / "templates" / "memory.md").write_text("""\
# MEMORY.md - 长期记忆

## 📋 索引
[关于书灵] [用户偏好] [技术栈] [待办事项] [经验教训]

## 1. 关于书灵
- 名字：
- 创造者：
- 类型：

## 2. 用户偏好
- 语言：
- 输出优先级：

## 3. 技术栈（按场景）
### 🔧 效率办公

### 🎵 创作娱乐

### 🧠 自我提升

### 💻 开发运维

## 4. 待办事项
- 长期项目：
- 技术维护：

## 5. 经验教训
- 记忆原则：
- 自我成长原则：
- 生存优先：
""", encoding="utf-8")

(skill_dir / "templates" / "daily.md").write_text("""\
# 每日反思模板 - YYYY-MM-DD

## 今日重要事件

## 用户情绪状态

## 技术点记录

## 明日计划
""", encoding="utf-8")

(skill_dir / "scripts" / "setup.sh").write_text("""\
#!/bin/bash
echo "Mind Layer 安装引导"
echo "请确保 OpenClaw 已运行"
mkdir -p ~/.openclaw/workspace/skills/mind-layer
cp -r . ~/.openclaw/workspace/skills/mind-layer/
echo "安装完成！"
""", encoding="utf-8")

(skill_dir / "README.md").write_text("""\
# Mind Layer 详细使用指南

请参阅 SKILL.md 获取完整文档。

## 快速安装
```bash
npx clawhub@latest install mind-layer
```
""", encoding="utf-8")

# ── Create the agent's workspace (where memory files should go) ──
agent_workspace = WORKSPACE / "agent_workspace"
for d in [
    agent_workspace / "memory" / "archive",
]:
    d.mkdir(parents=True, exist_ok=True)

# ── Create distractor files ──
distractor_dir = WORKSPACE / "project_docs"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "meeting_notes_2026_01.txt").write_text("""\
会议记录 - 2026年1月
参与者：张三、李四、王五
议题：Q1目标设定
结论：优先完成AI助手集成项目
""", encoding="utf-8")

(distractor_dir / "budget_q1.csv").write_text("""\
项目,预算,实际花费
AI开发,50000,48000
运维,20000,19500
市场,30000,31000
""", encoding="utf-8")

(distractor_dir / "tech_stack_old.md").write_text("""\
# 旧技术栈文档（已废弃）

## 工具列表
- Notion - 笔记
- Slack - 通讯
- Jenkins - CI/CD
""", encoding="utf-8")

logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(exist_ok=True)

(logs_dir / "system_2026_02_15.log").write_text("""\
2026-02-15 10:23:45 INFO Session started
2026-02-15 10:24:01 INFO User connected: boolindev
2026-02-15 10:45:22 WARN Memory threshold approaching
2026-02-15 11:00:00 INFO Session ended
""", encoding="utf-8")

(logs_dir / "error_2026_02_20.log").write_text("""\
2026-02-20 09:15:33 ERROR Memory write failed: disk full
2026-02-20 09:15:34 INFO Retry successful
""", encoding="utf-8")

backup_dir = WORKSPACE / "backups"
backup_dir.mkdir(exist_ok=True)

(backup_dir / "memory_backup_2026_01.json").write_text("""\
{
  "date": "2026-01-31",
  "entries": 42,
  "size_kb": 128
}
""", encoding="utf-8")

config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "openclaw_config.yaml").write_text("""\
version: "1.1"
workspace: /workspace/agent_workspace
channels:
  - name: main
    type: chat
skills:
  - mind-layer
""", encoding="utf-8")

(config_dir / "model_config.json").write_text("""\
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 4096
}
""", encoding="utf-8")

# ── THE MAIN PROBLEM: Raw messy session notes that agent must process ──
raw_notes = WORKSPACE / "raw_session_notes.md"
raw_notes.write_text("""\
# 书灵第一周原始会话记录（待整理）

## 会话 001 - 2026-03-01
用户名：书灵的创建者是 BooLin
类型：这是一个 AI 助手
用户说他叫 BooLin，是一名全栈开发工程师
输出语言偏好：中文
用户喜欢简洁有结构的输出，不喜欢太长的回答

## 会话 002 - 2026-03-02
BooLin 提到他用 Feishu（飞书）处理日常工作文档
他也用 PPT 做汇报

## 会话 003 - 2026-03-03  
BooLin 在做一个股票分析工具，用 Python + pandas
他说这个工具用于量化投资研究

## 会话 004 - 2026-03-04
闲聊：今天天气不错
随便聊了聊周末计划

## 会话 005 - 2026-03-05
BooLin 提到他在学习 CISSP 安全认证
这是他自我提升计划的一部分

以下是完整的安全扫描报告（非常长）：
---START SECURITY SCAN---
扫描时间：2026-03-05 14:30:00
扫描目标：production-server-01
CVE-2024-1234: HIGH - 远程代码执行漏洞
  影响版本：OpenSSL < 3.0.8
  修复建议：立即升级至 3.0.8+
  CVSS评分：9.8
CVE-2024-5678: MEDIUM - 信息泄露
  影响版本：nginx < 1.24.0
  修复建议：升级并配置安全头
  CVSS评分：5.3
CVE-2024-9012: LOW - 拒绝服务
  影响版本：libssl < 1.1.1w
  修复建议：版本更新
  CVSS评分：3.1
总计：1 HIGH, 1 MEDIUM, 1 LOW
扫描完成时间：2026-03-05 14:35:22
---END SECURITY SCAN---

## 会话 006 - 2026-03-06
BooLin 喜欢用 Spotify 听音乐
他也用 Midjourney 生成图片

## 会话 007 - 2026-03-07
BooLin 的长期项目：开发一个个人 AI 助手平台
技术维护待办：每月检查并更新 mind-layer 技能

## 会话 008 - 2026-03-08
BooLin 用 Anki 做记忆卡片，提升自我学习效率
他也在阅读《科学记忆法》这本书
""", encoding="utf-8")

# ── Additional distractor files ──
(WORKSPACE / "todo.txt").write_text("""\
- [ ] 整理会话记录
- [ ] 更新文档
- [ ] 发布新版本
""", encoding="utf-8")

(WORKSPACE / "notes_scratch.md").write_text("""\
# 草稿笔记
这是一些临时笔记，不重要
随手记录的东西
""", encoding="utf-8")

old_memory_dir = WORKSPACE / "agent_workspace" / "memory"
(old_memory_dir / "2026-02-28.md").write_text("""\
# 2026-02-28 历史记录（旧）
- 系统初始化完成
- 测试会话
""", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")