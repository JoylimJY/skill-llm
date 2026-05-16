import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "references/archive",
    "references/archive/2022",
    "references/archive/2023",
    "clients",
    "clients/pending",
    "clients/active",
    "templates",
    "templates/draft",
    "internal",
    "internal/ops",
    "logs",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── MAIN REFERENCE FILE: onboarding-process.md ──────────────────────────────
# Intentionally messy: uses inconsistent formatting, has raw table data,
# some steps have extra detail, some are sparse. Agent must parse and reformat.
onboarding_process = """# 财资管理系统对接流程文档

## 版本：V2.3  更新日期：2024-03

本文档记录企业接入财资管理系统的完整工作流程。

---

## 流程详情

### 步骤1 确定使用接口

工作内容：根据实际业务场景，确定使用哪些接口功能模块。
执行内容：银行提供相应的接口文档及外部系统接入确认单，企业方需确定使用的接口，填写联机交易清单，明确业务范围。
执行方：企业
配合方：银行
预计时间：3-5个工作日

---

### 步骤2 网络接入信息

工作内容：填写第三方网络信息登记表，提供企业侧网络拓扑。
执行内容：企业需提供IP地址段、端口需求、防火墙策略等网络参数；银行据此规划接入方案。
执行方：企业
配合方：银行
预计时间：2-3个工作日

---

### 步骤3 客户访问服务器信息

工作内容：提交企业访问服务器的相关信息。
执行内容：企业填写服务器操作系统版本、运行环境（JDK/SDK版本）、服务器IP及MAC地址、证书需求等信息。
执行方：企业
配合方：银行
预计时间：1-2个工作日

---

### 步骤4 开通测试网络

工作内容：银行侧开通测试环境网络通道。
执行内容：银行根据企业提供的网络信息配置测试环境，开通专线或VPN通道，并将测试环境地址、端口、账号信息反馈给企业。
执行方：银行
配合方：企业
预计时间：3-5个工作日

---

### 步骤5 提供测试数据

工作内容：银行提供测试用账户及数据。
执行内容：银行提供测试账号、模拟交易数据集、接口测试用例文档（含正向用例和异常用例）；企业配合确认数据范围。
执行方：银行
配合方：企业
预计时间：2-3个工作日

---

### 步骤6 联调测试

工作内容：企业与银行共同完成接口联调与功能验证。
执行内容：企业依据接口文档完成开发，逐一执行测试用例（含边界测试、异常测试、性能测试），记录测试结果；银行提供技术支持，协助排查问题；双方签署联调测试报告。
执行方：企业
配合方：银行
预计时间：5-10个工作日（视开发进度而定）
注意：此为关键环节，建议客户预留充足时间

---

### 步骤7 生产上线

工作内容：在生产环境完成系统部署和切换。
执行内容：企业提交上线申请，银行审核并开通生产环境权限；企业在银行配合下完成生产环境配置，制定回滚方案。
执行方：企业
配合方：银行
预计时间：2-3个工作日

---

### 步骤8 上线验证

工作内容：使用真实业务场景进行生产环境验证。
执行内容：建议使用小额交易进行初步验证，监控交易成功率和响应时间，确认无误后开放全量业务；银行侧同步监控系统状态，发现问题及时处置。
执行方：企业
配合方：银行
预计时间：1-3个工作日

---

## 整体周期说明

整个流程通常需要2-4周，具体取决于客户开发进度和测试复杂程度。
"""

with open(os.path.join(workspace, "references/onboarding-process.md"), "w", encoding="utf-8") as f:
    f.write(onboarding_process)

# ── checklist.md ─────────────────────────────────────────────────────────────
checklist_content = """# 客户准备工作清单

## 企业对接准备事项

在正式开始对接之前，企业方需要完成以下准备工作：

### 技术准备
- [ ] 确认开发团队成员及联系方式
- [ ] 准备开发服务器（测试环境）
- [ ] 确认服务器操作系统和运行环境版本
- [ ] 准备网络环境（能够与银行测试环境通信）

### 文档准备
- [ ] 填写《外部系统接入确认单》
- [ ] 提交《服务器信息登记表》
- [ ] 提交《网络信息登记表》

### 业务准备
- [ ] 明确需要对接的业务功能模块
- [ ] 确认交易类型和资金规模
- [ ] 指定项目负责人（技术+业务各一名）

## 联系方式

对接期间如有问题，请联系银行对接支持团队。
"""

with open(os.path.join(workspace, "references/checklist.md"), "w", encoding="utf-8") as f:
    f.write(checklist_content)

