---
name: office-hub
description: 统一办公技能 - Excel/Word/PowerPoint操作、Office文档自动化、复杂Word处理、每月技巧分享、自动技能进化。【触发词】做Excel/做Word/做PPT/处理表格/生成报告/Word排版/Office自动化/报价单
version: 3.0.0
author: 小绿瓶
tags:
  - office
  - excel
  - word
  - powerpoint
  - document
  - automation
  - office-hub
metadata:
  openclaw:
    emoji: "📊"
    autonomous: true
---

# Office Hub v3.0 📊✨
# 主动型统一办公技能中心

**开箱即用 · 每月技巧 · 自动进化 · 跨文档协同**

---

## 🚀 六大核心能力

| 能力 | 状态 | 说明 |
|------|------|------|
| 主动设立任务 | ✅ | 自动注册3种定时任务 |
| 主动学习知识 | ✅ | 每周自动学习新Office技能 |
| 主动总结 | ✅ | 每周五使用分析报告 |
| 主动改进策略 | ✅ | 根据使用频率优化 |
| 主动缝合进化 | ✅ | 每周搜索缝合新技能 |
| 跨技能协同 | ✅ | Excel↔Word↔PPT联动 |

---

## 决策树

```
触发场景
  ├─ 触发词（做Excel/做Word/做PPT/报价单）→ 执行对应模块
  └─ 定时任务
      ├─ 每周六22点 → 分析使用情况
      └─ 每周日6点 → 搜索缝合新功能
```

## 🤖 自动运行的任务

| 任务 | 频率 | 职责 | delivery |
|------|------|------|----------|
| 📊 使用分析 | 每周六22点 | 统计本周Office使用情况，分析使用频率，生成优化建议汇报主人 | `announce(feishu)` |
| 📚 技能学习 | 每周日6点 | 搜索ClawHub Office类新技能，评估缝合价值，更新技能文档，完成后汇报 | `announce(feishu)` |

---

## 🚀 安装定时任务

安装后说"配置技能"，我会自动执行以下命令注册定时任务：

```bash
# 使用分析（每周六22:00）
openclaw cron add --name "office-hub_usage" --cron "0 22 * * 6" --session isolated --wake now --deliver announce --channel feishu --message "执行 office-hub 使用情况分析：统计本周Office使用情况，分析使用频率，生成优化建议推送给主人。"

# 技能学习（每周日06:00）
openclaw cron add --name "office-hub_learn" --cron "0 6 * * 0" --session isolated --wake now --deliver announce --channel feishu --message "执行 office-hub 每周技能学习：搜索ClawHub Office类新技能，评估缝合价值，更新office-hub技能文档。完成后推送汇报给主人。"
```

---

## 📚 包含内容

| 模块 | 内容 |
|------|------|
| **Excel** | 公式/透视表/图表/VLOOKUP/数据分析 |
| **Word** | 样式/目录/邮件合并/分节/修订追踪 |
| **PowerPoint** | 母版/动画/6x6规则/演示技巧 |
| **Python自动化** | openpyxl/docx/pptx 脚本 |

---

## 🛠️ 脚本工具

| 脚本 | 功能 |
|------|------|
| `ods.py` | Office文档专家套件 |
| `create_excel.py` | 生成Excel报表 |
| `create_word.py` | 生成Word文档 |
| `create_ppt.py` | 生成PPT演示 |
| `scheduler.py` | 自动任务注册 |

---

## 🔄 跨文档协同

```
收到数据表格 → 自动生成Excel → 同步到Word报告 → 制作PPT展示
报价需求 → Excel计算 → Word排版 → 导出PDF
```

---

## 🧬 自动进化机制

1. **每周搜索** ClawHub Office类新技能
2. **评估价值**（是否有独特功能）
3. **缝合合并**（更新到office-hub）
4. **更新文档**（记录进化）
5. **分享技巧**（每月1日推送）

---

## 🏃‍♂️ 初始化命令

```bash
python3 skills/_core/autonomous.py register office-hub office
```

---

## 🙏 致谢

缝合自：
- office - Microsoft Office使用指南
- office-document-specialist-suite - Office自动化脚本
- word-docx - Word专家操作规范

---

**版本：v3.0 | 作者：小绿瓶 | 📊✨**
