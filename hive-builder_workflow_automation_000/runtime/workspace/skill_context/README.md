# Hive Builder Skill

## 概述

Hive Builder 用于从用户的业务描述快速构建一个定制化的 Hive 多 Agent 系统。

## 使用方法

用户说"构建一个适合 XXX 场景的 Hive"，即触发本 Skill。

## 文件结构

```
hive-builder/
├── SKILL.md              # 主 Skill 定义
├── README.md             # 本文件
├── templates/            # 预置行业模板
│   ├── README.md
│   └── 00-base-roles.md  # 合规专员模板（示例）
└── scripts/             # 辅助脚本（规划中）
```

## 构建流程

1. **理解需求** — 用户描述业务场景
2. **分析专员** — 确定需要哪些专员
3. **生成配置** — 为每个专员生成 ROLE.md
4. **部署** — 创建目录、写入文件
5. **验证** — 用测试任务验证系统可运行
6. **交付** — 生成 SETUP.md 总结文档

## 触发示例

- "我想创建一个 Hive · 法律研究 系统"
- "帮我构建一个适合财务审计的 Hive"
- "我想把 Hive 改成适合医疗行业的版本"

## 扩展模板

在 `templates/` 目录下按 `XX-{行业名}.md` 格式创建新模板即可。
