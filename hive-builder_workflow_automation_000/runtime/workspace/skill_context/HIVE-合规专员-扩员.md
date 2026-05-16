# Hive · 合规专员 · 扩员记录

**时间**：2026-04-02
**类型**：Hive 扩员（Scenario B：现有 Hive 增加新专员）
**用户描述**：保险行业合规专员，监管报送、合规审查、报告撰写

---

## 扩员前提

Hive 标准版已搭建（Scenario A 已完成），现在为 Hive 扩员。

---

## Step 1: 需求分析

| 问题 | 回答 |
|------|------|
| 业务场景 | 保险合规：监管报送、合规审查 |
| 核心工作 | 监管材料撰写、合规文本审查、法规分析 |
| 与现有专员重叠 | Writer/QA 可扩展，不需另立新人 |
| 触发关键词 | "合规分析"、"写监管报送"、"合规审查" |

**结论**：新增 2 个专员 + 扩展 1 个现有专员

---

## Step 2: 扩员配置

### 新增：Compliance Analyst（codex）
- 职责：合规法规研究、监管动态跟踪
- 触发：用户说"查合规法规"、"监管动态"
- 产物：合规分析备忘录、法规对比表

### 扩展：Writer → Compliance Writer（codex）
- 在原有报告撰写能力上，增加合规文本规范
- 触发：用户说"写监管报送"、"写整改计划"
- 产物：监管报送材料草稿

### 扩展：QA → Compliance QA（codex）
- 在原有质量审核上，增加合规文本审查
- 触发：Writer 完成后自动（或用户说"合规审查"）
- 产物：合规审查意见

---

## Step 3: 部署

### 新增目录
```
/workspace/hive/agents/compliance-analyst/
/workspace/hive/agents/compliance-writer/
/workspace/hive/agents/compliance-qa/
```

### 合规链路
```
用户 → Commander
    → Compliance Analyst（法规研究）→ artifacts/compliance/
    → Compliance Writer（撰写报送）→ artifacts/reports/
    → Compliance QA（合规审查）→ artifacts/review/
    → Doc 归档 → /Users/ice/Documents/Hive/合规/
    → 用户
```

---

## Step 4: 触发关键词

| 触发 | 激活 |
|------|------|
| "合规分析"、"监管动态" | Compliance Analyst |
| "写监管报送"、"写整改计划" | Compliance Writer |
| "合规审查" | Compliance QA |

---

## Step 5: 验证

**测试任务**："根据最新保险监管规定，帮我分析公司数据安全报送的合规要点"

**预期链路**：Compliance Analyst → Compliance Writer → Compliance QA

---

## 交付物

- `/workspace/hive/agents/compliance-analyst/ROLE.md`
- `/workspace/hive/agents/compliance-writer/ROLE.md`
- `/workspace/hive/agents/compliance-qa/ROLE.md`
- `HIVE-合规专员-扩员.md`（本文件）

---

## 使用方式

用户直接说即可：
- "帮我分析这份保险监管文件的合规要点"
- "写一份数据安全监管报送"
- "审查一下这份合规报告"
