# Hive Builder · Templates

预置的行业/场景模板，可作为新 Hive 系统的基础。

## 目录

| 文件 | 适用场景 | 状态 |
|------|---------|------|
| `00-base-roles.md` | 合规专员（保险/金融） | ✅ 基础版 |
| `01-financial-audit.md` | 财务审计 | 规划中 |
| `02-legal-research.md` | 法律研究 | 规划中 |
| `03-medical-report.md` | 医疗报告 | 规划中 |
| `04-education-admin.md` | 教育管理 | 规划中 |

## 使用方式

当用户描述一个场景时：
1. 找到最匹配的模板
2. 根据用户具体需求定制
3. 生成新的 ROLE.md
4. 部署到 `/workspace/hive/agents/{specialist}/`

## 如何贡献新模板

新建 `XX-{industry-name}.md`，包含：
- 适用场景说明
- 新增/修改的专员定义
- 触发条件
- 特殊配置说明