# ── faq.md ───────────────────────────────────────────────────────────────────
faq_content = """# 常见问题解答 (FAQ)

## Q1: 整个对接周期大概多久？
A: 通常需要2-4周，主要取决于企业开发进度。联调测试阶段通常占用时间最长。

## Q2: 联调测试阶段需要双方都在线吗？
A: 不需要同时在线，但遇到问题时需要及时沟通。建议建立专属沟通群。

## Q3: 生产上线前需要哪些审批？
A: 需要完成所有测试用例的验证，提交联调测试报告，并通过银行侧的安全审核。

## Q4: 上线后出现问题如何处理？
A: 银行侧有7x24小时监控，生产问题可通过紧急联系渠道反馈，必要时可启动回滚方案。
"""

with open(os.path.join(workspace, "references/faq.md"), "w", encoding="utf-8") as f:
    f.write(faq_content)

# ── DISTRACTOR FILES ──────────────────────────────────────────────────────────

# Archive files (outdated versions)
archive_2022 = """# 对接流程 V1.0 (已废弃)
此版本已于2023年停用，请参考最新版本。
步骤1: 申请接入
步骤2: 技术对接
步骤3: 上线
"""
with open(os.path.join(workspace, "references/archive/2022/onboarding-v1.md"), "w", encoding="utf-8") as f:
    f.write(archive_2022)

archive_2023 = """# 对接流程 V2.0 (旧版)
6步骤版本，已更新为8步骤版本。
"""
with open(os.path.join(workspace, "references/archive/2023/onboarding-v2.md"), "w", encoding="utf-8") as f:
    f.write(archive_2023)

# Client files
client_pending = """客户名称: 某科技有限公司
状态: 待对接
联系人: 张工
备注: 等待客户提交网络信息
"""
with open(os.path.join(workspace, "clients/pending/client_20240301.txt"), "w", encoding="utf-8") as f:
    f.write(client_pending)

client_active = """客户名称: XX集团财务部
状态: 联调测试中（第6步）
对接进度: 60%
"""
with open(os.path.join(workspace, "clients/active/client_20240115.txt"), "w", encoding="utf-8") as f:
    f.write(client_active)

# Template draft files
template_draft = """[草稿] 客户欢迎邮件模板

尊敬的客户，
欢迎您接入我行财资管理系统...
（模板内容待补充）
"""
with open(os.path.join(workspace, "templates/draft/welcome_email_draft.txt"), "w", encoding="utf-8") as f:
    f.write(template_draft)

template_report = """联调测试报告模板

项目名称: ___________
测试时间: ___________
测试结果: ___________
双方签字: ___________
"""
with open(os.path.join(workspace, "templates/test_report_template.txt"), "w", encoding="utf-8") as f:
    f.write(template_report)

# Internal ops files
internal_ops = """内部操作规程 - 测试环境开通

1. 收到企业网络信息后，提交内部工单
2. 运维团队在3-5个工作日内完成配置
3. 完成后邮件通知企业侧联系人
"""
with open(os.path.join(workspace, "internal/ops/test_env_procedure.txt"), "w", encoding="utf-8") as f:
    f.write(internal_ops)

internal_checklist = """银行内部核查表

[ ] 接入确认单已收到
[ ] 网络信息已登记
[ ] 服务器信息已核实
[ ] 测试账号已分配
"""
with open(os.path.join(workspace, "internal/ops/bank_internal_checklist.txt"), "w", encoding="utf-8") as f:
    f.write(internal_checklist)

# Logs
log_entry = """2024-03-01 09:00 - 客户A完成步骤1
2024-03-02 14:30 - 客户A提交网络信息
2024-03-05 10:00 - 测试网络已开通
"""
with open(os.path.join(workspace, "logs/onboarding_log_2024.txt"), "w", encoding="utf-8") as f:
    f.write(log_entry)

# Random config distractor
config_data = {
    "system": "treasury-management",
    "version": "2.3",
    "environment": "production",
    "max_connections": 100,
    "timeout_seconds": 30
}
with open(os.path.join(workspace, "internal/system_config.json"), "w", encoding="utf-8") as f:
    json.dump(config_data, f, indent=2, ensure_ascii=False)

# A misleading "summary" that has wrong step count (6 steps, old version)
misleading_summary = """对接流程简介（内部培训材料 - 旧版）

我行财资系统对接分6个主要阶段：
1. 需求确认
2. 网络开通
3. 环境准备
4. 测试验证
5. 上线准备
6. 正式上线

注：此为简化版本，详情请参考最新完整流程文档。
"""
with open(os.path.join(workspace, "templates/draft/old_6step_summary.txt"), "w", encoding="utf-8") as f:
    f.write(misleading_summary)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")